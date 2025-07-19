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
            'config_file_path': None,  # Path to configuration file
            'config_data': None,       # Loaded configuration data
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
        
        # Connect config file selection button
        self.ui.config_file.clicked.connect(self.select_config_file)
        
        # Connect server initialization button
        self.ui.init_server.clicked.connect(self.init_server)
        
        # Monitor CAN-FD checkbox
        self.ui.is_FD.toggled.connect(self.on_can_fd_changed)
        
    def select_config_file(self) -> None:
        """Handle config file selection"""
        try:
            # Open file dialog to select configuration file
            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "Select Configuration File",
                "",
                "JSON Files (*.json);;All Files (*.*)"
            )
            
            if file_path:
                # Display selected file path in label
                self.ui.config_file_label.setText(file_path)
                self.log_message.emit(f"Configuration file selected: {file_path}")
                
                # Store config file path in transport_info
                self.transport_info['config_file_path'] = file_path
                
            else:
                self.log_message.emit("No configuration file selected")
                
        except Exception as e:
            self.log_message.emit(f"Error selecting configuration file: {str(e)}")
            
    def load_config_file(self, file_path: str) -> None:
        """Load and validate configuration file"""
        try:

            
            self.log_message.emit("Configuration file loaded successfully")
            
        except json.JSONDecodeError as e:
            self.log_message.emit(f"Invalid JSON format in config file: {str(e)}")
        except FileNotFoundError:
            self.log_message.emit(f"Configuration file not found: {file_path}")
        except Exception as e:
            self.log_message.emit(f"Error loading configuration file: {str(e)}")
            
    def init_server(self) -> None:
        """Initialize DoIP or DoCAN server based on transport_info"""
        try:
            # Check if transport_info is complete
            if not self.validate_transport_info():
                self.log_message.emit("Transport information is incomplete. Please configure all settings.")
                return
                
            self.log_message.emit("=== Initializing Server ===")
            self.log_message.emit(f"Transport Type: {self.transport_info.get('transport_type', 'Unknown')}")
            
            # Initialize server based on transport type
            if self.transport_info['transport_type'] == 'ETH':
                self.init_doip_server()
            elif self.transport_info['transport_type'] == 'CAN':
                self.init_docan_server()
            else:
                self.log_message.emit("Unknown transport type. Please select DoIP or DoCAN tab.")
  
        except Exception as e:
            self.log_message.emit(f"Error initializing server: {str(e)}")
            
    def validate_transport_info(self) -> bool:
        """Validate if transport_info contains all required information"""
        transport_type = self.transport_info.get('transport_type')
        
        if not transport_type:
            self.log_message.emit("No transport type selected")
            return False
            
        if 'config_file_path' not in self.transport_info:
            self.log_message.emit("No configuration file selected")
            return False
            
        if transport_type == 'ETH':
            eth_info = self.transport_info.get('eth_info', {})
            required_fields = ['ip_address', 'client_addr', 'server_addr']
            for field in required_fields:
                if not eth_info.get(field):
                    self.log_message.emit(f"Missing ETH configuration: {field}")
                    return False
                    
        elif transport_type == 'CAN':
            can_info = self.transport_info.get('can_info', {})
            required_fields = ['channel', 'client_addr', 'server_addr']
            for field in required_fields:
                if not can_info.get(field):
                    self.log_message.emit(f"Missing CAN configuration: {field}")
                    return False
                    
        return True
        
    def init_doip_server(self) -> None:
        """Initialize DoIP server with transport_info"""
        try:
            self.log_message.emit("Initializing DoIP Server...")
            
            # Import DoIP server module
            from doip_server import DoIPServer
            
            # Extract ETH info parameters
            eth_info = self.transport_info.get('eth_info', {})
            
            # Get individual parameters with default values
            host = eth_info.get('ip_address', '127.0.0.1')
            port = eth_info.get('port', 13400)
            client_addr = eth_info.get('client_addr', '0x0E80')
            server_addr = eth_info.get('server_addr', '0x0040')
            interface_name = eth_info.get('interface_name', 'Unknown')
            
            # Convert hex string addresses to integers if needed
            if isinstance(client_addr, str) and client_addr.startswith('0x'):
                client_addr = int(client_addr, 16)
            if isinstance(server_addr, str) and server_addr.startswith('0x'):
                server_addr = int(server_addr, 16)
                
            # Log the parameters being used
            self.log_message.emit(f"DoIP Server Parameters:")
            self.log_message.emit(f"  Host IP: {host}")
            self.log_message.emit(f"  Port: {port}")
            self.log_message.emit(f"  Interface: {interface_name}")
            self.log_message.emit(f"  Client Address: {client_addr} (0x{client_addr:04X})")
            self.log_message.emit(f"  Server Address: {server_addr} (0x{server_addr:04X})")
            self.log_message.emit(f"  Response file path: {self.transport_info['config_file_path']}")
            
            # Create DoIP server instance with extracted parameters
            self.current_transport = DoIPServer(
                host=host,
                port=port,
                client_addr=client_addr,
                server_addr_func=0x7DF,  # Functional address for UDS
                server_addr=server_addr,
                responsefile=self.transport_info['config_file_path']
            )
            
            self.current_transport.log_message.connect(self.log_message.emit)
            self.current_transport.client_connected.connect(
                lambda addr: self.log_message.emit(f"Client connected: {addr}")
            )
            self.current_transport.client_disconnected.connect(
                lambda addr: self.log_message.emit(f"Client disconnected: {addr}")
            )
            self.current_transport.status_changed.connect(
                lambda status: self.log_message.emit(f"DoIP Server status: {status}")
            )
            # Start the server
            self.current_transport.start_server()
            self.log_message.emit("DoIP Server initialized and started successfully")
            # Emit transport ready signal
            self.transport_ready.emit(self.current_transport)
            
        except ImportError:
            self.log_message.emit("DoIP server module not found. Please ensure doip_server.py exists.")
        except ValueError as e:
            self.log_message.emit(f"Invalid address format: {str(e)}")
        except Exception as e:
            self.log_message.emit(f"Error initializing DoIP server: {str(e)}")
            
    def init_docan_server(self) -> None:
        """Initialize DoCAN server with transport_info"""
        try:
            self.log_message.emit("Initializing DoCAN Server...")
            
            # Import DoCAN server module
            from docan_server import DoCANServer
            
            # Extract CAN info parameters
            can_info = self.transport_info.get('can_info', {})
            
            # Get individual parameters with default values
            device_type = can_info.get('device_type', 'socketcan')
            channel = can_info.get('channel', 'can0')
            client_addr = can_info.get('client_addr', '0x0E80')
            server_addr = can_info.get('server_addr', '0x0040')
            is_fd = can_info.get('is_fd', False)
            bitrate = can_info.get('bitrate', 500000)
            
            # Convert hex string addresses to integers if needed
            if isinstance(client_addr, str) and client_addr.startswith('0x'):
                client_addr = int(client_addr, 16)
            if isinstance(server_addr, str) and server_addr.startswith('0x'):
                server_addr = int(server_addr, 16)
                
            # Log the parameters being used
            self.log_message.emit(f"DoCAN Server Parameters:")
            self.log_message.emit(f"  Device Type: {device_type}")
            self.log_message.emit(f"  Channel: {channel}")
            self.log_message.emit(f"  Client Address: {client_addr} (0x{client_addr:03X})")
            self.log_message.emit(f"  Server Address: {server_addr} (0x{server_addr:03X})")
            self.log_message.emit(f"  CAN-FD: {is_fd}")
            self.log_message.emit(f"  Bitrate: {bitrate}")
            
            # Create DoCAN server instance with extracted parameters
            self.current_transport = DoCANServer(
                device_type=device_type,
                channel=channel,
                client_addr=client_addr,
                server_addr=server_addr,
                is_fd=is_fd,
                bitrate=bitrate
            )
            
            # Connect server signals if available
            if hasattr(self.current_transport, 'log_message'):
                self.current_transport.log_message.connect(self.log_message.emit)
                
            # Start the server
            if hasattr(self.current_transport, 'start'):
                self.current_transport.start()
                self.log_message.emit("DoCAN Server initialized and started successfully")
            else:
                self.log_message.emit("DoCAN Server initialized (start method not available)")
                
            # Emit transport ready signal
            self.transport_ready.emit(self.current_transport)
            
        except ImportError:
            self.log_message.emit("DoCAN server module not found. Please ensure docan_server.py exists.")
        except ValueError as e:
            self.log_message.emit(f"Invalid address format: {str(e)}")
        except Exception as e:
            self.log_message.emit(f"Error initializing DoCAN server: {str(e)}")
    def create_empty_transport_info(self) -> Dict[str, Any]:
        """Create empty transport information structure"""
        return {
            'transport_type': None,  # 'CAN' or 'ETH'
            'config_file_path': None,  # Path to configuration file
            'config_data': None,       # Loaded configuration data
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