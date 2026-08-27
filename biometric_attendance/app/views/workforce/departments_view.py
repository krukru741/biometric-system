"""View for managing Departments."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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


class DepartmentsView(QWidget):
    """View to list and add Departments."""

    def __init__(self, view_model: DepartmentsViewModel, parent: QWidget | None = None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("DepartmentsView")
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        self.vm.load_departments()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("Departments")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Add Department Form
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

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.error_occurred.connect(self._on_error)

    def _on_add_clicked(self) -> None:
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Department Name is required.")
            return
            
        self.vm.create_department(name, desc)
        
        # Clear inputs on success expectation
        self.name_input.clear()
        self.desc_input.clear()

    def _on_departments_loaded(self, departments: list[DepartmentEntity]) -> None:
        self.table.setRowCount(0)
        for dept in departments:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(dept.id)))
            self.table.setItem(row, 1, QTableWidgetItem(dept.name))
            self.table.setItem(row, 2, QTableWidgetItem(dept.description))
            self.table.setItem(row, 3, QTableWidgetItem("Active" if dept.is_active else "Inactive"))

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)
