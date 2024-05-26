# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lip_syncer.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(260, 357)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.languageSelect = QComboBox(Dialog)
        self.languageSelect.addItem("")
        self.languageSelect.setObjectName(u"languageSelect")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.languageSelect)


        self.verticalLayout.addLayout(self.formLayout)

        self.audioList = QListWidget(Dialog)
        self.audioList.setObjectName(u"audioList")

        self.verticalLayout.addWidget(self.audioList)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.AddAudioButton = QPushButton(Dialog)
        self.AddAudioButton.setObjectName(u"AddAudioButton")

        self.horizontalLayout.addWidget(self.AddAudioButton)

        self.removeAudioButton = QPushButton(Dialog)
        self.removeAudioButton.setObjectName(u"removeAudioButton")

        self.horizontalLayout.addWidget(self.removeAudioButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"LLanguage:", None))
        self.languageSelect.setItemText(0, QCoreApplication.translate("Dialog", u"English", None))

        self.AddAudioButton.setText(QCoreApplication.translate("Dialog", u"Load MP3s", None))
        self.removeAudioButton.setText(QCoreApplication.translate("Dialog", u"Remove MP3", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
