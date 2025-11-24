# Updated ui/main_window.py with fixed Actions column layout
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from ui.components.styled_components import RoundedButton, StatusIndicator, LogPanel
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.api_settings_dialog import ApiSettingsDialog

class MainWindow(QMainWindow):
    def __init__(self, service_manager, logger, config, parent=None):
        super().__init__(parent)
        self.service_manager = service_manager
        self.logger = logger
        self.config = config
        self.setup_ui()
        self.show_settings_dialog = self.show_settings_dialog_with_update

    def show_settings_dialog_with_update(self, row):
        dialog = SettingsDialog(self.config, self)
        dialog.settings_updated.connect(self.handle_settings_update)
        dialog.exec_()

    def handle_settings_update(self,row, service_name, settings):
        # Apply settings to config
        for key, value in settings.items():
            setattr(self.config, key.upper(), value)

        # Update UI port display and restart services if needed
        if service_name == "Serial Service":
            self.services_table.item(row, 1).setText(str(settings.get('default_com_port', 'COM3')))
            if self.service_manager.get_service('serial'):
                self.service_manager.stop('serial')
                self.service_manager.start('serial')

        elif service_name == "API Service":
            self.services_table.item(row, 1).setText(str(settings.get('flask_port', '5000')))
            if self.service_manager.get_service('api'):
                self.service_manager.stop('api')
                self.service_manager.start('api')

        self.logger.info(f"Updated settings for {service_name}")

    def setup_ui(self):
        self.setWindowTitle("Weighbridge Control Panel")
        self.setMinimumSize(900, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel("Weighbridge Control Panel")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(header)

        # Services table
        self.setup_services_table()
        layout.addWidget(self.services_table)

        # Log panel
        log_label = QLabel("Activity Log")
        log_label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(log_label)

        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel, stretch=1)

        # Apply window stylesheet
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                gridline-color: #eee;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
            }
        """)

    def setup_services_table(self):
        self.services_table = QTableWidget(0, 4)
        self.services_table.setHorizontalHeaderLabels(["Service", "Port", "Status", "Actions"])
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.setShowGrid(False)
        self.services_table.setAlternatingRowColors(True)

        # Correct column sizing
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # Add services
        self.add_service("Serial Service", "COM3", False)
        self.add_service("API Service", "5000", False)

    def add_service(self, name, port, is_running):
        row = self.services_table.rowCount()
        self.services_table.insertRow(row)

        # Column 0: Service Name
        item = QTableWidgetItem(name)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.services_table.setItem(row, 0, item)

        # Column 1: Port
        port_item = QTableWidgetItem(str(port))
        port_item.setFlags(port_item.flags() ^ Qt.ItemIsEditable)
        self.services_table.setItem(row, 1, port_item)

        # Column 2: Status Indicator
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignCenter)

        status_indicator = StatusIndicator()
        status_indicator.set_status(is_running)
        status_layout.addWidget(status_indicator)
        self.services_table.setCellWidget(row, 2, status_widget)

        # Column 3: Actions
        actions_widget = QWidget()
        actions_widget.setAttribute(Qt.WA_TranslucentBackground)
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 5, 5, 5)
        actions_layout.setSpacing(6)

        # Buttons
        start_btn = RoundedButton("Start")
        stop_btn = RoundedButton("Stop")
        settings_btn = RoundedButton("⚙️")

        start_btn.setFixedWidth(70)
        stop_btn.setFixedWidth(70)
        settings_btn.setFixedSize(32, 32)

        stop_btn.setEnabled(is_running)
        start_btn.setEnabled(not is_running)

        actions_layout.addWidget(start_btn)
        actions_layout.addWidget(stop_btn)
        actions_layout.addWidget(settings_btn)

        # Prevent row expansion
        actions_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.services_table.setCellWidget(row, 3, actions_widget)

        # Store & connect
        start_btn.clicked.connect(lambda: self.start_service(row))
        stop_btn.clicked.connect(lambda: self.stop_service(row))
        settings_btn.clicked.connect(lambda checked, r=row: self.show_settings_dialog(r))

    def setup_connections(self):
        self.logger.set_ui_callback(self.append_log)

    def append_log(self, level, message):
        self.log_panel.append(f"[{level}] {message}")

    def start_service(self, row):
        self.update_service_status(row, True)

    def stop_service(self, row):
        self.update_service_status(row, False)

    def update_service_status(self, row, is_running):
        status_indicator = self.services_table.cellWidget(row, 2).findChild(StatusIndicator)
        status_indicator.set_status(is_running)

        actions_widget = self.services_table.cellWidget(row, 3)
        start_btn = actions_widget.layout().itemAt(0).widget()
        stop_btn = actions_widget.layout().itemAt(1).widget()

        start_btn.setEnabled(not is_running)
        stop_btn.setEnabled(is_running)

    def show_settings_dialog(self, row):
        """Show settings dialog for the selected service"""
        service_name = self.services_table.item(row, 0).text()

        dialog = SettingsDialog(self.config, self)
        result = dialog.exec_()
        if result != QDialog.Accepted:
            return

        new_settings = dialog.get_settings()  # ensure defined only on accept

        # Apply settings to config
        for key, value in new_settings.items():
            setattr(self.config, key.upper(), value)

        # Update UI port display and restart services if needed
        if service_name == "Serial Service":
            self.services_table.item(row, 1).setText(str(new_settings.get('default_com_port', 'COM3')))
            if self.service_manager.get_service('serial'):
                self.service_manager.stop('serial')
                self.service_manager.start('serial')

        elif service_name == "API Service":
            self.services_table.item(row, 1).setText(str(new_settings.get('flask_port', '5000')))
            if self.service_manager.get_service('api'):
                self.service_manager.stop('api')
                self.service_manager.start('api')

        self.logger.info(f"Updated settings for {service_name}")
