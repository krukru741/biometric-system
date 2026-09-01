# Fix Database Connection Leak and Atomicity

## Assessment of Current Refactor

You are absolutely right. The automated broad refactor of the 13 repository files broke several critical things:

1. **Automated Tests Failed**: The test suite manually instantiates repositories and passes in mock/test sessions (e.g. `AttendanceEventRepository(session)`). Because `session` was stripped from the `__init__` signatures, the entire test suite is crashing with `TypeError`.
2. **Atomicity Lost**: Complex multi-step operations like `process_event` (11 steps) and `approve_correction` are now broken. Because every single repository method creates its own `get_session()`, these operations are no longer atomic. If step 5 fails, steps 1-4 are already committed, leaving the database in an inconsistent state.
3. **Detached Instances**: While `expire_on_commit=False` prevents basic attribute access from crashing, any lazy-loaded relationships (like `EmployeeModel.department`) will raise a `DetachedInstanceError` if accessed by the service layer outside the repository's short-lived `with` block.

## Proposed Changes

To fix the connection pool leak while preserving atomicity, test isolation, and dependency injection, the **Service Layer** must own the unit of work.

Because injecting a pre-instantiated session into repositories at the container level locks that session for the lifetime of the repository, we have two architectural options to implement this. I strongly recommend **Option 2** for its minimal invasiveness and elegance.

### Option 1: Explicit Session Passing (Massive Refactor)
- **What it entails**: Remove `session` from repository `__init__` methods. Update **every** repository method signature to accept a `session: Session` parameter (e.g., `def create(self, session: Session, ...)`). Update **every** service method to open a `with get_session() as session:` block and pass that session down into every repository call. Update **all** tests to pass their mock sessions into the method calls instead of the constructor.
- **Pros**: Explicit, zero magic.
- **Cons**: Massive blast radius. Requires rewriting hundreds of method signatures across 13 repositories, 5 services, and the entire test suite.

### Option 2: Scoped Session + Transactional Service Decorator (Recommended)
- **What it entails**: 
  1. Revert the repositories back to their original state (accepting `session` in `__init__`).
  2. In `database.py`, wrap the `SessionFactory` in SQLAlchemy's thread-local `scoped_session` (e.g., `SessionLocal = scoped_session(SessionFactory)`).
  3. In `container.py`, inject `SessionLocal` into the repositories. Because it is a thread-local proxy, all repositories within the same thread transparently share the **exact same** active session.
  4. Create a `@transactional` decorator (or context manager) that wraps the Service Layer methods. When a service method completes, it calls `SessionLocal.remove()` to cleanly close the transaction and return the connection to the pool.
- **Pros**: Zero changes to repository code, zero changes to service method bodies, zero changes to tests (tests can still inject mock sessions manually). Atomicity is perfectly preserved.

## User Review Required

> [!WARNING]
> Please review the assessment. If you agree with **Option 2**, I will implement it. It perfectly aligns with your directive to scope sessions to a single unit of work (the service layer) while avoiding a massive rewrite of every method signature in the app.
