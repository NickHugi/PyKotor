# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'utt.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTabWidget, QVBoxLayout,
    QWidget)

from toolset.gui.common.widgets.combobox import FilterComboBox
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(364, 296)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName(u"actionSaveAs")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout_10 = QFormLayout()
        self.formLayout_10.setObjectName(u"formLayout_10")
        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_10.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.nameEdit = LocalizedStringLineEdit(self.tab)
        self.nameEdit.setObjectName(u"nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_15.addWidget(self.nameEdit)


        self.formLayout_10.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_15)

        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName(u"label_14")

        self.formLayout_10.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.tagEdit = QLineEdit(self.tab)
        self.tagEdit.setObjectName(u"tagEdit")

        self.horizontalLayout_16.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.tab)
        self.tagGenerateButton.setObjectName(u"tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_16.addWidget(self.tagGenerateButton)


        self.formLayout_10.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_16)

        self.label_38 = QLabel(self.tab)
        self.label_38.setObjectName(u"label_38")

        self.formLayout_10.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.resrefEdit = QLineEdit(self.tab)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_17.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.tab)
        self.resrefGenerateButton.setObjectName(u"resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_17.addWidget(self.resrefGenerateButton)


        self.formLayout_10.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_17)

        self.label_2 = QLabel(self.tab)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_10.setWidget(3, QFormLayout.LabelRole, self.label_2)

        self.typeSelect = QComboBox(self.tab)
        self.typeSelect.addItem("")
        self.typeSelect.addItem("")
        self.typeSelect.addItem("")
        self.typeSelect.setObjectName(u"typeSelect")

        self.formLayout_10.setWidget(3, QFormLayout.FieldRole, self.typeSelect)

        self.label_3 = QLabel(self.tab)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_10.setWidget(4, QFormLayout.LabelRole, self.label_3)

        self.cursorSelect = ComboBox2DA(self.tab)
        self.cursorSelect.setObjectName(u"cursorSelect")

        self.formLayout_10.setWidget(4, QFormLayout.FieldRole, self.cursorSelect)


        self.verticalLayout.addLayout(self.formLayout_10)

        self.tabWidget.addTab(self.tab, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.verticalLayout_4 = QVBoxLayout(self.tab_5)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.autoRemoveKeyCheckbox = QCheckBox(self.tab_5)
        self.autoRemoveKeyCheckbox.setObjectName(u"autoRemoveKeyCheckbox")

        self.verticalLayout_4.addWidget(self.autoRemoveKeyCheckbox)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_8 = QLabel(self.tab_5)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.keyEdit = QLineEdit(self.tab_5)
        self.keyEdit.setObjectName(u"keyEdit")

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.keyEdit)


        self.verticalLayout_4.addLayout(self.formLayout_4)

        self.line = QFrame(self.tab_5)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label = QLabel(self.tab_5)
        self.label.setObjectName(u"label")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label)

        self.factionSelect = ComboBox2DA(self.tab_5)
        self.factionSelect.setObjectName(u"factionSelect")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.factionSelect)

        self.highlightHeightSpin = QDoubleSpinBox(self.tab_5)
        self.highlightHeightSpin.setObjectName(u"highlightHeightSpin")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.highlightHeightSpin)

        self.label_7 = QLabel(self.tab_5)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_7)


        self.verticalLayout_4.addLayout(self.formLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.tabWidget.addTab(self.tab_5, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_3 = QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.isTrapCheckbox = QCheckBox(self.tab_2)
        self.isTrapCheckbox.setObjectName(u"isTrapCheckbox")

        self.verticalLayout_2.addWidget(self.isTrapCheckbox)

        self.activateOnceCheckbox = QCheckBox(self.tab_2)
        self.activateOnceCheckbox.setObjectName(u"activateOnceCheckbox")

        self.verticalLayout_2.addWidget(self.activateOnceCheckbox)

        self.formLayout_6 = QFormLayout()
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.label_17 = QLabel(self.tab_2)
        self.label_17.setObjectName(u"label_17")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_17)

        self.trapSelect = ComboBox2DA(self.tab_2)
        self.trapSelect.setObjectName(u"trapSelect")

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.trapSelect)


        self.verticalLayout_2.addLayout(self.formLayout_6)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)

        self.detectableCheckbox = QCheckBox(self.tab_2)
        self.detectableCheckbox.setObjectName(u"detectableCheckbox")

        self.verticalLayout_3.addWidget(self.detectableCheckbox)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_4 = QLabel(self.tab_2)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.detectDcSpin = QSpinBox(self.tab_2)
        self.detectDcSpin.setObjectName(u"detectDcSpin")
        self.detectDcSpin.setMinimum(-2147483648)
        self.detectDcSpin.setMaximum(2147483647)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.detectDcSpin)


        self.verticalLayout_3.addLayout(self.formLayout)

        self.disarmableCheckbox = QCheckBox(self.tab_2)
        self.disarmableCheckbox.setObjectName(u"disarmableCheckbox")

        self.verticalLayout_3.addWidget(self.disarmableCheckbox)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_5 = QLabel(self.tab_2)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_5)

        self.disarmDcSpin = QSpinBox(self.tab_2)
        self.disarmDcSpin.setObjectName(u"disarmDcSpin")
        self.disarmDcSpin.setMinimum(-2147483648)
        self.disarmDcSpin.setMaximum(2147483647)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.disarmDcSpin)


        self.verticalLayout_3.addLayout(self.formLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayout_5 = QVBoxLayout(self.tab_4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.label_9 = QLabel(self.tab_4)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_5.setWidget(4, QFormLayout.LabelRole, self.label_9)

        self.onHeartbeatEdit = FilterComboBox(self.tab_4)
        self.onHeartbeatEdit.setObjectName(u"onHeartbeatEdit")

        self.formLayout_5.setWidget(4, QFormLayout.FieldRole, self.onHeartbeatEdit)

        self.label_10 = QLabel(self.tab_4)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_5.setWidget(3, QFormLayout.LabelRole, self.label_10)

        self.label_11 = QLabel(self.tab_4)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_11)

        self.label_12 = QLabel(self.tab_4)
        self.label_12.setObjectName(u"label_12")

        self.formLayout_5.setWidget(6, QFormLayout.LabelRole, self.label_12)

        self.onExitEdit = FilterComboBox(self.tab_4)
        self.onExitEdit.setObjectName(u"onExitEdit")

        self.formLayout_5.setWidget(3, QFormLayout.FieldRole, self.onExitEdit)

        self.onEnterEdit = FilterComboBox(self.tab_4)
        self.onEnterEdit.setObjectName(u"onEnterEdit")

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.onEnterEdit)

        self.onUserDefinedEdit = FilterComboBox(self.tab_4)
        self.onUserDefinedEdit.setObjectName(u"onUserDefinedEdit")

        self.formLayout_5.setWidget(6, QFormLayout.FieldRole, self.onUserDefinedEdit)

        self.label_13 = QLabel(self.tab_4)
        self.label_13.setObjectName(u"label_13")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_13)

        self.label_15 = QLabel(self.tab_4)
        self.label_15.setObjectName(u"label_15")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_15)

        self.label_16 = QLabel(self.tab_4)
        self.label_16.setObjectName(u"label_16")

        self.formLayout_5.setWidget(5, QFormLayout.LabelRole, self.label_16)

        self.onTrapTriggeredEdit = FilterComboBox(self.tab_4)
        self.onTrapTriggeredEdit.setObjectName(u"onTrapTriggeredEdit")

        self.formLayout_5.setWidget(5, QFormLayout.FieldRole, self.onTrapTriggeredEdit)

        self.onDisarmEdit = FilterComboBox(self.tab_4)
        self.onDisarmEdit.setObjectName(u"onDisarmEdit")

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.onDisarmEdit)

        self.onClickEdit = FilterComboBox(self.tab_4)
        self.onClickEdit.setObjectName(u"onClickEdit")

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.onClickEdit)


        self.verticalLayout_5.addLayout(self.formLayout_5)

        self.verticalSpacer_3 = QSpacerItem(20, 26, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.tab_4, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName(u"commentsTab")
        self.gridLayout_2 = QGridLayout(self.commentsTab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.commentsEdit = QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.gridLayout_2.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 364, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Type:", None))
        self.typeSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Generic", None))
        self.typeSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Transition", None))
        self.typeSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Trap", None))

        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Cursor:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Basic", None))
        self.autoRemoveKeyCheckbox.setText(QCoreApplication.translate("MainWindow", u"Auto Remove Key", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Key Name:", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Faction:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Hightlight Height:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.isTrapCheckbox.setText(QCoreApplication.translate("MainWindow", u"Is a trap", None))
        self.activateOnceCheckbox.setText(QCoreApplication.translate("MainWindow", u"Activate Once", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Trap Type:", None))
        self.detectableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Detectable", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Detect DC:", None))
        self.disarmableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Disarmable", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Disarm DC:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Trap", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"OnHeartbeat:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"OnExit:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"OnEnter:", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"OnUserDefined:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"OnClick:", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"OnDisarm:", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"OnTrapTriggered:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", u"Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
