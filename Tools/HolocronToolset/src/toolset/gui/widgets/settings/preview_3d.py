from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore

from toolset.data.settings import Settings

if TYPE_CHECKING:
    from toolset.data.settings import SettingsProperty


class ModelRendererSettings(Settings):
    sig_settings_edited: QtCore.Signal = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    def __init__(self):
        super().__init__("ModelRenderer")

    # region Bools
    utcShowByDefault: SettingsProperty[bool] = Settings.addSetting(
        "utcShowByDefault",
        False,
    )
    # endregion

    # region Ints
    backgroundColour: SettingsProperty[int] = Settings.addSetting(
        "backgroundColour",
        0,
    )
    # endregion
