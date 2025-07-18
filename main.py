import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from Ui_uds_server_main import Ui_MainWindow
from transport import TransportManager
    
try:
    from uds_init import UDSInitManager
except ImportError:
    UDSInitManager = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Initialize managers
        self.transport_manager = None
        self.uds_init_manager = None
        
        # Setup
        self.setup_ui()
        self.init_managers()
        
    def setup_ui(self):
        """Setup basic UI"""
        self.setWindowTitle("UDS Server Emulator")
        self.ui.tracebox.clear()
        self.log("Application started")
        
    def init_managers(self):
        """Initialize all managers"""
        # Initialize transport manager
        if TransportManager:
            self.transport_manager = TransportManager(self.ui)
            self.transport_manager.log_message.connect(self.log)
            
        # Initialize UDS init manager
        if UDSInitManager:
            self.uds_init_manager = UDSInitManager(self.ui)
            self.uds_init_manager.log_message.connect(self.log)
            
            # Connect managers
            if self.transport_manager:
                self.uds_init_manager.set_transport_manager(self.transport_manager)
            
    def log(self, message):
        """Display log message in UI"""
        self.ui.tracebox.append(message)
        
    def closeEvent(self, event):
        """Handle application close"""
        self.log("Application closing...")
        
        # Cleanup managers
        if self.transport_manager:
            self.transport_manager.cleanup()
            
        if self.uds_init_manager:
            self.uds_init_manager.cleanup()
            
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()