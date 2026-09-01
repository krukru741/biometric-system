"""View for managing Holidays."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.viewmodels.scheduling_vms import HolidaysViewModel
from biometric_attendance.core.dtos.scheduling_dtos import HolidayEntity
from biometric_attendance.core.enums.scheduling import HolidayType


class HolidayFormDialog(QDialog):
    """Add / Edit Holiday dialog."""

    def __init__(self, parent=None, holiday: HolidayEntity | None = None):
        super().__init__(parent)
        is_edit = holiday is not None
        self.setWindowTitle("Edit Holiday" if is_edit else "Add Holiday")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        lbl = QLabel("Name *")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.name_input)

        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        lbl = QLabel("Date *")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.date_edit)

        self.type_combo = QComboBox()
        for ht in HolidayType:
            self.type_combo.addItem(ht.value, ht)
        lbl = QLabel("Type")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.type_combo)

        self.paid_check = QCheckBox()
        self.paid_check.setChecked(True)
        lbl = QLabel("Paid")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.paid_check)

        self.notes_input = QLineEdit()
        lbl = QLabel("Notes")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.notes_input)

        layout.addLayout(form)

        btn_label = "Update Holiday" if is_edit else "Add Holiday"
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.save_btn = QPushButton(btn_label)
        self.save_btn.setObjectName("PrimaryButton")
        self.button_box.addButton(self.save_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        if is_edit:
            self.name_input.setText(holiday.name)
            self.date_edit.setDate(QDate(holiday.date.year, holiday.date.month, holiday.date.day))
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == holiday.holiday_type:
                    self.type_combo.setCurrentIndex(i)
                    break
            self.paid_check.setChecked(holiday.is_paid)
            self.notes_input.setText(holiday.notes or "")

    def get_data(self) -> dict:
        qd = self.date_edit.date()
        return {
            "name": self.name_input.text().strip(),
            "date": dt.date(qd.year(), qd.month(), qd.day()),
            "holiday_type": self.type_combo.currentData(),
            "is_paid": self.paid_check.isChecked(),
            "notes": self.notes_input.text().strip() or None,
        }


class HolidaysView(QWidget):
    """View to manage Holidays with year filter."""

    def __init__(self, vm: HolidaysViewModel, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.setObjectName("HolidaysView")
        self._current_year = dt.date.today().year
        self._setup_ui()
        self._connect_signals()
        self.vm.load_holidays(self._current_year)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header_row = QHBoxLayout()
        title = QLabel("Holidays")
        title.setObjectName("PageTitle")
        self.add_btn = QPushButton("Add Holiday")
        self.add_btn.setObjectName("PrimaryButton")
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        lbl = QLabel("Year:")
        lbl.setObjectName("FormLabel")
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(self._current_year)
        self.year_spin.setFixedWidth(90)
        filter_row.addWidget(lbl)
        filter_row.addWidget(self.year_spin)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Name", "Type", "Paid", "Notes", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(5, 240)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.year_spin.valueChanged.connect(lambda y: self.vm.load_holidays(y))
        self.vm.holidays_loaded.connect(self._on_holidays_loaded)
        self.vm.error_occurred.connect(self._on_error)

    def _on_add_clicked(self):
        dialog = HolidayFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Validation Error", "Holiday Name is required.")
                return
            self.vm.create_holiday(**data)

    def _on_edit_clicked(self, holiday: HolidayEntity):
        dialog = HolidayFormDialog(self, holiday=holiday)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Validation Error", "Holiday Name is required.")
                return
            self.vm.update_holiday(holiday.id, **data)

    def _on_delete_clicked(self, holiday: HolidayEntity):
        reply = QMessageBox.question(
            self,
            "Delete Holiday",
            f"Delete '{holiday.name}' ({holiday.date})? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.vm.delete_holiday(holiday.id)

    def _on_holidays_loaded(self, holidays: list):
        self.table.setRowCount(0)
        for h in holidays:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(h.date)))
            self.table.setItem(row, 1, QTableWidgetItem(h.name))
            self.table.setItem(row, 2, QTableWidgetItem(h.holiday_type.value))
            self.table.setItem(row, 3, QTableWidgetItem("Yes" if h.is_paid else "No"))
            self.table.setItem(row, 4, QTableWidgetItem(h.notes or ""))

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            from biometric_attendance.app.styles.icons import icon
            from biometric_attendance.app.styles import theme
            
            edit_btn = QPushButton("Edit")
            edit_btn.setIcon(icon("edit", color=theme.PRIMARY, size=16))
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.setMinimumWidth(85)
            edit_btn.setStyleSheet("text-align: center; padding-left: 10px; padding-right: 10px;")
            edit_btn.clicked.connect(lambda _, hol=h: self._on_edit_clicked(hol))

            del_btn = QPushButton("Delete")
            del_btn.setIcon(icon("delete", color=theme.TEXT_SECONDARY, size=16))
            del_btn.setObjectName("GhostButton")
            del_btn.setMinimumWidth(100)
            del_btn.setStyleSheet("text-align: center; padding-left: 10px; padding-right: 10px;")
            del_btn.clicked.connect(lambda _, hol=h: self._on_delete_clicked(hol))

            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            self.table.setCellWidget(row, 5, actions)

        self.table.setColumnWidth(5, 240)

    def _on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
