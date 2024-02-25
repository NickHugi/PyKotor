from __future__ import annotations

from toolset.data.settings import Settings


class ModelRendererSettings(Settings):
    def __init__(self):
        super().__init__("ModelRenderer")

    # region Bools
    utcShowByDefault = Settings._addSetting(
        "utcShowByDefault",
        False,
    )
    # endregion

    # region Ints
    backgroundColour = Settings._addSetting(
        "backgroundColour",
        0,
    )
    # endregion
