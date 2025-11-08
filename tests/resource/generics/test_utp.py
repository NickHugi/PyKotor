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

from pykotor.common.misc import Game
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utp import construct_utp, dismantle_utp
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utp import UTP

TEST_UTP_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">SecLoc</exostring>
    <locstring label="LocName" strref="74450" />
    <locstring label="Description" strref="-1" />
    <resref label="TemplateResRef">lockerlg002</resref>
    <byte label="AutoRemoveKey">1</byte>
    <byte label="CloseLockDC">13</byte>
    <resref label="Conversation">conversation</resref>
    <byte label="Interruptable">1</byte>
    <uint32 label="Faction">1</uint32>
    <byte label="Plot">1</byte>
    <byte label="NotBlastable">1</byte>
    <byte label="Min1HP">1</byte>
    <byte label="KeyRequired">1</byte>
    <byte label="Lockable">0</byte>
    <byte label="Locked">1</byte>
    <byte label="OpenLockDC">28</byte>
    <byte label="OpenLockDiff">1</byte>
    <char label="OpenLockDiffMod">1</char>
    <uint16 label="PortraitId">0</uint16>
    <byte label="TrapDetectable">1</byte>
    <byte label="TrapDetectDC">0</byte>
    <byte label="TrapDisarmable">1</byte>
    <byte label="DisarmDC">15</byte>
    <byte label="TrapFlag">0</byte>
    <byte label="TrapOneShot">1</byte>
    <byte label="TrapType">0</byte>
    <exostring label="KeyName">somekey</exostring>
    <byte label="AnimationState">2</byte>
    <uint32 label="Appearance">67</uint32>
    <sint16 label="HP">15</sint16>
    <sint16 label="CurrentHP">15</sint16>
    <byte label="Hardness">5</byte>
    <byte label="Fort">16</byte>
    <byte label="Ref">0</byte>
    <byte label="Will">0</byte>
    <resref label="OnClosed">onclosed</resref>
    <resref label="OnDamaged">ondamaged</resref>
    <resref label="OnDeath">ondeath</resref>
    <resref label="OnDisarm">ondisarm</resref>
    <resref label="OnHeartbeat">onheartbeat</resref>
    <resref label="OnLock">onlock</resref>
    <resref label="OnMeleeAttacked">onmeleeattacked</resref>
    <resref label="OnOpen">onopen</resref>
    <resref label="OnSpellCastAt">onspellcastat</resref>
    <resref label="OnTrapTriggered" />
    <resref label="OnUnlock">onunlock</resref>
    <resref label="OnUserDefined">onuserdefined</resref>
    <byte label="HasInventory">1</byte>
    <byte label="PartyInteract">1</byte>
    <byte label="BodyBag">0</byte>
    <byte label="Static">1</byte>
    <byte label="Type">0</byte>
    <byte label="Useable">1</byte>
    <resref label="OnEndDialogue">onenddialogue</resref>
    <resref label="OnInvDisturbed">oninvdisturbed</resref>
    <resref label="OnUsed">onused</resref>
    <resref label="OnFailToOpen">onfailtoopen</resref>
    <list label="ItemList">
      <struct id="0">
        <resref label="InventoryRes">g_w_iongren01</resref>
        <uint16 label="Repos_PosX">0</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      <struct id="1">
        <resref label="InventoryRes">g_w_iongren02</resref>
        <uint16 label="Repos_PosX">1</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        <byte label="Dropable">1</byte>
        </struct>
      </list>
    <byte label="PaletteID">6</byte>
    <exostring label="Comment">Large standup locker</exostring>
    </struct>
  </gff3>
"""


class Test(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_io_construct(self):
        gff = read_gff(TEST_UTP_XML.encode(), file_format=ResourceType.GFF_XML)
        utp = construct_utp(gff)
        self.validate_io(utp)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTP_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_utp(construct_utp(gff))
        utp = construct_utp(gff)
        self.validate_io(utp)

    def validate_io(self, utp: UTP):
        self.assertEqual("SecLoc", utp.tag)
        self.assertEqual(74450, utp.name.stringref)
        self.assertEqual("lockerlg002", utp.resref)
        self.assertEqual(1, utp.auto_remove_key)
        self.assertEqual(13, utp.lock_dc)
        self.assertEqual("conversation", utp.conversation)
        self.assertEqual(1, utp.faction_id)
        self.assertEqual(1, utp.plot)
        self.assertEqual(1, utp.not_blastable)
        self.assertEqual(1, utp.min1_hp)
        self.assertEqual(1, utp.key_required)
        self.assertEqual(0, utp.lockable)
        self.assertEqual(1, utp.locked)
        self.assertEqual(28, utp.unlock_dc)
        self.assertEqual(1, utp.unlock_diff)
        self.assertEqual(1, utp.unlock_diff_mod)
        self.assertEqual("somekey", utp.key_name)
        self.assertEqual(2, utp.animation_state)
        self.assertEqual(67, utp.appearance_id)
        self.assertEqual(1, utp.min1_hp)
        self.assertEqual(15, utp.current_hp)
        self.assertEqual(5, utp.hardness)
        self.assertEqual(16, utp.fortitude)
        self.assertEqual("lockerlg002", utp.resref)
        self.assertEqual("onclosed", utp.on_closed)
        self.assertEqual("ondamaged", utp.on_damaged)
        self.assertEqual("ondeath", utp.on_death)
        self.assertEqual("onheartbeat", utp.on_heartbeat)
        self.assertEqual("onlock", utp.on_lock)
        self.assertEqual("onmeleeattacked", utp.on_melee_attack)
        self.assertEqual("onopen", utp.on_open)
        self.assertEqual("onspellcastat", utp.on_force_power)
        self.assertEqual("onunlock", utp.on_unlock)
        self.assertEqual("onuserdefined", utp.on_user_defined)
        self.assertEqual(1, utp.has_inventory)
        self.assertEqual(1, utp.party_interact)
        self.assertEqual(1, utp.static)
        self.assertEqual(1, utp.useable)
        self.assertEqual("onenddialogue", utp.on_end_dialog)
        self.assertEqual("oninvdisturbed", utp.on_inventory)
        self.assertEqual("onused", utp.on_used)
        self.assertEqual("onfailtoopen", utp.on_open_failed)
        self.assertEqual("Large standup locker", utp.comment)
        self.assertEqual(-1, utp.description.stringref)
        self.assertEqual(1, utp.interruptable)
        self.assertEqual(0, utp.portrait_id)
        self.assertEqual(1, utp.trap_detectable)
        self.assertEqual(0, utp.trap_detect_dc)
        self.assertEqual(1, utp.trap_disarmable)
        self.assertEqual(15, utp.trap_disarm_dc)
        self.assertEqual(0, utp.trap_flag)
        self.assertEqual(1, utp.trap_one_shot)
        self.assertEqual(0, utp.trap_type)
        self.assertEqual(0, utp.will)
        self.assertEqual("ondisarm", utp.on_disarm)
        self.assertEqual("", utp.on_trap_triggered)
        self.assertEqual(0, utp.bodybag_id)
        self.assertEqual(0, utp.trap_type)
        self.assertEqual(6, utp.palette_id)

        self.assertEqual(2, len(utp.inventory))
        self.assertFalse(utp.inventory[0].droppable)
        self.assertTrue(utp.inventory[1].droppable)
        self.assertEqual("g_w_iongren02", utp.inventory[1].resref)


if __name__ == "__main__":
    unittest.main()
