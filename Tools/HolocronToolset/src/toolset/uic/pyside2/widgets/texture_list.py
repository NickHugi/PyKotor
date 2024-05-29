# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'texture_list.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(327, 359)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.sectionCombo = QComboBox(Form)
        self.sectionCombo.setObjectName(u"sectionCombo")

        self.verticalLayout.addWidget(self.sectionCombo)

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
        self.searchEdit.setPlaceholderText(QCoreApplication.translate("Form", u"search...", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
