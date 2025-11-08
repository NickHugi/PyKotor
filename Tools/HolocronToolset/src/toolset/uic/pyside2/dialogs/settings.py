# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from toolset.gui.widgets.settings.misc import MiscWidget
from toolset.gui.widgets.settings.installations import InstallationsWidget
from toolset.gui.widgets.settings.application import ApplicationSettingsWidget
from toolset.gui.widgets.settings.module_designer import ModuleDesignerWidget
from toolset.gui.widgets.settings.git import GITWidget


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(757, 451)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.settingsTree = QTreeWidget(self.splitter)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        self.settingsTree.setObjectName(u"settingsTree")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settingsTree.sizePolicy().hasHeightForWidth())
        self.settingsTree.setSizePolicy(sizePolicy)
        self.settingsTree.setHeaderHidden(True)
        self.splitter.addWidget(self.settingsTree)
        self.settingsStack = QStackedWidget(self.splitter)
        self.settingsStack.setObjectName(u"settingsStack")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.settingsStack.sizePolicy().hasHeightForWidth())
        self.settingsStack.setSizePolicy(sizePolicy1)
        self.installationsPage = QWidget()
        self.installationsPage.setObjectName(u"installationsPage")
        self.gridLayout_2 = QGridLayout(self.installationsPage)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.installationsWidget = InstallationsWidget(self.installationsPage)
        self.installationsWidget.setObjectName(u"installationsWidget")

        self.gridLayout_2.addWidget(self.installationsWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.installationsPage)
        self.applicationSettingsPage = QWidget()
        self.applicationSettingsPage.setObjectName(u"applicationSettingsPage")
        self.gridLayout_26 = QGridLayout(self.applicationSettingsPage)
        self.gridLayout_26.setObjectName(u"gridLayout_26")
        self.applicationSettingsWidget = ApplicationSettingsWidget(self.applicationSettingsPage)
        self.applicationSettingsWidget.setObjectName(u"applicationSettingsWidget")

        self.gridLayout_26.addWidget(self.applicationSettingsWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.applicationSettingsPage)
        self.moduleDesignerPage = QWidget()
        self.moduleDesignerPage.setObjectName(u"moduleDesignerPage")
        self.gridLayout_3 = QGridLayout(self.moduleDesignerPage)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.moduleDesignerWidget = ModuleDesignerWidget(self.moduleDesignerPage)
        self.moduleDesignerWidget.setObjectName(u"moduleDesignerWidget")

        self.gridLayout_3.addWidget(self.moduleDesignerWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.moduleDesignerPage)
        self.miscPage = QWidget()
        self.miscPage.setObjectName(u"miscPage")
        self.gridLayout = QGridLayout(self.miscPage)
        self.gridLayout.setObjectName(u"gridLayout")
        self.miscWidget = MiscWidget(self.miscPage)
        self.miscWidget.setObjectName(u"miscWidget")

        self.gridLayout.addWidget(self.miscWidget, 0, 1, 1, 1)

        self.settingsStack.addWidget(self.miscPage)
        self.gitEditorPage = QWidget()
        self.gitEditorPage.setObjectName(u"gitEditorPage")
        self.gridLayout_4 = QGridLayout(self.gitEditorPage)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gitEditorWidget = GITWidget(self.gitEditorPage)
        self.gitEditorWidget.setObjectName(u"gitEditorWidget")

        self.gridLayout_4.addWidget(self.gitEditorWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.gitEditorPage)
        self.splitter.addWidget(self.settingsStack)

        self.verticalLayout.addWidget(self.splitter)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        self.settingsStack.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Settings", None))
        ___qtreewidgetitem = self.settingsTree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("Dialog", u"1", None));

        __sortingEnabled = self.settingsTree.isSortingEnabled()
        self.settingsTree.setSortingEnabled(False)
        ___qtreewidgetitem1 = self.settingsTree.topLevelItem(0)
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("Dialog", u"Installations", None));
        ___qtreewidgetitem2 = self.settingsTree.topLevelItem(1)
        ___qtreewidgetitem2.setText(0, QCoreApplication.translate("Dialog", u"GIT Editor", None));
        ___qtreewidgetitem3 = self.settingsTree.topLevelItem(2)
        ___qtreewidgetitem3.setText(0, QCoreApplication.translate("Dialog", u"Module Designer", None));
        ___qtreewidgetitem4 = self.settingsTree.topLevelItem(3)
        ___qtreewidgetitem4.setText(0, QCoreApplication.translate("Dialog", u"Misc", None));
        ___qtreewidgetitem5 = self.settingsTree.topLevelItem(4)
        ___qtreewidgetitem5.setText(0, QCoreApplication.translate("Dialog", u"Application", None));
        self.settingsTree.setSortingEnabled(__sortingEnabled)

    # retranslateUi


from toolset.rcc import resources_rc_pyside2
