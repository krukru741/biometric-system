"""Biometric Sync View."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BiometricSyncView(QWidget):
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("BiometricSyncView")
        self._setup_ui()
        self._connect_signals()
        self.vm.load_devices()
        self.vm.load_recent_logs()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Biometric Synchronization")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form = QFormLayout()
        self.device_combo = QComboBox()
        form.addRow("Target Device:", self.device_combo)
        layout.addLayout(form)

        actions_layout = QHBoxLayout()
        self.pull_btn = QPushButton("Pull Attendance Logs")
        self.pull_btn.setObjectName("PrimaryButton")
        self.push_btn = QPushButton("Push Users to Device")
        self.push_btn.setObjectName("SecondaryButton")
        
        self.simulate_fail_cb = QCheckBox("Simulate Failure (Push)")

        actions_layout.addWidget(self.pull_btn)
        actions_layout.addWidget(self.push_btn)
        actions_layout.addWidget(self.simulate_fail_cb)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        subtitle = QLabel("Recent Device Logs")
        subtitle.setObjectName("SubheadingLabel")
        layout.addWidget(subtitle)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Log Type", "Success", "Message", "Raw Payload"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

    def _connect_signals(self):
        self.vm.devices_loaded.connect(self._on_devices_loaded)
        self.vm.logs_loaded.connect(self._render_logs)
        self.vm.sync_complete.connect(self._on_sync_complete)
        self.vm.error_occurred.connect(self._on_error)
        
        self.pull_btn.clicked.connect(self._on_pull_clicked)
        self.push_btn.clicked.connect(self._on_push_clicked)

    def _on_devices_loaded(self, devices):
        self.device_combo.clear()
        for dev in devices:
            self.device_combo.addItem(f"{dev.device_name} ({dev.ip_address})", dev.id)

    def _render_logs(self, logs):
        self.table.setRowCount(0)
        for log in logs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(log.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(row, 1, QTableWidgetItem(log.log_type.value))
            self.table.setItem(row, 2, QTableWidgetItem("Yes" if log.success else "No"))
            self.table.setItem(row, 3, QTableWidgetItem(log.message))
            self.table.setItem(row, 4, QTableWidgetItem(log.raw_payload or ""))

    def _on_pull_clicked(self):
        device_id = self.device_combo.currentData()
        if not device_id:
            QMessageBox.warning(self, "Validation", "Select a device first.")
            return
        self.vm.pull_logs(device_id)

    def _on_push_clicked(self):
        device_id = self.device_combo.currentData()
        if not device_id:
            QMessageBox.warning(self, "Validation", "Select a device first.")
            return
        self.vm.push_users(device_id, self.simulate_fail_cb.isChecked())

    def _on_sync_complete(self, message: str):
        QMessageBox.information(self, "Sync Complete", message)

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
