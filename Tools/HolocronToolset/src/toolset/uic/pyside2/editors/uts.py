# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'uts.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(410, 364)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
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
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.nameEdit = LocalizedStringLineEdit(self.tab)
        self.nameEdit.setObjectName(u"nameEdit")
        self.nameEdit.setMinimumSize(QSize(0, 23))

        self.horizontalLayout_18.addWidget(self.nameEdit)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.horizontalLayout_18)

        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName(u"label_14")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.tagEdit = QLineEdit(self.tab)
        self.tagEdit.setObjectName(u"tagEdit")

        self.horizontalLayout_19.addWidget(self.tagEdit)

        self.tagGenerateButton = QPushButton(self.tab)
        self.tagGenerateButton.setObjectName(u"tagGenerateButton")
        self.tagGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_19.addWidget(self.tagGenerateButton)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_19)

        self.label_38 = QLabel(self.tab)
        self.label_38.setObjectName(u"label_38")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_38)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.resrefEdit = QLineEdit(self.tab)
        self.resrefEdit.setObjectName(u"resrefEdit")
        self.resrefEdit.setMaxLength(16)

        self.horizontalLayout_20.addWidget(self.resrefEdit)

        self.resrefGenerateButton = QPushButton(self.tab)
        self.resrefGenerateButton.setObjectName(u"resrefGenerateButton")
        self.resrefGenerateButton.setMaximumSize(QSize(26, 16777215))

        self.horizontalLayout_20.addWidget(self.resrefGenerateButton)


        self.formLayout.setLayout(2, QFormLayout.FieldRole, self.horizontalLayout_20)

        self.label = QLabel(self.tab)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label)

        self.volumeSlider = QSlider(self.tab)
        self.volumeSlider.setObjectName(u"volumeSlider")
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setOrientation(Qt.Horizontal)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.volumeSlider)


        self.verticalLayout.addLayout(self.formLayout)

        self.activeCheckbox = QCheckBox(self.tab)
        self.activeCheckbox.setObjectName(u"activeCheckbox")

        self.verticalLayout.addWidget(self.activeCheckbox)

        self.verticalSpacer = QSpacerItem(20, 132, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_5 = QVBoxLayout(self.tab_2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.styleGroup = QGroupBox(self.tab_2)
        self.styleGroup.setObjectName(u"styleGroup")
        self.verticalLayout_2 = QVBoxLayout(self.styleGroup)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.styleOnceRadio = QRadioButton(self.styleGroup)
        self.styleOnceRadio.setObjectName(u"styleOnceRadio")
        self.styleOnceRadio.setChecked(True)

        self.verticalLayout_2.addWidget(self.styleOnceRadio)

        self.styleRepeatRadio = QRadioButton(self.styleGroup)
        self.styleRepeatRadio.setObjectName(u"styleRepeatRadio")

        self.verticalLayout_2.addWidget(self.styleRepeatRadio)

        self.styleSeamlessRadio = QRadioButton(self.styleGroup)
        self.styleSeamlessRadio.setObjectName(u"styleSeamlessRadio")

        self.verticalLayout_2.addWidget(self.styleSeamlessRadio)


        self.horizontalLayout.addWidget(self.styleGroup)

        self.orderGroup = QGroupBox(self.tab_2)
        self.orderGroup.setObjectName(u"orderGroup")
        self.verticalLayout_3 = QVBoxLayout(self.orderGroup)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.orderSequentialRadio = QRadioButton(self.orderGroup)
        self.orderSequentialRadio.setObjectName(u"orderSequentialRadio")
        self.orderSequentialRadio.setChecked(False)

        self.verticalLayout_3.addWidget(self.orderSequentialRadio)

        self.orderRandomRadio = QRadioButton(self.orderGroup)
        self.orderRandomRadio.setObjectName(u"orderRandomRadio")
        self.orderRandomRadio.setChecked(True)

        self.verticalLayout_3.addWidget(self.orderRandomRadio)


        self.horizontalLayout.addWidget(self.orderGroup)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.intervalGroup = QGroupBox(self.tab_2)
        self.intervalGroup.setObjectName(u"intervalGroup")
        self.formLayout_2 = QFormLayout(self.intervalGroup)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_2 = QLabel(self.intervalGroup)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.label_3 = QLabel(self.intervalGroup)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.intervalSpin = QSpinBox(self.intervalGroup)
        self.intervalSpin.setObjectName(u"intervalSpin")
        self.intervalSpin.setMaximum(1000000)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.intervalSpin)

        self.intervalVariationSpin = QSpinBox(self.intervalGroup)
        self.intervalVariationSpin.setObjectName(u"intervalVariationSpin")
        self.intervalVariationSpin.setMaximum(1000000)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.intervalVariationSpin)


        self.verticalLayout_4.addWidget(self.intervalGroup)


        self.verticalLayout_5.addLayout(self.verticalLayout_4)

        self.variationGroup = QGroupBox(self.tab_2)
        self.variationGroup.setObjectName(u"variationGroup")
        self.formLayout_3 = QFormLayout(self.variationGroup)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_4 = QLabel(self.variationGroup)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.volumeVariationSlider = QSlider(self.variationGroup)
        self.volumeVariationSlider.setObjectName(u"volumeVariationSlider")
        self.volumeVariationSlider.setMaximum(127)
        self.volumeVariationSlider.setOrientation(Qt.Horizontal)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.volumeVariationSlider)

        self.label_5 = QLabel(self.variationGroup)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_5)

        self.pitchVariationSlider = QSlider(self.variationGroup)
        self.pitchVariationSlider.setObjectName(u"pitchVariationSlider")
        self.pitchVariationSlider.setMaximum(100)
        self.pitchVariationSlider.setOrientation(Qt.Horizontal)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.pitchVariationSlider)


        self.verticalLayout_5.addWidget(self.variationGroup)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.horizontalLayout_3 = QHBoxLayout(self.tab_3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.soundList = QListWidget(self.tab_3)
        self.soundList.setObjectName(u"soundList")
        self.soundList.setEditTriggers(QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed)
        self.soundList.setAlternatingRowColors(True)

        self.verticalLayout_9.addWidget(self.soundList)


        self.horizontalLayout_3.addLayout(self.verticalLayout_9)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.addSoundButton = QPushButton(self.tab_3)
        self.addSoundButton.setObjectName(u"addSoundButton")

        self.verticalLayout_8.addWidget(self.addSoundButton)

        self.removeSoundButton = QPushButton(self.tab_3)
        self.removeSoundButton.setObjectName(u"removeSoundButton")

        self.verticalLayout_8.addWidget(self.removeSoundButton)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_4)

        self.moveUpButton = QPushButton(self.tab_3)
        self.moveUpButton.setObjectName(u"moveUpButton")

        self.verticalLayout_8.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton(self.tab_3)
        self.moveDownButton.setObjectName(u"moveDownButton")

        self.verticalLayout_8.addWidget(self.moveDownButton)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_5)

        self.playSoundButton = QPushButton(self.tab_3)
        self.playSoundButton.setObjectName(u"playSoundButton")

        self.verticalLayout_8.addWidget(self.playSoundButton)

        self.stopSoundButton = QPushButton(self.tab_3)
        self.stopSoundButton.setObjectName(u"stopSoundButton")

        self.verticalLayout_8.addWidget(self.stopSoundButton)


        self.horizontalLayout_3.addLayout(self.verticalLayout_8)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayout_7 = QVBoxLayout(self.tab_4)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.playEverywhereRadio = QRadioButton(self.tab_4)
        self.playEverywhereRadio.setObjectName(u"playEverywhereRadio")

        self.verticalLayout_6.addWidget(self.playEverywhereRadio)

        self.playRandomRadio = QRadioButton(self.tab_4)
        self.playRandomRadio.setObjectName(u"playRandomRadio")

        self.verticalLayout_6.addWidget(self.playRandomRadio)

        self.playSpecificRadio = QRadioButton(self.tab_4)
        self.playSpecificRadio.setObjectName(u"playSpecificRadio")

        self.verticalLayout_6.addWidget(self.playSpecificRadio)


        self.verticalLayout_7.addLayout(self.verticalLayout_6)

        self.distanceGroup = QGroupBox(self.tab_4)
        self.distanceGroup.setObjectName(u"distanceGroup")
        self.formLayout_4 = QFormLayout(self.distanceGroup)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_7 = QLabel(self.distanceGroup)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_7)

        self.cutoffSpin = QDoubleSpinBox(self.distanceGroup)
        self.cutoffSpin.setObjectName(u"cutoffSpin")

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.cutoffSpin)

        self.label_8 = QLabel(self.distanceGroup)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_8)

        self.maxVolumeDistanceSpin = QDoubleSpinBox(self.distanceGroup)
        self.maxVolumeDistanceSpin.setObjectName(u"maxVolumeDistanceSpin")

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.maxVolumeDistanceSpin)


        self.verticalLayout_7.addWidget(self.distanceGroup)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.heightGroup = QGroupBox(self.tab_4)
        self.heightGroup.setObjectName(u"heightGroup")
        self.formLayout_5 = QFormLayout(self.heightGroup)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.label_9 = QLabel(self.heightGroup)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.label_9)

        self.heightSpin = QDoubleSpinBox(self.heightGroup)
        self.heightSpin.setObjectName(u"heightSpin")

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.heightSpin)


        self.horizontalLayout_2.addWidget(self.heightGroup)

        self.rangeGroup = QGroupBox(self.tab_4)
        self.rangeGroup.setObjectName(u"rangeGroup")
        self.formLayout_6 = QFormLayout(self.rangeGroup)
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.label_10 = QLabel(self.rangeGroup)
        self.label_10.setObjectName(u"label_10")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.label_10)

        self.northRandomSpin = QDoubleSpinBox(self.rangeGroup)
        self.northRandomSpin.setObjectName(u"northRandomSpin")

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.northRandomSpin)

        self.label_11 = QLabel(self.rangeGroup)
        self.label_11.setObjectName(u"label_11")

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.eastRandomSpin = QDoubleSpinBox(self.rangeGroup)
        self.eastRandomSpin.setObjectName(u"eastRandomSpin")

        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.eastRandomSpin)


        self.horizontalLayout_2.addWidget(self.rangeGroup)


        self.verticalLayout_7.addLayout(self.horizontalLayout_2)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.gridLayout_2 = QGridLayout(self.tab_5)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.commentsEdit = QPlainTextEdit(self.tab_5)
        self.commentsEdit.setObjectName(u"commentsEdit")

        self.gridLayout_2.addWidget(self.commentsEdit, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_5, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 410, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Sound Editor", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", u"Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Tag:", None))
        self.tagGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"ResRef:", None))
        self.resrefGenerateButton.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Volume:", None))
        self.activeCheckbox.setText(QCoreApplication.translate("MainWindow", u"Active", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Basic", None))
        self.styleGroup.setTitle(QCoreApplication.translate("MainWindow", u"Play Style", None))
        self.styleOnceRadio.setText(QCoreApplication.translate("MainWindow", u"Once", None))
        self.styleRepeatRadio.setText(QCoreApplication.translate("MainWindow", u"Repeating", None))
        self.styleSeamlessRadio.setText(QCoreApplication.translate("MainWindow", u"Seamless Looping", None))
        self.orderGroup.setTitle(QCoreApplication.translate("MainWindow", u"Play Order", None))
        self.orderSequentialRadio.setText(QCoreApplication.translate("MainWindow", u"Sequential", None))
        self.orderRandomRadio.setText(QCoreApplication.translate("MainWindow", u"Random", None))
        self.intervalGroup.setTitle(QCoreApplication.translate("MainWindow", u"Interval", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Interval between sounds (s):", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Interval variation (s):", None))
        self.variationGroup.setTitle(QCoreApplication.translate("MainWindow", u"Variation", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Volume Variation:", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Pitch Variation:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.addSoundButton.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.removeSoundButton.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.moveUpButton.setText(QCoreApplication.translate("MainWindow", u"Move Up", None))
        self.moveDownButton.setText(QCoreApplication.translate("MainWindow", u"Move Down", None))
        self.playSoundButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.stopSoundButton.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Sounds", None))
        self.playEverywhereRadio.setText(QCoreApplication.translate("MainWindow", u"Plays everywhere in area", None))
        self.playRandomRadio.setText(QCoreApplication.translate("MainWindow", u"Plays from a random position each time", None))
        self.playSpecificRadio.setText(QCoreApplication.translate("MainWindow", u"Plays from a specific position", None))
        self.distanceGroup.setTitle(QCoreApplication.translate("MainWindow", u"Volume Distances", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Cutoff Distance (m):", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Max Volume Distance (m):", None))
        self.heightGroup.setTitle(QCoreApplication.translate("MainWindow", u"Height", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Height (m):", None))
        self.rangeGroup.setTitle(QCoreApplication.translate("MainWindow", u"Random Range:", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"North/South (m):", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"East/West (m):", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Positioning", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", u"Comments", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside2
