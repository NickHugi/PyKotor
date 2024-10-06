
################################################################################
## Form generated from reading UI file 'settings.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QGridLayout,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from toolset.gui.widgets.settings.application import ApplicationSettingsWidget
from toolset.gui.widgets.settings.git import GITWidget
from toolset.gui.widgets.settings.installations import InstallationsWidget
from toolset.gui.widgets.settings.misc import MiscWidget
from toolset.gui.widgets.settings.module_designer import ModuleDesignerWidget


class Ui_Dialog:
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(757, 451)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.settingsTree = QTreeWidget(self.splitter)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        QTreeWidgetItem(self.settingsTree)
        self.settingsTree.setObjectName("settingsTree")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settingsTree.sizePolicy().hasHeightForWidth())
        self.settingsTree.setSizePolicy(sizePolicy)
        self.settingsTree.setHeaderHidden(True)
        self.splitter.addWidget(self.settingsTree)
        self.settingsStack = QStackedWidget(self.splitter)
        self.settingsStack.setObjectName("settingsStack")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.settingsStack.sizePolicy().hasHeightForWidth())
        self.settingsStack.setSizePolicy(sizePolicy1)
        self.installationsPage = QWidget()
        self.installationsPage.setObjectName("installationsPage")
        self.gridLayout_2 = QGridLayout(self.installationsPage)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.installationsWidget = InstallationsWidget(self.installationsPage)
        self.installationsWidget.setObjectName("installationsWidget")

        self.gridLayout_2.addWidget(self.installationsWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.installationsPage)
        self.applicationSettingsPage = QWidget()
        self.applicationSettingsPage.setObjectName("applicationSettingsPage")
        self.gridLayout_26 = QGridLayout(self.applicationSettingsPage)
        self.gridLayout_26.setObjectName("gridLayout_26")
        self.applicationSettingsWidget = ApplicationSettingsWidget(self.applicationSettingsPage)
        self.applicationSettingsWidget.setObjectName("applicationSettingsWidget")

        self.gridLayout_26.addWidget(self.applicationSettingsWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.applicationSettingsPage)
        self.moduleDesignerPage = QWidget()
        self.moduleDesignerPage.setObjectName("moduleDesignerPage")
        self.gridLayout_3 = QGridLayout(self.moduleDesignerPage)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.moduleDesignerWidget = ModuleDesignerWidget(self.moduleDesignerPage)
        self.moduleDesignerWidget.setObjectName("moduleDesignerWidget")

        self.gridLayout_3.addWidget(self.moduleDesignerWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.moduleDesignerPage)
        self.miscPage = QWidget()
        self.miscPage.setObjectName("miscPage")
        self.gridLayout = QGridLayout(self.miscPage)
        self.gridLayout.setObjectName("gridLayout")
        self.miscWidget = MiscWidget(self.miscPage)
        self.miscWidget.setObjectName("miscWidget")

        self.gridLayout.addWidget(self.miscWidget, 0, 1, 1, 1)

        self.settingsStack.addWidget(self.miscPage)
        self.gitEditorPage = QWidget()
        self.gitEditorPage.setObjectName("gitEditorPage")
        self.gridLayout_4 = QGridLayout(self.gitEditorPage)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gitEditorWidget = GITWidget(self.gitEditorPage)
        self.gitEditorWidget.setObjectName("gitEditorWidget")

        self.gridLayout_4.addWidget(self.gitEditorWidget, 0, 0, 1, 1)

        self.settingsStack.addWidget(self.gitEditorPage)
        self.splitter.addWidget(self.settingsStack)

        self.verticalLayout.addWidget(self.splitter)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName("buttonBox")
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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Settings", None))
        ___qtreewidgetitem = self.settingsTree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("Dialog", "1", None));

        __sortingEnabled = self.settingsTree.isSortingEnabled()
        self.settingsTree.setSortingEnabled(False)
        ___qtreewidgetitem1 = self.settingsTree.topLevelItem(0)
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("Dialog", "Installations", None));
        ___qtreewidgetitem2 = self.settingsTree.topLevelItem(1)
        ___qtreewidgetitem2.setText(0, QCoreApplication.translate("Dialog", "GIT Editor", None));
        ___qtreewidgetitem3 = self.settingsTree.topLevelItem(2)
        ___qtreewidgetitem3.setText(0, QCoreApplication.translate("Dialog", "Module Designer", None));
        ___qtreewidgetitem4 = self.settingsTree.topLevelItem(3)
        ___qtreewidgetitem4.setText(0, QCoreApplication.translate("Dialog", "Misc", None));
        ___qtreewidgetitem5 = self.settingsTree.topLevelItem(4)
        ___qtreewidgetitem5.setText(0, QCoreApplication.translate("Dialog", "Application", None));
        self.settingsTree.setSortingEnabled(__sortingEnabled)

    # retranslateUi

