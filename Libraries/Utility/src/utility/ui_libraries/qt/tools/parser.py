from __future__ import annotations

import enum
import json

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any

import qtpy

from qtpy.QtCore import (
    QBitArray,
    QByteArray,
    QDate,
    QDateTime,
    QEasingCurve,
    QItemSelection,
    QItemSelectionRange,
    QJsonDocument,
    QLine,
    QLineF,
    QLocale,
    QMargins,
    QMetaType,
    QObject,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QRegularExpression,
    QSize,
    QSizeF,
    QTime,
    QUrl,
    QUuid,
    Qt,
)
from qtpy.QtGui import (
    QBitmap,
    QBrush,
    QColor,
    QCursor,
    QFont,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QMatrix4x4,
    QMovie,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
    QPolygon,
    QPolygonF,
    QQuaternion,
    QRegion,
    QTextBlock,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextDocumentFragment,
    QTextFormat,
    QTextFragment,
    QTextFrame,
    QTextFrameFormat,
    QTextImageFormat,
    QTextLayout,
    QTextLength,
    QTextLine,
    QTextList,
    QTextListFormat,
    QTextOption,
    QTextTable,
    QTextTableCell,
    QTextTableCellFormat,
    QTextTableFormat,
    QTransform,
    QVector2D,
    QVector3D,
    QVector4D,
)
from qtpy.QtWidgets import (
    QCalendarWidget,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFontComboBox,
    QFontDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLCDNumber,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTimeEdit,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.tools.qt_meta import determine_type, get_qt_meta_type

QMatrix = object
try:
    from qtpy.QtGui import QMatrix
except ImportError:
    from qtpy.QtGui import QMatrix  # noqa: F401
if qtpy.API_NAME == "PySide2":
    from qtpy.QtCore import QJsonArray, QJsonValue  # noqa: F401
elif qtpy.API_NAME == "PySide6":
    from qtpy.QtCore import QJsonArray, QJsonValue  # noqa: F401, TCH002

if TYPE_CHECKING:
    from datetime import date, datetime, time

    from qtpy.QtCore import QModelIndex


class QtObjectParser:
    @classmethod
    def create_input_widget(cls, param_type: type, current_value: Any) -> QWidget:
        meta_type = determine_type(param_type, current_value)
        meta_type_type = get_qt_meta_type(param_type, current_value)
        assert meta_type_type != 0, f"Unknown param_type: {param_type} and current_value: {current_value}"

        widget_creators = {
            QMetaType.Type.Void: lambda: cls.create_void_widget(current_value),
            QMetaType.Type.Bool: lambda: cls.create_bool_widget(current_value),
            QMetaType.Type.Int: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.UInt: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.LongLong: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.ULongLong: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.Double: lambda: cls.create_number_widget(current_value, QDoubleSpinBox),
            QMetaType.Type.Long: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.Short: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.Char: lambda: cls.create_char_widget(current_value),
            QMetaType.Type.ULong: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.UShort: lambda: cls.create_number_widget(current_value, QSpinBox),
            QMetaType.Type.UChar: lambda: cls.create_char_widget(current_value),
            QMetaType.Type.Float: lambda: cls.create_number_widget(current_value, QDoubleSpinBox),
            QMetaType.Type.QChar: lambda: cls.create_char_widget(current_value),
            QMetaType.Type.QString: lambda: cls.create_string_widget(current_value),
            QMetaType.Type.QStringList: lambda: cls.create_stringlist_widget(current_value),
            QMetaType.Type.QByteArray: lambda: cls.create_bytearray_widget(current_value),
            QMetaType.Type.QBitArray: lambda: cls.create_bitarray_widget(current_value),
            QMetaType.Type.QDate: lambda: cls.create_date_widget(current_value),
            QMetaType.Type.QTime: lambda: cls.create_time_widget(current_value),
            QMetaType.Type.QDateTime: lambda: cls.create_datetime_widget(current_value),
            QMetaType.Type.QUrl: lambda: cls.create_url_widget(current_value),
            QMetaType.Type.QLocale: lambda: cls.create_locale_widget(current_value),
            QMetaType.Type.QRect: lambda: cls.create_rect_widget(current_value),
            QMetaType.Type.QRectF: lambda: cls.create_rect_widget(current_value, float),
            QMetaType.Type.QSize: lambda: cls.create_size_widget(current_value),
            QMetaType.Type.QSizeF: lambda: cls.create_size_widget(current_value, float),
            QMetaType.Type.QLine: lambda: cls.create_line_widget(current_value),
            QMetaType.Type.QLineF: lambda: cls.create_line_widget(current_value, float),
            QMetaType.Type.QPoint: lambda: cls.create_point_widget(current_value),
            QMetaType.Type.QPointF: lambda: cls.create_point_widget(current_value, float),
            QMetaType.Type.QVariantHash: lambda: cls.create_variant_hash_widget(current_value),
            QMetaType.Type.QEasingCurve: lambda: cls.create_easing_curve_widget(current_value),
            QMetaType.Type.QUuid: lambda: cls.create_uuid_widget(current_value),
            QMetaType.Type.QVariant: lambda: cls.create_variant_widget(current_value),
            QMetaType.Type.QModelIndex: lambda: cls.create_model_index_widget(current_value),
            QMetaType.Type.QRegularExpression: lambda: cls.create_regular_expression_widget(current_value),
            QMetaType.Type.QJsonValue: lambda: cls.create_json_value_widget(current_value),
            QMetaType.Type.QJsonObject: lambda: cls.create_json_object_widget(current_value),
            QMetaType.Type.QJsonArray: lambda: cls.create_json_array_widget(current_value),
            QMetaType.Type.QJsonDocument: lambda: cls.create_json_document_widget(current_value),
            QMetaType.Type.QByteArrayList: lambda: cls.create_bytearray_list_widget(current_value),
            QMetaType.Type.QFont: lambda: cls.create_font_widget(current_value),
            QMetaType.Type.QPixmap: lambda: cls.create_pixmap_widget(current_value),
            QMetaType.Type.QBrush: lambda: cls.create_brush_widget(current_value),
            QMetaType.Type.QColor: lambda: cls.create_color_widget(current_value),
            QMetaType.Type.QPalette: lambda: cls.create_palette_widget(current_value),
            QMetaType.Type.QIcon: lambda: cls.create_icon_widget(current_value),
            QMetaType.Type.QImage: lambda: cls.create_image_widget(current_value),
            QMetaType.Type.QPolygon: lambda: cls.create_polygon_widget(current_value),
            QMetaType.Type.QRegion: lambda: cls.create_region_widget(current_value),
            QMetaType.Type.QBitmap: lambda: cls.create_bitmap_widget(current_value),
            QMetaType.Type.QCursor: lambda: cls.create_cursor_widget(current_value),
            QMetaType.Type.QKeySequence: lambda: cls.create_key_sequence_widget(current_value),
            QMetaType.Type.QPen: lambda: cls.create_pen_widget(current_value),
            QMetaType.Type.QTextLength: lambda: cls.create_text_length_widget(current_value),
            QMetaType.Type.QTextFormat: lambda: cls.create_text_format_widget(current_value),
            #QMetaType.Type.QMatrix: lambda: cls.create_text_format_widget(current_value),
            QMetaType.Type.QTransform: lambda: cls.create_transform_widget(current_value),
            QMetaType.Type.QMatrix4x4: lambda: cls.create_matrix4x4_widget(current_value),
            QMetaType.Type.QVector2D: lambda: cls.create_vector2d_widget(current_value),
            QMetaType.Type.QVector3D: lambda: cls.create_vector3d_widget(current_value),
            QMetaType.Type.QVector4D: lambda: cls.create_vector4d_widget(current_value),
            QMetaType.Type.QQuaternion: lambda: cls.create_quaternion_widget(current_value),
            QMetaType.Type.QPolygonF: lambda: cls.create_polygon_widget(current_value, float),
            QMetaType.Type.QSizePolicy: lambda: cls.create_text_format_widget(current_value),
        }

        if meta_type_type in widget_creators:
            widget = widget_creators[meta_type_type]()
            return widget

        # Handle QObject subclasses
        if issubclass(param_type, QObject):
            return cls.create_qobject_widget(current_value, param_type)

        # Handle Enum types
        if issubclass(param_type, enum.Enum):
            return cls.create_enum_widget(param_type, current_value)

        # Default fallback
        return cls.create_qobject_widget(current_value)

    @classmethod
    def create_void_widget(cls, value: Any) -> QLineEdit:
        widget = QLineEdit(str(value))
        widget.setPlaceholderText("Enter a ctypes pointer or 'None'")
        return widget

    @classmethod
    def create_bool_widget(cls, value: bool) -> QCheckBox:  # noqa: FBT001
        widget = QCheckBox()
        widget.setChecked(value)
        return widget

    @classmethod
    def create_number_widget(cls, value: float, widget_type: type[QSpinBox | QDoubleSpinBox]) -> QSpinBox | QDoubleSpinBox:
        widget = widget_type()
        widget.setValue(value)
        return widget

    @classmethod
    def create_char_widget(cls, value: str) -> QLineEdit:
        widget = QLineEdit(value)
        widget.setMaxLength(1)
        return widget

    @classmethod
    def create_string_widget(cls, value: str) -> QLineEdit:
        return QLineEdit(value)

    @classmethod
    def create_stringlist_widget(cls, value: list[str]) -> QTextEdit:
        widget = QTextEdit()
        widget.setPlainText("\n".join(value))
        return widget

    @classmethod
    def create_bytearray_widget(cls, value: QByteArray) -> QLineEdit:
        widget = QLineEdit(value.toHex().data().decode())
        widget.setInputMask("HH " * len(value))
        return widget

    @classmethod
    def create_bitarray_widget(cls, value: QBitArray) -> QLineEdit:
        widget = QLineEdit("".join(["1" if value.testBit(i) else "0" for i in range(value.size())]))
        widget.setInputMask("B" * value.size())
        return widget

    @classmethod
    def create_date_widget(cls, value: QDate) -> QDateEdit:
        widget = QDateEdit(value)
        widget.setCalendarPopup(True)
        return widget

    @classmethod
    def create_time_widget(cls, value: QTime) -> QTimeEdit:
        return QTimeEdit(value)

    @classmethod
    def create_datetime_widget(cls, value: QDateTime) -> QDateTimeEdit:
        widget = QDateTimeEdit(value)
        widget.setCalendarPopup(True)
        return widget

    @classmethod
    def create_url_widget(cls, value: QUrl) -> QLineEdit:
        return QLineEdit(value.toString())

    @classmethod
    def create_locale_widget(cls, value: QLocale) -> QComboBox:
        widget = QComboBox()
        for locale in QLocale.matchingLocales(QLocale.AnyLanguage, QLocale.AnyScript, QLocale.AnyCountry):
            widget.addItem(QLocale(locale).name())
        widget.setCurrentText(value.name())
        return widget

    @classmethod
    def create_rect_widget(cls, value: QRect | QRectF, value_type: type = int) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)
        x = QSpinBox() if value_type is int else QDoubleSpinBox()
        y = QSpinBox() if value_type is int else QDoubleSpinBox()
        width = QSpinBox() if value_type is int else QDoubleSpinBox()
        height = QSpinBox() if value_type is int else QDoubleSpinBox()

        layout.addWidget(QLabel("X:"), 0, 0)
        layout.addWidget(x, 0, 1)
        layout.addWidget(QLabel("Y:"), 1, 0)
        layout.addWidget(y, 1, 1)
        layout.addWidget(QLabel("Width:"), 2, 0)
        layout.addWidget(width, 2, 1)
        layout.addWidget(QLabel("Height:"), 3, 0)
        layout.addWidget(height, 3, 1)

        x.setValue(value.x())
        y.setValue(value.y())
        width.setValue(value.width())
        height.setValue(value.height())

        return widget

    @classmethod
    def create_size_widget(cls, value: QSize | QSizeF, value_type: type = int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        width = QSpinBox() if value_type is int else QDoubleSpinBox()
        height = QSpinBox() if value_type is int else QDoubleSpinBox()

        layout.addWidget(QLabel("Width:"))
        layout.addWidget(width)
        layout.addWidget(QLabel("Height:"))
        layout.addWidget(height)

        width.setValue(value.width())
        height.setValue(value.height())

        return widget

    @classmethod
    def create_line_widget(cls, value: QLine | QLineF, value_type: type = int) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)
        x1 = QSpinBox() if value_type is int else QDoubleSpinBox()
        y1 = QSpinBox() if value_type is int else QDoubleSpinBox()
        x2 = QSpinBox() if value_type is int else QDoubleSpinBox()
        y2 = QSpinBox() if value_type is int else QDoubleSpinBox()

        layout.addWidget(QLabel("X1:"), 0, 0)
        layout.addWidget(x1, 0, 1)
        layout.addWidget(QLabel("Y1:"), 1, 0)
        layout.addWidget(y1, 1, 1)
        layout.addWidget(QLabel("X2:"), 2, 0)
        layout.addWidget(x2, 2, 1)
        layout.addWidget(QLabel("Y2:"), 3, 0)
        layout.addWidget(y2, 3, 1)

        x1.setValue(value.x1())
        y1.setValue(value.y1())
        x2.setValue(value.x2())
        y2.setValue(value.y2())

        return widget

    @classmethod
    def create_point_widget(cls, value: QPoint | QPointF, value_type: type = int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        x = QSpinBox() if value_type is int else QDoubleSpinBox()
        y = QSpinBox() if value_type is int else QDoubleSpinBox()

        layout.addWidget(QLabel("X:"))
        layout.addWidget(x)
        layout.addWidget(QLabel("Y:"))
        layout.addWidget(y)

        x.setValue(value.x())
        y.setValue(value.y())

        return widget

    @classmethod
    def create_regexp_widget(cls, value: QRegExp) -> QLineEdit:
        return QLineEdit(value.pattern())

    @classmethod
    def create_variant_hash_widget(cls, value: dict) -> QTableWidget:
        widget = QTableWidget(len(value), 2)
        widget.setHorizontalHeaderLabels(["Key", "Value"])
        for row, (key, val) in enumerate(value.items()):
            widget.setItem(row, 0, QTableWidgetItem(str(key)))
            widget.setItem(row, 1, QTableWidgetItem(str(val)))
        return widget

    @classmethod
    def create_easing_curve_widget(cls, value: QEasingCurve) -> QComboBox:
        widget = QComboBox()
        for curve_type_name, curve_type_value in QEasingCurve.Type.__dict__.items():
            widget.addItem(curve_type_name, curve_type_value)
        widget.setCurrentIndex(widget.findData(value.type()))
        return widget

    @classmethod
    def create_uuid_widget(cls, value: QUuid) -> QLineEdit:
        return QLineEdit(value.toString())

    @classmethod
    def create_variant_widget(cls, value: Any) -> QLineEdit:
        return QLineEdit(str(value))

    @classmethod
    def create_model_index_widget(cls, value: QModelIndex) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        row = QSpinBox()
        column = QSpinBox()

        layout.addWidget(QLabel("Row:"))
        layout.addWidget(row)
        layout.addWidget(QLabel("Column:"))
        layout.addWidget(column)

        row.setValue(value.row())
        column.setValue(value.column())

        return widget

    @classmethod
    def create_regular_expression_widget(cls, value: QRegularExpression) -> QLineEdit:
        return QLineEdit(value.pattern())

    @classmethod
    def create_json_value_widget(cls, value: QJsonValue) -> QTextEdit:
        widget = QTextEdit()
        widget.setPlainText(str(value.toVariant()))
        return widget

    @classmethod
    def create_json_document_widget(cls, value: QJsonDocument | QJsonArray) -> QTextEdit:
        widget = QTextEdit()
        widget.setPlainText(
            value.toJson().data().decode()
            if isinstance(value, QJsonDocument)
            else json.dumps(value.toVariantList())
        )
        return widget

    @classmethod
    def create_bytearray_list_widget(cls, value: list[QByteArray]) -> QTextEdit:
        widget = QTextEdit("\n".join([ba.toHex().data().decode() for ba in value]))
        return widget

    @classmethod
    def create_font_widget(cls, value: QFont) -> QPushButton:
        button = QPushButton(value.family())
        button.setFont(value)
        button.clicked.connect(lambda: cls.update_font_button(button))
        return button

    @classmethod
    def update_font_button(cls, button: QPushButton):
        font, ok = QFontDialog.getFont(button.font(), button)
        if ok:
            button.setFont(font)
            button.setText(font.family())

    @classmethod
    def create_pixmap_widget(cls, value: QPixmap) -> QLabel:
        widget = QLabel()
        widget.setPixmap(value.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return widget

    @classmethod
    def create_brush_widget(cls, value: QBrush) -> QPushButton:
        button = QPushButton()
        cls.update_brush_button(button, value)
        button.clicked.connect(lambda: cls.update_brush_button(button))
        return button

    @classmethod
    def update_brush_button(cls, button: QPushButton, brush: QBrush | None = None):
        if brush is None:
            color = QColorDialog.getColor(button.palette().color(QPalette.Button), button.window())
            if not color.isValid():
                return
            brush = QBrush(color)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(brush)
        painter.drawRect(0, 0, 32, 32)
        painter.end()
        button.setIcon(QIcon(pixmap))

    @classmethod
    def create_color_widget(cls, value: QColor) -> QPushButton:
        button = QPushButton()
        cls.update_color_button(button, value)
        button.clicked.connect(lambda: cls.update_color_button(button))
        return button

    @classmethod
    def update_color_button(cls, button: QPushButton, color: QColor | None = None):
        if color is None:
            color = QColorDialog.getColor(button.palette().color(QPalette.Button), button.window())
            if not color.isValid():
                return
        button.setStyleSheet(f"background-color: {color.name()};")

    @classmethod
    def create_palette_widget(cls, value: QPalette) -> QPushButton:
        button = QPushButton("Edit Palette")
        button.clicked.connect(lambda: cls.update_palette_button(button, value))
        return button

    @classmethod
    def update_palette_button(cls, button: QPushButton, palette: QPalette):
        new_palette = QColorDialog.getColor(button.palette().color(QPalette.Button), button.window())
        if new_palette.isValid():
            palette.setColor(QPalette.Button, new_palette)
            button.setPalette(palette)
            button.setText(f"Palette ({palette.currentColorGroup()})")

    @classmethod
    def create_icon_widget(cls, value: QIcon) -> QPushButton:
        button = QPushButton()
        cls.update_icon_button(button, value)
        button.clicked.connect(lambda: cls.update_icon_button(button))
        return button

    @classmethod
    def update_icon_button(cls, button: QPushButton, icon: QIcon | None = None):
        if icon is None:
            file_name, _ = QFileDialog.getOpenFileName(button.window(), "Select Icon", "", "Image Files (*.png *.jpg *.bmp)")
            if file_name:
                icon = QIcon(file_name)
            else:
                return
        button.setIcon(icon)

    @classmethod
    def create_image_widget(cls, value: QImage) -> QLabel:
        widget = QLabel()
        widget.setPixmap(QPixmap.fromImage(value).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return widget

    @classmethod
    def create_polygon_widget(cls, value: QPolygon | QPolygonF, value_type: type = int) -> QTableWidget:
        widget = QTableWidget(value.size(), 2)
        widget.setHorizontalHeaderLabels(["X", "Y"])
        for row in range(value.size()):
            point = value.at(row)
            widget.setItem(row, 0, QTableWidgetItem(str(point.x())))
            widget.setItem(row, 1, QTableWidgetItem(str(point.y())))
        return widget

    @classmethod
    def create_region_widget(cls, value: QRegion) -> QTextEdit:
        widget = QTextEdit("\n".join([f"({rect.x()}, {rect.y()}, {rect.width()}, {rect.height()})" for rect in value.rects()]))
        return widget

    @classmethod
    def create_bitmap_widget(cls, value: QBitmap) -> QLabel:
        widget = QLabel()
        widget.setPixmap(value.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return widget

    @classmethod
    def create_cursor_widget(cls, value: QCursor) -> QComboBox:
        widget = QComboBox()
        cursor_shapes = [
            Qt.ArrowCursor,
            Qt.UpArrowCursor,
            Qt.CrossCursor,
            Qt.WaitCursor,
            Qt.IBeamCursor,
            Qt.SizeVerCursor,
            Qt.SizeHorCursor,
            Qt.SizeBDiagCursor,
            Qt.SizeFDiagCursor,
            Qt.SizeAllCursor,
            Qt.BlankCursor,
            Qt.SplitVCursor,
            Qt.SplitHCursor,
            Qt.PointingHandCursor,
            Qt.ForbiddenCursor,
            Qt.WhatsThisCursor,
            Qt.BusyCursor,
            Qt.OpenHandCursor,
            Qt.ClosedHandCursor,
            Qt.DragCopyCursor,
            Qt.DragMoveCursor,
            Qt.DragLinkCursor,
        ]
        widget.addItems([str(shape).split(".")[-1] for shape in cursor_shapes])
        widget.setCurrentText(str(value.shape()).split(".")[-1])
        return widget

    @classmethod
    def create_key_sequence_widget(cls, value: QKeySequence) -> QKeySequenceEdit:
        widget = QKeySequenceEdit(value)
        return widget

    @classmethod
    def create_pen_widget(cls, value: QPen) -> QPushButton:
        button = QPushButton()
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(value)
        painter.drawLine(0, 16, 32, 16)
        painter.end()
        button.setIcon(QIcon(pixmap))
        button.clicked.connect(lambda: cls.update_pen_button(button, value))
        return button

    @classmethod
    def update_pen_button(cls, button: QPushButton, current_pen: QPen):
        dialog = QDialog(button)
        dialog.setWindowTitle("Edit Pen")
        layout = QVBoxLayout(dialog)

        color_button = QPushButton("Color")
        color_button.clicked.connect(lambda: cls.update_pen_color(color_button, current_pen))
        layout.addWidget(color_button)

        width_spin = QSpinBox()
        width_spin.setRange(1, 20)
        width_spin.setValue(current_pen.width())
        width_spin.valueChanged.connect(lambda v: current_pen.setWidth(v))
        layout.addWidget(QLabel("Width:"))
        layout.addWidget(width_spin)

        style_combo = QComboBox()
        pen_styles = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine, Qt.DashDotDotLine]
        style_combo.addItems([str(style).split(".")[-1] for style in pen_styles])
        style_combo.setCurrentIndex(pen_styles.index(current_pen.style()))
        style_combo.currentIndexChanged.connect(lambda i: current_pen.setStyle(pen_styles[i]))
        layout.addWidget(QLabel("Style:"))
        layout.addWidget(style_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.Accepted:
            cls.update_button_icon(button, current_pen)

    @classmethod
    def update_pen_color(cls, color_button: QPushButton, pen: QPen):
        color = QColorDialog.getColor(pen.color(), color_button)
        if color.isValid():
            pen.setColor(color)
            cls.update_button_icon(color_button, pen)

    @classmethod
    def update_button_icon(cls, button: QPushButton, pen: QPen):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(pen)
        painter.drawLine(0, 16, 32, 16)
        painter.end()
        button.setIcon(QIcon(pixmap))

    @classmethod
    def create_text_length_widget(cls, value: QTextLength) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        type_combo = QComboBox()
        type_combo.addItems([attr for attr in dir(QTextLength.Type) if not attr.startswith("__")])
        type_combo.setCurrentText(next(attr for attr in dir(QTextLength.Type) if getattr(QTextLength.Type, attr) == value.type()))
        value_spin = QDoubleSpinBox()
        value_spin.setValue(value.value(1000000))
        value_spin.setMaximum(1000000)  # Set a reasonable maximum value
        layout.addWidget(type_combo)
        layout.addWidget(value_spin)
        return widget

    @classmethod
    def create_text_format_widget(cls, value: QTextFormat) -> QPushButton:
        button = QPushButton("Edit Text Format")
        button.clicked.connect(lambda: cls.update_text_format_button(button, value))
        return button

    @classmethod
    def update_text_format_button(cls, button: QPushButton, current_format: QTextFormat):
        dialog = QDialog(button)
        dialog.setWindowTitle("Edit Text Format")
        layout = QVBoxLayout(dialog)

        color_button = QPushButton("Color")
        color_button.clicked.connect(lambda: cls.update_text_format_color(color_button, current_format))
        layout.addWidget(color_button)

        font_button = QPushButton("Font")

    @classmethod
    def update_text_format_color(cls, color_button: QPushButton, format: QTextFormat):
        color = QColorDialog.getColor(format.foreground().color(), color_button)
        if color.isValid():
            format.setForeground(color)
            cls.update_text_format_button(color_button, format)

    @classmethod
    def create_transform_widget(cls, value: QTransform) -> QTableWidget:
        widget = QTableWidget(3, 3)
        for i in range(3):
            for j in range(3):
                widget.setItem(i, j, QTableWidgetItem(str(value.m(i, j))))
        return widget

    @classmethod
    def create_matrix4x4_widget(cls, value: QMatrix4x4) -> QTableWidget:
        widget = QTableWidget(4, 4)
        for i in range(4):
            for j in range(4):
                widget.setItem(i, j, QTableWidgetItem(str(value.m(i, j))))
        return widget

    @classmethod
    def create_vector2d_widget(cls, value: QVector2D) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        x = QDoubleSpinBox()
        y = QDoubleSpinBox()
        layout.addWidget(QLabel("X:"))
        layout.addWidget(x)
        layout.addWidget(QLabel("Y:"))
        layout.addWidget(y)
        x.setValue(value.x())
        y.setValue(value.y())
        return widget

    @classmethod
    def create_vector3d_widget(cls, value: QVector3D) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        x = QDoubleSpinBox()
        y = QDoubleSpinBox()
        z = QDoubleSpinBox()
        layout.addWidget(QLabel("X:"))
        layout.addWidget(x)
        layout.addWidget(QLabel("Y:"))
        layout.addWidget(y)
        layout.addWidget(QLabel("Z:"))
        layout.addWidget(z)
        x.setValue(value.x())
        y.setValue(value.y())
        z.setValue(value.z())
        return widget

    @classmethod
    def create_vector4d_widget(cls, value: QVector4D) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        x = QDoubleSpinBox()
        y = QDoubleSpinBox()
        z = QDoubleSpinBox()
        w = QDoubleSpinBox()
        layout.addWidget(QLabel("X:"))
        layout.addWidget(x)
        layout.addWidget(QLabel("Y:"))
        layout.addWidget(y)
        layout.addWidget(QLabel("Z:"))
        layout.addWidget(z)
        layout.addWidget(QLabel("W:"))
        layout.addWidget(w)
        x.setValue(value.x())
        y.setValue(value.y())
        z.setValue(value.z())
        w.setValue(value.w())
        return widget

    @classmethod
    def create_quaternion_widget(cls, value: QQuaternion) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        scalar = QDoubleSpinBox()
        x = QDoubleSpinBox()
        y = QDoubleSpinBox()
        z = QDoubleSpinBox()
        layout.addWidget(QLabel("Scalar:"))
        layout.addWidget(scalar)
        layout.addWidget(QLabel("X:"))
        layout.addWidget(x)
        layout.addWidget(QLabel("Y:"))
        layout.addWidget(y)
        layout.addWidget(QLabel("Z:"))
        layout.addWidget(z)
        scalar.setValue(value.scalar())
        x.setValue(value.x())
        y.setValue(value.y())
        z.setValue(value.z())
        return widget

    @classmethod
    def format_qobject(cls, value: QObject) -> str:
        """Format a QObject as a string representation."""
        if isinstance(value, (QPoint, QPointF)):
            return f"({value.x()}, {value.y()})"
        if isinstance(value, (QSize, QSizeF)):
            return f"{value.width()}x{value.height()}"
        if isinstance(value, (QRect, QRectF)):
            return f"({value.x()}, {value.y()}, {value.width()}, {value.height()})"
        if isinstance(value, QColor):
            return value.name()
        if isinstance(value, QFont):
            return f"{value.family()}, {value.pointSize()}pt"
        if isinstance(value, QKeySequence):
            return value.toString()
        if isinstance(value, QDateTime):
            return value.toString(Qt.ISODate)
        if isinstance(value, QDate):
            return value.toString(Qt.ISODate)
        if isinstance(value, QTime):
            return value.toString(Qt.ISODate)
        if isinstance(value, QUrl):
            return value.toString()
        if isinstance(value, QUuid):
            return value.toString()
        if isinstance(value, QEasingCurve):
            return f"QEasingCurve({value.type().name})"
        if isinstance(value, (QLine, QLineF)):
            return f"({value.x1()}, {value.y1()}) to ({value.x2()}, {value.y2()})"
        if isinstance(value, QTextLength):
            return f"{value.value()} {value.type().name}"
        if isinstance(value, QLocale):
            return value.name()
        if isinstance(value, QSizePolicy):
            return f"h:{value.horizontalPolicy().name}, v:{value.verticalPolicy().name}"
        if isinstance(value, (QRegularExpression, QRegExp)):
            return value.pattern()
        if isinstance(value, QGradient):
            return f"QGradient({value.type().name})"
        if isinstance(value, QItemSelection):
            return f"QItemSelection({len(value)} ranges)"
        if isinstance(value, QItemSelectionRange):
            return f"({value.top()}, {value.left()}) to ({value.bottom()}, {value.right()})"
        if isinstance(value, QTextCursor):
            return f"pos:{value.position()}, anchor:{value.anchor()}"
        if isinstance(value, QTextCharFormat):
            return f"font:{value.font().family()}, color:{value.foreground().color().name()}"
        if isinstance(value, QTextBlockFormat):
            return f"alignment:{value.alignment().name}"
        if isinstance(value, QTextListFormat):
            return f"style:{value.style()}"
        if isinstance(value, QTextFrameFormat):
            return f"margin:{value.margin()}"
        if isinstance(value, QTextTableFormat):
            return f"columns:{value.columns()}"
        if isinstance(value, QTextImageFormat):
            return f"name:{value.name()}"
        if isinstance(value, QTextTableCellFormat):
            return f"row:{value.topPadding()}, col:{value.leftPadding()}"
        if isinstance(value, QTextDocumentFragment):
            return value.toPlainText()[:50] + "..." if len(value.toPlainText()) > 50 else value.toPlainText()
        if isinstance(value, QTextOption):
            return f"alignment:{value.alignment().name}"
        if isinstance(value, QTextLayout):
            return value.text()[:50] + "..." if len(value.text()) > 50 else value.text()
        if isinstance(value, QTextLine):
            return f"line:{value.lineNumber()}, length:{value.textLength()}"
        if isinstance(value, QTextBlock):
            return value.text()[:50] + "..." if len(value.text()) > 50 else value.text()
        if isinstance(value, QTextFragment):
            return value.text()[:50] + "..." if len(value.text()) > 50 else value.text()
        if isinstance(value, QTextFrame):
            return f"firstPosition:{value.firstPosition()}, lastPosition:{value.lastPosition()}"
        if isinstance(value, QTextTable):
            return f"rows:{value.rows()}, columns:{value.columns()}"
        if isinstance(value, QTextList):
            return f"count:{value.count()}"
        if isinstance(value, QTextTableCell):
            return f"row:{value.row()}, column:{value.column()}"
        if isinstance(value, QTextDocument):
            return value.toPlainText()[:50] + "..." if len(value.toPlainText()) > 50 else value.toPlainText()
        if isinstance(value, QVector2D):
            return f"({value.x()}, {value.y()})"
        if isinstance(value, QVector3D):
            return f"({value.x()}, {value.y()}, {value.z()})"
        if isinstance(value, QVector4D):
            return f"({value.x()}, {value.y()}, {value.z()}, {value.w()})"
        if isinstance(value, QQuaternion):
            return f"({value.scalar()}, {value.x()}, {value.y()}, {value.z()})"
        if isinstance(value, QMatrix4x4):
            return f"[{', '.join([str(value.column(i)) for i in range(4)])}]"
        if isinstance(value, QTransform):
            return f"m11:{value.m11()}, m12:{value.m12()}, m13:{value.m13()}, m21:{value.m21()}, m22:{value.m22()}, m23:{value.m23()}, m31:{value.m31()}, m32:{value.m32()}, m33:{value.m33()}"
        if isinstance(value, QPolygon):
            return f"[{', '.join([str(value.point(i)) for i in range(value.count())])}]"
        if isinstance(value, QPolygonF):
            return f"[{', '.join([str(value.point(i)) for i in range(value.count())])}]"
        if isinstance(value, QRegion):
            return f"boundingRect: {value.boundingRect()}"
        if isinstance(value, QBitArray):
            return value.toBitString()
        if isinstance(value, QByteArray):
            return value.toHex().data().decode()
        if isinstance(value, QMargins):
            return f"({value.left()}, {value.top()}, {value.right()}, {value.bottom()})"
        if isinstance(value, QPixmap):
            return f"QPixmap({value.width()}x{value.height()})"
        if isinstance(value, QImage):
            return f"QImage({value.width()}x{value.height()}, format:{value.format().name})"
        if isinstance(value, QBitmap):
            return f"QBitmap({value.width()}x{value.height()})"
        if isinstance(value, QBrush):
            return f"QBrush(style:{value.style().name}, color:{value.color().name()})"
        if isinstance(value, QPen):
            return f"QPen(style:{value.style().name}, width:{value.width()}, color:{value.color().name()})"
        if isinstance(value, QCursor):
            return f"QCursor(shape:{value.shape().name})"
        return str(value)

    @classmethod
    def parse_qobject(cls, value_str: str, param_type: type) -> QObject:
        """Parse a string representation into a QObject."""
        if param_type in (QPoint, QPointF):
            x, y = map(float, value_str.strip("()").split(","))
            return param_type(x, y)
        if param_type in (QSize, QSizeF):
            width, height = map(float, value_str.split("x"))
            return param_type(width, height)
        if param_type in (QRect, QRectF):
            x, y, width, height = map(float, value_str.strip("()").split(","))
            return param_type(x, y, width, height)
        if param_type == QColor:
            return QColor(value_str)
        if param_type == QFont:
            family, size = value_str.rsplit(",", 1)
            return QFont(family.strip(), int(size.strip("pt")))
        if param_type == QKeySequence:
            return QKeySequence(value_str)
        if param_type == QDateTime:
            return QDateTime.fromString(value_str, Qt.ISODate)
        if param_type == QDate:
            return QDate.fromString(value_str, Qt.ISODate)
        if param_type == QTime:
            return QTime.fromString(value_str, Qt.ISODate)
        if param_type == QUrl:
            return QUrl(value_str)
        if param_type == QUuid:
            return QUuid(value_str)
        if param_type == QEasingCurve:
            curve_type = QEasingCurve.Type[value_str.split("(")[1].split(")")[0]]
            return QEasingCurve(curve_type)
        if param_type in (QLine, QLineF):
            x1, y1, x2, y2 = map(float, value_str.replace("to", ",").strip("()").split(","))
            return param_type(x1, y1, x2, y2)
        if param_type == QTextLength:
            value, type_name = value_str.split()
            return QTextLength(QTextLength.Type[type_name], float(value))
        if param_type == QLocale:
            return QLocale(value_str)
        if param_type == QSizePolicy:
            h, v = value_str.split(",")
            return QSizePolicy(QSizePolicy.Policy[h.split(":")[1]], QSizePolicy.Policy[v.split(":")[1]])
        if param_type in (QRegularExpression, QRegExp):
            return param_type(value_str)
        if param_type == QGradient:
            gradient_type = QGradient.Type[value_str.split("(")[1].split(")")[0]]
            return QGradient(gradient_type)
        if param_type == QItemSelection:
            # This is a simplified representation, actual parsing would be more complex
            return QItemSelection()
        if param_type == QItemSelectionRange:
            top, left, bottom, right = map(int, value_str.replace("to", ",").strip("()").split(","))
            return QItemSelectionRange(QItemSelection.fromSelection(QItemSelection(top, left, bottom, right)))
        if param_type == QTextCursor:
            pos, anchor = map(int, value_str.replace("pos:", "").replace("anchor:", "").split(","))
            cursor = QTextCursor()
            cursor.set_position(pos)
            cursor.set_position(anchor, QTextCursor.KeepAnchor)
            return cursor
        if param_type == QTextCharFormat:
            font_family, color = value_str.split(",")
            fmt = QTextCharFormat()
            fmt.setFont(QFont(font_family.split(":")[1]))
            fmt.setForeground(QColor(color.split(":")[1]))
            return fmt
        if param_type == QTextBlockFormat:
            alignment = Qt.AlignmentFlag[value_str.split(":")[1]]
            fmt = QTextBlockFormat()
            fmt.setAlignment(alignment)
            return fmt
        if param_type == QTextListFormat:
            style = int(value_str.split(":")[1])
            fmt = QTextListFormat()
            fmt.setStyle(style)
            return fmt
        if param_type == QTextFrameFormat:
            margin = float(value_str.split(":")[1])
            fmt = QTextFrameFormat()
            fmt.setMargin(margin)
            return fmt
        if param_type == QTextTableFormat:
            columns = int(value_str.split(":")[1])
            fmt = QTextTableFormat()
            fmt.setColumns(columns)
            return fmt
        if param_type == QTextImageFormat:
            name = value_str.split(":")[1]
            fmt = QTextImageFormat()
            fmt.setName(name)
            return fmt
        if param_type == QTextTableCellFormat:
            top, left = map(float, value_str.replace("row:", "").replace("col:", "").split(","))
            fmt = QTextTableCellFormat()
            fmt.setTopPadding(top)
            fmt.setLeftPadding(left)
            return fmt
        if param_type == QTextDocumentFragment:
            return QTextDocumentFragment.fromPlainText(value_str.split("...")[0])
        if param_type == QTextOption:
            alignment = Qt.AlignmentFlag[value_str.split(":")[1]]
            option = QTextOption()
            option.setAlignment(alignment)
            return option
        if param_type == QTextLayout:
            return QTextLayout(value_str.split("...")[0])
        if param_type == QTextLine:
            # This is a simplified representation, actual parsing would be more complex
            return QTextLine()
        if param_type == QTextBlock:
            # This is a simplified representation, actual parsing would be more complex
            return QTextBlock()
        if param_type == QTextFragment:
            # This is a simplified representation, actual parsing would be more complex
            return QTextFragment()
        if param_type == QTextFrame:
            # This is a simplified representation, actual parsing would be more complex
            return QTextFrame()
        if param_type == QTextTable:
            rows, columns = map(int, value_str.replace("rows:", "").replace("columns:", "").split(","))
            table = QTextTable(QTextDocument())
            table.resize(rows, columns)
            return table
        if param_type == QTextList:
            # This is a simplified representation, actual parsing would be more complex
            return QTextList(QTextDocument())
        if param_type == QTextTableCell:
            row, column = map(int, value_str.replace("row:", "").replace("column:", "").split(","))
            # This is a simplified representation, actual parsing would be more complex
            return QTextTableCell()
        if param_type == QTextDocument:
            doc = QTextDocument()
            doc.setPlainText(value_str.split("...")[0])
            return doc
        if param_type == QVector2D:
            x, y = map(float, value_str.strip("()").split(","))
            return QVector2D(x, y)
        if param_type == QVector3D:
            x, y, z = map(float, value_str.strip("()").split(","))
            return QVector3D(x, y, z)
        if param_type == QVector4D:
            x, y, z, w = map(float, value_str.strip("()").split(","))
            return QVector4D(x, y, z, w)
        if param_type == QQuaternion:
            scalar, x, y, z = map(float, value_str.strip("()").split(","))
            return QQuaternion(scalar, x, y, z)
        if param_type == QMatrix4x4:
            values = [float(x.strip("[]")) for x in value_str.split(",")]
            return QMatrix4x4(*values)
        if param_type == QTransform:
            values = [float(x.split(":")[1]) for x in value_str.split(",")]
            return QTransform(*values)
        if param_type == QPolygon:
            points = [QPoint(*map(int, p.strip("()").split(","))) for p in value_str.strip("[]").split(",")]
            return QPolygon(points)
        if param_type == QPolygonF:
            points = [QPointF(*map(float, p.strip("()").split(","))) for p in value_str.strip("[]").split(",")]
            return QPolygonF(points)
        if param_type == QRegion:
            x, y, width, height = map(int, value_str.split(":")[1].strip("()").split(","))
            return QRegion(x, y, width, height)
        if param_type == QBitArray:
            return QBitArray.fromBitString(value_str)
        if param_type == QByteArray:
            return QByteArray.fromHex(value_str.encode())
        if param_type == QMargins:
            left, top, right, bottom = map(int, value_str.strip("()").split(","))
            return QMargins(left, top, right, bottom)
        if param_type == QPixmap:
            width, height = map(int, value_str.split("(")[1].split(")")[0].split("x"))
            return QPixmap(width, height)
        if param_type == QImage:
            width, height = map(int, value_str.split("(")[1].split(")")[0].split("x"))
            format_name = value_str.split("format:")[1].strip()
            return QImage(width, height, getattr(QImage, format_name))
        if param_type == QBitmap:
            width, height = map(int, value_str.split("(")[1].split(")")[0].split("x"))
            return QBitmap(width, height)
        if param_type == QBrush:
            style, color = value_str.split(",")
            return QBrush(QColor(color.split(":")[1]), getattr(Qt, style.split(":")[1]))
        if param_type == QPen:
            style, width, color = value_str.split(",")
            return QPen(QColor(color.split(":")[1]), float(width.split(":")[1]), getattr(Qt, style.split(":")[1]))
        if param_type == QCursor:
            shape = getattr(Qt, value_str.split(":")[1])
            return QCursor(shape)
        raise ValueError(f"Unsupported QObject type: {param_type}")

    @classmethod
    def get_qobject_value(cls, widget: QWidget, param_type: type) -> QObject:
        """Get the QObject value from a widget."""
        if isinstance(widget, QLineEdit):
            return cls.parse_qobject(widget.text(), param_type)
        if isinstance(widget, QSpinBox):
            return param_type(widget.value())
        if isinstance(widget, QDoubleSpinBox):
            return param_type(widget.value())
        if isinstance(widget, QComboBox):
            return cls.parse_qobject(widget.currentText(), param_type)
        if isinstance(widget, QCheckBox):
            return param_type(widget.isChecked())
        if isinstance(widget, QDateTimeEdit):
            return widget.dateTime()
        if isinstance(widget, QDateEdit):
            return widget.date()
        if isinstance(widget, QTimeEdit):
            return widget.time()
        if isinstance(widget, QPushButton):
            if param_type == QColor:
                return QColor(widget.styleSheet().split(":")[1].strip(";"))
            if param_type == QFont:
                return widget.font()
            return widget.text()
        if isinstance(widget, QFontComboBox):
            return widget.currentFont()
        if isinstance(widget, QSlider):
            return param_type(widget.value())
        if isinstance(widget, QDial):
            return param_type(widget.value())
        if isinstance(widget, QTextEdit):
            if param_type == QTextDocument:
                return widget.document()
            return cls.parse_qobject(widget.toPlainText(), param_type)
        if isinstance(widget, QPlainTextEdit):
            if param_type == QTextDocument:
                return widget.document()
            return cls.parse_qobject(widget.toPlainText(), param_type)
        if isinstance(widget, QLabel):
            if param_type == QPixmap:
                return widget.pixmap()
            if param_type == QMovie:
                return widget.movie()
            return cls.parse_qobject(widget.text(), param_type)
        if isinstance(widget, QProgressBar):
            return param_type(widget.value())
        if isinstance(widget, QLCDNumber):
            return param_type(widget.value())
        if isinstance(widget, QGroupBox):
            return param_type(widget.isChecked())
        if isinstance(widget, QRadioButton):
            return param_type(widget.isChecked())
        if isinstance(widget, QToolButton):
            if param_type == QIcon:
                return widget.icon()
            return cls.parse_qobject(widget.text(), param_type)
        if isinstance(widget, QTabWidget):
            return param_type(widget.currentIndex())
        if isinstance(widget, QListWidget):
            if param_type == QListWidgetItem:
                return widget.currentItem()
            return cls.parse_qobject(widget.currentItem().text(), param_type)
        if isinstance(widget, QTreeWidget):
            if param_type == QTreeWidgetItem:
                return widget.currentItem()
            return cls.parse_qobject(widget.currentItem().text(0), param_type)
        if isinstance(widget, QTableWidget):
            if param_type == QTableWidgetItem:
                return widget.currentItem()
            return cls.parse_qobject(widget.currentItem().text(), param_type)
        if isinstance(widget, QCalendarWidget):
            return widget.selectedDate()
        if isinstance(widget, QKeySequenceEdit):
            return widget.keySequence()
        raise ValueError(f"Unsupported widget type for QObject: {type(widget)}")

    @classmethod
    def create_qobject_widget(cls, value: QObject) -> QWidget:
        """Create a widget to edit a QObject value."""
        if isinstance(value, (QPoint, QPointF)):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            x = QDoubleSpinBox()
            y = QDoubleSpinBox()
            x.setRange(-1000000, 1000000)
            y.setRange(-1000000, 1000000)
            x.setValue(value.x())
            y.setValue(value.y())
            layout.addWidget(QLabel("X:"))
            layout.addWidget(x)
            layout.addWidget(QLabel("Y:"))
            layout.addWidget(y)
            return widget
        if isinstance(value, (QSize, QSizeF)):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            width = QDoubleSpinBox()
            height = QDoubleSpinBox()
            width.setRange(0, 1000000)
            height.setRange(0, 1000000)
            width.setValue(value.width())
            height.setValue(value.height())
            layout.addWidget(QLabel("Width:"))
            layout.addWidget(width)
            layout.addWidget(QLabel("Height:"))
            layout.addWidget(height)
            return widget
        if isinstance(value, (QRect, QRectF)):
            widget = QWidget()
            layout = QGridLayout(widget)
            x = QDoubleSpinBox()
            y = QDoubleSpinBox()
            width = QDoubleSpinBox()
            height = QDoubleSpinBox()
            x.setRange(-1000000, 1000000)
            y.setRange(-1000000, 1000000)
            width.setRange(0, 1000000)
            height.setRange(0, 1000000)
            x.setValue(value.x())
            y.setValue(value.y())
            width.setValue(value.width())
            height.setValue(value.height())
            layout.addWidget(QLabel("X:"), 0, 0)
            layout.addWidget(x, 0, 1)
            layout.addWidget(QLabel("Y:"), 0, 2)
            layout.addWidget(y, 0, 3)
            layout.addWidget(QLabel("Width:"), 1, 0)
            layout.addWidget(width, 1, 1)
            layout.addWidget(QLabel("Height:"), 1, 2)
            layout.addWidget(height, 1, 3)
            return widget
        if isinstance(value, QColor):
            button = QPushButton(value.name())
            button.setStyleSheet(f"background-color: {value.name()};")
            button.clicked.connect(lambda: cls.update_color_button(button))
            return button
        if isinstance(value, QFont):
            button = QPushButton(value.family())
            button.setFont(value)
            button.clicked.connect(lambda: cls.update_font_button(button))
            return button
        if isinstance(value, QKeySequence):
            return QKeySequenceEdit(value)
        if isinstance(value, QDateTime):
            return QDateTimeEdit(value)
        if isinstance(value, QDate):
            return QDateEdit(value)
        if isinstance(value, QTime):
            return QTimeEdit(value)
        if isinstance(value, QUrl):
            return QLineEdit(value.toString())
        if isinstance(value, QUuid):
            return QLineEdit(value.toString())
        if isinstance(value, QEasingCurve):
            combo = QComboBox()
            for curve_type in QEasingCurve.Type:
                combo.addItem(curve_type.name, curve_type)
            combo.setCurrentIndex(combo.findData(value.type()))
            return combo
        if isinstance(value, (QLine, QLineF)):
            widget = QWidget()
            layout = QGridLayout(widget)
            x1 = QDoubleSpinBox()
            y1 = QDoubleSpinBox()
            x2 = QDoubleSpinBox()
            y2 = QDoubleSpinBox()
            x1.setRange(-1000000, 1000000)
            y1.setRange(-1000000, 1000000)
            x2.setRange(-1000000, 1000000)
            y2.setRange(-1000000, 1000000)
            x1.setValue(value.x1())
            y1.setValue(value.y1())
            x2.setValue(value.x2())
            y2.setValue(value.y2())
            layout.addWidget(QLabel("X1:"), 0, 0)
            layout.addWidget(x1, 0, 1)
            layout.addWidget(QLabel("Y1:"), 0, 2)
            layout.addWidget(y1, 0, 3)
            layout.addWidget(QLabel("X2:"), 1, 0)
            layout.addWidget(x2, 1, 1)
            layout.addWidget(QLabel("Y2:"), 1, 2)
            layout.addWidget(y2, 1, 3)
            return widget
        if isinstance(value, QTextLength):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            value_spin = QDoubleSpinBox()
            type_combo = QComboBox()
            value_spin.setValue(value.value())
            for length_type in QTextLength.Type:
                type_combo.addItem(length_type.name, length_type)
            type_combo.setCurrentIndex(type_combo.findData(value.type()))
            layout.addWidget(value_spin)
            layout.addWidget(type_combo)
            return widget
        if isinstance(value, QLocale):
            return QLineEdit(value.name())
        if isinstance(value, QSizePolicy):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            h_combo = QComboBox()
            v_combo = QComboBox()
            for policy in QSizePolicy.Policy:
                h_combo.addItem(policy.name, policy)
                v_combo.addItem(policy.name, policy)
            h_combo.setCurrentIndex(h_combo.findData(value.horizontalPolicy()))
            v_combo.setCurrentIndex(v_combo.findData(value.verticalPolicy()))
            layout.addWidget(QLabel("Horizontal:"))
            layout.addWidget(h_combo)
            layout.addWidget(QLabel("Vertical:"))
            layout.addWidget(v_combo)
            return widget
        if isinstance(value, (QRegularExpression, QRegExp)):
            return QLineEdit(value.pattern())
        if isinstance(value, QGradient):
            combo = QComboBox()
            for gradient_type in QGradient.Type:
                combo.addItem(gradient_type.name, gradient_type)
            combo.setCurrentIndex(combo.findData(value.type()))
            return combo
        if isinstance(value, QItemSelection):
            return QLineEdit(str(len(value)) + " ranges")
        if isinstance(value, QItemSelectionRange):
            widget = QWidget()
            layout = QGridLayout(widget)
            top = QSpinBox()
            left = QSpinBox()
            bottom = QSpinBox()
            right = QSpinBox()
            top.setValue(value.top())
            left.setValue(value.left())
            bottom.setValue(value.bottom())
            right.setValue(value.right())
            layout.addWidget(QLabel("Top:"), 0, 0)
            layout.addWidget(top, 0, 1)
            layout.addWidget(QLabel("Left:"), 0, 2)
            layout.addWidget(left, 0, 3)
            layout.addWidget(QLabel("Bottom:"), 1, 0)
            layout.addWidget(bottom, 1, 1)
            layout.addWidget(QLabel("Right:"), 1, 2)
            layout.addWidget(right, 1, 3)
            return widget
        if isinstance(value, QTextCursor):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            position = QSpinBox()
            anchor = QSpinBox()
            position.setValue(value.position())
            anchor.setValue(value.anchor())
            layout.addWidget(QLabel("Position:"))
            layout.addWidget(position)
            layout.addWidget(QLabel("Anchor:"))
            layout.addWidget(anchor)
            return widget
        if isinstance(value, QTextCharFormat):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            font_button = QPushButton(value.font().family())
            font_button.setFont(value.font())
            font_button.clicked.connect(lambda: cls.update_font_button(font_button))
            color_button = QPushButton(value.foreground().color().name())
            color_button.setStyleSheet(f"background-color: {value.foreground().color().name()};")
            color_button.clicked.connect(lambda: cls.update_color_button(color_button))
            layout.addWidget(font_button)
            layout.addWidget(color_button)
            return widget
        if isinstance(value, QTextListFormat):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            style_combo = QComboBox()
            for style in QTextListFormat.Style:
                style_combo.addItem(style.name, style)
            style_combo.setCurrentIndex(style_combo.findData(value.style()))
            layout.addWidget(QLabel("Style:"))
            layout.addWidget(style_combo)
            layout.addWidget(QLabel("Indent:"))
            layout.addWidget(QSpinBox())
            return widget
        if isinstance(value, QTextTableFormat):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            columns = QSpinBox()
            rows = QSpinBox()
            columns.setValue(value.columns())
            rows.setValue(value.rows())
            layout.addWidget(QLabel("Columns:"))
            layout.addWidget(columns)
            layout.addWidget(QLabel("Rows:"))
            layout.addWidget(rows)
            return widget
        if isinstance(value, QTextImageFormat):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            width = QSpinBox()
            height = QSpinBox()
            width.setValue(value.width())
            height.setValue(value.height())
            layout.addWidget(QLabel("Width:"))
            layout.addWidget(width)
            layout.addWidget(QLabel("Height:"))
            layout.addWidget(height)
            return widget
        if isinstance(value, QTextDocumentFragment):
            return QTextEdit(value.toPlainText())
        if isinstance(value, QTextLayout):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            text = QTextEdit()
            text.setPlainText(value.text())
            layout.addWidget(text)
            return widget
        if isinstance(value, QTextLine):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            position = QSpinBox()
            height = QSpinBox()
            position.setValue(value.textStartPosition())
            height.setValue(value.height())
            layout.addWidget(QLabel("Position:"))
            layout.addWidget(position)
            layout.addWidget(QLabel("Height:"))
            layout.addWidget(height)
            return widget
        if isinstance(value, QTextBlock):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            text = QTextEdit()
            text.setPlainText(value.text())
            layout.addWidget(text)
            return widget
        if isinstance(value, QTextFragment):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            text = QTextEdit()
            text.setPlainText(value.text())
            layout.addWidget(text)
            return widget
        if isinstance(value, QTextFrame):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            text = QTextEdit()
            text.setPlainText(value.text())
            layout.addWidget(text)
            return widget
        if isinstance(value, QTextTable):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            text = QTextEdit()
            text.setPlainText(value.text())
            layout.addWidget(text)
            return widget
        return value

    # Value-specific getter methods
    @staticmethod
    def get_spin_value(w: QSpinBox | QDoubleSpinBox) -> float:
        return w.value()

    @staticmethod
    def get_checkbox_value(w: QCheckBox) -> bool:
        return w.isChecked()

    @staticmethod
    def get_combobox_value(w: QComboBox, param_type: type) -> enum.Enum:
        return param_type.__members__[w.currentText()]

    @staticmethod
    def get_datetime_value(w: QDateTimeEdit) -> datetime:
        return w.dateTime().toPyDateTime()

    @staticmethod
    def get_date_value(w: QDateEdit) -> date:
        return w.date().toPyDate()

    @staticmethod
    def get_time_value(w: QTimeEdit) -> time:
        return w.time().toPyTime()

    @classmethod
    def get_lineedit_value(cls, w: QLineEdit, param_type: type):  # noqa: ANN206
        return param_type(w.text())

    @staticmethod
    def get_button_value(button: QPushButton, param_type: type) -> Any:
        if param_type == QColor:
            return QColor(button.styleSheet().split(":")[1].strip(";"))
        if param_type == QFont:
            return QFont(button.text())
        raise ValueError(f"Unsupported button param type: {param_type}")

    @classmethod
    def get_widget_value(cls, widget: QWidget, param_type: type) -> Any:
        if param_type in (QSize, QSizeF):
            return cls.get_size_value(widget, param_type)
        if param_type in (QPoint, QPointF):
            return cls.get_point_value(widget, param_type)
        if param_type in (QRect, QRectF):
            return cls.get_rect_value(widget, param_type)
        if param_type == QMargins:
            return cls.get_margins_value(widget)
        raise ValueError(f"Unsupported widget param type: {param_type}")

    @staticmethod
    def get_size_value(widget: QWidget, param_type: type) -> QSize | QSizeF:
        width, height = widget.findChildren((QSpinBox, QDoubleSpinBox))
        assert isinstance(width, (QSpinBox, QDoubleSpinBox))
        assert isinstance(height, (QSpinBox, QDoubleSpinBox))
        return param_type(width.value(), height.value())

    @staticmethod
    def get_point_value(widget: QWidget, param_type: type) -> QPoint | QPointF:
        x, y = widget.findChildren((QSpinBox, QDoubleSpinBox))
        assert isinstance(x, (QSpinBox, QDoubleSpinBox))
        assert isinstance(y, (QSpinBox, QDoubleSpinBox))
        return param_type(x.value(), y.value())

    @staticmethod
    def get_rect_value(widget: QWidget, param_type: type) -> QRect | QRectF:
        x, y, width, height = widget.findChildren((QSpinBox, QDoubleSpinBox))
        assert isinstance(x, (QSpinBox, QDoubleSpinBox))
        assert isinstance(y, (QSpinBox, QDoubleSpinBox))
        assert isinstance(width, (QSpinBox, QDoubleSpinBox))
        assert isinstance(height, (QSpinBox, QDoubleSpinBox))
        return param_type(x.value(), y.value(), width.value(), height.value())

    @staticmethod
    def get_margins_value(widget: QWidget) -> tuple[int, int, int, int]:
        left, top, right, bottom = widget.findChildren(QSpinBox)
        assert isinstance(left, QSpinBox)
        assert isinstance(top, QSpinBox)
        assert isinstance(right, QSpinBox)
        assert isinstance(bottom, QSpinBox)
        return tuple(left.value(), top.value(), right.value(), bottom.value())

    @classmethod
    def get_new_value(cls, input_widget: QWidget, param_type: type) -> Any:
        value_getters = {
            (QSpinBox, QDoubleSpinBox): cls.get_spin_value,
            QCheckBox: cls.get_checkbox_value,
            QComboBox: lambda w: cls.get_combobox_value(w, param_type),
            QDateTimeEdit: cls.get_datetime_value,
            QDateEdit: cls.get_date_value,
            QTimeEdit: cls.get_time_value,
            QLineEdit: lambda w: cls.get_lineedit_value(w, param_type),
            QPushButton: lambda w: cls.get_button_value(w, param_type),
            QWidget: lambda w: cls.get_widget_value(w, param_type),
            QMargins: cls.get_margins_value,
            QSize: cls.get_size_value,
            QSizeF: cls.get_size_value,
            QPoint: cls.get_point_value,
            QPointF: cls.get_point_value,
            QRect: cls.get_rect_value,
            QRectF: cls.get_rect_value,
            QPixmap: cls.format_qobject,
            QImage: cls.format_qobject,
            QBitmap: cls.format_qobject,
            QBrush: cls.update_brush_button,
            QPen: cls.update_pen_color,
            QCursor: cls.get_point_value,
            QKeySequence: cls.format_qobject,
            QTransform: cls.format_qobject,
            # QMatrix: cls.matri,
            QMatrix4x4: cls.format_qobject,
            QVector2D: cls.format_qobject,
            QVector3D: cls.format_qobject,
            QVector4D: cls.format_qobject,
            QQuaternion: cls.format_qobject,
            QPolygon: cls.format_qobject,
            QPolygonF: cls.format_qobject,
            QRegion: cls.format_qobject,
            QBitArray: cls.format_qobject,
            QByteArray: cls.format_qobject,
            # QJsonArray: cls.format_qobject,
            QDate: cls.get_date_value,
            QTime: cls.get_time_value,
            QDateTime: cls.get_datetime_value,
            QUrl: cls.format_qobject,
            QUuid: cls.format_qobject,
            QEasingCurve: cls.format_qobject,
            QLine: cls.format_qobject,
            QLineF: cls.format_qobject,
            QTextLength: cls.format_qobject,
            QTextFormat: cls.format_qobject,
            QLocale: cls.format_qobject,
            QSizePolicy: cls.format_qobject,
            QRegularExpression if qtpy.QT6 else QRegExp: cls.format_qobject,
            QGradient: cls.format_qobject,
            QItemSelection: cls.format_qobject,
            QItemSelectionRange: cls.format_qobject,
            QTextCursor: cls.format_qobject,
            QTextCharFormat: cls.format_qobject,
            QTextBlockFormat: cls.format_qobject,
            QTextListFormat: cls.format_qobject,
            QTextFrameFormat: cls.format_qobject,
            QTextTableFormat: cls.format_qobject,
            QTextImageFormat: cls.format_qobject,
            QTextTableCellFormat: cls.format_qobject,
            QTextDocumentFragment: cls.format_qobject,
            QTextOption: cls.format_qobject,
            QTextLayout: cls.format_qobject,
            QTextLine: cls.format_qobject,
            QTextBlock: cls.format_qobject,
            QTextFragment: cls.format_qobject,
            QTextFrame: cls.format_qobject,
            QTextTable: cls.format_qobject,
            QTextList: cls.format_qobject,
            QTextTableCell: cls.format_qobject,
            QTextDocument: cls.format_qobject,
        }

        for widget_types, getter in value_getters.items():
            if isinstance(input_widget, widget_types):
                return getter(input_widget)

        raise ValueError(f"Unsupported input widget type: {type(input_widget)}")
