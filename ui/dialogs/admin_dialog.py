from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QGroupBox, QCheckBox, QMessageBox, QFileDialog,
    QHeaderView, QProgressBar, QTextEdit, QSplitter, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QPixmap
import os
import json
import platform
import psutil
import sqlite3
from datetime import datetime
import shutil

class AdminDialog(QDialog):
    def __init__(self, parent=None, db_path=None, logger=None):
        super().__init__(parent)
        self.db_path = db_path or 'weighbridge_local.db'
        self.logger = logger
        self.setWindowTitle("Administration Panel")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        self.load_system_info()
        self.load_users()
        self.load_database_stats()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        
        # User Management Tab
        user_tab = self.create_user_management_tab()
        system_tab = self.create_system_tab()
        backup_tab = self.create_backup_tab()
        logs_tab = self.create_logs_tab()
        
        tabs.addTab(user_tab, "User Management")
        tabs.addTab(system_tab, "System Info")
        tabs.addTab(backup_tab, "Backup & Restore")
        tabs.addTab(logs_tab, "Logs")
        
        main_layout.addWidget(tabs)
        
        # Status Bar
        self.status_bar = QLabel("Ready")
        main_layout.addWidget(self.status_bar)
        
    def create_user_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # User list table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["Username", "Role", "Last Login", "Status"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # User form
        form = QFormLayout()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Admin", "Operator", "Viewer"])
        
        form.addRow("Username:", self.username_edit)
        form.addRow("Password:", self.password_edit)
        form.addRow("Role:", self.role_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add User")
        self.edit_btn = QPushButton("Edit User")
        self.delete_btn = QPushButton("Delete User")
        self.reset_pwd_btn = QPushButton("Reset Password")
        
        self.add_btn.clicked.connect(self.add_user)
        self.edit_btn.clicked.connect(self.edit_user)
        self.delete_btn.clicked.connect(self.delete_user)
        self.reset_pwd_btn.clicked.connect(self.reset_password)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.reset_pwd_btn)
        
        layout.addWidget(QLabel("User Management"))
        layout.addWidget(self.user_table)
        layout.addLayout(form)
        layout.addLayout(btn_layout)
        
        return tab
    
    def create_system_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Info
        sys_group = QGroupBox("System Information")
        sys_layout = QFormLayout()
        
        self.os_label = QLabel()
        self.python_version = QLabel()
        self.cpu_usage = QProgressBar()
        self.memory_usage = QProgressBar()
        self.disk_usage = QProgressBar()
        
        sys_layout.addRow("Operating System:", self.os_label)
        sys_layout.addRow("Python Version:", self.python_version)
        sys_layout.addRow("CPU Usage:", self.cpu_usage)
        sys_layout.addRow("Memory Usage:", self.memory_usage)
        sys_layout.addRow("Disk Usage:", self.disk_usage)
        sys_group.setLayout(sys_layout)
        
        # Database Info
        db_group = QGroupBox("Database Information")
        db_layout = QFormLayout()
        
        self.db_size = QLabel()
        self.record_count = QLabel()
        self.last_backup = QLabel()
        
        db_layout.addRow("Database Size:", self.db_size)
        db_layout.addRow("Total Records:", self.record_count)
        db_layout.addRow("Last Backup:", self.last_backup)
        db_group.setLayout(db_layout)
        
        layout.addWidget(sys_group)
        layout.addWidget(db_group)
        
        # Update timer for system stats
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_system_stats)
        self.stats_timer.start(2000)  # Update every 2 seconds
        
        return tab
    
    def create_backup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Backup controls
        backup_group = QGroupBox("Backup")
        backup_layout = QVBoxLayout()
        
        self.backup_btn = QPushButton("Create Backup")
        self.backup_btn.clicked.connect(self.create_backup)
        
        backup_layout.addWidget(self.backup_btn)
        backup_group.setLayout(backup_layout)
        
        # Restore controls
        restore_group = QGroupBox("Restore")
        restore_layout = QVBoxLayout()
        
        self.restore_btn = QPushButton("Restore from Backup")
        self.restore_btn.clicked.connect(self.restore_backup)
        
        restore_layout.addWidget(self.restore_btn)
        restore_group.setLayout(restore_layout)
        
        layout.addWidget(backup_group)
        layout.addWidget(restore_group)
        layout.addStretch()
        
        return tab
    
    def create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFontFamily("Courier")
        
        btn_layout = QHBoxLayout()
        self.refresh_logs_btn = QPushButton("Refresh")
        self.clear_logs_btn = QPushButton("Clear Logs")
        self.export_logs_btn = QPushButton("Export Logs...")
        
        self.refresh_logs_btn.clicked.connect(self.refresh_logs)
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.export_logs_btn.clicked.connect(self.export_logs)
        
        btn_layout.addWidget(self.refresh_logs_btn)
        btn_layout.addWidget(self.clear_logs_btn)
        btn_layout.addWidget(self.export_logs_btn)
        btn_layout.addStretch()
        
        layout.addWidget(QLabel("Application Logs"))
        layout.addWidget(self.log_view)
        layout.addLayout(btn_layout)
        
        # Load initial logs
        self.refresh_logs()
        
        return tab
    
    # User Management Methods
    def load_users(self):
        # TODO: Load users from database
        users = [
            {"username": "admin", "role": "Admin", "last_login": "2023-11-22 15:30", "status": "Active"},
            {"username": "operator1", "role": "Operator", "last_login": "2023-11-22 14:45", "status": "Active"},
        ]
        
        self.user_table.setRowCount(len(users))
        for i, user in enumerate(users):
            self.user_table.setItem(i, 0, QTableWidgetItem(user["username"]))
            self.user_table.setItem(i, 1, QTableWidgetItem(user["role"]))
            self.user_table.setItem(i, 2, QTableWidgetItem(user["last_login"]))
            self.user_table.setItem(i, 3, QTableWidgetItem(user["status"]))
    
    def add_user(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        role = self.role_combo.currentText()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required")
            return
            
        # TODO: Add user to database
        self.status_bar.setText(f"Added user: {username}")
        self.load_users()
        self.clear_user_form()
    
    def edit_user(self):
        # TODO: Implement user editing
        pass
    
    def delete_user(self):
        selected = self.user_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "Please select a user to delete")
            return
            
        username = selected[0].text()
        if QMessageBox.question(self, "Confirm Delete", 
                              f"Are you sure you want to delete user '{username}'?",
                              QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # TODO: Delete user from database
            self.status_bar.setText(f"Deleted user: {username}")
            self.load_users()
    
    def reset_password(self):
        selected = self.user_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "Please select a user")
            return
            
        username = selected[0].text()
        new_password, ok = QInputDialog.getText(
            self, "Reset Password", 
            f"Enter new password for {username}:",
            QLineEdit.Password
        )
        
        if ok and new_password:
            # TODO: Update password in database
            self.status_bar.setText(f"Password reset for user: {username}")
    
    def clear_user_form(self):
        self.username_edit.clear()
        self.password_edit.clear()
        self.role_combo.setCurrentIndex(0)
    
    # System Methods
    def load_system_info(self):
        # System information
        self.os_label.setText(f"{platform.system()} {platform.release()} ({platform.machine()})")
        self.python_version.setText(platform.python_version())
        
        # Initial stats
        self.update_system_stats()
    
    def update_system_stats(self):
        # CPU Usage
        self.cpu_usage.setValue(int(psutil.cpu_percent()))
        
        # Memory Usage
        memory = psutil.virtual_memory()
        self.memory_usage.setValue(int(memory.percent))
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        self.disk_usage.setValue(int(disk.percent))
    
    def load_database_stats(self):
        try:
            # Get database size
            if os.path.exists(self.db_path):
                size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
                self.db_size.setText(f"{size:.2f} MB")
                
                # Get record count
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM readings")
                count = cursor.fetchone()[0]
                self.record_count.setText(str(count))
                conn.close()
            
            # Get last backup time
            backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
                if backups:
                    latest = max(backups, key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
                    mtime = os.path.getmtime(os.path.join(backup_dir, latest))
                    self.last_backup.setText(datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'))
                    return
            
            self.last_backup.setText("Never")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading database stats: {str(e)}")
    
    # Backup/Restore Methods
    def create_backup(self):
        try:
            backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"weighbridge_backup_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_path)
            
            self.status_bar.setText(f"Backup created: {os.path.basename(backup_path)}")
            self.load_database_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", f"Failed to create backup:\n{str(e)}")
    
    def restore_backup(self):
        try:
            backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select Backup File", 
                backup_dir,
                "Database Files (*.db);;All Files (*)"
            )
            
            if filename:
                if QMessageBox.question(
                    self, "Confirm Restore",
                    "WARNING: This will overwrite the current database. Continue?",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.Yes:
                    # Create a backup before restoring
                    self.create_backup()
                    
                    # Restore the selected backup
                    shutil.copy2(filename, self.db_path)
                    
                    self.status_bar.setText("Database restored successfully")
                    self.load_database_stats()
        
        except Exception as e:
            QMessageBox.critical(self, "Restore Failed", f"Failed to restore backup:\n{str(e)}")
    
    # Logs Methods
    def refresh_logs(self):
        # TODO: Load logs from file or database
        self.log_view.clear()
        self.log_view.append("2023-11-22 15:30:45 - INFO: Application started")
        self.log_view.append("2023-11-22 15:31:10 - INFO: Connected to scale")
        self.log_view.append("2023-11-22 15:35:22 - WARNING: Scale connection lost, retrying...")
        self.log_view.append("2023-11-22 15:35:25 - INFO: Scale reconnected")
    
    def clear_logs(self):
        if QMessageBox.question(
            self, "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            # TODO: Clear logs from file or database
            self.log_view.clear()
            self.status_bar.setText("Logs cleared")
    
    def export_logs(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Logs",
            f"weighbridge_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_view.toPlainText())
                self.status_bar.setText(f"Logs exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export logs:\n{str(e)}")
    
    def closeEvent(self, event):
        # Clean up resources
        if hasattr(self, 'stats_timer') and self.stats_timer.isActive():
            self.stats_timer.stop()
        event.accept()