# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'are.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTabWidget, QVBoxLayout,
    QWidget)

from toolset.gui.widgets.edit.color import ColorEdit
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(393, 479)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName(u"actionSaveAs")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName(u"actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_8 = QVBoxLayout(self.tab)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.groupBox_7 = QGroupBox(self.tab)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.gridLayout_6 = QGridLayout(self.groupBox_7)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.formLayout_7 = QFormLayout()
        self.formLayout_7.setObjectName(u"formLayout_7")
        self.label_20 = QLabel(self.groupBox_7)
        self.label_20.setObjectName(u"label_20")

        self.formLayout_7.setWidget(0, QFormLayout.LabelRole, self.label_20)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.nameEdit = LocalizedStringLineEdit(self.groupBox_7)
        self.nameEdit.setObjectName(u"nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_14.addWidget(self.nameEdit)


        self.formLayout_7.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_14)

        self.label_21 = QLabel(self.groupBox_7)
        self.label_21.setObjectName(u"label_21")

        self.formLayout_7.setWidget(1, QFormLayout.LabelRole, self.label_21)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.tagEdit = QLineEdit(self.groupBox_7)
        self.tagEdit.setObjectName(u"tagEdit")

        self.horizontalLayout_15.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.groupBox_7)
        self.tagGenerateButton.setObjectName(u"tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_15.addWidget(self.tagGenerateButton)


        self.formLayout_7.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_15)

        self.label_22 = QLabel(self.groupBox_7)
        self.label_22.setObjectName(u"label_22")

        self.formLayout_7.setWidget(2, QFormLayout.LabelRole, self.label_22)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.cameraStyleSelect = ComboBox2DA(self.groupBox_7)
        self.cameraStyleSelect.setObjectName(u"cameraStyleSelect")

        self.horizontalLayout_16.addWidget(self.cameraStyleSelect)

        self.horizontalSpacer_5 = QSpacerItem(32, 17, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_5)


        self.formLayout_7.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.envmapEdit = QLineEdit(self.groupBox_7)
        self.envmapEdit.setObjectName(u"envmapEdit")
        self.envmapEdit.setMaxLength(16)

        self.horizontalLayout_17.addWidget(self.envmapEdit)

        self.horizontalSpacer_4 = QSpacerItem(32, 17, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_4)


        self.formLayout_7.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_17)

        self.label_23 = QLabel(self.groupBox_7)
        self.label_23.setObjectName(u"label_23")

        self.formLayout_7.setWidget(3, QFormLayout.LabelRole, self.label_23)


        self.gridLayout_6.addLayout(self.formLayout_7, 0, 0, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_7)

        self.groupBox_8 = QGroupBox(self.tab)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.verticalLayout_6 = QVBoxLayout(self.groupBox_8)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.disableTransitCheck = QCheckBox(self.groupBox_8)
        self.disableTransitCheck.setObjectName(u"disableTransitCheck")

        self.verticalLayout_6.addWidget(self.disableTransitCheck)

        self.unescapableCheck = QCheckBox(self.groupBox_8)
        self.unescapableCheck.setObjectName(u"unescapableCheck")

        self.verticalLayout_6.addWidget(self.unescapableCheck)

        self.formLayout_8 = QFormLayout()
        self.formLayout_8.setObjectName(u"formLayout_8")
        self.label_24 = QLabel(self.groupBox_8)
        self.label_24.setObjectName(u"label_24")

        self.formLayout_8.setWidget(0, QFormLayout.LabelRole, self.label_24)

        self.alphaTestSpin = QDoubleSpinBox(self.groupBox_8)
        self.alphaTestSpin.setObjectName(u"alphaTestSpin")
        self.alphaTestSpin.setMinimum(-100.000000000000000)
        self.alphaTestSpin.setMaximum(10000.000000000000000)

        self.formLayout_8.setWidget(0, QFormLayout.FieldRole, self.alphaTestSpin)


        self.verticalLayout_6.addLayout(self.formLayout_8)


        self.verticalLayout_8.addWidget(self.groupBox_8)

        self.groupBox_9 = QGroupBox(self.tab)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.verticalLayout_7 = QVBoxLayout(self.groupBox_9)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.stealthCheck = QCheckBox(self.groupBox_9)
        self.stealthCheck.setObjectName(u"stealthCheck")

        self.verticalLayout_7.addWidget(self.stealthCheck)

        self.formLayout_9 = QFormLayout()
        self.formLayout_9.setObjectName(u"formLayout_9")
        self.label_25 = QLabel(self.groupBox_9)
        self.label_25.setObjectName(u"label_25")

        self.formLayout_9.setWidget(0, QFormLayout.LabelRole, self.label_25)

        self.stealthMaxSpin = QSpinBox(self.groupBox_9)
        self.stealthMaxSpin.setObjectName(u"stealthMaxSpin")
        self.stealthMaxSpin.setMaximum(100000)

        self.formLayout_9.setWidget(0, QFormLayout.FieldRole, self.stealthMaxSpin)

        self.label_26 = QLabel(self.groupBox_9)
        self.label_26.setObjectName(u"label_26")

        self.formLayout_9.setWidget(1, QFormLayout.LabelRole, self.label_26)

        self.stealthLossSpin = QSpinBox(self.groupBox_9)
        self.stealthLossSpin.setObjectName(u"stealthLossSpin")
        self.stealthLossSpin.setMaximum(100000)

        self.formLayout_9.setWidget(1, QFormLayout.FieldRole, self.stealthLossSpin)


        self.verticalLayout_7.addLayout(self.formLayout_9)


        self.verticalLayout_8.addWidget(self.groupBox_9)

        self.verticalSpacer_3 = QSpacerItem(20, 23, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.tab, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.verticalLayout_9 = QVBoxLayout(self.tab_6)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.formLayout_11 = QFormLayout()
        self.formLayout_11.setObjectName(u"formLayout_11")
        self.label_34 = QLabel(self.tab_6)
        self.label_34.setObjectName(u"label_34")

        self.formLayout_11.setWidget(0, QFormLayout.LabelRole, self.label_34)

        self.mapAxisSelect = QComboBox(self.tab_6)
        self.mapAxisSelect.addItem("")
        self.mapAxisSelect.addItem("")
        self.mapAxisSelect.addItem("")
        self.mapAxisSelect.addItem("")
        self.mapAxisSelect.setObjectName(u"mapAxisSelect")

        self.formLayout_11.setWidget(0, QFormLayout.FieldRole, self.mapAxisSelect)

        self.label_35 = QLabel(self.tab_6)
        self.label_35.setObjectName(u"label_35")

        self.formLayout_11.setWidget(1, QFormLayout.LabelRole, self.label_35)

        self.mapZoomSpin = QSpinBox(self.tab_6)
        self.mapZoomSpin.setObjectName(u"mapZoomSpin")
        self.mapZoomSpin.setMaximum(1000000)

        self.formLayout_11.setWidget(1, QFormLayout.FieldRole, self.mapZoomSpin)

        self.label_40 = QLabel(self.tab_6)
        self.label_40.setObjectName(u"label_40")

        self.formLayout_11.setWidget(2, QFormLayout.LabelRole, self.label_40)

        self.mapResXSpin = QSpinBox(self.tab_6)
        self.mapResXSpin.setObjectName(u"mapResXSpin")
        self.mapResXSpin.setMaximum(1000000)

        self.formLayout_11.setWidget(2, QFormLayout.FieldRole, self.mapResXSpin)


        self.verticalLayout_9.addLayout(self.formLayout_11)

        self.groupBox_10 = QGroupBox(self.tab_6)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.gridLayout_7 = QGridLayout(self.groupBox_10)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.formLayout_10 = QFormLayout()
        self.formLayout_10.setObjectName(u"formLayout_10")
        self.label_27 = QLabel(self.groupBox_10)
        self.label_27.setObjectName(u"label_27")

        self.formLayout_10.setWidget(1, QFormLayout.LabelRole, self.label_27)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.mapImageX1Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapImageX1Spin.setObjectName(u"mapImageX1Spin")
        self.mapImageX1Spin.setMinimum(-100000.000000000000000)
        self.mapImageX1Spin.setMaximum(100000.000000000000000)

        self.horizontalLayout_19.addWidget(self.mapImageX1Spin)

        self.mapImageY1Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapImageY1Spin.setObjectName(u"mapImageY1Spin")
        self.mapImageY1Spin.setMinimum(-100000.000000000000000)
        self.mapImageY1Spin.setMaximum(100000.000000000000000)
        self.mapImageY1Spin.setSingleStep(1.000000000000000)

        self.horizontalLayout_19.addWidget(self.mapImageY1Spin)


        self.formLayout_10.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_19)

        self.label_28 = QLabel(self.groupBox_10)
        self.label_28.setObjectName(u"label_28")

        self.formLayout_10.setWidget(2, QFormLayout.LabelRole, self.label_28)

        self.label_29 = QLabel(self.groupBox_10)
        self.label_29.setObjectName(u"label_29")

        self.formLayout_10.setWidget(3, QFormLayout.LabelRole, self.label_29)

        self.label_30 = QLabel(self.groupBox_10)
        self.label_30.setObjectName(u"label_30")

        self.formLayout_10.setWidget(4, QFormLayout.LabelRole, self.label_30)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.mapWorldX1Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapWorldX1Spin.setObjectName(u"mapWorldX1Spin")
        self.mapWorldX1Spin.setMinimum(-100000.000000000000000)
        self.mapWorldX1Spin.setMaximum(100000.000000000000000)

        self.horizontalLayout_20.addWidget(self.mapWorldX1Spin)

        self.mapWorldY1Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapWorldY1Spin.setObjectName(u"mapWorldY1Spin")
        self.mapWorldY1Spin.setMinimum(-100000.000000000000000)
        self.mapWorldY1Spin.setMaximum(100000.000000000000000)

        self.horizontalLayout_20.addWidget(self.mapWorldY1Spin)


        self.formLayout_10.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_20)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.mapImageX2Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapImageX2Spin.setObjectName(u"mapImageX2Spin")
        self.mapImageX2Spin.setMinimum(-100000.000000000000000)
        self.mapImageX2Spin.setMaximum(100000.000000000000000)

        self.horizontalLayout_21.addWidget(self.mapImageX2Spin)

        self.mapImageY2Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapImageY2Spin.setObjectName(u"mapImageY2Spin")
        self.mapImageY2Spin.setMinimum(-100000.000000000000000)
        self.mapImageY2Spin.setMaximum(100000.000000000000000)

        self.horizontalLayout_21.addWidget(self.mapImageY2Spin)


        self.formLayout_10.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_21)

        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.mapWorldX2Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapWorldX2Spin.setObjectName(u"mapWorldX2Spin")
        self.mapWorldX2Spin.setMinimum(-100000.000000000000000)
        self.mapWorldX2Spin.setMaximum(100000.000000000000000)

        self.horizontalLayout_22.addWidget(self.mapWorldX2Spin)

        self.mapWorldY2Spin = QDoubleSpinBox(self.groupBox_10)
        self.mapWorldY2Spin.setObjectName(u"mapWorldY2Spin")
        self.mapWorldY2Spin.setMinimum(-1000000.000000000000000)
        self.mapWorldY2Spin.setMaximum(100000.000000000000000)

        self.horizontalLayout_22.addWidget(self.mapWorldY2Spin)


        self.formLayout_10.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_22)

        self.label_31 = QLabel(self.groupBox_10)
        self.label_31.setObjectName(u"label_31")

        self.formLayout_10.setWidget(0, QFormLayout.LabelRole, self.label_31)

        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.label_32 = QLabel(self.groupBox_10)
        self.label_32.setObjectName(u"label_32")

        self.horizontalLayout_23.addWidget(self.label_32)

        self.label_33 = QLabel(self.groupBox_10)
        self.label_33.setObjectName(u"label_33")

        self.horizontalLayout_23.addWidget(self.label_33)

        self.horizontalLayout_23.setStretch(0, 1)
        self.horizontalLayout_23.setStretch(1, 1)

        self.formLayout_10.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_23)


        self.gridLayout_7.addLayout(self.formLayout_10, 0, 0, 1, 1)


        self.verticalLayout_9.addWidget(self.groupBox_10)

        self.minimapRenderer = WalkmeshRenderer(self.tab_6)
        self.minimapRenderer.setObjectName(u"minimapRenderer")
        self.minimapRenderer.setMinimumSize(QSize(0, 150))

        self.verticalLayout_9.addWidget(self.minimapRenderer)

        self.verticalSpacer_4 = QSpacerItem(20, 171, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer_4)

        self.tabWidget.addTab(self.tab_6, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_5 = QVBoxLayout(self.tab_3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox_3 = QGroupBox(self.tab_3)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.fogEnabledCheck = QCheckBox(self.groupBox_3)
        self.fogEnabledCheck.setObjectName(u"fogEnabledCheck")

        self.verticalLayout_2.addWidget(self.fogEnabledCheck)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.fogColorEdit = ColorEdit(self.groupBox_3)
        self.fogColorEdit.setObjectName(u"fogColorEdit")
        self.fogColorEdit.setMinimumSize(QSize(0, 20))
        self.fogColorEdit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_9.addWidget(self.fogColorEdit)


        self.formLayout_3.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_9)

        self.label_12 = QLabel(self.groupBox_3)
        self.label_12.setObjectName(u"label_12")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_12)

        self.fogNearSpin = QDoubleSpinBox(self.groupBox_3)
        self.fogNearSpin.setObjectName(u"fogNearSpin")
        self.fogNearSpin.setMaximum(1000.000000000000000)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.fogNearSpin)

        self.label_13 = QLabel(self.groupBox_3)
        self.label_13.setObjectName(u"label_13")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_13)

        self.fogFarSpin = QDoubleSpinBox(self.groupBox_3)
        self.fogFarSpin.setObjectName(u"fogFarSpin")
        self.fogFarSpin.setMaximum(1000.000000000000000)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.fogFarSpin)

        self.label_14 = QLabel(self.groupBox_3)
        self.label_14.setObjectName(u"label_14")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_14)


        self.verticalLayout_2.addLayout(self.formLayout_3)


        self.verticalLayout_5.addWidget(self.groupBox_3)

        self.groupBox_6 = QGroupBox(self.tab_3)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.gridLayout_4 = QGridLayout(self.groupBox_6)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.label_16 = QLabel(self.groupBox_6)
        self.label_16.setObjectName(u"label_16")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_16)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.ambientColorEdit = ColorEdit(self.groupBox_6)
        self.ambientColorEdit.setObjectName(u"ambientColorEdit")
        self.ambientColorEdit.setMinimumSize(QSize(0, 20))
        self.ambientColorEdit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_11.addWidget(self.ambientColorEdit)


        self.formLayout_5.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_11)

        self.label_19 = QLabel(self.groupBox_6)
        self.label_19.setObjectName(u"label_19")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_19)

        self.label_18 = QLabel(self.groupBox_6)
        self.label_18.setObjectName(u"label_18")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_18)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.diffuseColorEdit = ColorEdit(self.groupBox_6)
        self.diffuseColorEdit.setObjectName(u"diffuseColorEdit")
        self.diffuseColorEdit.setMinimumSize(QSize(0, 20))
        self.diffuseColorEdit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_12.addWidget(self.diffuseColorEdit)


        self.formLayout_5.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.dynamicColorEdit = ColorEdit(self.groupBox_6)
        self.dynamicColorEdit.setObjectName(u"dynamicColorEdit")
        self.dynamicColorEdit.setMinimumSize(QSize(0, 20))
        self.dynamicColorEdit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_13.addWidget(self.dynamicColorEdit)


        self.formLayout_5.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_13)


        self.gridLayout_4.addLayout(self.formLayout_5, 0, 0, 1, 1)


        self.verticalLayout_5.addWidget(self.groupBox_6)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.groupBox_4 = QGroupBox(self.tab_3)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.formLayout_6 = QFormLayout()
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.label_17 = QLabel(self.groupBox_4)
        self.label_17.setObjectName(u"label_17")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_17)

        self.windPowerSelect = QComboBox(self.groupBox_4)
        self.windPowerSelect.addItem("")
        self.windPowerSelect.addItem("")
        self.windPowerSelect.addItem("")
        self.windPowerSelect.setObjectName(u"windPowerSelect")

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.windPowerSelect)


        self.verticalLayout_3.addLayout(self.formLayout_6)

        self.rainCheck = QCheckBox(self.groupBox_4)
        self.rainCheck.setObjectName(u"rainCheck")

        self.verticalLayout_3.addWidget(self.rainCheck)

        self.snowCheck = QCheckBox(self.groupBox_4)
        self.snowCheck.setObjectName(u"snowCheck")

        self.verticalLayout_3.addWidget(self.snowCheck)

        self.lightningCheck = QCheckBox(self.groupBox_4)
        self.lightningCheck.setObjectName(u"lightningCheck")

        self.verticalLayout_3.addWidget(self.lightningCheck)


        self.horizontalLayout_10.addWidget(self.groupBox_4)

        self.groupBox_5 = QGroupBox(self.tab_3)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.shadowsCheck = QCheckBox(self.groupBox_5)
        self.shadowsCheck.setObjectName(u"shadowsCheck")

        self.verticalLayout_4.addWidget(self.shadowsCheck)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_15 = QLabel(self.groupBox_5)
        self.label_15.setObjectName(u"label_15")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_15)

        self.shadowsSpin = QSpinBox(self.groupBox_5)
        self.shadowsSpin.setObjectName(u"shadowsSpin")
        self.shadowsSpin.setMaximum(255)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.shadowsSpin)


        self.verticalLayout_4.addLayout(self.formLayout_4)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.spacer)


        self.horizontalLayout_10.addWidget(self.groupBox_5)


        self.verticalLayout_5.addLayout(self.horizontalLayout_10)

        self.verticalSpacer_2 = QSpacerItem(20, 19, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout = QVBoxLayout(self.tab_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(self.tab_2)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.grassTextureEdit = QLineEdit(self.groupBox)
        self.grassTextureEdit.setObjectName(u"grassTextureEdit")
        self.grassTextureEdit.setMaxLength(16)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.grassTextureEdit)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.grassDiffuseEdit = ColorEdit(self.groupBox)
        self.grassDiffuseEdit.setObjectName(u"grassDiffuseEdit")
        self.grassDiffuseEdit.setMinimumSize(QSize(0, 20))
        self.grassDiffuseEdit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout.addWidget(self.grassDiffuseEdit)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout)

        self.grassEmissiveLabel = QLabel(self.groupBox)
        self.grassEmissiveLabel.setObjectName(u"grassEmissiveLabel")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.grassEmissiveLabel)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.grassEmissiveEdit = ColorEdit(self.groupBox)
        self.grassEmissiveEdit.setObjectName(u"grassEmissiveEdit")
        self.grassEmissiveEdit.setMinimumSize(QSize(0, 20))
        self.grassEmissiveEdit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_2.addWidget(self.grassEmissiveEdit)


        self.formLayout.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_2)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.grassAmbientEdit = ColorEdit(self.groupBox)
        self.grassAmbientEdit.setObjectName(u"grassAmbientEdit")
        self.grassAmbientEdit.setMinimumSize(QSize(0, 20))
        self.grassAmbientEdit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_3.addWidget(self.grassAmbientEdit)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_3)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_5)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_6)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_7)

        self.grassDensitySpin = QDoubleSpinBox(self.groupBox)
        self.grassDensitySpin.setObjectName(u"grassDensitySpin")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.grassDensitySpin)

        self.grassSizeSpin = QDoubleSpinBox(self.groupBox)
        self.grassSizeSpin.setObjectName(u"grassSizeSpin")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.grassSizeSpin)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.grassProbULSpin = QDoubleSpinBox(self.groupBox)
        self.grassProbULSpin.setObjectName(u"grassProbULSpin")

        self.horizontalLayout_4.addWidget(self.grassProbULSpin)

        self.grassProbURSpin = QDoubleSpinBox(self.groupBox)
        self.grassProbURSpin.setObjectName(u"grassProbURSpin")

        self.horizontalLayout_4.addWidget(self.grassProbURSpin)

        self.grassProbLLSpin = QDoubleSpinBox(self.groupBox)
        self.grassProbLLSpin.setObjectName(u"grassProbLLSpin")

        self.horizontalLayout_4.addWidget(self.grassProbLLSpin)

        self.grassProbLRSpin = QDoubleSpinBox(self.groupBox)
        self.grassProbLRSpin.setObjectName(u"grassProbLRSpin")

        self.horizontalLayout_4.addWidget(self.grassProbLRSpin)


        self.formLayout.setLayout(6, QFormLayout.FieldRole, self.horizontalLayout_4)


        self.gridLayout_2.addLayout(self.formLayout, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox)

        self.dirtGroup = QGroupBox(self.tab_2)
        self.dirtGroup.setObjectName(u"dirtGroup")
        self.gridLayout_3 = QGridLayout(self.dirtGroup)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_8 = QLabel(self.dirtGroup)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_25 = QHBoxLayout()
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.dirtColor1Edit = ColorEdit(self.dirtGroup)
        self.dirtColor1Edit.setObjectName(u"dirtColor1Edit")
        self.dirtColor1Edit.setMinimumSize(QSize(0, 20))
        self.dirtColor1Edit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_25.addWidget(self.dirtColor1Edit)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_25)

        self.horizontalLayout_24 = QHBoxLayout()
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.dirtColor2Edit = ColorEdit(self.dirtGroup)
        self.dirtColor2Edit.setObjectName(u"dirtColor2Edit")
        self.dirtColor2Edit.setMinimumSize(QSize(0, 20))
        self.dirtColor2Edit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_24.addWidget(self.dirtColor2Edit)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_24)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.dirtColor3Edit = ColorEdit(self.dirtGroup)
        self.dirtColor3Edit.setObjectName(u"dirtColor3Edit")
        self.dirtColor3Edit.setMinimumSize(QSize(0, 20))
        self.dirtColor3Edit.setMaximumSize(QSize(16777215, 20))

        self.horizontalLayout_18.addWidget(self.dirtColor3Edit)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_18)


        self.formLayout_2.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_5)

        self.label_9 = QLabel(self.dirtGroup)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_9)

        self.label_10 = QLabel(self.dirtGroup)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_10)

        self.label_11 = QLabel(self.dirtGroup)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_11)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.dirtFormula1Spin = QSpinBox(self.dirtGroup)
        self.dirtFormula1Spin.setObjectName(u"dirtFormula1Spin")
        self.dirtFormula1Spin.setMaximum(2147483647)

        self.horizontalLayout_6.addWidget(self.dirtFormula1Spin)

        self.dirtFormula2Spin = QSpinBox(self.dirtGroup)
        self.dirtFormula2Spin.setObjectName(u"dirtFormula2Spin")
        self.dirtFormula2Spin.setMaximum(2147483647)

        self.horizontalLayout_6.addWidget(self.dirtFormula2Spin)

        self.dirtFormula3Spin = QSpinBox(self.dirtGroup)
        self.dirtFormula3Spin.setObjectName(u"dirtFormula3Spin")
        self.dirtFormula3Spin.setMaximum(2147483647)

        self.horizontalLayout_6.addWidget(self.dirtFormula3Spin)


        self.formLayout_2.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.dirtFunction1Spin = QSpinBox(self.dirtGroup)
        self.dirtFunction1Spin.setObjectName(u"dirtFunction1Spin")
        self.dirtFunction1Spin.setMaximum(2147483647)

        self.horizontalLayout_7.addWidget(self.dirtFunction1Spin)

        self.dirtFunction2Spin = QSpinBox(self.dirtGroup)
        self.dirtFunction2Spin.setObjectName(u"dirtFunction2Spin")
        self.dirtFunction2Spin.setMaximum(2147483647)

        self.horizontalLayout_7.addWidget(self.dirtFunction2Spin)

        self.dirtFunction3Spin = QSpinBox(self.dirtGroup)
        self.dirtFunction3Spin.setObjectName(u"dirtFunction3Spin")
        self.dirtFunction3Spin.setMaximum(2147483647)

        self.horizontalLayout_7.addWidget(self.dirtFunction3Spin)


        self.formLayout_2.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.dirtSize1Spin = QSpinBox(self.dirtGroup)
        self.dirtSize1Spin.setObjectName(u"dirtSize1Spin")
        self.dirtSize1Spin.setMaximum(2147483647)

        self.horizontalLayout_8.addWidget(self.dirtSize1Spin)

        self.dirtSize2Spin = QSpinBox(self.dirtGroup)
        self.dirtSize2Spin.setObjectName(u"dirtSize2Spin")
        self.dirtSize2Spin.setMaximum(2147483647)

        self.horizontalLayout_8.addWidget(self.dirtSize2Spin)

        self.dirtSize3Spin = QSpinBox(self.dirtGroup)
        self.dirtSize3Spin.setObjectName(u"dirtSize3Spin")
        self.dirtSize3Spin.setMaximum(2147483647)

        self.horizontalLayout_8.addWidget(self.dirtSize3Spin)


        self.formLayout_2.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_8)


        self.gridLayout_3.addLayout(self.formLayout_2, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.dirtGroup)

        self.verticalSpacer = QSpacerItem(20, 21, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayout_10 = QVBoxLayout(self.tab_4)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.formLayout_12 = QFormLayout()
        self.formLayout_12.setObjectName(u"formLayout_12")
        self.label_36 = QLabel(self.tab_4)
        self.label_36.setObjectName(u"label_36")

        self.formLayout_12.setWidget(0, QFormLayout.LabelRole, self.label_36)

        self.onEnterEdit = QLineEdit(self.tab_4)
        self.onEnterEdit.setObjectName(u"onEnterEdit")
        self.onEnterEdit.setMaxLength(16)

        self.formLayout_12.setWidget(0, QFormLayout.FieldRole, self.onEnterEdit)

        self.label_37 = QLabel(self.tab_4)
        self.label_37.setObjectName(u"label_37")

        self.formLayout_12.setWidget(1, QFormLayout.LabelRole, self.label_37)

        self.label_38 = QLabel(self.tab_4)
        self.label_38.setObjectName(u"label_38")

        self.formLayout_12.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.label_39 = QLabel(self.tab_4)
        self.label_39.setObjectName(u"label_39")

        self.formLayout_12.setWidget(3, QFormLayout.LabelRole, self.label_39)

        self.onExitEdit = QLineEdit(self.tab_4)
        self.onExitEdit.setObjectName(u"onExitEdit")
        self.onExitEdit.setMaxLength(16)

        self.formLayout_12.setWidget(1, QFormLayout.FieldRole, self.onExitEdit)

        self.onHeartbeatEdit = QLineEdit(self.tab_4)
        self.onHeartbeatEdit.setObjectName(u"onHeartbeatEdit")
        self.onHeartbeatEdit.setMaxLength(16)

        self.formLayout_12.setWidget(2, QFormLayout.FieldRole, self.onHeartbeatEdit)

        self.onUserDefinedEdit = QLineEdit(self.tab_4)
        self.onUserDefinedEdit.setObjectName(u"onUserDefinedEdit")
        self.onUserDefinedEdit.setMaxLength(16)

        self.formLayout_12.setWidget(3, QFormLayout.FieldRole, self.onUserDefinedEdit)


        self.verticalLayout_10.addLayout(self.formLayout_12)

        self.verticalSpacer_5 = QSpacerItem(20, 287, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_5)

        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.gridLayout_5 = QGridLayout(self.tab_5)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.commentsEdit = QPlainTextEdit(self.tab_5)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.gridLayout_5.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_5, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 393, 22))
        self.menuNew = QMenu(self.menubar)
        self.menuNew.setObjectName(u"menuNew")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuNew.menuAction())
        self.menuNew.addAction(self.actionNew)
        self.menuNew.addAction(self.actionOpen)
        self.menuNew.addAction(self.actionSave)
        self.menuNew.addAction(self.actionSaveAs)
        self.menuNew.addAction(self.actionRevert)
        self.menuNew.addSeparator()
        self.menuNew.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("MainWindow", u"Basic", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"Camera:", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Default Envmap:", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.disableTransitCheck.setText(QCoreApplication.translate("MainWindow", u"Disable Transit", None))
        self.unescapableCheck.setText(QCoreApplication.translate("MainWindow", u"Unescapable", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"Alpha Test:", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("MainWindow", u"Stealth XP Bonus", None))
        self.stealthCheck.setText(QCoreApplication.translate("MainWindow", u"Enabled", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Max:", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"Loss:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Basic", None))
        self.label_34.setText(QCoreApplication.translate("MainWindow", u"North Axis:", None))
        self.mapAxisSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"Positive Y", None))
        self.mapAxisSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Negative Y", None))
        self.mapAxisSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Positive X", None))
        self.mapAxisSelect.setItemText(3, QCoreApplication.translate("MainWindow", u"Negative X", None))

        self.label_35.setText(QCoreApplication.translate("MainWindow", u"Map Zoom:", None))
        self.label_40.setText(QCoreApplication.translate("MainWindow", u"Map Res X", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("MainWindow", u"Coordinates", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Map Point 1:", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", u"Map Point 2:", None))
        self.label_29.setText(QCoreApplication.translate("MainWindow", u"World Point 1:", None))
        self.label_30.setText(QCoreApplication.translate("MainWindow", u"World Point 2:", None))
        self.label_31.setText("")
        self.label_32.setText(QCoreApplication.translate("MainWindow", u"X", None))
        self.label_33.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), QCoreApplication.translate("MainWindow", u"Map", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Fog", None))
        self.fogEnabledCheck.setText(QCoreApplication.translate("MainWindow", u"Enabled", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Near Distance:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Far Distance:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Color:", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Lighting", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Ambient:", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"Diffuse:", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Dynamic:", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Weather Effects", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Wind:", None))
        self.windPowerSelect.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))
        self.windPowerSelect.setItemText(1, QCoreApplication.translate("MainWindow", u"Weak", None))
        self.windPowerSelect.setItemText(2, QCoreApplication.translate("MainWindow", u"Strong", None))

        self.rainCheck.setText(QCoreApplication.translate("MainWindow", u"Rain", None))
        self.snowCheck.setText(QCoreApplication.translate("MainWindow", u"Snow", None))
        self.lightningCheck.setText(QCoreApplication.translate("MainWindow", u"Lightning", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Shadows", None))
        self.shadowsCheck.setText(QCoreApplication.translate("MainWindow", u"Enabled", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"Opacity:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Weather", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Grass", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Texture:", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Diffuse:", None))
        self.grassEmissiveLabel.setText(QCoreApplication.translate("MainWindow", u"Emissive:", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Ambient:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Density:", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Size:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Probability:", None))
        self.dirtGroup.setTitle(QCoreApplication.translate("MainWindow", u"Dirt", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Color:", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Formula:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Function:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Size:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Terrain", None))
        self.label_36.setText(QCoreApplication.translate("MainWindow", u"OnEnter:", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", u"OnExit:", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"OnHearbeat:", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", u"OnUserDefined:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", u"Comments", None))
        self.menuNew.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
