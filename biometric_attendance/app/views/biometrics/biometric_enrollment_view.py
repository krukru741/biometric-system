"""Biometric Enrollment View."""


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.core.enums.biometrics import FingerType


class BiometricEnrollmentView(QWidget):
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("BiometricEnrollmentView")
        self._setup_ui()
        self._connect_signals()
        self.vm.load_employees()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Biometric Enrollment")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form = QFormLayout()
        
        self.emp_combo = QComboBox()
        form.addRow("Employee:", self.emp_combo)

        self.finger_combo = QComboBox()
        for f in FingerType:
            self.finger_combo.addItem(f.value, f)
        form.addRow("Finger:", self.finger_combo)

        layout.addLayout(form)

        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Mock Enrollment")
        self.start_btn.setObjectName("PrimaryButton")
        btn_layout.addWidget(self.start_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _connect_signals(self):
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.enrollment_progress.connect(self._on_progress)
        self.vm.enrollment_complete.connect(self._on_complete)
        self.vm.error_occurred.connect(self._on_error)
        self.start_btn.clicked.connect(self._on_start_clicked)

    def _on_employees_loaded(self, employees):
        self.emp_combo.clear()
        for emp in employees:
            self.emp_combo.addItem(f"{emp.full_name} ({emp.employee_id})", emp.id)

    def _on_start_clicked(self):
        emp_id = self.emp_combo.currentData()
        finger = self.finger_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "Validation", "Select an employee.")
            return

        self.start_btn.setEnabled(False)
        self.emp_combo.setEnabled(False)
        self.finger_combo.setEnabled(False)
        self.vm.start_enrollment(emp_id, finger)

    def _on_progress(self, step: int, message: str):
        self.progress_bar.setValue(step)
        self.status_label.setText(message)

    def _on_complete(self):
        self.progress_bar.setValue(5)
        self.status_label.setText("Enrollment successful and template encrypted!")
        self.start_btn.setEnabled(True)
        self.emp_combo.setEnabled(True)
        self.finger_combo.setEnabled(True)
        QMessageBox.information(self, "Success", "Mock fingerprint enrolled successfully.")

    def _on_error(self, message: str):
        self.status_label.setText("Error occurred.")
        self.start_btn.setEnabled(True)
        self.emp_combo.setEnabled(True)
        self.finger_combo.setEnabled(True)
        QMessageBox.critical(self, "Error", message)
