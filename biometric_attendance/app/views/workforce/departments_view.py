"""View for managing Departments."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

from biometric_attendance.app.viewmodels.workforce_vms import DepartmentsViewModel
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity


class DepartmentFormDialog(QDialog):
    """Reusable dialog for Add/Edit Department."""

    def __init__(self, parent=None, department=None):
        super().__init__(parent)
        self._department = department
        is_edit = department is not None

        self.setWindowTitle("Edit Department" if is_edit else "Add Department")
        self.setMinimumWidth(380)

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

        layout.addLayout(form)

        btn_label = "Update Department" if is_edit else "Add Department"
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.save_btn = QPushButton(btn_label)
        self.save_btn.setObjectName("PrimaryButton")
        self.button_box.addButton(self.save_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        if is_edit:
            self.name_input.setText(department.name)
            self.desc_input.setText(department.description or "")

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip(),
        }


class DepartmentsView(QWidget):
    """View to list, add, and edit Departments."""

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("DepartmentsView")
        self._departments = []
        self._setup_ui()
        self._connect_signals()
        self.vm.load_departments()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Departments")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Department Name")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        self.add_btn = QPushButton("Add Department")
        self.add_btn.setObjectName("PrimaryButton")
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(self.add_btn)
        layout.addLayout(form_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.error_occurred.connect(self._on_error)

    def _on_add_clicked(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Department Name is required.")
            return
        self.vm.create_department(name, desc)
        self.name_input.clear()
        self.desc_input.clear()

    def _on_edit_clicked(self, department):
        dialog = DepartmentFormDialog(self, department=department)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Validation Error", "Department Name is required.")
                return
            self.vm.update_department(department.id, data["name"], data["description"])

    def _on_departments_loaded(self, departments):
        self._departments = departments
        self.table.setRowCount(0)
        for dept in departments:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(dept.id)))
            self.table.setItem(row, 1, QTableWidgetItem(dept.name))
            self.table.setItem(row, 2, QTableWidgetItem(dept.description or ""))
            self.table.setItem(row, 3, QTableWidgetItem("Active" if dept.is_active else "Inactive"))
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.clicked.connect(lambda checked, d=dept: self._on_edit_clicked(d))
            self.table.setCellWidget(row, 4, edit_btn)

    def _on_error(self, message):
        QMessageBox.critical(self, "Error", message)
