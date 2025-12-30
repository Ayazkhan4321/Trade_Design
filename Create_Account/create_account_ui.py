# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'create_account.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QStackedWidget, QTabWidget,
    QVBoxLayout, QWidget)
import Main_Icons_rc
import Main_Icons_rc

class Ui_create_account(object):
    def setupUi(self, create_account):
        if not create_account.objectName():
            create_account.setObjectName(u"create_account")
        create_account.resize(574, 413)
        self.verticalLayout_3 = QVBoxLayout(create_account)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.stackedWidget = QStackedWidget(create_account)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.create_account_page_1 = QWidget()
        self.create_account_page_1.setObjectName(u"create_account_page_1")
        self.gridLayout = QGridLayout(self.create_account_page_1)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lb_logo = QLabel(self.create_account_page_1)
        self.lb_logo.setObjectName(u"lb_logo")
        self.lb_logo.setPixmap(QPixmap(u":/Main_Window/Icons/smallest_logo.png"))
        self.lb_logo.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.lb_logo)

        self.lb_title = QLabel(self.create_account_page_1)
        self.lb_title.setObjectName(u"lb_title")
        self.lb_title.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.lb_title)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.lb_tagline = QLabel(self.create_account_page_1)
        self.lb_tagline.setObjectName(u"lb_tagline")
        self.lb_tagline.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.lb_tagline)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.lb_one = QLabel(self.create_account_page_1)
        self.lb_one.setObjectName(u"lb_one")
        self.lb_one.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_4.addWidget(self.lb_one)

        self.lb_2 = QLabel(self.create_account_page_1)
        self.lb_2.setObjectName(u"lb_2")
        self.lb_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_4.addWidget(self.lb_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.le_first_name = QLineEdit(self.create_account_page_1)
        self.le_first_name.setObjectName(u"le_first_name")

        self.horizontalLayout.addWidget(self.le_first_name)

        self.le_last_name = QLineEdit(self.create_account_page_1)
        self.le_last_name.setObjectName(u"le_last_name")

        self.horizontalLayout.addWidget(self.le_last_name)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.cmb_country_code = QComboBox(self.create_account_page_1)
        self.cmb_country_code.setObjectName(u"cmb_country_code")

        self.horizontalLayout_5.addWidget(self.cmb_country_code)

        self.le_number = QLineEdit(self.create_account_page_1)
        self.le_number.setObjectName(u"le_number")

        self.horizontalLayout_5.addWidget(self.le_number)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.le_email = QLineEdit(self.create_account_page_1)
        self.le_email.setObjectName(u"le_email")

        self.verticalLayout.addWidget(self.le_email)

        self.le_refferal_code = QLineEdit(self.create_account_page_1)
        self.le_refferal_code.setObjectName(u"le_refferal_code")

        self.verticalLayout.addWidget(self.le_refferal_code)

        self.Live_Demo_tab = QTabWidget(self.create_account_page_1)
        self.Live_Demo_tab.setObjectName(u"Live_Demo_tab")
        self.Live_tab = QWidget()
        self.Live_tab.setObjectName(u"Live_tab")
        self.lb_live = QLabel(self.Live_tab)
        self.lb_live.setObjectName(u"lb_live")
        self.lb_live.setGeometry(QRect(0, 0, 51, 16))
        self.layoutWidget_2 = QWidget(self.Live_tab)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(20, 20, 238, 19))
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.pb_classic = QPushButton(self.layoutWidget_2)
        self.pb_classic.setObjectName(u"pb_classic")
        self.pb_classic.setCheckable(True)
        self.pb_classic.setChecked(True)

        self.horizontalLayout_2.addWidget(self.pb_classic)

        self.pb_ecn = QPushButton(self.layoutWidget_2)
        self.pb_ecn.setObjectName(u"pb_ecn")
        self.pb_ecn.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.pb_ecn)

        self.pb_premium = QPushButton(self.layoutWidget_2)
        self.pb_premium.setObjectName(u"pb_premium")
        self.pb_premium.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.pb_premium)

        self.pb_other = QPushButton(self.layoutWidget_2)
        self.pb_other.setObjectName(u"pb_other")
        self.pb_other.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.pb_other)

        icon = QIcon()
        icon.addFile(u":/Main_Window/Icons/show_symbol.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.Live_Demo_tab.addTab(self.Live_tab, icon, "")
        self.demo_tab = QWidget()
        self.demo_tab.setObjectName(u"demo_tab")
        self.ld_demo = QLabel(self.demo_tab)
        self.ld_demo.setObjectName(u"ld_demo")
        self.ld_demo.setGeometry(QRect(0, 0, 51, 16))
        self.pb_demo = QPushButton(self.demo_tab)
        self.pb_demo.setObjectName(u"pb_demo")
        self.pb_demo.setGeometry(QRect(20, 20, 56, 17))
        icon1 = QIcon()
        icon1.addFile(u":/Main_Window/Icons/allow_or_prohibit_trading.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.Live_Demo_tab.addTab(self.demo_tab, icon1, "")

        self.verticalLayout.addWidget(self.Live_Demo_tab)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.cb_terms_privacy_policy = QCheckBox(self.create_account_page_1)
        self.cb_terms_privacy_policy.setObjectName(u"cb_terms_privacy_policy")

        self.verticalLayout_2.addWidget(self.cb_terms_privacy_policy)

        self.pb_continue_verify = QPushButton(self.create_account_page_1)
        self.pb_continue_verify.setObjectName(u"pb_continue_verify")
        icon2 = QIcon()
        icon2.addFile(u":/Main_Window/Icons/Login_to_trade.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_continue_verify.setIcon(icon2)

        self.verticalLayout_2.addWidget(self.pb_continue_verify)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_2 = QLabel(self.create_account_page_1)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.label_2)

        self.lb_signin = QLabel(self.create_account_page_1)
        self.lb_signin.setObjectName(u"lb_signin")
        self.lb_signin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_6.addWidget(self.lb_signin)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)


        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.create_account_page_1)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.layoutWidget_3 = QWidget(self.page_2)
        self.layoutWidget_3.setObjectName(u"layoutWidget_3")
        self.layoutWidget_3.setGeometry(QRect(200, 100, 201, 151))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.lb_title_line = QLabel(self.layoutWidget_3)
        self.lb_title_line.setObjectName(u"lb_title_line")

        self.verticalLayout_4.addWidget(self.lb_title_line)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lb_one_page2 = QLabel(self.layoutWidget_3)
        self.lb_one_page2.setObjectName(u"lb_one_page2")
        self.lb_one_page2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.lb_one_page2)

        self.lb_2_page_2 = QLabel(self.layoutWidget_3)
        self.lb_2_page_2.setObjectName(u"lb_2_page_2")
        self.lb_2_page_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.lb_2_page_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_7)

        self.le_code = QLineEdit(self.layoutWidget_3)
        self.le_code.setObjectName(u"le_code")

        self.verticalLayout_4.addWidget(self.le_code)

        self.pb_verify = QPushButton(self.layoutWidget_3)
        self.pb_verify.setObjectName(u"pb_verify")

        self.verticalLayout_4.addWidget(self.pb_verify)

        self.pb_back = QPushButton(self.layoutWidget_3)
        self.pb_back.setObjectName(u"pb_back")

        self.verticalLayout_4.addWidget(self.pb_back)

        self.stackedWidget.addWidget(self.page_2)

        self.verticalLayout_3.addWidget(self.stackedWidget)


        self.retranslateUi(create_account)

        self.stackedWidget.setCurrentIndex(0)
        self.Live_Demo_tab.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(create_account)
    # setupUi

    def retranslateUi(self, create_account):
        create_account.setWindowTitle(QCoreApplication.translate("create_account", u"Dialog", None))
        self.lb_logo.setText("")
        self.lb_title.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p align=\"justify\"><span style=\" font-size:16pt; font-weight:600; color:#ff0000;\">Create Account</span></p></body></html>", None))
        self.lb_tagline.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" color:#ff0000;\">Your Company tagline here</span></p></body></html>", None))
        self.lb_one.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">1</span></p></body></html>", None))
        self.lb_2.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">2</span></p></body></html>", None))
        self.le_first_name.setPlaceholderText(QCoreApplication.translate("create_account", u"First Name", None))
        self.le_last_name.setPlaceholderText(QCoreApplication.translate("create_account", u"Last Name", None))
        self.le_number.setPlaceholderText(QCoreApplication.translate("create_account", u"Phone number", None))
        self.le_email.setPlaceholderText(QCoreApplication.translate("create_account", u"Email", None))
        self.le_refferal_code.setPlaceholderText(QCoreApplication.translate("create_account", u"Refferal Code", None))
        self.lb_live.setText(QCoreApplication.translate("create_account", u"Account type", None))
        self.pb_classic.setText(QCoreApplication.translate("create_account", u"Classic", None))
        self.pb_ecn.setText(QCoreApplication.translate("create_account", u"ECN", None))
        self.pb_premium.setText(QCoreApplication.translate("create_account", u"Premium", None))
        self.pb_other.setText(QCoreApplication.translate("create_account", u"Others", None))
        self.Live_Demo_tab.setTabText(self.Live_Demo_tab.indexOf(self.Live_tab), QCoreApplication.translate("create_account", u"Live", None))
        self.ld_demo.setText(QCoreApplication.translate("create_account", u"Account Type", None))
        self.pb_demo.setText(QCoreApplication.translate("create_account", u"ECNDemoGrp", None))
        self.Live_Demo_tab.setTabText(self.Live_Demo_tab.indexOf(self.demo_tab), QCoreApplication.translate("create_account", u"Demo", None))
        self.cb_terms_privacy_policy.setText(QCoreApplication.translate("create_account", u"I agree to the Terms of Service and Privacy Policy", None))
        self.pb_continue_verify.setText(QCoreApplication.translate("create_account", u"Continue to Verification", None))
        self.label_2.setText(QCoreApplication.translate("create_account", u"Already have the Account?", None))
        self.lb_signin.setText(QCoreApplication.translate("create_account", u"Sign in", None))
        self.lb_title_line.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:12pt; font-weight:600; color:#ff0000;\">Please Enter your Code</span></p></body></html>", None))
        self.lb_one_page2.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">1</span></p></body></html>", None))
        self.lb_2_page_2.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">2</span></p></body></html>", None))
        self.le_code.setPlaceholderText(QCoreApplication.translate("create_account", u"Enter your code", None))
        self.pb_verify.setText(QCoreApplication.translate("create_account", u"Verify & Continue to Login", None))
        self.pb_back.setText(QCoreApplication.translate("create_account", u"Back to Registration", None))
    # retranslateUi

