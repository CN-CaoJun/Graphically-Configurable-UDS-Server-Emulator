import socket
import netifaces
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox
from typing import Dict, Any, Optional

class TransportManager(QObject):
    # Signal definitions
    log_message = Signal(str)
    transport_ready = Signal(object)
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.current_transport = None
        
        # Transport information storage
        self.transport_info = self.create_empty_transport_info()
        
        # Connect UI signals
        self.setup_connections()
        
        # Initialize UI
        self.init_ui()
        
    def create_empty_transport_info(self) -> Dict[str, Any]:
        """Create empty transport information structure"""
        return {
            'transport_type': None,  # 'CAN' or 'ETH'
            'can_info': {
                'device_type': None,     # CAN device type (e.g., 'socketcan', 'pcan', 'kvaser')
                'channel': None,         # CAN channel (e.g., 'can0', 'PCAN_USBBUS1')
                'client_addr': None,     # Client CAN ID
                'server_addr': None,     # Server CAN ID
                'is_fd': False,          # CAN-FD support flag
                'bitrate': 500000        # CAN bitrate
            },
            'eth_info': {
                'ip_address': None,      # Network interface IP address
                'interface_name': None,  # Network interface name
                'client_addr': None,     # Client logical address
                'server_addr': None,     # Server logical address
                'port': 13400           # DoIP port (default 13400)
            }
        }
        
    def update_transport_info_can(self, device_type: str, channel: str, 
                                 client_addr: str, server_addr: str, is_fd: bool) -> None:
        """Update transport info for CAN configuration"""
        self.transport_info['transport_type'] = 'CAN'
        self.transport_info['can_info'].update({
            'device_type': device_type,
            'channel': channel,
            'client_addr': client_addr,
            'server_addr': server_addr,
            'is_fd': is_fd
        })
        
        self.log_message.emit("=== CAN Transport Info Updated ===")
        self.log_message.emit(f"Transport Type: {self.transport_info['transport_type']}")
        self.log_message.emit(f"Device Type: {device_type}")
        self.log_message.emit(f"Channel: {channel}")
        self.log_message.emit(f"Client Address: {client_addr}")
        self.log_message.emit(f"Server Address: {server_addr}")
        self.log_message.emit(f"CAN-FD Enabled: {is_fd}")
        self.log_message.emit("=================================")
        
    def update_transport_info_eth(self, ip_address: str, interface_name: str,
                                 client_addr: str, server_addr: str, port: int = 13400) -> None:
        """Update transport info for Ethernet/DoIP configuration"""
        self.transport_info['transport_type'] = 'ETH'
        self.transport_info['eth_info'].update({
            'ip_address': ip_address,
            'interface_name': interface_name,
            'client_addr': client_addr,
            'server_addr': server_addr,
            'port': port
        })
        
        self.log_message.emit("=== ETH Transport Info Updated ===")
        self.log_message.emit(f"Transport Type: {self.transport_info['transport_type']}")
        self.log_message.emit(f"IP Address: {ip_address}")
        self.log_message.emit(f"Interface Name: {interface_name}")
        self.log_message.emit(f"Client Address: {client_addr}")
        self.log_message.emit(f"Server Address: {server_addr}")
        self.log_message.emit(f"Port: {port}")
        self.log_message.emit("=================================")
        
    def get_transport_info(self) -> Dict[str, Any]:
        """Get current transport information"""
        return self.transport_info.copy()
        
    def setup_connections(self):
        """Setup UI signal connections"""
        # Monitor tab switching
        self.ui.transport_abstract.currentChanged.connect(self.on_tab_changed)
        
        # Monitor network interface selection changes
        self.ui.Net_Select.currentTextChanged.connect(self.on_net_select_changed)
        
        # Monitor CAN interface selection changes
        self.ui.comboBox.currentTextChanged.connect(self.on_can_select_changed)
        
        # Monitor address field changes
        self.ui.doip_server_addr.textChanged.connect(self.on_doip_addr_changed)
        self.ui.doip_client_addr.textChanged.connect(self.on_doip_addr_changed)
        self.ui.CAN_Server_Addr.textChanged.connect(self.on_can_addr_changed)
        self.ui.CAN_CLient_Addr.textChanged.connect(self.on_can_addr_changed)
        
        # Monitor CAN-FD checkbox
        self.ui.is_FD.toggled.connect(self.on_can_fd_changed)
        
    def on_net_select_changed(self, selected_text: str) -> None:
        """Handle network interface selection change"""
        if not selected_text or selected_text == "No available interfaces":
            return
            
        try:
            # Extract IP address from interface info
            ip_address = "N/A"
            interface_name = selected_text
            if "(" in selected_text and ")" in selected_text:
                parts = selected_text.split("(")
                interface_name = parts[0].strip()
                ip_address = parts[1].split(")")[0]
                
            # Get current addresses
            server_addr = self.ui.doip_server_addr.text() or "0x0040"
            client_addr = self.ui.doip_client_addr.text() or "0x0E80"
            
            # Update transport info
            self.update_transport_info_eth(ip_address, interface_name, client_addr, server_addr)
            
        except Exception as e:
            self.log_message.emit(f"Error handling network interface selection: {str(e)}")
            
    def on_can_select_changed(self, selected_text: str) -> None:
        """Handle CAN interface selection change"""
        if not selected_text:
            return
            
        try:
            # Get current addresses and settings
            server_addr = self.ui.CAN_Server_Addr.text() or "0x0040"
            client_addr = self.ui.CAN_CLient_Addr.text() or "0x0E80"
            is_fd = self.ui.is_FD.isChecked()
            
            # Determine device type based on interface name
            device_type = "socketcan"  # Default
            if "PCAN" in selected_text.upper():
                device_type = "pcan"
            elif "KVASER" in selected_text.upper():
                device_type = "kvaser"
                
            # Update transport info
            self.update_transport_info_can(device_type, selected_text, client_addr, server_addr, is_fd)
            
        except Exception as e:
            self.log_message.emit(f"Error handling CAN interface selection: {str(e)}")
            
    def on_doip_addr_changed(self) -> None:
        """Handle DoIP address field changes"""
        if self.is_doip_mode():
            current_text = self.ui.Net_Select.currentText()
            if current_text:
                self.on_net_select_changed(current_text)
                
    def on_can_addr_changed(self) -> None:
        """Handle CAN address field changes"""
        if self.is_docan_mode():
            current_text = self.ui.comboBox.currentText()
            if current_text:
                self.on_can_select_changed(current_text)
                
    def on_can_fd_changed(self, checked: bool) -> None:
        """Handle CAN-FD checkbox changes"""
        if self.is_docan_mode():
            current_text = self.ui.comboBox.currentText()
            if current_text:
                self.on_can_select_changed(current_text)
    
    def init_ui(self):
        """Initialize UI"""
        # Check current tab
        current_index = self.ui.transport_abstract.currentIndex()
        self.on_tab_changed(current_index)
        
    def on_tab_changed(self, index):
        """Handle tab switching"""
        if index == 0:  # DoIP tab
            self.log_message.emit("Switched to DoIP mode")
            self.scan_network_interfaces()
        elif index == 1:  # DoCAN tab
            self.log_message.emit("Switched to DoCAN mode")
            self.scan_can_interfaces()
            
    def scan_network_interfaces(self):
        """Scan local network interfaces"""
        try:
            self.log_message.emit("Starting network interface scan...")
            
            # Clear network selection dropdown
            self.ui.Net_Select.clear()
            
            # Get all network interfaces
            interfaces = netifaces.interfaces()
            valid_interfaces = []
            
            for interface in interfaces:
                # Get interface address information
                addrs = netifaces.ifaddresses(interface)
                
                # Check for IPv4 addresses
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get('addr')
                        if ip and ip != '127.0.0.1':  # Exclude loopback
                            interface_info = f"{interface} ({ip})"
                            valid_interfaces.append(interface_info)
                            self.ui.Net_Select.addItem(interface_info)
                            self.log_message.emit(f"Found network interface: {interface_info}")
            
            if not valid_interfaces:
                self.log_message.emit("No available network interfaces found")
                self.ui.Net_Select.addItem("No available interfaces")
            else:
                # Auto-trigger selection for first interface
                if self.ui.Net_Select.count() > 0:
                    self.on_net_select_changed(self.ui.Net_Select.itemText(0))
                
        except Exception as e:
            self.log_message.emit(f"Error scanning network interfaces: {str(e)}")
            
    def scan_can_interfaces(self):
        """Scan CAN interfaces"""
        try:
            self.log_message.emit("Starting CAN interface scan...")
            self.ui.comboBox.clear()
            
            # Add common CAN interfaces (this can be extended with actual scanning)
            can_interfaces = ["can0", "can1", "vcan0", "PCAN_USBBUS1", "KVASER_0"]
            for interface in can_interfaces:
                self.ui.comboBox.addItem(interface)
                self.log_message.emit(f"Found CAN interface: {interface}")
                
            # Auto-trigger selection for first interface
            if self.ui.comboBox.count() > 0:
                self.on_can_select_changed(self.ui.comboBox.itemText(0))
                
        except Exception as e:
            self.log_message.emit(f"Error scanning CAN interfaces: {str(e)}")
    
    def get_server_client_addresses(self):
        current_tab = self.ui.transport_abstract.currentIndex()
        
        if current_tab == 0:  # DoIP
            return self.auto_set_doip_addresses()
        elif current_tab == 1:  # DoCAN
            server_addr = self.ui.CAN_Server_Addr.text() or "0x0040"
            client_addr = self.ui.CAN_CLient_Addr.text() or "0x0E80"
            return None, server_addr, client_addr
            
        return None, None, None
        
    def get_current_transport_type(self):
        return self.ui.transport_abstract.currentIndex()
        
    def is_doip_mode(self):
        return self.ui.transport_abstract.currentIndex() == 0
        
    def is_docan_mode(self):
        return self.ui.transport_abstract.currentIndex() == 1
        
    def cleanup(self):
        self.log_message.emit("TransportManager clen done ")
        if self.current_transport:
            pass