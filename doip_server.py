import socket
import threading
import struct
import time
import json
import os
from typing import Dict, Tuple
import sys
from PySide6.QtCore import QObject, Signal

class DoIPServer(QObject):
    log_message = Signal(str)
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    message_received = Signal(bytes)
    status_changed = Signal(str)
    
    def __init__(self, responsefile: str, host='127.0.0.1', port=13400, server_addr=0x1001, server_addr_func=0x1FFF, client_addr=0x0E80):
        super().__init__()
        self.host = host
        self.port = port
        self.server_addr = server_addr
        self.server_addr_func = server_addr_func 
        self.client_addr = client_addr
        self.tcp_socket = None
        self.udp_socket = None
        self.running = False
        self.clients = {}  
        self.responsefilepath = responsefile
        self.response_config = self.load_response_config()
        
        self.DOIP_HEADER_SIZE = 8
        self.DOIP_VERSION = 0x03
        self.DOIP_INVERSE_VERSION = 0xFC
        
        self.DOIP_VEHICLE_IDENTIFICATION_REQUEST = 0x0001
        self.DOIP_VEHICLE_IDENTIFICATION_RESPONSE = 0x0004
        self.DOIP_ROUTING_ACTIVATION_REQUEST = 0x0005
        self.DOIP_ROUTING_ACTIVATION_RESPONSE = 0x0006
        self.DOIP_DIAGNOSTIC_MESSAGE = 0x8001
        self.DOIP_DIAGNOSTIC_MESSAGE_ACK = 0x8002
        self.DOIP_DIAGNOSTIC_MESSAGE_NACK = 0x8003
    
    def load_response_config(self):
        config_path = self.responsefilepath      
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_list = json.load(f)
                config_dict = {}
                for item in config_list:
                    req_hex = item['req'].upper()
                    res_hex = item['res'].upper()
                    config_dict[req_hex] = res_hex
                self.log_message.emit(f"Loaded {len(config_dict)} response configurations from {config_path}")
                return config_dict
        except FileNotFoundError:
            self.log_message.emit(f"Warning: Response config file not found: {config_path}")
            self.log_message.emit("Using default response generation")
            return {}
        except json.JSONDecodeError as e:
            self.log_message.emit(f"Error parsing JSON config file: {e}")
            return {}
        except Exception as e:
            self.log_message.emit(f"Error loading response config: {e}")
            return {}
    
    def start_server(self):
        if self.running:
            self.log_message.emit("DoIP Server is already running")
            return
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind((self.host, self.port))
            self.tcp_socket.listen(5)
            
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udp_socket.bind((self.host, self.port))
            
            self.running = True
            
            self.log_message.emit(f"DoIP Server started on {self.host}:{self.port}")
            self.log_message.emit(f"Physical Address: 0x{self.server_addr:04X}")
            self.log_message.emit(f"Functional Address: 0x{self.server_addr_func:04X}")
            self.log_message.emit(f"Expected Client Address: 0x{self.client_addr:04X}")
            self.log_message.emit("TCP and UDP sockets are listening...")
            self.status_changed.emit("running")
            
            # self.send_udp_vehicle_announcements()
            
            udp_thread = threading.Thread(target=self.handle_udp_messages)
            udp_thread.daemon = True
            udp_thread.start()
            
            tcp_thread = threading.Thread(target=self.tcp_accept_loop)
            tcp_thread.daemon = True
            tcp_thread.start()
            
            self.log_message.emit("DoIP Server started successfully (non-blocking mode)")
            
        except Exception as e:
            self.log_message.emit(f"Server error: {e}")
            self.status_changed.emit("error")
            self.stop_server()
            
    def tcp_accept_loop(self):
        self.log_message.emit("TCP accept loop started")
        
        while self.running:
            try:
                client_socket, client_address = self.tcp_socket.accept()
                self.log_message.emit(f"New TCP connection from {client_address}")
                self.client_connected.emit(f"{client_address[0]}:{client_address[1]}")
                
                client_thread = threading.Thread(
                    target=self.handle_tcp_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.error as e:
                if self.running:
                    self.log_message.emit(f"TCP Socket error: {e}")
                break
        
        self.log_message.emit("TCP accept loop stopped")
        
    def handle_udp_messages(self):
        self.log_message.emit("UDP message handler started")

        while self.running:
            try:
                data, client_address = self.udp_socket.recvfrom(4096)
                self.log_message.emit(f"Received UDP message from {client_address}, length: {len(data)}")
                
                if len(data) >= self.DOIP_HEADER_SIZE:
                    version, inv_version, payload_type, payload_length = struct.unpack('>BBHI', data[:self.DOIP_HEADER_SIZE])
                    
                    self.log_message.emit(f"UDP DoIP message:")
                    self.log_message.emit(f"  Version: 0x{version:02X}")
                    self.log_message.emit(f"  Inverse Version: 0x{inv_version:02X}")
                    self.log_message.emit(f"  Payload Type: 0x{payload_type:04X}")
                    self.log_message.emit(f"  Payload Length: {payload_length}")
                    
                    payload_data = data[self.DOIP_HEADER_SIZE:self.DOIP_HEADER_SIZE + payload_length]
                    
                    self.process_udp_doip_message(client_address, payload_type, payload_data)
                else:
                    self.log_message.emit(f"Invalid UDP DoIP message: too short ({len(data)} bytes)")
            except socket.timeout:
                continue
            except socket.error as e:
                if self.running:
                    self.log_message.emit(f"UDP socket error: {e}")
                break
            except KeyboardInterrupt:
                self.log_message.emit("\nReceived keyboard interrupt in UDP handler")
                break
            except Exception as e:
                self.log_message.emit(f"UDP message handling error: {e}")
                
        self.log_message.emit("UDP message handler stopped")
    
    def process_udp_doip_message(self, client_address: Tuple[str, int], payload_type: int, payload_data: bytes):
        # Skip loopback address processing for UDP messages
        # if client_address[0] == '127.0.0.1':
        #     log_message.emit(f"Skipping loopback UDP message from {client_address}")
        #     return
        if payload_type == self.DOIP_VEHICLE_IDENTIFICATION_REQUEST:
            self.handle_udp_vehicle_identification_request(client_address, payload_data)
        else:
            log_message.emit(f"Unknown UDP DoIP message type: 0x{payload_type:04X}")
    
    def handle_udp_vehicle_identification_request(self, client_address: Tuple[str, int], payload_data: bytes):
        log_message.emit(f"Processing UDP Vehicle Identification Request from {client_address}")
        
        vin = b'1HGBH41JXMN109186'  # VIN
        logical_address = struct.pack('>H', self.server_addr)
        eid = b'\x01\x02\x03\x04\x05\x06'  # EID
        gid = b'\x07\x08\x09\x0A\x0B\x0C'  # GID
        further_action = b'\x00'  # 
        
        response_payload = vin + logical_address + eid + gid + further_action
        
        self.send_udp_doip_message(client_address, self.DOIP_VEHICLE_IDENTIFICATION_RESPONSE, response_payload)
        log_message.emit(f"UDP Vehicle Identification Response sent to {client_address}")
    
    def send_udp_doip_message(self, client_address: Tuple[str, int], payload_type: int, payload_data: bytes):
        
        header = struct.pack('>BBHI', 
                           self.DOIP_VERSION, 
                           self.DOIP_INVERSE_VERSION, 
                           payload_type, 
                           len(payload_data))
        
        message = header + payload_data
        self.udp_socket.sendto(message, client_address)
        
        self.log_message.emit(f"Sent UDP DoIP message to {client_address}: Type=0x{payload_type:04X}, Length={len(payload_data)}")
        
    def send_udp_vehicle_announcements(self):
        self.log_message.emit("Sending Vehicle Announcements...")
        
        vin = b'1HGBH41JXMN109186'  #VIN
        logical_address = struct.pack('>H', self.server_addr)
        eid = b'\x01\x02\x03\x04\x05\x06'  # EID
        gid = b'\x07\x08\x09\x0A\x0B\x0C'  # GID
        further_action = b'\x00'  
        sync_status = b'\x10'  
        
        # DoIP Vehicle Announcement Message (0x0004) 
        announcement_payload = vin + logical_address + eid + gid + further_action + sync_status
        
        
        broadcast_address = ('255.255.255.255', self.port)
        
        for i in range(3):
            try:
                header = struct.pack('>BBHI', 
                                   self.DOIP_VERSION, 
                                   self.DOIP_INVERSE_VERSION, 
                                   self.DOIP_VEHICLE_IDENTIFICATION_RESPONSE,  # 0x0004
                                   len(announcement_payload))
                
                message = header + announcement_payload
                self.udp_socket.sendto(message, broadcast_address)
                
                self.log_message.emit(f"Vehicle Announcement {i+1}/3 sent to broadcast address")
                
                time.sleep(1)
                
            except Exception as e:
                self.log_message.emit(f"Error sending vehicle announcement {i+1}: {e}")
        
        self.log_message.emit("Vehicle Announcements completed")
        
    def handle_tcp_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        client_id = f"{client_address[0]}:{client_address[1]}"
        self.clients[client_id] = {
            'socket': client_socket,
            'address': client_address,
            'routing_activated': False
        }
        
        try:
            while self.running:
                header_data = self.receive_exact(client_socket, self.DOIP_HEADER_SIZE)
                if not header_data:
                    break
                
                version, inv_version, payload_type, payload_length = struct.unpack('>BBHI', header_data)
                
                self.log_message.emit(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Received TCP DoIP message: Version: 0x{version:02X}, Inverse Version: 0x{inv_version:02X}, Payload Type: 0x{payload_type:04X}, Payload Length: {payload_length}")
                
                payload_data = b''
                if payload_length > 0:
                    payload_data = self.receive_exact(client_socket, payload_length)
                    if not payload_data:
                        break
                
                self.process_tcp_doip_message(client_socket, payload_type, payload_data)
                
        except Exception as e:
            self.log_message.emit(f"TCP Client {client_id} error: {e}")
        finally:
            self.log_message.emit(f"TCP Client {client_id} disconnected")
            client_socket.close()
            if client_id in self.clients:
                del self.clients[client_id]
    
    def receive_exact(self, sock: socket.socket, length: int) -> bytes:
        data = b''
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def process_tcp_doip_message(self, client_socket: socket.socket, payload_type: int, payload_data: bytes):
        if payload_type == self.DOIP_VEHICLE_IDENTIFICATION_REQUEST:
            self.handle_vehicle_identification_request(client_socket, payload_data)
        elif payload_type == self.DOIP_ROUTING_ACTIVATION_REQUEST:
            self.handle_routing_activation_request(client_socket, payload_data)
        elif payload_type == self.DOIP_DIAGNOSTIC_MESSAGE:
            self.handle_diagnostic_message(client_socket, payload_data)
        else:
            self.log_message.emit(f"Unknown TCP DoIP message type: 0x{payload_type:04X}")
    
    def handle_vehicle_identification_request(self, client_socket: socket.socket, payload_data: bytes):
        lself.log_message.emit("Processing Vehicle Identification Request")
        
        vin = b'1HGBH41JXMN109186'  # VIN
        logical_address = struct.pack('>H', self.server_addr)
        eid = b'\x01\x02\x03\x04\x05\x06'  # EID
        gid = b'\x07\x08\x09\x0A\x0B\x0C'  # GID
        further_action = b'\x00'  
        
        response_payload = vin + logical_address + eid + gid + further_action
        
        self.send_doip_message(client_socket, self.DOIP_VEHICLE_IDENTIFICATION_RESPONSE, response_payload)
        self.log_message.emit("Vehicle Identification Response sent")
    
    def handle_routing_activation_request(self, client_socket: socket.socket, payload_data: bytes):
        self.log_message.emit("Processing Routing Activation Request")
        
        if len(payload_data) >= 4:
            source_address = struct.unpack('>H', payload_data[0:2])[0]
            activation_type = payload_data[2]
            
            self.log_message.emit(f"  Source Address: 0x{source_address:04X}")
            self.log_message.emit(f"  Activation Type: 0x{activation_type:02X}")
            
            client_logical_address = struct.pack('>H', source_address)
            server_logical_address = struct.pack('>H', self.server_addr)
            response_code = b'\x10' 
            
            response_payload = client_logical_address + server_logical_address + response_code + b'\x00\x00\x00\x00'
            
            self.send_doip_message(client_socket, self.DOIP_ROUTING_ACTIVATION_RESPONSE, response_payload)
            self.log_message.emit("Routing Activation Response sent (Success)")
            
            for client_info in self.clients.values():
                if client_info['socket'] == client_socket:
                    client_info['routing_activated'] = True
                    break
        else:
            self.log_message.emit("Invalid Routing Activation Request payload")
    
    def handle_diagnostic_message(self, client_socket: socket.socket, payload_data: bytes):
        self.log_message.emit("Processing Diagnostic Message")
        
        if len(payload_data) >= 4:
            source_address = struct.unpack('>H', payload_data[0:2])[0]
            target_address = struct.unpack('>H', payload_data[2:4])[0]
            user_data = payload_data[4:]
            
            self.log_message.emit(f"  Source Address: 0x{source_address:04X}，Target Address: 0x{target_address:04X}， User Data: {user_data.hex().upper()}")

            if target_address == self.server_addr:
                self.log_message.emit(f"  Message type: Physical addressing (0x{self.server_addr:04X})")
                address_type = "physical"
            elif target_address == self.server_addr_func:
                self.log_message.emit(f"  Message type: Functional addressing (0x{self.server_addr_func:04X})")
                address_type = "functional"
            else:
                self.log_message.emit(f"  Warning: Target address 0x{target_address:04X} does not match server addresses")
                self.log_message.emit(f"  Expected: 0x{self.server_addr:04X} (physical) or 0x{self.server_addr_func:04X} (functional)")
                address_type = "unknown"
                
            ack_payload = struct.pack('>HHB', source_address, target_address, 0x00)  # 确认码
            self.send_doip_message(client_socket, self.DOIP_DIAGNOSTIC_MESSAGE_ACK, ack_payload)
            
            if user_data:
                response_data = self.generate_diagnostic_response(user_data, address_type)
                if response_data:
                    response_source = self.server_addr
                    response_payload = struct.pack('>HH', response_source, source_address) + response_data
                    self.send_doip_message(client_socket, self.DOIP_DIAGNOSTIC_MESSAGE, response_payload)
                    self.log_message.emit(f"Diagnostic Response sent: {response_data.hex().upper()}")
                    self.log_message.emit(f"Response source address: 0x{response_source:04X} (physical)")
        else:
            self.log_message.emit("Invalid Diagnostic Message payload")
    
    def generate_diagnostic_response(self, request_data: bytes, address_type: str = "physical") -> bytes:
        if len(request_data) == 0:
            return None
        
        request_hex = request_data.hex().upper()
        # self.log_message.emit(f"Looking up response for request: {request_hex} (address_type: {address_type})")
        
        if request_hex in self.response_config:
            response_hex = self.response_config[request_hex]
            self.log_message.emit(f"Found configured response: {response_hex}")
            try:
                return bytes.fromhex(response_hex)
            except ValueError as e:
                self.log_message.emit(f"Error converting hex response to bytes: {e}")
                return None
        
        # self.log_message.emit(f"No configured response found, using default logic")
        return self.generate_default_diagnostic_response(request_data, address_type)
    
    def generate_default_diagnostic_response(self, request_data: bytes, address_type: str = "physical") -> bytes:
        service_id = request_data[0]
        
        if address_type == "functional":
            if service_id == 0x3E: 
                self.log_message.emit("TesterPresent with functional addressing - no response")
                return None
            elif service_id == 0x11: 
                self.log_message.emit("ECU Reset with functional addressing")
               
        elif address_type == "physical":
            if service_id == 0x3E:
                # self.log_message.emit("There is no need response for 3E80")
                return None
        
        if service_id == 0x10:  # DiagnosticSessionControl
            return bytes([0x50]) + request_data[1:2] + b'\x00\x32\x01\xF4'
        elif service_id == 0x22:  # ReadDataByIdentifier
            if len(request_data) >= 3:
                did = struct.unpack('>H', request_data[1:3])[0]
                return bytes([0x62]) + request_data[1:3] + b'\x01\x02\x03\x04' 
        elif service_id == 0x27:  # SecurityAccess
            if len(request_data) >= 2:
                level = request_data[1]
                if level % 2 == 1:  
                    return bytes([0x67, level]) + b'\x12\x34\x56\x78\x9A\xBC\xDE\xF0' * 2
                else: 
                    return bytes([0x67, level])
        elif service_id == 0x3E:  # TesterPresent
            if address_type == "physical":
                return bytes([0x7E])  # 物理寻址时响应
            else:
                return None 
        elif service_id == 0x11:  # ECU Reset
            if len(request_data) >= 2:
                reset_type = request_data[1]
                return bytes([0x51, reset_type])
            

        if (request_data[0] == 0x31 and 
            request_data[1] == 0x01 and request_data[2] == 0xDD and request_data[3] == 0x02):
            response = bytes([0x71, 0x01, 0xDD, 0x02, 0x00])
            return response
        
        if len(request_data) > 0 and request_data[0] == 0x34 and len(request_data) > 1:
            response = bytes([0x74,0x40,0x00,0x00,0x3F,0x02]) 
            return response
        
        
        if len(request_data) > 0 and request_data[0] == 0x36 and len(request_data) > 1:
            response = bytes([0x76, request_data[1]]) 
            return response
        
        if len(request_data) > 0 and request_data[0] == 0x37:
            response = bytes([0x77])  
            return response
        
        if (request_data[0] == 0x31 and 
            request_data[1] == 0x01 and request_data[2] == 0xFF and request_data[3] == 0x00):
            response = bytes([0x71, 0x01, 0xFF, 0x00, 0x00])
            return response
        
        return bytes([0x7F, service_id, 0x11]) 
    
    def send_doip_message(self, client_socket: socket.socket, payload_type: int, payload_data: bytes):
        header = struct.pack('>BBHI', 
                           self.DOIP_VERSION, 
                           self.DOIP_INVERSE_VERSION, 
                           payload_type, 
                           len(payload_data))
        
        message = header + payload_data
        client_socket.send(message)
        
        self.log_message.emit(f"Sent DoIP message: Type=0x{payload_type:04X}, Length={len(payload_data)}")
    
    def stop_server(self):
        self.log_message.emit("Stopping DoIP server...")
        self.running = False
        
        for client_info in self.clients.values():
            try:
                client_info['socket'].close()
            except:
                pass
        self.clients.clear()
        
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
        
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
        
        self.log_message.emit("DoIP server stopped")