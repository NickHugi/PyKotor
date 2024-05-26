# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sav.ui'
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
        MainWindow.resize(809, 633)
        self.actionRebuildCachedModules = QAction(MainWindow)
        self.actionRebuildCachedModules.setObjectName(u"actionRebuildCachedModules")
        self.actionFlushEventQueue = QAction(MainWindow)
        self.actionFlushEventQueue.setObjectName(u"actionFlushEventQueue")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabGlobalVars = QWidget()
        self.tabGlobalVars.setObjectName(u"tabGlobalVars")
        self.verticalLayoutGlobalVars = QVBoxLayout(self.tabGlobalVars)
        self.verticalLayoutGlobalVars.setObjectName(u"verticalLayoutGlobalVars")
        self.tableWidgetGlobalVars = QTableWidget(self.tabGlobalVars)
        if (self.tableWidgetGlobalVars.columnCount() < 2):
            self.tableWidgetGlobalVars.setColumnCount(2)
        if (self.tableWidgetGlobalVars.rowCount() < 16):
            self.tableWidgetGlobalVars.setRowCount(16)
        self.tableWidgetGlobalVars.setObjectName(u"tableWidgetGlobalVars")
        self.tableWidgetGlobalVars.setRowCount(16)
        self.tableWidgetGlobalVars.setColumnCount(2)

        self.verticalLayoutGlobalVars.addWidget(self.tableWidgetGlobalVars)

        self.tabWidget.addTab(self.tabGlobalVars, "")
        self.tabCachedModules = QWidget()
        self.tabCachedModules.setObjectName(u"tabCachedModules")
        self.verticalLayoutCachedModules = QVBoxLayout(self.tabCachedModules)
        self.verticalLayoutCachedModules.setObjectName(u"verticalLayoutCachedModules")
        self.treeViewCachedModules = QTreeView(self.tabCachedModules)
        self.treeViewCachedModules.setObjectName(u"treeViewCachedModules")

        self.verticalLayoutCachedModules.addWidget(self.treeViewCachedModules)

        self.tabWidget.addTab(self.tabCachedModules, "")
        self.tabGeneralResources = QWidget()
        self.tabGeneralResources.setObjectName(u"tabGeneralResources")
        self.verticalLayoutGeneralResources = QVBoxLayout(self.tabGeneralResources)
        self.verticalLayoutGeneralResources.setObjectName(u"verticalLayoutGeneralResources")
        self.tabWidget.addTab(self.tabGeneralResources, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        self.toolBox = QToolBox(self.centralwidget)
        self.toolBox.setObjectName(u"toolBox")
        self.page1 = QWidget()
        self.page1.setObjectName(u"page1")
        self.page1.setGeometry(QRect(0, 0, 392, 385))
        self.toolBox.addItem(self.page1, u"")
        self.page2 = QWidget()
        self.page2.setObjectName(u"page2")
        self.page2.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page2, u"")
        self.page3 = QWidget()
        self.page3.setObjectName(u"page3")
        self.page3.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page3, u"")
        self.page4 = QWidget()
        self.page4.setObjectName(u"page4")
        self.page4.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page4, u"")
        self.page5 = QWidget()
        self.page5.setObjectName(u"page5")
        self.page5.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page5, u"")
        self.page6 = QWidget()
        self.page6.setObjectName(u"page6")
        self.page6.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page6, u"")
        self.page7 = QWidget()
        self.page7.setObjectName(u"page7")
        self.page7.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page7, u"")

        self.horizontalLayout.addWidget(self.toolBox)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 809, 21))
        self.menuTools = QMenu(self.menuBar)
        self.menuTools.setObjectName(u"menuTools")
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.menuBar.addAction(self.menuTools.menuAction())
        self.menuTools.addAction(self.actionRebuildCachedModules)
        self.menuTools.addAction(self.actionFlushEventQueue)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)
        self.toolBox.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        self.actionRebuildCachedModules.setText(QCoreApplication.translate("MainWindow", u"Rebuild cached modules", None))
        self.actionFlushEventQueue.setText(QCoreApplication.translate("MainWindow", u"Flush EventQueue", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabGlobalVars), QCoreApplication.translate("MainWindow", u"Global Variables", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCachedModules), QCoreApplication.translate("MainWindow", u"Cached Modules", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabGeneralResources), QCoreApplication.translate("MainWindow", u"General Resources", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page1), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page2), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page3), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page4), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page5), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page6), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page7), "")
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"&Tools", None))
        pass
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
