# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'module_designer.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QSpacerItem,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from toolset.gui.widgets.edit.color import ColorEdit
from toolset.gui.widgets.set_bind import SetBindWidget

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(453, 767)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(Form)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, -686, 416, 1767))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_20 = QLabel(self.scrollAreaWidgetContents)
        self.label_20.setObjectName(u"label_20")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_20)

        self.fovSpin = QSpinBox(self.scrollAreaWidgetContents)
        self.fovSpin.setObjectName(u"fovSpin")
        self.fovSpin.setMinimum(40)
        self.fovSpin.setMaximum(160)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.fovSpin)


        self.verticalLayout.addLayout(self.formLayout_3)

        self.tabWidget = QTabWidget(self.scrollAreaWidgetContents)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab3DControls = QWidget()
        self.tab3DControls.setObjectName(u"tab3DControls")
        self.verticalLayout_2 = QVBoxLayout(self.tab3DControls)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.controls3dResetButton = QPushButton(self.tab3DControls)
        self.controls3dResetButton.setObjectName(u"controls3dResetButton")

        self.horizontalLayout_3.addWidget(self.controls3dResetButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.line = QFrame(self.tab3DControls)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.label602 = QLabel(self.tab3DControls)
        self.label602.setObjectName(u"label602")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label602)

        self.moveCameraSensitivity3dEdit = QSlider(self.tab3DControls)
        self.moveCameraSensitivity3dEdit.setObjectName(u"moveCameraSensitivity3dEdit")
        self.moveCameraSensitivity3dEdit.setMinimum(10)
        self.moveCameraSensitivity3dEdit.setMaximum(1000)
        self.moveCameraSensitivity3dEdit.setOrientation(Qt.Horizontal)

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.moveCameraSensitivity3dEdit)

        self.label_41 = QLabel(self.tab3DControls)
        self.label_41.setObjectName(u"label_41")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_41)

        self.rotateCameraSensitivity3dEdit = QSlider(self.tab3DControls)
        self.rotateCameraSensitivity3dEdit.setObjectName(u"rotateCameraSensitivity3dEdit")
        self.rotateCameraSensitivity3dEdit.setMinimum(10)
        self.rotateCameraSensitivity3dEdit.setMaximum(1000)
        self.rotateCameraSensitivity3dEdit.setOrientation(Qt.Horizontal)

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.rotateCameraSensitivity3dEdit)

        self.label_42 = QLabel(self.tab3DControls)
        self.label_42.setObjectName(u"label_42")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.label_42)

        self.zoomCameraSensitivity3dEdit = QSlider(self.tab3DControls)
        self.zoomCameraSensitivity3dEdit.setObjectName(u"zoomCameraSensitivity3dEdit")
        self.zoomCameraSensitivity3dEdit.setMinimum(10)
        self.zoomCameraSensitivity3dEdit.setMaximum(1000)
        self.zoomCameraSensitivity3dEdit.setOrientation(Qt.Horizontal)

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.zoomCameraSensitivity3dEdit)

        self.label = QLabel(self.tab3DControls)
        self.label.setObjectName(u"label")

        self.formLayout_5.setWidget(3, QFormLayout.LabelRole, self.label)

        self.boostedMoveCameraSensitivity3dEdit = QSlider(self.tab3DControls)
        self.boostedMoveCameraSensitivity3dEdit.setObjectName(u"boostedMoveCameraSensitivity3dEdit")
        self.boostedMoveCameraSensitivity3dEdit.setMinimum(10)
        self.boostedMoveCameraSensitivity3dEdit.setMaximum(1000)
        self.boostedMoveCameraSensitivity3dEdit.setOrientation(Qt.Horizontal)

        self.formLayout_5.setWidget(3, QFormLayout.FieldRole, self.boostedMoveCameraSensitivity3dEdit)


        self.verticalLayout_2.addLayout(self.formLayout_5)

        self.line_2 = QFrame(self.tab3DControls)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setVerticalSpacing(10)
        self.label_2 = QLabel(self.tab3DControls)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(110, 0))
        self.label_2.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.moveCameraXY3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraXY3dBindEdit.setObjectName(u"moveCameraXY3dBindEdit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.moveCameraXY3dBindEdit)

        self.label_12 = QLabel(self.tab3DControls)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMinimumSize(QSize(110, 0))
        self.label_12.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_12.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_12)

        self.moveCameraZ3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraZ3dBindEdit.setObjectName(u"moveCameraZ3dBindEdit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.moveCameraZ3dBindEdit)

        self.label_3 = QLabel(self.tab3DControls)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(110, 0))
        self.label_3.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_3.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.rotateCamera3dBindEdit = SetBindWidget(self.tab3DControls)
        self.rotateCamera3dBindEdit.setObjectName(u"rotateCamera3dBindEdit")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.rotateCamera3dBindEdit)

        self.label_4 = QLabel(self.tab3DControls)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(110, 0))
        self.label_4.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_4.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.zoomCamera3dBindEdit = SetBindWidget(self.tab3DControls)
        self.zoomCamera3dBindEdit.setObjectName(u"zoomCamera3dBindEdit")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.zoomCamera3dBindEdit)

        self.label_9 = QLabel(self.tab3DControls)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setMinimumSize(QSize(110, 0))
        self.label_9.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_9.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_9)

        self.zoomCameraMM3dBindEdit = SetBindWidget(self.tab3DControls)
        self.zoomCameraMM3dBindEdit.setObjectName(u"zoomCameraMM3dBindEdit")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.zoomCameraMM3dBindEdit)

        self.label_10 = QLabel(self.tab3DControls)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setMinimumSize(QSize(110, 0))
        self.label_10.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_10.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_10)

        self.moveSelectedXY3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveSelectedXY3dBindEdit.setObjectName(u"moveSelectedXY3dBindEdit")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.moveSelectedXY3dBindEdit)

        self.label_11 = QLabel(self.tab3DControls)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setMinimumSize(QSize(110, 0))
        self.label_11.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_11.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_11)

        self.moveSelectedZ3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveSelectedZ3dBindEdit.setObjectName(u"moveSelectedZ3dBindEdit")

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.moveSelectedZ3dBindEdit)

        self.label_5 = QLabel(self.tab3DControls)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMinimumSize(QSize(110, 0))
        self.label_5.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_5.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(8, QFormLayout.LabelRole, self.label_5)

        self.selectObject3dBindEdit = SetBindWidget(self.tab3DControls)
        self.selectObject3dBindEdit.setObjectName(u"selectObject3dBindEdit")

        self.formLayout.setWidget(8, QFormLayout.FieldRole, self.selectObject3dBindEdit)

        self.label_6 = QLabel(self.tab3DControls)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMinimumSize(QSize(110, 0))
        self.label_6.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_6.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(9, QFormLayout.LabelRole, self.label_6)

        self.rotateObject3dBindEdit = SetBindWidget(self.tab3DControls)
        self.rotateObject3dBindEdit.setObjectName(u"rotateObject3dBindEdit")

        self.formLayout.setWidget(9, QFormLayout.FieldRole, self.rotateObject3dBindEdit)

        self.line_3 = QFrame(self.tab3DControls)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.formLayout.setWidget(11, QFormLayout.FieldRole, self.line_3)

        self.label_7 = QLabel(self.tab3DControls)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMinimumSize(QSize(110, 0))
        self.label_7.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_7.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(15, QFormLayout.LabelRole, self.label_7)

        self.deleteObject3dBindEdit = SetBindWidget(self.tab3DControls)
        self.deleteObject3dBindEdit.setObjectName(u"deleteObject3dBindEdit")

        self.formLayout.setWidget(15, QFormLayout.FieldRole, self.deleteObject3dBindEdit)

        self.label_46 = QLabel(self.tab3DControls)
        self.label_46.setObjectName(u"label_46")
        self.label_46.setMinimumSize(QSize(110, 0))
        self.label_46.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_46.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(16, QFormLayout.LabelRole, self.label_46)

        self.rotateCameraLeft3dBindEdit = SetBindWidget(self.tab3DControls)
        self.rotateCameraLeft3dBindEdit.setObjectName(u"rotateCameraLeft3dBindEdit")

        self.formLayout.setWidget(16, QFormLayout.FieldRole, self.rotateCameraLeft3dBindEdit)

        self.label_47 = QLabel(self.tab3DControls)
        self.label_47.setObjectName(u"label_47")
        self.label_47.setMinimumSize(QSize(110, 0))
        self.label_47.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_47.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(17, QFormLayout.LabelRole, self.label_47)

        self.rotateCameraRight3dBindEdit = SetBindWidget(self.tab3DControls)
        self.rotateCameraRight3dBindEdit.setObjectName(u"rotateCameraRight3dBindEdit")

        self.formLayout.setWidget(17, QFormLayout.FieldRole, self.rotateCameraRight3dBindEdit)

        self.label_48 = QLabel(self.tab3DControls)
        self.label_48.setObjectName(u"label_48")
        self.label_48.setMinimumSize(QSize(110, 0))
        self.label_48.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_48.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(18, QFormLayout.LabelRole, self.label_48)

        self.rotateCameraUp3dBindEdit = SetBindWidget(self.tab3DControls)
        self.rotateCameraUp3dBindEdit.setObjectName(u"rotateCameraUp3dBindEdit")

        self.formLayout.setWidget(18, QFormLayout.FieldRole, self.rotateCameraUp3dBindEdit)

        self.label_49 = QLabel(self.tab3DControls)
        self.label_49.setObjectName(u"label_49")
        self.label_49.setMinimumSize(QSize(110, 0))
        self.label_49.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_49.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(19, QFormLayout.LabelRole, self.label_49)

        self.rotateCameraDown3dBindEdit = SetBindWidget(self.tab3DControls)
        self.rotateCameraDown3dBindEdit.setObjectName(u"rotateCameraDown3dBindEdit")

        self.formLayout.setWidget(19, QFormLayout.FieldRole, self.rotateCameraDown3dBindEdit)

        self.label_50 = QLabel(self.tab3DControls)
        self.label_50.setObjectName(u"label_50")
        self.label_50.setMinimumSize(QSize(110, 0))
        self.label_50.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_50.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(20, QFormLayout.LabelRole, self.label_50)

        self.moveCameraForward3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraForward3dBindEdit.setObjectName(u"moveCameraForward3dBindEdit")

        self.formLayout.setWidget(20, QFormLayout.FieldRole, self.moveCameraForward3dBindEdit)

        self.label_51 = QLabel(self.tab3DControls)
        self.label_51.setObjectName(u"label_51")
        self.label_51.setMinimumSize(QSize(110, 0))
        self.label_51.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_51.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(21, QFormLayout.LabelRole, self.label_51)

        self.moveCameraBackward3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraBackward3dBindEdit.setObjectName(u"moveCameraBackward3dBindEdit")

        self.formLayout.setWidget(21, QFormLayout.FieldRole, self.moveCameraBackward3dBindEdit)

        self.label_53 = QLabel(self.tab3DControls)
        self.label_53.setObjectName(u"label_53")
        self.label_53.setMinimumSize(QSize(110, 0))
        self.label_53.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_53.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(22, QFormLayout.LabelRole, self.label_53)

        self.moveCameraLeft3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraLeft3dBindEdit.setObjectName(u"moveCameraLeft3dBindEdit")

        self.formLayout.setWidget(22, QFormLayout.FieldRole, self.moveCameraLeft3dBindEdit)

        self.label_52 = QLabel(self.tab3DControls)
        self.label_52.setObjectName(u"label_52")
        self.label_52.setMinimumSize(QSize(110, 0))
        self.label_52.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_52.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(23, QFormLayout.LabelRole, self.label_52)

        self.moveCameraRight3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraRight3dBindEdit.setObjectName(u"moveCameraRight3dBindEdit")

        self.formLayout.setWidget(23, QFormLayout.FieldRole, self.moveCameraRight3dBindEdit)

        self.label_54 = QLabel(self.tab3DControls)
        self.label_54.setObjectName(u"label_54")
        self.label_54.setMinimumSize(QSize(110, 0))
        self.label_54.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_54.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(24, QFormLayout.LabelRole, self.label_54)

        self.moveCameraUp3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraUp3dBindEdit.setObjectName(u"moveCameraUp3dBindEdit")

        self.formLayout.setWidget(24, QFormLayout.FieldRole, self.moveCameraUp3dBindEdit)

        self.label_55 = QLabel(self.tab3DControls)
        self.label_55.setObjectName(u"label_55")
        self.label_55.setMinimumSize(QSize(110, 0))
        self.label_55.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_55.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(25, QFormLayout.LabelRole, self.label_55)

        self.moveCameraDown3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraDown3dBindEdit.setObjectName(u"moveCameraDown3dBindEdit")

        self.formLayout.setWidget(25, QFormLayout.FieldRole, self.moveCameraDown3dBindEdit)

        self.label_56 = QLabel(self.tab3DControls)
        self.label_56.setObjectName(u"label_56")
        self.label_56.setMinimumSize(QSize(110, 0))
        self.label_56.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_56.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(26, QFormLayout.LabelRole, self.label_56)

        self.zoomCameraIn3dBindEdit = SetBindWidget(self.tab3DControls)
        self.zoomCameraIn3dBindEdit.setObjectName(u"zoomCameraIn3dBindEdit")

        self.formLayout.setWidget(26, QFormLayout.FieldRole, self.zoomCameraIn3dBindEdit)

        self.label_57 = QLabel(self.tab3DControls)
        self.label_57.setObjectName(u"label_57")
        self.label_57.setMinimumSize(QSize(110, 0))
        self.label_57.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_57.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(27, QFormLayout.LabelRole, self.label_57)

        self.zoomCameraOut3dBindEdit = SetBindWidget(self.tab3DControls)
        self.zoomCameraOut3dBindEdit.setObjectName(u"zoomCameraOut3dBindEdit")

        self.formLayout.setWidget(27, QFormLayout.FieldRole, self.zoomCameraOut3dBindEdit)

        self.label_8 = QLabel(self.tab3DControls)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setMinimumSize(QSize(110, 0))
        self.label_8.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_8.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(12, QFormLayout.LabelRole, self.label_8)

        self.moveCameraToSelected3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraToSelected3dBindEdit.setObjectName(u"moveCameraToSelected3dBindEdit")

        self.formLayout.setWidget(12, QFormLayout.FieldRole, self.moveCameraToSelected3dBindEdit)

        self.duplicateObject3dBindEdit = SetBindWidget(self.tab3DControls)
        self.duplicateObject3dBindEdit.setObjectName(u"duplicateObject3dBindEdit")

        self.formLayout.setWidget(10, QFormLayout.FieldRole, self.duplicateObject3dBindEdit)

        self.label_58 = QLabel(self.tab3DControls)
        self.label_58.setObjectName(u"label_58")
        self.label_58.setMinimumSize(QSize(110, 0))
        self.label_58.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_58.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(10, QFormLayout.LabelRole, self.label_58)

        self.label_69 = QLabel(self.tab3DControls)
        self.label_69.setObjectName(u"label_69")
        self.label_69.setMinimumSize(QSize(110, 0))
        self.label_69.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_69.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(13, QFormLayout.LabelRole, self.label_69)

        self.moveCameraToCursor3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraToCursor3dBindEdit.setObjectName(u"moveCameraToCursor3dBindEdit")

        self.formLayout.setWidget(13, QFormLayout.FieldRole, self.moveCameraToCursor3dBindEdit)

        self.label_70 = QLabel(self.tab3DControls)
        self.label_70.setObjectName(u"label_70")
        self.label_70.setMinimumSize(QSize(110, 0))
        self.label_70.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_70.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(14, QFormLayout.LabelRole, self.label_70)

        self.moveCameraToEntryPoint3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraToEntryPoint3dBindEdit.setObjectName(u"moveCameraToEntryPoint3dBindEdit")

        self.formLayout.setWidget(14, QFormLayout.FieldRole, self.moveCameraToEntryPoint3dBindEdit)

        self.label_71 = QLabel(self.tab3DControls)
        self.label_71.setObjectName(u"label_71")
        self.label_71.setMinimumSize(QSize(110, 0))
        self.label_71.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_71.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_71)

        self.moveCameraPlane3dBindEdit = SetBindWidget(self.tab3DControls)
        self.moveCameraPlane3dBindEdit.setObjectName(u"moveCameraPlane3dBindEdit")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.moveCameraPlane3dBindEdit)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.tabWidget.addTab(self.tab3DControls, "")
        self.tab2DControls = QWidget()
        self.tab2DControls.setObjectName(u"tab2DControls")
        self.verticalLayout_3 = QVBoxLayout(self.tab2DControls)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.controls2dResetButton = QPushButton(self.tab2DControls)
        self.controls2dResetButton.setObjectName(u"controls2dResetButton")

        self.horizontalLayout_4.addWidget(self.controls2dResetButton)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.line888 = QFrame(self.tab2DControls)
        self.line888.setObjectName(u"line888")
        self.line888.setFrameShape(QFrame.HLine)
        self.line888.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line888)

        self.formLayout_6 = QFormLayout()
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.label_43 = QLabel(self.tab2DControls)
        self.label_43.setObjectName(u"label_43")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_43)

        self.moveCameraSensitivity2dEdit = QSlider(self.tab2DControls)
        self.moveCameraSensitivity2dEdit.setObjectName(u"moveCameraSensitivity2dEdit")
        self.moveCameraSensitivity2dEdit.setMinimum(10)
        self.moveCameraSensitivity2dEdit.setMaximum(1000)
        self.moveCameraSensitivity2dEdit.setOrientation(Qt.Horizontal)

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.moveCameraSensitivity2dEdit)

        self.label_44 = QLabel(self.tab2DControls)
        self.label_44.setObjectName(u"label_44")

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.label_44)

        self.label_45 = QLabel(self.tab2DControls)
        self.label_45.setObjectName(u"label_45")

        self.formLayout_6.setWidget(2, QFormLayout.LabelRole, self.label_45)

        self.rotateCameraSensitivity2dEdit = QSlider(self.tab2DControls)
        self.rotateCameraSensitivity2dEdit.setObjectName(u"rotateCameraSensitivity2dEdit")
        self.rotateCameraSensitivity2dEdit.setMinimum(10)
        self.rotateCameraSensitivity2dEdit.setMaximum(1000)
        self.rotateCameraSensitivity2dEdit.setOrientation(Qt.Horizontal)

        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.rotateCameraSensitivity2dEdit)

        self.zoomCameraSensitivity2dEdit = QSlider(self.tab2DControls)
        self.zoomCameraSensitivity2dEdit.setObjectName(u"zoomCameraSensitivity2dEdit")
        self.zoomCameraSensitivity2dEdit.setMinimum(10)
        self.zoomCameraSensitivity2dEdit.setMaximum(1000)
        self.zoomCameraSensitivity2dEdit.setOrientation(Qt.Horizontal)

        self.formLayout_6.setWidget(2, QFormLayout.FieldRole, self.zoomCameraSensitivity2dEdit)


        self.verticalLayout_3.addLayout(self.formLayout_6)

        self.line889 = QFrame(self.tab2DControls)
        self.line889.setObjectName(u"line889")
        self.line889.setFrameShape(QFrame.HLine)
        self.line889.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line889)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setVerticalSpacing(10)
        self.label_13 = QLabel(self.tab2DControls)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setMinimumSize(QSize(110, 0))
        self.label_13.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_13.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_13)

        self.moveCamera2dBindEdit = SetBindWidget(self.tab2DControls)
        self.moveCamera2dBindEdit.setObjectName(u"moveCamera2dBindEdit")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.moveCamera2dBindEdit)

        self.label_14 = QLabel(self.tab2DControls)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setMinimumSize(QSize(110, 0))
        self.label_14.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_14.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.zoomCamera2dBindEdit = SetBindWidget(self.tab2DControls)
        self.zoomCamera2dBindEdit.setObjectName(u"zoomCamera2dBindEdit")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.zoomCamera2dBindEdit)

        self.label_15 = QLabel(self.tab2DControls)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setMinimumSize(QSize(110, 0))
        self.label_15.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_15.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_15)

        self.rotateCamera2dBindEdit = SetBindWidget(self.tab2DControls)
        self.rotateCamera2dBindEdit.setObjectName(u"rotateCamera2dBindEdit")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.rotateCamera2dBindEdit)

        self.label_16 = QLabel(self.tab2DControls)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setMinimumSize(QSize(110, 0))
        self.label_16.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_16.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_16)

        self.selectObject2dBindEdit = SetBindWidget(self.tab2DControls)
        self.selectObject2dBindEdit.setObjectName(u"selectObject2dBindEdit")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.selectObject2dBindEdit)

        self.label_17 = QLabel(self.tab2DControls)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setMinimumSize(QSize(110, 0))
        self.label_17.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_17.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.label_17)

        self.moveObject2dBindEdit = SetBindWidget(self.tab2DControls)
        self.moveObject2dBindEdit.setObjectName(u"moveObject2dBindEdit")

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.moveObject2dBindEdit)

        self.label_19 = QLabel(self.tab2DControls)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setMinimumSize(QSize(110, 0))
        self.label_19.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_19.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.label_19)

        self.rotateObject2dBindEdit = SetBindWidget(self.tab2DControls)
        self.rotateObject2dBindEdit.setObjectName(u"rotateObject2dBindEdit")

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.rotateObject2dBindEdit)

        self.label_59 = QLabel(self.tab2DControls)
        self.label_59.setObjectName(u"label_59")
        self.label_59.setMinimumSize(QSize(110, 0))
        self.label_59.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_59.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(6, QFormLayout.LabelRole, self.label_59)

        self.duplicateObject2dBindEdit = SetBindWidget(self.tab2DControls)
        self.duplicateObject2dBindEdit.setObjectName(u"duplicateObject2dBindEdit")

        self.formLayout_2.setWidget(6, QFormLayout.FieldRole, self.duplicateObject2dBindEdit)

        self.line_4 = QFrame(self.tab2DControls)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.formLayout_2.setWidget(7, QFormLayout.FieldRole, self.line_4)

        self.label_61 = QLabel(self.tab2DControls)
        self.label_61.setObjectName(u"label_61")
        self.label_61.setMinimumSize(QSize(110, 0))
        self.label_61.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_61.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(9, QFormLayout.LabelRole, self.label_61)

        self.deleteObject2dBindEdit = SetBindWidget(self.tab2DControls)
        self.deleteObject2dBindEdit.setObjectName(u"deleteObject2dBindEdit")

        self.formLayout_2.setWidget(9, QFormLayout.FieldRole, self.deleteObject2dBindEdit)

        self.label_62 = QLabel(self.tab2DControls)
        self.label_62.setObjectName(u"label_62")
        self.label_62.setMinimumSize(QSize(110, 0))
        self.label_62.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_62.setAlignment(Qt.AlignCenter)

        self.formLayout_2.setWidget(8, QFormLayout.LabelRole, self.label_62)

        self.moveCameraToSelected2dBindEdit = SetBindWidget(self.tab2DControls)
        self.moveCameraToSelected2dBindEdit.setObjectName(u"moveCameraToSelected2dBindEdit")

        self.formLayout_2.setWidget(8, QFormLayout.FieldRole, self.moveCameraToSelected2dBindEdit)


        self.verticalLayout_3.addLayout(self.formLayout_2)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.tab2DControls, "")
        self.tabFCControls = QWidget()
        self.tabFCControls.setObjectName(u"tabFCControls")
        self.verticalLayout_4 = QVBoxLayout(self.tabFCControls)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.controlsFcResetButton = QPushButton(self.tabFCControls)
        self.controlsFcResetButton.setObjectName(u"controlsFcResetButton")

        self.horizontalLayout_5.addWidget(self.controlsFcResetButton)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_5)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.line_5 = QFrame(self.tabFCControls)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.HLine)
        self.line_5.setFrameShadow(QFrame.Sunken)
        self.line_5.setProperty("verticalSpacing", 10)

        self.verticalLayout_4.addWidget(self.line_5)

        self.formLayout_7 = QFormLayout()
        self.formLayout_7.setObjectName(u"formLayout_7")
        self.label_18 = QLabel(self.tabFCControls)
        self.label_18.setObjectName(u"label_18")

        self.formLayout_7.setWidget(0, QFormLayout.LabelRole, self.label_18)

        self.flySpeedFcEdit = QSlider(self.tabFCControls)
        self.flySpeedFcEdit.setObjectName(u"flySpeedFcEdit")
        self.flySpeedFcEdit.setMinimum(10)
        self.flySpeedFcEdit.setMaximum(1000)
        self.flySpeedFcEdit.setOrientation(Qt.Horizontal)

        self.formLayout_7.setWidget(0, QFormLayout.FieldRole, self.flySpeedFcEdit)

        self.label_601 = QLabel(self.tabFCControls)
        self.label_601.setObjectName(u"label_601")

        self.formLayout_7.setWidget(1, QFormLayout.LabelRole, self.label_601)

        self.rotateCameraSensitivityFcEdit = QSlider(self.tabFCControls)
        self.rotateCameraSensitivityFcEdit.setObjectName(u"rotateCameraSensitivityFcEdit")
        self.rotateCameraSensitivityFcEdit.setMinimum(10)
        self.rotateCameraSensitivityFcEdit.setMaximum(1000)
        self.rotateCameraSensitivityFcEdit.setOrientation(Qt.Horizontal)

        self.formLayout_7.setWidget(1, QFormLayout.FieldRole, self.rotateCameraSensitivityFcEdit)

        self.label_60 = QLabel(self.tabFCControls)
        self.label_60.setObjectName(u"label_60")

        self.formLayout_7.setWidget(2, QFormLayout.LabelRole, self.label_60)

        self.boostedFlyCameraSpeedFCEdit = QSlider(self.tabFCControls)
        self.boostedFlyCameraSpeedFCEdit.setObjectName(u"boostedFlyCameraSpeedFCEdit")
        self.boostedFlyCameraSpeedFCEdit.setMinimum(10)
        self.boostedFlyCameraSpeedFCEdit.setMaximum(1000)
        self.boostedFlyCameraSpeedFCEdit.setOrientation(Qt.Horizontal)

        self.formLayout_7.setWidget(2, QFormLayout.FieldRole, self.boostedFlyCameraSpeedFCEdit)


        self.verticalLayout_4.addLayout(self.formLayout_7)

        self.line_6 = QFrame(self.tabFCControls)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.HLine)
        self.line_6.setFrameShadow(QFrame.Sunken)
        self.line_6.setProperty("verticalSpacing", 10)

        self.verticalLayout_4.addWidget(self.line_6)

        self.formLayout_8 = QFormLayout()
        self.formLayout_8.setObjectName(u"formLayout_8")
        self.formLayout_8.setVerticalSpacing(10)
        self.label_63 = QLabel(self.tabFCControls)
        self.label_63.setObjectName(u"label_63")
        self.label_63.setMinimumSize(QSize(110, 0))
        self.label_63.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_63.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(0, QFormLayout.LabelRole, self.label_63)

        self.moveCameraForwardFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraForwardFcBindEdit.setObjectName(u"moveCameraForwardFcBindEdit")

        self.formLayout_8.setWidget(0, QFormLayout.FieldRole, self.moveCameraForwardFcBindEdit)

        self.label_64 = QLabel(self.tabFCControls)
        self.label_64.setObjectName(u"label_64")
        self.label_64.setMinimumSize(QSize(110, 0))
        self.label_64.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_64.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(1, QFormLayout.LabelRole, self.label_64)

        self.moveCameraBackwardFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraBackwardFcBindEdit.setObjectName(u"moveCameraBackwardFcBindEdit")

        self.formLayout_8.setWidget(1, QFormLayout.FieldRole, self.moveCameraBackwardFcBindEdit)

        self.label_65 = QLabel(self.tabFCControls)
        self.label_65.setObjectName(u"label_65")
        self.label_65.setMinimumSize(QSize(110, 0))
        self.label_65.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_65.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(2, QFormLayout.LabelRole, self.label_65)

        self.moveCameraLeftFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraLeftFcBindEdit.setObjectName(u"moveCameraLeftFcBindEdit")

        self.formLayout_8.setWidget(2, QFormLayout.FieldRole, self.moveCameraLeftFcBindEdit)

        self.label_66 = QLabel(self.tabFCControls)
        self.label_66.setObjectName(u"label_66")
        self.label_66.setMinimumSize(QSize(110, 0))
        self.label_66.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_66.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(3, QFormLayout.LabelRole, self.label_66)

        self.moveCameraRightFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraRightFcBindEdit.setObjectName(u"moveCameraRightFcBindEdit")

        self.formLayout_8.setWidget(3, QFormLayout.FieldRole, self.moveCameraRightFcBindEdit)

        self.label_67 = QLabel(self.tabFCControls)
        self.label_67.setObjectName(u"label_67")
        self.label_67.setMinimumSize(QSize(110, 0))
        self.label_67.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_67.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(4, QFormLayout.LabelRole, self.label_67)

        self.moveCameraUpFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraUpFcBindEdit.setObjectName(u"moveCameraUpFcBindEdit")

        self.formLayout_8.setWidget(4, QFormLayout.FieldRole, self.moveCameraUpFcBindEdit)

        self.label_68 = QLabel(self.tabFCControls)
        self.label_68.setObjectName(u"label_68")
        self.label_68.setMinimumSize(QSize(110, 0))
        self.label_68.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_68.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(5, QFormLayout.LabelRole, self.label_68)

        self.moveCameraDownFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraDownFcBindEdit.setObjectName(u"moveCameraDownFcBindEdit")

        self.formLayout_8.setWidget(5, QFormLayout.FieldRole, self.moveCameraDownFcBindEdit)

        self.label_691 = QLabel(self.tabFCControls)
        self.label_691.setObjectName(u"label_691")
        self.label_691.setMinimumSize(QSize(110, 0))
        self.label_691.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_691.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(6, QFormLayout.LabelRole, self.label_691)

        self.speedBoostCameraFcBindEdit = SetBindWidget(self.tabFCControls)
        self.speedBoostCameraFcBindEdit.setObjectName(u"speedBoostCameraFcBindEdit")

        self.formLayout_8.setWidget(6, QFormLayout.FieldRole, self.speedBoostCameraFcBindEdit)

        self.label_701 = QLabel(self.tabFCControls)
        self.label_701.setObjectName(u"label_701")
        self.label_701.setMinimumSize(QSize(110, 0))
        self.label_701.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_701.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(7, QFormLayout.LabelRole, self.label_701)

        self.rotateCameraLeftFcBindEdit = SetBindWidget(self.tabFCControls)
        self.rotateCameraLeftFcBindEdit.setObjectName(u"rotateCameraLeftFcBindEdit")

        self.formLayout_8.setWidget(7, QFormLayout.FieldRole, self.rotateCameraLeftFcBindEdit)

        self.label_711 = QLabel(self.tabFCControls)
        self.label_711.setObjectName(u"label_711")
        self.label_711.setMinimumSize(QSize(110, 0))
        self.label_711.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_711.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(8, QFormLayout.LabelRole, self.label_711)

        self.rotateCameraRightFcBindEdit = SetBindWidget(self.tabFCControls)
        self.rotateCameraRightFcBindEdit.setObjectName(u"rotateCameraRightFcBindEdit")

        self.formLayout_8.setWidget(8, QFormLayout.FieldRole, self.rotateCameraRightFcBindEdit)

        self.label_72 = QLabel(self.tabFCControls)
        self.label_72.setObjectName(u"label_72")
        self.label_72.setMinimumSize(QSize(110, 0))
        self.label_72.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_72.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(9, QFormLayout.LabelRole, self.label_72)

        self.rotateCameraUpFcBindEdit = SetBindWidget(self.tabFCControls)
        self.rotateCameraUpFcBindEdit.setObjectName(u"rotateCameraUpFcBindEdit")

        self.formLayout_8.setWidget(9, QFormLayout.FieldRole, self.rotateCameraUpFcBindEdit)

        self.label_73 = QLabel(self.tabFCControls)
        self.label_73.setObjectName(u"label_73")
        self.label_73.setMinimumSize(QSize(110, 0))
        self.label_73.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_73.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(10, QFormLayout.LabelRole, self.label_73)

        self.rotateCameraDownFcBindEdit = SetBindWidget(self.tabFCControls)
        self.rotateCameraDownFcBindEdit.setObjectName(u"rotateCameraDownFcBindEdit")

        self.formLayout_8.setWidget(10, QFormLayout.FieldRole, self.rotateCameraDownFcBindEdit)

        self.label_74 = QLabel(self.tabFCControls)
        self.label_74.setObjectName(u"label_74")
        self.label_74.setMinimumSize(QSize(110, 0))
        self.label_74.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_74.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(11, QFormLayout.LabelRole, self.label_74)

        self.zoomCameraInFcBindEdit = SetBindWidget(self.tabFCControls)
        self.zoomCameraInFcBindEdit.setObjectName(u"zoomCameraInFcBindEdit")

        self.formLayout_8.setWidget(11, QFormLayout.FieldRole, self.zoomCameraInFcBindEdit)

        self.label_75 = QLabel(self.tabFCControls)
        self.label_75.setObjectName(u"label_75")
        self.label_75.setMinimumSize(QSize(110, 0))
        self.label_75.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_75.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(12, QFormLayout.LabelRole, self.label_75)

        self.zoomCameraOutFcBindEdit = SetBindWidget(self.tabFCControls)
        self.zoomCameraOutFcBindEdit.setObjectName(u"zoomCameraOutFcBindEdit")

        self.formLayout_8.setWidget(12, QFormLayout.FieldRole, self.zoomCameraOutFcBindEdit)

        self.label_76 = QLabel(self.tabFCControls)
        self.label_76.setObjectName(u"label_76")
        self.label_76.setMinimumSize(QSize(110, 0))
        self.label_76.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_76.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(13, QFormLayout.LabelRole, self.label_76)

        self.moveCameraToEntryPointFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraToEntryPointFcBindEdit.setObjectName(u"moveCameraToEntryPointFcBindEdit")

        self.formLayout_8.setWidget(13, QFormLayout.FieldRole, self.moveCameraToEntryPointFcBindEdit)

        self.label_77 = QLabel(self.tabFCControls)
        self.label_77.setObjectName(u"label_77")
        self.label_77.setMinimumSize(QSize(110, 0))
        self.label_77.setStyleSheet(u"QLabel:hover { color: #555;}")
        self.label_77.setAlignment(Qt.AlignCenter)

        self.formLayout_8.setWidget(14, QFormLayout.LabelRole, self.label_77)

        self.moveCameraToCursorFcBindEdit = SetBindWidget(self.tabFCControls)
        self.moveCameraToCursorFcBindEdit.setObjectName(u"moveCameraToCursorFcBindEdit")

        self.formLayout_8.setWidget(14, QFormLayout.FieldRole, self.moveCameraToCursorFcBindEdit)


        self.verticalLayout_4.addLayout(self.formLayout_8)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.tabWidget.addTab(self.tabFCControls, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_2 = QGridLayout(self.groupBox_3)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setVerticalSpacing(10)
        self.label_21 = QLabel(self.groupBox_3)
        self.label_21.setObjectName(u"label_21")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_21)

        self.undefinedMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.undefinedMaterialColourEdit.setObjectName(u"undefinedMaterialColourEdit")
        self.undefinedMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.undefinedMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.undefinedMaterialColourEdit)

        self.label_22 = QLabel(self.groupBox_3)
        self.label_22.setObjectName(u"label_22")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_22)

        self.label_23 = QLabel(self.groupBox_3)
        self.label_23.setObjectName(u"label_23")

        self.formLayout_4.setWidget(14, QFormLayout.LabelRole, self.label_23)

        self.label_24 = QLabel(self.groupBox_3)
        self.label_24.setObjectName(u"label_24")

        self.formLayout_4.setWidget(13, QFormLayout.LabelRole, self.label_24)

        self.label_25 = QLabel(self.groupBox_3)
        self.label_25.setObjectName(u"label_25")

        self.formLayout_4.setWidget(12, QFormLayout.LabelRole, self.label_25)

        self.label_26 = QLabel(self.groupBox_3)
        self.label_26.setObjectName(u"label_26")

        self.formLayout_4.setWidget(11, QFormLayout.LabelRole, self.label_26)

        self.label_27 = QLabel(self.groupBox_3)
        self.label_27.setObjectName(u"label_27")

        self.formLayout_4.setWidget(10, QFormLayout.LabelRole, self.label_27)

        self.label_28 = QLabel(self.groupBox_3)
        self.label_28.setObjectName(u"label_28")

        self.formLayout_4.setWidget(9, QFormLayout.LabelRole, self.label_28)

        self.label_29 = QLabel(self.groupBox_3)
        self.label_29.setObjectName(u"label_29")

        self.formLayout_4.setWidget(8, QFormLayout.LabelRole, self.label_29)

        self.label_30 = QLabel(self.groupBox_3)
        self.label_30.setObjectName(u"label_30")

        self.formLayout_4.setWidget(7, QFormLayout.LabelRole, self.label_30)

        self.label_31 = QLabel(self.groupBox_3)
        self.label_31.setObjectName(u"label_31")

        self.formLayout_4.setWidget(6, QFormLayout.LabelRole, self.label_31)

        self.label_32 = QLabel(self.groupBox_3)
        self.label_32.setObjectName(u"label_32")

        self.formLayout_4.setWidget(5, QFormLayout.LabelRole, self.label_32)

        self.label_33 = QLabel(self.groupBox_3)
        self.label_33.setObjectName(u"label_33")

        self.formLayout_4.setWidget(4, QFormLayout.LabelRole, self.label_33)

        self.label_34 = QLabel(self.groupBox_3)
        self.label_34.setObjectName(u"label_34")

        self.formLayout_4.setWidget(3, QFormLayout.LabelRole, self.label_34)

        self.label_35 = QLabel(self.groupBox_3)
        self.label_35.setObjectName(u"label_35")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_35)

        self.label_36 = QLabel(self.groupBox_3)
        self.label_36.setObjectName(u"label_36")

        self.formLayout_4.setWidget(15, QFormLayout.LabelRole, self.label_36)

        self.label_37 = QLabel(self.groupBox_3)
        self.label_37.setObjectName(u"label_37")

        self.formLayout_4.setWidget(16, QFormLayout.LabelRole, self.label_37)

        self.label_38 = QLabel(self.groupBox_3)
        self.label_38.setObjectName(u"label_38")

        self.formLayout_4.setWidget(17, QFormLayout.LabelRole, self.label_38)

        self.label_39 = QLabel(self.groupBox_3)
        self.label_39.setObjectName(u"label_39")

        self.formLayout_4.setWidget(18, QFormLayout.LabelRole, self.label_39)

        self.label_40 = QLabel(self.groupBox_3)
        self.label_40.setObjectName(u"label_40")

        self.formLayout_4.setWidget(19, QFormLayout.LabelRole, self.label_40)

        self.dirtMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.dirtMaterialColourEdit.setObjectName(u"dirtMaterialColourEdit")
        self.dirtMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.dirtMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.dirtMaterialColourEdit)

        self.obscuringMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.obscuringMaterialColourEdit.setObjectName(u"obscuringMaterialColourEdit")
        self.obscuringMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.obscuringMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.obscuringMaterialColourEdit)

        self.grassMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.grassMaterialColourEdit.setObjectName(u"grassMaterialColourEdit")
        self.grassMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.grassMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.grassMaterialColourEdit)

        self.stoneMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.stoneMaterialColourEdit.setObjectName(u"stoneMaterialColourEdit")
        self.stoneMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.stoneMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(4, QFormLayout.FieldRole, self.stoneMaterialColourEdit)

        self.woodMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.woodMaterialColourEdit.setObjectName(u"woodMaterialColourEdit")
        self.woodMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.woodMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(5, QFormLayout.FieldRole, self.woodMaterialColourEdit)

        self.waterMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.waterMaterialColourEdit.setObjectName(u"waterMaterialColourEdit")
        self.waterMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.waterMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(6, QFormLayout.FieldRole, self.waterMaterialColourEdit)

        self.nonWalkMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.nonWalkMaterialColourEdit.setObjectName(u"nonWalkMaterialColourEdit")
        self.nonWalkMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.nonWalkMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(7, QFormLayout.FieldRole, self.nonWalkMaterialColourEdit)

        self.transparentMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.transparentMaterialColourEdit.setObjectName(u"transparentMaterialColourEdit")
        self.transparentMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.transparentMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(8, QFormLayout.FieldRole, self.transparentMaterialColourEdit)

        self.carpetMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.carpetMaterialColourEdit.setObjectName(u"carpetMaterialColourEdit")
        self.carpetMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.carpetMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(9, QFormLayout.FieldRole, self.carpetMaterialColourEdit)

        self.metalMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.metalMaterialColourEdit.setObjectName(u"metalMaterialColourEdit")
        self.metalMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.metalMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(10, QFormLayout.FieldRole, self.metalMaterialColourEdit)

        self.puddlesMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.puddlesMaterialColourEdit.setObjectName(u"puddlesMaterialColourEdit")
        self.puddlesMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.puddlesMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(11, QFormLayout.FieldRole, self.puddlesMaterialColourEdit)

        self.swampMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.swampMaterialColourEdit.setObjectName(u"swampMaterialColourEdit")
        self.swampMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.swampMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(12, QFormLayout.FieldRole, self.swampMaterialColourEdit)

        self.mudMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.mudMaterialColourEdit.setObjectName(u"mudMaterialColourEdit")
        self.mudMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.mudMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(13, QFormLayout.FieldRole, self.mudMaterialColourEdit)

        self.leavesMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.leavesMaterialColourEdit.setObjectName(u"leavesMaterialColourEdit")
        self.leavesMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.leavesMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(14, QFormLayout.FieldRole, self.leavesMaterialColourEdit)

        self.lavaMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.lavaMaterialColourEdit.setObjectName(u"lavaMaterialColourEdit")
        self.lavaMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.lavaMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(15, QFormLayout.FieldRole, self.lavaMaterialColourEdit)

        self.bottomlessPitMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.bottomlessPitMaterialColourEdit.setObjectName(u"bottomlessPitMaterialColourEdit")
        self.bottomlessPitMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.bottomlessPitMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(16, QFormLayout.FieldRole, self.bottomlessPitMaterialColourEdit)

        self.deepWaterMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.deepWaterMaterialColourEdit.setObjectName(u"deepWaterMaterialColourEdit")
        self.deepWaterMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.deepWaterMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(17, QFormLayout.FieldRole, self.deepWaterMaterialColourEdit)

        self.doorMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.doorMaterialColourEdit.setObjectName(u"doorMaterialColourEdit")
        self.doorMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.doorMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(18, QFormLayout.FieldRole, self.doorMaterialColourEdit)

        self.nonWalkGrassMaterialColourEdit = ColorEdit(self.groupBox_3)
        self.nonWalkGrassMaterialColourEdit.setObjectName(u"nonWalkGrassMaterialColourEdit")
        self.nonWalkGrassMaterialColourEdit.setMinimumSize(QSize(0, 20))
        self.nonWalkGrassMaterialColourEdit.setMaximumSize(QSize(16777215, 20))

        self.formLayout_4.setWidget(19, QFormLayout.FieldRole, self.nonWalkGrassMaterialColourEdit)


        self.gridLayout_2.addLayout(self.formLayout_4, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.coloursResetButton = QPushButton(self.groupBox_3)
        self.coloursResetButton.setObjectName(u"coloursResetButton")

        self.horizontalLayout.addWidget(self.coloursResetButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_3)

        self.verticalSpacer = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)


        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_20.setText(QCoreApplication.translate("Form", u"Field of View:", None))
        self.controls3dResetButton.setText(QCoreApplication.translate("Form", u"Reset", None))
        self.label602.setText(QCoreApplication.translate("Form", u"Move Sensitivity", None))
        self.label_41.setText(QCoreApplication.translate("Form", u"Rotate Sensitivity", None))
        self.label_42.setText(QCoreApplication.translate("Form", u"Zoom Sensitivity", None))
        self.label.setText(QCoreApplication.translate("Form", u"Boosted Speed", None))
#if QT_CONFIG(tooltip)
        self.label_2.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("Form", u"Move Camera\n"
"(XY)", None))
#if QT_CONFIG(tooltip)
        self.label_12.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_12.setText(QCoreApplication.translate("Form", u"Move Camera\n"
"(Z)", None))
#if QT_CONFIG(tooltip)
        self.label_3.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("Form", u"Rotate Camera", None))
#if QT_CONFIG(tooltip)
        self.label_4.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse scrolling.", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("Form", u"Zoom Camera\n"
"(Mouse Scroll)", None))
#if QT_CONFIG(tooltip)
        self.label_9.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("Form", u"Zoom Camera\n"
"(Mouse Movement)", None))
#if QT_CONFIG(tooltip)
        self.label_10.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse scrolling.", None))
#endif // QT_CONFIG(tooltip)
        self.label_10.setText(QCoreApplication.translate("Form", u"Move Object XY", None))
#if QT_CONFIG(tooltip)
        self.label_11.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse scrolling.", None))
#endif // QT_CONFIG(tooltip)
        self.label_11.setText(QCoreApplication.translate("Form", u"Move Object Z", None))
#if QT_CONFIG(tooltip)
        self.label_5.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse buttons.", None))
#endif // QT_CONFIG(tooltip)
        self.label_5.setText(QCoreApplication.translate("Form", u"Select Object", None))
#if QT_CONFIG(tooltip)
        self.label_6.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("Form", u"Rotate Object", None))
#if QT_CONFIG(tooltip)
        self.label_7.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_7.setText(QCoreApplication.translate("Form", u"Delete Object", None))
#if QT_CONFIG(tooltip)
        self.label_46.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_46.setText(QCoreApplication.translate("Form", u"Rotate Camera Left", None))
#if QT_CONFIG(tooltip)
        self.label_47.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_47.setText(QCoreApplication.translate("Form", u"Rotate Camera Right", None))
#if QT_CONFIG(tooltip)
        self.label_48.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_48.setText(QCoreApplication.translate("Form", u"Rotate Camera Up", None))
#if QT_CONFIG(tooltip)
        self.label_49.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_49.setText(QCoreApplication.translate("Form", u"Rotate Camera Down", None))
#if QT_CONFIG(tooltip)
        self.label_50.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_50.setText(QCoreApplication.translate("Form", u"Move Camera Forward", None))
#if QT_CONFIG(tooltip)
        self.label_51.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_51.setText(QCoreApplication.translate("Form", u"Move Camera Backward", None))
#if QT_CONFIG(tooltip)
        self.label_53.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_53.setText(QCoreApplication.translate("Form", u"Move Camera Left", None))
#if QT_CONFIG(tooltip)
        self.label_52.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_52.setText(QCoreApplication.translate("Form", u"Move Camera Right", None))
#if QT_CONFIG(tooltip)
        self.label_54.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_54.setText(QCoreApplication.translate("Form", u"Move Camera Up", None))
#if QT_CONFIG(tooltip)
        self.label_55.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_55.setText(QCoreApplication.translate("Form", u"Move Camera Down", None))
#if QT_CONFIG(tooltip)
        self.label_56.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_56.setText(QCoreApplication.translate("Form", u"Zoom Camera In", None))
#if QT_CONFIG(tooltip)
        self.label_57.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_57.setText(QCoreApplication.translate("Form", u"Zoom Camera Out", None))
#if QT_CONFIG(tooltip)
        self.label_8.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_8.setText(QCoreApplication.translate("Form", u"Move Camera\n"
"to Selection", None))
#if QT_CONFIG(tooltip)
        self.label_58.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_58.setText(QCoreApplication.translate("Form", u"Duplicate Object", None))
#if QT_CONFIG(tooltip)
        self.label_69.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_69.setText(QCoreApplication.translate("Form", u"Move Camera\n"
"to Cursor", None))
#if QT_CONFIG(tooltip)
        self.label_70.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_70.setText(QCoreApplication.translate("Form", u"Move Camera\n"
"to Entry Point", None))
#if QT_CONFIG(tooltip)
        self.label_71.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_71.setText(QCoreApplication.translate("Form", u"Move Camera\n"
"(Camera Plane)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab3DControls), QCoreApplication.translate("Form", u"3D Controls", None))
        self.controls2dResetButton.setText(QCoreApplication.translate("Form", u"Reset", None))
        self.label_43.setText(QCoreApplication.translate("Form", u"Move Sensitivity", None))
        self.label_44.setText(QCoreApplication.translate("Form", u"Rotate Sensitivity", None))
        self.label_45.setText(QCoreApplication.translate("Form", u"Zoom Sensitivity", None))
#if QT_CONFIG(tooltip)
        self.label_13.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_13.setText(QCoreApplication.translate("Form", u"Move Camera", None))
#if QT_CONFIG(tooltip)
        self.label_14.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse scrolling.", None))
#endif // QT_CONFIG(tooltip)
        self.label_14.setText(QCoreApplication.translate("Form", u"Zoom Camera", None))
#if QT_CONFIG(tooltip)
        self.label_15.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_15.setText(QCoreApplication.translate("Form", u"Rotate Camera", None))
#if QT_CONFIG(tooltip)
        self.label_16.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse presses.", None))
#endif // QT_CONFIG(tooltip)
        self.label_16.setText(QCoreApplication.translate("Form", u"Select Object", None))
#if QT_CONFIG(tooltip)
        self.label_17.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_17.setText(QCoreApplication.translate("Form", u"Move Object", None))
#if QT_CONFIG(tooltip)
        self.label_19.setToolTip(QCoreApplication.translate("Form", u"Reacts to mouse movement.", None))
#endif // QT_CONFIG(tooltip)
        self.label_19.setText(QCoreApplication.translate("Form", u"Rotate Object", None))
#if QT_CONFIG(tooltip)
        self.label_59.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_59.setText(QCoreApplication.translate("Form", u"Duplicate Object", None))
#if QT_CONFIG(tooltip)
        self.label_61.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_61.setText(QCoreApplication.translate("Form", u"Delete Object", None))
#if QT_CONFIG(tooltip)
        self.label_62.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_62.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>Move Camera<br/>to Selection</p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab2DControls), QCoreApplication.translate("Form", u"2D Controls", None))
        self.controlsFcResetButton.setText(QCoreApplication.translate("Form", u"Reset", None))
        self.label_18.setText(QCoreApplication.translate("Form", u"Fly Speed", None))
        self.label_601.setText(QCoreApplication.translate("Form", u"Rotate Sensitivity", None))
        self.label_60.setText(QCoreApplication.translate("Form", u"Boosted Fly Speed", None))
#if QT_CONFIG(tooltip)
        self.label_63.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_63.setText(QCoreApplication.translate("Form", u"Move Forwards", None))
#if QT_CONFIG(tooltip)
        self.label_64.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_64.setText(QCoreApplication.translate("Form", u"Move Backwards", None))
#if QT_CONFIG(tooltip)
        self.label_65.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_65.setText(QCoreApplication.translate("Form", u"Move Left", None))
#if QT_CONFIG(tooltip)
        self.label_66.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_66.setText(QCoreApplication.translate("Form", u"Move Right", None))
#if QT_CONFIG(tooltip)
        self.label_67.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_67.setText(QCoreApplication.translate("Form", u"Move Up", None))
#if QT_CONFIG(tooltip)
        self.label_68.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_68.setText(QCoreApplication.translate("Form", u"Move Down", None))
#if QT_CONFIG(tooltip)
        self.label_691.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_691.setText(QCoreApplication.translate("Form", u"Speed Boost", None))
#if QT_CONFIG(tooltip)
        self.label_701.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_701.setText(QCoreApplication.translate("Form", u"Rotate Left", None))
#if QT_CONFIG(tooltip)
        self.label_711.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_711.setText(QCoreApplication.translate("Form", u"Rotate Right", None))
#if QT_CONFIG(tooltip)
        self.label_72.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_72.setText(QCoreApplication.translate("Form", u"Rotate Up", None))
#if QT_CONFIG(tooltip)
        self.label_73.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_73.setText(QCoreApplication.translate("Form", u"Rotate Down", None))
#if QT_CONFIG(tooltip)
        self.label_74.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_74.setText(QCoreApplication.translate("Form", u"Zoom In", None))
#if QT_CONFIG(tooltip)
        self.label_75.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_75.setText(QCoreApplication.translate("Form", u"Zoom Out", None))
#if QT_CONFIG(tooltip)
        self.label_76.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_76.setText(QCoreApplication.translate("Form", u"Move to Entry Point", None))
#if QT_CONFIG(tooltip)
        self.label_77.setToolTip(QCoreApplication.translate("Form", u"Reacts to keyboard input.", None))
#endif // QT_CONFIG(tooltip)
        self.label_77.setText(QCoreApplication.translate("Form", u"Move to Cursor", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabFCControls), QCoreApplication.translate("Form", u"FreeCam Controls", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Form", u"Walkmesh Colours", None))
        self.label_21.setText(QCoreApplication.translate("Form", u"Undefined:", None))
        self.label_22.setText(QCoreApplication.translate("Form", u"Dirt:", None))
        self.label_23.setText(QCoreApplication.translate("Form", u"Leaves:", None))
        self.label_24.setText(QCoreApplication.translate("Form", u"Mud:", None))
        self.label_25.setText(QCoreApplication.translate("Form", u"Swamp:", None))
        self.label_26.setText(QCoreApplication.translate("Form", u"Puddles:", None))
        self.label_27.setText(QCoreApplication.translate("Form", u"Metal:", None))
        self.label_28.setText(QCoreApplication.translate("Form", u"Carpet:", None))
        self.label_29.setText(QCoreApplication.translate("Form", u"Transparent:", None))
        self.label_30.setText(QCoreApplication.translate("Form", u"Non-Walk:", None))
        self.label_31.setText(QCoreApplication.translate("Form", u"Water:", None))
        self.label_32.setText(QCoreApplication.translate("Form", u"Wood:", None))
        self.label_33.setText(QCoreApplication.translate("Form", u"Stone:", None))
        self.label_34.setText(QCoreApplication.translate("Form", u"Grass:", None))
        self.label_35.setText(QCoreApplication.translate("Form", u"Obscuring:", None))
        self.label_36.setText(QCoreApplication.translate("Form", u"Lava:", None))
        self.label_37.setText(QCoreApplication.translate("Form", u"Bottomless Pit:", None))
        self.label_38.setText(QCoreApplication.translate("Form", u"Deep Water:", None))
        self.label_39.setText(QCoreApplication.translate("Form", u"Door:", None))
        self.label_40.setText(QCoreApplication.translate("Form", u"Non-Walk Grass:", None))
        self.coloursResetButton.setText(QCoreApplication.translate("Form", u"Reset", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
