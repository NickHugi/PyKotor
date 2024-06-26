# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'jrl.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.plaintext import HTPlainTextEdit


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(948, 701)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.journalTree = QTreeView(self.splitter)
        self.journalTree.setObjectName(u"journalTree")
        self.journalTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.journalTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.journalTree.setHeaderHidden(True)
        self.splitter.addWidget(self.journalTree)
        self.questPages = QStackedWidget(self.splitter)
        self.questPages.setObjectName(u"questPages")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.questPages.sizePolicy().hasHeightForWidth())
        self.questPages.setSizePolicy(sizePolicy)
        self.categoryPage = QWidget()
        self.categoryPage.setObjectName(u"categoryPage")
        self.horizontalLayout_2 = QHBoxLayout(self.categoryPage)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.categoryPage)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.categoryNameEdit = LocalizedStringLineEdit(self.categoryPage)
        self.categoryNameEdit.setObjectName(u"categoryNameEdit")
        self.categoryNameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout.addWidget(self.categoryNameEdit)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_2 = QLabel(self.categoryPage)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_2)

        self.label_5 = QLabel(self.categoryPage)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_5)

        self.categoryTag = QLineEdit(self.categoryPage)
        self.categoryTag.setObjectName(u"categoryTag")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.categoryTag)

        self.label_3 = QLabel(self.categoryPage)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.categoryPlanetSelect = ComboBox2DA(self.categoryPage)
        self.categoryPlanetSelect.setObjectName(u"categoryPlanetSelect")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.categoryPlanetSelect)

        self.categoryPlotSelect = ComboBox2DA(self.categoryPage)
        self.categoryPlotSelect.setObjectName(u"categoryPlotSelect")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.categoryPlotSelect)

        self.label_4 = QLabel(self.categoryPage)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.categoryPrioritySelect = QComboBox(self.categoryPage)
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.addItem("")
        self.categoryPrioritySelect.setObjectName(u"categoryPrioritySelect")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.categoryPrioritySelect)


        self.horizontalLayout_2.addLayout(self.formLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_6 = QLabel(self.categoryPage)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout_2.addWidget(self.label_6)

        self.categoryCommentEdit = HTPlainTextEdit(self.categoryPage)
        self.categoryCommentEdit.setObjectName(u"categoryCommentEdit")

        self.verticalLayout_2.addWidget(self.categoryCommentEdit)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 2)
        self.questPages.addWidget(self.categoryPage)
        self.entryPage = QWidget()
        self.entryPage.setObjectName(u"entryPage")
        self.horizontalLayout_3 = QHBoxLayout(self.entryPage)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_8 = QLabel(self.entryPage)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.entryIdSpin = QSpinBox(self.entryPage)
        self.entryIdSpin.setObjectName(u"entryIdSpin")
        self.entryIdSpin.setMinimumSize(QSize(80, 0))

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.entryIdSpin)

        self.label_7 = QLabel(self.entryPage)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_7)

        self.label_9 = QLabel(self.entryPage)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_9)

        self.entryXpSpin = QDoubleSpinBox(self.entryPage)
        self.entryXpSpin.setObjectName(u"entryXpSpin")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.entryXpSpin)

        self.entryEndCheck = QCheckBox(self.entryPage)
        self.entryEndCheck.setObjectName(u"entryEndCheck")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.entryEndCheck)


        self.horizontalLayout_3.addLayout(self.formLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_10 = QLabel(self.entryPage)
        self.label_10.setObjectName(u"label_10")

        self.verticalLayout.addWidget(self.label_10)

        self.entryTextEdit = HTPlainTextEdit(self.entryPage)
        self.entryTextEdit.setObjectName(u"entryTextEdit")
        self.entryTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.entryTextEdit)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.questPages.addWidget(self.entryPage)
        self.splitter.addWidget(self.questPages)

        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 948, 22))
        self.menuNew = QMenu(self.menubar)
        self.menuNew.setObjectName(u"menuNew")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuNew.menuAction())
        self.menuNew.addAction(self.actionNew)
        self.menuNew.addAction(self.actionOpen)
        self.menuNew.addAction(self.actionSave)
        self.menuNew.addAction(self.actionSave_As)
        self.menuNew.addAction(self.actionRevert)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        self.questPages.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Planet ID:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Plot Index:", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Priority:", None))
        self.categoryPrioritySelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Highest", None))
        self.categoryPrioritySelect.setItemText(1, QCoreApplication.translate("MainWindow", u"High", None))
        self.categoryPrioritySelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Medium", None))
        self.categoryPrioritySelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Low", None))
        self.categoryPrioritySelect.setItemText(4, QCoreApplication.translate("MainWindow", u"Lowest", None))

        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Comment:", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"ID:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"End:", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"XP Percentage:", None))
        self.entryEndCheck.setText("")
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Text:", None))
        self.menuNew.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
