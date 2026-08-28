"""SetupWizardView — first-run administrator account creation.

Shown when SetupService.is_first_run() == True.
After successful creation, emits setup_complete(SessionUser).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.styles import theme
from biometric_attendance.app.viewmodels.setup_wizard_vm import SetupWizardViewModel
from biometric_attendance.core.dtos.auth_dtos import SessionUser


class _FieldRow(QWidget):
    """Label + input + inline error label for a single form field."""

    def __init__(self, label: str, placeholder: str, secret: bool = False) -> None:
        super().__init__()
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setObjectName("FormLabel")
        layout.addWidget(lbl)

        if secret:
            input_layout = QHBoxLayout()
            input_layout.setSpacing(0)
            
            self.input = QLineEdit()
            self.input.setPlaceholderText(placeholder)
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            self.input.setStyleSheet(f"border-top-right-radius: 0; border-bottom-right-radius: 0;")
            input_layout.addWidget(self.input)

            from biometric_attendance.app.styles.icons import icon
            self._show_pw_btn = QPushButton()
            self._show_pw_btn.setIcon(icon("eye", size=18))
            self._show_pw_btn.setFixedSize(40, 40)
            self._show_pw_btn.setCheckable(True)
            self._show_pw_btn.setObjectName("IconButton")
            self._show_pw_btn.setStyleSheet(
                f"border: 1px solid {theme.BORDER}; border-left: none; "
                f"border-top-left-radius: 0; border-bottom-left-radius: 0;"
            )
            self._show_pw_btn.clicked.connect(self._toggle_password_visibility)
            input_layout.addWidget(self._show_pw_btn)
            
            layout.addLayout(input_layout)
        else:
            self.input = QLineEdit()
            self.input.setPlaceholderText(placeholder)
            layout.addWidget(self.input)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("ErrorLabel")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.hide()
        layout.addWidget(self.error_lbl)

    def _toggle_password_visibility(self, checked: bool) -> None:
        from biometric_attendance.app.styles.icons import icon
        if checked:
            self.input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_pw_btn.setIcon(icon("eye-off", size=18))
        else:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_pw_btn.setIcon(icon("eye", size=18))

    def value(self) -> str:
        return self.input.text()

    def show_error(self, message: str) -> None:
        self.error_lbl.setText(message)
        self.error_lbl.show()
        self.input.setProperty("error", "true")
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)

    def clear_error(self) -> None:
        self.error_lbl.hide()
        self.error_lbl.setText("")
        self.input.setProperty("error", "false")
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)


class SetupWizardView(QWidget):
    """First-run setup wizard page.

    Signals:
        setup_complete(SessionUser): emitted after admin account is created.
    """

    setup_complete = Signal(object)

    def __init__(
        self, view_model: SetupWizardViewModel, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._field_map: dict[str, _FieldRow] = {}
        self._build_ui()
        self._connect_signals()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setObjectName("SetupWizardPage")
        self.setStyleSheet(f"#SetupWizardPage {{ background-color: {theme.BACKGROUND}; }}")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Centred card
        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(460)
        theme.apply_card_shadow(card, level=2)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(theme.SPACE_3XL, theme.SPACE_3XL, theme.SPACE_3XL, theme.SPACE_3XL)
        card_layout.setSpacing(theme.SPACE_LG)

        # Header
        from biometric_attendance.app.styles.icons import pixmap
        icon = QLabel()
        icon.setPixmap(pixmap("shield", color=theme.PRIMARY, size=48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon)

        heading = QLabel("Welcome — Create Administrator Account")
        heading.setObjectName("HeadingLabel")
        heading.setWordWrap(True)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet(f"font-size: {theme.TS_PAGE_TITLE}px; background: transparent;")
        card_layout.addWidget(heading)

        sub = QLabel(
            "This is the first time the system is launched.\n"
            "Create an administrator account to get started."
        )
        sub.setObjectName("SubheadingLabel")
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(sub)

        card_layout.addSpacing(theme.SPACE_SM)

        # Form fields
        fields: list[tuple[str, str, str, bool]] = [
            ("display_name", "Full Name", "e.g. Juan Dela Cruz", False),
            ("username", "Username", "e.g. admin", False),
            ("email", "Email Address", "e.g. admin@company.com", False),
            ("password", "Password", "At least 8 characters", True),
            ("confirm_password", "Confirm Password", "Re-enter your password", True),
        ]

        for field_key, label, placeholder, secret in fields:
            row = _FieldRow(label, placeholder, secret)
            card_layout.addWidget(row)
            self._field_map[field_key] = row

        # General error label
        self._general_error = QLabel("")
        self._general_error.setObjectName("ErrorLabel")
        self._general_error.setWordWrap(True)
        self._general_error.hide()
        card_layout.addWidget(self._general_error)

        # Submit button
        self._submit_btn = QPushButton("Create Administrator Account")
        self._submit_btn.setObjectName("PrimaryButton")
        self._submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._submit_btn.setFixedHeight(42)
        self._submit_btn.clicked.connect(self._on_submit)
        card_layout.addWidget(self._submit_btn)

        center.addWidget(card)
        outer.addLayout(center)

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._vm.setup_success.connect(self._on_setup_success)
        self._vm.field_error.connect(self._on_field_error)
        self._vm.general_error.connect(self._on_general_error)
        self._vm.loading_changed.connect(self._on_loading_changed)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_submit(self) -> None:
        self._clear_all_errors()
        self._vm.create_admin(
            display_name=self._field_map["display_name"].value(),
            username=self._field_map["username"].value(),
            email=self._field_map["email"].value(),
            password=self._field_map["password"].value(),
            confirm_password=self._field_map["confirm_password"].value(),
        )

    def _on_setup_success(self, user: SessionUser) -> None:
        self.setup_complete.emit(user)

    def _on_field_error(self, field: str, message: str) -> None:
        if field in self._field_map:
            self._field_map[field].show_error(message)
        else:
            self._on_general_error(message)

    def _on_general_error(self, message: str) -> None:
        self._general_error.setText(message)
        self._general_error.show()

    def _on_loading_changed(self, loading: bool) -> None:
        self._submit_btn.setEnabled(not loading)
        self._submit_btn.setText(
            "Creating account…" if loading else "Create Administrator Account"
        )

    def _clear_all_errors(self) -> None:
        for row in self._field_map.values():
            row.clear_error()
        self._general_error.hide()
        self._general_error.setText("")
