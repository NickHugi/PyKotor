from __future__ import annotations

import os
import pathlib
import sys
import unittest

from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.common.misc import EquipmentSlot, Game
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utc import construct_utc, dismantle_utc
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utc import UTC

TEST_UTC_XML = """<gff3>
  <struct id="-1">
    <resref label="TemplateResRef">n_minecoorta</resref>
    <byte label="Race">6</byte>
    <byte label="SubraceIndex">1</byte>
    <locstring label="FirstName" strref="76046" />
    <locstring label="LastName" strref="123" />
    <uint16 label="Appearance_Type">636</uint16>
    <byte label="Gender">2</byte>
    <sint32 label="Phenotype">0</sint32>
    <uint16 label="PortraitId">1</uint16>
    <locstring label="Description" strref="123" />
    <exostring label="Tag">Coorta</exostring>
    <resref label="Conversation">coorta</resref>
    <byte label="IsPC">1</byte>
    <uint16 label="FactionID">5</uint16>
    <byte label="Disarmable">1</byte>
    <exostring label="Subrace" />
    <exostring label="Deity" />
    <uint16 label="SoundSetFile">46</uint16>
    <byte label="Plot">1</byte>
    <byte label="Interruptable">1</byte>
    <byte label="NoPermDeath">1</byte>
    <byte label="NotReorienting">1</byte>
    <byte label="BodyBag">1</byte>
    <byte label="BodyVariation">1</byte>
    <byte label="TextureVar">1</byte>
    <byte label="Min1HP">1</byte>
    <byte label="PartyInteract">1</byte>
    <byte label="Hologram">1</byte>
    <byte label="IgnoreCrePath">1</byte>
    <byte label="MultiplierSet">3</byte>
    <byte label="Str">10</byte>
    <byte label="Dex">10</byte>
    <byte label="Con">10</byte>
    <byte label="Int">10</byte>
    <byte label="Wis">10</byte>
    <byte label="Cha">10</byte>
    <sint32 label="WalkRate">7</sint32>
    <byte label="NaturalAC">1</byte>
    <sint16 label="HitPoints">8</sint16>
    <sint16 label="CurrentHitPoints">8</sint16>
    <sint16 label="MaxHitPoints">8</sint16>
    <sint16 label="ForcePoints">1</sint16>
    <sint16 label="CurrentForce">1</sint16>
    <sint16 label="refbonus">1</sint16>
    <sint16 label="willbonus">1</sint16>
    <sint16 label="fortbonus">1</sint16>
    <byte label="GoodEvil">50</byte>
    <byte label="LawfulChaotic">0</byte>
    <float label="BlindSpot">120.0</float>
    <float label="ChallengeRating">1.0</float>
    <byte label="PerceptionRange">11</byte>
    <resref label="ScriptHeartbeat">k_def_heartbt01</resref>
    <resref label="ScriptOnNotice">k_def_percept01</resref>
    <resref label="ScriptSpellAt">k_def_spellat01</resref>
    <resref label="ScriptAttacked">k_def_attacked01</resref>
    <resref label="ScriptDamaged">k_def_damage01</resref>
    <resref label="ScriptDisturbed">k_def_disturb01</resref>
    <resref label="ScriptEndRound">k_def_combend01</resref>
    <resref label="ScriptEndDialogu">k_def_endconv</resref>
    <resref label="ScriptDialogue">k_def_dialogue01</resref>
    <resref label="ScriptSpawn">k_def_spawn01</resref>
    <resref label="ScriptRested" />
    <resref label="ScriptDeath">k_def_death01</resref>
    <resref label="ScriptUserDefine">k_def_userdef01</resref>
    <resref label="ScriptOnBlocked">k_def_blocked01</resref>
    <list label="SkillList">
      <struct id="0">
        <byte label="Rank">1</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">2</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">3</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">4</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">5</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">6</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">7</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">8</byte>
        </struct>
      </list>
    <list label="FeatList">
      <struct id="1">
        <uint16 label="Feat">93</uint16>
        </struct>
      <struct id="1">
        <uint16 label="Feat">94</uint16>
        </struct>
      </list>
    <list label="TemplateList" />
    <list label="SpecAbilityList" />
    <list label="ClassList">
      <struct id="2">
        <sint32 label="Class">0</sint32>
        <sint16 label="ClassLevel">2</sint16>
        <list label="KnownList0">
          <struct id="3">
            <uint16 label="Spell">7</uint16>
            <byte label="SpellMetaMagic">0</byte>
            <byte label="SpellFlags">1</byte>
            </struct>
          </list>
        </struct>
      <struct id="2">
        <sint32 label="Class">1</sint32>
        <sint16 label="ClassLevel">3</sint16>
        <list label="KnownList0">
          <struct id="3">
            <uint16 label="Spell">9</uint16>
            <byte label="SpellMetaMagic">0</byte>
            <byte label="SpellFlags">1</byte>
            </struct>
          <struct id="3">
            <uint16 label="Spell">11</uint16>
            <byte label="SpellMetaMagic">0</byte>
            <byte label="SpellFlags">1</byte>
            </struct>
          </list>
        </struct>
      </list>
    <list label="Equip_ItemList">
      <struct id="2">
        <resref label="EquippedRes">mineruniform</resref>
        <byte label="Dropable">1</byte>
        </struct>
      <struct id="131072">
        <resref label="EquippedRes">g_i_crhide008</resref>
        </struct>
      </list>
    <byte label="PaletteID">3</byte>
    <exostring label="Comment">comment</exostring>
    <list label="ItemList">
      <struct id="0">
        <resref label="InventoryRes">g_w_thermldet01</resref>
        <uint16 label="Repos_PosX">0</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        <byte label="Dropable">1</byte>
        </struct>
      <struct id="1">
        <resref label="InventoryRes">g_w_thermldet01</resref>
        <uint16 label="Repos_PosX">1</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      <struct id="2">
        <resref label="InventoryRes">g_w_thermldet01</resref>
        <uint16 label="Repos_PosX">2</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      <struct id="3">
        <resref label="InventoryRes">g_w_thermldet02</resref>
        <uint16 label="Repos_PosX">3</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      </list>
    </struct>
  </gff3>
"""


class TestUTC(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_io_construct(self):
        gff = read_gff(TEST_UTC_XML.encode(), file_format=ResourceType.GFF_XML)
        utc = construct_utc(gff)
        self.validate_io(utc)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTC_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_utc(construct_utc(gff))
        utc = construct_utc(gff)
        self.validate_io(utc)

    def validate_io(self, utc: UTC):
        self.assertEqual(636, utc.appearance_id)
        self.assertEqual(1, utc.body_variation)
        self.assertEqual(120.0, utc.blindspot)
        self.assertEqual(10, utc.charisma)
        self.assertEqual(1.0, utc.challenge_rating)
        self.assertEqual("comment", utc.comment)
        self.assertEqual(10, utc.constitution)
        self.assertEqual("coorta", utc.conversation)
        self.assertEqual(1, utc.fp)
        self.assertEqual(8, utc.current_hp)
        self.assertEqual(10, utc.dexterity)
        self.assertTrue(utc.disarmable)
        self.assertEqual(5, utc.faction_id)
        self.assertEqual(76046, utc.first_name.stringref)
        self.assertEqual(1, utc.max_fp)
        self.assertEqual(2, utc.gender_id)
        self.assertEqual(50, utc.alignment)
        self.assertEqual(8, utc.hp)
        self.assertTrue(utc.hologram)
        self.assertTrue(utc.ignore_cre_path)
        self.assertEqual(10, utc.intelligence)
        self.assertTrue(utc.interruptable)
        self.assertTrue(utc.is_pc)
        self.assertEqual(123, utc.last_name.stringref)
        self.assertEqual(8, utc.max_hp)
        self.assertTrue(utc.min1_hp)
        self.assertEqual(3, utc.multiplier_set)
        self.assertEqual(1, utc.natural_ac)
        self.assertTrue(utc.no_perm_death)
        self.assertTrue(utc.not_reorienting)
        self.assertTrue(utc.party_interact)
        self.assertEqual(11, utc.perception_id)
        self.assertTrue(utc.plot)
        self.assertEqual(1, utc.portrait_id)
        self.assertEqual(6, utc.race_id)
        self.assertEqual("k_def_attacked01", utc.on_attacked)
        self.assertEqual("k_def_damage01", utc.on_damaged)
        self.assertEqual("k_def_death01", utc.on_death)
        self.assertEqual("k_def_dialogue01", utc.on_dialog)
        self.assertEqual("k_def_disturb01", utc.on_disturbed)
        self.assertEqual("k_def_endconv", utc.on_end_dialog)
        self.assertEqual("k_def_combend01", utc.on_end_round)
        self.assertEqual("k_def_heartbt01", utc.on_heartbeat)
        self.assertEqual("k_def_blocked01", utc.on_blocked)
        self.assertEqual("k_def_percept01", utc.on_notice)
        self.assertEqual("k_def_spawn01", utc.on_spawn)
        self.assertEqual("k_def_spellat01", utc.on_spell)
        self.assertEqual("k_def_userdef01", utc.on_user_defined)
        self.assertEqual(46, utc.soundset_id)
        self.assertEqual(10, utc.strength)
        self.assertEqual(1, utc.subrace_id)
        self.assertEqual("Coorta", utc.tag)
        self.assertEqual("n_minecoorta", utc.resref)
        self.assertEqual(1, utc.texture_variation)
        self.assertEqual(7, utc.walkrate_id)
        self.assertEqual(10, utc.wisdom)
        self.assertEqual(1, utc.fortitude_bonus)
        self.assertEqual(1, utc.reflex_bonus)
        self.assertEqual(1, utc.willpower_bonus)

        self.assertEqual(2, len(utc.classes))
        self.assertEqual(1, utc.classes[1].class_id)
        self.assertEqual(3, utc.classes[1].class_level)
        self.assertEqual(2, len(utc.classes[1].powers))
        self.assertEqual(9, utc.classes[1].powers[0])

        self.assertEqual(2, len(utc.equipment.items()))
        self.assertEqual("mineruniform", utc.equipment[EquipmentSlot.ARMOR].resref)
        self.assertTrue(utc.equipment[EquipmentSlot.ARMOR].droppable)
        self.assertEqual("g_i_crhide008", utc.equipment[EquipmentSlot.HIDE].resref)
        self.assertFalse(utc.equipment[EquipmentSlot.HIDE].droppable)

        self.assertEqual(2, len(utc.feats))
        self.assertEqual(94, utc.feats[1])

        self.assertEqual(4, len(utc.inventory))
        self.assertTrue(utc.inventory[0].droppable)
        self.assertFalse(utc.inventory[1].droppable)
        self.assertEqual("g_w_thermldet01", utc.inventory[1].resref)

        self.assertEqual(1, utc.computer_use)
        self.assertEqual(2, utc.demolitions)
        self.assertEqual(3, utc.stealth)
        self.assertEqual(4, utc.awareness)
        self.assertEqual(5, utc.persuade)
        self.assertEqual(6, utc.repair)
        self.assertEqual(7, utc.security)
        self.assertEqual(8, utc.treat_injury)


if __name__ == "__main__":
    unittest.main()
