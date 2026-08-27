"""Application entry point.

Startup sequence:
1. Configure logging
2. Run Alembic migrations (creates/upgrades schema)
3. Seed roles and permissions (idempotent)
4. Create DI container
5. Check is_first_run()
   - True  → show SetupWizardView
   - False → show LoginView
6. On login/setup success → show AppShell
7. On logout → return to LoginView
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QStackedWidget

from biometric_attendance.infrastructure.logging.logging_setup import configure_logging, get_logger
from biometric_attendance.infrastructure.data.database import engine, get_session
from biometric_attendance.infrastructure.data.models import Base, seed_roles_and_permissions

from biometric_attendance.app.container import AppContainer
from biometric_attendance.app.styles.theme import build_global_stylesheet
from biometric_attendance.app.viewmodels.login_vm import LoginViewModel
from biometric_attendance.app.viewmodels.setup_wizard_vm import SetupWizardViewModel
from biometric_attendance.app.views.login_view import LoginView
from biometric_attendance.app.views.setup_wizard_view import SetupWizardView
from biometric_attendance.app.views.app_shell import AppShell
from biometric_attendance.core.dtos.auth_dtos import SessionUser


def _run_migrations() -> None:
    """Apply any pending Alembic migrations programmatically."""
    from alembic.config import Config
    from alembic import command
    import pathlib

    alembic_ini = pathlib.Path(__file__).parents[2] / "alembic.ini"
    if not alembic_ini.exists():
        # Fallback: create tables directly (dev convenience)
        Base.metadata.create_all(bind=engine)
        return
    cfg = Config(str(alembic_ini))
    command.upgrade(cfg, "head")


log = get_logger(__name__)


def main() -> int:
    configure_logging()
    log.info("app.starting")

    # ── Schema setup ──────────────────────────────────────────────────────────
    try:
        _run_migrations()
    except Exception:
        # On first run before a migration exists, fall back to create_all
        log.warning("app.migration_fallback", reason="No migration found, using create_all")
        Base.metadata.create_all(bind=engine)

    with get_session() as session:
        seed_roles_and_permissions(session)

    # ── Qt application ────────────────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setApplicationName("Biometric Attendance Tracking System")
    app.setApplicationDisplayName("Biometric Attendance Tracking System")
    app.setOrganizationName("BATS")

    # Apply global stylesheet
    app.setStyleSheet(build_global_stylesheet())

    # Set default font
    font = QFont("Segoe UI", 13)
    app.setFont(font)

    # ── DI container ──────────────────────────────────────────────────────────
    container = AppContainer()

    # ── Screen manager ────────────────────────────────────────────────────────
    # Use a plain QStackedWidget as a root screen switcher (not a full nav stack)
    root = QStackedWidget()
    root.setWindowTitle("Biometric Attendance Tracking System")
    root.setMinimumSize(1100, 680)

    # References kept so GC doesn't destroy them
    _shell_ref: list[AppShell] = []

    def show_login() -> None:
        # Close shell if it exists
        if _shell_ref:
            _shell_ref[0].close()
            _shell_ref.clear()

        # Fresh VM + View each time (new session, cleared state)
        login_vm = LoginViewModel(auth_service=container.auth_service())
        login_view = LoginView(view_model=login_vm)
        login_view.login_success.connect(show_shell)

        # Remove old login/setup pages, add fresh one
        while root.count() > 0:
            root.removeWidget(root.widget(0))
        root.addWidget(login_view)
        root.setCurrentWidget(login_view)
        root.setFixedSize(root.minimumSize())
        root.showNormal()

    def show_setup() -> None:
        setup_vm = SetupWizardViewModel(setup_service=container.setup_service())
        setup_view = SetupWizardView(view_model=setup_vm)
        setup_view.setup_complete.connect(lambda _user: show_login())

        while root.count() > 0:
            root.removeWidget(root.widget(0))
        root.addWidget(setup_view)
        root.setCurrentWidget(setup_view)
        root.setMinimumSize(1100, 680)
        root.resize(1100, 720)
        root.showNormal()

    def show_shell(user: SessionUser) -> None:
        shell = AppShell(user=user, container=container)
        shell.logout_requested.connect(show_login)
        _shell_ref.clear()
        _shell_ref.append(shell)

        # Hide the root switcher and show the shell as a separate window
        root.hide()
        shell.showMaximized()

    # ── First-run detection ───────────────────────────────────────────────────
    setup_service = container.setup_service()
    if setup_service.is_first_run():
        log.info("app.first_run")
        show_setup()
    else:
        show_login()

    root.show()
    log.info("app.ready")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
