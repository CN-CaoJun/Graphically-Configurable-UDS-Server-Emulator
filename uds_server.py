import json
import threading
from PySide6.QtCore import QObject, pyqtSignal

class UDSServer(QObject):
    """UDS协议处理服务器"""
    
    # 信号定义
    service_executed = pyqtSignal(dict)  # UDS服务执行完成
    error_occurred = pyqtSignal(dict)    # UDS处理错误
    diagnostic_session_changed = pyqtSignal(dict)  # 诊断会话变化
    
    def __init__(self, transport_server=None, config_file=None, server_type='doip'):
        super().__init__()
        self.transport_server = transport_server
        self.config_file = config_file
        self.server_type = server_type
        self.running = False
        
        # UDS状态
        self.current_session = 0x01  # Default session
        self.security_access_level = 0x00
        self.communication_control = True
        
        # 加载配置
        self.config = self.load_config()
        
        # 连接传输层信号
        if self.transport_server:
            self.transport_server.message_received.connect(self.process_uds_message)
            
    def load_config(self):
        """加载UDS配置文件"""
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Config load error: {str(e)}")
        
        # 默认配置
        return {
            "uds_services": {
                "diagnostic_session_control": {
                    "service_id": 0x10,
                    "sessions": [0x01, 0x02, 0x03]
                },
                "ecu_reset": {
                    "service_id": 0x11,
                    "reset_types": [0x01, 0x02]
                },
                "read_data_by_identifier": {
                    "service_id": 0x22,
                    "supported_dids": [0xF190, 0xF191, 0xF192]
                },
                "security_access": {
                    "service_id": 0x27,
                    "security_levels": [0x01, 0x03, 0x05]
                }
            },
            "timing": {
                "p2_client": 50,
                "p2_star_client": 5000
            }
        }
        
    def start(self):
        """启动UDS服务器"""
        self.running = True
        print("UDS Server started")
        
    def stop(self):
        """停止UDS服务器"""
        self.running = False
        print("UDS Server stopped")
        
    def process_uds_message(self, raw_data):
        """处理UDS消息"""
        if not self.running:
            return
            
        try:
            # 解析UDS消息
            if len(raw_data) < 1:
                return
                
            service_id = raw_data[0]
            
            # 根据服务ID分发处理
            if service_id == 0x10:
                self.handle_diagnostic_session_control(raw_data)
            elif service_id == 0x11:
                self.handle_ecu_reset(raw_data)
            elif service_id == 0x22:
                self.handle_read_data_by_identifier(raw_data)
            elif service_id == 0x27:
                self.handle_security_access(raw_data)
            else:
                self.send_negative_response(service_id, 0x11)  # Service not supported
                
        except Exception as e:
            print(f"UDS message processing error: {str(e)}")
            
    def handle_diagnostic_session_control(self, data):
        """处理诊断会话控制服务 (0x10)"""
        if len(data) < 2:
            self.send_negative_response(0x10, 0x13)  # Incorrect message length
            return
            
        session_type = data[1]
        supported_sessions = self.config["uds_services"]["diagnostic_session_control"]["sessions"]
        
        if session_type in supported_sessions:
            self.current_session = session_type
            response = bytes([0x50, session_type, 0x00, 0x32, 0x01, 0xF4])  # Positive response
            self.send_response(response)
            
            # 发送会话变化信号
            session_names = {0x01: "Default", 0x02: "Programming", 0x03: "Extended"}
            self.diagnostic_session_changed.emit({
                "session_type": session_names.get(session_type, f"0x{session_type:02X}")
            })
            
            # 发送服务执行信号
            self.service_executed.emit({
                "service_id": 0x10,
                "sub_function": f" {session_type:02X}",
                "response": response.hex().upper()
            })
        else:
            self.send_negative_response(0x10, 0x12)  # Sub-function not supported
            
    def handle_ecu_reset(self, data):
        """处理ECU复位服务 (0x11)"""
        if len(data) < 2:
            self.send_negative_response(0x11, 0x13)
            return
            
        reset_type = data[1]
        supported_resets = self.config["uds_services"]["ecu_reset"]["reset_types"]
        
        if reset_type in supported_resets:
            response = bytes([0x51, reset_type])
            self.send_response(response)
            
            self.service_executed.emit({
                "service_id": 0x11,
                "sub_function": f" {reset_type:02X}",
                "response": response.hex().upper()
            })
        else:
            self.send_negative_response(0x11, 0x12)
            
    def handle_read_data_by_identifier(self, data):
        """处理通过标识符读取数据服务 (0x22)"""
        if len(data) < 3:
            self.send_negative_response(0x22, 0x13)
            return
            
        did = (data[1] << 8) | data[2]
        supported_dids = self.config["uds_services"]["read_data_by_identifier"]["supported_dids"]
        
        if did in supported_dids:
            # 模拟数据响应
            mock_data = bytes([0x01, 0x02, 0x03, 0x04])  # 示例数据
            response = bytes([0x62]) + data[1:3] + mock_data
            self.send_response(response)
            
            self.service_executed.emit({
                "service_id": 0x22,
                "sub_function": f" {did:04X}",
                "response": response.hex().upper()
            })
        else:
            self.send_negative_response(0x22, 0x31)  # Request out of range
            
    def handle_security_access(self, data):
        """处理安全访问服务 (0x27)"""
        if len(data) < 2:
            self.send_negative_response(0x27, 0x13)
            return
            
        security_level = data[1]
        
        if security_level % 2 == 1:  # Request seed
            seed = bytes([0x12, 0x34, 0x56, 0x78])  # 示例种子
            response = bytes([0x67, security_level]) + seed
            self.send_response(response)
            
            self.service_executed.emit({
                "service_id": 0x27,
                "sub_function": f" {security_level:02X}",
                "response": response.hex().upper()
            })
        else:  # Send key
            # 简单的密钥验证（实际应用中需要复杂的算法）
            response = bytes([0x67, security_level])
            self.send_response(response)
            self.security_access_level = security_level
            
            self.service_executed.emit({
                "service_id": 0x27,
                "sub_function": f" {security_level:02X}",
                "response": response.hex().upper()
            })
            
    def send_response(self, response_data):
        """发送UDS响应"""
        if self.transport_server:
            self.transport_server.send_message(response_data)
            
    def send_negative_response(self, service_id, nrc):
        """发送否定响应"""
        response = bytes([0x7F, service_id, nrc])
        self.send_response(response)
        
        # 发送错误信号
        self.error_occurred.emit({
            "service_id": service_id,
            "nrc": f"0x{nrc:02X}"
        })