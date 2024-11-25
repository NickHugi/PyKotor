from __future__ import annotations

import os

from typing import TYPE_CHECKING

from qtpy.QtGui import QFont
from qtpy.QtWidgets import QApplication

from toolset.gui.widgets.settings.widgets.application import ApplicationSettings

if TYPE_CHECKING:
    from qtpy.QtCore import QSettings


def _setup_pre_init_settings():
    """Setup pre-initialization settings for the Holocron Toolset.

    Call main_init() to get here.
    """
    from qtpy.QtWidgets import QApplication  # pylint: disable=redefined-outer-name

    from toolset.gui.widgets.settings.widgets.application import ApplicationSettings

    # Some application settings must be set before the app starts.
    # These ones are accessible through the in-app settings window widget.
    settings_widget = ApplicationSettings()
    environment_variables: dict[str, str] = settings_widget.app_env_variables
    for key, value in environment_variables.items():
        os.environ[key] = os.environ.get(key, value)  # Use os.environ.get to prioritize the existing env.
    for attr_name, attr_value in settings_widget.REQUIRES_RESTART.items():
        if attr_value is None:  # attr not available in this qt version.
            continue
        QApplication.setAttribute(
            attr_value,
            settings_widget.settings.value(attr_name, QApplication.testAttribute(attr_value), bool),
        )


def setup_post_init_settings():
    """Set up post-initialization settings for the application.

    This function performs the following tasks:
    1. Imports necessary Qt modules and application settings.
    2. Retrieves the QApplication instance and sets the global font.
    3. Applies Qt attributes that require a restart to take effect.
    4. Sets miscellaneous settings that can be changed without restarting.

    The function uses the ApplicationSettings class to manage and apply various
    settings to the QApplication instance.
    """
    settings_widget = ApplicationSettings()
    toolset_qsettings: QSettings = settings_widget.settings
    app = QApplication.instance()
    assert app is not None, "QApplication instance not found."
    assert isinstance(app, QApplication), "QApplication instance not a QApplication type object."

    # Set the global font for the application
    app.setFont(toolset_qsettings.value("GlobalFont", QApplication.font(), QFont))

    # Apply Qt attributes that require a restart
    for attr_name, attr_value in settings_widget.__dict__.items():
        if attr_value is None:  # attr not available in this qt version.
            continue
        if attr_name.startswith("AA_"):
            QApplication.setAttribute(
                attr_value,
                toolset_qsettings.value(attr_name, QApplication.testAttribute(attr_value), bool),
            )

    # Set miscellaneous settings that can be changed without restarting
    for name, setting in settings_widget.MISC_SETTINGS.items():
        if toolset_qsettings.contains(name):
            qsetting_lookup_val = toolset_qsettings.value(name, setting.getter(), setting.setting_type)
            setting.setter(qsetting_lookup_val)


def setup_toolset_default_env():
    """Setup default environment variables for the toolset based on our recommendations.

    These can be configured in the toolset's Settings dialog.
    """
    from toolset.main_init import is_frozen
    from utility.misc import is_debug_mode

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation")
        os.environ["QT_MEDIA_BACKEND"] = "windows"
    if not is_debug_mode() or is_frozen():
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "0")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=false")  # Disable specific Qt debug output
    else:
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "1")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=true")  # Enable specific Qt debug output
