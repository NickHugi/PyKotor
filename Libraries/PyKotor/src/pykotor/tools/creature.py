from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from loggerplus import RobustLogger

from pykotor.common.misc import EquipmentSlot
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.generics.uti import UTI, read_uti
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.misc import InventoryItem, ResRef
    from pykotor.extract.file import ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.extract.twoda import TwoDARow
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.utc import UTC
    from pykotor.resource.generics.uti import UTI


def get_body_model(  # noqa: C901, PLR0912, PLR0915
    utc: UTC,
    installation: Installation,
    *,
    appearance: TwoDA | None = None,
    baseitems: TwoDA | None = None,
) -> tuple[str | None, str | None]:
    """Return the body model and texture names for the given creature UTC."""
    log = RobustLogger()

    # Load appearance.2da if not provided
    if appearance is None:
        appearance_lookup: ResourceResult | None = installation.resource("appearance", ResourceType.TwoDA)
        if not appearance_lookup:
            raise ValueError("appearance.2da missing from installation.")
        appearance = read_2da(appearance_lookup.data)

    # Load baseitems.2da if not provided
    if baseitems is None:
        baseitems_lookup: ResourceResult | None = installation.resource("baseitems", ResourceType.TwoDA)
        if not baseitems_lookup:
            raise ValueError("baseitems.2da missing from installation.")
        baseitems = read_2da(baseitems_lookup.data)

    # Prepare context for logging and error messages
    first_name: str = installation.string(utc.first_name)
    context_base: str = f" for UTC '{first_name}'"

    log.debug("Lookup appearance row %s for get_body_model call.", utc.appearance_id)
    utc_appearance_row: TwoDARow = appearance.get_row(utc.appearance_id, context=f"Fetching row based on appearance_id{context_base}")
    body_model: str | None = None
    override_texture: str | None = None

    # Determine body model and texture based on modeltype
    modeltype: str = utc_appearance_row.get_string("modeltype", context=f"Fetching model type{context_base}")
    if modeltype != "B":
        log.debug("appearance.2da: utc 'modeltype' is '%s', fetching 'race' model%s", modeltype, context_base)
        body_model = utc_appearance_row.get_string("race", context=context_base)
    else:
        log.debug("appearance.2da: utc 'modeltype' is 'B'")

        # Handle armor or default model/texture
        if EquipmentSlot.ARMOR not in utc.equipment or not utc.equipment[EquipmentSlot.ARMOR].resref:
            model_column = "modela"
            body_model = utc_appearance_row.get_string(model_column, context=f"Fetching model 'modela'{context_base}")
            tex_column: Literal["texaevil", "texa"] = "texaevil" if utc.alignment <= 25 else "texa"
            tex_append = "01"
            override_texture = utc_appearance_row.get_string(tex_column, context=f"Fetching default texture{context_base}")
        else:
            # Handle armor-specific model and texture
            armor_resref: ResRef = utc.equipment[EquipmentSlot.ARMOR].resref
            log.debug("utc is wearing armor, fetch '%s.uti'", armor_resref)

            # Attempt to load armor UTI
            armor_res_lookup: ResourceResult | None = installation.resource(str(armor_resref), ResourceType.UTI)
            if armor_res_lookup is None:
                log.error("'%s.uti' missing from installation%s", armor_resref, context_base)
                # Fallback to default values if armor UTI is missing
                model_column = "modela"
                body_model = utc_appearance_row.get_string(model_column, context=f"Fetching model 'modela'{context_base}")
                tex_column = "texaevil" if utc.alignment <= 25 else "texa"
                tex_append = "01"
                override_texture = utc_appearance_row.get_string(tex_column, context=f"Fetching default texture{context_base}")
            else:
                # Process armor-specific model and texture
                armor_uti: UTI = read_uti(armor_res_lookup.data)
                log.debug("baseitems.2da: get body row %s for their armor", armor_uti.base_item)

                body_row: TwoDARow = baseitems.get_row(armor_uti.base_item, context=f"Fetching armor base item row{context_base}")
                body_cell: str = body_row.get_string("bodyvar", context=f"Fetching 'bodyvar'{context_base}")
                log.debug("baseitems.2da: 'bodyvar' cell: %s", body_cell)

                # Determine model and texture columns
                armor_variation: str = body_cell.lower()
                model_column = f"model{armor_variation}"
                evil_tex_column = f"tex{armor_variation}evil"
                tex_column = (
                    evil_tex_column
                    if utc.alignment <= 25  # noqa: PLR2004
                    and evil_tex_column in appearance.get_headers()
                    else f"tex{armor_variation}"
                )
                tex_append = str(armor_uti.texture_variation).rjust(2, "0")

                body_model = utc_appearance_row.get_string(model_column, context=f"Fetching model column{context_base}")
                override_texture = utc_appearance_row.get_string(tex_column, context=f"Fetching texture column{context_base}")

        log.debug("appearance.2da's texture column: '%s'", tex_column)
        log.debug("override_texture name: '%s'", override_texture)

        # Process override texture
        if override_texture and override_texture.strip() and override_texture != "****":
            fallback_override_texture: str = override_texture + tex_append
            if tex_append != "01" and installation.texture(fallback_override_texture) is None:
                fallback_override_texture = f"{override_texture}01"
                log.debug(
                    "override texture '%s' not found, appending '01' to the end like the game itself would do.",
                    fallback_override_texture,
                )
            override_texture = fallback_override_texture
        else:
            override_texture = None
        log.debug(
            "Final override texture name (from appearance.2da's '%s' column): '%s'",
            tex_column,
            override_texture,
        )
        log.debug(
            "Final body model name (from appearance.2da's '%s' column): '%s'",
            model_column,
            body_model,
        )

    # Fallback to 'race' column if body_model is empty or invalid
    if not body_model or not body_model.strip() or body_model == "****":
        body_model = utc_appearance_row.get_string("race", context=f"Fetching 'race' column{context_base}")
        log.debug("body model name (from appearance.2da's 'race' column): '%s'", body_model)

    normalized_model = body_model.strip() if body_model and body_model.strip() else None
    normalized_texture = override_texture.strip() if override_texture and override_texture.strip() else None
    return normalized_model, normalized_texture


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
        appearance_lookup: ResourceResult | None = installation.resource("appearance", ResourceType.TwoDA)
        if not appearance_lookup:
            RobustLogger().error("appearance.2da missing from installation.")
            return None, None
        appearance = read_2da(appearance_lookup.data)
    if baseitems is None:
        baseitems_lookup: ResourceResult | None = installation.resource("baseitems", ResourceType.TwoDA)
        if not baseitems_lookup:
            RobustLogger().error("baseitems.2da missing from installation.")
            return None, None
        baseitems = read_2da(baseitems_lookup.data)

    right_hand_model: str | None = _load_hand_uti(installation, str(utc.equipment[EquipmentSlot.RIGHT_HAND].resref), baseitems) if EquipmentSlot.RIGHT_HAND in utc.equipment else None
    left_hand_model: str | None = _load_hand_uti(installation, str(utc.equipment[EquipmentSlot.LEFT_HAND].resref), baseitems) if EquipmentSlot.LEFT_HAND in utc.equipment else None
    return right_hand_model, left_hand_model


def _load_hand_uti(
    installation: Installation,
    hand_resref: str,
    baseitems: TwoDA,
) -> str | None:
    hand_lookup: ResourceResult | None = installation.resource(hand_resref, ResourceType.UTI)
    if not hand_lookup:
        RobustLogger().error(f"{hand_resref}.uti missing from installation.")
        return None
    hand_uti: UTI = read_uti(hand_lookup.data)
    default_model: str = baseitems.get_row(hand_uti.base_item).get_string("defaultmodel")
    return default_model.replace(
        "001",
        str(hand_uti.model_variation).rjust(3, "0"),
    ).strip()


def get_head_model(  # noqa: C901, PLR0912
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
        appearance_lookup: ResourceResult | None = installation.resource("appearance", ResourceType.TwoDA)
        if not appearance_lookup:
            RobustLogger().error("appearance.2da missing from installation.")
            return None, None
        appearance = read_2da(appearance_lookup.data)
    if heads is None:
        heads_lookup: ResourceResult | None = installation.resource("heads", ResourceType.TwoDA)
        if not heads_lookup:
            RobustLogger().error("heads.2da missing from installation.")
            return None, None
        heads = read_2da(heads_lookup.data)

    model: str | None = None
    texture: str | None = None

    head_id: int | None = appearance.get_row(utc.appearance_id).get_integer("normalhead")
    if head_id is not None:
        try:
            head_row: TwoDARow = heads.get_row(head_id)
        except IndexError:
            RobustLogger().error(
                "Row %s missing from heads.2da, defined in appearance.2da under the column 'normalhead' row %s",
                head_id,
                utc.appearance_id,
                exc_info=True,
            )
        model = head_row.get_string("head")
        head_column_name: str | None = None
        if utc.alignment < 10:  # noqa: PLR2004
            head_column_name = "headtexvvve"
        elif utc.alignment < 20:  # noqa: PLR2004
            head_column_name = "headtexvve"
        elif utc.alignment < 30:  # noqa: PLR2004
            head_column_name = "headtexve"
        elif utc.alignment < 40:  # noqa: PLR2004
            head_column_name = "headtexe"
        elif "alttexture" in heads.get_headers():
            if not installation.game().is_k2():  # TSL only override.
                RobustLogger().error("'alttexture' column in heads.2da should never exist in a K1 installation.")
            else:
                head_column_name = "alttexture"
        if head_column_name is not None:
            try:
                texture = head_row.get_string(head_column_name)
                texture = texture if texture and texture.strip() else None
            except KeyError:
                RobustLogger().error("Cannot find %s in heads.2da", head_column_name, exc_info=True)

    return model, texture


def get_mask_model(
    utc: UTC,
    installation: Installation,
) -> str | None:
    model: str | None = None

    head_equip: InventoryItem | None = utc.equipment.get(EquipmentSlot.HEAD)
    if head_equip is not None:
        resref: ResRef = head_equip.resref
        if not resref:
            return None
        resource: ResourceResult | None = installation.resource(str(resref), ResourceType.UTI)
        if resource is None:
            return None
        uti: UTI = read_uti(resource.data)
        model = "I_Mask_" + str(uti.model_variation).rjust(3, "0")

    return model and model.strip()
