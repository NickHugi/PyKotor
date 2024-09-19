# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'texture_list.ui'
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
    QHBoxLayout, QLineEdit, QListView, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(327, 359)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.sectionCombo = QComboBox(Form)
        self.sectionCombo.setObjectName(u"sectionCombo")

        self.horizontalLayout_2.addWidget(self.sectionCombo)

        self.refreshButton = QPushButton(Form)
        self.refreshButton.setObjectName(u"refreshButton")
        self.refreshButton.setMinimumSize(QSize(70, 0))

        self.horizontalLayout_2.addWidget(self.refreshButton)

        self.reloadButton = QPushButton(Form)
        self.reloadButton.setObjectName(u"reloadButton")
        self.reloadButton.setMinimumSize(QSize(70, 0))

        self.horizontalLayout_2.addWidget(self.reloadButton)

        self.horizontalLayout_2.setStretch(0, 4)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(2, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.textureLine = QFrame(Form)
        self.textureLine.setObjectName(u"textureLine")
        self.textureLine.setFrameShape(QFrame.HLine)
        self.textureLine.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.textureLine)

        self.searchEdit = QLineEdit(Form)
        self.searchEdit.setObjectName(u"searchEdit")

        self.verticalLayout.addWidget(self.searchEdit)

        self.resourceList = QListView(Form)
        self.resourceList.setObjectName(u"resourceList")
        self.resourceList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resourceList.setProperty("showDropIndicator", False)
        self.resourceList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.resourceList.setIconSize(QSize(64, 64))
        self.resourceList.setProperty("isWrapping", True)
        self.resourceList.setResizeMode(QListView.Adjust)
        self.resourceList.setLayoutMode(QListView.Batched)
        self.resourceList.setGridSize(QSize(92, 92))
        self.resourceList.setViewMode(QListView.IconMode)
        self.resourceList.setUniformItemSizes(True)

        self.verticalLayout.addWidget(self.resourceList)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
#if QT_CONFIG(tooltip)
        self.refreshButton.setToolTip(QCoreApplication.translate("Form", u"Refresh this list.", None))
#endif // QT_CONFIG(tooltip)
        self.refreshButton.setText(QCoreApplication.translate("Form", u"Refresh", None))
#if QT_CONFIG(tooltip)
        self.reloadButton.setToolTip(QCoreApplication.translate("Form", u"Reload the active module/folder.", None))
#endif // QT_CONFIG(tooltip)
        self.reloadButton.setText(QCoreApplication.translate("Form", u"Reload", None))
        self.searchEdit.setPlaceholderText(QCoreApplication.translate("Form", u"search...", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
