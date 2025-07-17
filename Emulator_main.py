import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from Ui_uds_server_main import Ui_MainWindow

# Import server modules
try:
    from doip_server import DoIPServer
except ImportError:
    DoIPServer = None
    
try:
    from docan_server import DoCANServer
except ImportError:
    DoCANServer = None

class UDSServerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Initialize server instances
        self.doip_server = None
        self.docan_server = None
        self.current_server = None
        self.config_file_path = None
        
        # Setup UI
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("UDS Server Emulator")
        self.ui.config_file_label.setText("No config file selected")
        
        # Populate network interfaces for DoIP
        self.populate_network_interfaces()
        
        # Populate CAN interfaces for DoCAN
        self.populate_can_interfaces()
        
    def connect_signals(self):
        """Connect UI signals to slots"""
        self.ui.config_file.clicked.connect(self.select_config_file)
        self.ui.init_server.clicked.connect(self.init_server)
        
    def populate_network_interfaces(self):
        """Populate network interface dropdown for DoIP"""
        # Add sample network interfaces
        interfaces = ["eth0 - 192.168.1.100", "wlan0 - 192.168.0.50"]
        self.ui.Net_Select.addItems(interfaces)
        
    def populate_can_interfaces(self):
        """Populate CAN interface dropdown for DoCAN"""
        # Add sample CAN interfaces
        interfaces = ["can0", "can1", "vcan0"]
        self.ui.comboBox.addItems(interfaces)
        
    def select_config_file(self):
        """Open file dialog to select configuration file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Configuration File", 
            "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.config_file_path = file_path
            self.ui.config_file_label.setText(os.path.basename(file_path))
            self.log_message(f"Configuration file selected: {file_path}")
            
    def scan_can_devices(self):
        """Scan for available CAN devices"""
        self.log_message("Scanning for CAN devices...")
        # This would be implemented in the DoCANServer module
        if DoCANServer:
            try:
                devices = DoCANServer.scan_devices()
                self.ui.comboBox.clear()
                self.ui.comboBox.addItems(devices)
                self.log_message(f"Found {len(devices)} CAN devices")
            except Exception as e:
                self.log_message(f"Error scanning CAN devices: {str(e)}")
        else:
            self.log_message("DoCAN server module not available")
            
    def init_server(self):
        """Initialize the selected server type"""
        current_tab = self.ui.UDS_Server.currentIndex()
        
        if current_tab == 0:  # DoIP tab
            self.init_doip_server()
        elif current_tab == 1:  # DoCAN tab
            self.init_docan_server()
            
    def init_doip_server(self):
        """Initialize DoIP server"""
        if not DoIPServer:
            self.log_message("DoIP server module not available")
            return
            
        try:
            # Stop existing server if running
            if self.current_server:
                self.current_server.stop()
                
            # Get selected network interface
            interface = self.ui.Net_Select.currentText()
            
            # Create and configure DoIP server
            self.doip_server = DoIPServer(
                interface=interface,
                config_file=self.config_file_path
            )
            
            # Connect server signals
            self.doip_server.message_received.connect(self.on_message_received)
            self.doip_server.status_changed.connect(self.on_status_changed)
            
            # Start server
            self.doip_server.start()
            self.current_server = self.doip_server
            
            self.log_message(f"DoIP server initialized on {interface}")
            
        except Exception as e:
            self.log_message(f"Error initializing DoIP server: {str(e)}")
            
    def init_docan_server(self):
        """Initialize DoCAN server"""
        if not DoCANServer:
            self.log_message("DoCAN server module not available")
            return
            
        try:
            # Stop existing server if running
            if self.current_server:
                self.current_server.stop()
                
            # Get selected CAN interface and settings
            interface = self.ui.comboBox.currentText()
            can_fd = self.ui.checkBox.isChecked()
            
            # Create and configure DoCAN server
            self.docan_server = DoCANServer(
                interface=interface,
                can_fd=can_fd,
                config_file=self.config_file_path
            )
            
            # Connect server signals
            self.docan_server.message_received.connect(self.on_message_received)
            self.docan_server.status_changed.connect(self.on_status_changed)
            
            # Start server
            self.docan_server.start()
            self.current_server = self.docan_server
            
            self.log_message(f"DoCAN server initialized on {interface} (CAN-FD: {can_fd})")
            
        except Exception as e:
            self.log_message(f"Error initializing DoCAN server: {str(e)}")
            
    def on_message_received(self, message):
        """Handle received UDS messages"""
        self.log_message(f"Received: {message}")
        
    def on_status_changed(self, status):
        """Handle server status changes"""
        self.log_message(f"Server status: {status}")
        
    def log_message(self, message):
        """Add message to the log browser"""
        self.ui.textBrowser.append(message)
        
    def closeEvent(self, event):
        """Handle application close event"""
        if self.current_server:
            self.current_server.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = UDSServerMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()