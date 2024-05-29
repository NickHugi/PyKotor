# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'resource_list.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFrame,
    QHBoxLayout, QHeaderView, QLineEdit, QPushButton,
    QSizePolicy, QTreeView, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(333, 364)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.sectionCombo = QComboBox(Form)
        self.sectionCombo.setObjectName(u"sectionCombo")
        self.sectionCombo.setMaxVisibleItems(18)

        self.horizontalLayout_2.addWidget(self.sectionCombo)

        self.refreshButton = QPushButton(Form)
        self.refreshButton.setObjectName(u"refreshButton")
        self.refreshButton.setMinimumSize(QSize(70, 0))
        self.refreshButton.setMaximumSize(QSize(16777215, 70))

        self.horizontalLayout_2.addWidget(self.refreshButton)

        self.horizontalLayout_2.setStretch(0, 4)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.searchEdit = QLineEdit(Form)
        self.searchEdit.setObjectName(u"searchEdit")

        self.horizontalLayout_4.addWidget(self.searchEdit)

        self.reloadButton = QPushButton(Form)
        self.reloadButton.setObjectName(u"reloadButton")
        self.reloadButton.setEnabled(True)
        self.reloadButton.setMinimumSize(QSize(70, 0))
        self.reloadButton.setMaximumSize(QSize(70, 16777215))

        self.horizontalLayout_4.addWidget(self.reloadButton)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.resourceTree = QTreeView(Form)
        self.resourceTree.setObjectName(u"resourceTree")
        self.resourceTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resourceTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resourceTree.setAlternatingRowColors(True)
        self.resourceTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.resourceTree.setSortingEnabled(True)
        self.resourceTree.setAllColumnsShowFocus(True)
        self.resourceTree.header().setProperty("showSortIndicator", True)
        self.resourceTree.header().setStretchLastSection(True)

        self.verticalLayout.addWidget(self.resourceTree)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
#if QT_CONFIG(tooltip)
        self.refreshButton.setToolTip(QCoreApplication.translate("Form", u"Refresh the list of modules.", None))
#endif // QT_CONFIG(tooltip)
        self.refreshButton.setText(QCoreApplication.translate("Form", u"Refresh", None))
        self.searchEdit.setPlaceholderText(QCoreApplication.translate("Form", u"search...", None))
#if QT_CONFIG(tooltip)
        self.reloadButton.setToolTip(QCoreApplication.translate("Form", u"Reload the active module.", None))
#endif // QT_CONFIG(tooltip)
        self.reloadButton.setText(QCoreApplication.translate("Form", u"Reload", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
