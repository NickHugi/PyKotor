from typing import Optional, Tuple

from pykotor.extract.installation import Installation

from pykotor.resource.type import ResourceType

from pykotor.resource.generics.uti import read_uti

from pykotor.common.misc import EquipmentSlot

from pykotor.resource.formats.twoda import TwoDA
from pykotor.resource.generics.utc import UTC


def get_model(
        utc: UTC,
        installation: Installation,
        *,
        appearance: Optional[TwoDA] = None,
        baseitems: Optional[TwoDA] = None
) -> Tuple[str, Optional[str]]:
    """
    Returns the model and texture names for the given creature.

    The value for the texture may be None and the default texture provided by the model should be used instead.

    If no value is specified for the appearance or baseitem parameters then they will be loaded from the given
    installation.

    Args:
        utc: UTC object of the target creature.
        installation: The relevant installation.
        appearance: The appearance.2da loaded into a TwoDA object.
        baseitems: The baseitems.2da loaded into a TwoDA object.

    Returns:
        Returns a tuple containing the name of the model and the texture to apply to the model.
    """
    if appearance is None:
        installation.resource("appearance", ResourceType.TwoDA)
    if baseitems is None:
        installation.resource("baseitems", ResourceType.TwoDA)

    try:
        armor_resref = utc.equipment[EquipmentSlot.ARMOR].resref.get()
        armor_uti = read_uti(installation.resource(armor_resref, ResourceType.UTI).data)
        model_column = "model" + baseitems.get_row(armor_uti.base_item).get_string("bodyvar").lower()
        tex_column = "tex" + baseitems.get_row(armor_uti.base_item).get_string("bodyvar").lower()

        # Get the model/texture from under the above columns, if the cell is blank default to the race column
        body_model = appearance.get_row(utc.appearance_id).get_string(model_column)
        override_texture = appearance.get_row(utc.appearance_id).get_string(tex_column) + str(armor_uti.texture_variation).rjust(2, "0")

        if override_texture == "":
            override_texture = None
        if body_model.isspace():
            raise ValueError("Use default race model")
    except Exception:
        body_model = appearance.get_row(utc.appearance_id).get_string("race")
        override_texture = None

    return body_model, override_texture
