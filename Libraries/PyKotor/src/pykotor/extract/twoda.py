from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, NamedTuple

# Import for runtime usage
from pykotor.extract.file import ResourceIdentifier  # pyright: ignore[reportMissingImports]
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from typing_extensions import Literal

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
                """All 2DA columns that reference door model resrefs."""
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
            """All 2DA columns that reference texture resrefs."""
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
    """Central registry for 2DA metadata, GFF mappings, and helpers.
    
    This registry provides metadata about 2DA files, including which columns contain
    string references (StrRefs) or resource references (ResRefs). It also maps GFF fields
    to their corresponding 2DA lookup tables.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/2dareader.cpp (2DA reading)
        vendor/reone/include/reone/resource/format/2dareader.h (2DA structure)
        vendor/xoreos-tools/src/xml/2dadumper.cpp (2DA to XML conversion)
        vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/Kotor2DA.cs (2DA structure)
        vendor/KotOR.js/src/resource/TwoDAObject.ts (2DA loading)
        Note: This registry is PyKotor-specific for tooling and modding purposes.
        Vendor implementations typically read 2DA files directly without such metadata.
    """

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
    """Manager for 2DA file lookups within an installation.
    
    Provides methods to search for string references or resource references across
    all known 2DA files in a game installation.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/2dareader.cpp (2DA reading)
        vendor/xoreos-tools/src/xml/2dadumper.cpp (2DA extraction)
        Note: This manager is PyKotor-specific for tooling and modding purposes.
    """
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
