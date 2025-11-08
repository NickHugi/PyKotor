from __future__ import annotations

from toolset.data.settings import Settings


class ModelRendererSettings(Settings):  # TODO(NickHugi):
    def __init__(self):
        super().__init__("ModelRenderer")

    # region Bools
    utcShowByDefault = Settings.addSetting(
        "utcShowByDefault",
        False,
    )
    # endregion

    # region Ints
    backgroundColour = Settings.addSetting(
        "backgroundColour",
        0,
    )
    # endregion
