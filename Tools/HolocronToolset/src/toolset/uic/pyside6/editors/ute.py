# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ute.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from toolset.gui.common.widgets.combobox import FilterComboBox
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(507, 313)
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
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout_2 = QGridLayout(self.tab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
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

        self.label_39 = QLabel(self.tab)
        self.label_39.setObjectName(u"label_39")

        self.formLayout_10.setWidget(3, QFormLayout.LabelRole, self.label_39)

        self.difficultySelect = ComboBox2DA(self.tab)
        self.difficultySelect.setObjectName(u"difficultySelect")

        self.formLayout_10.setWidget(3, QFormLayout.FieldRole, self.difficultySelect)

        self.label_40 = QLabel(self.tab)
        self.label_40.setObjectName(u"label_40")

        self.formLayout_10.setWidget(4, QFormLayout.LabelRole, self.label_40)

        self.minCreatureSpin = QSpinBox(self.tab)
        self.minCreatureSpin.setObjectName(u"minCreatureSpin")
        self.minCreatureSpin.setMinimum(-2147483648)
        self.minCreatureSpin.setMaximum(2147483647)

        self.formLayout_10.setWidget(4, QFormLayout.FieldRole, self.minCreatureSpin)

        self.label_41 = QLabel(self.tab)
        self.label_41.setObjectName(u"label_41")

        self.formLayout_10.setWidget(5, QFormLayout.LabelRole, self.label_41)

        self.maxCreatureSpin = QSpinBox(self.tab)
        self.maxCreatureSpin.setObjectName(u"maxCreatureSpin")
        self.maxCreatureSpin.setMinimum(-2147483648)
        self.maxCreatureSpin.setMaximum(2147483647)

        self.formLayout_10.setWidget(5, QFormLayout.FieldRole, self.maxCreatureSpin)

        self.label_42 = QLabel(self.tab)
        self.label_42.setObjectName(u"label_42")

        self.formLayout_10.setWidget(6, QFormLayout.LabelRole, self.label_42)

        self.spawnSelect = QComboBox(self.tab)
        self.spawnSelect.addItem("")
        self.spawnSelect.addItem("")
        self.spawnSelect.setObjectName(u"spawnSelect")

        self.formLayout_10.setWidget(6, QFormLayout.FieldRole, self.spawnSelect)


        self.gridLayout_2.addLayout(self.formLayout_10, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.activeCheckbox = QCheckBox(self.tab_2)
        self.activeCheckbox.setObjectName(u"activeCheckbox")

        self.verticalLayout.addWidget(self.activeCheckbox)

        self.playerOnlyCheckbox = QCheckBox(self.tab_2)
        self.playerOnlyCheckbox.setObjectName(u"playerOnlyCheckbox")

        self.verticalLayout.addWidget(self.playerOnlyCheckbox)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.tab_2)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.factionSelect = ComboBox2DA(self.tab_2)
        self.factionSelect.setObjectName(u"factionSelect")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.factionSelect)


        self.verticalLayout.addLayout(self.formLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.line = QFrame(self.tab_2)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.respawnsCheckbox = QCheckBox(self.tab_2)
        self.respawnsCheckbox.setObjectName(u"respawnsCheckbox")

        self.verticalLayout_2.addWidget(self.respawnsCheckbox)

        self.infiniteRespawnCheckbox = QCheckBox(self.tab_2)
        self.infiniteRespawnCheckbox.setObjectName(u"infiniteRespawnCheckbox")

        self.verticalLayout_2.addWidget(self.infiniteRespawnCheckbox)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_2 = QLabel(self.tab_2)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.respawnTimeSpin = QSpinBox(self.tab_2)
        self.respawnTimeSpin.setObjectName(u"respawnTimeSpin")
        self.respawnTimeSpin.setMinimum(-2147483648)
        self.respawnTimeSpin.setMaximum(2147483647)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.respawnTimeSpin)

        self.label_3 = QLabel(self.tab_2)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.respawnCountSpin = QSpinBox(self.tab_2)
        self.respawnCountSpin.setObjectName(u"respawnCountSpin")
        self.respawnCountSpin.setMinimum(0)
        self.respawnCountSpin.setMaximum(99999)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.respawnCountSpin)


        self.verticalLayout_2.addLayout(self.formLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.verticalLayout_3 = QVBoxLayout(self.tab_5)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.creatureTable = QTableWidget(self.tab_5)
        if (self.creatureTable.columnCount() < 4):
            self.creatureTable.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.creatureTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.creatureTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.creatureTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.creatureTable.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.creatureTable.setObjectName(u"creatureTable")
        self.creatureTable.setAlternatingRowColors(True)
        self.creatureTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.creatureTable.horizontalHeader().setStretchLastSection(True)

        self.verticalLayout_3.addWidget(self.creatureTable)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.removeCreatureButton = QPushButton(self.tab_5)
        self.removeCreatureButton.setObjectName(u"removeCreatureButton")

        self.horizontalLayout.addWidget(self.removeCreatureButton)

        self.addCreatureButton = QPushButton(self.tab_5)
        self.addCreatureButton.setObjectName(u"addCreatureButton")

        self.horizontalLayout.addWidget(self.addCreatureButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.tabWidget.addTab(self.tab_5, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.gridLayout_4 = QGridLayout(self.tab_3)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_4 = QLabel(self.tab_3)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.onEnterEdit = FilterComboBox(self.tab_3)
        self.onEnterEdit.setObjectName(u"onEnterEdit")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.onEnterEdit)

        self.label_5 = QLabel(self.tab_3)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_5)

        self.label_7 = QLabel(self.tab_3)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_7)

        self.label_8 = QLabel(self.tab_3)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label_8)

        self.label_9 = QLabel(self.tab_3)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_3.setWidget(4, QFormLayout.LabelRole, self.label_9)

        self.onExitEdit = FilterComboBox(self.tab_3)
        self.onExitEdit.setObjectName(u"onExitEdit")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.onExitEdit)

        self.onExhaustedEdit = FilterComboBox(self.tab_3)
        self.onExhaustedEdit.setObjectName(u"onExhaustedEdit")

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.onExhaustedEdit)

        self.onHeartbeatEdit = FilterComboBox(self.tab_3)
        self.onHeartbeatEdit.setObjectName(u"onHeartbeatEdit")

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.onHeartbeatEdit)

        self.onUserDefinedEdit = FilterComboBox(self.tab_3)
        self.onUserDefinedEdit.setObjectName(u"onUserDefinedEdit")

        self.formLayout_3.setWidget(4, QFormLayout.FieldRole, self.onUserDefinedEdit)


        self.gridLayout_4.addLayout(self.formLayout_3, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.gridLayout_3 = QGridLayout(self.tab_4)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.commentsEdit = QPlainTextEdit(self.tab_4)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.gridLayout_3.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_4, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 507, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
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
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", u"Difficulty:", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", u"Min Creatures:", None))
        self.label_41.setText(QCoreApplication.translate("MainWindow", u"Max Creatures:", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", u"Spawn Option:", None))
        self.spawnSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Single Shot", None))
        self.spawnSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Continuous", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Basic", None))
        self.activeCheckbox.setText(QCoreApplication.translate("MainWindow", u"Active", None))
        self.playerOnlyCheckbox.setText(QCoreApplication.translate("MainWindow", u"Player Triggered Only", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Faction:", None))
        self.respawnsCheckbox.setText(QCoreApplication.translate("MainWindow", u"Respawns", None))
        self.infiniteRespawnCheckbox.setText(QCoreApplication.translate("MainWindow", u"Infinite Respawns", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Respawn Time (s):", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Number of Respawns:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Advanced", None))
        ___qtablewidgetitem = self.creatureTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"SingleSpawn", None));
        ___qtablewidgetitem1 = self.creatureTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"CR", None));
        ___qtablewidgetitem2 = self.creatureTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Appearance", None));
        ___qtablewidgetitem3 = self.creatureTable.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"ResRef", None));
        self.removeCreatureButton.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.addCreatureButton.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", u"Creatures", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"OnEnter:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"OnExit:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"OnExhausted:", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"OnHeartbeat:", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"OnUserDefined:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
