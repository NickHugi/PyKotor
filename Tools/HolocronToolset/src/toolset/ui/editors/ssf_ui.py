
################################################################################
## Form generated from reading UI file 'ssf.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QMenuBar, QScrollArea, QSpinBox, QWidget


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(577, 437)
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
        self.actionSetTLK = QAction(MainWindow)
        self.actionSetTLK.setObjectName("actionSetTLK")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 540, 889))
        self.formLayout = QFormLayout(self.scrollAreaWidgetContents)
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName("label_3")
        self.label_3.setMinimumSize(QSize(90, 0))
        self.label_3.setMaximumSize(QSize(90, 16777215))

        self.horizontalLayout_2.addWidget(self.label_3)

        self.label_4 = QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName("label_4")
        self.label_4.setMinimumSize(QSize(150, 0))
        self.label_4.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_2.addWidget(self.label_4)

        self.label_5 = QLabel(self.scrollAreaWidgetContents)
        self.label_5.setObjectName("label_5")

        self.horizontalLayout_2.addWidget(self.label_5)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_2)

        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName("label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.battlecry1StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.battlecry1StrrefSpin.setObjectName("battlecry1StrrefSpin")
        self.battlecry1StrrefSpin.setMinimumSize(QSize(90, 0))
        self.battlecry1StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.battlecry1StrrefSpin.setMinimum(-1)
        self.battlecry1StrrefSpin.setMaximum(999999999)

        self.horizontalLayout.addWidget(self.battlecry1StrrefSpin)

        self.battlecry1SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry1SoundEdit.setObjectName("battlecry1SoundEdit")
        self.battlecry1SoundEdit.setEnabled(True)
        self.battlecry1SoundEdit.setMinimumSize(QSize(150, 0))
        self.battlecry1SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.battlecry1SoundEdit.setReadOnly(True)

        self.horizontalLayout.addWidget(self.battlecry1SoundEdit)

        self.battlecry1TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry1TextEdit.setObjectName("battlecry1TextEdit")
        self.battlecry1TextEdit.setEnabled(True)
        self.battlecry1TextEdit.setReadOnly(True)

        self.horizontalLayout.addWidget(self.battlecry1TextEdit)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout)

        self.label_6 = QLabel(self.scrollAreaWidgetContents)
        self.label_6.setObjectName("label_6")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.battlecry2StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.battlecry2StrrefSpin.setObjectName("battlecry2StrrefSpin")
        self.battlecry2StrrefSpin.setMinimumSize(QSize(90, 0))
        self.battlecry2StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.battlecry2StrrefSpin.setMinimum(-1)
        self.battlecry2StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_3.addWidget(self.battlecry2StrrefSpin)

        self.battlecry2SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry2SoundEdit.setObjectName("battlecry2SoundEdit")
        self.battlecry2SoundEdit.setEnabled(True)
        self.battlecry2SoundEdit.setMinimumSize(QSize(150, 0))
        self.battlecry2SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.battlecry2SoundEdit.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.battlecry2SoundEdit)

        self.battlecry2TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry2TextEdit.setObjectName("battlecry2TextEdit")
        self.battlecry2TextEdit.setEnabled(True)
        self.battlecry2TextEdit.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.battlecry2TextEdit)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_3)

        self.label_7 = QLabel(self.scrollAreaWidgetContents)
        self.label_7.setObjectName("label_7")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_7)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.battlecry3StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.battlecry3StrrefSpin.setObjectName("battlecry3StrrefSpin")
        self.battlecry3StrrefSpin.setMinimumSize(QSize(90, 0))
        self.battlecry3StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.battlecry3StrrefSpin.setMinimum(-1)
        self.battlecry3StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_5.addWidget(self.battlecry3StrrefSpin)

        self.battlecry3SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry3SoundEdit.setObjectName("battlecry3SoundEdit")
        self.battlecry3SoundEdit.setEnabled(True)
        self.battlecry3SoundEdit.setMinimumSize(QSize(150, 0))
        self.battlecry3SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.battlecry3SoundEdit.setReadOnly(True)

        self.horizontalLayout_5.addWidget(self.battlecry3SoundEdit)

        self.battlecry3TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry3TextEdit.setObjectName("battlecry3TextEdit")
        self.battlecry3TextEdit.setEnabled(True)
        self.battlecry3TextEdit.setReadOnly(True)

        self.horizontalLayout_5.addWidget(self.battlecry3TextEdit)


        self.formLayout.setLayout(3, QFormLayout.FieldRole, self.horizontalLayout_5)

        self.label_8 = QLabel(self.scrollAreaWidgetContents)
        self.label_8.setObjectName("label_8")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_8)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.battlecry4StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.battlecry4StrrefSpin.setObjectName("battlecry4StrrefSpin")
        self.battlecry4StrrefSpin.setMinimumSize(QSize(90, 0))
        self.battlecry4StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.battlecry4StrrefSpin.setMinimum(-1)
        self.battlecry4StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_6.addWidget(self.battlecry4StrrefSpin)

        self.battlecry4SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry4SoundEdit.setObjectName("battlecry4SoundEdit")
        self.battlecry4SoundEdit.setEnabled(True)
        self.battlecry4SoundEdit.setMinimumSize(QSize(150, 0))
        self.battlecry4SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.battlecry4SoundEdit.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.battlecry4SoundEdit)

        self.battlecry4TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry4TextEdit.setObjectName("battlecry4TextEdit")
        self.battlecry4TextEdit.setEnabled(True)
        self.battlecry4TextEdit.setReadOnly(True)

        self.horizontalLayout_6.addWidget(self.battlecry4TextEdit)


        self.formLayout.setLayout(4, QFormLayout.FieldRole, self.horizontalLayout_6)

        self.label_9 = QLabel(self.scrollAreaWidgetContents)
        self.label_9.setObjectName("label_9")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_9)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.battlecry5StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.battlecry5StrrefSpin.setObjectName("battlecry5StrrefSpin")
        self.battlecry5StrrefSpin.setMinimumSize(QSize(90, 0))
        self.battlecry5StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.battlecry5StrrefSpin.setMinimum(-1)
        self.battlecry5StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_7.addWidget(self.battlecry5StrrefSpin)

        self.battlecry5SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry5SoundEdit.setObjectName("battlecry5SoundEdit")
        self.battlecry5SoundEdit.setEnabled(True)
        self.battlecry5SoundEdit.setMinimumSize(QSize(150, 0))
        self.battlecry5SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.battlecry5SoundEdit.setReadOnly(True)

        self.horizontalLayout_7.addWidget(self.battlecry5SoundEdit)

        self.battlecry5TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry5TextEdit.setObjectName("battlecry5TextEdit")
        self.battlecry5TextEdit.setEnabled(True)
        self.battlecry5TextEdit.setReadOnly(True)

        self.horizontalLayout_7.addWidget(self.battlecry5TextEdit)


        self.formLayout.setLayout(5, QFormLayout.FieldRole, self.horizontalLayout_7)

        self.label_10 = QLabel(self.scrollAreaWidgetContents)
        self.label_10.setObjectName("label_10")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_10)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.battlecry6StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.battlecry6StrrefSpin.setObjectName("battlecry6StrrefSpin")
        self.battlecry6StrrefSpin.setMinimumSize(QSize(90, 0))
        self.battlecry6StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.battlecry6StrrefSpin.setMinimum(-1)
        self.battlecry6StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_8.addWidget(self.battlecry6StrrefSpin)

        self.battlecry6SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry6SoundEdit.setObjectName("battlecry6SoundEdit")
        self.battlecry6SoundEdit.setEnabled(True)
        self.battlecry6SoundEdit.setMinimumSize(QSize(150, 0))
        self.battlecry6SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.battlecry6SoundEdit.setReadOnly(True)

        self.horizontalLayout_8.addWidget(self.battlecry6SoundEdit)

        self.battlecry6TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.battlecry6TextEdit.setObjectName("battlecry6TextEdit")
        self.battlecry6TextEdit.setEnabled(True)
        self.battlecry6TextEdit.setReadOnly(True)

        self.horizontalLayout_8.addWidget(self.battlecry6TextEdit)


        self.formLayout.setLayout(6, QFormLayout.FieldRole, self.horizontalLayout_8)

        self.line = QFrame(self.scrollAreaWidgetContents)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.line)

        self.label_11 = QLabel(self.scrollAreaWidgetContents)
        self.label_11.setObjectName("label_11")

        self.formLayout.setWidget(8, QFormLayout.LabelRole, self.label_11)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.select1StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.select1StrrefSpin.setObjectName("select1StrrefSpin")
        self.select1StrrefSpin.setMinimumSize(QSize(90, 0))
        self.select1StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.select1StrrefSpin.setMinimum(-1)
        self.select1StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_4.addWidget(self.select1StrrefSpin)

        self.select1SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.select1SoundEdit.setObjectName("select1SoundEdit")
        self.select1SoundEdit.setEnabled(True)
        self.select1SoundEdit.setMinimumSize(QSize(150, 0))
        self.select1SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.select1SoundEdit.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.select1SoundEdit)

        self.select1TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.select1TextEdit.setObjectName("select1TextEdit")
        self.select1TextEdit.setEnabled(True)
        self.select1TextEdit.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.select1TextEdit)


        self.formLayout.setLayout(8, QFormLayout.FieldRole, self.horizontalLayout_4)

        self.label_12 = QLabel(self.scrollAreaWidgetContents)
        self.label_12.setObjectName("label_12")

        self.formLayout.setWidget(9, QFormLayout.LabelRole, self.label_12)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.select2StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.select2StrrefSpin.setObjectName("select2StrrefSpin")
        self.select2StrrefSpin.setMinimumSize(QSize(90, 0))
        self.select2StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.select2StrrefSpin.setMinimum(-1)
        self.select2StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_10.addWidget(self.select2StrrefSpin)

        self.select2SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.select2SoundEdit.setObjectName("select2SoundEdit")
        self.select2SoundEdit.setEnabled(True)
        self.select2SoundEdit.setMinimumSize(QSize(150, 0))
        self.select2SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.select2SoundEdit.setReadOnly(True)

        self.horizontalLayout_10.addWidget(self.select2SoundEdit)

        self.select2TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.select2TextEdit.setObjectName("select2TextEdit")
        self.select2TextEdit.setEnabled(True)
        self.select2TextEdit.setReadOnly(True)

        self.horizontalLayout_10.addWidget(self.select2TextEdit)


        self.formLayout.setLayout(9, QFormLayout.FieldRole, self.horizontalLayout_10)

        self.label_13 = QLabel(self.scrollAreaWidgetContents)
        self.label_13.setObjectName("label_13")

        self.formLayout.setWidget(10, QFormLayout.LabelRole, self.label_13)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.select3StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.select3StrrefSpin.setObjectName("select3StrrefSpin")
        self.select3StrrefSpin.setMinimumSize(QSize(90, 0))
        self.select3StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.select3StrrefSpin.setMinimum(-1)
        self.select3StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_11.addWidget(self.select3StrrefSpin)

        self.select3SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.select3SoundEdit.setObjectName("select3SoundEdit")
        self.select3SoundEdit.setEnabled(True)
        self.select3SoundEdit.setMinimumSize(QSize(150, 0))
        self.select3SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.select3SoundEdit.setReadOnly(True)

        self.horizontalLayout_11.addWidget(self.select3SoundEdit)

        self.select3TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.select3TextEdit.setObjectName("select3TextEdit")
        self.select3TextEdit.setEnabled(True)
        self.select3TextEdit.setReadOnly(True)

        self.horizontalLayout_11.addWidget(self.select3TextEdit)


        self.formLayout.setLayout(10, QFormLayout.FieldRole, self.horizontalLayout_11)

        self.line_2 = QFrame(self.scrollAreaWidgetContents)
        self.line_2.setObjectName("line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(11, QFormLayout.FieldRole, self.line_2)

        self.label_14 = QLabel(self.scrollAreaWidgetContents)
        self.label_14.setObjectName("label_14")

        self.formLayout.setWidget(12, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.attack1StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.attack1StrrefSpin.setObjectName("attack1StrrefSpin")
        self.attack1StrrefSpin.setMinimumSize(QSize(90, 0))
        self.attack1StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.attack1StrrefSpin.setMinimum(-1)
        self.attack1StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_12.addWidget(self.attack1StrrefSpin)

        self.attack1SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.attack1SoundEdit.setObjectName("attack1SoundEdit")
        self.attack1SoundEdit.setEnabled(True)
        self.attack1SoundEdit.setMinimumSize(QSize(150, 0))
        self.attack1SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.attack1SoundEdit.setReadOnly(True)

        self.horizontalLayout_12.addWidget(self.attack1SoundEdit)

        self.attack1TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.attack1TextEdit.setObjectName("attack1TextEdit")
        self.attack1TextEdit.setEnabled(True)
        self.attack1TextEdit.setReadOnly(True)

        self.horizontalLayout_12.addWidget(self.attack1TextEdit)


        self.formLayout.setLayout(12, QFormLayout.FieldRole, self.horizontalLayout_12)

        self.label_15 = QLabel(self.scrollAreaWidgetContents)
        self.label_15.setObjectName("label_15")

        self.formLayout.setWidget(13, QFormLayout.LabelRole, self.label_15)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.attack2StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.attack2StrrefSpin.setObjectName("attack2StrrefSpin")
        self.attack2StrrefSpin.setMinimumSize(QSize(90, 0))
        self.attack2StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.attack2StrrefSpin.setMinimum(-1)
        self.attack2StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_14.addWidget(self.attack2StrrefSpin)

        self.attack2SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.attack2SoundEdit.setObjectName("attack2SoundEdit")
        self.attack2SoundEdit.setEnabled(True)
        self.attack2SoundEdit.setMinimumSize(QSize(150, 0))
        self.attack2SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.attack2SoundEdit.setReadOnly(True)

        self.horizontalLayout_14.addWidget(self.attack2SoundEdit)

        self.attack2TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.attack2TextEdit.setObjectName("attack2TextEdit")
        self.attack2TextEdit.setEnabled(True)
        self.attack2TextEdit.setReadOnly(True)

        self.horizontalLayout_14.addWidget(self.attack2TextEdit)


        self.formLayout.setLayout(13, QFormLayout.FieldRole, self.horizontalLayout_14)

        self.label_16 = QLabel(self.scrollAreaWidgetContents)
        self.label_16.setObjectName("label_16")

        self.formLayout.setWidget(14, QFormLayout.LabelRole, self.label_16)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.attack3StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.attack3StrrefSpin.setObjectName("attack3StrrefSpin")
        self.attack3StrrefSpin.setMinimumSize(QSize(90, 0))
        self.attack3StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.attack3StrrefSpin.setMinimum(-1)
        self.attack3StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_15.addWidget(self.attack3StrrefSpin)

        self.attack3SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.attack3SoundEdit.setObjectName("attack3SoundEdit")
        self.attack3SoundEdit.setEnabled(True)
        self.attack3SoundEdit.setMinimumSize(QSize(150, 0))
        self.attack3SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.attack3SoundEdit.setReadOnly(True)

        self.horizontalLayout_15.addWidget(self.attack3SoundEdit)

        self.attack3TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.attack3TextEdit.setObjectName("attack3TextEdit")
        self.attack3TextEdit.setEnabled(True)
        self.attack3TextEdit.setReadOnly(True)

        self.horizontalLayout_15.addWidget(self.attack3TextEdit)


        self.formLayout.setLayout(14, QFormLayout.FieldRole, self.horizontalLayout_15)

        self.line_3 = QFrame(self.scrollAreaWidgetContents)
        self.line_3.setObjectName("line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(15, QFormLayout.FieldRole, self.line_3)

        self.label_17 = QLabel(self.scrollAreaWidgetContents)
        self.label_17.setObjectName("label_17")

        self.formLayout.setWidget(16, QFormLayout.LabelRole, self.label_17)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.pain1StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.pain1StrrefSpin.setObjectName("pain1StrrefSpin")
        self.pain1StrrefSpin.setMinimumSize(QSize(90, 0))
        self.pain1StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.pain1StrrefSpin.setMinimum(-1)
        self.pain1StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_16.addWidget(self.pain1StrrefSpin)

        self.pain1SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.pain1SoundEdit.setObjectName("pain1SoundEdit")
        self.pain1SoundEdit.setEnabled(True)
        self.pain1SoundEdit.setMinimumSize(QSize(150, 0))
        self.pain1SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.pain1SoundEdit.setReadOnly(True)

        self.horizontalLayout_16.addWidget(self.pain1SoundEdit)

        self.pain1TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.pain1TextEdit.setObjectName("pain1TextEdit")
        self.pain1TextEdit.setEnabled(True)
        self.pain1TextEdit.setReadOnly(True)

        self.horizontalLayout_16.addWidget(self.pain1TextEdit)


        self.formLayout.setLayout(16, QFormLayout.FieldRole, self.horizontalLayout_16)

        self.label_18 = QLabel(self.scrollAreaWidgetContents)
        self.label_18.setObjectName("label_18")

        self.formLayout.setWidget(17, QFormLayout.LabelRole, self.label_18)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.pain2StrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.pain2StrrefSpin.setObjectName("pain2StrrefSpin")
        self.pain2StrrefSpin.setMinimumSize(QSize(90, 0))
        self.pain2StrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.pain2StrrefSpin.setMinimum(-1)
        self.pain2StrrefSpin.setMaximum(999999999)

        self.horizontalLayout_17.addWidget(self.pain2StrrefSpin)

        self.pain2SoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.pain2SoundEdit.setObjectName("pain2SoundEdit")
        self.pain2SoundEdit.setEnabled(True)
        self.pain2SoundEdit.setMinimumSize(QSize(150, 0))
        self.pain2SoundEdit.setMaximumSize(QSize(150, 16777215))
        self.pain2SoundEdit.setReadOnly(True)

        self.horizontalLayout_17.addWidget(self.pain2SoundEdit)

        self.pain2TextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.pain2TextEdit.setObjectName("pain2TextEdit")
        self.pain2TextEdit.setEnabled(True)
        self.pain2TextEdit.setReadOnly(True)

        self.horizontalLayout_17.addWidget(self.pain2TextEdit)


        self.formLayout.setLayout(17, QFormLayout.FieldRole, self.horizontalLayout_17)

        self.label_19 = QLabel(self.scrollAreaWidgetContents)
        self.label_19.setObjectName("label_19")

        self.formLayout.setWidget(18, QFormLayout.LabelRole, self.label_19)

        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setObjectName("horizontalLayout_33")
        self.lowHpStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.lowHpStrrefSpin.setObjectName("lowHpStrrefSpin")
        self.lowHpStrrefSpin.setMinimumSize(QSize(90, 0))
        self.lowHpStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.lowHpStrrefSpin.setMinimum(-1)
        self.lowHpStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_33.addWidget(self.lowHpStrrefSpin)

        self.lowHpSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.lowHpSoundEdit.setObjectName("lowHpSoundEdit")
        self.lowHpSoundEdit.setEnabled(True)
        self.lowHpSoundEdit.setMinimumSize(QSize(150, 0))
        self.lowHpSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.lowHpSoundEdit.setReadOnly(True)

        self.horizontalLayout_33.addWidget(self.lowHpSoundEdit)

        self.lowHpTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.lowHpTextEdit.setObjectName("lowHpTextEdit")
        self.lowHpTextEdit.setEnabled(True)
        self.lowHpTextEdit.setReadOnly(True)

        self.horizontalLayout_33.addWidget(self.lowHpTextEdit)


        self.formLayout.setLayout(18, QFormLayout.FieldRole, self.horizontalLayout_33)

        self.label_45 = QLabel(self.scrollAreaWidgetContents)
        self.label_45.setObjectName("label_45")

        self.formLayout.setWidget(19, QFormLayout.LabelRole, self.label_45)

        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setObjectName("horizontalLayout_34")
        self.deadStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.deadStrrefSpin.setObjectName("deadStrrefSpin")
        self.deadStrrefSpin.setMinimumSize(QSize(90, 0))
        self.deadStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.deadStrrefSpin.setMinimum(-1)
        self.deadStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_34.addWidget(self.deadStrrefSpin)

        self.deadSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.deadSoundEdit.setObjectName("deadSoundEdit")
        self.deadSoundEdit.setEnabled(True)
        self.deadSoundEdit.setMinimumSize(QSize(150, 0))
        self.deadSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.deadSoundEdit.setReadOnly(True)

        self.horizontalLayout_34.addWidget(self.deadSoundEdit)

        self.deadTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.deadTextEdit.setObjectName("deadTextEdit")
        self.deadTextEdit.setEnabled(True)
        self.deadTextEdit.setReadOnly(True)

        self.horizontalLayout_34.addWidget(self.deadTextEdit)


        self.formLayout.setLayout(19, QFormLayout.FieldRole, self.horizontalLayout_34)

        self.label_44 = QLabel(self.scrollAreaWidgetContents)
        self.label_44.setObjectName("label_44")

        self.formLayout.setWidget(20, QFormLayout.LabelRole, self.label_44)

        self.horizontalLayout_35 = QHBoxLayout()
        self.horizontalLayout_35.setObjectName("horizontalLayout_35")
        self.criticalStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.criticalStrrefSpin.setObjectName("criticalStrrefSpin")
        self.criticalStrrefSpin.setMinimumSize(QSize(90, 0))
        self.criticalStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.criticalStrrefSpin.setMinimum(-1)
        self.criticalStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_35.addWidget(self.criticalStrrefSpin)

        self.criticalSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.criticalSoundEdit.setObjectName("criticalSoundEdit")
        self.criticalSoundEdit.setEnabled(True)
        self.criticalSoundEdit.setMinimumSize(QSize(150, 0))
        self.criticalSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.criticalSoundEdit.setReadOnly(True)

        self.horizontalLayout_35.addWidget(self.criticalSoundEdit)

        self.criticalTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.criticalTextEdit.setObjectName("criticalTextEdit")
        self.criticalTextEdit.setEnabled(True)
        self.criticalTextEdit.setReadOnly(True)

        self.horizontalLayout_35.addWidget(self.criticalTextEdit)


        self.formLayout.setLayout(20, QFormLayout.FieldRole, self.horizontalLayout_35)

        self.label_43 = QLabel(self.scrollAreaWidgetContents)
        self.label_43.setObjectName("label_43")

        self.formLayout.setWidget(21, QFormLayout.LabelRole, self.label_43)

        self.horizontalLayout_36 = QHBoxLayout()
        self.horizontalLayout_36.setObjectName("horizontalLayout_36")
        self.immuneStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.immuneStrrefSpin.setObjectName("immuneStrrefSpin")
        self.immuneStrrefSpin.setMinimumSize(QSize(90, 0))
        self.immuneStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.immuneStrrefSpin.setMinimum(-1)
        self.immuneStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_36.addWidget(self.immuneStrrefSpin)

        self.immuneSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.immuneSoundEdit.setObjectName("immuneSoundEdit")
        self.immuneSoundEdit.setEnabled(True)
        self.immuneSoundEdit.setMinimumSize(QSize(150, 0))
        self.immuneSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.immuneSoundEdit.setReadOnly(True)

        self.horizontalLayout_36.addWidget(self.immuneSoundEdit)

        self.immuneTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.immuneTextEdit.setObjectName("immuneTextEdit")
        self.immuneTextEdit.setEnabled(True)
        self.immuneTextEdit.setReadOnly(True)

        self.horizontalLayout_36.addWidget(self.immuneTextEdit)


        self.formLayout.setLayout(21, QFormLayout.FieldRole, self.horizontalLayout_36)

        self.line_7 = QFrame(self.scrollAreaWidgetContents)
        self.line_7.setObjectName("line_7")
        self.line_7.setFrameShape(QFrame.HLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(22, QFormLayout.FieldRole, self.line_7)

        self.label_21 = QLabel(self.scrollAreaWidgetContents)
        self.label_21.setObjectName("label_21")

        self.formLayout.setWidget(23, QFormLayout.LabelRole, self.label_21)

        self.horizontalLayout_37 = QHBoxLayout()
        self.horizontalLayout_37.setObjectName("horizontalLayout_37")
        self.layMineStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.layMineStrrefSpin.setObjectName("layMineStrrefSpin")
        self.layMineStrrefSpin.setMinimumSize(QSize(90, 0))
        self.layMineStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.layMineStrrefSpin.setMinimum(-1)
        self.layMineStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_37.addWidget(self.layMineStrrefSpin)

        self.layMineSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.layMineSoundEdit.setObjectName("layMineSoundEdit")
        self.layMineSoundEdit.setEnabled(True)
        self.layMineSoundEdit.setMinimumSize(QSize(150, 0))
        self.layMineSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.layMineSoundEdit.setReadOnly(True)

        self.horizontalLayout_37.addWidget(self.layMineSoundEdit)

        self.layMineTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.layMineTextEdit.setObjectName("layMineTextEdit")
        self.layMineTextEdit.setEnabled(True)
        self.layMineTextEdit.setReadOnly(True)

        self.horizontalLayout_37.addWidget(self.layMineTextEdit)


        self.formLayout.setLayout(23, QFormLayout.FieldRole, self.horizontalLayout_37)

        self.label_53 = QLabel(self.scrollAreaWidgetContents)
        self.label_53.setObjectName("label_53")

        self.formLayout.setWidget(24, QFormLayout.LabelRole, self.label_53)

        self.horizontalLayout_46 = QHBoxLayout()
        self.horizontalLayout_46.setObjectName("horizontalLayout_46")
        self.disarmMineStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.disarmMineStrrefSpin.setObjectName("disarmMineStrrefSpin")
        self.disarmMineStrrefSpin.setMinimumSize(QSize(90, 0))
        self.disarmMineStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.disarmMineStrrefSpin.setMinimum(-1)
        self.disarmMineStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_46.addWidget(self.disarmMineStrrefSpin)

        self.disarmMineSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.disarmMineSoundEdit.setObjectName("disarmMineSoundEdit")
        self.disarmMineSoundEdit.setEnabled(True)
        self.disarmMineSoundEdit.setMinimumSize(QSize(150, 0))
        self.disarmMineSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.disarmMineSoundEdit.setReadOnly(True)

        self.horizontalLayout_46.addWidget(self.disarmMineSoundEdit)

        self.disarmMineTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.disarmMineTextEdit.setObjectName("disarmMineTextEdit")
        self.disarmMineTextEdit.setEnabled(True)
        self.disarmMineTextEdit.setReadOnly(True)

        self.horizontalLayout_46.addWidget(self.disarmMineTextEdit)


        self.formLayout.setLayout(24, QFormLayout.FieldRole, self.horizontalLayout_46)

        self.label_20 = QLabel(self.scrollAreaWidgetContents)
        self.label_20.setObjectName("label_20")

        self.formLayout.setWidget(26, QFormLayout.LabelRole, self.label_20)

        self.horizontalLayout_39 = QHBoxLayout()
        self.horizontalLayout_39.setObjectName("horizontalLayout_39")
        self.beginStealthStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.beginStealthStrrefSpin.setObjectName("beginStealthStrrefSpin")
        self.beginStealthStrrefSpin.setMinimumSize(QSize(90, 0))
        self.beginStealthStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.beginStealthStrrefSpin.setMinimum(-1)
        self.beginStealthStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_39.addWidget(self.beginStealthStrrefSpin)

        self.beginStealthSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.beginStealthSoundEdit.setObjectName("beginStealthSoundEdit")
        self.beginStealthSoundEdit.setEnabled(True)
        self.beginStealthSoundEdit.setMinimumSize(QSize(150, 0))
        self.beginStealthSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.beginStealthSoundEdit.setReadOnly(True)

        self.horizontalLayout_39.addWidget(self.beginStealthSoundEdit)

        self.beginStealthTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.beginStealthTextEdit.setObjectName("beginStealthTextEdit")
        self.beginStealthTextEdit.setEnabled(True)
        self.beginStealthTextEdit.setReadOnly(True)

        self.horizontalLayout_39.addWidget(self.beginStealthTextEdit)


        self.formLayout.setLayout(26, QFormLayout.FieldRole, self.horizontalLayout_39)

        self.label_51 = QLabel(self.scrollAreaWidgetContents)
        self.label_51.setObjectName("label_51")

        self.formLayout.setWidget(27, QFormLayout.LabelRole, self.label_51)

        self.horizontalLayout_38 = QHBoxLayout()
        self.horizontalLayout_38.setObjectName("horizontalLayout_38")
        self.beginSearchStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.beginSearchStrrefSpin.setObjectName("beginSearchStrrefSpin")
        self.beginSearchStrrefSpin.setMinimumSize(QSize(90, 0))
        self.beginSearchStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.beginSearchStrrefSpin.setMinimum(-1)
        self.beginSearchStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_38.addWidget(self.beginSearchStrrefSpin)

        self.beginSearchSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.beginSearchSoundEdit.setObjectName("beginSearchSoundEdit")
        self.beginSearchSoundEdit.setEnabled(True)
        self.beginSearchSoundEdit.setMinimumSize(QSize(150, 0))
        self.beginSearchSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.beginSearchSoundEdit.setReadOnly(True)

        self.horizontalLayout_38.addWidget(self.beginSearchSoundEdit)

        self.beginSearchTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.beginSearchTextEdit.setObjectName("beginSearchTextEdit")
        self.beginSearchTextEdit.setEnabled(True)
        self.beginSearchTextEdit.setReadOnly(True)

        self.horizontalLayout_38.addWidget(self.beginSearchTextEdit)


        self.formLayout.setLayout(27, QFormLayout.FieldRole, self.horizontalLayout_38)

        self.label_49 = QLabel(self.scrollAreaWidgetContents)
        self.label_49.setObjectName("label_49")

        self.formLayout.setWidget(29, QFormLayout.LabelRole, self.label_49)

        self.horizontalLayout_40 = QHBoxLayout()
        self.horizontalLayout_40.setObjectName("horizontalLayout_40")
        self.beginUnlockStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.beginUnlockStrrefSpin.setObjectName("beginUnlockStrrefSpin")
        self.beginUnlockStrrefSpin.setMinimumSize(QSize(90, 0))
        self.beginUnlockStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.beginUnlockStrrefSpin.setMinimum(-1)
        self.beginUnlockStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_40.addWidget(self.beginUnlockStrrefSpin)

        self.beginUnlockSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.beginUnlockSoundEdit.setObjectName("beginUnlockSoundEdit")
        self.beginUnlockSoundEdit.setEnabled(True)
        self.beginUnlockSoundEdit.setMinimumSize(QSize(150, 0))
        self.beginUnlockSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.beginUnlockSoundEdit.setReadOnly(True)

        self.horizontalLayout_40.addWidget(self.beginUnlockSoundEdit)

        self.beginUnlockTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.beginUnlockTextEdit.setObjectName("beginUnlockTextEdit")
        self.beginUnlockTextEdit.setEnabled(True)
        self.beginUnlockTextEdit.setReadOnly(True)

        self.horizontalLayout_40.addWidget(self.beginUnlockTextEdit)


        self.formLayout.setLayout(29, QFormLayout.FieldRole, self.horizontalLayout_40)

        self.label_50 = QLabel(self.scrollAreaWidgetContents)
        self.label_50.setObjectName("label_50")

        self.formLayout.setWidget(30, QFormLayout.LabelRole, self.label_50)

        self.horizontalLayout_41 = QHBoxLayout()
        self.horizontalLayout_41.setObjectName("horizontalLayout_41")
        self.unlockFailedStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.unlockFailedStrrefSpin.setObjectName("unlockFailedStrrefSpin")
        self.unlockFailedStrrefSpin.setMinimumSize(QSize(90, 0))
        self.unlockFailedStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.unlockFailedStrrefSpin.setMinimum(-1)
        self.unlockFailedStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_41.addWidget(self.unlockFailedStrrefSpin)

        self.unlockFailedSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.unlockFailedSoundEdit.setObjectName("unlockFailedSoundEdit")
        self.unlockFailedSoundEdit.setEnabled(True)
        self.unlockFailedSoundEdit.setMinimumSize(QSize(150, 0))
        self.unlockFailedSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.unlockFailedSoundEdit.setReadOnly(True)

        self.horizontalLayout_41.addWidget(self.unlockFailedSoundEdit)

        self.unlockFailedTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.unlockFailedTextEdit.setObjectName("unlockFailedTextEdit")
        self.unlockFailedTextEdit.setEnabled(True)
        self.unlockFailedTextEdit.setReadOnly(True)

        self.horizontalLayout_41.addWidget(self.unlockFailedTextEdit)


        self.formLayout.setLayout(30, QFormLayout.FieldRole, self.horizontalLayout_41)

        self.label_48 = QLabel(self.scrollAreaWidgetContents)
        self.label_48.setObjectName("label_48")

        self.formLayout.setWidget(31, QFormLayout.LabelRole, self.label_48)

        self.horizontalLayout_42 = QHBoxLayout()
        self.horizontalLayout_42.setObjectName("horizontalLayout_42")
        self.unlockSuccessStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.unlockSuccessStrrefSpin.setObjectName("unlockSuccessStrrefSpin")
        self.unlockSuccessStrrefSpin.setMinimumSize(QSize(90, 0))
        self.unlockSuccessStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.unlockSuccessStrrefSpin.setMinimum(-1)
        self.unlockSuccessStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_42.addWidget(self.unlockSuccessStrrefSpin)

        self.unlockSuccessSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.unlockSuccessSoundEdit.setObjectName("unlockSuccessSoundEdit")
        self.unlockSuccessSoundEdit.setEnabled(True)
        self.unlockSuccessSoundEdit.setMinimumSize(QSize(150, 0))
        self.unlockSuccessSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.unlockSuccessSoundEdit.setReadOnly(True)

        self.horizontalLayout_42.addWidget(self.unlockSuccessSoundEdit)

        self.unlockSuccessTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.unlockSuccessTextEdit.setObjectName("unlockSuccessTextEdit")
        self.unlockSuccessTextEdit.setEnabled(True)
        self.unlockSuccessTextEdit.setReadOnly(True)

        self.horizontalLayout_42.addWidget(self.unlockSuccessTextEdit)


        self.formLayout.setLayout(31, QFormLayout.FieldRole, self.horizontalLayout_42)

        self.label_47 = QLabel(self.scrollAreaWidgetContents)
        self.label_47.setObjectName("label_47")

        self.formLayout.setWidget(33, QFormLayout.LabelRole, self.label_47)

        self.horizontalLayout_43 = QHBoxLayout()
        self.horizontalLayout_43.setObjectName("horizontalLayout_43")
        self.partySeparatedStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.partySeparatedStrrefSpin.setObjectName("partySeparatedStrrefSpin")
        self.partySeparatedStrrefSpin.setMinimumSize(QSize(90, 0))
        self.partySeparatedStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.partySeparatedStrrefSpin.setMinimum(-1)
        self.partySeparatedStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_43.addWidget(self.partySeparatedStrrefSpin)

        self.partySeparatedSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.partySeparatedSoundEdit.setObjectName("partySeparatedSoundEdit")
        self.partySeparatedSoundEdit.setEnabled(True)
        self.partySeparatedSoundEdit.setMinimumSize(QSize(150, 0))
        self.partySeparatedSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.partySeparatedSoundEdit.setReadOnly(True)

        self.horizontalLayout_43.addWidget(self.partySeparatedSoundEdit)

        self.partySeparatedTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.partySeparatedTextEdit.setObjectName("partySeparatedTextEdit")
        self.partySeparatedTextEdit.setEnabled(True)
        self.partySeparatedTextEdit.setReadOnly(True)

        self.horizontalLayout_43.addWidget(self.partySeparatedTextEdit)


        self.formLayout.setLayout(33, QFormLayout.FieldRole, self.horizontalLayout_43)

        self.label_46 = QLabel(self.scrollAreaWidgetContents)
        self.label_46.setObjectName("label_46")

        self.formLayout.setWidget(34, QFormLayout.LabelRole, self.label_46)

        self.horizontalLayout_44 = QHBoxLayout()
        self.horizontalLayout_44.setObjectName("horizontalLayout_44")
        self.rejoinPartyStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.rejoinPartyStrrefSpin.setObjectName("rejoinPartyStrrefSpin")
        self.rejoinPartyStrrefSpin.setMinimumSize(QSize(90, 0))
        self.rejoinPartyStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.rejoinPartyStrrefSpin.setMinimum(-1)
        self.rejoinPartyStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_44.addWidget(self.rejoinPartyStrrefSpin)

        self.rejoinPartySoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.rejoinPartySoundEdit.setObjectName("rejoinPartySoundEdit")
        self.rejoinPartySoundEdit.setEnabled(True)
        self.rejoinPartySoundEdit.setMinimumSize(QSize(150, 0))
        self.rejoinPartySoundEdit.setMaximumSize(QSize(150, 16777215))
        self.rejoinPartySoundEdit.setReadOnly(True)

        self.horizontalLayout_44.addWidget(self.rejoinPartySoundEdit)

        self.rejoinPartyTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.rejoinPartyTextEdit.setObjectName("rejoinPartyTextEdit")
        self.rejoinPartyTextEdit.setEnabled(True)
        self.rejoinPartyTextEdit.setReadOnly(True)

        self.horizontalLayout_44.addWidget(self.rejoinPartyTextEdit)


        self.formLayout.setLayout(34, QFormLayout.FieldRole, self.horizontalLayout_44)

        self.label_52 = QLabel(self.scrollAreaWidgetContents)
        self.label_52.setObjectName("label_52")

        self.formLayout.setWidget(36, QFormLayout.LabelRole, self.label_52)

        self.horizontalLayout_45 = QHBoxLayout()
        self.horizontalLayout_45.setObjectName("horizontalLayout_45")
        self.poisonedStrrefSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.poisonedStrrefSpin.setObjectName("poisonedStrrefSpin")
        self.poisonedStrrefSpin.setMinimumSize(QSize(90, 0))
        self.poisonedStrrefSpin.setMaximumSize(QSize(90, 16777215))
        self.poisonedStrrefSpin.setMinimum(-1)
        self.poisonedStrrefSpin.setMaximum(999999999)

        self.horizontalLayout_45.addWidget(self.poisonedStrrefSpin)

        self.poisonedSoundEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.poisonedSoundEdit.setObjectName("poisonedSoundEdit")
        self.poisonedSoundEdit.setEnabled(True)
        self.poisonedSoundEdit.setMinimumSize(QSize(150, 0))
        self.poisonedSoundEdit.setMaximumSize(QSize(150, 16777215))
        self.poisonedSoundEdit.setReadOnly(True)

        self.horizontalLayout_45.addWidget(self.poisonedSoundEdit)

        self.poisonedTextEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.poisonedTextEdit.setObjectName("poisonedTextEdit")
        self.poisonedTextEdit.setEnabled(True)
        self.poisonedTextEdit.setReadOnly(True)

        self.horizontalLayout_45.addWidget(self.poisonedTextEdit)


        self.formLayout.setLayout(36, QFormLayout.FieldRole, self.horizontalLayout_45)

        self.line_8 = QFrame(self.scrollAreaWidgetContents)
        self.line_8.setObjectName("line_8")
        self.line_8.setFrameShape(QFrame.HLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(25, QFormLayout.FieldRole, self.line_8)

        self.line_9 = QFrame(self.scrollAreaWidgetContents)
        self.line_9.setObjectName("line_9")
        self.line_9.setFrameShape(QFrame.HLine)
        self.line_9.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(28, QFormLayout.FieldRole, self.line_9)

        self.line_10 = QFrame(self.scrollAreaWidgetContents)
        self.line_10.setObjectName("line_10")
        self.line_10.setFrameShape(QFrame.HLine)
        self.line_10.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(32, QFormLayout.FieldRole, self.line_10)

        self.line_11 = QFrame(self.scrollAreaWidgetContents)
        self.line_11.setObjectName("line_11")
        self.line_11.setFrameShape(QFrame.HLine)
        self.line_11.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(35, QFormLayout.FieldRole, self.line_11)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 577, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuTools.addAction(self.actionSetTLK)

        self.retranslateUi(MainWindow)

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
        self.actionSetTLK.setText(QCoreApplication.translate("MainWindow", "Set TLK", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">Sound</span></p></body></html>", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">TLK StringRef</span></p></body></html>", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">Sound ResRef</span></p></body></html>", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">String Text</span></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Battlecry 1", None))
        self.battlecry1TextEdit.setText("")
        self.label_6.setText(QCoreApplication.translate("MainWindow", "Battlecry 2", None))
        self.battlecry2TextEdit.setText("")
        self.label_7.setText(QCoreApplication.translate("MainWindow", "Battlecry 3", None))
        self.battlecry3TextEdit.setText("")
        self.label_8.setText(QCoreApplication.translate("MainWindow", "Battlecry 4", None))
        self.battlecry4TextEdit.setText("")
        self.label_9.setText(QCoreApplication.translate("MainWindow", "Battlecry 5", None))
        self.battlecry5TextEdit.setText("")
        self.label_10.setText(QCoreApplication.translate("MainWindow", "Battlecry 6", None))
        self.battlecry6TextEdit.setText("")
        self.label_11.setText(QCoreApplication.translate("MainWindow", "Select 1", None))
        self.select1TextEdit.setText("")
        self.label_12.setText(QCoreApplication.translate("MainWindow", "Select 2", None))
        self.select2TextEdit.setText("")
        self.label_13.setText(QCoreApplication.translate("MainWindow", "Select 3", None))
        self.select3TextEdit.setText("")
        self.label_14.setText(QCoreApplication.translate("MainWindow", "Attack Grunt 1", None))
        self.attack1TextEdit.setText("")
        self.label_15.setText(QCoreApplication.translate("MainWindow", "Attack Grunt 2", None))
        self.attack2TextEdit.setText("")
        self.label_16.setText(QCoreApplication.translate("MainWindow", "Attack Grunt 3", None))
        self.attack3TextEdit.setText("")
        self.label_17.setText(QCoreApplication.translate("MainWindow", "Pain Grunt 1", None))
        self.pain1TextEdit.setText("")
        self.label_18.setText(QCoreApplication.translate("MainWindow", "Pain Grunt 2", None))
        self.pain2TextEdit.setText("")
        self.label_19.setText(QCoreApplication.translate("MainWindow", "Low Health", None))
        self.lowHpTextEdit.setText("")
        self.label_45.setText(QCoreApplication.translate("MainWindow", "Dead", None))
        self.deadTextEdit.setText("")
        self.label_44.setText(QCoreApplication.translate("MainWindow", "Critical Hit", None))
        self.criticalTextEdit.setText("")
        self.label_43.setText(QCoreApplication.translate("MainWindow", "Target Immune", None))
        self.immuneTextEdit.setText("")
        self.label_21.setText(QCoreApplication.translate("MainWindow", "Lay Mine", None))
        self.layMineTextEdit.setText("")
        self.label_53.setText(QCoreApplication.translate("MainWindow", "Disarm Mine", None))
        self.disarmMineTextEdit.setText("")
        self.label_20.setText(QCoreApplication.translate("MainWindow", "Begin Stealth", None))
        self.beginStealthTextEdit.setText("")
        self.label_51.setText(QCoreApplication.translate("MainWindow", "Begin Search", None))
        self.beginSearchTextEdit.setText("")
        self.label_49.setText(QCoreApplication.translate("MainWindow", "Begin Unlock", None))
        self.beginUnlockTextEdit.setText("")
        self.label_50.setText(QCoreApplication.translate("MainWindow", "Unlock Failed", None))
        self.unlockFailedTextEdit.setText("")
        self.label_48.setText(QCoreApplication.translate("MainWindow", "Unlock Success", None))
        self.unlockSuccessTextEdit.setText("")
        self.label_47.setText(QCoreApplication.translate("MainWindow", "Party Separated", None))
        self.partySeparatedTextEdit.setText("")
        self.label_46.setText(QCoreApplication.translate("MainWindow", "Rejoin Party", None))
        self.rejoinPartyTextEdit.setText("")
        self.label_52.setText(QCoreApplication.translate("MainWindow", "Poisoned", None))
        self.poisonedTextEdit.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", "Tools", None))
    # retranslateUi

