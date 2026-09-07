# Desktop UI component system

This project uses PySide6, so the component APIs use constructor arguments, methods, and Qt signals rather than web props. Attendance Records and Employees are the first integrated screens. Existing domain services and the clay/off-white theme remain the foundations.

## Architecture

- `app/styles/theme.py`: shared colors, spacing, focus indicators, and Qt styles.
- `app/widgets/components.py`: domain-independent page header, filter layout, state container, column schema, and table model/view.
- `app/viewmodels/async_loader.py`: bounded background reads with GUI-thread delivery and stale-result suppression.
- `app/viewmodels/*`: query inputs, validation, pagination, safe errors, and DTO signals.
- `app/views/*`: compose widgets and connect user actions to viewmodels. No database queries in the view.
- `infrastructure/repositories/*`: session ownership and database-side filtering/pagination.

Data flows from a user action to a viewmodel, through a repository-owned worker session, and back as detached DTOs through a queued Qt signal. Widgets and models are updated only on the GUI thread.

## Public APIs

| Component | Constructor/API | Contract |
| --- | --- | --- |
| `PageHeader` | `(title, description="", action=None, parent=None)` | Stacks its optional action below text at compact widths. |
| `FilterBar` | `add_field(label, control)`, `add_action(widget)` | Labels are buddies, accessible names are explicit, fields wrap in creation order. Use `&` for keyboard mnemonics. |
| `ContentState` | `(content, parent=None)` | Owns the content widget and a shared message panel. |
| | `show_content()` | Restores content and focus if focus was inside the hidden state panel. |
| | `show_state(state, title, detail="", action="")` | State is `loading`, `empty`, or `error`. Text is always plain text; error copy cannot inject rich text. |
| | `action_requested` signal | The view decides what retry or recovery means. No hidden network calls. |
| `Column` | `(title, value, format=str, width=130)` | Immutable column schema. `value(row)` returns a consistent comparable type; `format(value)` handles display only. `None` displays an em dash. |
| `RecordTable` | `(columns, name=..., row_key=..., parent=None)` | `name` is the accessible name. Keys must be unique and stable. |
| | `set_rows(sequence)`, `selected_record()` | Retains selection by key across replacement; returns `None` when nothing is selected. |
| `AsyncLoader` | `(parent=None, error_message=...)`, `load(callable)` | One running job and at most one pending replacement. Latest request wins; obsolete work is not delivered. |
| | `loaded(object)`, `failed(str)`, `busy_changed(bool)` | Delivered on the owner's GUI thread. Worker exceptions are logged; the UI receives safe copy. |

Qt parent ownership is used throughout. Destroying the receiver disconnects result delivery. Reads already running finish normally; there is no unsafe thread termination.

## Usage

```python
from biometric_attendance.app.widgets.components import (
    Column, ContentState, RecordTable,
)

table = RecordTable(
    [
        Column("Employee", lambda row: row.full_name, width=220),
        Column("Minutes", lambda row: row.minutes, lambda value: f"{value} min"),
    ],
    name="Employee hours",
    row_key=lambda row: row.id,
)
state = ContentState(table)
layout.addWidget(state)
state.show_state("loading", "Loading hours…")

# In a GUI-thread result handler:
table.set_rows(rows)
if rows:
    state.show_content()
else:
    state.show_state("empty", "No hours found", "Try a different date range.")

# In an error handler:
state.show_state("error", "Hours unavailable", "Please try again.", action="Retry")
state.action_requested.connect(view_model.reload)
```

Run the interactive, sample-only gallery:

```powershell
python -m biometric_attendance.app.examples.components_demo
```

The gallery exercises sorting, missing values, resizing, loading, empty, and retry states without opening a production database.

## Integrated behavior

Attendance Records fetches 100 rows plus one lookahead row per page. The repository applies the limit and offset in SQL. Filters are retained during refresh, invalid dates receive inline feedback, and navigation is disabled during loading. Sorting is explicitly scoped to the current page. Generating absent records refreshes the selected range instead of silently displaying a different range.

Employees uses the same header, filters, state panel, and model-backed table. Reads run in the background, search input is debounced, selection survives filtering when its key remains present, and selected-row actions work with the keyboard. Archived employees cannot be archived again. A text status is always provided; meaning does not depend on color.

Tables retain readable column widths and horizontal scrolling instead of shrinking every column into illegibility. They create no widgets or `QTableWidgetItem` objects per cell. Filters wrap by available width. The surrounding application still has its existing desktop minimum window size.

## Engineering practices and limits

- Keep repository sessions inside the worker that uses them. Never pass a shared SQLAlchemy session, ORM model, or Qt widget to a worker. Existing container repositories create short-lived sessions and return DTOs.
- Use `AsyncLoader` for idempotent reads only. It coalesces pending requests and must not be used for writes that must execute exactly once.
- Retain filter values and stable IDs; never use visual row numbers as business identifiers.
- Disable actions when selection is absent, a load is pending, or the action is invalid for the selected entity.
- Avoid automatic focus stealing when a background refresh completes. Label buddies, standard Qt keyboard controls, accessible names, plain text, and state-change accessibility events are provided. Real NVDA/Windows Narrator testing is still required before an accessibility conformance claim.
- The employee directory and employee dropdown still fetch all employees. A very large installation needs paginated server-side employee search and an asynchronous employee picker. Model-backed rendering reduces widget cost but does not make unbounded queries scalable.
- Attendance uses offset pagination. Deep pages at large scale should migrate to cursor pagination with indexed ordering. Cross-page sorting needs a validated server-side sort API; current-page sorting is labelled explicitly.
- Existing create/edit/archive and absent-generation writes remain synchronous. Long-running writes need a separate non-coalescing command runner with duplicate-submit protection and transaction-aware retry behavior.
- Database timeouts govern worker termination. A new request discards stale results; it does not cancel an already-running query. Do not promise immediate application shutdown during arbitrarily slow I/O.
- UI state handling does not replace authorization. Keep domain permissions and validation enforced at the service boundary.
- No claim of million-user capacity follows from these UI changes. Backend scale, indexes, deployment architecture, and end-to-end load testing remain separate requirements.

## Verification

`tests/ui/test_components.py` runs Qt offscreen and covers typed sorting, null values, stable selection, keyboard retry, compact filter wrapping, safe error recovery, bounded/coalesced background work, destruction during reads, GUI-thread delivery, attendance paging/validation, and employee actions. Integration tests cover SQL pagination alongside the existing attendance workflows.

```powershell
python -B -m pytest -p no:cacheprovider
```

Before release, also verify the real Windows application at 100%, 150%, and 200% scaling; keyboard-only navigation; Narrator/NVDA announcement order; slow storage; and representative production data volumes.
