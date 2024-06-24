# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'utc.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMenuBar, QPlainTextEdit,
    QPushButton, QSizePolicy, QSlider, QSpacerItem,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from toolset.gui.common.widgets.combobox import FilterComboBox
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.renderer.model import ModelRenderer

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(794, 584)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionSaveUnusedFields = QAction(MainWindow)
        self.actionSaveUnusedFields.setObjectName(u"actionSaveUnusedFields")
        self.actionSaveUnusedFields.setCheckable(True)
        self.actionAlwaysSaveK2Fields = QAction(MainWindow)
        self.actionAlwaysSaveK2Fields.setObjectName(u"actionAlwaysSaveK2Fields")
        self.actionAlwaysSaveK2Fields.setCheckable(True)
        self.actionShowPreview = QAction(MainWindow)
        self.actionShowPreview.setObjectName(u"actionShowPreview")
        self.actionShowPreview.setCheckable(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_15 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.previewRenderer = ModelRenderer(self.centralwidget)
        self.previewRenderer.setObjectName(u"previewRenderer")
        self.previewRenderer.setMinimumSize(QSize(350, 0))
        self.previewRenderer.setMouseTracking(True)
        self.previewRenderer.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayout_15.addWidget(self.previewRenderer)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(self.tab)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.firstnameEdit = LocalizedStringLineEdit(self.groupBox)
        self.firstnameEdit.setObjectName(u"firstnameEdit")
        self.firstnameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout.addWidget(self.firstnameEdit)

        self.firstnameRandomButton = QPushButton(self.groupBox)
        self.firstnameRandomButton.setObjectName(u"firstnameRandomButton")
        self.firstnameRandomButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout.addWidget(self.firstnameRandomButton)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lastnameEdit = LocalizedStringLineEdit(self.groupBox)
        self.lastnameEdit.setObjectName(u"lastnameEdit")
        self.lastnameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_2.addWidget(self.lastnameEdit)

        self.lastnameRandomButton = QPushButton(self.groupBox)
        self.lastnameRandomButton.setObjectName(u"lastnameRandomButton")
        self.lastnameRandomButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_2.addWidget(self.lastnameRandomButton)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_2)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.tagEdit = QLineEdit(self.groupBox)
        self.tagEdit.setObjectName(u"tagEdit")

        self.horizontalLayout_3.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.groupBox)
        self.tagGenerateButton.setObjectName(u"tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_3.addWidget(self.tagGenerateButton)

        self.horizontalSpacer = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_3)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.resrefEdit = QLineEdit(self.groupBox)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_8.addWidget(self.resrefEdit)

        self.horizontalSpacer_3 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_3)

        self.horizontalSpacer_2 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_2)


        self.formLayout.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_8)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.appearanceSelect = ComboBox2DA(self.groupBox)
        self.appearanceSelect.setObjectName(u"appearanceSelect")

        self.horizontalLayout_4.addWidget(self.appearanceSelect)

        self.horizontalSpacer_4 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)

        self.horizontalSpacer_5 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)


        self.formLayout.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_4)

        self.label_10 = QLabel(self.groupBox)
        self.label_10.setObjectName(u"label_10")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_10)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.soundsetSelect = ComboBox2DA(self.groupBox)
        self.soundsetSelect.setObjectName(u"soundsetSelect")

        self.horizontalLayout_10.addWidget(self.soundsetSelect)

        self.horizontalSpacer_7 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_7)

        self.horizontalSpacer_6 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_6)


        self.formLayout.setLayout(5, QFormLayout.FieldRole, self.horizontalLayout_10)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_5)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.conversationEdit = FilterComboBox(self.groupBox)
        self.conversationEdit.setObjectName(u"conversationEdit")

        self.horizontalLayout_5.addWidget(self.conversationEdit)

        self.conversationModifyButton = QPushButton(self.groupBox)
        self.conversationModifyButton.setObjectName(u"conversationModifyButton")
        self.conversationModifyButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_5.addWidget(self.conversationModifyButton)

        self.horizontalSpacer_10 = QSpacerItem(32, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_10)


        self.formLayout.setLayout(6, QFormLayout.FieldRole, self.horizontalLayout_5)


        self.gridLayout_2.addLayout(self.formLayout, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_15 = QGroupBox(self.tab)
        self.groupBox_15.setObjectName(u"groupBox_15")
        self.verticalLayout_10 = QVBoxLayout(self.groupBox_15)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.inventoryCountLabel = QLabel(self.groupBox_15)
        self.inventoryCountLabel.setObjectName(u"inventoryCountLabel")

        self.verticalLayout_10.addWidget(self.inventoryCountLabel)

        self.inventoryButton = QPushButton(self.groupBox_15)
        self.inventoryButton.setObjectName(u"inventoryButton")

        self.verticalLayout_10.addWidget(self.inventoryButton)


        self.verticalLayout.addWidget(self.groupBox_15)

        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.horizontalLayout_7 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.portraitPicture = QLabel(self.groupBox_2)
        self.portraitPicture.setObjectName(u"portraitPicture")
        self.portraitPicture.setMinimumSize(QSize(64, 64))
        self.portraitPicture.setMaximumSize(QSize(64, 64))
        self.portraitPicture.setStyleSheet(u"background-color: black;")
        self.portraitPicture.setFrameShape(QFrame.Box)
        self.portraitPicture.setScaledContents(True)

        self.horizontalLayout_7.addWidget(self.portraitPicture)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.portraitSelect = ComboBox2DA(self.groupBox_2)
        self.portraitSelect.setObjectName(u"portraitSelect")

        self.horizontalLayout_6.addWidget(self.portraitSelect)


        self.horizontalLayout_7.addLayout(self.horizontalLayout_6)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_5)

        self.verticalLayout.setStretch(0, 1)
        self.tabWidget.addTab(self.tab, "")
        self.advancedTab = QWidget()
        self.advancedTab.setObjectName(u"advancedTab")
        self.verticalLayout_4 = QVBoxLayout(self.advancedTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox_3 = QGroupBox(self.advancedTab)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.horizontalLayout_9 = QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.disarmableCheckbox = QCheckBox(self.groupBox_3)
        self.disarmableCheckbox.setObjectName(u"disarmableCheckbox")

        self.verticalLayout_2.addWidget(self.disarmableCheckbox)

        self.noPermDeathCheckbox = QCheckBox(self.groupBox_3)
        self.noPermDeathCheckbox.setObjectName(u"noPermDeathCheckbox")

        self.verticalLayout_2.addWidget(self.noPermDeathCheckbox)

        self.min1HpCheckbox = QCheckBox(self.groupBox_3)
        self.min1HpCheckbox.setObjectName(u"min1HpCheckbox")

        self.verticalLayout_2.addWidget(self.min1HpCheckbox)

        self.plotCheckbox = QCheckBox(self.groupBox_3)
        self.plotCheckbox.setObjectName(u"plotCheckbox")

        self.verticalLayout_2.addWidget(self.plotCheckbox)

        self.isPcCheckbox = QCheckBox(self.groupBox_3)
        self.isPcCheckbox.setObjectName(u"isPcCheckbox")

        self.verticalLayout_2.addWidget(self.isPcCheckbox)


        self.horizontalLayout_9.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.noReorientateCheckbox = QCheckBox(self.groupBox_3)
        self.noReorientateCheckbox.setObjectName(u"noReorientateCheckbox")

        self.verticalLayout_3.addWidget(self.noReorientateCheckbox)

        self.noBlockCheckbox = QCheckBox(self.groupBox_3)
        self.noBlockCheckbox.setObjectName(u"noBlockCheckbox")

        self.verticalLayout_3.addWidget(self.noBlockCheckbox)

        self.hologramCheckbox = QCheckBox(self.groupBox_3)
        self.hologramCheckbox.setObjectName(u"hologramCheckbox")

        self.verticalLayout_3.addWidget(self.hologramCheckbox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)


        self.horizontalLayout_9.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(self.advancedTab)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.formLayout_2 = QFormLayout(self.groupBox_4)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_8 = QLabel(self.groupBox_4)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.raceSelect = ComboBox2DA(self.groupBox_4)
        self.raceSelect.setObjectName(u"raceSelect")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.raceSelect)

        self.label_9 = QLabel(self.groupBox_4)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_9)

        self.subraceSelect = ComboBox2DA(self.groupBox_4)
        self.subraceSelect.setObjectName(u"subraceSelect")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.subraceSelect)


        self.verticalLayout_4.addWidget(self.groupBox_4)

        self.groupBox_5 = QGroupBox(self.advancedTab)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.verticalLayout_18 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_16 = QLabel(self.groupBox_5)
        self.label_16.setObjectName(u"label_16")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_16)

        self.speedSelect = ComboBox2DA(self.groupBox_5)
        self.speedSelect.setObjectName(u"speedSelect")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.speedSelect)

        self.label_11 = QLabel(self.groupBox_5)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.factionSelect = ComboBox2DA(self.groupBox_5)
        self.factionSelect.setObjectName(u"factionSelect")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.factionSelect)

        self.label_99 = QLabel(self.groupBox_5)
        self.label_99.setObjectName(u"label_99")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_99)

        self.genderSelect = ComboBox2DA(self.groupBox_5)
        self.genderSelect.setObjectName(u"genderSelect")

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.genderSelect)

        self.label_12 = QLabel(self.groupBox_5)
        self.label_12.setObjectName(u"label_12")

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label_12)

        self.perceptionSelect = ComboBox2DA(self.groupBox_5)
        self.perceptionSelect.setObjectName(u"perceptionSelect")

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.perceptionSelect)

        self.label_13 = QLabel(self.groupBox_5)
        self.label_13.setObjectName(u"label_13")

        self.formLayout_3.setWidget(4, QFormLayout.LabelRole, self.label_13)

        self.challengeRatingSpin = QDoubleSpinBox(self.groupBox_5)
        self.challengeRatingSpin.setObjectName(u"challengeRatingSpin")

        self.formLayout_3.setWidget(4, QFormLayout.FieldRole, self.challengeRatingSpin)


        self.verticalLayout_18.addLayout(self.formLayout_3)

        self.k2onlyBox = QFrame(self.groupBox_5)
        self.k2onlyBox.setObjectName(u"k2onlyBox")
        self.k2onlyBox.setFrameShape(QFrame.NoFrame)
        self.k2onlyBox.setFrameShadow(QFrame.Plain)
        self.formLayout_24 = QFormLayout(self.k2onlyBox)
        self.formLayout_24.setObjectName(u"formLayout_24")
        self.formLayout_24.setContentsMargins(0, 0, 0, 0)
        self.label_102 = QLabel(self.k2onlyBox)
        self.label_102.setObjectName(u"label_102")

        self.formLayout_24.setWidget(1, QFormLayout.LabelRole, self.label_102)

        self.blindSpotSpin = QDoubleSpinBox(self.k2onlyBox)
        self.blindSpotSpin.setObjectName(u"blindSpotSpin")

        self.formLayout_24.setWidget(1, QFormLayout.FieldRole, self.blindSpotSpin)

        self.label_110 = QLabel(self.k2onlyBox)
        self.label_110.setObjectName(u"label_110")

        self.formLayout_24.setWidget(2, QFormLayout.LabelRole, self.label_110)

        self.line = QFrame(self.k2onlyBox)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.formLayout_24.setWidget(0, QFormLayout.FieldRole, self.line)

        self.multiplierSetSpin = QSpinBox(self.k2onlyBox)
        self.multiplierSetSpin.setObjectName(u"multiplierSetSpin")
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
        self.statsTab.setObjectName(u"statsTab")
        self.horizontalLayout_11 = QHBoxLayout(self.statsTab)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox_6 = QGroupBox(self.statsTab)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.formLayout_4 = QFormLayout(self.groupBox_6)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_17 = QLabel(self.groupBox_6)
        self.label_17.setObjectName(u"label_17")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_17)

        self.computerUseSpin = QSpinBox(self.groupBox_6)
        self.computerUseSpin.setObjectName(u"computerUseSpin")
        self.computerUseSpin.setMinimum(-2147483648)
        self.computerUseSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.computerUseSpin)

        self.label_18 = QLabel(self.groupBox_6)
        self.label_18.setObjectName(u"label_18")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_18)

        self.demolitionsSpin = QSpinBox(self.groupBox_6)
        self.demolitionsSpin.setObjectName(u"demolitionsSpin")
        self.demolitionsSpin.setMinimum(-2147483648)
        self.demolitionsSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.demolitionsSpin)

        self.label_19 = QLabel(self.groupBox_6)
        self.label_19.setObjectName(u"label_19")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_19)

        self.stealthSpin = QSpinBox(self.groupBox_6)
        self.stealthSpin.setObjectName(u"stealthSpin")
        self.stealthSpin.setMinimum(-2147483648)
        self.stealthSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.stealthSpin)

        self.label_20 = QLabel(self.groupBox_6)
        self.label_20.setObjectName(u"label_20")

        self.formLayout_4.setWidget(3, QFormLayout.LabelRole, self.label_20)

        self.awarenessSpin = QSpinBox(self.groupBox_6)
        self.awarenessSpin.setObjectName(u"awarenessSpin")
        self.awarenessSpin.setMinimum(-2147483648)
        self.awarenessSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.awarenessSpin)

        self.label_21 = QLabel(self.groupBox_6)
        self.label_21.setObjectName(u"label_21")

        self.formLayout_4.setWidget(4, QFormLayout.LabelRole, self.label_21)

        self.persuadeSpin = QSpinBox(self.groupBox_6)
        self.persuadeSpin.setObjectName(u"persuadeSpin")
        self.persuadeSpin.setMinimum(-2147483648)
        self.persuadeSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(4, QFormLayout.FieldRole, self.persuadeSpin)

        self.label_22 = QLabel(self.groupBox_6)
        self.label_22.setObjectName(u"label_22")

        self.formLayout_4.setWidget(5, QFormLayout.LabelRole, self.label_22)

        self.repairSpin = QSpinBox(self.groupBox_6)
        self.repairSpin.setObjectName(u"repairSpin")
        self.repairSpin.setMinimum(-2147483648)
        self.repairSpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(5, QFormLayout.FieldRole, self.repairSpin)

        self.label_23 = QLabel(self.groupBox_6)
        self.label_23.setObjectName(u"label_23")

        self.formLayout_4.setWidget(6, QFormLayout.LabelRole, self.label_23)

        self.securitySpin = QSpinBox(self.groupBox_6)
        self.securitySpin.setObjectName(u"securitySpin")
        self.securitySpin.setMinimum(-2147483648)
        self.securitySpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(6, QFormLayout.FieldRole, self.securitySpin)

        self.label_24 = QLabel(self.groupBox_6)
        self.label_24.setObjectName(u"label_24")

        self.formLayout_4.setWidget(7, QFormLayout.LabelRole, self.label_24)

        self.treatInjurySpin = QSpinBox(self.groupBox_6)
        self.treatInjurySpin.setObjectName(u"treatInjurySpin")
        self.treatInjurySpin.setMinimum(-2147483648)
        self.treatInjurySpin.setMaximum(2147483647)

        self.formLayout_4.setWidget(7, QFormLayout.FieldRole, self.treatInjurySpin)


        self.verticalLayout_5.addWidget(self.groupBox_6)

        self.groupBox_8 = QGroupBox(self.statsTab)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.formLayout_6 = QFormLayout(self.groupBox_8)
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.label_31 = QLabel(self.groupBox_8)
        self.label_31.setObjectName(u"label_31")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_31)

        self.fortitudeSpin = QSpinBox(self.groupBox_8)
        self.fortitudeSpin.setObjectName(u"fortitudeSpin")
        self.fortitudeSpin.setMinimum(-2147483648)
        self.fortitudeSpin.setMaximum(2147483647)

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.fortitudeSpin)

        self.label_32 = QLabel(self.groupBox_8)
        self.label_32.setObjectName(u"label_32")

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.label_32)

        self.label_33 = QLabel(self.groupBox_8)
        self.label_33.setObjectName(u"label_33")

        self.formLayout_6.setWidget(2, QFormLayout.LabelRole, self.label_33)

        self.reflexSpin = QSpinBox(self.groupBox_8)
        self.reflexSpin.setObjectName(u"reflexSpin")
        self.reflexSpin.setMinimum(-2147483648)
        self.reflexSpin.setMaximum(2147483647)

        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.reflexSpin)

        self.willSpin = QSpinBox(self.groupBox_8)
        self.willSpin.setObjectName(u"willSpin")
        self.willSpin.setMinimum(-2147483648)
        self.willSpin.setMaximum(2147483647)

        self.formLayout_6.setWidget(2, QFormLayout.FieldRole, self.willSpin)


        self.verticalLayout_5.addWidget(self.groupBox_8)

        self.groupBox_9 = QGroupBox(self.statsTab)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.formLayout_7 = QFormLayout(self.groupBox_9)
        self.formLayout_7.setObjectName(u"formLayout_7")
        self.label_34 = QLabel(self.groupBox_9)
        self.label_34.setObjectName(u"label_34")

        self.formLayout_7.setWidget(0, QFormLayout.LabelRole, self.label_34)

        self.armorClassSpin = QSpinBox(self.groupBox_9)
        self.armorClassSpin.setObjectName(u"armorClassSpin")
        self.armorClassSpin.setMinimum(-2147483648)
        self.armorClassSpin.setMaximum(2147483647)

        self.formLayout_7.setWidget(0, QFormLayout.FieldRole, self.armorClassSpin)


        self.verticalLayout_5.addWidget(self.groupBox_9)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)


        self.horizontalLayout_11.addLayout(self.verticalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.groupBox_7 = QGroupBox(self.statsTab)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.formLayout_5 = QFormLayout(self.groupBox_7)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.label_25 = QLabel(self.groupBox_7)
        self.label_25.setObjectName(u"label_25")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_25)

        self.strengthSpin = QSpinBox(self.groupBox_7)
        self.strengthSpin.setObjectName(u"strengthSpin")
        self.strengthSpin.setMinimum(-2147483648)
        self.strengthSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.strengthSpin)

        self.label_26 = QLabel(self.groupBox_7)
        self.label_26.setObjectName(u"label_26")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_26)

        self.dexteritySpin = QSpinBox(self.groupBox_7)
        self.dexteritySpin.setObjectName(u"dexteritySpin")
        self.dexteritySpin.setMinimum(-2147483648)
        self.dexteritySpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.dexteritySpin)

        self.label_27 = QLabel(self.groupBox_7)
        self.label_27.setObjectName(u"label_27")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_27)

        self.constitutionSpin = QSpinBox(self.groupBox_7)
        self.constitutionSpin.setObjectName(u"constitutionSpin")
        self.constitutionSpin.setMinimum(-2147483648)
        self.constitutionSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.constitutionSpin)

        self.label_28 = QLabel(self.groupBox_7)
        self.label_28.setObjectName(u"label_28")

        self.formLayout_5.setWidget(3, QFormLayout.LabelRole, self.label_28)

        self.intelligenceSpin = QSpinBox(self.groupBox_7)
        self.intelligenceSpin.setObjectName(u"intelligenceSpin")
        self.intelligenceSpin.setMinimum(-2147483648)
        self.intelligenceSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(3, QFormLayout.FieldRole, self.intelligenceSpin)

        self.label_29 = QLabel(self.groupBox_7)
        self.label_29.setObjectName(u"label_29")

        self.formLayout_5.setWidget(4, QFormLayout.LabelRole, self.label_29)

        self.wisdomSpin = QSpinBox(self.groupBox_7)
        self.wisdomSpin.setObjectName(u"wisdomSpin")
        self.wisdomSpin.setMinimum(-2147483648)
        self.wisdomSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(4, QFormLayout.FieldRole, self.wisdomSpin)

        self.label_30 = QLabel(self.groupBox_7)
        self.label_30.setObjectName(u"label_30")

        self.formLayout_5.setWidget(5, QFormLayout.LabelRole, self.label_30)

        self.charismaSpin = QSpinBox(self.groupBox_7)
        self.charismaSpin.setObjectName(u"charismaSpin")
        self.charismaSpin.setMinimum(-2147483648)
        self.charismaSpin.setMaximum(2147483647)

        self.formLayout_5.setWidget(5, QFormLayout.FieldRole, self.charismaSpin)


        self.verticalLayout_6.addWidget(self.groupBox_7)

        self.groupBox_10 = QGroupBox(self.statsTab)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.formLayout_8 = QFormLayout(self.groupBox_10)
        self.formLayout_8.setObjectName(u"formLayout_8")
        self.label_35 = QLabel(self.groupBox_10)
        self.label_35.setObjectName(u"label_35")

        self.formLayout_8.setWidget(0, QFormLayout.LabelRole, self.label_35)

        self.label_36 = QLabel(self.groupBox_10)
        self.label_36.setObjectName(u"label_36")

        self.formLayout_8.setWidget(1, QFormLayout.LabelRole, self.label_36)

        self.label_37 = QLabel(self.groupBox_10)
        self.label_37.setObjectName(u"label_37")

        self.formLayout_8.setWidget(2, QFormLayout.LabelRole, self.label_37)

        self.baseHpSpin = QSpinBox(self.groupBox_10)
        self.baseHpSpin.setObjectName(u"baseHpSpin")
        self.baseHpSpin.setMinimum(-2147483648)
        self.baseHpSpin.setMaximum(2147483647)

        self.formLayout_8.setWidget(0, QFormLayout.FieldRole, self.baseHpSpin)

        self.currentHpSpin = QSpinBox(self.groupBox_10)
        self.currentHpSpin.setObjectName(u"currentHpSpin")
        self.currentHpSpin.setMinimum(-2147483648)
        self.currentHpSpin.setMaximum(2147483647)

        self.formLayout_8.setWidget(1, QFormLayout.FieldRole, self.currentHpSpin)

        self.maxHpSpin = QSpinBox(self.groupBox_10)
        self.maxHpSpin.setObjectName(u"maxHpSpin")
        self.maxHpSpin.setMinimum(-2147483648)
        self.maxHpSpin.setMaximum(2147483647)

        self.formLayout_8.setWidget(2, QFormLayout.FieldRole, self.maxHpSpin)


        self.verticalLayout_6.addWidget(self.groupBox_10)

        self.groupBox_11 = QGroupBox(self.statsTab)
        self.groupBox_11.setObjectName(u"groupBox_11")
        self.formLayout_9 = QFormLayout(self.groupBox_11)
        self.formLayout_9.setObjectName(u"formLayout_9")
        self.label_39 = QLabel(self.groupBox_11)
        self.label_39.setObjectName(u"label_39")

        self.formLayout_9.setWidget(0, QFormLayout.LabelRole, self.label_39)

        self.currentFpSpin = QSpinBox(self.groupBox_11)
        self.currentFpSpin.setObjectName(u"currentFpSpin")
        self.currentFpSpin.setMinimum(-2147483648)
        self.currentFpSpin.setMaximum(2147483647)

        self.formLayout_9.setWidget(0, QFormLayout.FieldRole, self.currentFpSpin)

        self.label_40 = QLabel(self.groupBox_11)
        self.label_40.setObjectName(u"label_40")

        self.formLayout_9.setWidget(1, QFormLayout.LabelRole, self.label_40)

        self.maxFpSpin = QSpinBox(self.groupBox_11)
        self.maxFpSpin.setObjectName(u"maxFpSpin")
        self.maxFpSpin.setMinimum(-2147483648)
        self.maxFpSpin.setMaximum(2147483647)

        self.formLayout_9.setWidget(1, QFormLayout.FieldRole, self.maxFpSpin)


        self.verticalLayout_6.addWidget(self.groupBox_11)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_2)


        self.horizontalLayout_11.addLayout(self.verticalLayout_6)

        self.tabWidget.addTab(self.statsTab, "")
        self.classesTab = QWidget()
        self.classesTab.setObjectName(u"classesTab")
        self.verticalLayout_7 = QVBoxLayout(self.classesTab)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.groupBox_13 = QGroupBox(self.classesTab)
        self.groupBox_13.setObjectName(u"groupBox_13")
        self.gridLayout_3 = QGridLayout(self.groupBox_13)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.class1Select = ComboBox2DA(self.groupBox_13)
        self.class1Select.setObjectName(u"class1Select")

        self.horizontalLayout_13.addWidget(self.class1Select)

        self.class1LevelSpin = QSpinBox(self.groupBox_13)
        self.class1LevelSpin.setObjectName(u"class1LevelSpin")
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
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.class2Select = ComboBox2DA(self.groupBox_13)
        self.class2Select.setObjectName(u"class2Select")

        self.horizontalLayout_14.addWidget(self.class2Select)

        self.class2LevelSpin = QSpinBox(self.groupBox_13)
        self.class2LevelSpin.setObjectName(u"class2LevelSpin")
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
        self.groupBox_12.setObjectName(u"groupBox_12")
        self.horizontalLayout_12 = QHBoxLayout(self.groupBox_12)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_52 = QLabel(self.groupBox_12)
        self.label_52.setObjectName(u"label_52")

        self.horizontalLayout_12.addWidget(self.label_52)

        self.alignmentSlider = QSlider(self.groupBox_12)
        self.alignmentSlider.setObjectName(u"alignmentSlider")
        self.alignmentSlider.setMaximum(100)
        self.alignmentSlider.setValue(50)
        self.alignmentSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_12.addWidget(self.alignmentSlider)

        self.label_53 = QLabel(self.groupBox_12)
        self.label_53.setObjectName(u"label_53")

        self.horizontalLayout_12.addWidget(self.label_53)


        self.verticalLayout_7.addWidget(self.groupBox_12)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.spacer)

        self.tabWidget.addTab(self.classesTab, "")
        self.featsTab = QWidget()
        self.featsTab.setObjectName(u"featsTab")
        self.verticalLayout_8 = QVBoxLayout(self.featsTab)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.featList = QListWidget(self.featsTab)
        self.featList.setObjectName(u"featList")

        self.verticalLayout_8.addWidget(self.featList)

        self.groupBox_14 = QGroupBox(self.featsTab)
        self.groupBox_14.setObjectName(u"groupBox_14")
        self.gridLayout_4 = QGridLayout(self.groupBox_14)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.featSummaryEdit = QPlainTextEdit(self.groupBox_14)
        self.featSummaryEdit.setObjectName(u"featSummaryEdit")
        self.featSummaryEdit.setReadOnly(True)

        self.gridLayout_4.addWidget(self.featSummaryEdit, 0, 0, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_14)

        self.verticalLayout_8.setStretch(0, 2)
        self.verticalLayout_8.setStretch(1, 1)
        self.tabWidget.addTab(self.featsTab, "")
        self.powersTab = QWidget()
        self.powersTab.setObjectName(u"powersTab")
        self.verticalLayout_17 = QVBoxLayout(self.powersTab)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.powerList = QListWidget(self.powersTab)
        self.powerList.setObjectName(u"powerList")

        self.verticalLayout_17.addWidget(self.powerList)

        self.groupBox_29 = QGroupBox(self.powersTab)
        self.groupBox_29.setObjectName(u"groupBox_29")
        self.gridLayout_8 = QGridLayout(self.groupBox_29)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.powerSummaryEdit = QPlainTextEdit(self.groupBox_29)
        self.powerSummaryEdit.setObjectName(u"powerSummaryEdit")
        self.powerSummaryEdit.setReadOnly(True)

        self.gridLayout_8.addWidget(self.powerSummaryEdit, 0, 0, 1, 1)


        self.verticalLayout_17.addWidget(self.groupBox_29)

        self.verticalLayout_17.setStretch(0, 2)
        self.verticalLayout_17.setStretch(1, 1)
        self.tabWidget.addTab(self.powersTab, "")
        self.Scripts = QWidget()
        self.Scripts.setObjectName(u"Scripts")
        self.formLayout_22 = QFormLayout(self.Scripts)
        self.formLayout_22.setObjectName(u"formLayout_22")
        self.label_95 = QLabel(self.Scripts)
        self.label_95.setObjectName(u"label_95")

        self.formLayout_22.setWidget(0, QFormLayout.LabelRole, self.label_95)

        self.horizontalLayout_29 = QHBoxLayout()
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.onBlockedEdit = FilterComboBox(self.Scripts)
        self.onBlockedEdit.setObjectName(u"onBlockedEdit")

        self.horizontalLayout_29.addWidget(self.onBlockedEdit)


        self.formLayout_22.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_29)

        self.label_106 = QLabel(self.Scripts)
        self.label_106.setObjectName(u"label_106")

        self.formLayout_22.setWidget(1, QFormLayout.LabelRole, self.label_106)

        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setObjectName(u"horizontalLayout_30")
        self.onAttackedEdit = FilterComboBox(self.Scripts)
        self.onAttackedEdit.setObjectName(u"onAttackedEdit")

        self.horizontalLayout_30.addWidget(self.onAttackedEdit)


        self.formLayout_22.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_30)

        self.label_96 = QLabel(self.Scripts)
        self.label_96.setObjectName(u"label_96")

        self.formLayout_22.setWidget(2, QFormLayout.LabelRole, self.label_96)

        self.horizontalLayout_31 = QHBoxLayout()
        self.horizontalLayout_31.setObjectName(u"horizontalLayout_31")
        self.onNoticeEdit = FilterComboBox(self.Scripts)
        self.onNoticeEdit.setObjectName(u"onNoticeEdit")

        self.horizontalLayout_31.addWidget(self.onNoticeEdit)


        self.formLayout_22.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_31)

        self.label_97 = QLabel(self.Scripts)
        self.label_97.setObjectName(u"label_97")

        self.formLayout_22.setWidget(3, QFormLayout.LabelRole, self.label_97)

        self.horizontalLayout_32 = QHBoxLayout()
        self.horizontalLayout_32.setObjectName(u"horizontalLayout_32")
        self.onConversationEdit = FilterComboBox(self.Scripts)
        self.onConversationEdit.setObjectName(u"onConversationEdit")

        self.horizontalLayout_32.addWidget(self.onConversationEdit)


        self.formLayout_22.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_32)

        self.label_98 = QLabel(self.Scripts)
        self.label_98.setObjectName(u"label_98")

        self.formLayout_22.setWidget(4, QFormLayout.LabelRole, self.label_98)

        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setObjectName(u"horizontalLayout_33")
        self.onDamagedEdit = FilterComboBox(self.Scripts)
        self.onDamagedEdit.setObjectName(u"onDamagedEdit")

        self.horizontalLayout_33.addWidget(self.onDamagedEdit)


        self.formLayout_22.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_33)

        self.label_109 = QLabel(self.Scripts)
        self.label_109.setObjectName(u"label_109")

        self.formLayout_22.setWidget(5, QFormLayout.LabelRole, self.label_109)

        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.onDeathEdit = FilterComboBox(self.Scripts)
        self.onDeathEdit.setObjectName(u"onDeathEdit")

        self.horizontalLayout_34.addWidget(self.onDeathEdit)


        self.formLayout_22.setLayout(5, QFormLayout.FieldRole, self.horizontalLayout_34)

        self.label_107 = QLabel(self.Scripts)
        self.label_107.setObjectName(u"label_107")

        self.formLayout_22.setWidget(6, QFormLayout.LabelRole, self.label_107)

        self.horizontalLayout_35 = QHBoxLayout()
        self.horizontalLayout_35.setObjectName(u"horizontalLayout_35")
        self.onEndRoundEdit = FilterComboBox(self.Scripts)
        self.onEndRoundEdit.setObjectName(u"onEndRoundEdit")

        self.horizontalLayout_35.addWidget(self.onEndRoundEdit)


        self.formLayout_22.setLayout(6, QFormLayout.FieldRole, self.horizontalLayout_35)

        self.label_108 = QLabel(self.Scripts)
        self.label_108.setObjectName(u"label_108")

        self.formLayout_22.setWidget(7, QFormLayout.LabelRole, self.label_108)

        self.horizontalLayout_36 = QHBoxLayout()
        self.horizontalLayout_36.setObjectName(u"horizontalLayout_36")
        self.onEndConversationEdit = FilterComboBox(self.Scripts)
        self.onEndConversationEdit.setObjectName(u"onEndConversationEdit")

        self.horizontalLayout_36.addWidget(self.onEndConversationEdit)


        self.formLayout_22.setLayout(7, QFormLayout.FieldRole, self.horizontalLayout_36)

        self.label_100 = QLabel(self.Scripts)
        self.label_100.setObjectName(u"label_100")

        self.formLayout_22.setWidget(8, QFormLayout.LabelRole, self.label_100)

        self.horizontalLayout_38 = QHBoxLayout()
        self.horizontalLayout_38.setObjectName(u"horizontalLayout_38")
        self.onDisturbedEdit = FilterComboBox(self.Scripts)
        self.onDisturbedEdit.setObjectName(u"onDisturbedEdit")

        self.horizontalLayout_38.addWidget(self.onDisturbedEdit)


        self.formLayout_22.setLayout(8, QFormLayout.FieldRole, self.horizontalLayout_38)

        self.label_101 = QLabel(self.Scripts)
        self.label_101.setObjectName(u"label_101")

        self.formLayout_22.setWidget(9, QFormLayout.LabelRole, self.label_101)

        self.horizontalLayout_39 = QHBoxLayout()
        self.horizontalLayout_39.setObjectName(u"horizontalLayout_39")
        self.onHeartbeatEdit = FilterComboBox(self.Scripts)
        self.onHeartbeatEdit.setObjectName(u"onHeartbeatEdit")

        self.horizontalLayout_39.addWidget(self.onHeartbeatEdit)


        self.formLayout_22.setLayout(9, QFormLayout.FieldRole, self.horizontalLayout_39)

        self.label_103 = QLabel(self.Scripts)
        self.label_103.setObjectName(u"label_103")

        self.formLayout_22.setWidget(10, QFormLayout.LabelRole, self.label_103)

        self.horizontalLayout_41 = QHBoxLayout()
        self.horizontalLayout_41.setObjectName(u"horizontalLayout_41")
        self.onSpawnEdit = FilterComboBox(self.Scripts)
        self.onSpawnEdit.setObjectName(u"onSpawnEdit")

        self.horizontalLayout_41.addWidget(self.onSpawnEdit)


        self.formLayout_22.setLayout(10, QFormLayout.FieldRole, self.horizontalLayout_41)

        self.label_104 = QLabel(self.Scripts)
        self.label_104.setObjectName(u"label_104")

        self.formLayout_22.setWidget(11, QFormLayout.LabelRole, self.label_104)

        self.horizontalLayout_42 = QHBoxLayout()
        self.horizontalLayout_42.setObjectName(u"horizontalLayout_42")
        self.onSpellCastEdit = FilterComboBox(self.Scripts)
        self.onSpellCastEdit.setObjectName(u"onSpellCastEdit")

        self.horizontalLayout_42.addWidget(self.onSpellCastEdit)


        self.formLayout_22.setLayout(11, QFormLayout.FieldRole, self.horizontalLayout_42)

        self.label_105 = QLabel(self.Scripts)
        self.label_105.setObjectName(u"label_105")

        self.formLayout_22.setWidget(12, QFormLayout.LabelRole, self.label_105)

        self.horizontalLayout_43 = QHBoxLayout()
        self.horizontalLayout_43.setObjectName(u"horizontalLayout_43")
        self.onUserDefinedEdit = FilterComboBox(self.Scripts)
        self.onUserDefinedEdit.setObjectName(u"onUserDefinedEdit")

        self.horizontalLayout_43.addWidget(self.onUserDefinedEdit)


        self.formLayout_22.setLayout(12, QFormLayout.FieldRole, self.horizontalLayout_43)

        self.tabWidget.addTab(self.Scripts, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName(u"commentsTab")
        self.gridLayout_9 = QGridLayout(self.commentsTab)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.comments = QPlainTextEdit(self.commentsTab)
        self.comments.setObjectName(u"comments")

        self.gridLayout_9.addWidget(self.comments, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.horizontalLayout_15.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 900, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionSaveUnusedFields.setText(QCoreApplication.translate("MainWindow", u"Save Unused Fields", None))
        self.actionAlwaysSaveK2Fields.setText(QCoreApplication.translate("MainWindow", u"Always Save K2 Fields", None))
        self.actionShowPreview.setText(QCoreApplication.translate("MainWindow", u"Show Preview", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Profile", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"First Name:", None))
        self.firstnameRandomButton.setText(QCoreApplication.translate("MainWindow", u"?", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Last Name:", None))
        self.lastnameRandomButton.setText(QCoreApplication.translate("MainWindow", u"?", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"ResRef:", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Appearance:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Soundset:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Conversation:", None))
        self.conversationModifyButton.setText(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.groupBox_15.setTitle(QCoreApplication.translate("MainWindow", u"Inventory", None))
        self.inventoryCountLabel.setText(QCoreApplication.translate("MainWindow", u"Total Items:", None))
        self.inventoryButton.setText(QCoreApplication.translate("MainWindow", u"Edit Inventory", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Portrait", None))
        self.portraitPicture.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Basic", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Flags", None))
        self.disarmableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Disarmable", None))
        self.noPermDeathCheckbox.setText(QCoreApplication.translate("MainWindow", u"No Perm Death", None))
        self.min1HpCheckbox.setText(QCoreApplication.translate("MainWindow", u"Min 1 HP", None))
        self.plotCheckbox.setText(QCoreApplication.translate("MainWindow", u"Plot", None))
        self.isPcCheckbox.setText(QCoreApplication.translate("MainWindow", u"Is PC", None))
        self.noReorientateCheckbox.setText(QCoreApplication.translate("MainWindow", u"Doesn't Reorientate on PC", None))
        self.noBlockCheckbox.setText(QCoreApplication.translate("MainWindow", u"Doesn't Block PC", None))
        self.hologramCheckbox.setText(QCoreApplication.translate("MainWindow", u"Hologram", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Race", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Race:", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Subrace:", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Other", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Speed:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Faction:", None))
        self.label_99.setText(QCoreApplication.translate("MainWindow", u"Gender:", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Perception:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Challenge Rating:", None))
        self.label_102.setText(QCoreApplication.translate("MainWindow", u"Blindspot:", None))
        self.label_110.setText(QCoreApplication.translate("MainWindow", u"Multiplier Set:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.advancedTab), QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Skills", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Computer Use:", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Demolitions:", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"Stealth:", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"Awareness:", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Persuade:", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"Repair:", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Security:", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"Treat Injury:", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", u"Saves", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", u"Fortitude:", None))
        self.label_32.setText(QCoreApplication.translate("MainWindow", u"Reflex:", None))
        self.label_33.setText(QCoreApplication.translate("MainWindow", u"Will:", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("MainWindow", u"Armor Class", None))
        self.label_34.setText(QCoreApplication.translate("MainWindow", u"Armor Class:", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("MainWindow", u"Attributes", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Strength:", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"Dexterity:", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Constitution:", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", u"Intelligence:", None))
        self.label_29.setText(QCoreApplication.translate("MainWindow", u"Wisdom:", None))
        self.label_30.setText(QCoreApplication.translate("MainWindow", u"Charisma:", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("MainWindow", u"Hit Points", None))
        self.label_35.setText(QCoreApplication.translate("MainWindow", u"Base HP:", None))
        self.label_36.setText(QCoreApplication.translate("MainWindow", u"Current HP:", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", u"Max HP:", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("MainWindow", u"Force Points", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", u"Current FP:", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", u"Max FP:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.statsTab), QCoreApplication.translate("MainWindow", u"Stats", None))
        self.groupBox_13.setTitle(QCoreApplication.translate("MainWindow", u"Classes", None))
        self.groupBox_12.setTitle(QCoreApplication.translate("MainWindow", u"Alignment", None))
        self.label_52.setText(QCoreApplication.translate("MainWindow", u"Dark", None))
        self.label_53.setText(QCoreApplication.translate("MainWindow", u"Light", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.classesTab), QCoreApplication.translate("MainWindow", u"Classes", None))
        self.groupBox_14.setTitle(QCoreApplication.translate("MainWindow", u"Feat Summary", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.featsTab), QCoreApplication.translate("MainWindow", u"Feats", None))
        self.groupBox_29.setTitle(QCoreApplication.translate("MainWindow", u"Force Power Summary", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.powersTab), QCoreApplication.translate("MainWindow", u"Powers", None))
        self.label_95.setText(QCoreApplication.translate("MainWindow", u"OnBlocked:", None))
        self.label_106.setText(QCoreApplication.translate("MainWindow", u"OnAttacked:", None))
        self.label_96.setText(QCoreApplication.translate("MainWindow", u"OnNoticed:", None))
        self.label_97.setText(QCoreApplication.translate("MainWindow", u"OnConversation:", None))
        self.label_98.setText(QCoreApplication.translate("MainWindow", u"OnDamaged:", None))
        self.label_109.setText(QCoreApplication.translate("MainWindow", u"OnDeath:", None))
        self.label_107.setText(QCoreApplication.translate("MainWindow", u"OnEndRound:", None))
        self.label_108.setText(QCoreApplication.translate("MainWindow", u"OnEndConversation:", None))
        self.label_100.setText(QCoreApplication.translate("MainWindow", u"OnDisturbed:", None))
        self.label_101.setText(QCoreApplication.translate("MainWindow", u"OnHeartbeat:", None))
        self.label_103.setText(QCoreApplication.translate("MainWindow", u"OnSpawn:", None))
        self.label_104.setText(QCoreApplication.translate("MainWindow", u"OnSpellCastAt:", None))
        self.label_105.setText(QCoreApplication.translate("MainWindow", u"OnUserDefined:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Scripts), QCoreApplication.translate("MainWindow", u"Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", u"Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
