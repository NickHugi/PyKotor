from __future__ import annotations

from qtpy.QtCore import Qt

# Role constants
_LINK_PARENT_NODE_PATH_ROLE: int = Qt.ItemDataRole.UserRole + 1
_EXTRA_DISPLAY_ROLE: int = Qt.ItemDataRole.UserRole + 2
_DUMMY_ITEM: int = Qt.ItemDataRole.UserRole + 3
_COPY_ROLE = Qt.ItemDataRole.UserRole + 4
_DLG_MIME_DATA_ROLE = Qt.ItemDataRole.UserRole + 5
_MODEL_INSTANCE_ID_ROLE = Qt.ItemDataRole.UserRole + 6

# MIME type constants
QT_STANDARD_ITEM_FORMAT = "application/x-qabstractitemmodeldatalist"
