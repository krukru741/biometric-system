# Development Roadmap

## Phase 1 --- Foundation

-   Create Python project (PySide6)
-   Configure MVVM
-   Configure dependency injection (dependency-injector)
-   Configure SQLAlchemy + Alembic
-   Configure SQLite
-   Create AppShell
-   Create theme
-   Create login
-   Create roles and permissions

## Phase 2 --- Workforce

-   Departments
-   Positions
-   Employees
-   Employee profile
-   Employee archive
-   Search and filtering

## Phase 3 --- Scheduling

-   Shift templates
-   Employee schedules
-   Calendar
-   Rest days
-   Holidays
-   Overnight shifts

## Phase 4 --- Attendance Engine

-   Attendance events
-   Attendance records
-   IN/OUT processing
-   Late calculation
-   Undertime
-   Overtime
-   Status calculation
-   Correction workflow

**Event source:** Phase 4 is built and fully tested against
`MockAttendanceEvent` / test fixtures, not a physical biometric device.
This lets late/absence/overnight/overtime rules be validated in
isolation before any hardware dependency is introduced.

``` text
Phase 4 — Attendance Engine
        ↓
Uses MockAttendanceEvent / Test Fixtures
        ↓
Validate attendance rules
        ↓
Phase 5 — Biometric Integration
        ↓
Replace mock event source with real biometric adapter
```

## Phase 5 --- Biometrics

-   Scanner adapter
-   Enrollment
-   Verification
-   Template storage
-   Device management
-   Device synchronization

**Integration point:** Phase 5 replaces the mock event source from Phase 4
with `IBiometricDevice` adapters (see `05-BIOMETRICS.md`, Section 7). The
Attendance Engine's processing logic itself does not change — only the
origin of the `AttendanceEvent` records.

## Phase 6 --- Leave

-   Leave types
-   Requests
-   Approval
-   Leave balances
-   Attendance integration

## Phase 7 --- Overtime

-   OT requests
-   Approval
-   Calculation
-   Attendance integration

## Phase 8 --- Reports

-   Daily report
-   Monthly report
-   Employee report
-   Department report
-   Late/absence
-   OT
-   Leave
-   PDF
-   Excel
-   Printing

## Phase 9 --- Administration

-   User management
-   Permissions
-   Audit logs
-   Settings
-   Backup
-   Restore

## Phase 10 --- Hardening

-   Error handling
-   Logging
-   Offline mode
-   Sync retry
-   Performance testing
-   Security testing
-   Backup testing
-   User acceptance testing
