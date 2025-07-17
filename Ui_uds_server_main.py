# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'uds_server_main.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QLabel, QLineEdit, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTabWidget,
    QTextBrowser, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(475, 439)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.UDS_Server = QTabWidget(self.centralwidget)
        self.UDS_Server.setObjectName(u"UDS_Server")
        self.UDS_Server.setGeometry(QRect(10, 10, 451, 71))
        self.DoIP = QWidget()
        self.DoIP.setObjectName(u"DoIP")
        self.Net_Select = QComboBox(self.DoIP)
        self.Net_Select.setObjectName(u"Net_Select")
        self.Net_Select.setGeometry(QRect(10, 10, 141, 22))
        self.label = QLabel(self.DoIP)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(160, 10, 71, 25))
        self.doip_server_addr = QLineEdit(self.DoIP)
        self.doip_server_addr.setObjectName(u"doip_server_addr")
        self.doip_server_addr.setGeometry(QRect(230, 10, 51, 21))
        self.label_2 = QLabel(self.DoIP)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(290, 10, 71, 25))
        self.doip_client_addr = QLineEdit(self.DoIP)
        self.doip_client_addr.setObjectName(u"doip_client_addr")
        self.doip_client_addr.setGeometry(QRect(360, 10, 51, 21))
        self.UDS_Server.addTab(self.DoIP, "")
        self.DoCAN = QWidget()
        self.DoCAN.setObjectName(u"DoCAN")
        self.is_FD = QCheckBox(self.DoCAN)
        self.is_FD.setObjectName(u"is_FD")
        self.is_FD.setGeometry(QRect(400, 10, 41, 25))
        self.comboBox = QComboBox(self.DoCAN)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(10, 10, 121, 25))
        self.CAN_Server_Addr = QLineEdit(self.DoCAN)
        self.CAN_Server_Addr.setObjectName(u"CAN_Server_Addr")
        self.CAN_Server_Addr.setGeometry(QRect(210, 10, 51, 21))
        self.label_5 = QLabel(self.DoCAN)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(140, 10, 71, 25))
        self.label_6 = QLabel(self.DoCAN)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(270, 10, 71, 25))
        self.CAN_CLient_Addr = QLineEdit(self.DoCAN)
        self.CAN_CLient_Addr.setObjectName(u"CAN_CLient_Addr")
        self.CAN_CLient_Addr.setGeometry(QRect(338, 10, 51, 21))
        self.UDS_Server.addTab(self.DoCAN, "")
        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(10, 141, 451, 251))
        self.init_server = QPushButton(self.centralwidget)
        self.init_server.setObjectName(u"init_server")
        self.init_server.setGeometry(QRect(364, 100, 91, 24))
        self.config_file = QPushButton(self.centralwidget)
        self.config_file.setObjectName(u"config_file")
        self.config_file.setGeometry(QRect(10, 100, 71, 25))
        self.config_file_label = QLabel(self.centralwidget)
        self.config_file_label.setObjectName(u"config_file_label")
        self.config_file_label.setGeometry(QRect(90, 100, 271, 25))
        self.config_file_label.setFrameShape(QFrame.Shape.Box)
        self.config_file_label.setFrameShadow(QFrame.Shadow.Sunken)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 475, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.UDS_Server.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Server Addr", None))
        self.doip_server_addr.setText(QCoreApplication.translate("MainWindow", u"0x0040", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Clent Addr", None))
        self.doip_client_addr.setText(QCoreApplication.translate("MainWindow", u"0x0E80", None))
        self.UDS_Server.setTabText(self.UDS_Server.indexOf(self.DoIP), QCoreApplication.translate("MainWindow", u"DoIP_Server", None))
        self.is_FD.setText(QCoreApplication.translate("MainWindow", u"FD", None))
        self.CAN_Server_Addr.setText(QCoreApplication.translate("MainWindow", u"0x0040", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Server Addr", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Clent Addr", None))
        self.CAN_CLient_Addr.setText(QCoreApplication.translate("MainWindow", u"0x0E80", None))
        self.UDS_Server.setTabText(self.UDS_Server.indexOf(self.DoCAN), QCoreApplication.translate("MainWindow", u"DoCAN Server", None))
        self.init_server.setText(QCoreApplication.translate("MainWindow", u"Init Server", None))
        self.config_file.setText(QCoreApplication.translate("MainWindow", u"Config File", None))
        self.config_file_label.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
    # retranslateUi

