"""Biometric Devices View."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class AddDeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Mock Biometric Device")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit("Main Entrance Scanner")
        self.ip_edit = QLineEdit("192.168.1.201")
        self.port_edit = QLineEdit("4370")

        form.addRow("Device Name:", self.name_edit)
        form.addRow("IP Address:", self.ip_edit)
        form.addRow("Port:", self.port_edit)
        layout.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def get_data(self):
        return self.name_edit.text(), self.ip_edit.text(), int(self.port_edit.text() or 4370)


class BiometricDevicesView(QWidget):
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("BiometricDevicesView")
        self._setup_ui()
        self._connect_signals()
        self.vm.load_devices()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Biometric Devices")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Add Device")
        self.add_btn.setObjectName("PrimaryButton")
        self.test_conn_btn = QPushButton("Test Connection")
        self.test_conn_btn.setObjectName("SecondaryButton")
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.test_conn_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "IP Address", "Port", "Model", "Status", "Last Sync"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

    def _connect_signals(self):
        self.vm.devices_loaded.connect(self._render_table)
        self.vm.device_added.connect(self.vm.load_devices)
        self.vm.connection_tested.connect(self._on_connection_tested)
        self.vm.error_occurred.connect(self._on_error)
        
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.test_conn_btn.clicked.connect(self._on_test_conn_clicked)

    def _render_table(self, devices):
        self.table.setRowCount(0)
        for dev in devices:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(dev.id)))
            self.table.setItem(row, 1, QTableWidgetItem(dev.device_name))
            self.table.setItem(row, 2, QTableWidgetItem(dev.ip_address))
            self.table.setItem(row, 3, QTableWidgetItem(str(dev.port)))
            self.table.setItem(row, 4, QTableWidgetItem(dev.model))
            self.table.setItem(row, 5, QTableWidgetItem(dev.status.value))
            
            sync_str = dev.last_sync_at.strftime("%Y-%m-%d %H:%M") if dev.last_sync_at else "Never"
            self.table.setItem(row, 6, QTableWidgetItem(sync_str))

    def _on_add_clicked(self):
        dlg = AddDeviceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, ip, port = dlg.get_data()
            self.vm.add_device(name, ip, port)

    def _on_test_conn_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Select a device first.")
            return
        device_id = int(self.table.item(row, 0).text())
        self.vm.test_connection(device_id)

    def _on_connection_tested(self, success: bool, message: str):
        if success:
            QMessageBox.information(self, "Connection Test", message)
        else:
            QMessageBox.warning(self, "Connection Test", message)
        self.vm.load_devices()

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
