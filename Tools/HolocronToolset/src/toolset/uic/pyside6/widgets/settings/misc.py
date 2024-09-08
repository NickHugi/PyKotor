# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'misc.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(420, 334)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(Form)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 400, 314))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.saveRimCheck = QCheckBox(self.scrollAreaWidgetContents)
        self.saveRimCheck.setObjectName(u"saveRimCheck")

        self.verticalLayout.addWidget(self.saveRimCheck)

        self.useBetaChannel = QCheckBox(self.scrollAreaWidgetContents)
        self.useBetaChannel.setObjectName(u"useBetaChannel")

        self.verticalLayout.addWidget(self.useBetaChannel)

        self.hBoxLayoutForSubOption = QHBoxLayout()
        self.hBoxLayoutForSubOption.setObjectName(u"hBoxLayoutForSubOption")
        self.hBoxLayoutForSubOption.setContentsMargins(20, -1, -1, -1)
        self.alsoCheckReleaseVersion = QCheckBox(self.scrollAreaWidgetContents)
        self.alsoCheckReleaseVersion.setObjectName(u"alsoCheckReleaseVersion")
        self.alsoCheckReleaseVersion.setEnabled(True)

        self.hBoxLayoutForSubOption.addWidget(self.alsoCheckReleaseVersion)


        self.verticalLayout.addLayout(self.hBoxLayoutForSubOption)

        self.mergeRimCheck = QCheckBox(self.scrollAreaWidgetContents)
        self.mergeRimCheck.setObjectName(u"mergeRimCheck")

        self.verticalLayout.addWidget(self.mergeRimCheck)

        self.attemptKeepOldGFFFields = QCheckBox(self.scrollAreaWidgetContents)
        self.attemptKeepOldGFFFields.setObjectName(u"attemptKeepOldGFFFields")

        self.verticalLayout.addWidget(self.attemptKeepOldGFFFields)

        self.moduleSortOptionComboBox = QComboBox(self.scrollAreaWidgetContents)
        self.moduleSortOptionComboBox.addItem("")
        self.moduleSortOptionComboBox.addItem("")
        self.moduleSortOptionComboBox.addItem("")
        self.moduleSortOptionComboBox.setObjectName(u"moduleSortOptionComboBox")
        self.moduleSortOptionComboBox.setEditable(False)

        self.verticalLayout.addWidget(self.moduleSortOptionComboBox)

        self.greyRimCheck = QCheckBox(self.scrollAreaWidgetContents)
        self.greyRimCheck.setObjectName(u"greyRimCheck")

        self.verticalLayout.addWidget(self.greyRimCheck)

        self.showPreviewUTCCheck = QCheckBox(self.scrollAreaWidgetContents)
        self.showPreviewUTCCheck.setObjectName(u"showPreviewUTCCheck")

        self.verticalLayout.addWidget(self.showPreviewUTCCheck)

        self.showPreviewUTPCheck = QCheckBox(self.scrollAreaWidgetContents)
        self.showPreviewUTPCheck.setObjectName(u"showPreviewUTPCheck")

        self.verticalLayout.addWidget(self.showPreviewUTPCheck)

        self.showPreviewUTDCheck = QCheckBox(self.scrollAreaWidgetContents)
        self.showPreviewUTDCheck.setObjectName(u"showPreviewUTDCheck")

        self.verticalLayout.addWidget(self.showPreviewUTDCheck)

        self.profileToolset = QCheckBox(self.scrollAreaWidgetContents)
        self.profileToolset.setObjectName(u"profileToolset")

        self.verticalLayout.addWidget(self.profileToolset)

        self.line = QFrame(self.scrollAreaWidgetContents)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.tempDirEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.tempDirEdit.setObjectName(u"tempDirEdit")

        self.horizontalLayout.addWidget(self.tempDirEdit)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.line_2 = QFrame(self.scrollAreaWidgetContents)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_5 = QLabel(self.scrollAreaWidgetContents)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_5)

        self.gffEditorCombo = QComboBox(self.scrollAreaWidgetContents)
        self.gffEditorCombo.addItem("")
        self.gffEditorCombo.addItem("")
        self.gffEditorCombo.setObjectName(u"gffEditorCombo")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.gffEditorCombo)

        self.label_4 = QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.nssCompEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.nssCompEdit.setObjectName(u"nssCompEdit")
        self.nssCompEdit.setEnabled(True)

        self.horizontalLayout_4.addWidget(self.nssCompEdit)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_4)

        self.label_10 = QLabel(self.scrollAreaWidgetContents)
        self.label_10.setObjectName(u"label_10")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_10)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.ncsToolEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.ncsToolEdit.setObjectName(u"ncsToolEdit")
        self.ncsToolEdit.setEnabled(True)

        self.horizontalLayout_8.addWidget(self.ncsToolEdit)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_8)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(17, 139, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.saveRimCheck.setText(QCoreApplication.translate("Form", u"Allow saving resources to RIM files.", None))
        self.useBetaChannel.setText(QCoreApplication.translate("Form", u"Check for beta updates and take me to their download link when they're available.", None))
        self.alsoCheckReleaseVersion.setText(QCoreApplication.translate("Form", u"Also check release version if it is newer than beta version.", None))
        self.mergeRimCheck.setText(QCoreApplication.translate("Form", u"Merge secondary ERF/RIM's in the Modules tab of the Main Window (i.e. '_s.rim' and '_dlg.erf').", None))
        self.attemptKeepOldGFFFields.setText(QCoreApplication.translate("Form", u"Attempts to keep any pre-existing GFF fields when saving the editor. Required for save editing.", None))
        self.moduleSortOptionComboBox.setItemText(0, QCoreApplication.translate("Form", u"Sort by filename", None))
        self.moduleSortOptionComboBox.setItemText(1, QCoreApplication.translate("Form", u"Sort by humanized area name", None))
        self.moduleSortOptionComboBox.setItemText(2, QCoreApplication.translate("Form", u"Sort by area name", None))

        self.greyRimCheck.setText(QCoreApplication.translate("Form", u"Set RIM files to have grey text in the Modules tab of the Main Window.", None))
        self.showPreviewUTCCheck.setText(QCoreApplication.translate("Form", u"Show 3D Preview in UTC Editor", None))
        self.showPreviewUTPCheck.setText(QCoreApplication.translate("Form", u"Show 3D Preview in UTP Editor", None))
        self.showPreviewUTDCheck.setText(QCoreApplication.translate("Form", u"Show 3D Preview in UTD Editor", None))
        self.profileToolset.setText(QCoreApplication.translate("Form", u"Profile various subroutines of the toolset.", None))
        self.label.setText(QCoreApplication.translate("Form", u"Temp Directory:", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"GFF Files:", None))
        self.gffEditorCombo.setItemText(0, QCoreApplication.translate("Form", u"GFF Editor", None))
        self.gffEditorCombo.setItemText(1, QCoreApplication.translate("Form", u"Specialized Editor", None))

        self.label_4.setText(QCoreApplication.translate("Form", u"NSS Compiler:", None))
        self.label_10.setText(QCoreApplication.translate("Form", u"NCS Decompiler:", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
