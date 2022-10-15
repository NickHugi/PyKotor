import traceback
from typing import Optional, Tuple

from pykotor.extract.installation import Installation

from pykotor.resource.type import ResourceType

from pykotor.resource.generics.uti import read_uti

from pykotor.common.misc import EquipmentSlot

from pykotor.resource.formats.twoda import TwoDA
from pykotor.resource.generics.utc import UTC


def get_body_model(
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

    body_model = ""
    override_texture = None

    if appearance.get_row(utc.appearance_id).get_string("modeltype") == "B":
        body_model = appearance.get_row(utc.appearance_id).get_string("modela")
        override_texture = appearance.get_row(utc.appearance_id).get_string("texa") + "01"

        if EquipmentSlot.ARMOR in utc.equipment:
            armor_resref = utc.equipment[EquipmentSlot.ARMOR].resref.get()
            armor_uti = read_uti(installation.resource(armor_resref, ResourceType.UTI).data)
            model_column = "model" + baseitems.get_row(armor_uti.base_item).get_string("bodyvar").lower()
            tex_column = "tex" + baseitems.get_row(armor_uti.base_item).get_string("bodyvar").lower()
            body_model = appearance.get_row(utc.appearance_id).get_string(model_column)
            override_texture = appearance.get_row(utc.appearance_id).get_string(tex_column) + str(armor_uti.texture_variation).rjust(2, "0")

    if body_model == "":
        body_model = appearance.get_row(utc.appearance_id).get_string("race")

    return body_model, override_texture


def get_weapon_models(
        utc: UTC,
        installation: Installation,
        *,
        appearance: Optional[TwoDA] = None,
        baseitems: Optional[TwoDA] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns a tuple containing the right-hand weapon model and the left-hand weapon model (in that order).

    If no weapon is equipped in a particular hand the value will return None.

    If no value is specified for the appearance or baseitem parameters then they will be loaded from the given
    installation.

    Args:
        utc: UTC object of the target creature.
        installation: The relevant installation.
        appearance: The appearance.2da loaded into a TwoDA object.
        baseitems: The baseitems.2da loaded into a TwoDA object.

    Returns:
        Returns a tuple containing right-hand and left-hand weapon model names.
    """
    if appearance is None:
        installation.resource("appearance", ResourceType.TwoDA)
    if baseitems is None:
        installation.resource("baseitems", ResourceType.TwoDA)

    rhand_model = None
    lhand_model = None

    rhand_resref = utc.equipment[EquipmentSlot.RIGHT_HAND].resref.get() if EquipmentSlot.RIGHT_HAND in utc.equipment else None
    lhand_resref = utc.equipment[EquipmentSlot.LEFT_HAND].resref.get() if EquipmentSlot.LEFT_HAND in utc.equipment else None

    if rhand_resref is not None:
        rhand_uti = read_uti(installation.resource(rhand_resref, ResourceType.UTI).data)
        default_model = baseitems.get_row(rhand_uti.base_item).get_string("defaultmodel")
        rhand_model = default_model.replace("001", str(rhand_uti.model_variation).rjust(3, "0"))

    if lhand_resref is not None:
        lhand_uti = read_uti(installation.resource(lhand_resref, ResourceType.UTI).data)
        default_model = baseitems.get_row(lhand_uti.base_item).get_string("defaultmodel")
        lhand_model = default_model.replace("001", str(lhand_uti.model_variation).rjust(3, "0"))

    return rhand_model, lhand_model


def get_head_model(
        utc: UTC,
        installation: Installation,
        *,
        appearance: Optional[TwoDA] = None,
        heads: Optional[TwoDA] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns the model and texture names for the head used by a creature.

    The value for the texture may be None and the default texture provided by the model should be used instead.

    If no value is specified for the appearance or heads parameters then they will be loaded from the given
    installation.

    Args:
        utc: UTC object of the target creature.
        installation: The relevant installation.
        appearance: The appearance.2da loaded into a TwoDA object.
        heads: The heads.2da loaded into a TwoDA object.

    Returns:
        Returns a tuple containing the name of the model and the texture to apply to the model.
    """
    if appearance is None:
        installation.resource("appearance", ResourceType.TwoDA)
    if heads is None:
        installation.resource("heads", ResourceType.TwoDA)

    model = None
    texture = None

    head_id = appearance.get_row(utc.appearance_id).get_integer("normalhead")
    if head_id is not None:
        model = heads.get_row(head_id).get_string("head")
        if utc.alignment < 10:
            texture = heads.get_row(head_id).get_string("headtexvvve")
        elif utc.alignment < 20:
            texture = heads.get_row(head_id).get_string("headtexvve")
        elif utc.alignment < 30:
            texture = heads.get_row(head_id).get_string("headtexve")
        elif utc.alignment < 40:
            texture = heads.get_row(head_id).get_string("headtexe")

        if texture == "":
            texture = None

    return model, texture


def get_mask_model(
        utc: UTC,
        installation: Installation,
) -> Optional[str]:
    """
    Returns the model for the mask a creature is wearing.

    The value for the texture will return None if the creature does not have a mask equipped.

    If no value is specified for the appearance or heads parameters then they will be loaded from the given
    installation.

    Args:
        utc: UTC object of the target creature.
        installation: The relevant installation.

    Returns:
        Returns a name of the mask model.
    """
    model = None

    if EquipmentSlot.HEAD in utc.equipment:
        resref = utc.equipment[EquipmentSlot.HEAD].resref.get()
        uti = read_uti(installation.resource(resref, ResourceType.UTI).data)
        model = "I_Mask_" + str(uti.model_variation).rjust(3, "0")

    return model
