from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import EquipmentSlot
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.generics.uti import read_uti
from pykotor.resource.type import ResourceType
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.utc import UTC
    from pykotor.resource.generics.uti import UTI


def get_body_model(
    utc: UTC,
    installation: Installation,
    *,
    appearance: TwoDA | None = None,
    baseitems: TwoDA | None = None,
) -> tuple[str | None, str | None]:    # sourcery skip: extract-duplicate-method
    """Returns the body model and texture names for the given creature utc.

    The values for the model/texture may be None and the default texture provided by the model should be used instead.

    If no value is specified for the appearance or baseitem parameters then they will be loaded from the given
    installation.

    Args:
    ----
        utc: UTC object of the target creature.
        installation: The relevant installation.
        appearance: The appearance.2da loaded into a TwoDA object.
        baseitems: The baseitems.2da loaded into a TwoDA object.

    Raises:
        ValueError - Required installation resource not found.
        KeyError - Column name not found in a 2DA.
        IndexError - Row index not found in a 2DA.
        OSError - appearance.2da, baseitems.2da, or the armor UTI is corrupted.

    Returns:
    -------
        Returns a tuple containing the name of the model and the texture for the creature.

    Processing Logic:
        - if modeltype column in appearance.2da is something other than B:
            - there's no override texture and the body model name is in the 'race' column
        - if it is B:
            - if wearing armor:
                - Check the 'bodyvar' column of 'bodyitems.2da' with the row specified by the armor uti
                - use the utc texture variation attr to determine the specific model column in appearance (e.g. 'modelb')
            - else:
                - get it from 'modela' column, append '01' to the end of the texture name
            - process override texture based on alignment
    """
    if appearance is None:
        appearance_lookup = installation.resource("appearance", ResourceType.TwoDA)
        if not appearance_lookup:
            raise ValueError("appearance.2da missing from installation.")
        appearance = read_2da(appearance_lookup.data)

    if baseitems is None:
        baseitems_lookup = installation.resource("baseitems", ResourceType.TwoDA)
        if not baseitems_lookup:
            raise ValueError("baseitems.2da missing from installation.")
        baseitems = read_2da(baseitems_lookup.data)

    first_name = installation.string(utc.first_name)
    context_base = f" for UTC '{first_name}'"

    print(f"Lookup appearance row {utc.appearance_id} for get_body_model call.")
    utc_appearance_row = appearance.get_row(utc.appearance_id, context=f"Fetching row based on appearance_id{context_base}")
    body_model: str | None = None
    override_texture: str | None = None

    modeltype = utc_appearance_row.get_string("modeltype", context=f"Fetching model type{context_base}")
    if modeltype != "B":
        print(f"appearance.2da: utc 'modeltype' is '{modeltype}', fetching 'race' model{context_base}")
        body_model = utc_appearance_row.get_string("race", context=context_base)
    else:
        print("appearance.2da: utc 'modeltype' is 'B'")

        def lookupNoArmor() -> tuple[Literal["modela"], str, Literal["texaevil", "texa"], Literal["01"], str]:
            model_column = "modela"
            body_model = utc_appearance_row.get_string(model_column, context=f"Fetching model 'modela'{context_base}")
            tex_column = "texaevil" if utc.alignment <= 25 else "texa"
            tex_append = "01"
            override_texture = utc_appearance_row.get_string(tex_column, context=f"Fetching default texture{context_base}")
            return model_column, body_model, tex_column, tex_append, override_texture

        if EquipmentSlot.ARMOR in utc.equipment and utc.equipment[EquipmentSlot.ARMOR].resref:
            armor_resref = utc.equipment[EquipmentSlot.ARMOR].resref
            RobustRootLogger().debug(f"utc is wearing armor, fetch '{armor_resref}.uti'")
            armor_res_lookup = installation.resource(str(armor_resref), ResourceType.UTI)
            if armor_res_lookup is None:
                RobustRootLogger.error(f"'{armor_resref}.uti' missing from installation{context_base}")
                model_column, body_model, tex_column, tex_append, override_texture = lookupNoArmor()  # fallback
            else:
                armor_uti = read_uti(armor_res_lookup.data)
                RobustRootLogger().debug(f"baseitems.2da: get body row {armor_uti.base_item} for their armor")
                body_row = baseitems.get_row(armor_uti.base_item, context=f"Fetching armor base item row{context_base}")
                body_cell = body_row.get_string("bodyvar", context=f"Fetching 'bodyvar'{context_base}")
                RobustRootLogger().debug(f"baseitems.2da: 'bodyvar' cell: {body_cell}")

                armor_variation = body_cell.lower()
                model_column = f"model{armor_variation}"
                evil_tex_column = f"tex{armor_variation}evil"
                tex_column = evil_tex_column if utc.alignment <= 25 and evil_tex_column in appearance.get_headers() else f"tex{armor_variation}"
                tex_append = str(armor_uti.texture_variation).rjust(2, "0")  # Ensure one-digit numerics are proceeded by '0'. 5 -> 05, 100 -> 100.

                body_model = utc_appearance_row.get_string(model_column, context=f"Fetching model column{context_base}")
                override_texture = utc_appearance_row.get_string(tex_column, context=f"Fetching texture column{context_base}")
        else:
            model_column, body_model, tex_column, tex_append, override_texture = lookupNoArmor()

        print(f"appearance.2da's texture column: '{tex_column}'")
        print(f"override_texture name: '{override_texture}'")

        if override_texture and override_texture.strip() and override_texture != "****":
            fallback_override_texture = override_texture + tex_append
            if tex_append != "01" and installation.texture(fallback_override_texture) is None:  # e.g. g_lena.utc which uses the twi'lek stripper model (i.e. should be n_twilekfc01 not n_twilekfc05)
                fallback_override_texture = f"{override_texture}01"
                print(f"override texture '{fallback_override_texture}' not found, appending '01' to the end like the game itself would do.")
            override_texture = fallback_override_texture
        else:
            override_texture = None
        print(f"Final override texture name (from appearance.2da's '{tex_column}' column): '{override_texture}'")
        print(f"Final body model name (from appearance.2da's '{model_column}' column): '{body_model}'")

    if not body_model or not body_model.strip() or body_model == "****":
        body_model = utc_appearance_row.get_string("race", context=f"Fetching 'race' column{context_base}")
        print(f"body model name (from appearance.2da's 'race' column): '{body_model}'")

    return body_model, override_texture


def get_weapon_models(
    utc: UTC,
    installation: Installation,
    *,
    appearance: TwoDA | None = None,
    baseitems: TwoDA | None = None,
) -> tuple[str | None, str | None]:  # sourcery skip: extract-duplicate-method
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
        appearance_lookup = installation.resource("appearance", ResourceType.TwoDA)
        if not appearance_lookup:
            RobustRootLogger().error("appearance.2da missing from installation.")
            return None, None
        appearance = read_2da(appearance_lookup.data)
    if baseitems is None:
        baseitems_lookup = installation.resource("baseitems", ResourceType.TwoDA)
        if not baseitems_lookup:
            RobustRootLogger().error("baseitems.2da missing from installation.")
            return None, None
        baseitems = read_2da(baseitems_lookup.data)

    rhand_model: str | None = None
    lhand_model: str | None = None

    rhand_resname: str | None = str(utc.equipment[EquipmentSlot.RIGHT_HAND].resref) if EquipmentSlot.RIGHT_HAND in utc.equipment else None
    lhand_resname: str | None = str(utc.equipment[EquipmentSlot.LEFT_HAND].resref) if EquipmentSlot.LEFT_HAND in utc.equipment else None

    if rhand_resname:
        rhand_model = _load_hand_uti(installation, rhand_resname, baseitems)
    if lhand_resname:
        lhand_model = _load_hand_uti(installation, lhand_resname, baseitems)
    return rhand_model, lhand_model


def _load_hand_uti(
    installation: Installation,
    hand_resref: str,
    baseitems: TwoDA,
) -> str | None:
    """Loads the hand UTI model variation from the base item row.

    Args:
    ----
        installation: Installation - The installation object
        hand_resref: str - The resref of the hand UTI
        baseitems: TwoDA - The base items table
    Returns:
        default_model: str - The default model string with model variation substituted

    Processing Logic:
    ----------------
        - The function reads the UTI data from the provided installation
        - It looks up the default model string for the base item in the base items table
        - It replaces the "001" placeholder in the default model with the zero padded model variation from the UTI
        - The formatted default model is returned.
    """
    hand_lookup = installation.resource(hand_resref, ResourceType.UTI)
    if not hand_lookup:
        RobustRootLogger.error(f"{hand_resref}.uti missing from installation.")
        return None
    hand_uti: UTI = read_uti(hand_lookup.data)
    default_model: str = baseitems.get_row(hand_uti.base_item).get_string("defaultmodel")
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
) -> tuple[str | None, str | None]:  # sourcery skip: extract-duplicate-method
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
        appearance_lookup = installation.resource("appearance", ResourceType.TwoDA)
        if not appearance_lookup:
            RobustRootLogger().error("appearance.2da missing from installation.")
            return None, None
        appearance = read_2da(appearance_lookup.data)
    if heads is None:
        heads_lookup = installation.resource("heads", ResourceType.TwoDA)
        if not heads_lookup:
            RobustRootLogger().error("heads.2da missing from installation.")
            return None, None
        heads = read_2da(heads_lookup.data)

    model: str | None = None
    texture: str | None = None

    head_id = appearance.get_row(utc.appearance_id).get_integer("normalhead")
    if head_id is not None:
        try:
            head_row = heads.get_row(head_id)
        except IndexError:
            RobustRootLogger().error(
                "Row %s missing from heads.2da, defined in appearance.2da under the column 'normalhead' row %s",
                head_id,
                utc.appearance_id,
                exc_info=True,
            )
        model = head_row.get_string("head")
        head_column_name: str | None = None
        if utc.alignment < 10:
            head_column_name = "headtexvvve"
        elif utc.alignment < 20:
            head_column_name = "headtexvve"
        elif utc.alignment < 30:
            head_column_name = "headtexve"
        elif utc.alignment < 40:
            head_column_name = "headtexe"
        elif "alttexture" in heads.get_headers():
            if not installation.game().is_k2():  # TSL only override.
                RobustRootLogger().error("'alttexture' column in heads.2da should never exist in a K1 installation.")
            else:
                head_column_name = "alttexture"
        if head_column_name is not None:
            try:
                texture = head_row.get_string(head_column_name)
                texture = texture if texture and texture.strip() else None
            except KeyError:
                RobustRootLogger().error("Cannot find %s in heads.2da", head_column_name, exc_info=True)

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
    model: str | None = None

    headEquip = utc.equipment.get(EquipmentSlot.HEAD)
    if headEquip is not None:
        resref = headEquip.resref
        if not resref:
            return None
        uti: UTI = read_uti(installation.resource(str(resref), ResourceType.UTI).data)
        model = "I_Mask_" + str(uti.model_variation).rjust(3, "0")

    return model
