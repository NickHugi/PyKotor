# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'utd.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.renderer.model import ModelRenderer
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(654, 451)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionShowPreview = QAction(MainWindow)
        self.actionShowPreview.setObjectName(u"actionShowPreview")
        self.actionShowPreview.setCheckable(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.previewRenderer = ModelRenderer(self.centralwidget)
        self.previewRenderer.setObjectName(u"previewRenderer")
        self.previewRenderer.setMinimumSize(QSize(300, 0))
        self.previewRenderer.setMouseTracking(True)
        self.previewRenderer.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayout_2.addWidget(self.previewRenderer)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setMinimumSize(QSize(330, 0))
        self.tab_9 = QWidget()
        self.tab_9.setObjectName(u"tab_9")
        self.gridLayout_3 = QGridLayout(self.tab_9)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.verticalSpacer = QSpacerItem(20, 77, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.groupBox = QGroupBox(self.tab_9)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.formLayout_10 = QFormLayout()
        self.formLayout_10.setObjectName(u"formLayout_10")
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_10.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.nameEdit = LocalizedStringLineEdit(self.groupBox)
        self.nameEdit.setObjectName(u"nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_21.addWidget(self.nameEdit)


        self.horizontalLayout_15.addLayout(self.horizontalLayout_21)


        self.formLayout_10.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_15)

        self.label_14 = QLabel(self.groupBox)
        self.label_14.setObjectName(u"label_14")

        self.formLayout_10.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.tagEdit = QLineEdit(self.groupBox)
        self.tagEdit.setObjectName(u"tagEdit")

        self.horizontalLayout_16.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.groupBox)
        self.tagGenerateButton.setObjectName(u"tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_16.addWidget(self.tagGenerateButton)


        self.formLayout_10.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_16)

        self.label_38 = QLabel(self.groupBox)
        self.label_38.setObjectName(u"label_38")

        self.formLayout_10.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.resrefEdit = QLineEdit(self.groupBox)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_17.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.groupBox)
        self.resrefGenerateButton.setObjectName(u"resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_17.addWidget(self.resrefGenerateButton)


        self.formLayout_10.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_17)

        self.label_15 = QLabel(self.groupBox)
        self.label_15.setObjectName(u"label_15")

        self.formLayout_10.setWidget(3, QFormLayout.LabelRole, self.label_15)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.appearanceSelect = ComboBox2DA(self.groupBox)
        self.appearanceSelect.setObjectName(u"appearanceSelect")

        self.horizontalLayout_18.addWidget(self.appearanceSelect)

        self.horizontalSpacer_11 = QSpacerItem(29, 17, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_11)


        self.formLayout_10.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_18)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout_10.setWidget(4, QFormLayout.LabelRole, self.label)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.conversationEdit = QLineEdit(self.groupBox)
        self.conversationEdit.setObjectName(u"conversationEdit")
        self.conversationEdit.setMaxLength(16)

        self.horizontalLayout_5.addWidget(self.conversationEdit)

        self.conversationModifyButton = QPushButton(self.groupBox)
        self.conversationModifyButton.setObjectName(u"conversationModifyButton")
        self.conversationModifyButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_5.addWidget(self.conversationModifyButton)


        self.formLayout_10.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_5)


        self.gridLayout_2.addLayout(self.formLayout_10, 0, 0, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_9, "")
        self.tab_10 = QWidget()
        self.tab_10.setObjectName(u"tab_10")
        self.verticalLayout = QVBoxLayout(self.tab_10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox_16 = QGroupBox(self.tab_10)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.gridLayout_5 = QGridLayout(self.groupBox_16)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.useableCheckbox = QCheckBox(self.groupBox_16)
        self.useableCheckbox.setObjectName(u"useableCheckbox")

        self.gridLayout_5.addWidget(self.useableCheckbox, 2, 0, 1, 1)

        self.partyInteractCheckbox = QCheckBox(self.groupBox_16)
        self.partyInteractCheckbox.setObjectName(u"partyInteractCheckbox")

        self.gridLayout_5.addWidget(self.partyInteractCheckbox, 1, 0, 1, 1)

        self.staticCheckbox = QCheckBox(self.groupBox_16)
        self.staticCheckbox.setObjectName(u"staticCheckbox")

        self.gridLayout_5.addWidget(self.staticCheckbox, 1, 1, 1, 1)

        self.plotCheckbox = QCheckBox(self.groupBox_16)
        self.plotCheckbox.setObjectName(u"plotCheckbox")

        self.gridLayout_5.addWidget(self.plotCheckbox, 0, 1, 1, 1)

        self.notBlastableCheckbox = QCheckBox(self.groupBox_16)
        self.notBlastableCheckbox.setObjectName(u"notBlastableCheckbox")

        self.gridLayout_5.addWidget(self.notBlastableCheckbox, 2, 1, 1, 1)

        self.min1HpCheckbox = QCheckBox(self.groupBox_16)
        self.min1HpCheckbox.setObjectName(u"min1HpCheckbox")

        self.gridLayout_5.addWidget(self.min1HpCheckbox, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_16)

        self.groupBox_17 = QGroupBox(self.tab_10)
        self.groupBox_17.setObjectName(u"groupBox_17")
        self.formLayout_11 = QFormLayout(self.groupBox_17)
        self.formLayout_11.setObjectName(u"formLayout_11")
        self.label_41 = QLabel(self.groupBox_17)
        self.label_41.setObjectName(u"label_41")

        self.formLayout_11.setWidget(0, QFormLayout.LabelRole, self.label_41)

        self.factionSelect = ComboBox2DA(self.groupBox_17)
        self.factionSelect.setObjectName(u"factionSelect")

        self.formLayout_11.setWidget(0, QFormLayout.FieldRole, self.factionSelect)

        self.label_42 = QLabel(self.groupBox_17)
        self.label_42.setObjectName(u"label_42")

        self.formLayout_11.setWidget(1, QFormLayout.LabelRole, self.label_42)

        self.animationState = QSpinBox(self.groupBox_17)
        self.animationState.setObjectName(u"animationState")
        self.animationState.setMinimum(-2147483648)
        self.animationState.setMaximum(2147483647)

        self.formLayout_11.setWidget(1, QFormLayout.FieldRole, self.animationState)


        self.verticalLayout.addWidget(self.groupBox_17)

        self.groupBox_4 = QGroupBox(self.tab_10)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.formLayout_3 = QFormLayout(self.groupBox_4)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_3 = QLabel(self.groupBox_4)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.currenHpSpin = QSpinBox(self.groupBox_4)
        self.currenHpSpin.setObjectName(u"currenHpSpin")
        self.currenHpSpin.setMinimum(-2147483648)
        self.currenHpSpin.setMaximum(2147483647)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.currenHpSpin)

        self.label_26 = QLabel(self.groupBox_4)
        self.label_26.setObjectName(u"label_26")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_26)

        self.label_20 = QLabel(self.groupBox_4)
        self.label_20.setObjectName(u"label_20")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_20)

        self.hardnessSpin = QSpinBox(self.groupBox_4)
        self.hardnessSpin.setObjectName(u"hardnessSpin")
        self.hardnessSpin.setMinimum(-2147483648)
        self.hardnessSpin.setMaximum(2147483647)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.hardnessSpin)

        self.label_21 = QLabel(self.groupBox_4)
        self.label_21.setObjectName(u"label_21")

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label_21)

        self.fortitudeSpin = QSpinBox(self.groupBox_4)
        self.fortitudeSpin.setObjectName(u"fortitudeSpin")
        self.fortitudeSpin.setMinimum(-2147483648)
        self.fortitudeSpin.setMaximum(2147483647)

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.fortitudeSpin)

        self.label_24 = QLabel(self.groupBox_4)
        self.label_24.setObjectName(u"label_24")

        self.formLayout_3.setWidget(4, QFormLayout.LabelRole, self.label_24)

        self.reflexSpin = QSpinBox(self.groupBox_4)
        self.reflexSpin.setObjectName(u"reflexSpin")
        self.reflexSpin.setMinimum(-2147483648)
        self.reflexSpin.setMaximum(2147483647)

        self.formLayout_3.setWidget(4, QFormLayout.FieldRole, self.reflexSpin)

        self.label_25 = QLabel(self.groupBox_4)
        self.label_25.setObjectName(u"label_25")

        self.formLayout_3.setWidget(5, QFormLayout.LabelRole, self.label_25)

        self.willSpin = QSpinBox(self.groupBox_4)
        self.willSpin.setObjectName(u"willSpin")
        self.willSpin.setMinimum(-2147483648)
        self.willSpin.setMaximum(2147483647)

        self.formLayout_3.setWidget(5, QFormLayout.FieldRole, self.willSpin)

        self.maxHpSpin = QSpinBox(self.groupBox_4)
        self.maxHpSpin.setObjectName(u"maxHpSpin")
        self.maxHpSpin.setMinimum(-2147483648)
        self.maxHpSpin.setMaximum(2147483647)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.maxHpSpin)


        self.verticalLayout.addWidget(self.groupBox_4)

        self.tabWidget.addTab(self.tab_10, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_5 = QVBoxLayout(self.tab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox_3 = QGroupBox(self.tab)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.needKeyCheckbox = QCheckBox(self.groupBox_3)
        self.needKeyCheckbox.setObjectName(u"needKeyCheckbox")

        self.verticalLayout_4.addWidget(self.needKeyCheckbox)

        self.removeKeyCheckbox = QCheckBox(self.groupBox_3)
        self.removeKeyCheckbox.setObjectName(u"removeKeyCheckbox")

        self.verticalLayout_4.addWidget(self.removeKeyCheckbox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.keyEdit = QLineEdit(self.groupBox_3)
        self.keyEdit.setObjectName(u"keyEdit")

        self.horizontalLayout.addWidget(self.keyEdit)


        self.verticalLayout_4.addLayout(self.horizontalLayout)


        self.verticalLayout_5.addWidget(self.groupBox_3)

        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lockedCheckbox = QCheckBox(self.groupBox_2)
        self.lockedCheckbox.setObjectName(u"lockedCheckbox")

        self.verticalLayout_2.addWidget(self.lockedCheckbox)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.difficultyLabel = QLabel(self.groupBox_2)
        self.difficultyLabel.setObjectName(u"difficultyLabel")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.difficultyLabel)

        self.difficultyModLabel = QLabel(self.groupBox_2)
        self.difficultyModLabel.setObjectName(u"difficultyModLabel")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.difficultyModLabel)

        self.openLockSpin = QSpinBox(self.groupBox_2)
        self.openLockSpin.setObjectName(u"openLockSpin")
        self.openLockSpin.setMinimum(-2147483648)
        self.openLockSpin.setMaximum(2147483647)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.openLockSpin)

        self.difficultySpin = QSpinBox(self.groupBox_2)
        self.difficultySpin.setObjectName(u"difficultySpin")
        self.difficultySpin.setMinimum(-2147483648)
        self.difficultySpin.setMaximum(2147483647)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.difficultySpin)

        self.difficultyModSpin = QSpinBox(self.groupBox_2)
        self.difficultyModSpin.setObjectName(u"difficultyModSpin")
        self.difficultyModSpin.setMinimum(-2147483648)
        self.difficultyModSpin.setMaximum(2147483647)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.difficultyModSpin)


        self.verticalLayout_3.addLayout(self.formLayout)


        self.verticalLayout_5.addWidget(self.groupBox_2)

        self.verticalSpacer_3 = QSpacerItem(20, 123, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.formLayout_2 = QFormLayout(self.tab_2)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_18 = QLabel(self.tab_2)
        self.label_18.setObjectName(u"label_18")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_18)

        self.onClickEdit = QLineEdit(self.tab_2)
        self.onClickEdit.setObjectName(u"onClickEdit")
        self.onClickEdit.setMaxLength(16)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.onClickEdit)

        self.label_5 = QLabel(self.tab_2)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_5)

        self.onClosedEdit = QLineEdit(self.tab_2)
        self.onClosedEdit.setObjectName(u"onClosedEdit")
        self.onClosedEdit.setMaxLength(16)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.onClosedEdit)

        self.label_7 = QLabel(self.tab_2)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_7)

        self.onDamagedEdit = QLineEdit(self.tab_2)
        self.onDamagedEdit.setObjectName(u"onDamagedEdit")
        self.onDamagedEdit.setMaxLength(16)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.onDamagedEdit)

        self.label_8 = QLabel(self.tab_2)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_8)

        self.onDeathEdit = QLineEdit(self.tab_2)
        self.onDeathEdit.setObjectName(u"onDeathEdit")
        self.onDeathEdit.setMaxLength(16)

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.onDeathEdit)

        self.label_10 = QLabel(self.tab_2)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.label_10)

        self.onOpenFailedEdit = QLineEdit(self.tab_2)
        self.onOpenFailedEdit.setObjectName(u"onOpenFailedEdit")
        self.onOpenFailedEdit.setMaxLength(16)

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.onOpenFailedEdit)

        self.label_11 = QLabel(self.tab_2)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.label_11)

        self.onHeartbeatEdit = QLineEdit(self.tab_2)
        self.onHeartbeatEdit.setObjectName(u"onHeartbeatEdit")
        self.onHeartbeatEdit.setMaxLength(16)

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.onHeartbeatEdit)

        self.label_13 = QLabel(self.tab_2)
        self.label_13.setObjectName(u"label_13")

        self.formLayout_2.setWidget(6, QFormLayout.LabelRole, self.label_13)

        self.onMeleeAttackEdit = QLineEdit(self.tab_2)
        self.onMeleeAttackEdit.setObjectName(u"onMeleeAttackEdit")
        self.onMeleeAttackEdit.setMaxLength(16)

        self.formLayout_2.setWidget(6, QFormLayout.FieldRole, self.onMeleeAttackEdit)

        self.label_16 = QLabel(self.tab_2)
        self.label_16.setObjectName(u"label_16")

        self.formLayout_2.setWidget(7, QFormLayout.LabelRole, self.label_16)

        self.onSpellEdit = QLineEdit(self.tab_2)
        self.onSpellEdit.setObjectName(u"onSpellEdit")
        self.onSpellEdit.setMaxLength(16)

        self.formLayout_2.setWidget(7, QFormLayout.FieldRole, self.onSpellEdit)

        self.label_17 = QLabel(self.tab_2)
        self.label_17.setObjectName(u"label_17")

        self.formLayout_2.setWidget(8, QFormLayout.LabelRole, self.label_17)

        self.onOpenEdit = QLineEdit(self.tab_2)
        self.onOpenEdit.setObjectName(u"onOpenEdit")
        self.onOpenEdit.setMaxLength(16)

        self.formLayout_2.setWidget(8, QFormLayout.FieldRole, self.onOpenEdit)

        self.label_23 = QLabel(self.tab_2)
        self.label_23.setObjectName(u"label_23")

        self.formLayout_2.setWidget(9, QFormLayout.LabelRole, self.label_23)

        self.onUnlockEdit = QLineEdit(self.tab_2)
        self.onUnlockEdit.setObjectName(u"onUnlockEdit")
        self.onUnlockEdit.setMaxLength(16)

        self.formLayout_2.setWidget(9, QFormLayout.FieldRole, self.onUnlockEdit)

        self.label_19 = QLabel(self.tab_2)
        self.label_19.setObjectName(u"label_19")

        self.formLayout_2.setWidget(10, QFormLayout.LabelRole, self.label_19)

        self.onUserDefinedEdit = QLineEdit(self.tab_2)
        self.onUserDefinedEdit.setObjectName(u"onUserDefinedEdit")
        self.onUserDefinedEdit.setMaxLength(16)

        self.formLayout_2.setWidget(10, QFormLayout.FieldRole, self.onUserDefinedEdit)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.gridLayout_4 = QGridLayout(self.tab_3)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.commentsEdit = QPlainTextEdit(self.tab_3)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.gridLayout_4.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_3, "")

        self.horizontalLayout_2.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 654, 22))
        self.menuNew = QMenu(self.menubar)
        self.menuNew.setObjectName(u"menuNew")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuNew.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menuNew.addAction(self.actionNew)
        self.menuNew.addAction(self.actionOpen)
        self.menuNew.addAction(self.actionSave)
        self.menuNew.addAction(self.actionSave_As)
        self.menuNew.addAction(self.actionRevert)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionExit)
        self.menuView.addAction(self.actionShowPreview)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionShowPreview.setText(QCoreApplication.translate("MainWindow", u"Show Preview", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Profile", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"Appearance:", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Conversation:", None))
        self.conversationModifyButton.setText(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_9), QCoreApplication.translate("MainWindow", u"Basic", None))
        self.groupBox_16.setTitle(QCoreApplication.translate("MainWindow", u"Flags", None))
        self.useableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Useable", None))
        self.partyInteractCheckbox.setText(QCoreApplication.translate("MainWindow", u"Party Interact", None))
        self.staticCheckbox.setText(QCoreApplication.translate("MainWindow", u"Static", None))
        self.plotCheckbox.setText(QCoreApplication.translate("MainWindow", u"Plot", None))
        self.notBlastableCheckbox.setText(QCoreApplication.translate("MainWindow", u"Not Blastable", None))
        self.min1HpCheckbox.setText(QCoreApplication.translate("MainWindow", u"Min1HP", None))
        self.groupBox_17.setTitle(QCoreApplication.translate("MainWindow", u"Other", None))
        self.label_41.setText(QCoreApplication.translate("MainWindow", u"Faction:", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", u"Animation State:", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Stats", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Current HP:", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"Max HP:", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"Hardness:", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Fortitude:", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"Reflex:", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Will:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_10), QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Key", None))
        self.needKeyCheckbox.setText(QCoreApplication.translate("MainWindow", u"Key required to unlock", None))
        self.removeKeyCheckbox.setText(QCoreApplication.translate("MainWindow", u"Remove key on unlock", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Key Tag:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Lock", None))
        self.lockedCheckbox.setText(QCoreApplication.translate("MainWindow", u"Locked", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Open Lock DC:", None))
        self.difficultyLabel.setText(QCoreApplication.translate("MainWindow", u"Difficulty:", None))
        self.difficultyModLabel.setText(QCoreApplication.translate("MainWindow", u"Difficulty Mod:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Lock", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"OnClicked:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"OnClosed:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"OnDamaged:", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"OnDeath:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"OnOpenFailed:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"OnHeartbeat:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"OnMeleeAttack:", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"OnSpellCastAt:", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"OnOpen:", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"OnUnlock:", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"OnUserDefined:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Comments", None))
        self.menuNew.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
    # retranslateUi

