from __future__ import annotations

import qtpy

from qtpy.QtCore import QMetaType, QObject


def get_qt_meta_type(param_type: type, current_value: QObject | None = None) -> QMetaType.Type:
    if isinstance(current_value, QObject):
        meta_type = current_value.metaObject().userProperty().userType()
    elif qtpy.QT5:
        meta_type = QMetaType.type(param_type.__name__)
    else:
        # For Qt6, we need to find the corresponding QMetaType.Type enum value
        type_name = param_type.__name__
        try:
            meta_type = QMetaType.Type(type_name)
        except KeyError:
            # If the type is not in QMetaType.Type, default to UnknownType
            meta_type = QMetaType.Type.UnknownType
    return meta_type


def determine_type(param_type: type, current_value: QObject | None = None) -> QMetaType | type:
    if not issubclass(param_type, QObject):
        return param_type
    if isinstance(current_value, QObject):
        return QMetaType(current_value.metaObject().userProperty().userType())
    if qtpy.QT5:
        return QMetaType(QMetaType.type(param_type.__name__))
    if qtpy.QT6:
        return QMetaType(QMetaType.fromName(param_type.__name__.encode()))
    return QMetaType(QMetaType.Type.UnknownType)
