
################################################################################
## Form generated from reading UI file 'utd.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
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
        MainWindow.resize(654, 495)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionShowPreview = QAction(MainWindow)
        self.actionShowPreview.setObjectName("actionShowPreview")
        self.actionShowPreview.setCheckable(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.previewRenderer = ModelRenderer(self.centralwidget)
        self.previewRenderer.setObjectName("previewRenderer")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.previewRenderer.sizePolicy().hasHeightForWidth())
        self.previewRenderer.setSizePolicy(sizePolicy)
        self.previewRenderer.setMinimumSize(QSize(300, 0))
        self.previewRenderer.setMouseTracking(True)
        self.previewRenderer.setFocusPolicy(Qt.StrongFocus)

        self.horizontalLayout_2.addWidget(self.previewRenderer)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setMinimumSize(QSize(330, 0))
        self.tab_9 = QWidget()
        self.tab_9.setObjectName("tab_9")
        self.gridLayout_3 = QGridLayout(self.tab_9)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")
        self.formLayout_3.setContentsMargins(6, 6, 6, 6)
        self.label_6 = QLabel(self.tab_9)
        self.label_6.setObjectName("label_6")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.nameEdit = LocalizedStringLineEdit(self.tab_9)
        self.nameEdit.setObjectName("nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_15.addWidget(self.nameEdit)


        self.formLayout_3.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_15)

        self.label_14 = QLabel(self.tab_9)
        self.label_14.setObjectName("label_14")
        sizePolicy1.setHeightForWidth(self.label_14.sizePolicy().hasHeightForWidth())
        self.label_14.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.tagEdit = QLineEdit(self.tab_9)
        self.tagEdit.setObjectName("tagEdit")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tagEdit.sizePolicy().hasHeightForWidth())
        self.tagEdit.setSizePolicy(sizePolicy2)

        self.horizontalLayout_16.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.tab_9)
        self.tagGenerateButton.setObjectName("tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(30, 16777215))

        self.horizontalLayout_16.addWidget(self.tagGenerateButton)


        self.formLayout_3.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_16)

        self.label_38 = QLabel(self.tab_9)
        self.label_38.setObjectName("label_38")
        sizePolicy1.setHeightForWidth(self.label_38.sizePolicy().hasHeightForWidth())
        self.label_38.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.resrefEdit = QLineEdit(self.tab_9)
        self.resrefEdit.setObjectName("resrefEdit")
        sizePolicy2.setHeightForWidth(self.resrefEdit.sizePolicy().hasHeightForWidth())
        self.resrefEdit.setSizePolicy(sizePolicy2)
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_17.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.tab_9)
        self.resrefGenerateButton.setObjectName("resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(30, 16777215))

        self.horizontalLayout_17.addWidget(self.resrefGenerateButton)


        self.formLayout_3.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_17)

        self.label_15 = QLabel(self.tab_9)
        self.label_15.setObjectName("label_15")
        sizePolicy1.setHeightForWidth(self.label_15.sizePolicy().hasHeightForWidth())
        self.label_15.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.label_15)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.appearanceSelect = ComboBox2DA(self.tab_9)
        self.appearanceSelect.setObjectName("appearanceSelect")
        sizePolicy2.setHeightForWidth(self.appearanceSelect.sizePolicy().hasHeightForWidth())
        self.appearanceSelect.setSizePolicy(sizePolicy2)

        self.horizontalLayout_18.addWidget(self.appearanceSelect)


        self.formLayout_3.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_18)

        self.label = QLabel(self.tab_9)
        self.label.setObjectName("label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(4, QFormLayout.LabelRole, self.label)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.conversationEdit = FilterComboBox(self.tab_9)
        self.conversationEdit.setObjectName("conversationEdit")
        sizePolicy1.setHeightForWidth(self.conversationEdit.sizePolicy().hasHeightForWidth())
        self.conversationEdit.setSizePolicy(sizePolicy1)

        self.horizontalLayout_5.addWidget(self.conversationEdit)

        self.conversationModifyButton = QPushButton(self.tab_9)
        self.conversationModifyButton.setObjectName("conversationModifyButton")
        sizePolicy2.setHeightForWidth(self.conversationModifyButton.sizePolicy().hasHeightForWidth())
        self.conversationModifyButton.setSizePolicy(sizePolicy2)

        self.horizontalLayout_5.addWidget(self.conversationModifyButton)


        self.formLayout_3.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_5)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_3.setItem(5, QFormLayout.SpanningRole, self.verticalSpacer_2)


        self.gridLayout_3.addLayout(self.formLayout_3, 0, 0, 3, 1)

        self.tabWidget.addTab(self.tab_9, "")
        self.tab_10 = QWidget()
        self.tab_10.setObjectName("tab_10")
        self.verticalLayout = QVBoxLayout(self.tab_10)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_16 = QGroupBox(self.tab_10)
        self.groupBox_16.setObjectName("groupBox_16")
        self.gridLayout = QGridLayout(self.groupBox_16)
        self.gridLayout.setObjectName("gridLayout")
        self.min1HpCheckbox = QCheckBox(self.groupBox_16)
        self.min1HpCheckbox.setObjectName("min1HpCheckbox")

        self.gridLayout.addWidget(self.min1HpCheckbox, 0, 0, 1, 1)

        self.plotCheckbox = QCheckBox(self.groupBox_16)
        self.plotCheckbox.setObjectName("plotCheckbox")

        self.gridLayout.addWidget(self.plotCheckbox, 0, 1, 1, 1)

        self.partyInteractCheckbox = QCheckBox(self.groupBox_16)
        self.partyInteractCheckbox.setObjectName("partyInteractCheckbox")

        self.gridLayout.addWidget(self.partyInteractCheckbox, 1, 0, 1, 1)

        self.staticCheckbox = QCheckBox(self.groupBox_16)
        self.staticCheckbox.setObjectName("staticCheckbox")

        self.gridLayout.addWidget(self.staticCheckbox, 1, 1, 1, 1)

        self.useableCheckbox = QCheckBox(self.groupBox_16)
        self.useableCheckbox.setObjectName("useableCheckbox")

        self.gridLayout.addWidget(self.useableCheckbox, 2, 0, 1, 1)

        self.notBlastableCheckbox = QCheckBox(self.groupBox_16)
        self.notBlastableCheckbox.setObjectName("notBlastableCheckbox")

        self.gridLayout.addWidget(self.notBlastableCheckbox, 2, 1, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_16)

        self.groupBox_17 = QGroupBox(self.tab_10)
        self.groupBox_17.setObjectName("groupBox_17")
        self.formLayout_11 = QFormLayout(self.groupBox_17)
        self.formLayout_11.setObjectName("formLayout_11")
        self.label_41 = QLabel(self.groupBox_17)
        self.label_41.setObjectName("label_41")

        self.formLayout_11.setWidget(0, QFormLayout.LabelRole, self.label_41)

        self.factionSelect = ComboBox2DA(self.groupBox_17)
        self.factionSelect.setObjectName("factionSelect")

        self.formLayout_11.setWidget(0, QFormLayout.FieldRole, self.factionSelect)

        self.label_42 = QLabel(self.groupBox_17)
        self.label_42.setObjectName("label_42")

        self.formLayout_11.setWidget(1, QFormLayout.LabelRole, self.label_42)

        self.animationState = QSpinBox(self.groupBox_17)
        self.animationState.setObjectName("animationState")
        self.animationState.setMinimumSize(QSize(0, 25))
        self.animationState.setMinimum(-2147483648)
        self.animationState.setMaximum(2147483647)

        self.formLayout_11.setWidget(1, QFormLayout.FieldRole, self.animationState)


        self.verticalLayout.addWidget(self.groupBox_17)

        self.widget_4 = QWidget(self.tab_10)
        self.widget_4.setObjectName("widget_4")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.widget_4.sizePolicy().hasHeightForWidth())
        self.widget_4.setSizePolicy(sizePolicy3)
        self.statsLayout = QFormLayout(self.widget_4)
        self.statsLayout.setObjectName("statsLayout")
        self.label_3 = QLabel(self.widget_4)
        self.label_3.setObjectName("label_3")

        self.statsLayout.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.currenHpSpin = QSpinBox(self.widget_4)
        self.currenHpSpin.setObjectName("currenHpSpin")
        self.currenHpSpin.setMinimumSize(QSize(30, 25))
        self.currenHpSpin.setMinimum(-2147483648)
        self.currenHpSpin.setMaximum(2147483647)

        self.statsLayout.setWidget(0, QFormLayout.FieldRole, self.currenHpSpin)

        self.label_26 = QLabel(self.widget_4)
        self.label_26.setObjectName("label_26")

        self.statsLayout.setWidget(1, QFormLayout.LabelRole, self.label_26)

        self.maxHpSpin = QSpinBox(self.widget_4)
        self.maxHpSpin.setObjectName("maxHpSpin")
        self.maxHpSpin.setMinimumSize(QSize(0, 25))
        self.maxHpSpin.setMinimum(-2147483648)
        self.maxHpSpin.setMaximum(2147483647)

        self.statsLayout.setWidget(1, QFormLayout.FieldRole, self.maxHpSpin)

        self.label_20 = QLabel(self.widget_4)
        self.label_20.setObjectName("label_20")

        self.statsLayout.setWidget(2, QFormLayout.LabelRole, self.label_20)

        self.hardnessSpin = QSpinBox(self.widget_4)
        self.hardnessSpin.setObjectName("hardnessSpin")
        self.hardnessSpin.setMinimumSize(QSize(0, 25))
        self.hardnessSpin.setMinimum(-2147483648)
        self.hardnessSpin.setMaximum(2147483647)

        self.statsLayout.setWidget(2, QFormLayout.FieldRole, self.hardnessSpin)

        self.label_21 = QLabel(self.widget_4)
        self.label_21.setObjectName("label_21")

        self.statsLayout.setWidget(3, QFormLayout.LabelRole, self.label_21)

        self.fortitudeSpin = QSpinBox(self.widget_4)
        self.fortitudeSpin.setObjectName("fortitudeSpin")
        self.fortitudeSpin.setMinimumSize(QSize(0, 25))
        self.fortitudeSpin.setMinimum(-2147483648)
        self.fortitudeSpin.setMaximum(2147483647)

        self.statsLayout.setWidget(3, QFormLayout.FieldRole, self.fortitudeSpin)

        self.label_24 = QLabel(self.widget_4)
        self.label_24.setObjectName("label_24")

        self.statsLayout.setWidget(4, QFormLayout.LabelRole, self.label_24)

        self.reflexSpin = QSpinBox(self.widget_4)
        self.reflexSpin.setObjectName("reflexSpin")
        self.reflexSpin.setMinimumSize(QSize(0, 25))
        self.reflexSpin.setMinimum(-2147483648)
        self.reflexSpin.setMaximum(2147483647)

        self.statsLayout.setWidget(4, QFormLayout.FieldRole, self.reflexSpin)

        self.label_25 = QLabel(self.widget_4)
        self.label_25.setObjectName("label_25")

        self.statsLayout.setWidget(5, QFormLayout.LabelRole, self.label_25)

        self.willSpin = QSpinBox(self.widget_4)
        self.willSpin.setObjectName("willSpin")
        self.willSpin.setMinimumSize(QSize(0, 25))
        self.willSpin.setMinimum(-2147483648)
        self.willSpin.setMaximum(2147483647)

        self.statsLayout.setWidget(5, QFormLayout.FieldRole, self.willSpin)


        self.verticalLayout.addWidget(self.widget_4)

        self.tabWidget.addTab(self.tab_10, "")
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_5 = QVBoxLayout(self.tab)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.groupBox_3 = QGroupBox(self.tab)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.needKeyCheckbox = QCheckBox(self.groupBox_3)
        self.needKeyCheckbox.setObjectName("needKeyCheckbox")

        self.verticalLayout_4.addWidget(self.needKeyCheckbox)

        self.removeKeyCheckbox = QCheckBox(self.groupBox_3)
        self.removeKeyCheckbox.setObjectName("removeKeyCheckbox")

        self.verticalLayout_4.addWidget(self.removeKeyCheckbox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName("label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.keyEdit = QLineEdit(self.groupBox_3)
        self.keyEdit.setObjectName("keyEdit")

        self.horizontalLayout.addWidget(self.keyEdit)


        self.verticalLayout_4.addLayout(self.horizontalLayout)


        self.verticalLayout_5.addWidget(self.groupBox_3)

        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.lockedCheckbox = QCheckBox(self.groupBox_2)
        self.lockedCheckbox.setObjectName("lockedCheckbox")

        self.verticalLayout_2.addWidget(self.lockedCheckbox)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.difficultyLabel = QLabel(self.groupBox_2)
        self.difficultyLabel.setObjectName("difficultyLabel")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.difficultyLabel)

        self.difficultyModLabel = QLabel(self.groupBox_2)
        self.difficultyModLabel.setObjectName("difficultyModLabel")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.difficultyModLabel)

        self.openLockSpin = QSpinBox(self.groupBox_2)
        self.openLockSpin.setObjectName("openLockSpin")
        self.openLockSpin.setMinimum(-2147483648)
        self.openLockSpin.setMaximum(2147483647)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.openLockSpin)

        self.difficultySpin = QSpinBox(self.groupBox_2)
        self.difficultySpin.setObjectName("difficultySpin")
        self.difficultySpin.setMinimum(-2147483648)
        self.difficultySpin.setMaximum(2147483647)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.difficultySpin)

        self.difficultyModSpin = QSpinBox(self.groupBox_2)
        self.difficultyModSpin.setObjectName("difficultyModSpin")
        self.difficultyModSpin.setMinimum(-2147483648)
        self.difficultyModSpin.setMaximum(2147483647)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.difficultyModSpin)


        self.verticalLayout_3.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)


        self.verticalLayout_5.addWidget(self.groupBox_2)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.formLayout_2 = QFormLayout(self.tab_2)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_18 = QLabel(self.tab_2)
        self.label_18.setObjectName("label_18")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_18)

        self.onClickEdit = FilterComboBox(self.tab_2)
        self.onClickEdit.setObjectName("onClickEdit")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.onClickEdit)

        self.label_5 = QLabel(self.tab_2)
        self.label_5.setObjectName("label_5")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_5)

        self.onClosedEdit = FilterComboBox(self.tab_2)
        self.onClosedEdit.setObjectName("onClosedEdit")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.onClosedEdit)

        self.label_7 = QLabel(self.tab_2)
        self.label_7.setObjectName("label_7")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_7)

        self.onDamagedEdit = FilterComboBox(self.tab_2)
        self.onDamagedEdit.setObjectName("onDamagedEdit")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.onDamagedEdit)

        self.label_8 = QLabel(self.tab_2)
        self.label_8.setObjectName("label_8")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_8)

        self.onDeathEdit = FilterComboBox(self.tab_2)
        self.onDeathEdit.setObjectName("onDeathEdit")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.onDeathEdit)

        self.label_10 = QLabel(self.tab_2)
        self.label_10.setObjectName("label_10")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.label_10)

        self.onOpenFailedEdit = FilterComboBox(self.tab_2)
        self.onOpenFailedEdit.setObjectName("onOpenFailedEdit")

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.onOpenFailedEdit)

        self.label_11 = QLabel(self.tab_2)
        self.label_11.setObjectName("label_11")

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.label_11)

        self.onHeartbeatSelect = FilterComboBox(self.tab_2)
        self.onHeartbeatSelect.setObjectName("onHeartbeatSelect")

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.onHeartbeatSelect)

        self.label_13 = QLabel(self.tab_2)
        self.label_13.setObjectName("label_13")

        self.formLayout_2.setWidget(6, QFormLayout.LabelRole, self.label_13)

        self.onMeleeAttackEdit = FilterComboBox(self.tab_2)
        self.onMeleeAttackEdit.setObjectName("onMeleeAttackEdit")

        self.formLayout_2.setWidget(6, QFormLayout.FieldRole, self.onMeleeAttackEdit)

        self.label_16 = QLabel(self.tab_2)
        self.label_16.setObjectName("label_16")

        self.formLayout_2.setWidget(7, QFormLayout.LabelRole, self.label_16)

        self.onSpellEdit = FilterComboBox(self.tab_2)
        self.onSpellEdit.setObjectName("onSpellEdit")

        self.formLayout_2.setWidget(7, QFormLayout.FieldRole, self.onSpellEdit)

        self.label_17 = QLabel(self.tab_2)
        self.label_17.setObjectName("label_17")

        self.formLayout_2.setWidget(8, QFormLayout.LabelRole, self.label_17)

        self.onOpenEdit = FilterComboBox(self.tab_2)
        self.onOpenEdit.setObjectName("onOpenEdit")

        self.formLayout_2.setWidget(8, QFormLayout.FieldRole, self.onOpenEdit)

        self.label_23 = QLabel(self.tab_2)
        self.label_23.setObjectName("label_23")

        self.formLayout_2.setWidget(9, QFormLayout.LabelRole, self.label_23)

        self.onUnlockEdit = FilterComboBox(self.tab_2)
        self.onUnlockEdit.setObjectName("onUnlockEdit")

        self.formLayout_2.setWidget(9, QFormLayout.FieldRole, self.onUnlockEdit)

        self.label_19 = QLabel(self.tab_2)
        self.label_19.setObjectName("label_19")

        self.formLayout_2.setWidget(10, QFormLayout.LabelRole, self.label_19)

        self.onUserDefinedSelect = FilterComboBox(self.tab_2)
        self.onUserDefinedSelect.setObjectName("onUserDefinedSelect")

        self.formLayout_2.setWidget(10, QFormLayout.FieldRole, self.onUserDefinedSelect)

        self.tabWidget.addTab(self.tab_2, "")
        self.commentsTab = QWidget()
        self.commentsTab.setObjectName("commentsTab")
        self.gridLayout_4 = QGridLayout(self.commentsTab)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.commentsEdit = QPlainTextEdit(self.commentsTab)
        self.commentsEdit.setObjectName("commentsEdit")

        self.gridLayout_4.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.commentsTab, "")

        self.horizontalLayout_2.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 654, 21))
        self.menuNew = QMenu(self.menubar)
        self.menuNew.setObjectName("menuNew")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionShowPreview.setText(QCoreApplication.translate("MainWindow", "Show Preview", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", "Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", "Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", "-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", "ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", "-", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", "Appearance:", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Conversation:", None))
        self.conversationModifyButton.setText(QCoreApplication.translate("MainWindow", "Edit", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_9), QCoreApplication.translate("MainWindow", "Basic", None))
        self.groupBox_16.setTitle(QCoreApplication.translate("MainWindow", "Flags", None))
        self.min1HpCheckbox.setText(QCoreApplication.translate("MainWindow", "Min1HP", None))
        self.plotCheckbox.setText(QCoreApplication.translate("MainWindow", "Plot", None))
        self.partyInteractCheckbox.setText(QCoreApplication.translate("MainWindow", "Party Interact", None))
        self.staticCheckbox.setText(QCoreApplication.translate("MainWindow", "Static", None))
        self.useableCheckbox.setText(QCoreApplication.translate("MainWindow", "Useable", None))
        self.notBlastableCheckbox.setText(QCoreApplication.translate("MainWindow", "Not Blastable", None))
        self.groupBox_17.setTitle(QCoreApplication.translate("MainWindow", "Other", None))
        self.label_41.setText(QCoreApplication.translate("MainWindow", "Faction:", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", "Animation State:", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", "Current HP:", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", "Max HP:", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", "Hardness:", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", "Fortitude:", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", "Reflex:", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", "Will:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_10), QCoreApplication.translate("MainWindow", "Advanced", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", "Key", None))
        self.needKeyCheckbox.setText(QCoreApplication.translate("MainWindow", "Key required to unlock", None))
        self.removeKeyCheckbox.setText(QCoreApplication.translate("MainWindow", "Remove key on unlock", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", "Key Tag:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", "Lock", None))
        self.lockedCheckbox.setText(QCoreApplication.translate("MainWindow", "Locked", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", "Open Lock DC:", None))
        self.difficultyLabel.setText(QCoreApplication.translate("MainWindow", "Difficulty:", None))
        self.difficultyModLabel.setText(QCoreApplication.translate("MainWindow", "Difficulty Mod:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", "Lock", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", "OnClicked:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", "OnClosed:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", "OnDamaged:", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", "OnDeath:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", "OnOpenFailed:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", "OnHeartbeat:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", "OnMeleeAttack:", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", "OnSpellCastAt:", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", "OnOpen:", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", "OnUnlock:", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", "OnUserDefined:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", "Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentsTab), QCoreApplication.translate("MainWindow", "Comments", None))
        self.menuNew.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", "View", None))
    # retranslateUi

