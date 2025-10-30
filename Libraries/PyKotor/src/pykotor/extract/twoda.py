from __future__ import annotations

import traceback

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, NamedTuple

# Import for runtime usage
from pykotor.extract.file import ResourceIdentifier  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.gff.gff_data import GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.type import ResourceType
from utility.system.path import PurePath

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.common.misc import Game
    from pykotor.extract.file import FileResource
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.twoda.twoda_data import TwoDARow
    from pykotor.tools.path import CaseAwarePath


class LookupResult2DA(NamedTuple):
    filepath: CaseAwarePath
    row_index: int
    column_name: str
    contents: str
    entire_row: TwoDARow


@dataclass(frozen=True, init=False, repr=False)
class K1ResRef2DAColumns:
    ...


class ABSColumns2DA:

    @classmethod
    def as_dict(cls) -> dict[str, set[str]]:
        # HACK(th3w1zard1): Include only attributes that are defined in the current class and are not methods or private
        parent_attrs: set[str] = set(dir(cls.__base__))
        current_attrs: set[str] = set(dir(cls)) - parent_attrs
        this_dict: dict[str, set[str]] = {}
        for k in current_attrs:
            v = cls.__dict__[k]
            if k.startswith("__") or callable(v):
                continue
            if isinstance(v, ABSColumns2DA):
                this_dict.update(v.as_dict())
            else:
                this_dict[f"{k}.2da"] = v
        return this_dict

    @classmethod
    def all_files(cls) -> set[str]:
        # HACK(th3w1zard): Include only attributes that are defined in the current class and are not methods or private
        parent_attrs: set[str] = set(dir(cls.__base__))
        current_attrs: set[str] = set(dir(cls)) - parent_attrs
        filenames: set[str] = set()
        for k in current_attrs:
            v = cls.__dict__[k]
            if k.startswith("__") or callable(v):
                continue
            if isinstance(v, ABSColumns2DA):
                filenames.update(v.all_files())
            else:
                filenames.add(f"{k}.2da")
        return filenames


class K1Columns2DA:
    @dataclass(frozen=True, init=False, repr=False)
    class StrRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a stringref in the TalkTable used by the first game."""
        actions: ClassVar[set[str]] = {"string_ref"}
        aiscripts: ClassVar[set[str]] = {"name_strref", "description_strref"}  # k1 only
        ambientsound: ClassVar[set[str]] = {"description"}
        appearance: ClassVar[set[str]] = {"string_ref"}
        bindablekeys: ClassVar[set[str]] = {"keynamestrref"}
        classes: ClassVar[set[str]] = {"name", "description"}
        crtemplates: ClassVar[set[str]] = {"strref"}
        creaturesize: ClassVar[set[str]] = {"strref"}
        doortypes: ClassVar[set[str]] = {"stringrefgame"}
        effecticons: ClassVar[set[str]] = {"strref"}
        encdifficulty: ClassVar[set[str]] = {"strref"}
        environment: ClassVar[set[str]] = {"strref"}
        feat: ClassVar[set[str]] = {"name", "description"}
        feedbacktext: ClassVar[set[str]] = {"strref"}
        fractionalcr: ClassVar[set[str]] = {"displaystrref"}
        gamespyrooms: ClassVar[set[str]] = {"str_ref"}
        genericdoors: ClassVar[set[str]] = {"strref"}
        hen_companion: ClassVar[set[str]] = {"strref"}
        iprp_abilities: ClassVar[set[str]] = {"name"}
        iprp_acmodtype: ClassVar[set[str]] = {"name"}
        iprp_aligngrp: ClassVar[set[str]] = {"name"}
        iprp_alignment: ClassVar[set[str]] = {"name"}
        iprp_ammocost: ClassVar[set[str]] = {"name"}
        iprp_ammotype: ClassVar[set[str]] = {"name"}
        iprp_amount: ClassVar[set[str]] = {"name"}  # ...
        iprp_bonuscost: ClassVar[set[str]] = {"name"}
        iprp_chargecost: ClassVar[set[str]] = {"name"}
        iprp_color: ClassVar[set[str]] = {"name"}
        iprp_combatdam: ClassVar[set[str]] = {"name"}
        iprp_damagecost: ClassVar[set[str]] = {"name"}
        iprp_damagetype: ClassVar[set[str]] = {"name"}
        iprp_damvulcost: ClassVar[set[str]] = {"name"}
        iprp_feats: ClassVar[set[str]] = {"name"}
        iprp_immuncost: ClassVar[set[str]] = {"name"}
        iprp_immunity: ClassVar[set[str]] = {"name"}
        iprp_lightcost: ClassVar[set[str]] = {"name"}
        iprp_meleecost: ClassVar[set[str]] = {"name"}
        iprp_monstcost: ClassVar[set[str]] = {"name"}
        iprp_monsterhit: ClassVar[set[str]] = {"name"}
        iprp_neg10cost: ClassVar[set[str]] = {"name"}
        iprp_neg5cost: ClassVar[set[str]] = {"name"}
        iprp_onhit: ClassVar[set[str]] = {"name"}
        iprp_onhitcost: ClassVar[set[str]] = {"name"}
        iprp_onhitdc: ClassVar[set[str]] = {"name"}
        iprp_onhitdur: ClassVar[set[str]] = {"name"}
        iprp_paramtable: ClassVar[set[str]] = {"name"}
        iprp_poison: ClassVar[set[str]] = {"name"}
        iprp_protection: ClassVar[set[str]] = {"name"}
        iprp_redcost: ClassVar[set[str]] = {"name"}
        iprp_resistcost: ClassVar[set[str]] = {"name"}
        iprp_saveelement: ClassVar[set[str]] = {"name"}
        iprp_savingthrow: ClassVar[set[str]] = {"name"}
        iprp_soakcost: ClassVar[set[str]] = {"name"}
        iprp_spellcost: ClassVar[set[str]] = {"name"}
        iprp_spellvcost: ClassVar[set[str]] = {"name"}
        iprp_spellvlimm: ClassVar[set[str]] = {"name"}
        iprp_spells: ClassVar[set[str]] = {"name"}
        iprp_spellshl: ClassVar[set[str]] = {"name"}
        iprp_srcost: ClassVar[set[str]] = {"name"}
        iprp_trapcost: ClassVar[set[str]] = {"name"}
        iprp_traps: ClassVar[set[str]] = {"name"}
        iprp_walk: ClassVar[set[str]] = {"name"}
        iprp_weightcost: ClassVar[set[str]] = {"name"}
        iprp_weightinc: ClassVar[set[str]] = {"name"}
        itempropdef: ClassVar[set[str]] = {"name"}
        itemprops: ClassVar[set[str]] = {"stringref"}
        keymap: ClassVar[set[str]] = {"actionstrref"}
        loadscreenhints: ClassVar[set[str]] = {"gameplayhint", "storyhint"}
        masterfeats: ClassVar[set[str]] = {"strref"}
        modulesave: ClassVar[set[str]] = {"areaname"}
        movies: ClassVar[set[str]] = {"strrefname", "strrefdesc"}
        placeables: ClassVar[set[str]] = {"strref"}
        planetary: ClassVar[set[str]] = {"name", "description"}
        soundset: ClassVar[set[str]] = {"strref"}
        stringtokens: ClassVar[set[str]] = {"strref1", "strref2", "strref3", "strref4"}
        texpacks: ClassVar[set[str]] = {"strrefname"}
        tutorial: ClassVar[set[str]] = {"message0", "message1", "message2"}
        tutorial_old: ClassVar[set[str]] = {"message0", "message1", "message2"}
        skills: ClassVar[set[str]] = {"name", "description"}
        spells: ClassVar[set[str]] = {"name", "spelldesc"}
        traps: ClassVar[set[str]] = {"trapname", "name"}

    @dataclass(frozen=True, init=False, repr=False)
    class ResRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a filestem used by the first game."""
        appearance: ClassVar[set[str]] = {"race"}
        droiddischarge: ClassVar[set[str]] = {">>##HEADER##<<"}
        hen_companion: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        hen_familiar: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        iprp_paramtable: ClassVar[set[str]] = {"tableresref"}
        itempropdef: ClassVar[set[str]] = {"subtyperesref", "param1resref", "gamestrref", "description"}
        minglobalrim: ClassVar[set[str]] = {"moduleresref"}
        modulesave: ClassVar[set[str]] = {"modulename"}

        @dataclass(frozen=True, init=False, repr=False)
        class Models(ABSColumns2DA):
            """All 2DA columns that reference model resrefs in the first game."""
            ammunitiontypes: ClassVar[set[str]] = {"model", "model0", "model1", "muzzleflash"}
            appearance: ClassVar[set[str]] = {"modela", "modelb", "modelc", "modeld", "modele", "modelf", "modelg", "modelh", "modeli", "modelj"}
            baseitems: ClassVar[set[str]] = {"defaultmodel"}
            placeables: ClassVar[set[str]] = {"modelname"}
            planetary: ClassVar[set[str]] = {"model"}
            upcrystals: ClassVar[set[str]] = {"shortmdlvar", "longmdlvar", "doublemdlvar"}

            @dataclass(frozen=True, init=False, repr=False)
            class Doors(ABSColumns2DA):
                """All 2DA columns that reference door model resrefs."""
                doortypes: ClassVar[set[str]] = {"model"}
                genericdoors: ClassVar[set[str]] = {"modelname"}

        @dataclass(frozen=True, init=False, repr=False)
        class Sounds(ABSColumns2DA):
            """All 2DA columns that reference sound resrefs."""
            aliensound: ClassVar[set[str]] = {"filename"}
            ambientsound: ClassVar[set[str]] = {"resource"}
            ammunitiontypes: ClassVar[set[str]] = {"shotsound0", "shotsound1", "impactsound0", "impactsound1"}
            appearancesndset: ClassVar[set[str]] = {"falldirt", "fallhard", "fallmetal", "fallwater"}
            baseitems: ClassVar[set[str]] = {"powerupsnd", "powerdownsnd", "poweredsnd"}
            footstepsounds: ClassVar[set[str]] = {"rolling",
                                                  "dirt0", "dirt1", "dirt2",
                                                  "grass0", "grass1", "grass2",
                                                  "stone0", "stone1", "stone2",
                                                  "wood0", "wood1", "wood2"
                                                  "water0", "water1", "water2"
                                                  "carpet0", "carpet1", "carpet2",
                                                  "metal0", "metal1", "metal2",
                                                  "puddles0", "puddles1", "puddles2",
                                                  "leaves0", "leaves1", "leaves2",
                                                  "force1", "force2", "force3"}  # TODO: Why are these the only ones different?
            grenadesnd: ClassVar[set[str]] = {"sound"}
            guisounds: ClassVar[set[str]] = {"soundresref"}
            inventorysnds: ClassVar[set[str]] = {"inventorysound"}

        @dataclass(frozen=True, init=False, repr=False)
        class Music(ABSColumns2DA):
            """All 2DA columns that reference music resrefs."""
            ambientmusic: ClassVar[set[str]] = {"resource", "stinger1", "stinger2", "stinger3"}
            loadscreens: ClassVar[set[str]] = {"musicresref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Textures(ABSColumns2DA):
            """All 2DA columns that reference texture resrefs."""
            actions: ClassVar[set[str]] = {"iconresref"}
            appearance: ClassVar[set[str]] = {"racetex", "texa", "texb", "texc", "texd", "texe", "texf", "texg", "texh", "texi", "texj",
                                              "headtexve", "headtexe", "headtexvg", "headtexg"}
            baseitems: ClassVar[set[str]] = {"defaulticon"}
            effecticon: ClassVar[set[str]] = {"iconresref"}
            heads: ClassVar[set[str]] = {"head", "headtexvvve", "headtexvve", "headtexve", "headtexe", "headtexg", "headtexvg"}
            iprp_spells: ClassVar[set[str]] = {"icon"}
            loadscreens: ClassVar[set[str]] = {"bmpresref"}
            planetary: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class Items(ABSColumns2DA):
            """All 2DA columns that reference item resrefs."""
            baseitems: ClassVar[set[str]] = {"itemclass", "baseitemstatref"}
            chargenclothes: ClassVar[set[str]] = {"itemresref"}
            feat: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class GUIs(ABSColumns2DA):
            """All 2DA columns that reference GUI resrefs."""
            cursors: ClassVar[set[str]] = {"resref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Scripts(ABSColumns2DA):
            """All 2DA columns that reference script resrefs."""
            areaeffects: ClassVar[set[str]] = {"onenter", "heartbeat", "onexit"}
            disease: ClassVar[set[str]] = {"end_incu_script", "24_hour_script"}
            spells: ClassVar[set[str]] = {"impactscript"}


class K2Columns2DA:
    @dataclass(frozen=True, init=False, repr=False)
    class StrRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a stringref in the TalkTable used by the second game."""
        aiscripts: ClassVar[set[str]] = {"name_strref"}
        ambientsound: ClassVar[set[str]] = {"description"}
        appearance: ClassVar[set[str]] = {"string_ref"}
        bindablekeys: ClassVar[set[str]] = {"keynamestrref"}
        classes: ClassVar[set[str]] = {"name", "description"}
        credits: ClassVar[set[str]] = {"name"}
        crtemplates: ClassVar[set[str]] = {"strref"}
        creaturesize: ClassVar[set[str]] = {"strref"}
        difficultyop: ClassVar[set[str]] = {"name"}
        disease: ClassVar[set[str]] = {"name"}
        doortypes: ClassVar[set[str]] = {"stringrefgame"}
        effecticons: ClassVar[set[str]] = {"strref"}
        encdifficulty: ClassVar[set[str]] = {"strref"}
        environment: ClassVar[set[str]] = {"strref"}
        feat: ClassVar[set[str]] = {"name", "description"}
        feedbacktext: ClassVar[set[str]] = {"strref"}
        fractionalcr: ClassVar[set[str]] = {"displaystrref"}
        gamespyrooms: ClassVar[set[str]] = {"str_ref"}
        genericdoors: ClassVar[set[str]] = {"strref"}
        hen_companion: ClassVar[set[str]] = {"strref"}
        iprp_abilities: ClassVar[set[str]] = {"name"}
        iprp_acmodtype: ClassVar[set[str]] = {"name"}
        iprp_aligngrp: ClassVar[set[str]] = {"name"}
        iprp_alignment: ClassVar[set[str]] = {"name"}
        iprp_ammocost: ClassVar[set[str]] = {"name"}
        iprp_ammotype: ClassVar[set[str]] = {"name"}
        iprp_amount: ClassVar[set[str]] = {"name"}  # ...
        iprp_bonuscost: ClassVar[set[str]] = {"name"}
        iprp_chargecost: ClassVar[set[str]] = {"name"}
        iprp_color: ClassVar[set[str]] = {"name"}
        iprp_combatdam: ClassVar[set[str]] = {"name"}
        iprp_damagecost: ClassVar[set[str]] = {"name"}
        iprp_damagetype: ClassVar[set[str]] = {"name"}
        iprp_damvulcost: ClassVar[set[str]] = {"name"}
        iprp_feats: ClassVar[set[str]] = {"name"}
        iprp_immuncost: ClassVar[set[str]] = {"name"}
        iprp_immunity: ClassVar[set[str]] = {"name"}
        iprp_lightcost: ClassVar[set[str]] = {"name"}
        iprp_meleecost: ClassVar[set[str]] = {"name"}
        iprp_monstcost: ClassVar[set[str]] = {"name"}
        iprp_monsterhit: ClassVar[set[str]] = {"name"}
        iprp_neg10cost: ClassVar[set[str]] = {"name"}
        iprp_neg5cost: ClassVar[set[str]] = {"name"}
        iprp_onhit: ClassVar[set[str]] = {"name"}
        iprp_onhitcost: ClassVar[set[str]] = {"name"}
        iprp_onhitdc: ClassVar[set[str]] = {"name"}
        iprp_onhitdur: ClassVar[set[str]] = {"name"}
        iprp_paramtable: ClassVar[set[str]] = {"name"}
        iprp_poison: ClassVar[set[str]] = {"name"}
        iprp_protection: ClassVar[set[str]] = {"name"}
        iprp_redcost: ClassVar[set[str]] = {"name"}
        iprp_resistcost: ClassVar[set[str]] = {"name"}
        iprp_saveelement: ClassVar[set[str]] = {"name"}
        iprp_savingthrow: ClassVar[set[str]] = {"name"}
        iprp_soakcost: ClassVar[set[str]] = {"name"}
        iprp_spellcost: ClassVar[set[str]] = {"name"}
        iprp_spellvcost: ClassVar[set[str]] = {"name"}
        iprp_spellvlimm: ClassVar[set[str]] = {"name"}
        iprp_spells: ClassVar[set[str]] = {"name"}
        iprp_spellshl: ClassVar[set[str]] = {"name"}
        iprp_srcost: ClassVar[set[str]] = {"name"}
        iprp_trapcost: ClassVar[set[str]] = {"name"}
        iprp_traps: ClassVar[set[str]] = {"name"}
        iprp_walk: ClassVar[set[str]] = {"name"}
        iprp_weightcost: ClassVar[set[str]] = {"name"}
        iprp_weightinc: ClassVar[set[str]] = {"name"}
        itempropdef: ClassVar[set[str]] = {"name"}
        itemprops: ClassVar[set[str]] = {"stringref"}
        keymap: ClassVar[set[str]] = {"actionstrref"}
        loadscreenhints: ClassVar[set[str]] = {"gameplayhint", "storyhint"}
        masterfeats: ClassVar[set[str]] = {"strref"}
        modulesave: ClassVar[set[str]] = {"areaname"}
        movies: ClassVar[set[str]] = {"strrefname", "strrefdesc"}
        placeables: ClassVar[set[str]] = {"strref"}
        planetary: ClassVar[set[str]] = {"name", "description"}
        soundset: ClassVar[set[str]] = {"strref"}
        stringtokens: ClassVar[set[str]] = {"strref1", "strref2", "strref3", "strref4"}
        texpacks: ClassVar[set[str]] = {"strrefname"}
        tutorial: ClassVar[set[str]] = {"message0", "message1", "message2"}
        tutorial_old: ClassVar[set[str]] = {"message0", "message1", "message2"}
        skills: ClassVar[set[str]] = {"name", "description"}
        spells: ClassVar[set[str]] = {"name", "spelldesc"}
        traps: ClassVar[set[str]] = {"trapname", "name"}

    @dataclass(frozen=True, init=False, repr=False)
    class ResRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a filestem."""
        ammunitiontypes: ClassVar[set[str]] = {"muzzleflash"}
        appearance: ClassVar[set[str]] = {"race"}
        droiddischarge: ClassVar[set[str]] = {">>##HEADER##<<"}
        hen_companion: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        hen_familiar: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        iprp_paramtable: ClassVar[set[str]] = {"tableresref"}
        itempropdef: ClassVar[set[str]] = {"subtyperesref", "param1resref", "gamestrref", "description"}
        minglobalrim: ClassVar[set[str]] = {"moduleresref"}
        modulesave: ClassVar[set[str]] = {"modulename"}

        @dataclass(frozen=True, init=False, repr=False)
        class Models(ABSColumns2DA):
            """All 2DA columns that reference model resrefs."""
            ammunitiontypes: ClassVar[set[str]] = {"model", "model0", "model1"}
            appearance: ClassVar[set[str]] = {"modela", "modelb", "modelc", "modeld", "modele", "modelf", "modelg", "modelh", "modeli", "modelj"}
            baseitems: ClassVar[set[str]] = {"defaultmodel"}
            placeables: ClassVar[set[str]] = {"modelname"}
            planetary: ClassVar[set[str]] = {"model"}
            upcrystals: ClassVar[set[str]] = {"shortmdlvar", "longmdlvar", "doublemdlvar"}

            @dataclass(frozen=True, init=False, repr=False)
            class Doors(ABSColumns2DA):
                doortypes: ClassVar[set[str]] = {"model"}
                genericdoors: ClassVar[set[str]] = {"modelname"}

        @dataclass(frozen=True, init=False, repr=False)
        class Sounds(ABSColumns2DA):
            """All 2DA columns that reference sound resrefs."""
            aliensound: ClassVar[set[str]] = {"filename"}
            alienvo: ClassVar[set[str]] = {"angry_long", "angry_medium", "angry_short",
                                           "comment_generic_long", "comment_generic_medium", "comment_generic_short",
                                           "greeting_medium", "greeting_short",
                                           "happy_thankful_long", "happy_thankful_medium", "happy_thankful_short",
                                           "laughter_normal", "laughter_mocking_medium", "laughter_mocking_short", "laughter_long", "laughter_short"
                                           "pleading_medium", "pleading_short",
                                           "question_long", "question_medium", "question_short",
                                           "sad_long", "sad_medium", "sad_short",
                                           "scared_long", "scared_medium", "scared_short",
                                           "seductive_long", "seductive_medium", "seductive_short",
                                           "silence",
                                           "wounded_medium", "wounded_small",
                                           "screaming_medium", "screaming_small"}
            ambientsound: ClassVar[set[str]] = {"resource"}
            ammunitiontypes: ClassVar[set[str]] = {"shotsound0", "shotsound1", "impactsound0", "impactsound1"}
            appearancesndset: ClassVar[set[str]] = {"falldirt", "fallhard", "fallmetal", "fallwater"}
            baseitems: ClassVar[set[str]] = {"powerupsnd", "powerdownsnd", "poweredsnd"}
            footstepsounds: ClassVar[set[str]] = {"rolling",
                                                  "dirt0", "dirt1", "dirt2",
                                                  "grass0", "grass1", "grass2",
                                                  "stone0", "stone1", "stone2",
                                                  "wood0", "wood1", "wood2"
                                                  "water0", "water1", "water2"
                                                  "carpet0", "carpet1", "carpet2",
                                                  "metal0", "metal1", "metal2",
                                                  "puddles0", "puddles1", "puddles2",
                                                  "leaves0", "leaves1", "leaves2",
                                                  "force1", "force2", "force3"}  # TODO: Why are these the only ones different?
            grenadesnd: ClassVar[set[str]] = {"sound"}
            guisounds: ClassVar[set[str]] = {"soundresref"}
            inventorysnds: ClassVar[set[str]] = {"inventorysound"}

            @dataclass(frozen=True, init=False, repr=False)
            class Music(ABSColumns2DA):
                """All 2DA columns that reference music resref sounds."""
                ambientmusic: ClassVar[set[str]] = {"resource", "stinger1", "stinger2", "stinger3"}
                loadscreens: ClassVar[set[str]] = {"musicresref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Textures(ABSColumns2DA):
            actions: ClassVar[set[str]] = {"iconresref"}
            appearance: ClassVar[set[str]] = {"racetex", "texa", "texb", "texc", "texd", "texe", "texf", "texg", "texh", "texi", "texj",
                                              "headtexve", "headtexe", "headtexvg", "headtexg"}
            cursors: ClassVar[set[str]] = {"resref"}
            baseitems: ClassVar[set[str]] = {"defaulticon"}
            effecticon: ClassVar[set[str]] = {"iconresref"}
            heads: ClassVar[set[str]] = {"head", "headtexvvve", "headtexvve", "headtexve", "headtexe", "headtexg", "headtexvg"}
            iprp_spells: ClassVar[set[str]] = {"icon"}
            loadscreens: ClassVar[set[str]] = {"bmpresref"}
            planetary: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class Items(ABSColumns2DA):
            """All 2DA columns that reference item resrefs."""
            baseitems: ClassVar[set[str]] = {"itemclass", "baseitemstatref"}
            chargenclothes: ClassVar[set[str]] = {"itemresref"}
            feat: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class GUIs(ABSColumns2DA):
            """All 2DA columns that reference GUI resrefs."""
            cursors: ClassVar[set[str]] = {"resref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Scripts(ABSColumns2DA):
            """All 2DA columns that reference script resrefs."""
            areaeffects: ClassVar[set[str]] = {"onenter", "heartbeat", "onexit"}
            disease: ClassVar[set[str]] = {"end_incu_script", "24_hour_script"}
            spells: ClassVar[set[str]] = {"impactscript"}



class TwoDARegistry:
    """Central registry for 2DA metadata, GFF mappings, and helpers."""

    # Canonical 2DA file names (single source of truth)
    PORTRAITS: ClassVar[str] = "portraits"
    APPEARANCES: ClassVar[str] = "appearance"
    SUBRACES: ClassVar[str] = "subrace"
    SPEEDS: ClassVar[str] = "creaturespeed"
    SOUNDSETS: ClassVar[str] = "soundset"
    FACTIONS: ClassVar[str] = "repute"
    GENDERS: ClassVar[str] = "gender"
    PERCEPTIONS: ClassVar[str] = "ranges"
    CLASSES: ClassVar[str] = "classes"
    FEATS: ClassVar[str] = "feat"
    POWERS: ClassVar[str] = "spells"
    BASEITEMS: ClassVar[str] = "baseitems"
    PLACEABLES: ClassVar[str] = "placeables"
    DOORS: ClassVar[str] = "genericdoors"
    CURSORS: ClassVar[str] = "cursors"
    TRAPS: ClassVar[str] = "traps"
    RACES: ClassVar[str] = "racialtypes"
    SKILLS: ClassVar[str] = "skills"
    UPGRADES: ClassVar[str] = "upgrade"
    ENC_DIFFICULTIES: ClassVar[str] = "encdifficulty"
    ITEM_PROPERTIES: ClassVar[str] = "itempropdef"
    IPRP_PARAMTABLE: ClassVar[str] = "iprp_paramtable"
    IPRP_COSTTABLE: ClassVar[str] = "iprp_costtable"
    IPRP_ABILITIES: ClassVar[str] = "iprp_abilities"
    IPRP_ALIGNGRP: ClassVar[str] = "iprp_aligngrp"
    IPRP_COMBATDAM: ClassVar[str] = "iprp_combatdam"
    IPRP_DAMAGETYPE: ClassVar[str] = "iprp_damagetype"
    IPRP_PROTECTION: ClassVar[str] = "iprp_protection"
    IPRP_ACMODTYPE: ClassVar[str] = "iprp_acmodtype"
    IPRP_IMMUNITY: ClassVar[str] = "iprp_immunity"
    IPRP_SAVEELEMENT: ClassVar[str] = "iprp_saveelement"
    IPRP_SAVINGTHROW: ClassVar[str] = "iprp_savingthrow"
    IPRP_ONHIT: ClassVar[str] = "iprp_onhit"
    IPRP_AMMOTYPE: ClassVar[str] = "iprp_ammotype"
    IPRP_MONSTERHIT: ClassVar[str] = "iprp_mosterhit"
    IPRP_WALK: ClassVar[str] = "iprp_walk"
    EMOTIONS: ClassVar[str] = "emotion"
    EXPRESSIONS: ClassVar[str] = "facialanim"
    VIDEO_EFFECTS: ClassVar[str] = "videoeffects"
    DIALOG_ANIMS: ClassVar[str] = "dialoganimations"
    PLANETS: ClassVar[str] = "planetary"
    PLOT: ClassVar[str] = "plot"
    CAMERAS: ClassVar[str] = "camerastyle"

    _STRREF_COLUMNS: ClassVar[dict[str, set[str]]] = {}
    _RESREF_COLUMNS: ClassVar[dict[str, set[str]]] = {}
    _GFF_FIELD_TO_2DA: ClassVar[dict[str, ResourceIdentifier]] = {}

    @classmethod
    def init_metadata(cls) -> None:
        if cls._GFF_FIELD_TO_2DA:
            return

        # Merge K1/K2 strref and resref columns into unified maps keyed by filename
        def merge_columns(root_cls: type[ABSColumns2DA]) -> dict[str, set[str]]:
            return root_cls.as_dict()

        cls._STRREF_COLUMNS = {}
        cls._STRREF_COLUMNS.update(merge_columns(K1Columns2DA.StrRefs))
        cls._STRREF_COLUMNS.update(merge_columns(K2Columns2DA.StrRefs))

        cls._RESREF_COLUMNS = {}
        cls._RESREF_COLUMNS.update(merge_columns(K1Columns2DA.ResRefs))
        cls._RESREF_COLUMNS.update(merge_columns(K2Columns2DA.ResRefs))

        # Centralize the GFF field mapping here
        cls._GFF_FIELD_TO_2DA = {
            "SoundSetFile": ResourceIdentifier(cls.SOUNDSETS, ResourceType.TwoDA),
            "PortraitId": ResourceIdentifier(cls.PORTRAITS, ResourceType.TwoDA),
            "Appearance_Type": ResourceIdentifier(cls.APPEARANCES, ResourceType.TwoDA),
            "Phenotype": ResourceIdentifier("phenotype", ResourceType.TwoDA),
            "FactionID": ResourceIdentifier(cls.FACTIONS, ResourceType.TwoDA),
            "Faction": ResourceIdentifier(cls.FACTIONS, ResourceType.TwoDA),
            "Subrace": ResourceIdentifier(cls.SUBRACES, ResourceType.TwoDA),
            "SubraceIndex": ResourceIdentifier(cls.SUBRACES, ResourceType.TwoDA),
            "Race": ResourceIdentifier(cls.RACES, ResourceType.TwoDA),
            "Class": ResourceIdentifier(cls.CLASSES, ResourceType.TwoDA),
            "Gender": ResourceIdentifier(cls.GENDERS, ResourceType.TwoDA),
            "PerceptionRange": ResourceIdentifier(cls.PERCEPTIONS, ResourceType.TwoDA),
            "WalkRate": ResourceIdentifier(cls.SPEEDS, ResourceType.TwoDA),
            "PaletteID": ResourceIdentifier("palette", ResourceType.TwoDA),
            "BodyBag": ResourceIdentifier("bodybag", ResourceType.TwoDA),
            "BaseItem": ResourceIdentifier(cls.BASEITEMS, ResourceType.TwoDA),
            "ModelVariation": ResourceIdentifier(cls.BASEITEMS, ResourceType.TwoDA),
            "BodyVariation": ResourceIdentifier("bodyvariation", ResourceType.TwoDA),
            "TextureVar": ResourceIdentifier("textures", ResourceType.TwoDA),
            "UpgradeType": ResourceIdentifier(cls.UPGRADES, ResourceType.TwoDA),
            "Appearance": ResourceIdentifier(cls.PLACEABLES, ResourceType.TwoDA),
            "GenericType": ResourceIdentifier(cls.DOORS, ResourceType.TwoDA),
            "Cursor": ResourceIdentifier(cls.CURSORS, ResourceType.TwoDA),
            "MusicDay": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "MusicNight": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "MusicBattle": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "MusicDelay": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "LoadScreenID": ResourceIdentifier("loadscreens", ResourceType.TwoDA),
            "CameraStyle": ResourceIdentifier(cls.CAMERAS, ResourceType.TwoDA),
            "Animation": ResourceIdentifier(cls.DIALOG_ANIMS, ResourceType.TwoDA),
            "Emotion": ResourceIdentifier(cls.EMOTIONS, ResourceType.TwoDA),
            "FacialAnim": ResourceIdentifier(cls.EXPRESSIONS, ResourceType.TwoDA),
            "AlienRaceOwner": ResourceIdentifier(cls.RACES, ResourceType.TwoDA),
            "AlienRaceNode": ResourceIdentifier(cls.RACES, ResourceType.TwoDA),
            "CamVidEffect": ResourceIdentifier(cls.VIDEO_EFFECTS, ResourceType.TwoDA),
            "CameraID": ResourceIdentifier(cls.CAMERAS, ResourceType.TwoDA),
            "Subtype": ResourceIdentifier(cls.POWERS, ResourceType.TwoDA),
            "SpellId": ResourceIdentifier(cls.POWERS, ResourceType.TwoDA),
            "Spell": ResourceIdentifier(cls.POWERS, ResourceType.TwoDA),
            "FeatID": ResourceIdentifier(cls.FEATS, ResourceType.TwoDA),
            "Feat": ResourceIdentifier(cls.FEATS, ResourceType.TwoDA),
            "SkillID": ResourceIdentifier(cls.SKILLS, ResourceType.TwoDA),
            "MarkUp": ResourceIdentifier("merchants", ResourceType.TwoDA),
            "MarkDown": ResourceIdentifier("merchants", ResourceType.TwoDA),
            "Difficulty": ResourceIdentifier(cls.ENC_DIFFICULTIES, ResourceType.TwoDA),
            "DifficultyIndex": ResourceIdentifier(cls.ENC_DIFFICULTIES, ResourceType.TwoDA),
            "TrapType": ResourceIdentifier(cls.TRAPS, ResourceType.TwoDA),
            "PlanetID": ResourceIdentifier(cls.PLANETS, ResourceType.TwoDA),
            "PlotIndex": ResourceIdentifier(cls.PLOT, ResourceType.TwoDA),
            "VideoResRef": ResourceIdentifier(cls.VIDEO_EFFECTS, ResourceType.TwoDA),
            "AIStyle": ResourceIdentifier("ai_styles", ResourceType.TwoDA),
            "DamageType": ResourceIdentifier(cls.IPRP_DAMAGETYPE, ResourceType.TwoDA),
            "DamageVsType": ResourceIdentifier("iprp_damagevs", ResourceType.TwoDA),
            "AttackModifier": ResourceIdentifier("iprp_attackmod", ResourceType.TwoDA),
            "ACModifierType": ResourceIdentifier(cls.IPRP_ACMODTYPE, ResourceType.TwoDA),
            "BonusFeatID": ResourceIdentifier("iprp_bonusfeat", ResourceType.TwoDA),
            "CastSpell": ResourceIdentifier("iprp_spells", ResourceType.TwoDA),
            "LightColor": ResourceIdentifier("iprp_lightcol", ResourceType.TwoDA),
            "MonsterDamage": ResourceIdentifier("iprp_monstdam", ResourceType.TwoDA),
            "OnHit": ResourceIdentifier(cls.IPRP_ONHIT, ResourceType.TwoDA),
            "Param1": ResourceIdentifier(cls.IPRP_PARAMTABLE, ResourceType.TwoDA),
            "Param1Value": ResourceIdentifier(cls.IPRP_PARAMTABLE, ResourceType.TwoDA),
            "SkillBonus": ResourceIdentifier("iprp_skillcost", ResourceType.TwoDA),
            "SpecialWalk": ResourceIdentifier(cls.IPRP_WALK, ResourceType.TwoDA),
            "WeightIncrease": ResourceIdentifier("iprp_weightinc", ResourceType.TwoDA),
            "Trap": ResourceIdentifier("iprp_traptype", ResourceType.TwoDA),
            "DamageReduction": ResourceIdentifier("iprp_damagered", ResourceType.TwoDA),
            "ImmunityType": ResourceIdentifier(cls.IPRP_IMMUNITY, ResourceType.TwoDA),
            "SavedGame": ResourceIdentifier("saves", ResourceType.TwoDA),
            "SaveType": ResourceIdentifier(cls.IPRP_SAVEELEMENT, ResourceType.TwoDA),
            "SpellResistance": ResourceIdentifier("iprp_spellres", ResourceType.TwoDA),
            "VisualType": ResourceIdentifier("visualeffects", ResourceType.TwoDA),
        }

    @classmethod
    def gff_field_mapping(cls) -> dict[str, ResourceIdentifier]:
        cls.init_metadata()
        return cls._GFF_FIELD_TO_2DA

    @classmethod
    def columns_for(cls, data_type: Literal["resref", "strref"]) -> dict[str, set[str]]:
        cls.init_metadata()
        return cls._STRREF_COLUMNS if data_type == "strref" else cls._RESREF_COLUMNS

    @classmethod
    def files(cls) -> set[str]:
        cls.init_metadata()
        files: set[str] = set(cls._STRREF_COLUMNS.keys()) | set(cls._RESREF_COLUMNS.keys())
        return files

class TwoDAManager:
    def __init__(self, installation: Installation):
        TwoDARegistry.init_metadata()
        self._installation: Installation = installation

    @classmethod
    def get_column_names(
        cls,
        data_type: Literal["resref", "strref"],
    ) -> list[str]:
        """Retrieve all column names for a given data type across known 2DA files."""
        result: list[str] = []
        for columns in TwoDARegistry.columns_for(data_type).values():
            result.extend(columns)
        return list(set(result))

    @classmethod
    def lookup(cls, query: str, data_type: str) -> LookupResult2DA | None:
        """Deprecated: use instance.lookup_in_installation."""
        return None

    def lookup_in_installation(self, query: str, data_type: Literal["resref", "strref"]) -> LookupResult2DA | None:
        from pykotor.resource.formats.twoda.twoda_auto import read_2da  # lazy import
        from pykotor.tools.path import CaseAwarePath

        if not query:
            return None

        targets = TwoDARegistry.columns_for(data_type)
        for filename, columns in targets.items():
            ident = ResourceIdentifier.identify(filename)
            result = self._installation.resource(ident.resname, ident.restype)
            if result is None or result.data is None:
                continue
            table = read_2da(result.data)
            for row_index in range(table.get_height()):
                row = table.get_row(row_index)
                for column in columns:
                    try:
                        cell = row.get_string(column)
                    except Exception:  # noqa: S112
                        continue
                    if cell == query:
                        return LookupResult2DA(
                            filepath=CaseAwarePath(f"{filename}"),
                            row_index=row_index,
                            column_name=column,
                            contents=cell or "",
                            entire_row=row,
                        )
        return None


# Logging disabled intentionally (no-op)
_log_level = 0


def _log_debug(msg: str) -> None:
    return


def _log_verbose(msg: str) -> None:
    return


# GFF field name to 2DA filename mappings
# Maps GFF field names to the 2DA files they reference
#
# Sources consulted for this mapping:
# - reone engine (C++): vendor/reone/src/libs/resource/parser/gff/*.cpp
#   Specifically: utc.cpp, uti.cpp, utd.cpp, utp.cpp, utt.cpp, ute.cpp, utm.cpp,
#                  are.cpp, git.cpp, ifo.cpp, dlg.cpp
# - HolocronToolset: Tools/HolocronToolset/src/toolset/data/installation.py
#   Constants like TwoDA_APPEARANCES, TwoDA_FACTIONS, etc.
# - KotOR.js (TypeScript): vendor/KotOR.js/src/resource/ (reference only)
# - xoreos (C++): vendor/xoreos/src/aurora/ (reference only)
#
# Note: Some fields are context-dependent (e.g. "Appearance" in doors vs placeables).
# The mapping should handle the most common case or be disambiguated by file type.
GFF_FIELD_TO_2DA_MAPPING: dict[str, ResourceIdentifier] = TwoDARegistry.gff_field_mapping()
    # mapping provided by TwoDARegistry


class TwoDAMemoryReferenceCache:
    """Cache of 2DA memory token references found during resource scanning.

    Maps (2da_filename, row_index) -> list of (resource_identifier, field_paths)
    where that row is referenced.

    This enables automatic generation of linking patches when 2DA rows are modified,
    similar to how StrRef linking works.
    """

    def __init__(self, game: Game):
        """Initialize cache.

        Args:
            game: Game instance (for potential game-specific logic)
        """
        self.game: Game = game

        # Map: (2da_filename, row_index) -> [(resource_identifier, [field_paths])]
        self._cache: dict[tuple[str, int], list[tuple[ResourceIdentifier, list[str]]]] = {}

        # Statistics
        self._total_references_found: int = 0
        self._files_with_2da_refs: set[str] = set()

    def scan_resource(
        self,
        resource: FileResource,
        data: bytes,
    ) -> None:
        """Scan a resource for 2DA memory references and cache them.

        Args:
            resource: FileResource being scanned
            data: Resource data bytes
        """
        identifier: ResourceIdentifier = resource.identifier()
        restype: ResourceType = resource.restype()

        try:
            # Only scan GFF files for 2DA references
            if restype in GFFContent.get_restypes():
                try:
                    gff_obj = read_gff(data)
                    self._scan_gff(identifier, gff_obj.root)
                except Exception as e:  # noqa: BLE001, S110
                    print(f"Not a valid GFF file or failed to parse: {identifier.resname}, skipping: {e.__class__.__name__}")
                    traceback.print_exc()

        except Exception:  # noqa: BLE001, S110
            # Skip files that fail to scan
            pass

    def _scan_gff(
        self,
        identifier: ResourceIdentifier,
        gff_struct: GFFStruct,
        current_path: PurePath | None = None,
    ) -> None:
        """Recursively scan GFF structure for 2DA references.

        Args:
            identifier: Resource identifier
            gff_struct: GFF struct to scan
            current_path: Current path in the GFF hierarchy
        """
        if current_path is None:
            current_path = PurePath()

        for label, field_type, value in gff_struct:
            field_path = current_path / label

            # Check if this field references a 2DA
            if label in GFF_FIELD_TO_2DA_MAPPING:
                # This field references a 2DA file
                twoda_identifier: ResourceIdentifier = GFF_FIELD_TO_2DA_MAPPING[label]
                twoda_filename = f"{twoda_identifier.resname}.{twoda_identifier.restype.extension}"

                # Extract the numeric value (row index)
                row_index: int | None = None
                if field_type in (
                    GFFFieldType.Int8,
                    GFFFieldType.Int16,
                    GFFFieldType.Int32,
                    GFFFieldType.Int64,
                ):
                    if isinstance(value, int):
                        row_index = value
                elif field_type in (
                    GFFFieldType.UInt8,
                    GFFFieldType.UInt16,
                    GFFFieldType.UInt32,
                    GFFFieldType.UInt64,
                ) and isinstance(value, int):
                    row_index = value

                if row_index is not None and row_index >= 0:
                    self._add_reference(twoda_filename, row_index, identifier, str(field_path))

            # Recurse into nested structures
            if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
                self._scan_gff(identifier, value, field_path)
            elif field_type == GFFFieldType.List and isinstance(value, GFFList):
                for idx, item in enumerate(value):
                    if isinstance(item, GFFStruct):
                        item_path = field_path / str(idx)
                        self._scan_gff(identifier, item, item_path)

    def _add_reference(
        self,
        twoda_filename: str,
        row_index: int,
        identifier: ResourceIdentifier,
        location: str,
    ) -> None:
        """Add a reference to the cache.

        Args:
            twoda_filename: Name of the 2DA file (e.g., "soundset.2da")
            row_index: Row index in the 2DA
            identifier: Resource identifier
            location: Field path in the GFF structure
        """
        key = (twoda_filename.lower(), row_index)

        if key not in self._cache:
            self._cache[key] = []

        # Check if this resource is already in the list
        for existing_identifier, locations in self._cache[key]:
            if existing_identifier == identifier:
                # Add location if not already present
                if location not in locations:
                    locations.append(location)
                    self._total_references_found += 1
                return

        # New resource for this 2DA row
        self._cache[key].append((identifier, [location]))
        self._files_with_2da_refs.add(identifier.resname)
        self._total_references_found += 1

    def get_references(
        self,
        twoda_filename: str,
        row_index: int,
    ) -> list[tuple[ResourceIdentifier, list[str]]]:
        """Get all references to a specific 2DA row.

        Args:
            twoda_filename: Name of the 2DA file
            row_index: Row index in the 2DA

        Returns:
            List of (resource_identifier, field_paths) tuples
        """
        key = (twoda_filename.lower(), row_index)
        return self._cache.get(key, [])

    def has_references(
        self,
        twoda_filename: str,
        row_index: int,
    ) -> bool:
        """Check if any resources reference this 2DA row.

        Args:
            twoda_filename: Name of the 2DA file
            row_index: Row index in the 2DA

        Returns:
            True if references exist
        """
        key = (twoda_filename.lower(), row_index)
        return key in self._cache

    def get_statistics(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        unique_2da_refs = len(self._cache)
        return {
            "unique_2da_refs": unique_2da_refs,
            "total_references": self._total_references_found,
            "files_with_2da_refs": len(self._files_with_2da_refs),
        }

    def log_summary(self) -> None:
        """Log a summary of cache contents."""
        stats = self.get_statistics()
        _log_verbose(f"2DA Memory Reference Cache: {stats['unique_2da_refs']} unique 2DA rows referenced")
        _log_verbose(f"  Total references: {stats['total_references']}")
        _log_verbose(f"  Files with 2DA refs: {stats['files_with_2da_refs']}")

    def to_dict(self) -> dict[str, list[dict[str, str | int | list[str]]]]:
        """Serialize cache to dictionary for saving.

        Returns:
            Serialized cache data
        """
        result: dict[str, list[dict[str, str | int | list[str]]]] = {}

        for (twoda_filename, row_index), references in self._cache.items():
            key = f"{twoda_filename}:{row_index}"
            result[key] = [
                {
                    "resname": ref_id.resname,
                    "restype": ref_id.restype.extension,
                    "locations": locations,
                }
                for ref_id, locations in references
            ]

        return result

    @classmethod
    def from_dict(
        cls,
        game: Game,
        data: dict[str, list[dict[str, str | int | list[str]]]],
    ) -> TwoDAMemoryReferenceCache:
        """Restore cache from serialized dictionary.

        Args:
            game: Game instance
            data: Serialized cache data

        Returns:
            Restored TwoDAMemoryReferenceCache
        """
        cache = cls(game)

        for key_str, references in data.items():
            # Parse key: "soundset.2da:123" -> ("soundset.2da", 123)
            twoda_filename, row_index_str = key_str.rsplit(":", 1)
            row_index = int(row_index_str)

            cache_key = (twoda_filename, row_index)
            cache._cache[cache_key] = []

            for ref_data in references:
                resname = ref_data["resname"]
                assert isinstance(resname, str)
                restype_ext = ref_data["restype"]
                assert isinstance(restype_ext, str)
                locations_data = ref_data["locations"]
                assert isinstance(locations_data, list)
                locations = [str(loc) for loc in locations_data]

                restype = ResourceType.from_extension(restype_ext)
                if restype is None or not restype.is_valid():
                    continue

                from pykotor.extract.file import ResourceIdentifier  # noqa: PLC0415

                identifier = ResourceIdentifier(resname, restype)

                cache._cache[cache_key].append((identifier, locations))
                cache._files_with_2da_refs.add(resname)
                cache._total_references_found += len(locations)

        return cache
