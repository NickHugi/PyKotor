
################################################################################
## Form generated from reading UI file 'git.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.edit.color import ColorEdit
from toolset.gui.widgets.set_bind import SetBindWidget


class Ui_Form:
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(466, 773)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.scrollArea = QScrollArea(Form)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, -195, 429, 948))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.controlsResetButton = QPushButton(self.groupBox)
        self.controlsResetButton.setObjectName("controlsResetButton")

        self.horizontalLayout_3.addWidget(self.controlsResetButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.widget = QWidget(self.groupBox)
        self.widget.setObjectName("widget")
        self.widget.setMinimumSize(QSize(0, 200))
        self.formLayout = QFormLayout(self.widget)
        self.formLayout.setObjectName("formLayout")
        self.formLayout.setVerticalSpacing(10)
        self.label = QLabel(self.widget)
        self.label.setObjectName("label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.moveCameraBindEdit = SetBindWidget(self.widget)
        self.moveCameraBindEdit.setObjectName("moveCameraBindEdit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.moveCameraBindEdit)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.rotateCameraBindEdit = SetBindWidget(self.widget)
        self.rotateCameraBindEdit.setObjectName("rotateCameraBindEdit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.rotateCameraBindEdit)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName("label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.zoomCameraBindEdit = SetBindWidget(self.widget)
        self.zoomCameraBindEdit.setObjectName("zoomCameraBindEdit")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.zoomCameraBindEdit)

        self.label_5 = QLabel(self.widget)
        self.label_5.setObjectName("label_5")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_5)

        self.selectUnderneathBindEdit = SetBindWidget(self.widget)
        self.selectUnderneathBindEdit.setObjectName("selectUnderneathBindEdit")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.selectUnderneathBindEdit)

        self.label_4 = QLabel(self.widget)
        self.label_4.setObjectName("label_4")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.rotateSelectedToPointBindEdit = SetBindWidget(self.widget)
        self.rotateSelectedToPointBindEdit.setObjectName("rotateSelectedToPointBindEdit")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.rotateSelectedToPointBindEdit)

        self.label_6 = QLabel(self.widget)
        self.label_6.setObjectName("label_6")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_6)

        self.deleteSelectedBindEdit = SetBindWidget(self.widget)
        self.deleteSelectedBindEdit.setObjectName("deleteSelectedBindEdit")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.deleteSelectedBindEdit)

        self.label_7 = QLabel(self.widget)
        self.label_7.setObjectName("label_7")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_7)

        self.duplicateSelectedBindEdit = SetBindWidget(self.widget)
        self.duplicateSelectedBindEdit.setObjectName("duplicateSelectedBindEdit")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.duplicateSelectedBindEdit)

        self.label_8 = QLabel(self.widget)
        self.label_8.setObjectName("label_8")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_8)

        self.toggleLockInstancesBindEdit = SetBindWidget(self.widget)
        self.toggleLockInstancesBindEdit.setObjectName("toggleLockInstancesBindEdit")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.toggleLockInstancesBindEdit)


        self.verticalLayout_2.addWidget(self.widget)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_2.setObjectName("groupBox_2")
        self.groupBox_2.setMinimumSize(QSize(0, 660))
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.formLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.formLayout_2.setVerticalSpacing(10)
        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName("label_10")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_10)

        self.undefinedMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.undefinedMaterialColourEdit.setObjectName("undefinedMaterialColourEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.undefinedMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.undefinedMaterialColourEdit.setSizePolicy(sizePolicy)
        self.undefinedMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.undefinedMaterialColourEdit)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName("label_11")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.label_12 = QLabel(self.groupBox_2)
        self.label_12.setObjectName("label_12")

        self.formLayout_2.setWidget(14, QFormLayout.LabelRole, self.label_12)

        self.label_13 = QLabel(self.groupBox_2)
        self.label_13.setObjectName("label_13")

        self.formLayout_2.setWidget(13, QFormLayout.LabelRole, self.label_13)

        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName("label_14")

        self.formLayout_2.setWidget(12, QFormLayout.LabelRole, self.label_14)

        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName("label_15")

        self.formLayout_2.setWidget(11, QFormLayout.LabelRole, self.label_15)

        self.label_16 = QLabel(self.groupBox_2)
        self.label_16.setObjectName("label_16")

        self.formLayout_2.setWidget(10, QFormLayout.LabelRole, self.label_16)

        self.label_17 = QLabel(self.groupBox_2)
        self.label_17.setObjectName("label_17")

        self.formLayout_2.setWidget(9, QFormLayout.LabelRole, self.label_17)

        self.label_18 = QLabel(self.groupBox_2)
        self.label_18.setObjectName("label_18")

        self.formLayout_2.setWidget(8, QFormLayout.LabelRole, self.label_18)

        self.label_19 = QLabel(self.groupBox_2)
        self.label_19.setObjectName("label_19")

        self.formLayout_2.setWidget(7, QFormLayout.LabelRole, self.label_19)

        self.label_20 = QLabel(self.groupBox_2)
        self.label_20.setObjectName("label_20")

        self.formLayout_2.setWidget(6, QFormLayout.LabelRole, self.label_20)

        self.label_21 = QLabel(self.groupBox_2)
        self.label_21.setObjectName("label_21")

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.label_21)

        self.label_22 = QLabel(self.groupBox_2)
        self.label_22.setObjectName("label_22")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.label_22)

        self.label_23 = QLabel(self.groupBox_2)
        self.label_23.setObjectName("label_23")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_23)

        self.label_24 = QLabel(self.groupBox_2)
        self.label_24.setObjectName("label_24")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_24)

        self.label_25 = QLabel(self.groupBox_2)
        self.label_25.setObjectName("label_25")

        self.formLayout_2.setWidget(15, QFormLayout.LabelRole, self.label_25)

        self.label_26 = QLabel(self.groupBox_2)
        self.label_26.setObjectName("label_26")

        self.formLayout_2.setWidget(16, QFormLayout.LabelRole, self.label_26)

        self.label_27 = QLabel(self.groupBox_2)
        self.label_27.setObjectName("label_27")

        self.formLayout_2.setWidget(17, QFormLayout.LabelRole, self.label_27)

        self.label_28 = QLabel(self.groupBox_2)
        self.label_28.setObjectName("label_28")

        self.formLayout_2.setWidget(18, QFormLayout.LabelRole, self.label_28)

        self.label_29 = QLabel(self.groupBox_2)
        self.label_29.setObjectName("label_29")

        self.formLayout_2.setWidget(19, QFormLayout.LabelRole, self.label_29)

        self.dirtMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.dirtMaterialColourEdit.setObjectName("dirtMaterialColourEdit")
        self.dirtMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.dirtMaterialColourEdit)

        self.obscuringMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.obscuringMaterialColourEdit.setObjectName("obscuringMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.obscuringMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.obscuringMaterialColourEdit.setSizePolicy(sizePolicy)
        self.obscuringMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.obscuringMaterialColourEdit)

        self.grassMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.grassMaterialColourEdit.setObjectName("grassMaterialColourEdit")
        self.grassMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.grassMaterialColourEdit)

        self.stoneMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.stoneMaterialColourEdit.setObjectName("stoneMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.stoneMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.stoneMaterialColourEdit.setSizePolicy(sizePolicy)
        self.stoneMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.stoneMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.stoneMaterialColourEdit)

        self.woodMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.woodMaterialColourEdit.setObjectName("woodMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.woodMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.woodMaterialColourEdit.setSizePolicy(sizePolicy)
        self.woodMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.woodMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.woodMaterialColourEdit)

        self.waterMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.waterMaterialColourEdit.setObjectName("waterMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.waterMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.waterMaterialColourEdit.setSizePolicy(sizePolicy)
        self.waterMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.waterMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(6, QFormLayout.FieldRole, self.waterMaterialColourEdit)

        self.nonWalkMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.nonWalkMaterialColourEdit.setObjectName("nonWalkMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.nonWalkMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.nonWalkMaterialColourEdit.setSizePolicy(sizePolicy)
        self.nonWalkMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(7, QFormLayout.FieldRole, self.nonWalkMaterialColourEdit)

        self.transparentMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.transparentMaterialColourEdit.setObjectName("transparentMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.transparentMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.transparentMaterialColourEdit.setSizePolicy(sizePolicy)
        self.transparentMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.transparentMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(8, QFormLayout.FieldRole, self.transparentMaterialColourEdit)

        self.carpetMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.carpetMaterialColourEdit.setObjectName("carpetMaterialColourEdit")
        self.carpetMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(9, QFormLayout.FieldRole, self.carpetMaterialColourEdit)

        self.metalMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.metalMaterialColourEdit.setObjectName("metalMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.metalMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.metalMaterialColourEdit.setSizePolicy(sizePolicy)
        self.metalMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(10, QFormLayout.FieldRole, self.metalMaterialColourEdit)

        self.puddlesMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.puddlesMaterialColourEdit.setObjectName("puddlesMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.puddlesMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.puddlesMaterialColourEdit.setSizePolicy(sizePolicy)
        self.puddlesMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.puddlesMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(11, QFormLayout.FieldRole, self.puddlesMaterialColourEdit)

        self.swampMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.swampMaterialColourEdit.setObjectName("swampMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.swampMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.swampMaterialColourEdit.setSizePolicy(sizePolicy)
        self.swampMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.swampMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_2.setWidget(12, QFormLayout.FieldRole, self.swampMaterialColourEdit)

        self.mudMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.mudMaterialColourEdit.setObjectName("mudMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.mudMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.mudMaterialColourEdit.setSizePolicy(sizePolicy)
        self.mudMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(13, QFormLayout.FieldRole, self.mudMaterialColourEdit)

        self.leavesMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.leavesMaterialColourEdit.setObjectName("leavesMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.leavesMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.leavesMaterialColourEdit.setSizePolicy(sizePolicy)
        self.leavesMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(14, QFormLayout.FieldRole, self.leavesMaterialColourEdit)

        self.lavaMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.lavaMaterialColourEdit.setObjectName("lavaMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.lavaMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.lavaMaterialColourEdit.setSizePolicy(sizePolicy)
        self.lavaMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(15, QFormLayout.FieldRole, self.lavaMaterialColourEdit)

        self.bottomlessPitMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.bottomlessPitMaterialColourEdit.setObjectName("bottomlessPitMaterialColourEdit")
        self.bottomlessPitMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(16, QFormLayout.FieldRole, self.bottomlessPitMaterialColourEdit)

        self.deepWaterMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.deepWaterMaterialColourEdit.setObjectName("deepWaterMaterialColourEdit")
        self.deepWaterMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(17, QFormLayout.FieldRole, self.deepWaterMaterialColourEdit)

        self.doorMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.doorMaterialColourEdit.setObjectName("doorMaterialColourEdit")
        self.doorMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(18, QFormLayout.FieldRole, self.doorMaterialColourEdit)

        self.nonWalkGrassMaterialColourEdit = ColorEdit(self.groupBox_2)
        self.nonWalkGrassMaterialColourEdit.setObjectName("nonWalkGrassMaterialColourEdit")
        sizePolicy.setHeightForWidth(self.nonWalkGrassMaterialColourEdit.sizePolicy().hasHeightForWidth())
        self.nonWalkGrassMaterialColourEdit.setSizePolicy(sizePolicy)
        self.nonWalkGrassMaterialColourEdit.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(19, QFormLayout.FieldRole, self.nonWalkGrassMaterialColourEdit)


        self.gridLayout_2.addLayout(self.formLayout_2, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.coloursResetButton = QPushButton(self.groupBox_2)
        self.coloursResetButton.setObjectName("coloursResetButton")

        self.horizontalLayout.addWidget(self.coloursResetButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", "Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", "Controls", None))
        self.controlsResetButton.setText(QCoreApplication.translate("Form", "Reset", None))
        self.label.setText(QCoreApplication.translate("Form", "Move Camera:", None))
        self.label_2.setText(QCoreApplication.translate("Form", "Rotate Camera:", None))
        self.label_3.setText(QCoreApplication.translate("Form", "Zoom Camera:", None))
        self.label_5.setText(QCoreApplication.translate("Form", "Select Object:", None))
        self.label_4.setText(QCoreApplication.translate("Form", "Rotate Object:", None))
        self.label_6.setText(QCoreApplication.translate("Form", "Delete Object:", None))
        self.label_7.setText(QCoreApplication.translate("Form", "Duplicate Object:", None))
        self.label_8.setText(QCoreApplication.translate("Form", "Toggle Instance Lock:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Form", "Walkmesh Colours", None))
        self.label_10.setText(QCoreApplication.translate("Form", "Undefined:", None))
        self.label_11.setText(QCoreApplication.translate("Form", "Dirt:", None))
        self.label_12.setText(QCoreApplication.translate("Form", "Leaves:", None))
        self.label_13.setText(QCoreApplication.translate("Form", "Mud:", None))
        self.label_14.setText(QCoreApplication.translate("Form", "Swamp:", None))
        self.label_15.setText(QCoreApplication.translate("Form", "Puddles:", None))
        self.label_16.setText(QCoreApplication.translate("Form", "Metal:", None))
        self.label_17.setText(QCoreApplication.translate("Form", "Carpet:", None))
        self.label_18.setText(QCoreApplication.translate("Form", "Transparent:", None))
        self.label_19.setText(QCoreApplication.translate("Form", "Non-Walk:", None))
        self.label_20.setText(QCoreApplication.translate("Form", "Water:", None))
        self.label_21.setText(QCoreApplication.translate("Form", "Wood:", None))
        self.label_22.setText(QCoreApplication.translate("Form", "Stone:", None))
        self.label_23.setText(QCoreApplication.translate("Form", "Grass:", None))
        self.label_24.setText(QCoreApplication.translate("Form", "Obscuring:", None))
        self.label_25.setText(QCoreApplication.translate("Form", "Lava:", None))
        self.label_26.setText(QCoreApplication.translate("Form", "Bottomless Pit:", None))
        self.label_27.setText(QCoreApplication.translate("Form", "Deep Water:", None))
        self.label_28.setText(QCoreApplication.translate("Form", "Door:", None))
        self.label_29.setText(QCoreApplication.translate("Form", "Non-Walk Grass:", None))
        self.coloursResetButton.setText(QCoreApplication.translate("Form", "Reset", None))
    # retranslateUi

