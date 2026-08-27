"""View for managing Shift Templates."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.viewmodels.scheduling_vms import ShiftTemplatesViewModel
from biometric_attendance.core.dtos.scheduling_dtos import ShiftTemplateEntity


def _to_qtime(t: dt.time) -> QTime:
    return QTime(t.hour, t.minute)


def _from_qtime(q: QTime) -> dt.time:
    return dt.time(q.hour(), q.minute())


class ShiftFormDialog(QDialog):
    """Add / Edit Shift Template dialog."""

    def __init__(self, parent=None, shift: ShiftTemplateEntity | None = None):
        super().__init__(parent)
        is_edit = shift is not None
        self.setWindowTitle("Edit Shift Template" if is_edit else "Add Shift Template")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        from PySide6.QtWidgets import QLineEdit
        self.name_input = QLineEdit()
        lbl = QLabel("Shift Name *")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.name_input)

        self.start_edit = QTimeEdit()
        self.start_edit.setDisplayFormat("HH:mm")
        lbl = QLabel("Start Time *")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.start_edit)

        self.end_edit = QTimeEdit()
        self.end_edit.setDisplayFormat("HH:mm")
        lbl = QLabel("End Time *")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.end_edit)

        self.break_start_edit = QTimeEdit()
        self.break_start_edit.setDisplayFormat("HH:mm")
        lbl = QLabel("Break Start")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.break_start_edit)

        self.break_end_edit = QTimeEdit()
        self.break_end_edit.setDisplayFormat("HH:mm")
        lbl = QLabel("Break End")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.break_end_edit)

        def _spin(lo=0, hi=120):
            s = QSpinBox()
            s.setRange(lo, hi)
            return s

        self.grace_spin = _spin()
        lbl = QLabel("Grace Period (mins)")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.grace_spin)

        self.late_spin = _spin()
        lbl = QLabel("Late Threshold (mins)")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.late_spin)

        self.early_out_spin = _spin()
        lbl = QLabel("Early-Out Threshold (mins)")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.early_out_spin)

        self.ot_spin = _spin(0, 480)
        lbl = QLabel("OT Threshold (mins)")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.ot_spin)

        layout.addLayout(form)

        btn_label = "Update Shift" if is_edit else "Add Shift"
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.save_btn = QPushButton(btn_label)
        self.save_btn.setObjectName("PrimaryButton")
        self.button_box.addButton(self.save_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        if is_edit:
            self.name_input.setText(shift.name)
            self.start_edit.setTime(_to_qtime(shift.start_time))
            self.end_edit.setTime(_to_qtime(shift.end_time))
            if shift.break_start:
                self.break_start_edit.setTime(_to_qtime(shift.break_start))
            if shift.break_end:
                self.break_end_edit.setTime(_to_qtime(shift.break_end))
            self.grace_spin.setValue(shift.grace_period_mins)
            self.late_spin.setValue(shift.late_threshold_mins)
            self.early_out_spin.setValue(shift.early_out_threshold_mins)
            self.ot_spin.setValue(shift.overtime_threshold_mins)
        else:
            self.start_edit.setTime(QTime(8, 0))
            self.end_edit.setTime(QTime(17, 0))

    def get_data(self) -> dict:
        from PySide6.QtWidgets import QLineEdit
        return {
            "name": self.name_input.text().strip(),
            "start_time": _from_qtime(self.start_edit.time()),
            "end_time": _from_qtime(self.end_edit.time()),
            "break_start": _from_qtime(self.break_start_edit.time()),
            "break_end": _from_qtime(self.break_end_edit.time()),
            "grace_period_mins": self.grace_spin.value(),
            "late_threshold_mins": self.late_spin.value(),
            "early_out_threshold_mins": self.early_out_spin.value(),
            "overtime_threshold_mins": self.ot_spin.value(),
        }


class ShiftTemplatesView(QWidget):
    """View to list, add, edit, and deactivate Shift Templates."""

    def __init__(self, vm: ShiftTemplatesViewModel, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.setObjectName("ShiftTemplatesView")
        self._setup_ui()
        self._connect_signals()
        self.vm.load_shifts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header_row = QHBoxLayout()
        title = QLabel("Shift Templates")
        title.setObjectName("PageTitle")
        self.add_btn = QPushButton("Add Shift Template")
        self.add_btn.setObjectName("PrimaryButton")
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Start", "End", "Break", "Grace", "Late", "OT", "Actions"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.shifts_loaded.connect(self._on_shifts_loaded)
        self.vm.error_occurred.connect(self._on_error)

    def _on_add_clicked(self):
        dialog = ShiftFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Validation Error", "Shift Name is required.")
                return
            self.vm.create_shift(**data)

    def _on_edit_clicked(self, shift: ShiftTemplateEntity):
        dialog = ShiftFormDialog(self, shift=shift)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Validation Error", "Shift Name is required.")
                return
            self.vm.update_shift(shift.id, **data)

    def _on_deactivate_clicked(self, shift: ShiftTemplateEntity):
        reply = QMessageBox.question(
            self,
            "Deactivate Shift",
            f"Deactivate '{shift.name}'? It will no longer be available for assignment.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.vm.deactivate_shift(shift.id)

    def _on_shifts_loaded(self, shifts: list):
        self.table.setRowCount(0)
        fmt = "%H:%M"
        for s in shifts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            break_str = ""
            if s.break_start and s.break_end:
                break_str = f"{s.break_start.strftime(fmt)}–{s.break_end.strftime(fmt)}"

            name_cell = s.name + (" 🌙" if s.is_overnight else "")
            status_flag = "" if s.is_active else " [Inactive]"
            self.table.setItem(row, 0, QTableWidgetItem(name_cell + status_flag))
            self.table.setItem(row, 1, QTableWidgetItem(s.start_time.strftime(fmt)))
            self.table.setItem(row, 2, QTableWidgetItem(s.end_time.strftime(fmt)))
            self.table.setItem(row, 3, QTableWidgetItem(break_str))
            self.table.setItem(row, 4, QTableWidgetItem(str(s.grace_period_mins)))
            self.table.setItem(row, 5, QTableWidgetItem(str(s.late_threshold_mins)))
            self.table.setItem(row, 6, QTableWidgetItem(str(s.overtime_threshold_mins)))

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.setMinimumWidth(60)
            edit_btn.clicked.connect(lambda _, sh=s: self._on_edit_clicked(sh))

            deact_btn = QPushButton("Deactivate")
            deact_btn.setObjectName("GhostButton")
            deact_btn.setEnabled(s.is_active)
            deact_btn.clicked.connect(lambda _, sh=s: self._on_deactivate_clicked(sh))

            al.addWidget(edit_btn)
            al.addWidget(deact_btn)
            self.table.setCellWidget(row, 7, actions)

        self.table.setColumnWidth(7, 190)

    def _on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
