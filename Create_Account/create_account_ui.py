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
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QStackedWidget, QTabWidget,
    QVBoxLayout, QWidget)
import Main_Icons_rc
import Main_Icons_rc

class Ui_create_account(object):
    def setupUi(self, create_account):
        if not create_account.objectName():
            create_account.setObjectName(u"create_account")
        create_account.resize(475, 558)
        self.verticalLayout_3 = QVBoxLayout(create_account)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.stackedWidget = QStackedWidget(create_account)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.create_account_page_1 = QWidget()
        self.create_account_page_1.setObjectName(u"create_account_page_1")
        self.layoutWidget_9 = QWidget(self.create_account_page_1)
        self.layoutWidget_9.setObjectName(u"layoutWidget_9")
        self.layoutWidget_9.setGeometry(QRect(10, 20, 431, 471))
        self.verticalLayout_6 = QVBoxLayout(self.layoutWidget_9)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalSpacer_left_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_left_2)

        self.lb_logo_2 = QLabel(self.layoutWidget_9)
        self.lb_logo_2.setObjectName(u"lb_logo_2")
        self.lb_logo_2.setPixmap(QPixmap(u":/Main_Window/Icons/smallest_logo.png"))
        self.lb_logo_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_9.addWidget(self.lb_logo_2)

        self.lb_title_2 = QLabel(self.layoutWidget_9)
        self.lb_title_2.setObjectName(u"lb_title_2")
        self.lb_title_2.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)

        self.horizontalLayout_9.addWidget(self.lb_title_2)

        self.horizontalSpacer_right_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_right_2)


        self.verticalLayout_6.addLayout(self.horizontalLayout_9)

        self.lb_tagline_2 = QLabel(self.layoutWidget_9)
        self.lb_tagline_2.setObjectName(u"lb_tagline_2")
        self.lb_tagline_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout_6.addWidget(self.lb_tagline_2)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lb_one_2 = QLabel(self.layoutWidget_9)
        self.lb_one_2.setObjectName(u"lb_one_2")
        self.lb_one_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.lb_one_2)

        self.lb_3 = QLabel(self.layoutWidget_9)
        self.lb_3.setObjectName(u"lb_3")
        self.lb_3.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.lb_3)

        self.lb_4 = QLabel(self.layoutWidget_9)
        self.lb_4.setObjectName(u"lb_4")

        self.horizontalLayout_2.addWidget(self.lb_4)


        self.horizontalLayout_10.addLayout(self.horizontalLayout_2)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_2)


        self.verticalLayout_6.addLayout(self.horizontalLayout_10)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.le_first_name = QLineEdit(self.layoutWidget_9)
        self.le_first_name.setObjectName(u"le_first_name")

        self.verticalLayout_7.addWidget(self.le_first_name)

        self.le_last_name = QLineEdit(self.layoutWidget_9)
        self.le_last_name.setObjectName(u"le_last_name")

        self.verticalLayout_7.addWidget(self.le_last_name)

        self.le_email = QLineEdit(self.layoutWidget_9)
        self.le_email.setObjectName(u"le_email")

        self.verticalLayout_7.addWidget(self.le_email)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.cmb_country_code = QComboBox(self.layoutWidget_9)
        self.cmb_country_code.setObjectName(u"cmb_country_code")

        self.horizontalLayout_12.addWidget(self.cmb_country_code)

        self.le_number = QLineEdit(self.layoutWidget_9)
        self.le_number.setObjectName(u"le_number")

        self.horizontalLayout_12.addWidget(self.le_number)


        self.verticalLayout_7.addLayout(self.horizontalLayout_12)

        self.le_refferal_code = QLineEdit(self.layoutWidget_9)
        self.le_refferal_code.setObjectName(u"le_refferal_code")

        self.verticalLayout_7.addWidget(self.le_refferal_code)


        self.verticalLayout_6.addLayout(self.verticalLayout_7)

        self.pb_continue_to_account_selection = QPushButton(self.layoutWidget_9)
        self.pb_continue_to_account_selection.setObjectName(u"pb_continue_to_account_selection")
        icon = QIcon()
        icon.addFile(u":/Main_Window/Icons/Login_to_trade.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_continue_to_account_selection.setIcon(icon)

        self.verticalLayout_6.addWidget(self.pb_continue_to_account_selection)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_3)

        self.label = QLabel(self.layoutWidget_9)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_13.addWidget(self.label)

        self.lb_signin = QLabel(self.layoutWidget_9)
        self.lb_signin.setObjectName(u"lb_signin")
        self.lb_signin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_13.addWidget(self.lb_signin)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_4)


        self.verticalLayout_6.addLayout(self.horizontalLayout_13)

        self.stackedWidget.addWidget(self.create_account_page_1)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.Live_Demo_tab_2 = QTabWidget(self.page)
        self.Live_Demo_tab_2.setObjectName(u"Live_Demo_tab_2")
        self.Live_Demo_tab_2.setGeometry(QRect(10, 180, 441, 171))
        self.Live_tab_2 = QWidget()
        self.Live_tab_2.setObjectName(u"Live_tab_2")
        self.lb_live_2 = QLabel(self.Live_tab_2)
        self.lb_live_2.setObjectName(u"lb_live_2")
        self.lb_live_2.setGeometry(QRect(0, 0, 51, 16))
        self.layoutWidget = QWidget(self.Live_tab_2)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(10, 50, 411, 41))
        self.horizontalLayout_8 = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.pb_classic_3 = QPushButton(self.layoutWidget)
        self.pb_classic_3.setObjectName(u"pb_classic_3")
        self.pb_classic_3.setCheckable(True)
        self.pb_classic_3.setChecked(True)

        self.horizontalLayout_8.addWidget(self.pb_classic_3)

        self.pb_premium_3 = QPushButton(self.layoutWidget)
        self.pb_premium_3.setObjectName(u"pb_premium_3")
        self.pb_premium_3.setCheckable(True)

        self.horizontalLayout_8.addWidget(self.pb_premium_3)

        self.pb_other_3 = QPushButton(self.layoutWidget)
        self.pb_other_3.setObjectName(u"pb_other_3")
        self.pb_other_3.setCheckable(True)

        self.horizontalLayout_8.addWidget(self.pb_other_3)

        self.pb_ecn_3 = QPushButton(self.layoutWidget)
        self.pb_ecn_3.setObjectName(u"pb_ecn_3")
        self.pb_ecn_3.setCheckable(True)

        self.horizontalLayout_8.addWidget(self.pb_ecn_3)

        icon1 = QIcon()
        icon1.addFile(u":/Main_Window/Icons/show_symbol.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.Live_Demo_tab_2.addTab(self.Live_tab_2, icon1, "")
        self.demo_tab_2 = QWidget()
        self.demo_tab_2.setObjectName(u"demo_tab_2")
        self.ld_demo_2 = QLabel(self.demo_tab_2)
        self.ld_demo_2.setObjectName(u"ld_demo_2")
        self.ld_demo_2.setGeometry(QRect(0, 0, 51, 16))
        self.layoutWidget_2 = QWidget(self.demo_tab_2)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(10, 30, 411, 71))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.pb_demo_2 = QPushButton(self.layoutWidget_2)
        self.pb_demo_2.setObjectName(u"pb_demo_2")

        self.horizontalLayout.addWidget(self.pb_demo_2)

        self.pb_demo_grp = QPushButton(self.layoutWidget_2)
        self.pb_demo_grp.setObjectName(u"pb_demo_grp")

        self.horizontalLayout.addWidget(self.pb_demo_grp)

        self.pb_new_grp = QPushButton(self.layoutWidget_2)
        self.pb_new_grp.setObjectName(u"pb_new_grp")

        self.horizontalLayout.addWidget(self.pb_new_grp)

        icon2 = QIcon()
        icon2.addFile(u":/Main_Window/Icons/allow_or_prohibit_trading.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.Live_Demo_tab_2.addTab(self.demo_tab_2, icon2, "")
        self.layoutWidget_10 = QWidget(self.page)
        self.layoutWidget_10.setObjectName(u"layoutWidget_10")
        self.layoutWidget_10.setGeometry(QRect(8, 10, 431, 141))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget_10)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_left = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_left)

        self.lb_logo = QLabel(self.layoutWidget_10)
        self.lb_logo.setObjectName(u"lb_logo")
        self.lb_logo.setPixmap(QPixmap(u":/Main_Window/Icons/smallest_logo.png"))
        self.lb_logo.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.lb_logo)

        self.lb_title = QLabel(self.layoutWidget_10)
        self.lb_title.setObjectName(u"lb_title")
        self.lb_title.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.lb_title)

        self.horizontalSpacer_right = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_right)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.lb_tagline = QLabel(self.layoutWidget_10)
        self.lb_tagline.setObjectName(u"lb_tagline")
        self.lb_tagline.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.lb_tagline)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_5)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.lb_one = QLabel(self.layoutWidget_10)
        self.lb_one.setObjectName(u"lb_one")
        self.lb_one.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_19.addWidget(self.lb_one)

        self.lb_2 = QLabel(self.layoutWidget_10)
        self.lb_2.setObjectName(u"lb_2")
        self.lb_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_19.addWidget(self.lb_2)

        self.lb_7 = QLabel(self.layoutWidget_10)
        self.lb_7.setObjectName(u"lb_7")

        self.horizontalLayout_19.addWidget(self.lb_7)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_19)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_6)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.layoutWidget_4 = QWidget(self.page)
        self.layoutWidget_4.setObjectName(u"layoutWidget_4")
        self.layoutWidget_4.setGeometry(QRect(20, 380, 431, 161))
        self.verticalLayout_5 = QVBoxLayout(self.layoutWidget_4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.cb_terms_privacy_policy = QCheckBox(self.layoutWidget_4)
        self.cb_terms_privacy_policy.setObjectName(u"cb_terms_privacy_policy")

        self.verticalLayout_5.addWidget(self.cb_terms_privacy_policy)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_9)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pb_continue_to_verification = QPushButton(self.layoutWidget_4)
        self.pb_continue_to_verification.setObjectName(u"pb_continue_to_verification")

        self.verticalLayout.addWidget(self.pb_continue_to_verification)

        self.pb_back_2 = QPushButton(self.layoutWidget_4)
        self.pb_back_2.setObjectName(u"pb_back_2")

        self.verticalLayout.addWidget(self.pb_back_2)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_10)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.layoutWidget_3 = QWidget(self.page_2)
        self.layoutWidget_3.setObjectName(u"layoutWidget_3")
        self.layoutWidget_3.setGeometry(QRect(40, 80, 371, 451))
        self.verticalLayout_8 = QVBoxLayout(self.layoutWidget_3)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer_left_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_left_4)

        self.lb_logo_4 = QLabel(self.layoutWidget_3)
        self.lb_logo_4.setObjectName(u"lb_logo_4")
        self.lb_logo_4.setPixmap(QPixmap(u":/Main_Window/Icons/smallest_logo.png"))
        self.lb_logo_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.lb_logo_4)

        self.lb_title_4 = QLabel(self.layoutWidget_3)
        self.lb_title_4.setObjectName(u"lb_title_4")
        self.lb_title_4.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.lb_title_4)

        self.horizontalSpacer_right_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_right_4)


        self.verticalLayout_9.addLayout(self.horizontalLayout_6)

        self.lb_tagline_4 = QLabel(self.layoutWidget_3)
        self.lb_tagline_4.setObjectName(u"lb_tagline_4")
        self.lb_tagline_4.setAlignment(Qt.AlignCenter)

        self.verticalLayout_9.addWidget(self.lb_tagline_4)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_7)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.lb_one_4 = QLabel(self.layoutWidget_3)
        self.lb_one_4.setObjectName(u"lb_one_4")
        self.lb_one_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_21.addWidget(self.lb_one_4)

        self.lb_8 = QLabel(self.layoutWidget_3)
        self.lb_8.setObjectName(u"lb_8")
        self.lb_8.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_21.addWidget(self.lb_8)

        self.lb_9 = QLabel(self.layoutWidget_3)
        self.lb_9.setObjectName(u"lb_9")

        self.horizontalLayout_21.addWidget(self.lb_9)


        self.horizontalLayout_20.addLayout(self.horizontalLayout_21)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_8)


        self.verticalLayout_9.addLayout(self.horizontalLayout_20)


        self.verticalLayout_8.addLayout(self.verticalLayout_9)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lb_title_line_3 = QLabel(self.layoutWidget_3)
        self.lb_title_line_3.setObjectName(u"lb_title_line_3")

        self.verticalLayout_2.addWidget(self.lb_title_line_3)

        self.le_code = QLineEdit(self.layoutWidget_3)
        self.le_code.setObjectName(u"le_code")

        self.verticalLayout_2.addWidget(self.le_code)

        self.pb_verify = QPushButton(self.layoutWidget_3)
        self.pb_verify.setObjectName(u"pb_verify")

        self.verticalLayout_2.addWidget(self.pb_verify)

        self.pb_back = QPushButton(self.layoutWidget_3)
        self.pb_back.setObjectName(u"pb_back")

        self.verticalLayout_2.addWidget(self.pb_back)


        self.verticalLayout_8.addLayout(self.verticalLayout_2)

        self.stackedWidget.addWidget(self.page_2)

        self.verticalLayout_3.addWidget(self.stackedWidget)


        self.retranslateUi(create_account)

        self.stackedWidget.setCurrentIndex(0)
        self.Live_Demo_tab_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(create_account)
    # setupUi

    def retranslateUi(self, create_account):
        create_account.setWindowTitle(QCoreApplication.translate("create_account", u"Dialog", None))
        self.lb_logo_2.setText("")
        self.lb_title_2.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p align=\"justify\"><span style=\" font-size:16pt; font-weight:600; color:#ff0000;\">Create Account</span></p></body></html>", None))
        self.lb_tagline_2.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" color:#ff0000;\">Your Company tagline here</span></p></body></html>", None))
        self.lb_one_2.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">1</span></p></body></html>", None))
        self.lb_3.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">2</span></p></body></html>", None))
        self.lb_4.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">3</span></p></body></html>", None))
        self.le_first_name.setPlaceholderText(QCoreApplication.translate("create_account", u"First Name", None))
        self.le_last_name.setPlaceholderText(QCoreApplication.translate("create_account", u"Last Name", None))
        self.le_email.setPlaceholderText(QCoreApplication.translate("create_account", u"Email", None))
        self.le_number.setPlaceholderText(QCoreApplication.translate("create_account", u"Phone number", None))
        self.le_refferal_code.setPlaceholderText(QCoreApplication.translate("create_account", u"Refferal Code", None))
        self.pb_continue_to_account_selection.setText(QCoreApplication.translate("create_account", u"Continue to Account Selection", None))
        self.label.setText(QCoreApplication.translate("create_account", u"Already have the Account?", None))
        self.lb_signin.setText(QCoreApplication.translate("create_account", u"Sign in", None))
        self.lb_live_2.setText(QCoreApplication.translate("create_account", u"Account type", None))
        self.pb_classic_3.setText(QCoreApplication.translate("create_account", u"Classic", None))
        self.pb_premium_3.setText(QCoreApplication.translate("create_account", u"Premium", None))
        self.pb_other_3.setText(QCoreApplication.translate("create_account", u"Others", None))
        self.pb_ecn_3.setText(QCoreApplication.translate("create_account", u"ECN", None))
        self.Live_Demo_tab_2.setTabText(self.Live_Demo_tab_2.indexOf(self.Live_tab_2), QCoreApplication.translate("create_account", u"Live", None))
        self.ld_demo_2.setText(QCoreApplication.translate("create_account", u"Account Type", None))
        self.pb_demo_2.setText(QCoreApplication.translate("create_account", u"ECNDemoGrp", None))
        self.pb_demo_grp.setText(QCoreApplication.translate("create_account", u"Demo Grp", None))
        self.pb_new_grp.setText(QCoreApplication.translate("create_account", u"New Group 1", None))
        self.Live_Demo_tab_2.setTabText(self.Live_Demo_tab_2.indexOf(self.demo_tab_2), QCoreApplication.translate("create_account", u"Demo", None))
        self.lb_logo.setText("")
        self.lb_title.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p align=\"justify\"><span style=\" font-size:16pt; font-weight:600; color:#ff0000;\">Create Account</span></p></body></html>", None))
        self.lb_tagline.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" color:#ff0000;\">Your Company tagline here</span></p></body></html>", None))
        self.lb_one.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">1</span></p></body></html>", None))
        self.lb_2.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">2</span></p></body></html>", None))
        self.lb_7.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">3</span></p></body></html>", None))
        self.cb_terms_privacy_policy.setText(QCoreApplication.translate("create_account", u"I agree to the Terms of Service and Privacy Policy", None))
        self.pb_continue_to_verification.setText(QCoreApplication.translate("create_account", u"Continue to Verification", None))
        self.pb_back_2.setText(QCoreApplication.translate("create_account", u"Back to Registration", None))
        self.lb_logo_4.setText("")
        self.lb_title_4.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p align=\"justify\"><span style=\" font-size:16pt; font-weight:600; color:#ff0000;\">Create Account</span></p></body></html>", None))
        self.lb_tagline_4.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" color:#ff0000;\">Your Company tagline here</span></p></body></html>", None))
        self.lb_one_4.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">1</span></p></body></html>", None))
        self.lb_8.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">2</span></p></body></html>", None))
        self.lb_9.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:10pt;\">3</span></p></body></html>", None))
        self.lb_title_line_3.setText(QCoreApplication.translate("create_account", u"<html><head/><body><p><span style=\" font-size:12pt; font-weight:600; color:#ff0000;\">Please Enter your Code</span></p></body></html>", None))
        self.le_code.setPlaceholderText(QCoreApplication.translate("create_account", u"Enter your code", None))
        self.pb_verify.setText(QCoreApplication.translate("create_account", u"Verify & Continue to Login", None))
        self.pb_back.setText(QCoreApplication.translate("create_account", u"Back to Registration", None))
    # retranslateUi

