"""LoginView — the login screen (02-AUTHENTICATION-AUTHORIZATION.md §3).

UI concerns only:
- Renders the form.
- Forwards button clicks to LoginViewModel via Slot.
- Responds to ViewModel Signals.
- Zero business logic, zero direct service calls.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.styles import theme
from biometric_attendance.app.viewmodels.login_vm import LoginViewModel
from biometric_attendance.core.dtos.auth_dtos import SessionUser


class LoginView(QWidget):
    """Full-screen login page.

    Signals:
        login_success(SessionUser): relayed from ViewModel for AppShell routing.
    """

    login_success = Signal(object)

    def __init__(self, view_model: LoginViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._build_ui()
        self._connect_signals()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setObjectName("LoginPage")
        self.setStyleSheet(f"#LoginPage {{ background-color: {theme.BACKGROUND}; }}")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left decorative panel
        left = self._build_left_panel()
        outer.addWidget(left, 1)

        # Right login card
        right = self._build_right_panel()
        outer.addWidget(right, 1)

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("LoginLeftPanel")
        panel.setStyleSheet(f"""
            #LoginLeftPanel {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme.PRIMARY},
                    stop:1 {theme.PRIMARY_DARK}
                );
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(theme.SPACE_3XL, 0, theme.SPACE_3XL, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from biometric_attendance.app.styles.icons import pixmap
        icon = QLabel()
        icon.setPixmap(pixmap("badge", color=theme.ACCENT, size=64))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        layout.addSpacing(theme.SPACE_XL)

        title = QLabel("Biometric Attendance\nTracking System")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {theme.TEXT_ON_PRIMARY}; font-size: {theme.TS_DISPLAY}px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(title)

        layout.addSpacing(theme.SPACE_LG)

        tagline = QLabel(
            "Secure • Accurate • Efficient\n\n"
            "Track employee attendance with biometric\n"
            "precision and real-time reporting."
        )
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet(
            f"color: rgba(255,255,255,0.72); font-size: {theme.TS_BODY}px; background: transparent;"
        )
        layout.addWidget(tagline)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("LoginRightPanel")
        panel.setStyleSheet(f"#LoginRightPanel {{ background-color: {theme.BACKGROUND}; }}")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(theme.SPACE_3XL, 0, theme.SPACE_3XL, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(400)
        theme.apply_card_shadow(card, level=2)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(theme.SPACE_2XL, theme.SPACE_2XL, theme.SPACE_2XL, theme.SPACE_2XL)
        card_layout.setSpacing(theme.SPACE_LG)

        # Heading
        heading = QLabel("Sign In")
        heading.setObjectName("HeadingLabel")
        card_layout.addWidget(heading)

        sub = QLabel("Enter your credentials to continue")
        sub.setObjectName("SubheadingLabel")
        card_layout.addWidget(sub)

        card_layout.addSpacing(theme.SPACE_SM)

        # Username
        lbl_user = QLabel("Username")
        lbl_user.setObjectName("FormLabel")
        card_layout.addWidget(lbl_user)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Enter username")
        self._username_input.setObjectName("UsernameInput")
        card_layout.addWidget(self._username_input)

        # Password
        lbl_pass = QLabel("Password")
        lbl_pass.setObjectName("FormLabel")
        card_layout.addWidget(lbl_pass)

        pw_row = QHBoxLayout()
        pw_row.setSpacing(0)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Enter password")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setObjectName("PasswordInput")
        pw_row.addWidget(self._password_input)

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
        pw_row.addWidget(self._show_pw_btn)

        # Fix the line-edit right border radius when show-pw is present
        self._password_input.setStyleSheet(
            f"border-top-right-radius: 0; border-bottom-right-radius: 0;"
        )

        card_layout.addLayout(pw_row)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setObjectName("ErrorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        card_layout.addWidget(self._error_label)

        # Sign In button
        self._sign_in_btn = QPushButton("Sign In")
        self._sign_in_btn.setObjectName("PrimaryButton")
        self._sign_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sign_in_btn.setFixedHeight(42)
        self._sign_in_btn.clicked.connect(self._on_sign_in_clicked)
        card_layout.addWidget(self._sign_in_btn)

        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

        # Allow Enter key to submit
        self._username_input.returnPressed.connect(self._on_sign_in_clicked)
        self._password_input.returnPressed.connect(self._on_sign_in_clicked)

        return panel

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._vm.login_success.connect(self._on_login_success)
        self._vm.login_failed.connect(self._on_login_failed)
        self._vm.loading_changed.connect(self._on_loading_changed)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_sign_in_clicked(self) -> None:
        self._clear_error()
        self._vm.login(
            self._username_input.text(),
            self._password_input.text(),
        )

    def _toggle_password_visibility(self, checked: bool) -> None:
        from biometric_attendance.app.styles.icons import icon
        if checked:
            self._password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_pw_btn.setIcon(icon("eye-off", size=18))
        else:
            self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_pw_btn.setIcon(icon("eye", size=18))

    def _on_login_success(self, user: SessionUser) -> None:
        self._password_input.clear()
        self.login_success.emit(user)

    def _on_login_failed(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()
        # Shake the error label for micro-feedback
        self._username_input.setProperty("error", "true")
        self._password_input.setProperty("error", "true")
        self._username_input.style().unpolish(self._username_input)
        self._username_input.style().polish(self._username_input)
        self._password_input.style().unpolish(self._password_input)
        self._password_input.style().polish(self._password_input)

    def _on_loading_changed(self, loading: bool) -> None:
        self._sign_in_btn.setEnabled(not loading)
        self._sign_in_btn.setText("Signing in…" if loading else "Sign In")

    def _clear_error(self) -> None:
        self._error_label.hide()
        self._error_label.setText("")
        for widget in (self._username_input, self._password_input):
            widget.setProperty("error", "false")
            widget.style().unpolish(widget)
            widget.style().polish(widget)
