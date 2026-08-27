"""View for managing Positions."""
from __future__ import annotations

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
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from biometric_attendance.app.viewmodels.workforce_vms import PositionsViewModel
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, PositionEntity


class PositionFormDialog(QDialog):
    """Reusable dialog for Add/Edit Position."""

    def __init__(self, parent=None, position=None, departments=None):
        super().__init__(parent)
        self._position = position
        is_edit = position is not None

        self.setWindowTitle("Edit Position" if is_edit else "Add Position")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        lbl_name = QLabel("Name *")
        lbl_name.setObjectName("FormLabel")
        form.addRow(lbl_name, self.name_input)

        self.desc_input = QLineEdit()
        lbl_desc = QLabel("Description")
        lbl_desc.setObjectName("FormLabel")
        form.addRow(lbl_desc, self.desc_input)

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Select Department...", -1)
        for dept in (departments or []):
            self.dept_combo.addItem(dept.name, dept.id)
        lbl_dept = QLabel("Department")
        lbl_dept.setObjectName("FormLabel")
        form.addRow(lbl_dept, self.dept_combo)

        layout.addLayout(form)

        btn_label = "Update Position" if is_edit else "Add Position"
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.save_btn = QPushButton(btn_label)
        self.save_btn.setObjectName("PrimaryButton")
        self.button_box.addButton(self.save_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        if is_edit:
            self.name_input.setText(position.name)
            self.desc_input.setText(position.description or "")
            for i in range(self.dept_combo.count()):
                if self.dept_combo.itemData(i) == position.department_id:
                    self.dept_combo.setCurrentIndex(i)
                    break

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip(),
            "department_id": self.dept_combo.currentData(),
        }


class PositionsView(QWidget):
    """View to list, add, and edit Positions."""

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("PositionsView")
        self._departments = []
        self._setup_ui()
        self._connect_signals()
        self.vm.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Positions")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Position Name")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Select Department...", -1)
        self.add_btn = QPushButton("Add Position")
        self.add_btn.setObjectName("PrimaryButton")
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(self.dept_combo)
        form_layout.addWidget(self.add_btn)
        layout.addLayout(form_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Department", "Description", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(5, 100)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.positions_loaded.connect(self._on_positions_loaded)
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.error_occurred.connect(self._on_error)

    def _on_add_clicked(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        dept_id = self.dept_combo.currentData()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Position Name is required.")
            return
        self.vm.create_position(name, desc, dept_id)
        self.name_input.clear()
        self.desc_input.clear()
        self.dept_combo.setCurrentIndex(0)

    def _on_edit_clicked(self, position):
        dialog = PositionFormDialog(self, position=position, departments=self._departments)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Validation Error", "Position Name is required.")
                return
            self.vm.update_position(position.id, data["name"], data["description"], data["department_id"])

    def _on_departments_loaded(self, departments):
        self._departments = departments
        current_id = self.dept_combo.currentData()
        self.dept_combo.clear()
        self.dept_combo.addItem("Select Department...", -1)
        for dept in departments:
            self.dept_combo.addItem(dept.name, dept.id)
        for i in range(self.dept_combo.count()):
            if self.dept_combo.itemData(i) == current_id:
                self.dept_combo.setCurrentIndex(i)
                break

    def _on_positions_loaded(self, positions):
        self.table.setRowCount(0)
        for pos in positions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(pos.id)))
            self.table.setItem(row, 1, QTableWidgetItem(pos.name))
            self.table.setItem(row, 2, QTableWidgetItem(pos.department_name or "N/A"))
            self.table.setItem(row, 3, QTableWidgetItem(pos.description or ""))
            self.table.setItem(row, 4, QTableWidgetItem("Active" if pos.is_active else "Inactive"))
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.setMinimumWidth(70)
            edit_btn.clicked.connect(lambda checked, p=pos: self._on_edit_clicked(p))
            self.table.setCellWidget(row, 5, edit_btn)
        self.table.setColumnWidth(5, 100)

    def _on_error(self, message):
        QMessageBox.critical(self, "Error", message)
