from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, NamedTuple

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
        # HACK: Include only attributes that are defined in the current class and are not methods or private
        parent_attrs = set(dir(cls.__base__))
        current_attrs = set(dir(cls)) - parent_attrs
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
        # HACK: Include only attributes that are defined in the current class and are not methods or private
        parent_attrs = set(dir(cls.__base__))
        current_attrs = set(dir(cls)) - parent_attrs
        filenames = set()
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
        aiscripts: ClassVar[set[str]] = {"name_strref", "description_strref"}
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
            ambientmusic: ClassVar[set[str]] = {"resource", "stinger1", "stinger2", "stinger3"}
            loadscreens: ClassVar[set[str]] = {"musicresref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Textures(ABSColumns2DA):
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
            baseitems: ClassVar[set[str]] = {"itemclass", "baseitemstatref"}
            chargenclothes: ClassVar[set[str]] = {"itemresref"}
            feat: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class GUIs(ABSColumns2DA):
            cursors: ClassVar[set[str]] = {"resref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Scripts(ABSColumns2DA):
            areaeffects: ClassVar[set[str]] = {"onenter", "heartbeat", "onexit"}
            disease: ClassVar[set[str]] = {"end_incu_script", "24_hour_script"}
            spells: ClassVar[set[str]] = {"impactscript"}



class TwoDAManager:
    def __init__(self, installation: Installation):
        self._installation: Installation = installation

    @classmethod
    def get_column_names(  # TODO:
        cls,
        data_type: Literal["resref", "strref"],
    ) -> list[str]:
        """Retrieve all column names for a given data type (stringrefs, resrefs, models)."""
        result = []
        for columns in cls.metadata.get(data_type, {}).values():
            result.extend(columns)
        return list(set(result))  # Remove duplicates

    @classmethod
    def lookup(cls, query: str, data_type: str) -> LookupResult2DA:  # TODO:
        """Perform a lookup based on a query and return a read-only result object."""
        # This method should implement retrieval logic, possibly involving reading from files or a database
        # For simplicity, the example returns a simple dummy object
        return LookupResult2DA()
