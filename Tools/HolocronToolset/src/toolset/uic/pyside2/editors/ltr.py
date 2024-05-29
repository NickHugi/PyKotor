# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ltr.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
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
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabSingles = QWidget()
        self.tabSingles.setObjectName(u"tabSingles")
        self.verticalLayoutSingles = QVBoxLayout(self.tabSingles)
        self.verticalLayoutSingles.setObjectName(u"verticalLayoutSingles")
        self.horizontalLayoutSingleSelection = QHBoxLayout()
        self.horizontalLayoutSingleSelection.setObjectName(u"horizontalLayoutSingleSelection")
        self.labelSingleChar = QLabel(self.tabSingles)
        self.labelSingleChar.setObjectName(u"labelSingleChar")

        self.horizontalLayoutSingleSelection.addWidget(self.labelSingleChar)

        self.comboBoxSingleChar = QComboBox(self.tabSingles)
        self.comboBoxSingleChar.setObjectName(u"comboBoxSingleChar")

        self.horizontalLayoutSingleSelection.addWidget(self.comboBoxSingleChar)

        self.labelSingleStart = QLabel(self.tabSingles)
        self.labelSingleStart.setObjectName(u"labelSingleStart")

        self.horizontalLayoutSingleSelection.addWidget(self.labelSingleStart)

        self.spinBoxSingleStart = QDoubleSpinBox(self.tabSingles)
        self.spinBoxSingleStart.setObjectName(u"spinBoxSingleStart")
        self.spinBoxSingleStart.setMinimum(0.000000000000000)
        self.spinBoxSingleStart.setMaximum(1.000000000000000)
        self.spinBoxSingleStart.setSingleStep(0.010000000000000)

        self.horizontalLayoutSingleSelection.addWidget(self.spinBoxSingleStart)

        self.labelSingleMiddle = QLabel(self.tabSingles)
        self.labelSingleMiddle.setObjectName(u"labelSingleMiddle")

        self.horizontalLayoutSingleSelection.addWidget(self.labelSingleMiddle)

        self.spinBoxSingleMiddle = QDoubleSpinBox(self.tabSingles)
        self.spinBoxSingleMiddle.setObjectName(u"spinBoxSingleMiddle")
        self.spinBoxSingleMiddle.setMinimum(0.000000000000000)
        self.spinBoxSingleMiddle.setMaximum(1.000000000000000)
        self.spinBoxSingleMiddle.setSingleStep(0.010000000000000)

        self.horizontalLayoutSingleSelection.addWidget(self.spinBoxSingleMiddle)

        self.labelSingleEnd = QLabel(self.tabSingles)
        self.labelSingleEnd.setObjectName(u"labelSingleEnd")

        self.horizontalLayoutSingleSelection.addWidget(self.labelSingleEnd)

        self.spinBoxSingleEnd = QDoubleSpinBox(self.tabSingles)
        self.spinBoxSingleEnd.setObjectName(u"spinBoxSingleEnd")
        self.spinBoxSingleEnd.setMinimum(0.000000000000000)
        self.spinBoxSingleEnd.setMaximum(1.000000000000000)
        self.spinBoxSingleEnd.setSingleStep(0.010000000000000)

        self.horizontalLayoutSingleSelection.addWidget(self.spinBoxSingleEnd)


        self.verticalLayoutSingles.addLayout(self.horizontalLayoutSingleSelection)

        self.buttonSetSingle = QPushButton(self.tabSingles)
        self.buttonSetSingle.setObjectName(u"buttonSetSingle")

        self.verticalLayoutSingles.addWidget(self.buttonSetSingle)

        self.tableSingles = QTableWidget(self.tabSingles)
        if (self.tableSingles.columnCount() < 4):
            self.tableSingles.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableSingles.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableSingles.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableSingles.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableSingles.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.tableSingles.setObjectName(u"tableSingles")

        self.verticalLayoutSingles.addWidget(self.tableSingles)

        self.buttonAddSingle = QPushButton(self.tabSingles)
        self.buttonAddSingle.setObjectName(u"buttonAddSingle")

        self.verticalLayoutSingles.addWidget(self.buttonAddSingle)

        self.buttonRemoveSingle = QPushButton(self.tabSingles)
        self.buttonRemoveSingle.setObjectName(u"buttonRemoveSingle")

        self.verticalLayoutSingles.addWidget(self.buttonRemoveSingle)

        self.tabWidget.addTab(self.tabSingles, "")
        self.tabDoubles = QWidget()
        self.tabDoubles.setObjectName(u"tabDoubles")
        self.verticalLayoutDoubles = QVBoxLayout(self.tabDoubles)
        self.verticalLayoutDoubles.setObjectName(u"verticalLayoutDoubles")
        self.horizontalLayoutDoubleSelection = QHBoxLayout()
        self.horizontalLayoutDoubleSelection.setObjectName(u"horizontalLayoutDoubleSelection")
        self.labelDoublePrevChar = QLabel(self.tabDoubles)
        self.labelDoublePrevChar.setObjectName(u"labelDoublePrevChar")

        self.horizontalLayoutDoubleSelection.addWidget(self.labelDoublePrevChar)

        self.comboBoxDoublePrevChar = QComboBox(self.tabDoubles)
        self.comboBoxDoublePrevChar.setObjectName(u"comboBoxDoublePrevChar")

        self.horizontalLayoutDoubleSelection.addWidget(self.comboBoxDoublePrevChar)

        self.labelDoubleChar = QLabel(self.tabDoubles)
        self.labelDoubleChar.setObjectName(u"labelDoubleChar")

        self.horizontalLayoutDoubleSelection.addWidget(self.labelDoubleChar)

        self.comboBoxDoubleChar = QComboBox(self.tabDoubles)
        self.comboBoxDoubleChar.setObjectName(u"comboBoxDoubleChar")

        self.horizontalLayoutDoubleSelection.addWidget(self.comboBoxDoubleChar)

        self.labelDoubleStart = QLabel(self.tabDoubles)
        self.labelDoubleStart.setObjectName(u"labelDoubleStart")

        self.horizontalLayoutDoubleSelection.addWidget(self.labelDoubleStart)

        self.spinBoxDoubleStart = QDoubleSpinBox(self.tabDoubles)
        self.spinBoxDoubleStart.setObjectName(u"spinBoxDoubleStart")
        self.spinBoxDoubleStart.setMinimum(0.000000000000000)
        self.spinBoxDoubleStart.setMaximum(1.000000000000000)
        self.spinBoxDoubleStart.setSingleStep(0.010000000000000)

        self.horizontalLayoutDoubleSelection.addWidget(self.spinBoxDoubleStart)

        self.labelDoubleMiddle = QLabel(self.tabDoubles)
        self.labelDoubleMiddle.setObjectName(u"labelDoubleMiddle")

        self.horizontalLayoutDoubleSelection.addWidget(self.labelDoubleMiddle)

        self.spinBoxDoubleMiddle = QDoubleSpinBox(self.tabDoubles)
        self.spinBoxDoubleMiddle.setObjectName(u"spinBoxDoubleMiddle")
        self.spinBoxDoubleMiddle.setMinimum(0.000000000000000)
        self.spinBoxDoubleMiddle.setMaximum(1.000000000000000)
        self.spinBoxDoubleMiddle.setSingleStep(0.010000000000000)

        self.horizontalLayoutDoubleSelection.addWidget(self.spinBoxDoubleMiddle)

        self.labelDoubleEnd = QLabel(self.tabDoubles)
        self.labelDoubleEnd.setObjectName(u"labelDoubleEnd")

        self.horizontalLayoutDoubleSelection.addWidget(self.labelDoubleEnd)

        self.spinBoxDoubleEnd = QDoubleSpinBox(self.tabDoubles)
        self.spinBoxDoubleEnd.setObjectName(u"spinBoxDoubleEnd")
        self.spinBoxDoubleEnd.setMinimum(0.000000000000000)
        self.spinBoxDoubleEnd.setMaximum(1.000000000000000)
        self.spinBoxDoubleEnd.setSingleStep(0.010000000000000)

        self.horizontalLayoutDoubleSelection.addWidget(self.spinBoxDoubleEnd)


        self.verticalLayoutDoubles.addLayout(self.horizontalLayoutDoubleSelection)

        self.buttonSetDouble = QPushButton(self.tabDoubles)
        self.buttonSetDouble.setObjectName(u"buttonSetDouble")

        self.verticalLayoutDoubles.addWidget(self.buttonSetDouble)

        self.tableDoubles = QTableWidget(self.tabDoubles)
        if (self.tableDoubles.columnCount() < 5):
            self.tableDoubles.setColumnCount(5)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableDoubles.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableDoubles.setHorizontalHeaderItem(1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableDoubles.setHorizontalHeaderItem(2, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableDoubles.setHorizontalHeaderItem(3, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableDoubles.setHorizontalHeaderItem(4, __qtablewidgetitem8)
        self.tableDoubles.setObjectName(u"tableDoubles")

        self.verticalLayoutDoubles.addWidget(self.tableDoubles)

        self.buttonAddDouble = QPushButton(self.tabDoubles)
        self.buttonAddDouble.setObjectName(u"buttonAddDouble")

        self.verticalLayoutDoubles.addWidget(self.buttonAddDouble)

        self.buttonRemoveDouble = QPushButton(self.tabDoubles)
        self.buttonRemoveDouble.setObjectName(u"buttonRemoveDouble")

        self.verticalLayoutDoubles.addWidget(self.buttonRemoveDouble)

        self.tabWidget.addTab(self.tabDoubles, "")
        self.tabTriples = QWidget()
        self.tabTriples.setObjectName(u"tabTriples")
        self.verticalLayoutTriples = QVBoxLayout(self.tabTriples)
        self.verticalLayoutTriples.setObjectName(u"verticalLayoutTriples")
        self.horizontalLayoutTripleSelection = QHBoxLayout()
        self.horizontalLayoutTripleSelection.setObjectName(u"horizontalLayoutTripleSelection")
        self.labelTriplePrev2Char = QLabel(self.tabTriples)
        self.labelTriplePrev2Char.setObjectName(u"labelTriplePrev2Char")

        self.horizontalLayoutTripleSelection.addWidget(self.labelTriplePrev2Char)

        self.comboBoxTriplePrev2Char = QComboBox(self.tabTriples)
        self.comboBoxTriplePrev2Char.setObjectName(u"comboBoxTriplePrev2Char")

        self.horizontalLayoutTripleSelection.addWidget(self.comboBoxTriplePrev2Char)

        self.labelTriplePrev1Char = QLabel(self.tabTriples)
        self.labelTriplePrev1Char.setObjectName(u"labelTriplePrev1Char")

        self.horizontalLayoutTripleSelection.addWidget(self.labelTriplePrev1Char)

        self.comboBoxTriplePrev1Char = QComboBox(self.tabTriples)
        self.comboBoxTriplePrev1Char.setObjectName(u"comboBoxTriplePrev1Char")

        self.horizontalLayoutTripleSelection.addWidget(self.comboBoxTriplePrev1Char)

        self.labelTripleChar = QLabel(self.tabTriples)
        self.labelTripleChar.setObjectName(u"labelTripleChar")

        self.horizontalLayoutTripleSelection.addWidget(self.labelTripleChar)

        self.comboBoxTripleChar = QComboBox(self.tabTriples)
        self.comboBoxTripleChar.setObjectName(u"comboBoxTripleChar")

        self.horizontalLayoutTripleSelection.addWidget(self.comboBoxTripleChar)

        self.labelTripleStart = QLabel(self.tabTriples)
        self.labelTripleStart.setObjectName(u"labelTripleStart")

        self.horizontalLayoutTripleSelection.addWidget(self.labelTripleStart)

        self.spinBoxTripleStart = QDoubleSpinBox(self.tabTriples)
        self.spinBoxTripleStart.setObjectName(u"spinBoxTripleStart")
        self.spinBoxTripleStart.setMinimum(0.000000000000000)
        self.spinBoxTripleStart.setMaximum(1.000000000000000)
        self.spinBoxTripleStart.setSingleStep(0.010000000000000)

        self.horizontalLayoutTripleSelection.addWidget(self.spinBoxTripleStart)

        self.labelTripleMiddle = QLabel(self.tabTriples)
        self.labelTripleMiddle.setObjectName(u"labelTripleMiddle")

        self.horizontalLayoutTripleSelection.addWidget(self.labelTripleMiddle)

        self.spinBoxTripleMiddle = QDoubleSpinBox(self.tabTriples)
        self.spinBoxTripleMiddle.setObjectName(u"spinBoxTripleMiddle")
        self.spinBoxTripleMiddle.setMinimum(0.000000000000000)
        self.spinBoxTripleMiddle.setMaximum(1.000000000000000)
        self.spinBoxTripleMiddle.setSingleStep(0.010000000000000)

        self.horizontalLayoutTripleSelection.addWidget(self.spinBoxTripleMiddle)

        self.labelTripleEnd = QLabel(self.tabTriples)
        self.labelTripleEnd.setObjectName(u"labelTripleEnd")

        self.horizontalLayoutTripleSelection.addWidget(self.labelTripleEnd)

        self.spinBoxTripleEnd = QDoubleSpinBox(self.tabTriples)
        self.spinBoxTripleEnd.setObjectName(u"spinBoxTripleEnd")
        self.spinBoxTripleEnd.setMinimum(0.000000000000000)
        self.spinBoxTripleEnd.setMaximum(1.000000000000000)
        self.spinBoxTripleEnd.setSingleStep(0.010000000000000)

        self.horizontalLayoutTripleSelection.addWidget(self.spinBoxTripleEnd)


        self.verticalLayoutTriples.addLayout(self.horizontalLayoutTripleSelection)

        self.buttonSetTriple = QPushButton(self.tabTriples)
        self.buttonSetTriple.setObjectName(u"buttonSetTriple")

        self.verticalLayoutTriples.addWidget(self.buttonSetTriple)

        self.tableTriples = QTableWidget(self.tabTriples)
        if (self.tableTriples.columnCount() < 6):
            self.tableTriples.setColumnCount(6)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableTriples.setHorizontalHeaderItem(0, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableTriples.setHorizontalHeaderItem(1, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableTriples.setHorizontalHeaderItem(2, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableTriples.setHorizontalHeaderItem(3, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tableTriples.setHorizontalHeaderItem(4, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.tableTriples.setHorizontalHeaderItem(5, __qtablewidgetitem14)
        self.tableTriples.setObjectName(u"tableTriples")

        self.verticalLayoutTriples.addWidget(self.tableTriples)

        self.buttonAddTriple = QPushButton(self.tabTriples)
        self.buttonAddTriple.setObjectName(u"buttonAddTriple")

        self.verticalLayoutTriples.addWidget(self.buttonAddTriple)

        self.buttonRemoveTriple = QPushButton(self.tabTriples)
        self.buttonRemoveTriple.setObjectName(u"buttonRemoveTriple")

        self.verticalLayoutTriples.addWidget(self.buttonRemoveTriple)

        self.tabWidget.addTab(self.tabTriples, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonGenerate = QPushButton(self.centralwidget)
        self.buttonGenerate.setObjectName(u"buttonGenerate")

        self.verticalLayout.addWidget(self.buttonGenerate)

        self.lineEditGeneratedName = QLineEdit(self.centralwidget)
        self.lineEditGeneratedName.setObjectName(u"lineEditGeneratedName")

        self.verticalLayout.addWidget(self.lineEditGeneratedName)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuFormat = QMenu(self.menubar)
        self.menuFormat.setObjectName(u"menuFormat")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuFormat.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"LTR Editor", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.labelSingleChar.setText(QCoreApplication.translate("MainWindow", u"Character", None))
        self.labelSingleStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.labelSingleMiddle.setText(QCoreApplication.translate("MainWindow", u"Middle", None))
        self.labelSingleEnd.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.buttonSetSingle.setText(QCoreApplication.translate("MainWindow", u"Set Single Character", None))
        ___qtablewidgetitem = self.tableSingles.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Character", None));
        ___qtablewidgetitem1 = self.tableSingles.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Start", None));
        ___qtablewidgetitem2 = self.tableSingles.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Middle", None));
        ___qtablewidgetitem3 = self.tableSingles.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"End", None));
        self.buttonAddSingle.setText(QCoreApplication.translate("MainWindow", u"Add Row", None))
        self.buttonRemoveSingle.setText(QCoreApplication.translate("MainWindow", u"Remove Selected Row", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSingles), QCoreApplication.translate("MainWindow", u"Singles", None))
        self.labelDoublePrevChar.setText(QCoreApplication.translate("MainWindow", u"Previous Character", None))
        self.labelDoubleChar.setText(QCoreApplication.translate("MainWindow", u"Character", None))
        self.labelDoubleStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.labelDoubleMiddle.setText(QCoreApplication.translate("MainWindow", u"Middle", None))
        self.labelDoubleEnd.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.buttonSetDouble.setText(QCoreApplication.translate("MainWindow", u"Set Double Character", None))
        ___qtablewidgetitem4 = self.tableDoubles.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Previous Character", None));
        ___qtablewidgetitem5 = self.tableDoubles.horizontalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"Character", None));
        ___qtablewidgetitem6 = self.tableDoubles.horizontalHeaderItem(2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"Start", None));
        ___qtablewidgetitem7 = self.tableDoubles.horizontalHeaderItem(3)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"Middle", None));
        ___qtablewidgetitem8 = self.tableDoubles.horizontalHeaderItem(4)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("MainWindow", u"End", None));
        self.buttonAddDouble.setText(QCoreApplication.translate("MainWindow", u"Add Row", None))
        self.buttonRemoveDouble.setText(QCoreApplication.translate("MainWindow", u"Remove Selected Row", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabDoubles), QCoreApplication.translate("MainWindow", u"Doubles", None))
        self.labelTriplePrev2Char.setText(QCoreApplication.translate("MainWindow", u"Previous Character 2", None))
        self.labelTriplePrev1Char.setText(QCoreApplication.translate("MainWindow", u"Previous Character 1", None))
        self.labelTripleChar.setText(QCoreApplication.translate("MainWindow", u"Character", None))
        self.labelTripleStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.labelTripleMiddle.setText(QCoreApplication.translate("MainWindow", u"Middle", None))
        self.labelTripleEnd.setText(QCoreApplication.translate("MainWindow", u"End", None))
        self.buttonSetTriple.setText(QCoreApplication.translate("MainWindow", u"Set Triple Character", None))
        ___qtablewidgetitem9 = self.tableTriples.horizontalHeaderItem(0)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("MainWindow", u"Previous Character 2", None));
        ___qtablewidgetitem10 = self.tableTriples.horizontalHeaderItem(1)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("MainWindow", u"Previous Character 1", None));
        ___qtablewidgetitem11 = self.tableTriples.horizontalHeaderItem(2)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("MainWindow", u"Character", None));
        ___qtablewidgetitem12 = self.tableTriples.horizontalHeaderItem(3)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("MainWindow", u"Start", None));
        ___qtablewidgetitem13 = self.tableTriples.horizontalHeaderItem(4)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("MainWindow", u"Middle", None));
        ___qtablewidgetitem14 = self.tableTriples.horizontalHeaderItem(5)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("MainWindow", u"End", None));
        self.buttonAddTriple.setText(QCoreApplication.translate("MainWindow", u"Add Row", None))
        self.buttonRemoveTriple.setText(QCoreApplication.translate("MainWindow", u"Remove Selected Row", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabTriples), QCoreApplication.translate("MainWindow", u"Triples", None))
        self.buttonGenerate.setText(QCoreApplication.translate("MainWindow", u"Generate Name", None))
        self.lineEditGeneratedName.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Generated Name", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuFormat.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
    # retranslateUi

