from __future__ import annotations

import os

from typing import TYPE_CHECKING

from qtpy.QtGui import QFont
from qtpy.QtWidgets import QApplication

if TYPE_CHECKING:
    from qtpy.QtCore import QCoreApplication, QSettings


def setup_pre_init_settings():
    """Setup pre-initialization settings for HoloPazaak.

    Call main_init() to get here.
    
    Currently, no pre-init settings are required for HoloPazaak.
    This function exists for future extensibility and to maintain
    consistency with the initialization pattern.
    """
    # Pre-init settings would go here if needed (e.g., environment variables,
    # logging configuration, etc.). Currently none required.


def setup_post_init_settings():
    """Set up post-initialization settings for the application.

    This function performs the following tasks:
    1. Retrieves the QApplication instance and sets the global font.
    2. Sets miscellaneous settings that can be changed without restarting.
    """
    app: QCoreApplication | None = QApplication.instance()
    assert app is not None, "QApplication instance not found."
    assert isinstance(app, QApplication), "QApplication instance not a QApplication type object."

    # Set the global font for the application (can be customized later)
    app.setFont(QApplication.font())


def setup_holopazaak_default_env():
    """Setup default environment variables for HoloPazaak based on our recommendations.

    These can be configured later if needed.
    """
    from holopazaak.main_init import is_frozen

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation")
        os.environ["QT_MEDIA_BACKEND"] = os.environ.get("QT_MEDIA_BACKEND", "windows")
    if is_frozen():
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "0")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=false")
    else:
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "1")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=true")

