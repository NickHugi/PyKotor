
################################################################################
## Form generated from reading UI file 'utc.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
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
    QSlider,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.renderer.model import ModelRenderer
from utility.ui_libraries.qt.widgets.widgets.combobox import FilterComboBox


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1007, 585)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionSaveUnusedFields = QAction(MainWindow)
        self.actionSaveUnusedFields.setObjectName("actionSaveUnusedFields")
        self.actionSaveUnusedFields.setCheckable(True)
        self.actionAlwaysSaveK2Fields = QAction(MainWindow)
        self.actionAlwaysSaveK2Fields.setObjectName("actionAlwaysSaveK2Fields")
        self.actionAlwaysSaveK2Fields.setCheckable(True)
        self.actionShowPreview = QAction(MainWindow)
        self.actionShowPreview.setObjectName("actionShowPreview")
        self.actionShowPreview.setCheckable(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_15 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.previewRenderer = ModelRenderer(self.centralwidget)
        self.previewRenderer.setObjectName("previewRenderer")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.previewRenderer.sizePolicy().hasHeightForWidth())
        self.previewRenderer.setSizePolicy(sizePolicy1)
        self.previewRenderer.setMinimumSize(QSize(350, 0))
        self.previewRenderer.setMouseTracking(True)
        self.previewRenderer.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayout_15.addWidget(self.previewRenderer)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QGroupBox(self.tab)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.firstnameEdit = LocalizedStringLineEdit(self.groupBox)
        self.firstnameEdit.setObjectName("firstnameEdit")
        self.firstnameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout.addWidget(self.firstnameEdit)

        self.firstnameRandomButton = QPushButton(self.groupBox)
        self.firstnameRandomButton.setObjectName("firstnameRandomButton")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.firstnameRandomButton.sizePolicy().hasHeightForWidth())
        self.firstnameRandomButton.setSizePolicy(sizePolicy2)
        self.firstnameRandomButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout.addWidget(self.firstnameRandomButton)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lastnameEdit = LocalizedStringLineEdit(self.groupBox)
        self.lastnameEdit.setObjectName("lastnameEdit")
        self.lastnameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_2.addWidget(self.lastnameEdit)

        self.lastnameRandomButton = QPushButton(self.groupBox)
        self.lastnameRandomButton.setObjectName("lastnameRandomButton")
        sizePolicy2.setHeightForWidth(self.lastnameRandomButton.sizePolicy().hasHeightForWidth())
        self.lastnameRandomButton.setSizePolicy(sizePolicy2)
        self.lastnameRandomButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_2.addWidget(self.lastnameRandomButton)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_2)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tagEdit = QLineEdit(self.groupBox)
        self.tagEdit.setObjectName("tagEdit")

        self.horizontalLayout_3.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.groupBox)
        self.tagGenerateButton.setObjectName("tagGenerateButton")
        sizePolicy2.setHeightForWidth(self.tagGenerateButton.sizePolicy().hasHeightForWidth())
        self.tagGenerateButton.setSizePolicy(sizePolicy2)
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_3.addWidget(self.tagGenerateButton)

        self.horizontalSpacer = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_3)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.resrefEdit = QLineEdit(self.groupBox)
        self.resrefEdit.setObjectName("resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_8.addWidget(self.resrefEdit)

        self.horizontalSpacer_2 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_2)


        self.formLayout.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_8)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.appearanceSelect = ComboBox2DA(self.groupBox)
        self.appearanceSelect.setObjectName("appearanceSelect")

        self.horizontalLayout_4.addWidget(self.appearanceSelect)

        self.horizontalSpacer_5 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)


        self.formLayout.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_4)

        self.label_10 = QLabel(self.groupBox)
        self.label_10.setObjectName("label_10")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_10)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.soundsetSelect = ComboBox2DA(self.groupBox)
        self.soundsetSelect.setObjectName("soundsetSelect")

        self.horizontalLayout_10.addWidget(self.soundsetSelect)

        self.horizontalSpacer_6 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_6)


        self.formLayout.setLayout(5, QFormLayout.FieldRole, self.horizontalLayout_10)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_5)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.conversationEdit = FilterComboBox(self.groupBox)
        self.conversationEdit.setObjectName("conversationEdit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(1)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.conversationEdit.sizePolicy().hasHeightForWidth())
        self.conversationEdit.setSizePolicy(sizePolicy3)

        self.horizontalLayout_5.addWidget(self.conversationEdit)

        self.conversationModifyButton = QPushButton(self.groupBox)
        self.conversationModifyButton.setObjectName("conversationModifyButton")
        sizePolicy2.setHeightForWidth(self.conversationModifyButton.sizePolicy().hasHeightForWidth())
        self.conversationModifyButton.setSizePolicy(sizePolicy2)
        font = QFont()
        font.setStyleStrategy(QFont.PreferAntialias)
        self.conversationModifyButton.setFont(font)

        self.horizontalLayout_5.addWidget(self.conversationModifyButton)

        self.horizontalSpacer_10 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_10)


        self.formLayout.setLayout(6, QFormLayout.FieldRole, self.horizontalLayout_5)


        self.gridLayout_2.addLayout(self.formLayout, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_15 = QGroupBox(self.tab)
        self.groupBox_15.setObjectName("groupBox_15")
        self.verticalLayout_10 = QVBoxLayout(self.groupBox_15)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.inventoryCountLabel = QLabel(self.groupBox_15)
        self.inventoryCountLabel.setObjectName("inventoryCountLabel")

        self.verticalLayout_10.addWidget(self.inventoryCountLabel)

        self.inventoryButton = QPushButton(self.groupBox_15)
        self.inventoryButton.setObjectName("inventoryButton")

        self.verticalLayout_10.addWidget(self.inventoryButton)


        self.verticalLayout.addWidget(self.groupBox_15)

        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_7 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.portraitPicture = QLabel(self.groupBox_2)
        self.portraitPicture.setObjectName("portraitPicture")
        self.portraitPicture.setMinimumSize(QSize(64, 64))
        self.portraitPicture.setMaximumSize(QSize(64, 64))
        self.portraitPicture.setStyleSheet("background-color: black;")
        self.portraitPicture.setFrameShape(QFrame.Box)
        self.portraitPicture.setScaledContents(True)

        self.horizontalLayout_7.addWidget(self.portraitPicture)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.portraitSelect = ComboBox2DA(self.groupBox_2)
        self.portraitSelect.setObjectName("portraitSelect")

        self.horizontalLayout_6.addWidget(self.portraitSelect)


        self.horizontalLayout_7.addLayout(self.horizontalLayout_6)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_5)

        self.verticalLayout.setStretch(0, 1)
        self.tabWidget.addTab(self.tab, "")
        self.advancedTab = QWidget()
        self.advancedTab.setObjectName("advancedTab")
        self.verticalLayout_4 = QVBoxLayout(self.advancedTab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.groupBox_3 = QGroupBox(self.advancedTab)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_9 = QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.disarmableCheckbox = QCheckBox(self.groupBox_3)
        self.disarmableCheckbox.setObjectName("disarmableCheckbox")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.disarmableCheckbox.sizePolicy().hasHeightForWidth())
        self.disarmableCheckbox.setSizePolicy(sizePolicy4)

        self.verticalLayout_2.addWidget(self.disarmableCheckbox)

        self.noPermDeathCheckbox = QCheckBox(self.groupBox_3)
        self.noPermDeathCheckbox.setObjectName("noPermDeathCheckbox")
        sizePolicy4.setHeightForWidth(self.noPermDeathCheckbox.sizePolicy().hasHeightForWidth())
        self.noPermDeathCheckbox.setSizePolicy(sizePolicy4)

        self.verticalLayout_2.addWidget(self.noPermDeathCheckbox)

        self.min1HpCheckbox = QCheckBox(self.groupBox_3)
        self.min1HpCheckbox.setObjectName("min1HpCheckbox")
        sizePolicy4.setHeightForWidth(self.min1HpCheckbox.sizePolicy().hasHeightForWidth())
        self.min1HpCheckbox.setSizePolicy(sizePolicy4)

        self.verticalLayout_2.addWidget(self.min1HpCheckbox)

        self.plotCheckbox = QCheckBox(self.groupBox_3)
        self.plotCheckbox.setObjectName("plotCheckbox")
        sizePolicy4.setHeightForWidth(self.plotCheckbox.sizePolicy().hasHeightForWidth())
        self.plotCheckbox.setSizePolicy(sizePolicy4)

        self.verticalLayout_2.addWidget(self.plotCheckbox)

        self.isPcCheckbox = QCheckBox(self.groupBox_3)
        self.isPcCheckbox.setObjectName("isPcCheckbox")
        sizePolicy4.setHeightForWidth(self.isPcCheckbox.sizePolicy().hasHeightForWidth())
        self.isPcCheckbox.setSizePolicy(sizePolicy4)

        self.verticalLayout_2.addWidget(self.isPcCheckbox)


        self.horizontalLayout_9.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.noReorientateCheckbox = QCheckBox(self.groupBox_3)
        self.noReorientateCheckbox.setObjectName("noReorientateCheckbox")

        self.verticalLayout_3.addWidget(self.noReorientateCheckbox)

        self.noBlockCheckbox = QCheckBox(self.groupBox_3)
        self.noBlockCheckbox.setObjectName("noBlockCheckbox")

        self.verticalLayout_3.addWidget(self.noBlockCheckbox)

        self.hologramCheckbox = QCheckBox(self.groupBox_3)
        self.hologramCheckbox.setObjectName("hologramCheckbox")

        self.verticalLayout_3.addWidget(self.hologramCheckbox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)


        self.horizontalLayout_9.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(self.advancedTab)
        self.groupBox_4.setObjectName("groupBox_4")
        self.formLayout_2 = QFormLayout(self.groupBox_4)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_8 = QLabel(self.groupBox_4)
        self.label_8.setObjectName("label_8")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.raceSelect = ComboBox2DA(self.groupBox_4)
        self.raceSelect.setObjectName("raceSelect")
        sizePolicy2.setHeightForWidth(self.raceSelect.sizePolicy().hasHeightForWidth())
        self.raceSelect.setSizePolicy(sizePolicy2)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.raceSelect)

        self.label_9 = QLabel(self.groupBox_4)
        self.label_9.setObjectName("label_9")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_9)

        self.subraceSelect = ComboBox2DA(self.groupBox_4)
        self.subraceSelect.setObjectName("subraceSelect")
        sizePolicy2.setHeightForWidth(self.subraceSelect.sizePolicy().hasHeightForWidth())
        self.subraceSelect.setSizePolicy(sizePolicy2)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.subraceSelect)


        self.verticalLayout_4.addWidget(self.groupBox_4)

        self.groupBox_5 = QGroupBox(self.advancedTab)
        self.groupBox_5.setObjectName("groupBox_5")
        self.verticalLayout_18 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_18.setObjectName("verticalLayout_18")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_16 = QLabel(self.groupBox_5)
        self.label_16.setObjectName("label_16")
        sizePolicy3.setHeightForWidth(self.label_16.sizePolicy().hasHeightForWidth())
        self.label_16.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_16)

        self.speedSelect = ComboBox2DA(self.groupBox_5)
        self.speedSelect.setObjectName("speedSelect")
        sizePolicy2.setHeightForWidth(self.speedSelect.sizePolicy().hasHeightForWidth())
        self.speedSelect.setSizePolicy(sizePolicy2)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.speedSelect)

        self.label_11 = QLabel(self.groupBox_5)
        self.label_11.setObjectName("label_11")
        sizePolicy3.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.factionSelect = ComboBox2DA(self.groupBox_5)
        self.factionSelect.setObjectName("factionSelect")
        sizePolicy2.setHeightForWidth(self.factionSelect.sizePolicy().hasHeightForWidth())
        self.factionSelect.setSizePolicy(sizePolicy2)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.factionSelect)

        self.genderAdvancedLabel = QLabel(self.groupBox_5)
        self.genderAdvancedLabel.setObjectName("genderAdvancedLabel")
        sizePolicy3.setHeightForWidth(self.genderAdvancedLabel.sizePolicy().hasHeightForWidth())
        self.genderAdvancedLabel.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.genderAdvancedLabel)

        self.genderSelect = ComboBox2DA(self.groupBox_5)
        self.genderSelect.setObjectName("genderSelect")
        sizePolicy2.setHeightForWidth(self.genderSelect.sizePolicy().hasHeightForWidth())
        self.genderSelect.setSizePolicy(sizePolicy2)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.genderSelect)

        self.label_12 = QLabel(self.groupBox_5)
        self.label_12.setObjectName("label_12")
        sizePolicy3.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label_12)

        self.perceptionSelect = ComboBox2DA(self.groupBox_5)
        self.perceptionSelect.setObjectName("perceptionSelect")
        sizePolicy2.setHeightForWidth(self.perceptionSelect.sizePolicy().hasHeightForWidth())
        self.perceptionSelect.setSizePolicy(sizePolicy2)

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.perceptionSelect)

        self.label_13 = QLabel(self.groupBox_5)
        self.label_13.setObjectName("label_13")
        sizePolicy3.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(4, QFormLayout.LabelRole, self.label_13)

        self.challengeRatingSpin = QDoubleSpinBox(self.groupBox_5)
        self.challengeRatingSpin.setObjectName("challengeRatingSpin")
        sizePolicy2.setHeightForWidth(self.challengeRatingSpin.sizePolicy().hasHeightForWidth())
        self.challengeRatingSpin.setSizePolicy(sizePolicy2)

        self.formLayout_3.setWidget(4, QFormLayout.FieldRole, self.challengeRatingSpin)


        self.verticalLayout_18.addLayout(self.formLayout_3)

        self.k2onlyBox = QFrame(self.groupBox_5)
        self.k2onlyBox.setObjectName("k2onlyBox")
        self.k2onlyBox.setFrameShape(QFrame.NoFrame)
        self.k2onlyBox.setFrameShadow(QFrame.Plain)
        self.formLayout_24 = QFormLayout(self.k2onlyBox)
        self.formLayout_24.setObjectName("formLayout_24")
        self.formLayout_24.setContentsMargins(0, 0, 0, 0)
        self.label_102 = QLabel(self.k2onlyBox)
        self.label_102.setObjectName("label_102")
        sizePolicy3.setHeightForWidth(self.label_102.sizePolicy().hasHeightForWidth())
        self.label_102.setSizePolicy(sizePolicy3)

        self.formLayout_24.setWidget(1, QFormLayout.LabelRole, self.label_102)

        self.blindSpotSpin = QDoubleSpinBox(self.k2onlyBox)
        self.blindSpotSpin.setObjectName("blindSpotSpin")

        self.formLayout_24.setWidget(1, QFormLayout.FieldRole, self.blindSpotSpin)

        self.label_110 = QLabel(self.k2onlyBox)
        self.label_110.setObjectName("label_110")
        sizePolicy3.setHeightForWidth(self.label_110.sizePolicy().hasHeightForWidth())
        self.label_110.setSizePolicy(sizePolicy3)

        self.formLayout_24.setWidget(2, QFormLayout.LabelRole, self.label_110)

        self.line = QFrame(self.k2onlyBox)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.formLayout_24.setWidget(0, QFormLayout.FieldRole, self.line)

        self.multiplierSetSpin = QSpinBox(self.k2onlyBox)
        self.multiplierSetSpin.setObjectName("multiplierSetSpin")
        self.multiplierSetSpin.setMinimum(-2147483648)
        self.multiplierSetSpin.setMaximum(2147483647)

        self.formLayout_24.setWidget(2, QFormLayout.FieldRole, self.multiplierSetSpin)


        self.verticalLayout_18.addWidget(self.k2onlyBox)


        self.verticalLayout_4.addWidget(self.groupBox_5)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_4)

        self.verticalLayout_4.setStretch(0, 1)
        self.verticalLayout_4.setStretch(1, 1)
        self.tabWidget.addTab(self.advancedTab, "")
        self.statsTab = QWidget()
        self.statsTab.setObjectName("statsTab")
        self.horizontalLayout_11 = QHBoxLayout(self.statsTab)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.groupBox_6 = QGroupBox(self.statsTab)
        self.groupBox_6.setObjectName("groupBox_6")
        sizePolicy.setHeightForWidth(self.groupBox_6.sizePolicy().hasHeightForWidth())
        self.groupBox_6.setSizePolicy(sizePolicy)
        self.formLayout_4 = QFormLayout(self.groupBox_6)
        self.formLayout_4.setObjectName("formLayout_4")
        self.label_17 = QLabel(self.groupBox_6)
        self.label_17.setObjectName("label_17")
        sizePolicy2.setHeightForWidth(self.label_17.sizePolicy().hasHeightForWidth())
        self.label_17.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_17)

        self.computerUseSpin = QSpinBox(self.groupBox_6)
        self.computerUseSpin.setObjectName("computerUseSpin")
        sizePolicy2.setHeightForWidth(self.computerUseSpin.sizePolicy().hasHeightForWidth())
        self.computerUseSpin.setSizePolicy(sizePolicy2)
        self.computerUseSpin.setMinimum(-2147483648)
        self.computerUseSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.computerUseSpin)

        self.label_18 = QLabel(self.groupBox_6)
        self.label_18.setObjectName("label_18")
        sizePolicy2.setHeightForWidth(self.label_18.sizePolicy().hasHeightForWidth())
        self.label_18.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_18)

        self.demolitionsSpin = QSpinBox(self.groupBox_6)
        self.demolitionsSpin.setObjectName("demolitionsSpin")
        sizePolicy2.setHeightForWidth(self.demolitionsSpin.sizePolicy().hasHeightForWidth())
        self.demolitionsSpin.setSizePolicy(sizePolicy2)
        self.demolitionsSpin.setMinimum(-2147483648)
        self.demolitionsSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.demolitionsSpin)

        self.label_19 = QLabel(self.groupBox_6)
        self.label_19.setObjectName("label_19")
        sizePolicy2.setHeightForWidth(self.label_19.sizePolicy().hasHeightForWidth())
        self.label_19.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_19)

        self.stealthSpin = QSpinBox(self.groupBox_6)
        self.stealthSpin.setObjectName("stealthSpin")
        sizePolicy2.setHeightForWidth(self.stealthSpin.sizePolicy().hasHeightForWidth())
        self.stealthSpin.setSizePolicy(sizePolicy2)
        self.stealthSpin.setMinimum(-2147483648)
        self.stealthSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.stealthSpin)

        self.label_20 = QLabel(self.groupBox_6)
        self.label_20.setObjectName("label_20")
        sizePolicy2.setHeightForWidth(self.label_20.sizePolicy().hasHeightForWidth())
        self.label_20.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(3, QFormLayout.LabelRole, self.label_20)

        self.awarenessSpin = QSpinBox(self.groupBox_6)
        self.awarenessSpin.setObjectName("awarenessSpin")
        sizePolicy2.setHeightForWidth(self.awarenessSpin.sizePolicy().hasHeightForWidth())
        self.awarenessSpin.setSizePolicy(sizePolicy2)
        self.awarenessSpin.setMinimum(-2147483648)
        self.awarenessSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.awarenessSpin)

        self.label_21 = QLabel(self.groupBox_6)
        self.label_21.setObjectName("label_21")
        sizePolicy2.setHeightForWidth(self.label_21.sizePolicy().hasHeightForWidth())
        self.label_21.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(4, QFormLayout.LabelRole, self.label_21)

        self.persuadeSpin = QSpinBox(self.groupBox_6)
        self.persuadeSpin.setObjectName("persuadeSpin")
        sizePolicy2.setHeightForWidth(self.persuadeSpin.sizePolicy().hasHeightForWidth())
        self.persuadeSpin.setSizePolicy(sizePolicy2)
        self.persuadeSpin.setMinimum(-2147483648)
        self.persuadeSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(4, QFormLayout.FieldRole, self.persuadeSpin)

        self.label_22 = QLabel(self.groupBox_6)
        self.label_22.setObjectName("label_22")
        sizePolicy2.setHeightForWidth(self.label_22.sizePolicy().hasHeightForWidth())
        self.label_22.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(5, QFormLayout.LabelRole, self.label_22)

        self.repairSpin = QSpinBox(self.groupBox_6)
        self.repairSpin.setObjectName("repairSpin")
        sizePolicy2.setHeightForWidth(self.repairSpin.sizePolicy().hasHeightForWidth())
        self.repairSpin.setSizePolicy(sizePolicy2)
        self.repairSpin.setMinimum(-2147483648)
        self.repairSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(5, QFormLayout.FieldRole, self.repairSpin)

        self.label_23 = QLabel(self.groupBox_6)
        self.label_23.setObjectName("label_23")
        sizePolicy2.setHeightForWidth(self.label_23.sizePolicy().hasHeightForWidth())
        self.label_23.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(6, QFormLayout.LabelRole, self.label_23)

        self.securitySpin = QSpinBox(self.groupBox_6)
        self.securitySpin.setObjectName("securitySpin")
        sizePolicy2.setHeightForWidth(self.securitySpin.sizePolicy().hasHeightForWidth())
        self.securitySpin.setSizePolicy(sizePolicy2)
        self.securitySpin.setMinimum(-2147483648)
        self.securitySpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(6, QFormLayout.FieldRole, self.securitySpin)

        self.label_24 = QLabel(self.groupBox_6)
        self.label_24.setObjectName("label_24")
        sizePolicy2.setHeightForWidth(self.label_24.sizePolicy().hasHeightForWidth())
        self.label_24.setSizePolicy(sizePolicy2)

        self.formLayout_4.setWidget(7, QFormLayout.LabelRole, self.label_24)

        self.treatInjurySpin = QSpinBox(self.groupBox_6)
        self.treatInjurySpin.setObjectName("treatInjurySpin")
        sizePolicy2.setHeightForWidth(self.treatInjurySpin.sizePolicy().hasHeightForWidth())
        self.treatInjurySpin.setSizePolicy(sizePolicy2)
        self.treatInjurySpin.setMinimum(-2147483648)
        self.treatInjurySpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(7, QFormLayout.FieldRole, self.treatInjurySpin)


        self.verticalLayout_5.addWidget(self.groupBox_6)

        self.groupBox_8 = QGroupBox(self.statsTab)
        self.groupBox_8.setObjectName("groupBox_8")
        self.formLayout_6 = QFormLayout(self.groupBox_8)
        self.formLayout_6.setObjectName("formLayout_6")
        self.label_31 = QLabel(self.groupBox_8)
        self.label_31.setObjectName("label_31")
        sizePolicy2.setHeightForWidth(self.label_31.sizePolicy().hasHeightForWidth())
        self.label_31.setSizePolicy(sizePolicy2)

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_31)

        self.fortitudeSpin = QSpinBox(self.groupBox_8)
        self.fortitudeSpin.setObjectName("fortitudeSpin")
        sizePolicy2.setHeightForWidth(self.fortitudeSpin.sizePolicy().hasHeightForWidth())
        self.fortitudeSpin.setSizePolicy(sizePolicy2)
        self.fortitudeSpin.setMinimum(-2147483648)
        self.fortitudeSpin.setMaximum(2147483647)

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.fortitudeSpin)

        self.label_32 = QLabel(self.groupBox_8)
        self.label_32.setObjectName("label_32")
        sizePolicy2.setHeightForWidth(self.label_32.sizePolicy().hasHeightForWidth())
        self.label_32.setSizePolicy(sizePolicy2)

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.label_32)

        self.label_33 = QLabel(self.groupBox_8)
        self.label_33.setObjectName("label_33")
        sizePolicy2.setHeightForWidth(self.label_33.sizePolicy().hasHeightForWidth())
        self.label_33.setSizePolicy(sizePolicy2)

        self.formLayout_6.setWidget(2, QFormLayout.LabelRole, self.label_33)

        self.reflexSpin = QSpinBox(self.groupBox_8)
        self.reflexSpin.setObjectName("reflexSpin")
        sizePolicy2.setHeightForWidth(self.reflexSpin.sizePolicy().hasHeightForWidth())
        self.reflexSpin.setSizePolicy(sizePolicy2)
        self.reflexSpin.setMinimum(-2147483648)
        self.reflexSpin.setMaximum(2147483647)

        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.reflexSpin)

        self.willSpin = QSpinBox(self.groupBox_8)
        self.willSpin.setObjectName("willSpin")
        sizePolicy2.setHeightForWidth(self.willSpin.sizePolicy().hasHeightForWidth())
        self.willSpin.setSizePolicy(sizePolicy2)
        self.willSpin.setMinimum(-2147483648)
        self.willSpin.setMaximum(2147483647)

        self.formLayout_6.setWidget(2, QFormLayout.FieldRole, self.willSpin)


        self.verticalLayout_5.addWidget(self.groupBox_8)

        self.groupBox_9 = QGroupBox(self.statsTab)
        self.groupBox_9.setObjectName("groupBox_9")
        self.formLayout_7 = QFormLayout(self.groupBox_9)
        self.formLayout_7.setObjectName("formLayout_7")
        self.label_34 = QLabel(self.groupBox_9)
        self.label_34.setObjectName("label_34")
        sizePolicy2.setHeightForWidth(self.label_34.sizePolicy().hasHeightForWidth())
        self.label_34.setSizePolicy(sizePolicy2)

        self.formLayout_7.setWidget(0, QFormLayout.LabelRole, self.label_34)

        self.armorClassSpin = QSpinBox(self.groupBox_9)
        self.armorClassSpin.setObjectName("armorClassSpin")
        sizePolicy2.setHeightForWidth(self.armorClassSpin.sizePolicy().hasHeightForWidth())
        self.armorClassSpin.setSizePolicy(sizePolicy2)
        self.armorClassSpin.setMinimum(-2147483648)
        self.armorClassSpin.setMaximum(2147483647)

        self.formLayout_7.setWidget(0, QFormLayout.FieldRole, self.armorClassSpin)


        self.verticalLayout_5.addWidget(self.groupBox_9)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)


        self.horizontalLayout_11.addLayout(self.verticalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.groupBox_7 = QGroupBox(self.statsTab)
        self.groupBox_7.setObjectName("groupBox_7")
        sizePolicy.setHeightForWidth(self.groupBox_7.sizePolicy().hasHeightForWidth())
        self.groupBox_7.setSizePolicy(sizePolicy)
        self.formLayout_5 = QFormLayout(self.groupBox_7)
        self.formLayout_5.setObjectName("formLayout_5")
        self.label_25 = QLabel(self.groupBox_7)
        self.label_25.setObjectName("label_25")
        sizePolicy2.setHeightForWidth(self.label_25.sizePolicy().hasHeightForWidth())
        self.label_25.setSizePolicy(sizePolicy2)

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_25)

        self.strengthSpin = QSpinBox(self.groupBox_7)
        self.strengthSpin.setObjectName("strengthSpin")
        sizePolicy2.setHeightForWidth(self.strengthSpin.sizePolicy().hasHeightForWidth())
        self.strengthSpin.setSizePolicy(sizePolicy2)
        self.strengthSpin.setMinimum(-2147483648)
        self.strengthSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.strengthSpin)

        self.label_26 = QLabel(self.groupBox_7)
        self.label_26.setObjectName("label_26")
        sizePolicy2.setHeightForWidth(self.label_26.sizePolicy().hasHeightForWidth())
        self.label_26.setSizePolicy(sizePolicy2)

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_26)

        self.dexteritySpin = QSpinBox(self.groupBox_7)
        self.dexteritySpin.setObjectName("dexteritySpin")
        sizePolicy2.setHeightForWidth(self.dexteritySpin.sizePolicy().hasHeightForWidth())
        self.dexteritySpin.setSizePolicy(sizePolicy2)
        self.dexteritySpin.setMinimum(-2147483648)
        self.dexteritySpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.dexteritySpin)

        self.label_27 = QLabel(self.groupBox_7)
        self.label_27.setObjectName("label_27")
        sizePolicy2.setHeightForWidth(self.label_27.sizePolicy().hasHeightForWidth())
        self.label_27.setSizePolicy(sizePolicy2)

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_27)

        self.constitutionSpin = QSpinBox(self.groupBox_7)
        self.constitutionSpin.setObjectName("constitutionSpin")
        sizePolicy2.setHeightForWidth(self.constitutionSpin.sizePolicy().hasHeightForWidth())
        self.constitutionSpin.setSizePolicy(sizePolicy2)
        self.constitutionSpin.setMinimum(-2147483648)
        self.constitutionSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.constitutionSpin)

        self.label_28 = QLabel(self.groupBox_7)
        self.label_28.setObjectName("label_28")
        sizePolicy2.setHeightForWidth(self.label_28.sizePolicy().hasHeightForWidth())
        self.label_28.setSizePolicy(sizePolicy2)

        self.formLayout_5.setWidget(3, QFormLayout.LabelRole, self.label_28)

        self.intelligenceSpin = QSpinBox(self.groupBox_7)
        self.intelligenceSpin.setObjectName("intelligenceSpin")
        sizePolicy2.setHeightForWidth(self.intelligenceSpin.sizePolicy().hasHeightForWidth())
        self.intelligenceSpin.setSizePolicy(sizePolicy2)
        self.intelligenceSpin.setMinimum(-2147483648)
        self.intelligenceSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(3, QFormLayout.FieldRole, self.intelligenceSpin)

        self.label_29 = QLabel(self.groupBox_7)
        self.label_29.setObjectName("label_29")
        sizePolicy2.setHeightForWidth(self.label_29.sizePolicy().hasHeightForWidth())
        self.label_29.setSizePolicy(sizePolicy2)

        self.formLayout_5.setWidget(4, QFormLayout.LabelRole, self.label_29)

        self.wisdomSpin = QSpinBox(self.groupBox_7)
        self.wisdomSpin.setObjectName("wisdomSpin")
        sizePolicy2.setHeightForWidth(self.wisdomSpin.sizePolicy().hasHeightForWidth())
        self.wisdomSpin.setSizePolicy(sizePolicy2)
        self.wisdomSpin.setMinimum(-2147483648)
        self.wisdomSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(4, QFormLayout.FieldRole, self.wisdomSpin)

        self.label_30 = QLabel(self.groupBox_7)
        self.label_30.setObjectName("label_30")
        sizePolicy2.setHeightForWidth(self.label_30.sizePolicy().hasHeightForWidth())
        self.label_30.setSizePolicy(sizePolicy2)

        self.formLayout_5.setWidget(5, QFormLayout.LabelRole, self.label_30)

        self.charismaSpin = QSpinBox(self.groupBox_7)
        self.charismaSpin.setObjectName("charismaSpin")
        sizePolicy2.setHeightForWidth(self.charismaSpin.sizePolicy().hasHeightForWidth())
        self.charismaSpin.setSizePolicy(sizePolicy2)
        self.charismaSpin.setMinimum(-2147483648)
        self.charismaSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(5, QFormLayout.FieldRole, self.charismaSpin)


        self.verticalLayout_6.addWidget(self.groupBox_7)

        self.groupBox_10 = QGroupBox(self.statsTab)
        self.groupBox_10.setObjectName("groupBox_10")
        self.formLayout_8 = QFormLayout(self.groupBox_10)
        self.formLayout_8.setObjectName("formLayout_8")
        self.label_35 = QLabel(self.groupBox_10)
        self.label_35.setObjectName("label_35")
        sizePolicy2.setHeightForWidth(self.label_35.sizePolicy().hasHeightForWidth())
        self.label_35.setSizePolicy(sizePolicy2)

        self.formLayout_8.setWidget(0, QFormLayout.LabelRole, self.label_35)

        self.label_36 = QLabel(self.groupBox_10)
        self.label_36.setObjectName("label_36")
        sizePolicy2.setHeightForWidth(self.label_36.sizePolicy().hasHeightForWidth())
        self.label_36.setSizePolicy(sizePolicy2)

        self.formLayout_8.setWidget(1, QFormLayout.LabelRole, self.label_36)

        self.label_37 = QLabel(self.groupBox_10)
        self.label_37.setObjectName("label_37")
        sizePolicy2.setHeightForWidth(self.label_37.sizePolicy().hasHeightForWidth())
        self.label_37.setSizePolicy(sizePolicy2)

        self.formLayout_8.setWidget(2, QFormLayout.LabelRole, self.label_37)

        self.baseHpSpin = QSpinBox(self.groupBox_10)
        self.baseHpSpin.setObjectName("baseHpSpin")
        sizePolicy2.setHeightForWidth(self.baseHpSpin.sizePolicy().hasHeightForWidth())
        self.baseHpSpin.setSizePolicy(sizePolicy2)
        self.baseHpSpin.setMinimum(-2147483648)
        self.baseHpSpin.setMaximum(2147483647)

        self.formLayout_8.setWidget(0, QFormLayout.FieldRole, self.baseHpSpin)

        self.currentHpSpin = QSpinBox(self.groupBox_10)
        self.currentHpSpin.setObjectName("currentHpSpin")
        sizePolicy2.setHeightForWidth(self.currentHpSpin.sizePolicy().hasHeightForWidth())
        self.currentHpSpin.setSizePolicy(sizePolicy2)
        self.currentHpSpin.setMinimum(-2147483648)
        self.currentHpSpin.setMaximum(2147483647)

        self.formLayout_8.setWidget(1, QFormLayout.FieldRole, self.currentHpSpin)

        self.maxHpSpin = QSpinBox(self.groupBox_10)
        self.maxHpSpin.setObjectName("maxHpSpin")
        sizePolicy2.setHeightForWidth(self.maxHpSpin.sizePolicy().hasHeightForWidth())
        self.maxHpSpin.setSizePolicy(sizePolicy2)
        self.maxHpSpin.setMinimum(-2147483648)
        self.maxHpSpin.setMaximum(2147483647)

        self.formLayout_8.setWidget(2, QFormLayout.FieldRole, self.maxHpSpin)


        self.verticalLayout_6.addWidget(self.groupBox_10)

        self.groupBox_11 = QGroupBox(self.statsTab)
        self.groupBox_11.setObjectName("groupBox_11")
        self.formLayout_9 = QFormLayout(self.groupBox_11)
        self.formLayout_9.setObjectName("formLayout_9")
        self.label_39 = QLabel(self.groupBox_11)
        self.label_39.setObjectName("label_39")
        sizePolicy2.setHeightForWidth(self.label_39.sizePolicy().hasHeightForWidth())
        self.label_39.setSizePolicy(sizePolicy2)

        self.formLayout_9.setWidget(0, QFormLayout.LabelRole, self.label_39)

        self.currentFpSpin = QSpinBox(self.groupBox_11)
        self.currentFpSpin.setObjectName("currentFpSpin")
        sizePolicy2.setHeightForWidth(self.currentFpSpin.sizePolicy().hasHeightForWidth())
        self.currentFpSpin.setSizePolicy(sizePolicy2)
        self.currentFpSpin.setMinimum(-2147483648)
        self.currentFpSpin.setMaximum(2147483647)

        self.formLayout_9.setWidget(0, QFormLayout.FieldRole, self.currentFpSpin)

        self.label_40 = QLabel(self.groupBox_11)
        self.label_40.setObjectName("label_40")
        sizePolicy2.setHeightForWidth(self.label_40.sizePolicy().hasHeightForWidth())
        self.label_40.setSizePolicy(sizePolicy2)

        self.formLayout_9.setWidget(1, QFormLayout.LabelRole, self.label_40)

        self.maxFpSpin = QSpinBox(self.groupBox_11)
        self.maxFpSpin.setObjectName("maxFpSpin")
        sizePolicy2.setHeightForWidth(self.maxFpSpin.sizePolicy().hasHeightForWidth())
        self.maxFpSpin.setSizePolicy(sizePolicy2)
        self.maxFpSpin.setMinimum(-2147483648)
        self.maxFpSpin.setMaximum(2147483647)

        self.formLayout_9.setWidget(1, QFormLayout.FieldRole, self.maxFpSpin)


        self.verticalLayout_6.addWidget(self.groupBox_11)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_2)


        self.horizontalLayout_11.addLayout(self.verticalLayout_6)

        self.tabWidget.addTab(self.statsTab, "")
        self.classesTab = QWidget()
        self.classesTab.setObjectName("classesTab")
        self.verticalLayout_7 = QVBoxLayout(self.classesTab)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.groupBox_13 = QGroupBox(self.classesTab)
        self.groupBox_13.setObjectName("groupBox_13")
        self.gridLayout_3 = QGridLayout(self.groupBox_13)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.class1Select = ComboBox2DA(self.groupBox_13)
        self.class1Select.setObjectName("class1Select")
        sizePolicy2.setHeightForWidth(self.class1Select.sizePolicy().hasHeightForWidth())
        self.class1Select.setSizePolicy(sizePolicy2)

        self.horizontalLayout_13.addWidget(self.class1Select)

        self.class1LevelSpin = QSpinBox(self.groupBox_13)
        self.class1LevelSpin.setObjectName("class1LevelSpin")
        sizePolicy2.setHeightForWidth(self.class1LevelSpin.sizePolicy().hasHeightForWidth())
        self.class1LevelSpin.setSizePolicy(sizePolicy2)
        self.class1LevelSpin.setMinimum(-2147483648)
        self.class1LevelSpin.setMaximum(2147483647)

        self.horizontalLayout_13.addWidget(self.class1LevelSpin)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_8)

        self.horizontalLayout_13.setStretch(0, 3)
        self.horizontalLayout_13.setStretch(1, 1)
        self.horizontalLayout_13.setStretch(2, 2)

        self.gridLayout_3.addLayout(self.horizontalLayout_13, 0, 0, 1, 1)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.class2Select = ComboBox2DA(self.groupBox_13)
        self.class2Select.setObjectName("class2Select")
        sizePolicy2.setHeightForWidth(self.class2Select.sizePolicy().hasHeightForWidth())
        self.class2Select.setSizePolicy(sizePolicy2)

        self.horizontalLayout_14.addWidget(self.class2Select)

        self.class2LevelSpin = QSpinBox(self.groupBox_13)
        self.class2LevelSpin.setObjectName("class2LevelSpin")
        sizePolicy2.setHeightForWidth(self.class2LevelSpin.sizePolicy().hasHeightForWidth())
        self.class2LevelSpin.setSizePolicy(sizePolicy2)
        self.class2LevelSpin.setMinimum(-2147483648)
        self.class2LevelSpin.setMaximum(2147483647)

        self.horizontalLayout_14.addWidget(self.class2LevelSpin)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_9)

        self.horizontalLayout_14.setStretch(0, 3)
        self.horizontalLayout_14.setStretch(1, 1)
        self.horizontalLayout_14.setStretch(2, 2)

        self.gridLayout_3.addLayout(self.horizontalLayout_14, 1, 0, 1, 1)


        self.verticalLayout_7.addWidget(self.groupBox_13)

        self.groupBox_12 = QGroupBox(self.classesTab)
        self.groupBox_12.setObjectName("groupBox_12")
        self.horizontalLayout_12 = QHBoxLayout(self.groupBox_12)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.label_52 = QLabel(self.groupBox_12)
        self.label_52.setObjectName("label_52")

        self.horizontalLayout_12.addWidget(self.label_52)

        self.alignmentSlider = QSlider(self.groupBox_12)
        self.alignmentSlider.setObjectName("alignmentSlider")
        self.alignmentSlider.setMaximum(100)
        self.alignmentSlider.setValue(50)
        self.alignmentSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_12.addWidget(self.alignmentSlider)

        self.label_53 = QLabel(self.groupBox_12)
        self.label_53.setObjectName("label_53")

        self.horizontalLayout_12.addWidget(self.label_53)


        self.verticalLayout_7.addWidget(self.groupBox_12)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.spacer)

        self.tabWidget.addTab(self.classesTab, "")
        self.featsTab = QWidget()
        self.featsTab.setObjectName("featsTab")
        self.verticalLayout_8 = QVBoxLayout(self.featsTab)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.featList = QListWidget(self.featsTab)
        self.featList.setObjectName("featList")

        self.verticalLayout_8.addWidget(self.featList)

        self.groupBox_14 = QGroupBox(self.featsTab)
        self.groupBox_14.setObjectName("groupBox_14")
        self.gridLayout_4 = QGridLayout(self.groupBox_14)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.featSummaryEdit = QPlainTextEdit(self.groupBox_14)
        self.featSummaryEdit.setObjectName("featSummaryEdit")
        self.featSummaryEdit.setReadOnly(True)

        self.gridLayout_4.addWidget(self.featSummaryEdit, 0, 0, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_14)

        self.verticalLayout_8.setStretch(0, 2)
        self.verticalLayout_8.setStretch(1, 1)
        self.tabWidget.addTab(self.featsTab, "")
        self.powersTab = QWidget()
        self.powersTab.setObjectName("powersTab")
        self.verticalLayout_17 = QVBoxLayout(self.powersTab)
        self.verticalLayout_17.setObjectName("verticalLayout_17")
        self.powerList = QListWidget(self.powersTab)
        self.powerList.setObjectName("powerList")

        self.verticalLayout_17.addWidget(self.powerList)

        self.groupBox_29 = QGroupBox(self.powersTab)
        self.groupBox_29.setObjectName("groupBox_29")
        self.gridLayout_8 = QGridLayout(self.groupBox_29)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.powerSummaryEdit = QPlainTextEdit(self.groupBox_29)
        self.powerSummaryEdit.setObjectName("powerSummaryEdit")
        self.powerSummaryEdit.setReadOnly(True)

        self.gridLayout_8.addWidget(self.powerSummaryEdit, 0, 0, 1, 1)


        self.verticalLayout_17.addWidget(self.groupBox_29)

        self.verticalLayout_17.setStretch(0, 2)
        self.verticalLayout_17.setStretch(1, 1)
        self.tabWidget.addTab(self.powersTab, "")
        self.Scripts = QWidget()
        self.Scripts.setObjectName("Scripts")
        self.formLayout_22 = QFormLayout(self.Scripts)
        self.formLayout_22.setObjectName("formLayout_22")
        self.label_95 = QLabel(self.Scripts)
        self.label_95.setObjectName("label_95")
        sizePolicy3.setHeightForWidth(self.label_95.sizePolicy().hasHeightForWidth())
        self.label_95.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(0, QFormLayout.LabelRole, self.label_95)

        self.horizontalLayout_29 = QHBoxLayout()
        self.horizontalLayout_29.setObjectName("horizontalLayout_29")
        self.onBlockedEdit = FilterComboBox(self.Scripts)
        self.onBlockedEdit.setObjectName("onBlockedEdit")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.onBlockedEdit.sizePolicy().hasHeightForWidth())
        self.onBlockedEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_29.addWidget(self.onBlockedEdit)


        self.formLayout_22.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_29)

        self.label_106 = QLabel(self.Scripts)
        self.label_106.setObjectName("label_106")
        sizePolicy3.setHeightForWidth(self.label_106.sizePolicy().hasHeightForWidth())
        self.label_106.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(1, QFormLayout.LabelRole, self.label_106)

        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setObjectName("horizontalLayout_30")
        self.onAttackedEdit = FilterComboBox(self.Scripts)
        self.onAttackedEdit.setObjectName("onAttackedEdit")
        sizePolicy5.setHeightForWidth(self.onAttackedEdit.sizePolicy().hasHeightForWidth())
        self.onAttackedEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_30.addWidget(self.onAttackedEdit)


        self.formLayout_22.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_30)

        self.label_96 = QLabel(self.Scripts)
        self.label_96.setObjectName("label_96")
        sizePolicy3.setHeightForWidth(self.label_96.sizePolicy().hasHeightForWidth())
        self.label_96.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(2, QFormLayout.LabelRole, self.label_96)

        self.horizontalLayout_31 = QHBoxLayout()
        self.horizontalLayout_31.setObjectName("horizontalLayout_31")
        self.onNoticeEdit = FilterComboBox(self.Scripts)
        self.onNoticeEdit.setObjectName("onNoticeEdit")
        sizePolicy5.setHeightForWidth(self.onNoticeEdit.sizePolicy().hasHeightForWidth())
        self.onNoticeEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_31.addWidget(self.onNoticeEdit)


        self.formLayout_22.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_31)

        self.label_97 = QLabel(self.Scripts)
        self.label_97.setObjectName("label_97")
        sizePolicy3.setHeightForWidth(self.label_97.sizePolicy().hasHeightForWidth())
        self.label_97.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(3, QFormLayout.LabelRole, self.label_97)

        self.horizontalLayout_32 = QHBoxLayout()
        self.horizontalLayout_32.setObjectName("horizontalLayout_32")
        self.onConversationEdit = FilterComboBox(self.Scripts)
        self.onConversationEdit.setObjectName("onConversationEdit")
        sizePolicy5.setHeightForWidth(self.onConversationEdit.sizePolicy().hasHeightForWidth())
        self.onConversationEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_32.addWidget(self.onConversationEdit)


        self.formLayout_22.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_32)

        self.label_98 = QLabel(self.Scripts)
        self.label_98.setObjectName("label_98")
        sizePolicy3.setHeightForWidth(self.label_98.sizePolicy().hasHeightForWidth())
        self.label_98.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(4, QFormLayout.LabelRole, self.label_98)

        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setObjectName("horizontalLayout_33")
        self.onDamagedEdit = FilterComboBox(self.Scripts)
        self.onDamagedEdit.setObjectName("onDamagedEdit")
        sizePolicy5.setHeightForWidth(self.onDamagedEdit.sizePolicy().hasHeightForWidth())
        self.onDamagedEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_33.addWidget(self.onDamagedEdit)


        self.formLayout_22.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_33)

        self.label_109 = QLabel(self.Scripts)
        self.label_109.setObjectName("label_109")
        sizePolicy3.setHeightForWidth(self.label_109.sizePolicy().hasHeightForWidth())
        self.label_109.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(5, QFormLayout.LabelRole, self.label_109)

        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setObjectName("horizontalLayout_34")
        self.onDeathEdit = FilterComboBox(self.Scripts)
        self.onDeathEdit.setObjectName("onDeathEdit")
        sizePolicy5.setHeightForWidth(self.onDeathEdit.sizePolicy().hasHeightForWidth())
        self.onDeathEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_34.addWidget(self.onDeathEdit)


        self.formLayout_22.setLayout(5, QFormLayout.FieldRole, self.horizontalLayout_34)

        self.label_107 = QLabel(self.Scripts)
        self.label_107.setObjectName("label_107")
        sizePolicy3.setHeightForWidth(self.label_107.sizePolicy().hasHeightForWidth())
        self.label_107.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(6, QFormLayout.LabelRole, self.label_107)

        self.horizontalLayout_35 = QHBoxLayout()
        self.horizontalLayout_35.setObjectName("horizontalLayout_35")
        self.onEndRoundEdit = FilterComboBox(self.Scripts)
        self.onEndRoundEdit.setObjectName("onEndRoundEdit")
        sizePolicy5.setHeightForWidth(self.onEndRoundEdit.sizePolicy().hasHeightForWidth())
        self.onEndRoundEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_35.addWidget(self.onEndRoundEdit)


        self.formLayout_22.setLayout(6, QFormLayout.FieldRole, self.horizontalLayout_35)

        self.label_108 = QLabel(self.Scripts)
        self.label_108.setObjectName("label_108")
        sizePolicy3.setHeightForWidth(self.label_108.sizePolicy().hasHeightForWidth())
        self.label_108.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(7, QFormLayout.LabelRole, self.label_108)

        self.horizontalLayout_36 = QHBoxLayout()
        self.horizontalLayout_36.setObjectName("horizontalLayout_36")
        self.onEndConversationEdit = FilterComboBox(self.Scripts)
        self.onEndConversationEdit.setObjectName("onEndConversationEdit")
        sizePolicy5.setHeightForWidth(self.onEndConversationEdit.sizePolicy().hasHeightForWidth())
        self.onEndConversationEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_36.addWidget(self.onEndConversationEdit)


        self.formLayout_22.setLayout(7, QFormLayout.FieldRole, self.horizontalLayout_36)

        self.label_100 = QLabel(self.Scripts)
        self.label_100.setObjectName("label_100")
        sizePolicy3.setHeightForWidth(self.label_100.sizePolicy().hasHeightForWidth())
        self.label_100.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(8, QFormLayout.LabelRole, self.label_100)

        self.horizontalLayout_38 = QHBoxLayout()
        self.horizontalLayout_38.setObjectName("horizontalLayout_38")
        self.onDisturbedEdit = FilterComboBox(self.Scripts)
        self.onDisturbedEdit.setObjectName("onDisturbedEdit")
        sizePolicy5.setHeightForWidth(self.onDisturbedEdit.sizePolicy().hasHeightForWidth())
        self.onDisturbedEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_38.addWidget(self.onDisturbedEdit)


        self.formLayout_22.setLayout(8, QFormLayout.FieldRole, self.horizontalLayout_38)

        self.label_101 = QLabel(self.Scripts)
        self.label_101.setObjectName("label_101")
        sizePolicy3.setHeightForWidth(self.label_101.sizePolicy().hasHeightForWidth())
        self.label_101.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(9, QFormLayout.LabelRole, self.label_101)

        self.horizontalLayout_39 = QHBoxLayout()
        self.horizontalLayout_39.setObjectName("horizontalLayout_39")
        self.onHeartbeatSelect = FilterComboBox(self.Scripts)
        self.onHeartbeatSelect.setObjectName("onHeartbeatSelect")
        sizePolicy5.setHeightForWidth(self.onHeartbeatSelect.sizePolicy().hasHeightForWidth())
        self.onHeartbeatSelect.setSizePolicy(sizePolicy5)

        self.horizontalLayout_39.addWidget(self.onHeartbeatSelect)


        self.formLayout_22.setLayout(9, QFormLayout.FieldRole, self.horizontalLayout_39)

        self.label_103 = QLabel(self.Scripts)
        self.label_103.setObjectName("label_103")
        sizePolicy3.setHeightForWidth(self.label_103.sizePolicy().hasHeightForWidth())
        self.label_103.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(10, QFormLayout.LabelRole, self.label_103)

        self.horizontalLayout_41 = QHBoxLayout()
        self.horizontalLayout_41.setObjectName("horizontalLayout_41")
        self.onSpawnEdit = FilterComboBox(self.Scripts)
        self.onSpawnEdit.setObjectName("onSpawnEdit")
        sizePolicy5.setHeightForWidth(self.onSpawnEdit.sizePolicy().hasHeightForWidth())
        self.onSpawnEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_41.addWidget(self.onSpawnEdit)


        self.formLayout_22.setLayout(10, QFormLayout.FieldRole, self.horizontalLayout_41)

        self.label_104 = QLabel(self.Scripts)
        self.label_104.setObjectName("label_104")
        sizePolicy3.setHeightForWidth(self.label_104.sizePolicy().hasHeightForWidth())
        self.label_104.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(11, QFormLayout.LabelRole, self.label_104)

        self.horizontalLayout_42 = QHBoxLayout()
        self.horizontalLayout_42.setObjectName("horizontalLayout_42")
        self.onSpellCastEdit = FilterComboBox(self.Scripts)
        self.onSpellCastEdit.setObjectName("onSpellCastEdit")
        sizePolicy5.setHeightForWidth(self.onSpellCastEdit.sizePolicy().hasHeightForWidth())
        self.onSpellCastEdit.setSizePolicy(sizePolicy5)

        self.horizontalLayout_42.addWidget(self.onSpellCastEdit)


        self.formLayout_22.setLayout(11, QFormLayout.FieldRole, self.horizontalLayout_42)

        self.label_105 = QLabel(self.Scripts)
        self.label_105.setObjectName("label_105")
        sizePolicy3.setHeightForWidth(self.label_105.sizePolicy().hasHeightForWidth())
        self.label_105.setSizePolicy(sizePolicy3)

        self.formLayout_22.setWidget(12, QFormLayout.LabelRole, self.label_105)

        self.horizontalLayout_43 = QHBoxLayout()
        self.horizontalLayout_43.setObjectName("horizontalLayout_43")
        self.onUserDefinedSelect = FilterComboBox(self.Scripts)
        self.onUserDefinedSelect.setObjectName("onUserDefinedSelect")
        sizePolicy5.setHeightForWidth(self.onUserDefinedSelect.sizePolicy().hasHeightForWidth())
        self.onUserDefinedSelect.setSizePolicy(sizePolicy5)

        self.horizontalLayout_43.addWidget(self.onUserDefinedSelect)


        self.formLayout_22.setLayout(12, QFormLayout.FieldRole, self.horizontalLayout_43)

        self.tabWidget.addTab(self.Scripts, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName("commentsTab")
        self.gridLayout_9 = QGridLayout(self.commentsTab)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.comments = QPlainTextEdit(self.commentsTab)
        self.comments.setObjectName("comments")

        self.gridLayout_9.addWidget(self.comments, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.horizontalLayout_15.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1007, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuTools.addAction(self.actionSaveUnusedFields)
        self.menuTools.addAction(self.actionAlwaysSaveK2Fields)
        self.menuView.addAction(self.actionShowPreview)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionSaveUnusedFields.setText(QCoreApplication.translate("MainWindow", "Save Unused Fields", None))
        self.actionAlwaysSaveK2Fields.setText(QCoreApplication.translate("MainWindow", "Always Save K2 Fields", None))
        self.actionShowPreview.setText(QCoreApplication.translate("MainWindow", "Show Preview", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", "Profile", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "First Name:", None))
        self.firstnameRandomButton.setText(QCoreApplication.translate("MainWindow", "?", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Last Name:", None))
        self.lastnameRandomButton.setText(QCoreApplication.translate("MainWindow", "?", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", "Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", "-", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", "ResRef:", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", "Appearance:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", "Soundset:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", "Conversation:", None))
        self.conversationModifyButton.setText(QCoreApplication.translate("MainWindow", "Edit", None))
        self.groupBox_15.setTitle(QCoreApplication.translate("MainWindow", "Inventory", None))
        self.inventoryCountLabel.setText(QCoreApplication.translate("MainWindow", "Total Items:", None))
        self.inventoryButton.setText(QCoreApplication.translate("MainWindow", "Edit Inventory", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", "Portrait", None))
        self.portraitPicture.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", "Basic", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", "Flags", None))
        self.disarmableCheckbox.setText(QCoreApplication.translate("MainWindow", "Disarmable", None))
        self.noPermDeathCheckbox.setText(QCoreApplication.translate("MainWindow", "No Perm Death", None))
        self.min1HpCheckbox.setText(QCoreApplication.translate("MainWindow", "Min 1 HP", None))
        self.plotCheckbox.setText(QCoreApplication.translate("MainWindow", "Plot", None))
        self.isPcCheckbox.setText(QCoreApplication.translate("MainWindow", "Is PC", None))
        self.noReorientateCheckbox.setText(QCoreApplication.translate("MainWindow", "Doesn't Reorientate on PC", None))
        self.noBlockCheckbox.setText(QCoreApplication.translate("MainWindow", "Doesn't Block PC", None))
        self.hologramCheckbox.setText(QCoreApplication.translate("MainWindow", "Hologram", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", "Race", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", "Race:", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", "Subrace:", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", "Other", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", "Speed:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", "Faction:", None))
        self.genderAdvancedLabel.setText(QCoreApplication.translate("MainWindow", "Gender:", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", "Perception:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", "Challenge Rating:", None))
        self.label_102.setText(QCoreApplication.translate("MainWindow", "Blindspot:", None))
        self.label_110.setText(QCoreApplication.translate("MainWindow", "Multiplier Set:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.advancedTab), QCoreApplication.translate("MainWindow", "Advanced", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", "Skills", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", "Computer Use:", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", "Demolitions:", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", "Stealth:", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", "Awareness:", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", "Persuade:", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", "Repair:", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", "Security:", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", "Treat Injury:", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", "Saves", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", "Fortitude:", None))
        self.label_32.setText(QCoreApplication.translate("MainWindow", "Reflex:", None))
        self.label_33.setText(QCoreApplication.translate("MainWindow", "Will:", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("MainWindow", "Armor Class", None))
        self.label_34.setText(QCoreApplication.translate("MainWindow", "Armor Class:", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("MainWindow", "Attributes", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", "Strength:", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", "Dexterity:", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", "Constitution:", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", "Intelligence:", None))
        self.label_29.setText(QCoreApplication.translate("MainWindow", "Wisdom:", None))
        self.label_30.setText(QCoreApplication.translate("MainWindow", "Charisma:", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("MainWindow", "Hit Points", None))
        self.label_35.setText(QCoreApplication.translate("MainWindow", "Base HP:", None))
        self.label_36.setText(QCoreApplication.translate("MainWindow", "Current HP:", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", "Max HP:", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("MainWindow", "Force Points", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", "Current FP:", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", "Max FP:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.statsTab), QCoreApplication.translate("MainWindow", "Stats", None))
        self.groupBox_13.setTitle(QCoreApplication.translate("MainWindow", "Classes", None))
        self.groupBox_12.setTitle(QCoreApplication.translate("MainWindow", "Alignment", None))
        self.label_52.setText(QCoreApplication.translate("MainWindow", "Dark", None))
        self.label_53.setText(QCoreApplication.translate("MainWindow", "Light", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.classesTab), QCoreApplication.translate("MainWindow", "Classes", None))
        self.groupBox_14.setTitle(QCoreApplication.translate("MainWindow", "Feat Summary", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.featsTab), QCoreApplication.translate("MainWindow", "Feats", None))
        self.groupBox_29.setTitle(QCoreApplication.translate("MainWindow", "Force Power Summary", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.powersTab), QCoreApplication.translate("MainWindow", "Powers", None))
        self.label_95.setText(QCoreApplication.translate("MainWindow", "OnBlocked:", None))
        self.label_106.setText(QCoreApplication.translate("MainWindow", "OnAttacked:", None))
        self.label_96.setText(QCoreApplication.translate("MainWindow", "OnNoticed:", None))
        self.label_97.setText(QCoreApplication.translate("MainWindow", "OnConversation:", None))
        self.label_98.setText(QCoreApplication.translate("MainWindow", "OnDamaged:", None))
        self.label_109.setText(QCoreApplication.translate("MainWindow", "OnDeath:", None))
        self.label_107.setText(QCoreApplication.translate("MainWindow", "OnEndRound:", None))
        self.label_108.setText(QCoreApplication.translate("MainWindow", "OnEndConversation:", None))
        self.label_100.setText(QCoreApplication.translate("MainWindow", "OnDisturbed:", None))
        self.label_101.setText(QCoreApplication.translate("MainWindow", "OnHeartbeat:", None))
        self.label_103.setText(QCoreApplication.translate("MainWindow", "OnSpawn:", None))
        self.label_104.setText(QCoreApplication.translate("MainWindow", "OnSpellCastAt:", None))
        self.label_105.setText(QCoreApplication.translate("MainWindow", "OnUserDefined:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Scripts), QCoreApplication.translate("MainWindow", "Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", "Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", "Tools", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", "View", None))
    # retranslateUi

