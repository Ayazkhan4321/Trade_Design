# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Login_page.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)
import Main_Icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(439, 463)
        self.layoutWidget = QWidget(Dialog)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(100, 30, 251, 391))
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.lb_logo = QLabel(self.layoutWidget)
        self.lb_logo.setObjectName(u"lb_logo")
        self.lb_logo.setPixmap(QPixmap(u":/Main_Window/Icons/Logo.png"))
        self.lb_logo.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lb_logo)

        self.lb_tagline = QLabel(self.layoutWidget)
        self.lb_tagline.setObjectName(u"lb_tagline")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.lb_tagline.setFont(font)
        self.lb_tagline.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lb_tagline)

        self.live_demo = QHBoxLayout()
        self.live_demo.setObjectName(u"live_demo")
        self.btn_live = QPushButton(self.layoutWidget)
        self.btn_live.setObjectName(u"btn_live")
        icon = QIcon()
        icon.addFile(u":/Main_Window/Icons/show_symbol.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_live.setIcon(icon)
        self.btn_live.setCheckable(True)
        self.btn_live.setChecked(True)

        self.live_demo.addWidget(self.btn_live)

        self.btn_demo = QPushButton(self.layoutWidget)
        self.btn_demo.setObjectName(u"btn_demo")
        icon1 = QIcon()
        icon1.addFile(u":/Main_Window/Icons/allow_or_prohibit_trading.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_demo.setIcon(icon1)
        self.btn_demo.setCheckable(True)

        self.live_demo.addWidget(self.btn_demo)


        self.verticalLayout_3.addLayout(self.live_demo)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lb_email = QLabel(self.layoutWidget)
        self.lb_email.setObjectName(u"lb_email")

        self.verticalLayout_2.addWidget(self.lb_email)

        self.lb_password = QLabel(self.layoutWidget)
        self.lb_password.setObjectName(u"lb_password")

        self.verticalLayout_2.addWidget(self.lb_password)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.input_email = QLineEdit(self.layoutWidget)
        self.input_email.setObjectName(u"input_email")

        self.verticalLayout.addWidget(self.input_email)

        self.input_password = QLineEdit(self.layoutWidget)
        self.input_password.setObjectName(u"input_password")

        self.verticalLayout.addWidget(self.input_password)


        self.horizontalLayout_2.addLayout(self.verticalLayout)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.rememberme = QHBoxLayout()
        self.rememberme.setObjectName(u"rememberme")
        self.cb_remember_me = QCheckBox(self.layoutWidget)
        self.cb_remember_me.setObjectName(u"cb_remember_me")

        self.rememberme.addWidget(self.cb_remember_me)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.rememberme.addItem(self.horizontalSpacer)

        self.lbl_forgot_password = QLabel(self.layoutWidget)
        self.lbl_forgot_password.setObjectName(u"lbl_forgot_password")

        self.rememberme.addWidget(self.lbl_forgot_password)


        self.verticalLayout_3.addLayout(self.rememberme)

        self.btn_signin = QPushButton(self.layoutWidget)
        self.btn_signin.setObjectName(u"btn_signin")
        self.btn_signin.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        icon2 = QIcon()
        icon2.addFile(u":/Main_Window/Icons/signin.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_signin.setIcon(icon2)

        self.verticalLayout_3.addWidget(self.btn_signin)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lb_trading = QLabel(self.layoutWidget)
        self.lb_trading.setObjectName(u"lb_trading")
        self.lb_trading.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self.horizontalLayout.addWidget(self.lb_trading)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.lbl_create_account = QLabel(self.layoutWidget)
        self.lbl_create_account.setObjectName(u"lbl_create_account")
        self.lbl_create_account.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout.addWidget(self.lbl_create_account)


        self.verticalLayout_3.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.lb_logo.setText("")
        self.lb_tagline.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Your Company Tagline Here</p></body></html>", None))
        self.btn_live.setText(QCoreApplication.translate("Dialog", u"Live", None))
        self.btn_demo.setText(QCoreApplication.translate("Dialog", u"Demo", None))
        self.lb_email.setText(QCoreApplication.translate("Dialog", u"Email :", None))
        self.lb_password.setText(QCoreApplication.translate("Dialog", u"Password :", None))
        self.input_email.setText("")
        self.input_email.setPlaceholderText(QCoreApplication.translate("Dialog", u"john@example.com", None))
        self.input_password.setPlaceholderText(QCoreApplication.translate("Dialog", u"Enter your password", None))
        self.cb_remember_me.setText(QCoreApplication.translate("Dialog", u"Remember me", None))
        self.lbl_forgot_password.setText(QCoreApplication.translate("Dialog", u"Forgot Password?", None))
        self.btn_signin.setText(QCoreApplication.translate("Dialog", u"Sign In", None))
        self.lb_trading.setText(QCoreApplication.translate("Dialog", u"New to trading?", None))
        self.lbl_create_account.setText(QCoreApplication.translate("Dialog", u"Create Account", None))
    # retranslateUi

