# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'insert_instance.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.renderer.model import ModelRenderer


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 447)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.sidebarLayout = QVBoxLayout()
        self.sidebarLayout.setObjectName(u"sidebarLayout")
        self.dynamicTextLabel = QLabel(Dialog)
        self.dynamicTextLabel.setObjectName(u"dynamicTextLabel")

        self.sidebarLayout.addWidget(self.dynamicTextLabel)

        self.staticTextLabel = QLabel(Dialog)
        self.staticTextLabel.setObjectName(u"staticTextLabel")

        self.sidebarLayout.addWidget(self.staticTextLabel)

        self.previewRenderer = ModelRenderer(Dialog)
        self.previewRenderer.setObjectName(u"previewRenderer")
        self.previewRenderer.setMinimumSize(QSize(350, 0))
        self.previewRenderer.setMouseTracking(True)
        self.previewRenderer.setFocusPolicy(Qt.StrongFocus)

        self.sidebarLayout.addWidget(self.previewRenderer)


        self.horizontalLayout.addLayout(self.sidebarLayout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.resrefEdit = QLineEdit(Dialog)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setEnabled(False)
        self.resrefEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.resrefEdit)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.locationSelect = QComboBox(Dialog)
        self.locationSelect.setObjectName(u"locationSelect")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.locationSelect)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.reuseResourceRadio = QRadioButton(Dialog)
        self.reuseResourceRadio.setObjectName(u"reuseResourceRadio")
        self.reuseResourceRadio.setChecked(True)

        self.horizontalLayout_2.addWidget(self.reuseResourceRadio)

        self.copyResourceRadio = QRadioButton(Dialog)
        self.copyResourceRadio.setObjectName(u"copyResourceRadio")

        self.horizontalLayout_2.addWidget(self.copyResourceRadio)

        self.createResourceRadio = QRadioButton(Dialog)
        self.createResourceRadio.setObjectName(u"createResourceRadio")

        self.horizontalLayout_2.addWidget(self.createResourceRadio)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.resourceFilter = QLineEdit(self.groupBox)
        self.resourceFilter.setObjectName(u"resourceFilter")

        self.verticalLayout_2.addWidget(self.resourceFilter)

        self.resourceList = QListWidget(self.groupBox)
        self.resourceList.setObjectName(u"resourceList")
        self.resourceList.setSortingEnabled(True)

        self.verticalLayout_2.addWidget(self.resourceList)


        self.verticalLayout.addWidget(self.groupBox)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.horizontalLayout.addLayout(self.verticalLayout)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Insert Instance", None))
        self.dynamicTextLabel.setText(QCoreApplication.translate("Dialog", u"Dynamic Text", None))
        self.staticTextLabel.setText(QCoreApplication.translate("Dialog", u"Selected Resource", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"ResRef:", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Location:", None))
        self.reuseResourceRadio.setText(QCoreApplication.translate("Dialog", u"Reuse Resource", None))
        self.copyResourceRadio.setText(QCoreApplication.translate("Dialog", u"Copy Resource", None))
        self.createResourceRadio.setText(QCoreApplication.translate("Dialog", u"Create Resource", None))
        self.groupBox.setTitle("")
        self.resourceFilter.setPlaceholderText(QCoreApplication.translate("Dialog", u"search...", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
