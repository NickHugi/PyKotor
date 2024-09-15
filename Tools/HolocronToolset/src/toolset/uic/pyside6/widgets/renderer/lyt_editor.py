# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lyt_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QGraphicsView, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_LYTEditor(object):
    def setupUi(self, LYTEditor):
        if not LYTEditor.objectName():
            LYTEditor.setObjectName(u"LYTEditor")
        LYTEditor.resize(400, 300)
        self.verticalLayout = QVBoxLayout(LYTEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.graphicsView = QGraphicsView(LYTEditor)
        self.graphicsView.setObjectName(u"graphicsView")

        self.verticalLayout.addWidget(self.graphicsView)


        self.retranslateUi(LYTEditor)

        QMetaObject.connectSlotsByName(LYTEditor)
    # setupUi

    def retranslateUi(self, LYTEditor):
        LYTEditor.setWindowTitle(QCoreApplication.translate("LYTEditor", u"LYT Editor", None))
    # retranslateUi


from toolset.rcc import resources_rc_pyside6
