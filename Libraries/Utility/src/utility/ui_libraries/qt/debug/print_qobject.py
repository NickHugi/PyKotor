from __future__ import annotations

import inspect
import os

from functools import wraps
from typing import Any, Callable, Type, TypeVar, cast

import qtpy

from qtpy import QtCore
from qtpy.QtCore import (
    QAbstractItemModel,
    QAbstractListModel,
    QAbstractTableModel,
    QByteArray,
    QDate,
    QDateTime,
    QDir,
    QEvent,
    QFile,
    QFileInfo,
    QItemSelection,
    QItemSelectionModel,
    QItemSelectionRange,
    QJsonDocument,
    QJsonValue,
    QLineF,
    QLocale,
    QMimeData,
    QModelIndex,
    QObject,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    QSizeF,
    QSortFilterProxyModel,
    QTime,
    QTimer,
    QUrl,
    QUuid,
    QVariant,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import (
    QAbstractTextDocumentLayout,
    QBitmap,
    QBrush,
    QClipboard,
    QColor,
    QConicalGradient,
    QCursor,
    QDoubleValidator,
    QDragEnterEvent,
    QDropEvent,
    QFocusEvent,
    QFont,
    QGradient,
    QGuiApplication,
    QIcon,
    QImage,
    QIntValidator,
    QKeyEvent,
    QKeySequence,
    QLinearGradient,
    QMatrix4x4,
    QMouseEvent,
    QOpenGLBuffer,
    QOpenGLContext,
    QOpenGLDebugLogger,
    QOpenGLFramebufferObject,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLTexture,
    QOpenGLTimerQuery,
    QOpenGLVersionProfile,
    QOpenGLVertexArrayObject,
    QPagedPaintDevice,
    QPainter,
    QPainterPath,
    QPalette,
    QPdfWriter,
    QPen,
    QPixmap,
    QPolygon,
    QPolygonF,
    QQuaternion,
    QRadialGradient,
    QRawFont,
    QRegion,
    QResizeEvent,
    QStaticText,
    QSyntaxHighlighter,
    QTextBlock,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
    QTextFragment,
    QTextFrameFormat,
    QTextImageFormat,
    QTextItem,
    QTextLayout,
    QTextLength,
    QTextLine,
    QTextListFormat,
    QTextObjectInterface,
    QTextOption,
    QTextTableFormat,
    QTransform,
    QValidator,
    QVector2D,
    QVector3D,
    QVector4D,
    QWheelEvent,
)
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDockWidget,
    QDoubleSpinBox,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTabWidget,
    QTableView,
    QTextEdit,
    QTimeEdit,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

if qtpy.QT5:
    from qtpy.QtGui import QRegExpValidator, QTouchDevice
elif qtpy.QT6:
    from qtpy.QtGui import QRegularExpressionValidator
else:
    raise ImportError(f"Unsupported Qt version: {qtpy.QT_API}")

def repr_qt_enum(enum: QObject, members: dict[str, Any] | None = None) -> str:
    if members is None:
        if not hasattr(enum.__class__, "__members__"):
            raise ValueError(f"Enum '{enum.__class__.__name__}' has no members")
        members = enum.__class__.__members__  # pyright: ignore[reportAttributeAccessIssue]
    if not members:
        return repr(enum)
    active_flags = [
        name
        for name, value in members.items()  # pyright: ignore[reportAttributeAccessIssue]
        if enum & value
    ]
    if not active_flags:
        return f"{enum.__class__.__name__}.NONE"
    return f"{' | '.join(f'{enum.__class__.__name__}.{flag}' for flag in active_flags)}"


def format_qt_obj(arg: Any) -> str:  # noqa: PLR0911
    format_dict = {
        # Common Qt objects
        QSize: lambda x: f"QSize(width={cast(QSize, x).width()}, height={cast(QSize, x).height()})",
        QPoint: lambda x: f"QPoint(x={cast(QPoint, x).x()}, y={cast(QPoint, x).y()})",
        QRect: lambda x: f"QRect(x={cast(QRect, x).x()}, y={cast(QRect, x).y()}, width={cast(QRect, x).width()}, height={cast(QRect, x).height()})",
        QColor: lambda x: f"QColor(red={cast(QColor, x).red()}, green={cast(QColor, x).green()}, blue={cast(QColor, x).blue()}, alpha={cast(QColor, x).alpha()})",
        QFont: lambda x: f"QFont(family='{cast(QFont, x).family()}', pointSize={cast(QFont, x).pointSize()})",
        QIcon: lambda x: f"QIcon(availableSizes={cast(QIcon, x).availableSizes()})",
        QPixmap: lambda x: f"QPixmap(width={cast(QPixmap, x).width()}, height={cast(QPixmap, x).height()})",
        QAction: lambda x: f"QAction(text='{cast(QAction, x).text()}', checkable={cast(QAction, x).isCheckable()}, checked={cast(QAction, x).isChecked()})",
        QToolBar: lambda x: f"QToolBar(windowTitle='{cast(QToolBar, x).windowTitle()}', orientation={cast(QToolBar, x).orientation()})",
        QMenu: lambda x: f"QMenu(title='{cast(QMenu, x).title()}', actions={len(cast(QMenu, x).actions())})",
        Qt.ToolBarArea: lambda x: f"ToolBarArea({repr_qt_enum(x)})",
        **({Qt.ToolBarAreas: lambda x: f"ToolBarAreas({repr_qt_enum(x, {'Left': Qt.ToolBarArea.LeftToolBarArea, 'Right': Qt.ToolBarArea.RightToolBarArea, 'Top': Qt.ToolBarArea.TopToolBarArea, 'Bottom': Qt.ToolBarArea.BottomToolBarArea})})"} if qtpy.QT5 else {}),
        # Widgets
        QPushButton: lambda x: f"QPushButton(text='{cast(QPushButton, x).text()}')",
        QLineEdit: lambda x: f"QLineEdit(text='{cast(QLineEdit, x).text()}')",
        QTextEdit: lambda x: f"QTextEdit(plainText='{cast(QTextEdit, x).toPlainText()[:20]}...')",
        QCheckBox: lambda x: f"QCheckBox(text='{cast(QCheckBox, x).text()}', checked={cast(QCheckBox, x).isChecked()})",
        QRadioButton: lambda x: f"QRadioButton(text='{cast(QRadioButton, x).text()}', checked={cast(QRadioButton, x).isChecked()})",
        QComboBox: lambda x: f"QComboBox(currentText='{cast(QComboBox, x).currentText()}')",
        QSpinBox: lambda x: f"QSpinBox(value={cast(QSpinBox, x).value()})",
        QDoubleSpinBox: lambda x: f"QDoubleSpinBox(value={cast(QDoubleSpinBox, x).value()})",
        QSlider: lambda x: f"QSlider(value={cast(QSlider, x).value()}, orientation={cast(QSlider, x).orientation()})",
        QProgressBar: lambda x: f"QProgressBar(value={cast(QProgressBar, x).value()})",
        QDateEdit: lambda x: f"QDateEdit(date={cast(QDateEdit, x).date().toString()})",
        QTimeEdit: lambda x: f"QTimeEdit(time={cast(QTimeEdit, x).time().toString()})",
        QDateTimeEdit: lambda x: f"QDateTimeEdit(dateTime={cast(QDateTimeEdit, x).dateTime().toString()})",
        QLabel: lambda x: f"QLabel(text='{cast(QLabel, x).text()}')",
        QGroupBox: lambda x: f"QGroupBox(title='{cast(QGroupBox, x).title()}')",
        QTabWidget: lambda x: f"QTabWidget(currentIndex={cast(QTabWidget, x).currentIndex()})",
        QStatusBar: lambda x: repr(x),
        QDockWidget: lambda x: f"QDockWidget(windowTitle='{cast(QDockWidget, x).windowTitle()}')",
        QDialog: lambda x: f"QDialog(windowTitle='{cast(QDialog, x).windowTitle()}')",
        QFrame: lambda x: f"QFrame(frameShape={cast(QFrame, x).frameShape()})",
        QScrollArea: lambda x: f"QScrollArea(widgetResizable={cast(QScrollArea, x).widgetResizable()})",
        # Layouts
        QVBoxLayout: lambda x: f"QVBoxLayout(count={cast(QVBoxLayout, x).count()})",
        QHBoxLayout: lambda x: f"QHBoxLayout(count={cast(QHBoxLayout, x).count()})",
        QGridLayout: lambda x: f"QGridLayout(rowCount={cast(QGridLayout, x).rowCount()}, columnCount={cast(QGridLayout, x).columnCount()})",
        QFormLayout: lambda x: f"QFormLayout(rowCount={cast(QFormLayout, x).rowCount()})",
        # Models and Views
        QListView: lambda x: f"QListView(viewMode={cast(QListView, x).viewMode()})",
        QTableView: lambda x: f"QTableView(rowCount={cast(QTableView, x).model().rowCount() if cast(QTableView, x).model() else 'N/A'})",
        QTreeView: lambda x: f"QTreeView(expanded={cast(QTreeView, x).isExpanded(cast(QTreeView, x).currentIndex())})",
        QFileSystemModel: lambda x: f"QFileSystemModel(rootPath='{cast(QFileSystemModel, x).rootPath()}')",
        QSortFilterProxyModel: lambda x: f"QSortFilterProxyModel(sourceModel={cast(QSortFilterProxyModel, x).sourceModel()})",
        QItemSelectionRange: lambda x: f"QItemSelectionRange(topLeft={cast(QItemSelectionRange, x).topLeft()}, bottomRight={cast(QItemSelectionRange, x).bottomRight()})",
        QItemSelection: lambda x: f"QItemSelection({len(cast(QItemSelection, x))} ranges)",
        # Graphics and Painting
        QPainter: lambda x: f"QPainter(device={cast(QPainter, x).device()})",
        QCursor: lambda x: f"QCursor(shape={cast(QCursor, x).shape()})",
        QPen: lambda x: f"QPen(color={cast(QPen, x).color().name()}, width={cast(QPen, x).width()}, style={cast(QPen, x).style()})",
        QBrush: lambda x: f"QBrush(color={cast(QBrush, x).color().name()}, style={cast(QBrush, x).style()})",
        QPolygon: lambda x: f"QPolygon(points={len(cast(QPolygon, x))})",
        QPolygonF: lambda x: f"QPolygonF(points={len(cast(QPolygonF, x))})",
        QPainterPath: lambda x: f"QPainterPath(elementCount={cast(QPainterPath, x).elementCount()})",
        QGradient: lambda x: f"QGradient(type={cast(QGradient, x).type()}, spread={cast(QGradient, x).spread()})",
        QLinearGradient: lambda x: f"QLinearGradient(start={cast(QLinearGradient, x).start()}, finalStop={cast(QLinearGradient, x).finalStop()})",
        QRadialGradient: lambda x: f"QRadialGradient(center={cast(QRadialGradient, x).center()}, radius={cast(QRadialGradient, x).radius()}, focalPoint={cast(QRadialGradient, x).focalPoint()})",  # noqa: E501
        QConicalGradient: lambda x: f"QConicalGradient(center={cast(QConicalGradient, x).center()}, angle={cast(QConicalGradient, x).angle()})",
        # Text and Fonts
        QTextCursor: lambda x: f"QTextCursor(position={cast(QTextCursor, x).position()}, anchor={cast(QTextCursor, x).anchor()})",
        QTextDocument: lambda x: f"QTextDocument(documentLayout={cast(QTextDocument, x).documentLayout()})",
        QTextFormat: lambda x: f"QTextFormat(type={cast(QTextFormat, x).type()})",
        QTextCharFormat: lambda x: f"QTextCharFormat(font='{cast(QTextCharFormat, x).font().family()}', pointSize={cast(QTextCharFormat, x).font().pointSize()})",
        QTextBlockFormat: lambda x: f"QTextBlockFormat(alignment={cast(QTextBlockFormat, x).alignment()})",
        QTextListFormat: lambda x: f"QTextListFormat(style={cast(QTextListFormat, x).style()})",
        QTextTableFormat: lambda x: f"QTextTableFormat(columns={cast(QTextTableFormat, x).columns()})",
        QTextFrameFormat: lambda x: f"QTextFrameFormat(position={cast(QTextFrameFormat, x).position()})",
        QTextImageFormat: lambda x: f"QTextImageFormat(name='{cast(QTextImageFormat, x).name()}')",
        QTextLength: lambda x: f"QTextLength(type={cast(QTextLength, x).type()}, value={cast(QTextLength, x).value(cast(QTextLength, x).rawValue())}, maximumLength={cast(QTextLength, x).rawValue()})",  # noqa: E501
        QTextLine: lambda x: f"QTextLine(lineNumber={cast(QTextLine, x).lineNumber()}, rect={cast(QTextLine, x).rect()})",
        QTextBlock: lambda x: f"QTextBlock(position={cast(QTextBlock, x).position()}, length={cast(QTextBlock, x).length()})",
        QTextFragment: lambda x: f"QTextFragment(position={cast(QTextFragment, x).position()}, length={cast(QTextFragment, x).length()})",
        QTextLayout: lambda x: f"QTextLayout(text='{cast(QTextLayout, x).text()[:20]}...')",
        QTextOption: lambda x: f"QTextOption(alignment={cast(QTextOption, x).alignment()})",
        QStaticText: lambda x: f"QStaticText(text='{cast(QStaticText, x).text()[:20]}...')",
        # Events
        QResizeEvent: lambda x: f"QResizeEvent(old={cast(QResizeEvent, x).oldSize()}, new={cast(QResizeEvent, x).size()})",
        QWheelEvent: lambda x: f"QWheelEvent(pos={cast(QWheelEvent, x).position()}, delta={cast(QWheelEvent, x).angleDelta()})",
        QMouseEvent: lambda x: f"QMouseEvent(type={cast(QMouseEvent, x).type()}, pos={cast(QMouseEvent, x).pos()})",
        QKeyEvent: lambda x: f"QKeyEvent(type={cast(QKeyEvent, x).type()}, key={cast(QKeyEvent, x).key()})",
        QFocusEvent: lambda x: f"QFocusEvent(type={cast(QFocusEvent, x).type()})",
        QDragEnterEvent: lambda x: f"QDragEnterEvent(pos={cast(QDragEnterEvent, x).pos()})",
        QDropEvent: lambda x: f"QDropEvent(pos={cast(QDropEvent, x).pos()}, mimeData={cast(QDropEvent, x).mimeData()})",
        # OpenGL
        QOpenGLContext: lambda x: f"QOpenGLContext(surface={cast(QOpenGLContext, x).surface()})",
        QOpenGLFramebufferObject: lambda x: f"QOpenGLFramebufferObject(size={cast(QOpenGLFramebufferObject, x).size()}, format={cast(QOpenGLFramebufferObject, x).format().samples()})",
        QOpenGLShader: lambda x: f"QOpenGLShader(type={cast(QOpenGLShader, x).shaderType()})",
        QOpenGLShaderProgram: lambda x: f"QOpenGLShaderProgram(programId={cast(QOpenGLShaderProgram, x).programId()})",
        QOpenGLTexture: lambda x: f"QOpenGLTexture(target={cast(QOpenGLTexture, x).target()}, textureId={cast(QOpenGLTexture, x).textureId()})",
        QOpenGLBuffer: lambda x: f"QOpenGLBuffer(type={cast(QOpenGLBuffer, x).type()}, usagePattern={cast(QOpenGLBuffer, x).usagePattern()})",
        QOpenGLVertexArrayObject: lambda x: f"QOpenGLVertexArrayObject(created={cast(QOpenGLVertexArrayObject, x).isCreated()})",
        QOpenGLDebugLogger: lambda x: f"QOpenGLDebugLogger(loggingMode={cast(QOpenGLDebugLogger, x).loggingMode()})",
        QOpenGLTimerQuery: lambda x: f"QOpenGLTimerQuery(created={cast(QOpenGLTimerQuery, x).isCreated()})",
        QOpenGLVersionProfile: lambda x: f"QOpenGLVersionProfile(version={cast(QOpenGLVersionProfile, x).version()}, profile={cast(QOpenGLVersionProfile, x).profile()})",
        # Miscellaneous
        QCompleter: lambda x: f"QCompleter(model={cast(QCompleter, x).model()})",
        QInputDialog: lambda x: f"QInputDialog(labelText='{cast(QInputDialog, x).labelText()}')",
        QMessageBox: lambda x: f"QMessageBox(text='{cast(QMessageBox, x).text()}')",
        QClipboard: lambda x: f"QClipboard(mode={cast(QClipboard, x).supportsSelection()})",
        QPagedPaintDevice: lambda x: f"QPagedPaintDevice(pageSize={cast(QPagedPaintDevice, x).pageSize()})",
        QPdfWriter: lambda x: repr(x),
        QTextItem: lambda x: f"QTextItem(renderFlags={cast(QTextItem, x).renderFlags()})",
        **({QTouchDevice: lambda x: f"QTouchDevice(name='{cast(QTouchDevice, x).name()}', type={cast(QTouchDevice, x).type()})"} if qtpy.QT5 else {}),
        QRawFont: lambda x: f"QRawFont(familyName='{cast(QRawFont, x).familyName()}', pixelSize={cast(QRawFont, x).pixelSize()})",
        # Base classes (moved towards the bottom)
        QWidget: lambda x: f"QWidget(type={cast(QWidget, x).__class__.__name__})",
        QMainWindow: lambda x: f"QMainWindow(windowTitle='{cast(QMainWindow, x).windowTitle()}')",
        QSplitter: lambda x: f"QSplitter(orientation={cast(QSplitter, x).orientation()})",
        QStackedWidget: lambda x: f"QStackedWidget(currentIndex={cast(QStackedWidget, x).currentIndex()})",
        QApplication: lambda x: repr(x),
        QGuiApplication: lambda x: repr(x),
        QStyledItemDelegate: lambda x: f"QStyledItemDelegate(parent={cast(QStyledItemDelegate, x).parent()})",
        QStyleOptionViewItem: lambda x: f"QStyleOptionViewItem(rect={cast(QStyleOptionViewItem, x).rect})",
        QAbstractTextDocumentLayout: lambda x: f"QAbstractTextDocumentLayout(document={cast(QAbstractTextDocumentLayout, x).document()})",
        QTextObjectInterface: lambda x: repr(x),
        QValidator: lambda x: f"QValidator(parent={cast(QValidator, x).parent()})",
        QIntValidator: lambda x: f"QIntValidator(bottom={cast(QIntValidator, x).bottom()}, top={cast(QIntValidator, x).top()})",
        QDoubleValidator: lambda x: f"QDoubleValidator(bottom={cast(QDoubleValidator, x).bottom()}, top={cast(QDoubleValidator, x).top()}, decimals={cast(QDoubleValidator, x).decimals()})",  # noqa: E501
        **({QRegExpValidator: lambda x: f"QRegExpValidator(regExp={cast(QRegExpValidator, x).regExp().pattern()})"} if qtpy.QT5 else {}),
        **({QRegularExpressionValidator: lambda x: f"QRegularExpressionValidator(regularExpression={cast(QRegularExpressionValidator, x).regularExpression().pattern()})"} if not qtpy.QT5 else {}),
        QSyntaxHighlighter: lambda x: f"QSyntaxHighlighter(parent={cast(QSyntaxHighlighter, x).document()})",
        QFileInfo: lambda x: f"{cast(QFileInfo, x).filePath()}(QFileInfo)",
        QModelIndex: lambda x: f"QModelIndex(row={cast(QModelIndex, x).row()}, column={cast(QModelIndex, x).column()})",
        QUrl: lambda x: f"QUrl('{cast(QUrl, x).toString()}')",
        QDir: lambda x: f"QDir('{cast(QDir, x).path()}')",
        QFile: lambda x: f"QFile('{cast(QFile, x).fileName()}')",
        QMimeData: lambda x: f"QMimeData(formats={cast(QMimeData, x).formats()})",
        QItemSelectionModel: lambda x: f"QItemSelectionModel(selectedIndexes={cast(QItemSelectionModel, x).selectedIndexes()})",
        QPointF: lambda x: f"QPointF({cast(QPointF, x).x()}, {cast(QPointF, x).y()})",
        QLineF: lambda x: f"QLineF({cast(QLineF, x).x1()}, {cast(QLineF, x).y1()}, {cast(QLineF, x).x2()}, {cast(QLineF, x).y2()})",
        QRegion: lambda x: f"QRegion(boundingRect={cast(QRegion, x).boundingRect()})",
        QBitmap: lambda x: f"QBitmap({cast(QBitmap, x).width()}x{cast(QBitmap, x).height()})",
        QImage: lambda x: f"QImage({cast(QImage, x).width()}x{cast(QImage, x).height()}, format={cast(QImage, x).format()})",
        QMatrix4x4: lambda x: repr(x),
        QVector2D: lambda x: f"QVector2D({cast(QVector2D, x).x()}, {cast(QVector2D, x).y()})",
        QVector3D: lambda x: f"QVector3D({cast(QVector3D, x).x()}, {cast(QVector3D, x).y()}, {cast(QVector3D, x).z()})",
        QVector4D: lambda x: f"QVector4D({cast(QVector4D, x).x()}, {cast(QVector4D, x).y()}, {cast(QVector4D, x).z()}, {cast(QVector4D, x).w()})",
        QQuaternion: lambda x: f"QQuaternion(scalar={cast(QQuaternion, x).scalar()}, vector={cast(QQuaternion, x).vector()})",
        QVariant: lambda x: f"QVariant(type={cast(QVariant, x).type()}, value={cast(QVariant, x).value()})",
        QDateTime: lambda x: f"QDateTime({cast(QDateTime, x).toString(QtCore.Qt.ISODate)})",
        QDate: lambda x: f"QDate({cast(QDate, x).toString(QtCore.Qt.ISODate)})",
        QTime: lambda x: f"QTime({cast(QTime, x).toString(QtCore.Qt.ISODate)})",
        QLocale: lambda x: f"QLocale(name='{cast(QLocale, x).name()}')",
        QUuid: lambda x: f"QUuid('{cast(QUuid, x).toString()}')",
        QByteArray: lambda x: f"QByteArray({len(cast(QByteArray, x))} bytes)",
        QJsonValue: lambda x: f"QJsonValue(type={cast(QJsonValue, x).type()})",
        QJsonDocument: lambda x: f"QJsonDocument(isArray={cast(QJsonDocument, x).isArray()}, isObject={cast(QJsonDocument, x).isObject()})",
        QAbstractItemModel: lambda x: f"QAbstractItemModel(rowCount={cast(QAbstractItemModel, x).rowCount()}, columnCount={cast(QAbstractItemModel, x).columnCount()})",
        QAbstractTableModel: lambda x: f"QAbstractTableModel(rowCount={cast(QAbstractTableModel, x).rowCount()}, columnCount={cast(QAbstractTableModel, x).columnCount()})",
        QAbstractListModel: lambda x: f"QAbstractListModel(rowCount={cast(QAbstractListModel, x).rowCount()})",
        QObject: lambda x: f"QObject(objectName='{cast(QObject, x).objectName()}')",
        QTimer: lambda x: f"QTimer(interval={cast(QTimer, x).interval()})",
        QSizeF: lambda x: f"QSizeF({cast(QSizeF, x).width()}, {cast(QSizeF, x).height()})",
        QRectF: lambda x: f"QRectF({cast(QRectF, x).x()}, {cast(QRectF, x).y()}, {cast(QRectF, x).width()}, {cast(QRectF, x).height()})",
        QPalette: lambda x: f"QPalette(active={cast(QPalette, x).currentColorGroup()})",
        QTransform: lambda x: f"QTransform(m11={cast(QTransform, x).m11()}, m12={cast(QTransform, x).m12()}, m13={cast(QTransform, x).m13()}, m21={cast(QTransform, x).m21()}, m22={cast(QTransform, x).m22()}, m23={cast(QTransform, x).m23()}, m31={cast(QTransform, x).m31()}, m32={cast(QTransform, x).m32()}, m33={cast(QTransform, x).m33()})",  # noqa: E501
        # Unorganized:
        QEvent: lambda x: f"QEvent(type={cast(QEvent, x).type()})",
        QKeySequence: lambda x: f"QKeySequence('{cast(QKeySequence, x).toString()}')",
    }

    for key, formatter in format_dict.items():
        if isinstance(arg, key):
            return formatter(arg)
    return repr(arg)


def print_qt_func_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and hasattr(args[0].__class__, func.__name__):
            # Use the original class name instead of the wrapper
            class_name = args[0].__class__.__bases__[0].__name__
            func_name = f"{class_name}.{func.__name__}"
            start_index = 1
        else:
            class_name = ""
            func_name = func.__name__
            start_index = 0

        arg_strings = [format_qt_obj(arg) for arg in args[start_index:]]
        arg_strings.extend(f"{k}={format_qt_obj(v)}" for k, v in kwargs.items())

        try:
            result = func(*args, **kwargs)
            print(f"{func_name}({', '.join(arg_strings)}) -> {format_qt_obj(result)}{os.linesep}")
        except Exception as e:
            print(f"{func_name}({', '.join(arg_strings)}) -> {e.__class__.__name__}({e!r}){os.linesep}")
            raise
        else:
            return result

    return wrapper


def get_qt_methods(cls: type) -> list[tuple[str, Callable[..., Any]]]:
    methods: list[tuple[str, Callable[..., Any]]] = []
    seen_names = set()

    # Iterate through the class and its base classes in MRO order
    for base in cls.mro():
        if base is object:
            continue

        # Get methods using inspect
        for name, method in inspect.getmembers(base, predicate=inspect.isfunction):
            if name in seen_names:
                continue
            methods.append((name, method))
            seen_names.add(name)

        # Use meta-object system for QObject subclasses
        if not issubclass(base, QObject):
            continue

        meta = base.staticMetaObject
        for i in range(meta.methodCount()):
            method = meta.method(i)
            name = bytes(method.name()).decode()
            if name in seen_names:
                continue

            attr = getattr(base, name, None)
            if attr is None or name.startswith("_") or not callable(attr) or isinstance(attr, Signal):
                continue

            methods.append((name, attr))
            seen_names.add(name)

    return methods


T = TypeVar("T")
def print_qt_class_calls(exclude_funcs: list[str] | None = None) -> Callable[[type[T]], type[T]]:  # noqa: ANN201
    if exclude_funcs is None:
        exclude_funcs = []

    def decorator(cls: type[T]) -> type[T]:  # noqa: ANN202
        # Create a new class that inherits from the original class
        class Wrapper(cls):
            pass

        # Get all methods and wrap them
        all_methods = get_qt_methods(cls)
        for name, method in all_methods:
            if name not in exclude_funcs and not (name.startswith("__") and name != "__repr__"):
                setattr(Wrapper, name, print_qt_func_call(method))

        return cast(Type[T], Wrapper)

    return decorator
