
################################################################################
## Form generated from reading UI file 'texture_list.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QFrame, QHBoxLayout, QLineEdit, QListView, QPushButton, QVBoxLayout


class Ui_Form:
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(327, 359)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.sectionCombo = QComboBox(Form)
        self.sectionCombo.setObjectName("sectionCombo")

        self.horizontalLayout_2.addWidget(self.sectionCombo)

        self.refreshButton = QPushButton(Form)
        self.refreshButton.setObjectName("refreshButton")
        self.refreshButton.setMinimumSize(QSize(70, 0))

        self.horizontalLayout_2.addWidget(self.refreshButton)

        self.reloadButton = QPushButton(Form)
        self.reloadButton.setObjectName("reloadButton")
        self.reloadButton.setMinimumSize(QSize(70, 0))

        self.horizontalLayout_2.addWidget(self.reloadButton)

        self.horizontalLayout_2.setStretch(0, 4)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(2, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.textureLine = QFrame(Form)
        self.textureLine.setObjectName("textureLine")
        self.textureLine.setFrameShape(QFrame.HLine)
        self.textureLine.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.textureLine)

        self.searchEdit = QLineEdit(Form)
        self.searchEdit.setObjectName("searchEdit")

        self.verticalLayout.addWidget(self.searchEdit)

        self.resourceList = QListView(Form)
        self.resourceList.setObjectName("resourceList")
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
        Form.setWindowTitle(QCoreApplication.translate("Form", "Form", None))
#if QT_CONFIG(tooltip)
        self.refreshButton.setToolTip(QCoreApplication.translate("Form", "Refresh this list.", None))
#endif // QT_CONFIG(tooltip)
        self.refreshButton.setText(QCoreApplication.translate("Form", "Refresh", None))
#if QT_CONFIG(tooltip)
        self.reloadButton.setToolTip(QCoreApplication.translate("Form", "Reload the active module/folder.", None))
#endif // QT_CONFIG(tooltip)
        self.reloadButton.setText(QCoreApplication.translate("Form", "Reload", None))
        self.searchEdit.setPlaceholderText(QCoreApplication.translate("Form", "search...", None))
    # retranslateUi

