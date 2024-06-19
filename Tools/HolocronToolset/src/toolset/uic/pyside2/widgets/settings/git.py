# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'git.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.set_bind import SetBindWidget
from toolset.gui.widgets.edit.color import ColorEdit


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(466, 773)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(Form)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 429, 952))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.controlsResetButton = QPushButton(self.groupBox)
        self.controlsResetButton.setObjectName(u"controlsResetButton")

        self.horizontalLayout_3.addWidget(self.controlsResetButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.widget = QWidget(self.groupBox)
        self.widget.setObjectName(u"widget")
        self.widget.setMinimumSize(QSize(0, 200))
        self.formLayout = QFormLayout(self.widget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setVerticalSpacing(10)
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.moveCameraBindEdit = SetBindWidget(self.widget)
        self.moveCameraBindEdit.setObjectName(u"moveCameraBindEdit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.moveCameraBindEdit)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.rotateCameraBindEdit = SetBindWidget(self.widget)
        self.rotateCameraBindEdit.setObjectName(u"rotateCameraBindEdit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.rotateCameraBindEdit)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.zoomCameraBindEdit = SetBindWidget(self.widget)
        self.zoomCameraBindEdit.setObjectName(u"zoomCameraBindEdit")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.zoomCameraBindEdit)

        self.label_5 = QLabel(self.widget)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_5)

        self.selectUnderneathBindEdit = SetBindWidget(self.widget)
        self.selectUnderneathBindEdit.setObjectName(u"selectUnderneathBindEdit")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.selectUnderneathBindEdit)

        self.label_4 = QLabel(self.widget)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.rotateSelectedToPointBindEdit = SetBindWidget(self.widget)
        self.rotateSelectedToPointBindEdit.setObjectName(u"rotateSelectedToPointBindEdit")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.rotateSelectedToPointBindEdit)

        self.label_6 = QLabel(self.widget)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_6)

        self.deleteSelectedBindEdit = SetBindWidget(self.widget)
        self.deleteSelectedBindEdit.setObjectName(u"deleteSelectedBindEdit")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.deleteSelectedBindEdit)

        self.label_7 = QLabel(self.widget)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_7)

        self.duplicateSelectedBindEdit = SetBindWidget(self.widget)
        self.duplicateSelectedBindEdit.setObjectName(u"duplicateSelectedBindEdit")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.duplicateSelectedBindEdit)

        self.label_8 = QLabel(self.widget)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_8)

        self.toggleLockInstancesBindEdit = SetBindWidget(self.widget)
        self.toggleLockInstancesBindEdit.setObjectName(u"toggleLockInstancesBindEdit")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.toggleLockInstancesBindEdit)


        self.verticalLayout_2.addWidget(self.widget)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setMinimumSize(QSize(0, 660))
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setVerticalSpacing(10)
        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_10)

        self.undefinedMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.undefinedMaterialColourEdit.setObjectName(u"undefinedMaterialColourEdit")
        self.undefinedMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.undefinedMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.undefinedMaterialColourEdit)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.label_12 = QLabel(self.groupBox_2)
        self.label_12.setObjectName(u"label_12")

        self.formLayout_2.setWidget(14, QFormLayout.LabelRole, self.label_12)

        self.label_13 = QLabel(self.groupBox_2)
        self.label_13.setObjectName(u"label_13")

        self.formLayout_2.setWidget(13, QFormLayout.LabelRole, self.label_13)

        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName(u"label_14")

        self.formLayout_2.setWidget(12, QFormLayout.LabelRole, self.label_14)

        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName(u"label_15")

        self.formLayout_2.setWidget(11, QFormLayout.LabelRole, self.label_15)

        self.label_16 = QLabel(self.groupBox_2)
        self.label_16.setObjectName(u"label_16")

        self.formLayout_2.setWidget(10, QFormLayout.LabelRole, self.label_16)

        self.label_17 = QLabel(self.groupBox_2)
        self.label_17.setObjectName(u"label_17")

        self.formLayout_2.setWidget(9, QFormLayout.LabelRole, self.label_17)

        self.label_18 = QLabel(self.groupBox_2)
        self.label_18.setObjectName(u"label_18")

        self.formLayout_2.setWidget(8, QFormLayout.LabelRole, self.label_18)

        self.label_19 = QLabel(self.groupBox_2)
        self.label_19.setObjectName(u"label_19")

        self.formLayout_2.setWidget(7, QFormLayout.LabelRole, self.label_19)

        self.label_20 = QLabel(self.groupBox_2)
        self.label_20.setObjectName(u"label_20")

        self.formLayout_2.setWidget(6, QFormLayout.LabelRole, self.label_20)

        self.label_21 = QLabel(self.groupBox_2)
        self.label_21.setObjectName(u"label_21")

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.label_21)

        self.label_22 = QLabel(self.groupBox_2)
        self.label_22.setObjectName(u"label_22")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.label_22)

        self.label_23 = QLabel(self.groupBox_2)
        self.label_23.setObjectName(u"label_23")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_23)

        self.label_24 = QLabel(self.groupBox_2)
        self.label_24.setObjectName(u"label_24")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_24)

        self.label_25 = QLabel(self.groupBox_2)
        self.label_25.setObjectName(u"label_25")

        self.formLayout_2.setWidget(15, QFormLayout.LabelRole, self.label_25)

        self.label_26 = QLabel(self.groupBox_2)
        self.label_26.setObjectName(u"label_26")

        self.formLayout_2.setWidget(16, QFormLayout.LabelRole, self.label_26)

        self.label_27 = QLabel(self.groupBox_2)
        self.label_27.setObjectName(u"label_27")

        self.formLayout_2.setWidget(17, QFormLayout.LabelRole, self.label_27)

        self.label_28 = QLabel(self.groupBox_2)
        self.label_28.setObjectName(u"label_28")

        self.formLayout_2.setWidget(18, QFormLayout.LabelRole, self.label_28)

        self.label_29 = QLabel(self.groupBox_2)
        self.label_29.setObjectName(u"label_29")

        self.formLayout_2.setWidget(19, QFormLayout.LabelRole, self.label_29)

        self.dirtMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.dirtMaterialColourEdit.setObjectName(u"dirtMaterialColourEdit")
        self.dirtMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.dirtMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.dirtMaterialColourEdit)

        self.obscuringMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.obscuringMaterialColourEdit.setObjectName(u"obscuringMaterialColourEdit")
        self.obscuringMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.obscuringMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.obscuringMaterialColourEdit)

        self.grassMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.grassMaterialColourEdit.setObjectName(u"grassMaterialColourEdit")
        self.grassMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.grassMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.grassMaterialColourEdit)

        self.stoneMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.stoneMaterialColourEdit.setObjectName(u"stoneMaterialColourEdit")
        self.stoneMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.stoneMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.stoneMaterialColourEdit)

        self.woodMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.woodMaterialColourEdit.setObjectName(u"woodMaterialColourEdit")
        self.woodMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.woodMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.woodMaterialColourEdit)

        self.waterMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.waterMaterialColourEdit.setObjectName(u"waterMaterialColourEdit")
        self.waterMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.waterMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(6, QFormLayout.FieldRole, self.waterMaterialColourEdit)

        self.nonWalkMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.nonWalkMaterialColourEdit.setObjectName(u"nonWalkMaterialColourEdit")
        self.nonWalkMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.nonWalkMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(7, QFormLayout.FieldRole, self.nonWalkMaterialColourEdit)

        self.transparentMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.transparentMaterialColourEdit.setObjectName(u"transparentMaterialColourEdit")
        self.transparentMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.transparentMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(8, QFormLayout.FieldRole, self.transparentMaterialColourEdit)

        self.carpetMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.carpetMaterialColourEdit.setObjectName(u"carpetMaterialColourEdit")
        self.carpetMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.carpetMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(9, QFormLayout.FieldRole, self.carpetMaterialColourEdit)

        self.metalMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.metalMaterialColourEdit.setObjectName(u"metalMaterialColourEdit")
        self.metalMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.metalMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(10, QFormLayout.FieldRole, self.metalMaterialColourEdit)

        self.puddlesMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.puddlesMaterialColourEdit.setObjectName(u"puddlesMaterialColourEdit")
        self.puddlesMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.puddlesMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(11, QFormLayout.FieldRole, self.puddlesMaterialColourEdit)

        self.swampMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.swampMaterialColourEdit.setObjectName(u"swampMaterialColourEdit")
        self.swampMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.swampMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(12, QFormLayout.FieldRole, self.swampMaterialColourEdit)

        self.mudMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.mudMaterialColourEdit.setObjectName(u"mudMaterialColourEdit")
        self.mudMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.mudMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(13, QFormLayout.FieldRole, self.mudMaterialColourEdit)

        self.leavesMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.leavesMaterialColourEdit.setObjectName(u"leavesMaterialColourEdit")
        self.leavesMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.leavesMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(14, QFormLayout.FieldRole, self.leavesMaterialColourEdit)

        self.lavaMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.lavaMaterialColourEdit.setObjectName(u"lavaMaterialColourEdit")
        self.lavaMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.lavaMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(15, QFormLayout.FieldRole, self.lavaMaterialColourEdit)

        self.bottomlessPitMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.bottomlessPitMaterialColourEdit.setObjectName(u"bottomlessPitMaterialColourEdit")
        self.bottomlessPitMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.bottomlessPitMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(16, QFormLayout.FieldRole, self.bottomlessPitMaterialColourEdit)

        self.deepWaterMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.deepWaterMaterialColourEdit.setObjectName(u"deepWaterMaterialColourEdit")
        self.deepWaterMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.deepWaterMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(17, QFormLayout.FieldRole, self.deepWaterMaterialColourEdit)

        self.doorMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.doorMaterialColourEdit.setObjectName(u"doorMaterialColourEdit")
        self.doorMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.doorMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(18, QFormLayout.FieldRole, self.doorMaterialColourEdit)

        self.nonWalkGrassMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.nonWalkGrassMaterialColourEdit.setObjectName(u"nonWalkGrassMaterialColourEdit")
        self.nonWalkGrassMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.nonWalkGrassMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(19, QFormLayout.FieldRole, self.nonWalkGrassMaterialColourEdit)


        self.gridLayout_2.addLayout(self.formLayout_2, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.coloursResetButton = QPushButton(self.groupBox_2)
        self.coloursResetButton.setObjectName(u"coloursResetButton")

        self.horizontalLayout.addWidget(self.coloursResetButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"Controls", None))
        self.controlsResetButton.setText(QCoreApplication.translate("Form", u"Reset", None))
        self.label.setText(QCoreApplication.translate("Form", u"Move Camera:", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Rotate Camera:", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Zoom Camera:", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"Select Object:", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Rotate Object:", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Delete Object:", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Duplicate Object:", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"Toggle Instance Lock:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Form", u"Walkmesh Colours", None))
        self.label_10.setText(QCoreApplication.translate("Form", u"Undefined:", None))
        self.label_11.setText(QCoreApplication.translate("Form", u"Dirt:", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"Leaves:", None))
        self.label_13.setText(QCoreApplication.translate("Form", u"Mud:", None))
        self.label_14.setText(QCoreApplication.translate("Form", u"Swamp:", None))
        self.label_15.setText(QCoreApplication.translate("Form", u"Puddles:", None))
        self.label_16.setText(QCoreApplication.translate("Form", u"Metal:", None))
        self.label_17.setText(QCoreApplication.translate("Form", u"Carpet:", None))
        self.label_18.setText(QCoreApplication.translate("Form", u"Transparent:", None))
        self.label_19.setText(QCoreApplication.translate("Form", u"Non-Walk:", None))
        self.label_20.setText(QCoreApplication.translate("Form", u"Water:", None))
        self.label_21.setText(QCoreApplication.translate("Form", u"Wood:", None))
        self.label_22.setText(QCoreApplication.translate("Form", u"Stone:", None))
        self.label_23.setText(QCoreApplication.translate("Form", u"Grass:", None))
        self.label_24.setText(QCoreApplication.translate("Form", u"Obscuring:", None))
        self.label_25.setText(QCoreApplication.translate("Form", u"Lava:", None))
        self.label_26.setText(QCoreApplication.translate("Form", u"Bottomless Pit:", None))
        self.label_27.setText(QCoreApplication.translate("Form", u"Deep Water:", None))
        self.label_28.setText(QCoreApplication.translate("Form", u"Door:", None))
        self.label_29.setText(QCoreApplication.translate("Form", u"Non-Walk Grass:", None))
        self.coloursResetButton.setText(QCoreApplication.translate("Form", u"Reset", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
