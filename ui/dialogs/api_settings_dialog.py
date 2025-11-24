# ui/dialogs/api_settings_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from ui.components.styled_components import RoundedButton

class ApiSettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        
    def setup_ui(self):
        # ... rest of your dialog implementation ...
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        form = QFormLayout()
        form.setSpacing(15)
        
        self.api_port_edit = QLineEdit()
        form.addRow(QLabel("API Port:"), self.api_port_edit)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = RoundedButton("Save")
        self.cancel_btn = RoundedButton("Cancel")
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.api_port_edit.setText(str(self.config.get('flask_port', 5000)))
        
        self.setLayout(layout)
        
        self.setWindowTitle("API Settings")
        self.setMinimumWidth(400)
        
        self.api_port_edit.setValidator(QtGui.QIntValidator(0, 65535))
        
        self.api_port_edit.textChanged.connect(self.validate_api_port)
        
        self.api_port_edit.editingFinished.connect(self.validate_api_port)
        
        self.api_port_edit.textEdited.connect(self.enable_save_btn)
        
        self.save_btn.setEnabled(False)
        
    def validate_api_port(self):
        try:
            port = int(self.api_port_edit.text())
            self.save_btn.setEnabled(True)
        except ValueError:
            self.save_btn.setEnabled(False)
            
    def enable_save_btn(self):
        self.save_btn.setEnabled(True)
        
    def get_settings(self):
        return {'flask_port': int(self.api_port_edit.text())}
        
    def load_settings(self):
        self.api_port_edit.setText(str(self.config.get('flask_port', 5000)))
        