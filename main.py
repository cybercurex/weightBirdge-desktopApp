# main.py
import sys
from PyQt5.QtWidgets import QApplication
from app import App

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the application
    app_obj = App()
    app_obj.run()
    
    sys.exit(app.exec_())