"""View for managing Positions."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from biometric_attendance.app.viewmodels.workforce_vms import PositionsViewModel
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, PositionEntity


class PositionsView(QWidget):
    """View to list and add Positions."""

    def __init__(self, view_model: PositionsViewModel, parent: QWidget | None = None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("PositionsView")
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        self.vm.load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("Positions")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Add Position Form
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

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Department", "Description", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.positions_loaded.connect(self._on_positions_loaded)
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.error_occurred.connect(self._on_error)

    def _on_add_clicked(self) -> None:
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        dept_id = self.dept_combo.currentData()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Position Name is required.")
            return
            
        self.vm.create_position(name, desc, dept_id)
        
        # Clear inputs on success expectation
        self.name_input.clear()
        self.desc_input.clear()
        self.dept_combo.setCurrentIndex(0)

    def _on_departments_loaded(self, departments: list[DepartmentEntity]) -> None:
        self.dept_combo.clear()
        self.dept_combo.addItem("Select Department...", -1)
        for dept in departments:
            self.dept_combo.addItem(dept.name, dept.id)

    def _on_positions_loaded(self, positions: list[PositionEntity]) -> None:
        self.table.setRowCount(0)
        for pos in positions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(pos.id)))
            self.table.setItem(row, 1, QTableWidgetItem(pos.name))
            self.table.setItem(row, 2, QTableWidgetItem(pos.department_name or "N/A"))
            self.table.setItem(row, 3, QTableWidgetItem(pos.description))
            self.table.setItem(row, 4, QTableWidgetItem("Active" if pos.is_active else "Inactive"))

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)
