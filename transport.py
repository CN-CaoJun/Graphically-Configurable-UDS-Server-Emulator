import socket
import netifaces
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox

class TransportManager(QObject):
    # 信号定义
    log_message = Signal(str)
    transport_ready = Signal(object)
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.current_transport = None
        
        # 连接UI信号
        self.setup_connections()
        
        # 初始化界面
        self.init_ui()
        
    def setup_connections(self):
        """设置UI连接"""
        # 监听标签页切换
        self.ui.transport_abstract.currentChanged.connect(self.on_tab_changed)
        
    def init_ui(self):
        """初始化UI"""
        # 检查当前标签页
        current_index = self.ui.transport_abstract.currentIndex()
        self.on_tab_changed(current_index)
        
    def on_tab_changed(self, index):
        """标签页切换处理"""
        if index == 0:  # DoIP标签页
            self.log_message.emit("切换到DoIP模式")
            self.scan_network_interfaces()
        elif index == 1:  # DoCAN标签页
            self.log_message.emit("切换到DoCAN模式")
            self.scan_can_interfaces()
            
    def scan_network_interfaces(self):
        """扫描本地网络接口"""
        try:
            self.log_message.emit("开始扫描网络接口...")
            
            # 清空网络选择下拉框
            self.ui.Net_Select.clear()
            
            # 获取所有网络接口
            interfaces = netifaces.interfaces()
            valid_interfaces = []
            
            for interface in interfaces:
                # 获取接口地址信息
                addrs = netifaces.ifaddresses(interface)
                
                # 检查是否有IPv4地址
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get('addr')
                        interface_info = f"{interface} ({ip})"
                        valid_interfaces.append(interface_info)
                        self.ui.Net_Select.addItem(interface_info)
                        self.log_message.emit(f"发现网络接口: {interface_info}")
            
            if not valid_interfaces:
                self.log_message.emit("未发现可用的网络接口")
                self.ui.Net_Select.addItem("无可用接口")
            else:
                # 自动设置服务器和客户端地址
                self.auto_set_doip_addresses()
                
        except Exception as e:
            self.log_message.emit(f"扫描网络接口时出错: {str(e)}")
            
    def auto_set_doip_addresses(self):
        """自动设置DoIP服务器和客户端地址"""
        try:
            # 获取当前选中的网络接口
            current_text = self.ui.Net_Select.currentText()
            if current_text and "(" in current_text:
                # 提取IP地址
                ip = current_text.split("(")[1].split(")")[0]
                
                # 设置服务器地址（使用默认值或基于IP生成）
                server_addr = self.ui.doip_server_addr.text() or "0x0040"
                client_addr = self.ui.doip_client_addr.text() or "0x0E80"
                
                self.log_message.emit(f"设置DoIP地址 - 服务器: {server_addr}, 客户端: {client_addr}")
                self.log_message.emit(f"使用网络接口IP: {ip}")
                
                return ip, server_addr, client_addr
                
        except Exception as e:
            self.log_message.emit(f"设置DoIP地址时出错: {str(e)}")
            
        return None, None, None
        
    def scan_can_interfaces(self):
        try:
            self.log_message.emit("开始扫描CAN接口...")
            
            # 清空CAN接口下拉框
            self.ui.comboBox.clear()
            
            # 这里可以添加实际的CAN接口扫描逻辑
            # 例如使用python-can库扫描可用的CAN接口
            
            # 临时添加一些示例接口
            can_interfaces = ["can0", "can1", "vcan0"]
            for interface in can_interfaces:
                self.ui.comboBox.addItem(interface)
                self.log_message.emit(f"发现CAN接口: {interface}")
                
        except Exception as e:
            self.log_message.emit(f"扫描CAN接口时出错: {str(e)}")
            
    def get_server_client_addresses(self):
        """获取当前设置的服务器和客户端地址"""
        current_tab = self.ui.transport_abstract.currentIndex()
        
        if current_tab == 0:  # DoIP
            return self.auto_set_doip_addresses()
        elif current_tab == 1:  # DoCAN
            server_addr = self.ui.CAN_Server_Addr.text() or "0x0040"
            client_addr = self.ui.CAN_CLient_Addr.text() or "0x0E80"
            return None, server_addr, client_addr
            
        return None, None, None
        
    def get_current_transport_type(self):
        """获取当前传输类型"""
        return self.ui.transport_abstract.currentIndex()
        
    def is_doip_mode(self):
        """检查是否为DoIP模式"""
        return self.ui.transport_abstract.currentIndex() == 0
        
    def is_docan_mode(self):
        """检查是否为DoCAN模式"""
        return self.ui.transport_abstract.currentIndex() == 1
        
    def cleanup(self):
        """清理资源"""
        self.log_message.emit("TransportManager 清理完成")
        if self.current_transport:
            # 这里可以添加传输层清理逻辑
            pass