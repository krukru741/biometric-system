"""Attendance Corrections View — Pending Approvals + My Requests tabs."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.core.enums.attendance import CorrectionStatus


_STATUS_COLORS = {
    CorrectionStatus.PENDING: "#FFC107",
    CorrectionStatus.APPROVED: "#28A745",
    CorrectionStatus.REJECTED: "#DC3545",
}


class AttendanceCorrectionsView(QWidget):
    """Corrections approval workflow — two tabs: Pending Approvals and My Requests."""

    def __init__(self, view_model, logged_in_user_id: int = 1, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self._user_id = logged_in_user_id
        self.setObjectName("AttendanceCorrectionsView")
        self._setup_ui()
        self._connect_signals()
        self.vm.load_pending()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Attendance Corrections")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # ── Pending Approvals tab ─────────────────────────────────────────────
        pending_widget = QWidget()
        pending_layout = QVBoxLayout(pending_widget)
        pending_layout.setContentsMargins(8, 8, 8, 8)

        self.pending_table = self._make_corrections_table()
        pending_layout.addWidget(self.pending_table)

        action_row = QHBoxLayout()
        self.approve_btn = QPushButton("Approve Selected")
        self.approve_btn.setObjectName("PrimaryButton")
        self.reject_btn = QPushButton("Reject Selected")
        self.reject_btn.setObjectName("GhostButton")
        action_row.addStretch()
        action_row.addWidget(self.approve_btn)
        action_row.addWidget(self.reject_btn)
        pending_layout.addLayout(action_row)

        self.tabs.addTab(pending_widget, "Pending Approvals")

        # ── My Requests tab ───────────────────────────────────────────────────
        my_widget = QWidget()
        my_layout = QVBoxLayout(my_widget)
        my_layout.setContentsMargins(8, 8, 8, 8)

        self.my_table = self._make_corrections_table()
        my_layout.addWidget(self.my_table)

        self.tabs.addTab(my_widget, "My Requests")

    def _make_corrections_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Employee", "Type", "Original", "Requested", "Reason",
            "Requested By", "Requested At", "Status"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return table

    def _connect_signals(self):
        self.vm.pending_loaded.connect(self._render_pending)
        self.vm.my_corrections_loaded.connect(self._render_my_corrections)
        self.vm.error_occurred.connect(self._on_error)
        self.vm.correction_approved.connect(lambda _: QMessageBox.information(
            self, "Approved", "Correction approved and record recalculated."
        ))
        self.vm.correction_rejected.connect(lambda _: QMessageBox.information(
            self, "Rejected", "Correction rejected."
        ))
        self.approve_btn.clicked.connect(self._on_approve)
        self.reject_btn.clicked.connect(self._on_reject)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, idx: int):
        if idx == 1:
            self.vm.load_my_corrections(self._user_id)

    def _render_pending(self, corrections):
        self._render_to_table(self.pending_table, corrections)

    def _render_my_corrections(self, corrections):
        self._render_to_table(self.my_table, corrections)

    def _render_to_table(self, table: QTableWidget, corrections):
        table.setRowCount(0)
        for c in corrections:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(c.employee_name))
            table.setItem(row, 1, QTableWidgetItem(c.correction_type.value))
            table.setItem(row, 2, QTableWidgetItem(c.original_value))
            table.setItem(row, 3, QTableWidgetItem(c.requested_value))
            table.setItem(row, 4, QTableWidgetItem(c.reason))
            table.setItem(row, 5, QTableWidgetItem(str(c.requested_by)))
            table.setItem(row, 6, QTableWidgetItem(c.requested_at.strftime("%Y-%m-%d %H:%M")))
            status_item = QTableWidgetItem(c.status.value)
            from PySide6.QtGui import QColor, QBrush
            color = _STATUS_COLORS.get(c.status, "#6C757D")
            status_item.setBackground(QBrush(QColor(color)))
            status_item.setForeground(Qt.GlobalColor.white)
            table.setItem(row, 7, status_item)
            # Store correction id in UserRole on first column
            table.item(row, 0).setData(Qt.ItemDataRole.UserRole, c.id)

    def _get_selected_correction_id(self) -> int | None:
        rows = self.pending_table.selectedItems()
        if not rows:
            return None
        first = self.pending_table.item(rows[0].row(), 0)
        return first.data(Qt.ItemDataRole.UserRole) if first else None

    def _on_approve(self):
        cid = self._get_selected_correction_id()
        if cid is None:
            QMessageBox.warning(self, "Select", "Please select a correction to approve.")
            return
        reply = QMessageBox.question(
            self, "Approve", "Approve this correction? The record will be recalculated.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.vm.approve_correction(cid, self._user_id)

    def _on_reject(self):
        cid = self._get_selected_correction_id()
        if cid is None:
            QMessageBox.warning(self, "Select", "Please select a correction to reject.")
            return
        comment, ok = _ask_comment(self)
        if ok and comment.strip():
            self.vm.reject_correction(cid, self._user_id, comment.strip())

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Error", message)


def _ask_comment(parent) -> tuple[str, bool]:
    """Simple dialog to collect a rejection comment."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Rejection Comment")
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("Please enter a reason for rejection:"))
    text_edit = QTextEdit()
    text_edit.setMaximumHeight(100)
    layout.addWidget(text_edit)
    bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    bb.accepted.connect(dialog.accept)
    bb.rejected.connect(dialog.reject)
    layout.addWidget(bb)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return text_edit.toPlainText(), True
    return "", False
