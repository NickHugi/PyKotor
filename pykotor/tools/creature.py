from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import EquipmentSlot
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.generics.uti import read_uti
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.utc import UTC


def get_body_model(
    utc: UTC,
    installation: Installation,
    *,
    appearance: TwoDA | None = None,
    baseitems: TwoDA | None = None,
) -> tuple[str, str | None]:
    """Returns the model and texture names for the given creature.

    The value for the texture may be None and the default texture provided by the model should be used instead.

    If no value is specified for the appearance or baseitem parameters then they will be loaded from the given
    installation.

    Args:
    ----
        utc: UTC object of the target creature.
        installation: The relevant installation.
        appearance: The appearance.2da loaded into a TwoDA object.
        baseitems: The baseitems.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns a tuple containing the name of the model and the texture to apply to the model.
    """
    if appearance is None:
        appearance = read_2da(installation.resource("appearance", ResourceType.TwoDA).data)
    if baseitems is None:
        baseitems = read_2da(installation.resource("baseitems", ResourceType.TwoDA).data)

    body_model = ""
    override_texture = None

    if appearance.get_row(utc.appearance_id).get_string("modeltype") == "B":
        body_model = appearance.get_row(utc.appearance_id).get_string("modela")

        if utc.alignment <= 25:
            override_texture = appearance.get_row(utc.appearance_id).get_string("texaevil") + "01"
        else:
            override_texture = appearance.get_row(utc.appearance_id).get_string("texa") + "01"

        if EquipmentSlot.ARMOR in utc.equipment:
            armor_resref = utc.equipment[EquipmentSlot.ARMOR].resref.get()
            armor_uti = read_uti(installation.resource(armor_resref, ResourceType.UTI).data)
            armor_variation = baseitems.get_row(armor_uti.base_item).get_string("bodyvar").lower()

            normal_tex_column = f"tex{armor_variation}"
            evil_tex_column = f"tex{armor_variation}evil"
            if utc.alignment <= 25 and evil_tex_column in appearance.get_headers():
                tex_column = evil_tex_column
            else:
                tex_column = normal_tex_column

            model_column = f"model{armor_variation}"
            body_model = appearance.get_row(utc.appearance_id).get_string(model_column)
            override_texture: str = (
                appearance.get_row(utc.appearance_id).get_string(tex_column)
                + str(armor_uti.texture_variation).rjust(2, "0")
            )

    if body_model == "":
        body_model = appearance.get_row(utc.appearance_id).get_string("race")

    return body_model, override_texture


def get_weapon_models(
    utc: UTC,
    installation: Installation,
    *,
    appearance: TwoDA | None = None,
    baseitems: TwoDA | None = None,
) -> tuple[str | None, str | None]:
    """Returns a tuple containing the right-hand weapon model and the left-hand weapon model (in that order).

    If no weapon is equipped in a particular hand the value will return None.

    If no value is specified for the appearance or baseitem parameters then they will be loaded from the given
    installation.

    Args:
    ----
        utc: UTC object of the target creature.
        installation: The relevant installation.
        appearance: The appearance.2da loaded into a TwoDA object.
        baseitems: The baseitems.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns a tuple containing right-hand and left-hand weapon model names.
    """
    if appearance is None:
        appearance = read_2da(installation.resource("appearance", ResourceType.TwoDA).data)
    if baseitems is None:
        baseitems = read_2da(installation.resource("baseitems", ResourceType.TwoDA).data)

    rhand_model = None
    lhand_model = None

    rhand_resref = utc.equipment[EquipmentSlot.RIGHT_HAND].resref.get() if EquipmentSlot.RIGHT_HAND in utc.equipment else None
    lhand_resref = utc.equipment[EquipmentSlot.LEFT_HAND].resref.get() if EquipmentSlot.LEFT_HAND in utc.equipment else None

    if rhand_resref is not None:
        rhand_model = _load_hand_uti(
            installation,
            rhand_resref,
            baseitems,
        )
    if lhand_resref is not None:
        lhand_model = _load_hand_uti(
            installation,
            lhand_resref,
            baseitems,
        )
    return rhand_model, lhand_model


def _load_hand_uti(
    installation: Installation,
    hand_resref: str,
    baseitems: TwoDA | None,
):
    hand_uti = read_uti(installation.resource(hand_resref, ResourceType.UTI).data)
    default_model = baseitems.get_row(hand_uti.base_item).get_string("defaultmodel")
    return default_model.replace(
        "001",
        str(hand_uti.model_variation).rjust(3, "0"),
    )


def get_head_model(
    utc: UTC,
    installation: Installation,
    *,
    appearance: TwoDA | None = None,
    heads: TwoDA | None = None,
) -> tuple[str | None, str | None]:
    """Returns the model and texture names for the head used by a creature.

    The value for the texture may be None and the default texture provided by the model should be used instead.

    If no value is specified for the appearance or heads parameters then they will be loaded from the given
    installation.

    Args:
    ----
        utc: UTC object of the target creature.
        installation: The relevant installation.
        appearance: The appearance.2da loaded into a TwoDA object.
        heads: The heads.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns a tuple containing the name of the model and the texture to apply to the model.
    """
    if appearance is None:
        appearance = read_2da(installation.resource("appearance", ResourceType.TwoDA).data)
    if heads is None:
        heads = read_2da(installation.resource("heads", ResourceType.TwoDA).data)

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
) -> str | None:
    """Returns the model for the mask a creature is wearing.

    The value for the texture will return None if the creature does not have a mask equipped.

    If no value is specified for the appearance or heads parameters then they will be loaded from the given
    installation.

    Args:
    ----
        utc: UTC object of the target creature.
        installation: The relevant installation.

    Returns:
    -------
        Returns a name of the mask model.
    """
    model = None

    if EquipmentSlot.HEAD in utc.equipment:
        resref = utc.equipment[EquipmentSlot.HEAD].resref.get()
        uti = read_uti(installation.resource(resref, ResourceType.UTI).data)
        model = "I_Mask_" + str(uti.model_variation).rjust(3, "0")

    return model
