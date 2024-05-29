# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gff.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QComboBox,
    QDoubleSpinBox, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMenuBar, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QSplitter,
    QStackedWidget, QTreeView, QVBoxLayout, QWidget)

from toolset.gui.widgets.long_spinbox import LongSpinBox

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(668, 486)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionSetTLK = QAction(MainWindow)
        self.actionSetTLK.setObjectName(u"actionSetTLK")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.treeView = QTreeView(self.splitter)
        self.treeView.setObjectName(u"treeView")
        font = QFont()
        font.setFamilies([u"Courier New"])
        self.treeView.setFont(font)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.setAlternatingRowColors(True)
        self.splitter.addWidget(self.treeView)
        self.treeView.header().setVisible(False)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.fieldBox = QGroupBox(self.layoutWidget)
        self.fieldBox.setObjectName(u"fieldBox")
        self.fieldBox.setEnabled(False)
        self.formLayout = QFormLayout(self.fieldBox)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.fieldBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.labelEdit = QLineEdit(self.fieldBox)
        self.labelEdit.setObjectName(u"labelEdit")
        self.labelEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.labelEdit)

        self.label_2 = QLabel(self.fieldBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.typeCombo = QComboBox(self.fieldBox)
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.addItem("")
        self.typeCombo.setObjectName(u"typeCombo")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.typeCombo)


        self.verticalLayout.addWidget(self.fieldBox)

        self.pages = QStackedWidget(self.layoutWidget)
        self.pages.setObjectName(u"pages")
        self.pages.setFrameShape(QFrame.StyledPanel)
        self.linePage = QWidget()
        self.linePage.setObjectName(u"linePage")
        self.verticalLayout_2 = QVBoxLayout(self.linePage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lineEdit = QLineEdit(self.linePage)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setMaxLength(16)

        self.verticalLayout_2.addWidget(self.lineEdit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.pages.addWidget(self.linePage)
        self.intPage = QWidget()
        self.intPage.setObjectName(u"intPage")
        self.verticalLayout_5 = QVBoxLayout(self.intPage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.intSpin = LongSpinBox(self.intPage)
        self.intSpin.setObjectName(u"intSpin")

        self.verticalLayout_5.addWidget(self.intSpin)

        self.verticalSpacer_3 = QSpacerItem(20, 280, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.pages.addWidget(self.intPage)
        self.blankPage = QWidget()
        self.blankPage.setObjectName(u"blankPage")
        self.pages.addWidget(self.blankPage)
        self.floatPage = QWidget()
        self.floatPage.setObjectName(u"floatPage")
        self.verticalLayout_4 = QVBoxLayout(self.floatPage)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.floatSpin = QDoubleSpinBox(self.floatPage)
        self.floatSpin.setObjectName(u"floatSpin")
        self.floatSpin.setDecimals(6)
        self.floatSpin.setMinimum(-10000000000000000000000.000000000000000)
        self.floatSpin.setMaximum(99999999999999991611392.000000000000000)
        self.floatSpin.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)

        self.verticalLayout_4.addWidget(self.floatSpin)

        self.verticalSpacer_2 = QSpacerItem(20, 280, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.pages.addWidget(self.floatPage)
        self.vector3Page = QWidget()
        self.vector3Page.setObjectName(u"vector3Page")
        self.formLayout_3 = QFormLayout(self.vector3Page)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_3 = QLabel(self.vector3Page)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.xVec3Spin = QDoubleSpinBox(self.vector3Page)
        self.xVec3Spin.setObjectName(u"xVec3Spin")
        self.xVec3Spin.setDecimals(6)
        self.xVec3Spin.setMinimum(-99999999999999991433150857216.000000000000000)
        self.xVec3Spin.setMaximum(100000000000000004764729344.000000000000000)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.xVec3Spin)

        self.label_4 = QLabel(self.vector3Page)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.yVec3Spin = QDoubleSpinBox(self.vector3Page)
        self.yVec3Spin.setObjectName(u"yVec3Spin")
        self.yVec3Spin.setDecimals(6)
        self.yVec3Spin.setMinimum(-99999999999999991433150857216.000000000000000)
        self.yVec3Spin.setMaximum(100000000000000004764729344.000000000000000)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.yVec3Spin)

        self.label_5 = QLabel(self.vector3Page)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_5)

        self.zVec3Spin = QDoubleSpinBox(self.vector3Page)
        self.zVec3Spin.setObjectName(u"zVec3Spin")
        self.zVec3Spin.setDecimals(6)
        self.zVec3Spin.setMinimum(-99999999999999991433150857216.000000000000000)
        self.zVec3Spin.setMaximum(100000000000000004764729344.000000000000000)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.zVec3Spin)

        self.pages.addWidget(self.vector3Page)
        self.vector4Page = QWidget()
        self.vector4Page.setObjectName(u"vector4Page")
        self.formLayout_2 = QFormLayout(self.vector4Page)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_10 = QLabel(self.vector4Page)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_10)

        self.xVec4Spin = QDoubleSpinBox(self.vector4Page)
        self.xVec4Spin.setObjectName(u"xVec4Spin")
        self.xVec4Spin.setDecimals(8)
        self.xVec4Spin.setMinimum(-9999999999999999583119736832.000000000000000)
        self.xVec4Spin.setMaximum(99999999999999991433150857216.000000000000000)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.xVec4Spin)

        self.label_8 = QLabel(self.vector4Page)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_8)

        self.yVec4Spin = QDoubleSpinBox(self.vector4Page)
        self.yVec4Spin.setObjectName(u"yVec4Spin")
        self.yVec4Spin.setDecimals(8)
        self.yVec4Spin.setMinimum(-9999999999999999583119736832.000000000000000)
        self.yVec4Spin.setMaximum(99999999999999991433150857216.000000000000000)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.yVec4Spin)

        self.label_9 = QLabel(self.vector4Page)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_9)

        self.label_7 = QLabel(self.vector4Page)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_7)

        self.zVec4Spin = QDoubleSpinBox(self.vector4Page)
        self.zVec4Spin.setObjectName(u"zVec4Spin")
        self.zVec4Spin.setDecimals(8)
        self.zVec4Spin.setMinimum(-9999999999999999583119736832.000000000000000)
        self.zVec4Spin.setMaximum(99999999999999991433150857216.000000000000000)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.zVec4Spin)

        self.wVec4Spin = QDoubleSpinBox(self.vector4Page)
        self.wVec4Spin.setObjectName(u"wVec4Spin")
        self.wVec4Spin.setDecimals(8)
        self.wVec4Spin.setMinimum(-9999999999999999583119736832.000000000000000)
        self.wVec4Spin.setMaximum(99999999999999991433150857216.000000000000000)

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.wVec4Spin)

        self.pages.addWidget(self.vector4Page)
        self.textPage = QWidget()
        self.textPage.setObjectName(u"textPage")
        self.gridLayout = QGridLayout(self.textPage)
        self.gridLayout.setObjectName(u"gridLayout")
        self.textEdit = QPlainTextEdit(self.textPage)
        self.textEdit.setObjectName(u"textEdit")

        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)

        self.pages.addWidget(self.textPage)
        self.substringPage = QWidget()
        self.substringPage.setObjectName(u"substringPage")
        self.verticalLayout_3 = QVBoxLayout(self.substringPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_6 = QLabel(self.substringPage)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_3.addWidget(self.label_6)

        self.stringrefSpin = QSpinBox(self.substringPage)
        self.stringrefSpin.setObjectName(u"stringrefSpin")
        self.stringrefSpin.setMinimum(-1)
        self.stringrefSpin.setMaximum(999999999)

        self.horizontalLayout_3.addWidget(self.stringrefSpin)

        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.tlkTextEdit = QPlainTextEdit(self.substringPage)
        self.tlkTextEdit.setObjectName(u"tlkTextEdit")
        self.tlkTextEdit.setEnabled(False)
        self.tlkTextEdit.setMinimumSize(QSize(0, 40))
        self.tlkTextEdit.setMaximumSize(QSize(16777215, 40))
        self.tlkTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.tlkTextEdit)

        self.line = QFrame(self.substringPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.substringLangCombo = QComboBox(self.substringPage)
        self.substringLangCombo.addItem("")
        self.substringLangCombo.addItem("")
        self.substringLangCombo.addItem("")
        self.substringLangCombo.addItem("")
        self.substringLangCombo.addItem("")
        self.substringLangCombo.addItem("")
        self.substringLangCombo.setObjectName(u"substringLangCombo")

        self.horizontalLayout_2.addWidget(self.substringLangCombo)

        self.substringGenderCombo = QComboBox(self.substringPage)
        self.substringGenderCombo.addItem("")
        self.substringGenderCombo.addItem("")
        self.substringGenderCombo.setObjectName(u"substringGenderCombo")

        self.horizontalLayout_2.addWidget(self.substringGenderCombo)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.addSubstringButton = QPushButton(self.substringPage)
        self.addSubstringButton.setObjectName(u"addSubstringButton")

        self.horizontalLayout_4.addWidget(self.addSubstringButton)

        self.removeSubstringButton = QPushButton(self.substringPage)
        self.removeSubstringButton.setObjectName(u"removeSubstringButton")

        self.horizontalLayout_4.addWidget(self.removeSubstringButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.line_2 = QFrame(self.substringPage)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line_2)

        self.substringList = QListWidget(self.substringPage)
        self.substringList.setObjectName(u"substringList")
        self.substringList.setMaximumSize(QSize(16777215, 100))
        self.substringList.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.verticalLayout_3.addWidget(self.substringList)

        self.substringEdit = QPlainTextEdit(self.substringPage)
        self.substringEdit.setObjectName(u"substringEdit")

        self.verticalLayout_3.addWidget(self.substringEdit)

        self.pages.addWidget(self.substringPage)

        self.verticalLayout.addWidget(self.pages)

        self.splitter.addWidget(self.layoutWidget)

        self.gridLayout_2.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 668, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuTools.addAction(self.actionSetTLK)

        self.retranslateUi(MainWindow)

        self.pages.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionSetTLK.setText(QCoreApplication.translate("MainWindow", u"Set TLK", None))
        self.fieldBox.setTitle("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Label:", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Type:", None))
        self.typeCombo.setItemText(0, QCoreApplication.translate("MainWindow", u"UInt8", None))
        self.typeCombo.setItemText(1, QCoreApplication.translate("MainWindow", u"Int8", None))
        self.typeCombo.setItemText(2, QCoreApplication.translate("MainWindow", u"UInt16", None))
        self.typeCombo.setItemText(3, QCoreApplication.translate("MainWindow", u"Int16", None))
        self.typeCombo.setItemText(4, QCoreApplication.translate("MainWindow", u"UInt32", None))
        self.typeCombo.setItemText(5, QCoreApplication.translate("MainWindow", u"Int32", None))
        self.typeCombo.setItemText(6, QCoreApplication.translate("MainWindow", u"UInt64", None))
        self.typeCombo.setItemText(7, QCoreApplication.translate("MainWindow", u"Int64", None))
        self.typeCombo.setItemText(8, QCoreApplication.translate("MainWindow", u"Single", None))
        self.typeCombo.setItemText(9, QCoreApplication.translate("MainWindow", u"Double", None))
        self.typeCombo.setItemText(10, QCoreApplication.translate("MainWindow", u"String", None))
        self.typeCombo.setItemText(11, QCoreApplication.translate("MainWindow", u"ResRef", None))
        self.typeCombo.setItemText(12, QCoreApplication.translate("MainWindow", u"LocalizedString", None))
        self.typeCombo.setItemText(13, QCoreApplication.translate("MainWindow", u"Binary", None))
        self.typeCombo.setItemText(14, QCoreApplication.translate("MainWindow", u"Struct", None))
        self.typeCombo.setItemText(15, QCoreApplication.translate("MainWindow", u"List", None))
        self.typeCombo.setItemText(16, QCoreApplication.translate("MainWindow", u"Vector4", None))
        self.typeCombo.setItemText(17, QCoreApplication.translate("MainWindow", u"Vector3", None))

        self.label_3.setText(QCoreApplication.translate("MainWindow", u"X", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Z", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"X", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Z", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"W", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"StringRef:", None))
        self.substringLangCombo.setItemText(0, QCoreApplication.translate("MainWindow", u"English", None))
        self.substringLangCombo.setItemText(1, QCoreApplication.translate("MainWindow", u"French", None))
        self.substringLangCombo.setItemText(2, QCoreApplication.translate("MainWindow", u"German", None))
        self.substringLangCombo.setItemText(3, QCoreApplication.translate("MainWindow", u"Italian", None))
        self.substringLangCombo.setItemText(4, QCoreApplication.translate("MainWindow", u"Spanish", None))
        self.substringLangCombo.setItemText(5, QCoreApplication.translate("MainWindow", u"Polish", None))

        self.substringGenderCombo.setItemText(0, QCoreApplication.translate("MainWindow", u"Male", None))
        self.substringGenderCombo.setItemText(1, QCoreApplication.translate("MainWindow", u"Female", None))

        self.addSubstringButton.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.removeSubstringButton.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
