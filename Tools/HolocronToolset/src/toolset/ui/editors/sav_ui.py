
################################################################################
## Form generated from reading UI file 'sav.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QMenu, QMenuBar, QStatusBar, QTabWidget, QTableWidget, QToolBox, QTreeView, QVBoxLayout, QWidget


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(809, 633)
        self.actionRebuildCachedModules = QAction(MainWindow)
        self.actionRebuildCachedModules.setObjectName("actionRebuildCachedModules")
        self.actionFlushEventQueue = QAction(MainWindow)
        self.actionFlushEventQueue.setObjectName("actionFlushEventQueue")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabGlobalVars = QWidget()
        self.tabGlobalVars.setObjectName("tabGlobalVars")
        self.verticalLayoutGlobalVars = QVBoxLayout(self.tabGlobalVars)
        self.verticalLayoutGlobalVars.setObjectName("verticalLayoutGlobalVars")
        self.tableWidgetGlobalVars = QTableWidget(self.tabGlobalVars)
        if (self.tableWidgetGlobalVars.columnCount() < 2):
            self.tableWidgetGlobalVars.setColumnCount(2)
        if (self.tableWidgetGlobalVars.rowCount() < 16):
            self.tableWidgetGlobalVars.setRowCount(16)
        self.tableWidgetGlobalVars.setObjectName("tableWidgetGlobalVars")
        self.tableWidgetGlobalVars.setRowCount(16)
        self.tableWidgetGlobalVars.setColumnCount(2)

        self.verticalLayoutGlobalVars.addWidget(self.tableWidgetGlobalVars)

        self.tabWidget.addTab(self.tabGlobalVars, "")
        self.tabCachedModules = QWidget()
        self.tabCachedModules.setObjectName("tabCachedModules")
        self.verticalLayoutCachedModules = QVBoxLayout(self.tabCachedModules)
        self.verticalLayoutCachedModules.setObjectName("verticalLayoutCachedModules")
        self.treeViewCachedModules = QTreeView(self.tabCachedModules)
        self.treeViewCachedModules.setObjectName("treeViewCachedModules")

        self.verticalLayoutCachedModules.addWidget(self.treeViewCachedModules)

        self.tabWidget.addTab(self.tabCachedModules, "")
        self.tabGeneralResources = QWidget()
        self.tabGeneralResources.setObjectName("tabGeneralResources")
        self.verticalLayoutGeneralResources = QVBoxLayout(self.tabGeneralResources)
        self.verticalLayoutGeneralResources.setObjectName("verticalLayoutGeneralResources")
        self.tabWidget.addTab(self.tabGeneralResources, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        self.toolBox = QToolBox(self.centralwidget)
        self.toolBox.setObjectName("toolBox")
        self.page1 = QWidget()
        self.page1.setObjectName("page1")
        self.page1.setGeometry(QRect(0, 0, 392, 385))
        self.toolBox.addItem(self.page1, "")
        self.page2 = QWidget()
        self.page2.setObjectName("page2")
        self.page2.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page2, "")
        self.page3 = QWidget()
        self.page3.setObjectName("page3")
        self.page3.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page3, "")
        self.page4 = QWidget()
        self.page4.setObjectName("page4")
        self.page4.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page4, "")
        self.page5 = QWidget()
        self.page5.setObjectName("page5")
        self.page5.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page5, "")
        self.page6 = QWidget()
        self.page6.setObjectName("page6")
        self.page6.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page6, "")
        self.page7 = QWidget()
        self.page7.setObjectName("page7")
        self.page7.setGeometry(QRect(0, 0, 98, 28))
        self.toolBox.addItem(self.page7, "")

        self.horizontalLayout.addWidget(self.toolBox)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName("menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 809, 21))
        self.menuTools = QMenu(self.menuBar)
        self.menuTools.setObjectName("menuTools")
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
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
        self.actionRebuildCachedModules.setText(QCoreApplication.translate("MainWindow", "Rebuild cached modules", None))
        self.actionFlushEventQueue.setText(QCoreApplication.translate("MainWindow", "Flush EventQueue", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabGlobalVars), QCoreApplication.translate("MainWindow", "Global Variables", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCachedModules), QCoreApplication.translate("MainWindow", "Cached Modules", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabGeneralResources), QCoreApplication.translate("MainWindow", "General Resources", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page1), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page2), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page3), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page4), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page5), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page6), "")
        self.toolBox.setItemText(self.toolBox.indexOf(self.page7), "")
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", "&Tools", None))
        pass
    # retranslateUi

