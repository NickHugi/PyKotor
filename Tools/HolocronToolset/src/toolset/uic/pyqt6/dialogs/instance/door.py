# Form implementation generated from reading ui file '..\ui\dialogs\instance\door.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(374, 290)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(parent=Dialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label)
        self.resrefEdit = QtWidgets.QLineEdit(parent=Dialog)
        self.resrefEdit.setMaximumSize(QtCore.QSize(187, 16777215))
        self.resrefEdit.setMaxLength(16)
        self.resrefEdit.setObjectName("resrefEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.resrefEdit)
        self.label_2 = QtWidgets.QLabel(parent=Dialog)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.xPosSpin = QtWidgets.QDoubleSpinBox(parent=Dialog)
        self.xPosSpin.setMaximumSize(QtCore.QSize(90, 16777215))
        self.xPosSpin.setWrapping(True)
        self.xPosSpin.setDecimals(6)
        self.xPosSpin.setMinimum(-1000000.0)
        self.xPosSpin.setMaximum(1000000.0)
        self.xPosSpin.setObjectName("xPosSpin")
        self.horizontalLayout.addWidget(self.xPosSpin)
        self.yPosSpin = QtWidgets.QDoubleSpinBox(parent=Dialog)
        self.yPosSpin.setMaximumSize(QtCore.QSize(90, 16777215))
        self.yPosSpin.setWrapping(True)
        self.yPosSpin.setDecimals(6)
        self.yPosSpin.setMinimum(-1000000.0)
        self.yPosSpin.setMaximum(1000000.0)
        self.yPosSpin.setObjectName("yPosSpin")
        self.horizontalLayout.addWidget(self.yPosSpin)
        self.zPosSpin = QtWidgets.QDoubleSpinBox(parent=Dialog)
        self.zPosSpin.setMaximumSize(QtCore.QSize(90, 16777215))
        self.zPosSpin.setWrapping(True)
        self.zPosSpin.setDecimals(6)
        self.zPosSpin.setMinimum(-1000000.0)
        self.zPosSpin.setMaximum(1000000.0)
        self.zPosSpin.setObjectName("zPosSpin")
        self.horizontalLayout.addWidget(self.zPosSpin)
        self.formLayout.setLayout(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.horizontalLayout)
        self.label_3 = QtWidgets.QLabel(parent=Dialog)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3)
        self.bearingSpin = QtWidgets.QDoubleSpinBox(parent=Dialog)
        self.bearingSpin.setMaximumSize(QtCore.QSize(90, 16777215))
        self.bearingSpin.setDecimals(6)
        self.bearingSpin.setMinimum(-1000000.0)
        self.bearingSpin.setMaximum(1000000.0)
        self.bearingSpin.setObjectName("bearingSpin")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.bearingSpin)
        self.label_4 = QtWidgets.QLabel(parent=Dialog)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.color = QtWidgets.QLabel(parent=Dialog)
        self.color.setMinimumSize(QtCore.QSize(16, 16))
        self.color.setMaximumSize(QtCore.QSize(16, 16))
        self.color.setStyleSheet("background: black;")
        self.color.setText("")
        self.color.setObjectName("color")
        self.horizontalLayout_9.addWidget(self.color)
        self.colorSpin = LongSpinBox(parent=Dialog)
        self.colorSpin.setMinimumSize(QtCore.QSize(90, 0))
        self.colorSpin.setMaximumSize(QtCore.QSize(90, 16777215))
        self.colorSpin.setObjectName("colorSpin")
        self.horizontalLayout_9.addWidget(self.colorSpin)
        self.colorButton = QtWidgets.QPushButton(parent=Dialog)
        self.colorButton.setMaximumSize(QtCore.QSize(24, 20))
        self.colorButton.setObjectName("colorButton")
        self.horizontalLayout_9.addWidget(self.colorButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem)
        self.formLayout.setLayout(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.horizontalLayout_9)
        self.label_8 = QtWidgets.QLabel(parent=Dialog)
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_8)
        self.tagEdit = QtWidgets.QLineEdit(parent=Dialog)
        self.tagEdit.setMaximumSize(QtCore.QSize(187, 16777215))
        self.tagEdit.setObjectName("tagEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.tagEdit)
        self.verticalLayout.addLayout(self.formLayout)
        self.line = QtWidgets.QFrame(parent=Dialog)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.noTransCheck = QtWidgets.QRadioButton(parent=Dialog)
        self.noTransCheck.setObjectName("noTransCheck")
        self.horizontalLayout_2.addWidget(self.noTransCheck)
        self.toDoorCheck = QtWidgets.QRadioButton(parent=Dialog)
        self.toDoorCheck.setObjectName("toDoorCheck")
        self.horizontalLayout_2.addWidget(self.toDoorCheck)
        self.toWaypointCheck = QtWidgets.QRadioButton(parent=Dialog)
        self.toWaypointCheck.setObjectName("toWaypointCheck")
        self.horizontalLayout_2.addWidget(self.toWaypointCheck)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_5 = QtWidgets.QLabel(parent=Dialog)
        self.label_5.setObjectName("label_5")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_5)
        self.linkToModuleEdit = QtWidgets.QLineEdit(parent=Dialog)
        self.linkToModuleEdit.setMaximumSize(QtCore.QSize(187, 16777215))
        self.linkToModuleEdit.setMaxLength(16)
        self.linkToModuleEdit.setObjectName("linkToModuleEdit")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.linkToModuleEdit)
        self.label_6 = QtWidgets.QLabel(parent=Dialog)
        self.label_6.setObjectName("label_6")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_6)
        self.linkToTagEdit = QtWidgets.QLineEdit(parent=Dialog)
        self.linkToTagEdit.setMaximumSize(QtCore.QSize(187, 16777215))
        self.linkToTagEdit.setObjectName("linkToTagEdit")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.linkToTagEdit)
        self.label_7 = QtWidgets.QLabel(parent=Dialog)
        self.label_7.setObjectName("label_7")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_7)
        self.transNameEdit = LocalizedStringLineEdit(parent=Dialog)
        self.transNameEdit.setMinimumSize(QtCore.QSize(219, 23))
        self.transNameEdit.setMaximumSize(QtCore.QSize(219, 16777215))
        self.transNameEdit.setObjectName("transNameEdit")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.transNameEdit)
        self.verticalLayout.addLayout(self.formLayout_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Edit Door"))
        self.label.setText(_translate("Dialog", "ResRef:"))
        self.label_2.setText(_translate("Dialog", "Position:"))
        self.label_3.setText(_translate("Dialog", "Bearing:"))
        self.label_4.setText(_translate("Dialog", "Tweak Color:"))
        self.colorButton.setText(_translate("Dialog", "..."))
        self.label_8.setText(_translate("Dialog", "Tag:"))
        self.noTransCheck.setText(_translate("Dialog", "No Transition"))
        self.toDoorCheck.setText(_translate("Dialog", "Links to Door"))
        self.toWaypointCheck.setText(_translate("Dialog", "Links to Waypoint"))
        self.label_5.setText(_translate("Dialog", "Link To Module:"))
        self.label_6.setText(_translate("Dialog", "Link To Tag:"))
        self.label_7.setText(_translate("Dialog", "Transition Name:"))
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.long_spinbox import LongSpinBox