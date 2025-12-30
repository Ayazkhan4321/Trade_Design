# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'forgot_password.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
import mail_icon_rc
import Main_Icons_rc

class Ui_Forgot_Password(object):
    def setupUi(self, Forgot_Password):
        if not Forgot_Password.objectName():
            Forgot_Password.setObjectName(u"Forgot_Password")
        Forgot_Password.resize(400, 300)
        self.layoutWidget = QWidget(Forgot_Password)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(40, 50, 331, 221))
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lb_title_reset_password = QLabel(self.layoutWidget)
        self.lb_title_reset_password.setObjectName(u"lb_title_reset_password")
        font = QFont()
        font.setPointSize(16)
        self.lb_title_reset_password.setFont(font)

        self.verticalLayout.addWidget(self.lb_title_reset_password)

        self.lb_desc_line_forgot_pass = QLabel(self.layoutWidget)
        self.lb_desc_line_forgot_pass.setObjectName(u"lb_desc_line_forgot_pass")
        font1 = QFont()
        font1.setPointSize(10)
        self.lb_desc_line_forgot_pass.setFont(font1)
        self.lb_desc_line_forgot_pass.setWordWrap(True)

        self.verticalLayout.addWidget(self.lb_desc_line_forgot_pass)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lb_forgot_password = QLabel(self.layoutWidget)
        self.lb_forgot_password.setObjectName(u"lb_forgot_password")
        self.lb_forgot_password.setPixmap(QPixmap(u":/Main_Window/Icons/mail.png"))

        self.horizontalLayout.addWidget(self.lb_forgot_password)

        self.le_forgot_password = QLineEdit(self.layoutWidget)
        self.le_forgot_password.setObjectName(u"le_forgot_password")

        self.horizontalLayout.addWidget(self.le_forgot_password)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.pb_cancel = QPushButton(self.layoutWidget)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout_2.addWidget(self.pb_cancel)

        self.pb_send_link = QPushButton(self.layoutWidget)
        self.pb_send_link.setObjectName(u"pb_send_link")

        self.horizontalLayout_2.addWidget(self.pb_send_link)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Forgot_Password)

        QMetaObject.connectSlotsByName(Forgot_Password)
    # setupUi

    def retranslateUi(self, Forgot_Password):
        Forgot_Password.setWindowTitle(QCoreApplication.translate("Forgot_Password", u"Dialog", None))
        self.lb_title_reset_password.setText(QCoreApplication.translate("Forgot_Password", u"Reset Password", None))
        self.lb_desc_line_forgot_pass.setText(QCoreApplication.translate("Forgot_Password", u"<html><head/><body><p align=\"justify\"><span style=\" color:#ff0000;\">Enter your email or account nomber to recieve a password reset link.</span></p></body></html>", None))
        self.lb_forgot_password.setText("")
        self.le_forgot_password.setText("")
        self.le_forgot_password.setPlaceholderText(QCoreApplication.translate("Forgot_Password", u"Email or account number", None))
        self.pb_cancel.setText(QCoreApplication.translate("Forgot_Password", u"Cancel", None))
        self.pb_send_link.setText(QCoreApplication.translate("Forgot_Password", u"Send Link", None))
    # retranslateUi

