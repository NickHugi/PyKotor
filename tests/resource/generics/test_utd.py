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

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utd import construct_utd, dismantle_utd
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utd import UTD

TEST_UTD_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">TelosDoor13</exostring>
    <locstring label="LocName" strref="123731" />
    <locstring label="Description" strref="-1" />
    <resref label="TemplateResRef">door_tel014</resref>
    <byte label="AutoRemoveKey">1</byte>
    <byte label="CloseLockDC">0</byte>
    <resref label="Conversation">convoresref</resref>
    <byte label="Interruptable">1</byte>
    <uint32 label="Faction">1</uint32>
    <byte label="Plot">1</byte>
    <byte label="NotBlastable">1</byte>
    <byte label="Min1HP">1</byte>
    <byte label="KeyRequired">1</byte>
    <byte label="Lockable">1</byte>
    <byte label="Locked">1</byte>
    <byte label="OpenLockDC">28</byte>
    <byte label="OpenLockDiff">1</byte>
    <char label="OpenLockDiffMod">1</char>
    <uint16 label="PortraitId">0</uint16>
    <byte label="TrapDetectable">1</byte>
    <byte label="TrapDetectDC">0</byte>
    <byte label="TrapDisarmable">1</byte>
    <byte label="DisarmDC">28</byte>
    <byte label="TrapFlag">0</byte>
    <byte label="TrapOneShot">1</byte>
    <byte label="TrapType">2</byte>
    <exostring label="KeyName">keyname</exostring>
    <byte label="AnimationState">1</byte>
    <uint32 label="Appearance">1</uint32>
    <sint16 label="HP">20</sint16>
    <sint16 label="CurrentHP">60</sint16>
    <byte label="Hardness">5</byte>
    <byte label="Fort">28</byte>
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
    <resref label="OnTrapTriggered">ontraptriggered</resref>
    <resref label="OnUnlock">onunlock</resref>
    <resref label="OnUserDefined">onuserdefined</resref>
    <uint16 label="LoadScreenID">0</uint16>
    <byte label="GenericType">110</byte>
    <byte label="Static">1</byte>
    <byte label="OpenState">1</byte>
    <resref label="OnClick">onclick</resref>
    <resref label="OnFailToOpen">onfailtoopen</resref>
    <byte label="PaletteID">1</byte>
    <exostring label="Comment">abcdefg</exostring>
    </struct>
  </gff3>
"""
K1_SAME_TEST_UTD_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">ldr_agtoaj</exostring>
    <locstring label="LocName" strref="-1">
      <string language="0">Door</string>
      </locstring>
    <locstring label="Description" strref="-1">
      <string language="0" />
      </locstring>
    <resref label="TemplateResRef">ldr_agtoaj</resref>
    <byte label="AutoRemoveKey">0</byte>
    <byte label="CloseLockDC">0</byte>
    <resref label="Conversation" />
    <byte label="Interruptable">0</byte>
    <uint32 label="Faction">1</uint32>
    <byte label="Plot">1</byte>
    <byte label="NotBlastable">1</byte>
    <byte label="Min1HP">0</byte>
    <byte label="KeyRequired">0</byte>
    <byte label="Lockable">0</byte>
    <byte label="Locked">0</byte>
    <byte label="OpenLockDC">28</byte>
    <byte label="OpenLockDiff">1</byte>
    <char label="OpenLockDiffMod">0</char>
    <uint16 label="PortraitId">0</uint16>
    <byte label="TrapDetectable">1</byte>
    <byte label="TrapDetectDC">0</byte>
    <byte label="TrapDisarmable">1</byte>
    <byte label="DisarmDC">28</byte>
    <byte label="TrapFlag">0</byte>
    <byte label="TrapOneShot">1</byte>
    <byte label="TrapType">2</byte>
    <exostring label="KeyName" />
    <byte label="AnimationState">0</byte>
    <uint32 label="Appearance">0</uint32>
    <sint16 label="HP">20</sint16>
    <sint16 label="CurrentHP">60</sint16>
    <byte label="Hardness">5</byte>
    <byte label="Fort">28</byte>
    <byte label="Ref">0</byte>
    <byte label="Will">0</byte>
    <resref label="OnClosed" />
    <resref label="OnDamaged" />
    <resref label="OnDeath" />
    <resref label="OnDisarm" />
    <resref label="OnHeartbeat" />
    <resref label="OnLock" />
    <resref label="OnMeleeAttacked" />
    <resref label="OnOpen" />
    <resref label="OnSpellCastAt" />
    <resref label="OnTrapTriggered" />
    <resref label="OnUnlock" />
    <resref label="OnUserDefined" />
    <uint16 label="LoadScreenID">0</uint16>
    <byte label="GenericType">19</byte>
    <byte label="Static">0</byte>
    <byte label="OpenState">0</byte>
    <resref label="OnClick" />
    <resref label="OnFailToOpen" />
    <byte label="PaletteID">6</byte>
    <exostring label="Comment">Hammerhead Door 1</exostring>
    <exostring label="KTInfoVersion">1.0.2210.16738</exostring>
    <exostring label="KTInfoDate">Tuesday, June 9, 2020 11:05:31 PM</exostring>
    <sint32 label="KTGameVerIndex">0</sint32>
    </struct>
  </gff3>
"""


class TestUTD(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skip("This test is known to fail - fixme")  # FIXME:
    def test_gff_reconstruct(self):
        gff = read_gff(K1_SAME_TEST_UTD_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_utd(construct_utd(gff))
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_UTD_XML.encode(), file_format=ResourceType.GFF_XML)
        utd = construct_utd(gff)
        self.validate_io(utd)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTD_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_utd(construct_utd(gff))
        utd = construct_utd(gff)
        self.validate_io(utd)

    def validate_io(self, utd: UTD):
        self.assertEqual("TelosDoor13", utd.tag)
        self.assertEqual(123731, utd.name.stringref)
        self.assertEqual(-1, utd.description.stringref)
        self.assertEqual("door_tel014", utd.resref)
        self.assertEqual(1, utd.auto_remove_key)
        self.assertEqual(0, utd.lock_dc)
        self.assertEqual("convoresref", utd.conversation)
        self.assertEqual(1, utd.interruptable)
        self.assertEqual(1, utd.faction_id)
        self.assertEqual(1, utd.plot)
        self.assertEqual(1, utd.not_blastable)
        self.assertEqual(1, utd.min1_hp)
        self.assertEqual(1, utd.key_required)
        self.assertEqual(1, utd.lockable)
        self.assertEqual(1, utd.locked)
        self.assertEqual(28, utd.unlock_dc)
        self.assertEqual(1, utd.unlock_diff_mod)
        self.assertEqual(1, utd.unlock_diff_mod)
        self.assertEqual(0, utd.portrait_id)
        self.assertEqual(1, utd.trap_detectable)
        self.assertEqual(0, utd.trap_detect_dc)
        self.assertEqual(1, utd.trap_disarmable)
        self.assertEqual(28, utd.trap_disarm_dc)
        self.assertEqual(0, utd.trap_flag)
        self.assertEqual(1, utd.trap_one_shot)
        self.assertEqual(2, utd.trap_type)
        self.assertEqual("keyname", utd.key_name)
        self.assertEqual(1, utd.animation_state)
        self.assertEqual(1, utd.unused_appearance)
        self.assertEqual(1, utd.min1_hp)
        self.assertEqual(60, utd.current_hp)
        self.assertEqual(5, utd.hardness)
        self.assertEqual(28, utd.fortitude)
        self.assertEqual("door_tel014", utd.resref)
        self.assertEqual(0, utd.willpower)
        self.assertEqual("onclosed", utd.on_closed)
        self.assertEqual("ondamaged", utd.on_damaged)
        self.assertEqual("ondeath", utd.on_death)
        self.assertEqual("ondisarm", utd.on_disarm)
        self.assertEqual("onheartbeat", utd.on_heartbeat)
        self.assertEqual("onlock", utd.on_lock)
        self.assertEqual("onmeleeattacked", utd.on_melee)
        self.assertEqual("onopen", utd.on_open)
        self.assertEqual("onspellcastat", utd.on_power)
        self.assertEqual("ontraptriggered", utd.on_trap_triggered)
        self.assertEqual("onunlock", utd.on_unlock)
        self.assertEqual("onuserdefined", utd.on_user_defined)
        self.assertEqual(0, utd.loadscreen_id)
        self.assertEqual(110, utd.appearance_id)
        self.assertEqual(1, utd.static)
        self.assertEqual(1, utd.open_state)
        self.assertEqual("onclick", utd.on_click)
        self.assertEqual("onfailtoopen", utd.on_open_failed)
        self.assertEqual(1, utd.palette_id)
        self.assertEqual("abcdefg", utd.comment)


if __name__ == "__main__":
    unittest.main()
