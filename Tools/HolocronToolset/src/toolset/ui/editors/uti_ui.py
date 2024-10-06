
################################################################################
## Form generated from reading UI file 'uti.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(550, 323)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.horizontalLayout = QHBoxLayout(self.tab)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName("label_6")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.nameEdit = LocalizedStringLineEdit(self.tab)
        self.nameEdit.setObjectName("nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_18.addWidget(self.nameEdit)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_18)

        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName("label_14")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.tagEdit = QLineEdit(self.tab)
        self.tagEdit.setObjectName("tagEdit")

        self.horizontalLayout_19.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.tab)
        self.tagGenerateButton.setObjectName("tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_19.addWidget(self.tagGenerateButton)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_19)

        self.label_38 = QLabel(self.tab)
        self.label_38.setObjectName("label_38")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName("horizontalLayout_20")
        self.resrefEdit = QLineEdit(self.tab)
        self.resrefEdit.setObjectName("resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_20.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.tab)
        self.resrefGenerateButton.setObjectName("resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_20.addWidget(self.resrefGenerateButton)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_20)

        self.label_53 = QLabel(self.tab)
        self.label_53.setObjectName("label_53")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_53)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.descEdit = LocalizedStringLineEdit(self.tab)
        self.descEdit.setObjectName("descEdit")
        self.descEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_21.addWidget(self.descEdit)


        self.formLayout.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_21)

        self.label_39 = QLabel(self.tab)
        self.label_39.setObjectName("label_39")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_39)

        self.baseSelect = ComboBox2DA(self.tab)
        self.baseSelect.setObjectName("baseSelect")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.baseSelect)

        self.label_40 = QLabel(self.tab)
        self.label_40.setObjectName("label_40")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_40)

        self.costSpin = QSpinBox(self.tab)
        self.costSpin.setObjectName("costSpin")
        self.costSpin.setMaximum(1000000)

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.costSpin)

        self.label_41 = QLabel(self.tab)
        self.label_41.setObjectName("label_41")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_41)

        self.additionalCostSpin = QSpinBox(self.tab)
        self.additionalCostSpin.setObjectName("additionalCostSpin")
        self.additionalCostSpin.setMaximum(1000000)

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.additionalCostSpin)

        self.label_42 = QLabel(self.tab)
        self.label_42.setObjectName("label_42")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_42)

        self.upgradeSpin = QSpinBox(self.tab)
        self.upgradeSpin.setObjectName("upgradeSpin")
        self.upgradeSpin.setMaximum(255)

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.upgradeSpin)


        self.horizontalLayout.addLayout(self.formLayout)

        self.horizontalSpacer = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.plotCheckbox = QCheckBox(self.tab)
        self.plotCheckbox.setObjectName("plotCheckbox")

        self.verticalLayout.addWidget(self.plotCheckbox)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_43 = QLabel(self.tab)
        self.label_43.setObjectName("label_43")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_43)

        self.chargesSpin = QSpinBox(self.tab)
        self.chargesSpin.setObjectName("chargesSpin")
        self.chargesSpin.setMaximum(255)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.chargesSpin)

        self.label_44 = QLabel(self.tab)
        self.label_44.setObjectName("label_44")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_44)

        self.stackSpin = QSpinBox(self.tab)
        self.stackSpin.setObjectName("stackSpin")
        self.stackSpin.setMaximum(65535)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.stackSpin)

        self.label_45 = QLabel(self.tab)
        self.label_45.setObjectName("label_45")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_45)

        self.modelVarSpin = QSpinBox(self.tab)
        self.modelVarSpin.setObjectName("modelVarSpin")
        self.modelVarSpin.setMaximum(255)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.modelVarSpin)

        self.label_46 = QLabel(self.tab)
        self.label_46.setObjectName("label_46")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_46)

        self.bodyVarSpin = QSpinBox(self.tab)
        self.bodyVarSpin.setObjectName("bodyVarSpin")
        self.bodyVarSpin.setMaximum(255)

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.bodyVarSpin)

        self.label_47 = QLabel(self.tab)
        self.label_47.setObjectName("label_47")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.label_47)

        self.textureVarSpin = QSpinBox(self.tab)
        self.textureVarSpin.setObjectName("textureVarSpin")
        self.textureVarSpin.setMaximum(255)

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.textureVarSpin)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.groupBox = QGroupBox(self.tab)
        self.groupBox.setObjectName("groupBox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMaximumSize(QSize(84, 16777215))
        self.gridLayout_3 = QGridLayout(self.groupBox)
        self.gridLayout_3.setSpacing(3)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout_3.setContentsMargins(3, 3, 3, 3)
        self.iconLabel = QLabel(self.groupBox)
        self.iconLabel.setObjectName("iconLabel")
        self.iconLabel.setMinimumSize(QSize(64, 64))
        self.iconLabel.setMaximumSize(QSize(64, 64))
        self.iconLabel.setScaledContents(True)

        self.gridLayout_3.addWidget(self.iconLabel, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalLayout.setStretch(0, 6)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 5)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.horizontalLayout_2 = QHBoxLayout(self.tab_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QLabel(self.tab_2)
        self.label.setObjectName("label")

        self.verticalLayout_3.addWidget(self.label)

        self.availablePropertyList = QTreeWidget(self.tab_2)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, "1");
        self.availablePropertyList.setHeaderItem(__qtreewidgetitem)
        self.availablePropertyList.setObjectName("availablePropertyList")
        self.availablePropertyList.header().setVisible(False)

        self.verticalLayout_3.addWidget(self.availablePropertyList)


        self.horizontalLayout_2.addLayout(self.verticalLayout_3)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.addPropertyButton = QPushButton(self.tab_2)
        self.addPropertyButton.setObjectName("addPropertyButton")
        self.addPropertyButton.setMaximumSize(QSize(20, 16777215))

        self.verticalLayout_2.addWidget(self.addPropertyButton)

        self.removePropertyButton = QPushButton(self.tab_2)
        self.removePropertyButton.setObjectName("removePropertyButton")
        self.removePropertyButton.setMaximumSize(QSize(20, 16777215))

        self.verticalLayout_2.addWidget(self.removePropertyButton)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_2 = QLabel(self.tab_2)
        self.label_2.setObjectName("label_2")

        self.verticalLayout_4.addWidget(self.label_2)

        self.assignedPropertiesList = QListWidget(self.tab_2)
        self.assignedPropertiesList.setObjectName("assignedPropertiesList")

        self.verticalLayout_4.addWidget(self.assignedPropertiesList)

        self.editPropertyButton = QPushButton(self.tab_2)
        self.editPropertyButton.setObjectName("editPropertyButton")

        self.verticalLayout_4.addWidget(self.editPropertyButton)


        self.horizontalLayout_2.addLayout(self.verticalLayout_4)

        self.tabWidget.addTab(self.tab_2, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName("commentsTab")
        self.gridLayout_2 = QGridLayout(self.commentsTab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.commentsEdit = QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName("commentsEdit")

        self.gridLayout_2.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 550, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", "Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", "Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", "-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", "ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", "-", None))
        self.label_53.setText(QCoreApplication.translate("MainWindow", "Description:", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", "Base Item:", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", "Cost:", None))
        self.label_41.setText(QCoreApplication.translate("MainWindow", "Additional Cost:", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", "Upgrade Level:", None))
        self.plotCheckbox.setText(QCoreApplication.translate("MainWindow", "Plot", None))
        self.label_43.setText(QCoreApplication.translate("MainWindow", "Charges:", None))
        self.label_44.setText(QCoreApplication.translate("MainWindow", "Stack Size:", None))
        self.label_45.setText(QCoreApplication.translate("MainWindow", "Model Variation:", None))
        self.label_46.setText(QCoreApplication.translate("MainWindow", "Body Variation:", None))
        self.label_47.setText(QCoreApplication.translate("MainWindow", "Texture Variation:", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", "Icon", None))
        self.iconLabel.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", "General", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Available Properties", None))
        self.addPropertyButton.setText(QCoreApplication.translate("MainWindow", "->", None))
        self.removePropertyButton.setText(QCoreApplication.translate("MainWindow", "<-", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Assigned Properties", None))
        self.editPropertyButton.setText(QCoreApplication.translate("MainWindow", "Edit Property", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", "Properties", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", "Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
    # retranslateUi

