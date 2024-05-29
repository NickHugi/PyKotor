# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'twoda.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGroupBox, QHeaderView,
    QLineEdit, QMainWindow, QMenu, QMenuBar,
    QSizePolicy, QTableView, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(635, 454)
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
        self.actionToggleFilter = QAction(MainWindow)
        self.actionToggleFilter.setObjectName(u"actionToggleFilter")
        self.actionCopy = QAction(MainWindow)
        self.actionCopy.setObjectName(u"actionCopy")
        self.actionPaste = QAction(MainWindow)
        self.actionPaste.setObjectName(u"actionPaste")
        self.actionInsertRow = QAction(MainWindow)
        self.actionInsertRow.setObjectName(u"actionInsertRow")
        self.actionRemoveRows = QAction(MainWindow)
        self.actionRemoveRows.setObjectName(u"actionRemoveRows")
        self.actionRedoRowLabels = QAction(MainWindow)
        self.actionRedoRowLabels.setObjectName(u"actionRedoRowLabels")
        self.actionDuplicateRow = QAction(MainWindow)
        self.actionDuplicateRow.setObjectName(u"actionDuplicateRow")
        self.actionplaceholder = QAction(MainWindow)
        self.actionplaceholder.setObjectName(u"actionplaceholder")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.filterBox = QGroupBox(self.centralwidget)
        self.filterBox.setObjectName(u"filterBox")
        self.verticalLayout = QVBoxLayout(self.filterBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.filterEdit = QLineEdit(self.filterBox)
        self.filterEdit.setObjectName(u"filterEdit")

        self.verticalLayout.addWidget(self.filterEdit)


        self.verticalLayout_2.addWidget(self.filterBox)

        self.twodaTable = QTableView(self.centralwidget)
        self.twodaTable.setObjectName(u"twodaTable")
        self.twodaTable.setStyleSheet(u"")
        self.twodaTable.setAlternatingRowColors(True)
        self.twodaTable.setSelectionMode(QAbstractItemView.ContiguousSelection)

        self.verticalLayout_2.addWidget(self.twodaTable)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 635, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuSetRowHeader = QMenu(self.menuView)
        self.menuSetRowHeader.setObjectName(u"menuSetRowHeader")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuTools.addAction(self.actionToggleFilter)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionInsertRow)
        self.menuTools.addAction(self.actionDuplicateRow)
        self.menuTools.addAction(self.actionRemoveRows)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionRedoRowLabels)
        self.menuView.addAction(self.menuSetRowHeader.menuAction())
        self.menuSetRowHeader.addAction(self.actionplaceholder)

        self.retranslateUi(MainWindow)

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
        self.actionToggleFilter.setText(QCoreApplication.translate("MainWindow", u"Toggle Filter", None))
#if QT_CONFIG(shortcut)
        self.actionToggleFilter.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+F", None))
#endif // QT_CONFIG(shortcut)
        self.actionCopy.setText(QCoreApplication.translate("MainWindow", u"Copy", None))
#if QT_CONFIG(shortcut)
        self.actionCopy.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+C", None))
#endif // QT_CONFIG(shortcut)
        self.actionPaste.setText(QCoreApplication.translate("MainWindow", u"Paste", None))
#if QT_CONFIG(shortcut)
        self.actionPaste.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+V", None))
#endif // QT_CONFIG(shortcut)
        self.actionInsertRow.setText(QCoreApplication.translate("MainWindow", u"Insert Row", None))
#if QT_CONFIG(shortcut)
        self.actionInsertRow.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+I", None))
#endif // QT_CONFIG(shortcut)
        self.actionRemoveRows.setText(QCoreApplication.translate("MainWindow", u"Remove Rows", None))
#if QT_CONFIG(shortcut)
        self.actionRemoveRows.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Del", None))
#endif // QT_CONFIG(shortcut)
        self.actionRedoRowLabels.setText(QCoreApplication.translate("MainWindow", u"Redo Row Labels", None))
#if QT_CONFIG(shortcut)
        self.actionRedoRowLabels.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+L", None))
#endif // QT_CONFIG(shortcut)
        self.actionDuplicateRow.setText(QCoreApplication.translate("MainWindow", u"Duplicate Row", None))
#if QT_CONFIG(shortcut)
        self.actionDuplicateRow.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+D", None))
#endif // QT_CONFIG(shortcut)
        self.actionplaceholder.setText(QCoreApplication.translate("MainWindow", u"placeholder", None))
        self.filterBox.setTitle(QCoreApplication.translate("MainWindow", u"Filter", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menuSetRowHeader.setTitle(QCoreApplication.translate("MainWindow", u"Set Row Header", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
