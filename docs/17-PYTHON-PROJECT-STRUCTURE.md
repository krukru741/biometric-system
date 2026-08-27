# Python (PySide6) Project Structure

## Recommended Layout

``` text
biometric-attendance/
├── pyproject.toml
├── alembic.ini
│
├── biometric_attendance/
│   ├── app/
│   │   ├── views/
│   │   ├── viewmodels/
│   │   ├── widgets/
│   │   ├── resources/
│   │   ├── styles/
│   │   ├── converters/
│   │   └── main.py
│   │
│   ├── core/
│   │   ├── entities/
│   │   ├── enums/
│   │   ├── interfaces/
│   │   ├── dtos/
│   │   └── exceptions/
│   │
│   ├── application/
│   │   ├── services/
│   │   ├── interfaces/
│   │   ├── validators/
│   │   ├── attendance/
│   │   └── use_cases/
│   │
│   └── infrastructure/
│       ├── data/
│       ├── repositories/
│       ├── biometric/
│       ├── security/
│       ├── logging/
│       └── sync/
│
└── tests/
    ├── unit/
    ├── integration/
    └── attendance/
```

## MVVM Flow

``` text
View (PySide6 QWidget/QML)
 ↓
ViewModel (QObject + Signals/Slots)
 ↓
Application Service
 ↓
Core Interface
 ↓
Infrastructure Implementation
 ↓
Database / Device
```

## Rules

-   Views should contain UI concerns only.
-   ViewModels should expose state (as properties/Signals) and commands (as
    Slots) — Views bind to ViewModels via Qt's Signal/Slot mechanism rather
    than direct manipulation.
-   Business rules belong in application/domain services.
-   Database access belongs in Infrastructure logic (SQLAlchemy engine/session,
    repository implementations, biometric SDK wrappers).
-   Avoid embedding queries directly inside button click handlers.
-   Use `dependency-injector` (or a similar container) to wire ViewModels to
    Application Services and Services to Repositories.

## Example Command Flow

``` text
Enroll Button (clicked Signal)
 ↓
EnrollmentViewModel.on_enroll_clicked()
 ↓
IBiometricService
 ↓
Biometric Adapter
 ↓
Vendor SDK
 ↓
BiometricTemplate
 ↓
EmployeeBiometric Repository (SQLAlchemy)
 ↓
SQLite
```

## Example ViewModel Skeleton

``` python
from PySide6.QtCore import QObject, Signal, Slot


class EnrollmentViewModel(QObject):
    status_changed = Signal(str)
    enrollment_completed = Signal(bool)

    def __init__(self, biometric_service: "IBiometricService"):
        super().__init__()
        self._biometric_service = biometric_service

    @Slot()
    def on_enroll_clicked(self) -> None:
        self.status_changed.emit("Capturing sample...")
        # delegate to application service, then emit results
```

## Packaging / Tooling Notes

-   Use `pyproject.toml` (e.g. with `poetry` or `hatch`) for dependency
    management and packaging.
-   Use `Alembic` for versioned SQLite schema migrations.
-   Use `pytest` for unit/integration tests, matching the `tests/` layout.
-   Package the desktop app for distribution with a tool such as
    `PyInstaller` or `Briefcase`.
