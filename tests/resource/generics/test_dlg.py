from __future__ import annotations

from copy import deepcopy
import os
import pathlib
import sys
import unittest

from unittest import TestCase

from pykotor.common.language import Gender, Language, LocalizedString

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

from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.dlg import DLGAnimation, DLGLink, DLGNode, DLGStunt, construct_dlg, dismantle_dlg
from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGReply

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from typing_extensions import LiteralString

TEST_DLG_XML = """<gff3>
  <struct id="-1">
    <uint32 label="DelayEntry">13</uint32>
    <uint32 label="DelayReply">14</uint32>
    <uint32 label="NumWords">1337</uint32>
    <resref label="EndConverAbort">abort</resref>
    <resref label="EndConversation">end</resref>
    <byte label="Skippable">1</byte>
    <resref label="AmbientTrack">track</resref>
    <byte label="AnimatedCut">123</byte>
    <resref label="CameraModel">camm</resref>
    <byte label="ComputerType">1</byte>
    <sint32 label="ConversationType">1</sint32>
    <list label="EntryList">
      <struct id="0">
        <exostring label="Speaker">bark</exostring>
        <exostring label="Listener">yoohoo</exostring>
        <list label="AnimList">
          <struct id="0">
            <exostring label="Participant">aaa</exostring>
            <uint16 label="Animation">1200</uint16>
            </struct>
          <struct id="0">
            <exostring label="Participant">bbb</exostring>
            <uint16 label="Animation">2400</uint16>
            </struct>
          </list>
        <locstring label="Text" strref="-1">
          <string language="0">Greetings</string>
          </locstring>
        <resref label="VO_ResRef">gand</resref>
        <resref label="Script">num1</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment">commentto</exostring>
        <resref label="Sound">gonk</resref>
        <exostring label="Quest">quest</exostring>
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">1</uint32>
        <uint32 label="CameraAngle">14</uint32>
        <byte label="FadeType">1</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">0</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            </struct>
          <struct id="1">
            <uint32 label="Index">1</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        <sint32 label="ActionParam1">1</sint32>
        <sint32 label="ActionParam1b">2</sint32>
        <sint32 label="ActionParam2">3</sint32>
        <sint32 label="ActionParam2b">4</sint32>
        <sint32 label="ActionParam3">5</sint32>
        <sint32 label="ActionParam3b">6</sint32>
        <sint32 label="ActionParam4">7</sint32>
        <sint32 label="ActionParam4b">8</sint32>
        <sint32 label="ActionParam5">9</sint32>
        <sint32 label="ActionParam5b">11</sint32>
        <exostring label="ActionParamStrA">aaa</exostring>
        <exostring label="ActionParamStrB">bbb</exostring>
        <sint32 label="AlienRaceNode">1</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">1</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">2</sint32>
        <sint32 label="NodeID">1</sint32>
        <sint32 label="NodeUnskippable">1</sint32>
        <sint32 label="PostProcNode">3</sint32>
        <sint32 label="RecordNoOverri">1</sint32>
        <sint32 label="RecordVO">1</sint32>
        <resref label="Script2">num2</resref>
        <sint32 label="VOTextChanged">1</sint32>
        <sint32 label="CameraID">32</sint32>
        <sint32 label="RecordNoVOOverri">1</sint32>
        </struct>
      <struct id="1">
        <exostring label="Speaker" />
        <exostring label="Listener" />
        <list label="AnimList" />
        <locstring label="Text" strref="-1">
          <string language="0">Farewell</string>
          </locstring>
        <resref label="VO_ResRef" />
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList" />
        <byte label="SoundExists">0</byte>
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">0</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">0</sint32>
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PostProcNode">0</sint32>
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script2" />
        <sint32 label="VOTextChanged">0</sint32>
        <sint32 label="CameraID">-1</sint32>
        <sint32 label="RecordNoVOOverri">0</sint32>
        </struct>
      <struct id="2">
        <exostring label="Speaker" />
        <exostring label="Listener" />
        <list label="AnimList" />
        <locstring label="Text" strref="-1">
          <string language="0">I dun wanna talk no more.</string>
          </locstring>
        <resref label="VO_ResRef" />
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList" />
        <byte label="SoundExists">0</byte>
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">0</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">0</sint32>
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PostProcNode">0</sint32>
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script2" />
        <sint32 label="VOTextChanged">0</sint32>
        <sint32 label="CameraID">-1</sint32>
        <sint32 label="RecordNoVOOverri">0</sint32>
        </struct>
      </list>
    <byte label="OldHitCheck">1</byte>
    <list label="ReplyList">
      <struct id="0">
        <exostring label="Listener" />
        <list label="AnimList" />
        <locstring label="Text" strref="-1">
          <string language="0">Hello creature!</string>
          </locstring>
        <resref label="VO_ResRef" />
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList">
          <struct id="0">
            <uint32 label="Index">0</uint32>
            <resref label="Active" />
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">0</byte>
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <sint32 label="CamVidEffect">-1</sint32>
        <byte label="Changed">0</byte>
        <sint32 label="Emotion">4</sint32>
        <sint32 label="FacialAnim">0</sint32>
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PostProcNode">0</sint32>
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script" />
        <resref label="Script2" />
        <resref label="Sound" />
        <byte label="SoundExists">0</byte>
        <locstring label="Text" strref="-1">
          <string language="0">Goodbye.</string>
          </locstring>
        <sint32 label="VOTextChanged">0</sint32>
        <resref label="VO_ResRef" />
        <uint32 label="WaitFlags">0</uint32>
        </struct>
      <struct id="1">
        <sint32 label="ActionParam1">0</sint32>
        <sint32 label="ActionParam1b">0</sint32>
        <sint32 label="ActionParam2">0</sint32>
        <sint32 label="ActionParam2b">0</sint32>
        <sint32 label="ActionParam3">0</sint32>
        <sint32 label="ActionParam3b">0</sint32>
        <sint32 label="ActionParam4">0</sint32>
        <sint32 label="ActionParam4b">0</sint32>
        <sint32 label="ActionParam5">0</sint32>
        <sint32 label="ActionParam5b">0</sint32>
        <exostring label="ActionParamStrA" />
        <exostring label="ActionParamStrB" />
        <sint32 label="AlienRaceNode">0</sint32>
        <list label="AnimList">
          <struct id="0">
            <exostring label="Participant">aaa</exostring>
            <uint16 label="Animation">1200</uint16>
            </struct>
          <struct id="0">
            <exostring label="Participant">bbb</exostring>
            <uint16 label="Animation">2400</uint16>
            </struct>
          </list>
        <sint32 label="CamVidEffect">-1</sint32>
        <uint32 label="CameraAngle">0</uint32>
        <sint32 label="CameraID">-1</sint32>
        <byte label="Changed">0</byte>
        <exostring label="Comment" />
        <uint32 label="Delay">4294967295</uint32>
        <sint32 label="Emotion">4</sint32>
        <list label="EntriesList">
          <struct id="0">
            <uint32 label="Index">1</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            <resref label="Active2" />
            <sint32 label="Param1">0</sint32>
            <sint32 label="Param1b">0</sint32>
            <sint32 label="Param2">0</sint32>
            <sint32 label="Param2b">0</sint32>
            <sint32 label="Param3">0</sint32>
            <sint32 label="Param3b">0</sint32>
            <sint32 label="Param4">0</sint32>
            <sint32 label="Param4b">0</sint32>
            <sint32 label="Param5">0</sint32>
            <sint32 label="Param5b">0</sint32>
            <exostring label="ParamStrA" />
            <exostring label="ParamStrB" />
            <byte label="Not">0</byte>
            <byte label="Not2">0</byte>
            <sint32 label="Logic">0</sint32>
            </struct>
          </list>
        <sint32 label="FacialAnim">0</sint32>
        <byte label="FadeType">0</byte>
        <exostring label="Listener" />
        <sint32 label="NodeID">0</sint32>
        <sint32 label="NodeUnskippable">0</sint32>
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <sint32 label="PostProcNode">0</sint32>
        <exostring label="Quest" />
        <sint32 label="RecordNoOverri">0</sint32>
        <sint32 label="RecordNoVOOverri">0</sint32>
        <sint32 label="RecordVO">0</sint32>
        <resref label="Script" />
        <resref label="Script2" />
        <resref label="Sound" />
        <byte label="SoundExists">0</byte>
        <locstring label="Text" strref="-1">
          <string language="0">Goodbye.</string>
          </locstring>
        <sint32 label="VOTextChanged">0</sint32>
        <resref label="VO_ResRef" />
        <uint32 label="WaitFlags">0</uint32>
        </struct>
      </list>
    <list label="StartingList">
      <struct id="0">
        <uint32 label="Index">0</uint32>
        <resref label="Active" />
        <resref label="Active2" />
        <sint32 label="Param1">0</sint32>
        <sint32 label="Param1b">0</sint32>
        <sint32 label="Param2">0</sint32>
        <sint32 label="Param2b">0</sint32>
        <sint32 label="Param3">0</sint32>
        <sint32 label="Param3b">0</sint32>
        <sint32 label="Param4">0</sint32>
        <sint32 label="Param4b">0</sint32>
        <sint32 label="Param5">0</sint32>
        <sint32 label="Param5b">0</sint32>
        <exostring label="ParamStrA" />
        <exostring label="ParamStrB" />
        <byte label="Not">0</byte>
        <byte label="Not2">0</byte>
        <sint32 label="Logic">0</sint32>
        </struct>
      <struct id="1">
        <uint32 label="Index">2</uint32>
        <resref label="Active" />
        <resref label="Active2" />
        <sint32 label="Param1">0</sint32>
        <sint32 label="Param1b">0</sint32>
        <sint32 label="Param2">0</sint32>
        <sint32 label="Param2b">0</sint32>
        <sint32 label="Param3">0</sint32>
        <sint32 label="Param3b">0</sint32>
        <sint32 label="Param4">0</sint32>
        <sint32 label="Param4b">0</sint32>
        <sint32 label="Param5">0</sint32>
        <sint32 label="Param5b">0</sint32>
        <exostring label="ParamStrA" />
        <exostring label="ParamStrB" />
        <byte label="Not">0</byte>
        <byte label="Not2">0</byte>
        <sint32 label="Logic">0</sint32>
        </struct>
      </list>
    <byte label="UnequipHItem">1</byte>
    <byte label="UnequipItems">1</byte>
    <list label="StuntList">
      <struct id="0">
        <exostring label="Participant">aaa</exostring>
        <resref label="StuntModel">m01aa_c04_char01</resref>
        </struct>
      <struct id="0">
        <exostring label="Participant">bbb</exostring>
        <resref label="StuntModel">m01aa_c04_char01</resref>
        </struct>
      </list>
    <exostring label="VO_ID">echo</exostring>
    <sint32 label="AlienRaceOwner">123</sint32>
    <sint32 label="PostProcOwner">12</sint32>
    <sint32 label="RecordNoVO">3</sint32>
    <exostring label="EditorInfo">v2.3.2 Apr 30, 2008 LastEdit: 11-Jan-22 18:14:34</exostring>
    </struct>
  </gff3>
"""

TEST_K1_DLG_XML = """<gff3>
  <struct id="-1">
    <uint32 label="DelayEntry">0</uint32>
    <uint32 label="DelayReply">0</uint32>
    <uint32 label="NumWords">74</uint32>
    <resref label="EndConversation" />
    <resref label="EndConverAbort" />
    <byte label="Skippable">1</byte>
    <list label="StuntList" />
    <resref label="CameraModel" />
    <exostring label="VO_ID">woma08</exostring>
    <list label="EntryList">
      <struct id="0">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5448" />
        <resref label="VO_ResRef">nm02aawoma08008_</resref>
        <resref label="Script">k_ptar_rndtlkres</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">0</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="1">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5449" />
        <resref label="VO_ResRef">nm02aawoma08006_</resref>
        <resref label="Script">k_ptar_rndtlkinc</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">1</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="2">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5450" />
        <resref label="VO_ResRef">nm02aawoma08004_</resref>
        <resref label="Script">k_ptar_rndtlkinc</resref>
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment">outside apartment</exostring>
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">2</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="3">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5451" />
        <resref label="VO_ResRef">nm02aawoma08002_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment">inside apartment</exostring>
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">3</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      <struct id="4">
        <exostring label="Speaker" />
        <list label="AnimList" />
        <locstring label="Text" strref="5452" />
        <resref label="VO_ResRef">nm02aawoma08000_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <sint32 label="PlotIndex">-1</sint32>
        <float label="PlotXPPercentage">1.0</float>
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="RepliesList">
          <struct id="0">
            <uint32 label="Index">4</uint32>
            <resref label="Active" />
            <byte label="IsChild">0</byte>
            </struct>
          </list>
        <byte label="SoundExists">1</byte>
        </struct>
      </list>
    <list label="ReplyList">
      <struct id="0">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08009_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="1">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08007_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="2">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08005_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="3">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08003_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      <struct id="4">
        <list label="AnimList" />
        <locstring label="Text" strref="-1" />
        <resref label="VO_ResRef">_m02aawoma08001_</resref>
        <resref label="Script" />
        <uint32 label="Delay">4294967295</uint32>
        <exostring label="Comment" />
        <resref label="Sound" />
        <exostring label="Quest" />
        <exostring label="Listener" />
        <uint32 label="WaitFlags">0</uint32>
        <uint32 label="CameraAngle">0</uint32>
        <byte label="FadeType">0</byte>
        <list label="EntriesList" />
        <byte label="SoundExists">0</byte>
        </struct>
      </list>
    <list label="StartingList">
      <struct id="0">
        <uint32 label="Index">4</uint32>
        <resref label="Active">k_ptar_sithdis</resref>
        </struct>
      <struct id="1">
        <uint32 label="Index">3</uint32>
        <resref label="Active">k_ptar_genhome</resref>
        </struct>
      <struct id="2">
        <uint32 label="Index">2</uint32>
        <resref label="Active">k_ptar_rndtalk0</resref>
        </struct>
      <struct id="3">
        <uint32 label="Index">1</uint32>
        <resref label="Active">k_ptar_rndtalk1</resref>
        </struct>
      <struct id="4">
        <uint32 label="Index">0</uint32>
        <resref label="Active" />
        </struct>
      </list>
    </struct>
  </gff3>
"""
class TestDLG(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, *args):
        self.log_messages.extend(args)

    def test_k1_serialization(self):
        gff: GFF = read_gff(TEST_K1_DLG_XML.encode())
        dlg: DLG = construct_dlg(gff)
        for node in dlg.all_entries():
            assert node == DLGNode.from_dict(node.to_dict())

    def test_k2_serialization(self):
        gff: GFF = read_gff(TEST_DLG_XML.encode())
        dlg: DLG = construct_dlg(gff)
        for node in dlg.all_entries():
            reserialized_dlg_node: DLGNode = DLGNode.from_dict(node.to_dict())
            for attr_name, value in node.__dict__.items():
                reserialized_node_attr_value = reserialized_dlg_node.__dict__[attr_name]
                assert reserialized_node_attr_value == value, attr_name + repr(value) + " vs " + repr(reserialized_node_attr_value)

    def test_io_construct(self):
        gff = read_gff(TEST_DLG_XML.encode())
        dlg = construct_dlg(gff)
        self.validate_io(dlg)

    def validate_io(self, dlg: DLG):
        all_entries: list[DLGEntry] = dlg.all_entries()
        all_replies: list[DLGReply] = dlg.all_replies()

        entry0 = all_entries[0]
        entry1 = all_entries[1]
        entry2 = all_entries[2]

        reply0 = all_replies[0]
        reply1 = all_replies[1]

        self.assertEqual(3, len(all_entries))
        self.assertEqual(2, len(all_replies))
        self.assertEqual(2, len(dlg.starters))
        self.assertEqual(2, len(dlg.stunts))

        self.assertIn(entry0, [link.node for link in dlg.starters])
        self.assertIn(entry2, [link.node for link in dlg.starters])

        self.assertEqual(2, len(entry0.links))
        self.assertIn(reply0, [link.node for link in entry0.links])
        self.assertIn(reply1, [link.node for link in entry0.links])

        self.assertEqual(1, len(reply0.links))
        self.assertIn(entry0, [link.node for link in reply0.links])

        self.assertEqual(1, len(reply1.links))
        self.assertIn(entry1, [link.node for link in reply1.links])

        self.assertEqual(0, len(entry2.links))

        self.assertEqual(13, dlg.delay_entry)
        self.assertEqual(14, dlg.delay_reply)
        self.assertEqual(1337, dlg.word_count)
        self.assertEqual("abort", dlg.on_abort)
        self.assertEqual("end", dlg.on_end)
        self.assertEqual(1, dlg.skippable)
        self.assertEqual("track", dlg.ambient_track)
        self.assertEqual(123, dlg.animated_cut)
        self.assertEqual("camm", dlg.camera_model)
        self.assertEqual(1, dlg.computer_type.value)
        self.assertEqual(1, dlg.conversation_type.value)
        self.assertEqual(1, dlg.old_hit_check)
        self.assertEqual(1, dlg.unequip_hands)
        self.assertEqual(1, dlg.unequip_items)
        self.assertEqual("echo", dlg.vo_id)
        self.assertEqual(123, dlg.alien_race_owner)
        self.assertEqual(12, dlg.post_proc_owner)
        self.assertEqual(3, dlg.record_no_vo)

        self.assertEqual("yoohoo", entry0.listener)
        self.assertEqual(-1, entry0.text.stringref)
        self.assertEqual("gand", entry0.vo_resref)
        self.assertEqual("num1", entry0.script1)
        self.assertEqual(-1, entry0.delay)
        self.assertEqual("commentto", entry0.comment)
        self.assertEqual("gonk", entry0.sound)
        self.assertEqual("quest", entry0.quest)
        self.assertEqual(-1, entry0.plot_index)
        self.assertEqual(1.0, entry0.plot_xp_percentage)
        self.assertEqual(1, entry0.wait_flags)
        self.assertEqual(14, entry0.camera_angle)
        self.assertEqual(1, entry0.fade_type)
        self.assertEqual(1, entry0.sound_exists)
        self.assertEqual(1, entry0.alien_race_node)
        self.assertEqual(1, entry0.vo_text_changed)
        self.assertEqual(4, entry0.emotion_id)
        self.assertEqual(2, entry0.facial_id)
        self.assertEqual(1, entry0.node_id)
        self.assertEqual(1, entry0.unskippable)
        self.assertEqual(3, entry0.post_proc_node)
        self.assertEqual(1, entry0.record_vo)
        self.assertEqual("num2", entry0.script2)
        self.assertEqual(1, entry0.vo_text_changed)
        self.assertEqual(1, entry0.record_no_vo_override)
        self.assertEqual(32, entry0.camera_id)
        self.assertEqual("bark", entry0.speaker)
        self.assertEqual(-1, entry0.camera_effect)
        self.assertEqual(1, entry0.record_no_vo_override)

        self.assertEqual("bbb", dlg.stunts[1].participant)
        self.assertEqual("m01aa_c04_char01", dlg.stunts[1].stunt_model)


class TestDLGEntrySerialization(unittest.TestCase):
    def test_dlg_entry_serialization_basic(self):
        entry = DLGEntry()
        entry.comment = "Test Comment"
        entry.camera_angle = 45

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        self.assertEqual(entry.comment, deserialized.comment)
        self.assertEqual(entry.camera_angle, deserialized.camera_angle)

    def test_dlg_entry_serialization_with_links(self):
        entry = DLGEntry()
        entry.comment = "Entry with links"
        link = DLGLink(entry, 1)
        entry.links.append(link)

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        self.assertEqual(entry.comment, deserialized.comment)
        self.assertEqual(len(deserialized.links), 1)
        self.assertEqual(deserialized.links[0].list_index, 1)

    def test_dlg_entry_serialization_all_attributes(self):
        entry = DLGEntry()
        entry.comment = "All attributes"
        entry.camera_angle = 30
        entry.listener = "Listener"
        entry.quest = "Quest"
        entry.script1 = ResRef("script1")

        serialized = entry.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        self.assertEqual(entry.comment, deserialized.comment)
        self.assertEqual(entry.camera_angle, deserialized.camera_angle)
        self.assertEqual(entry.listener, deserialized.listener)
        self.assertEqual(entry.quest, deserialized.quest)
        self.assertEqual(entry.script1, deserialized.script1)

    def test_dlg_entry_with_nested_replies(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))

        entry1.links.append(DLGLink(node=reply1))
        reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])
        reply2.links.append(DLGLink(node=entry1))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        serialized = entry1.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        self.assertEqual(entry1.comment, deserialized.comment)
        self.assertEqual(len(deserialized.links), 1)
        self.assertEqual(deserialized.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R222")
        self.assertEqual(len(deserialized.links[0].node.links), 2)
        self.assertEqual(deserialized.links[0].node.links[0].node.comment, "E221")
        self.assertEqual(deserialized.links[0].node.links[1].node.text.get(Language.ENGLISH, Gender.MALE), "R223")
        self.assertEqual(deserialized.links[0].node.links[1].node.links[0].node.comment, "E248")

    def test_dlg_entry_with_circular_reference(self):
        # Create DLGEntry and DLGReply objects
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        # Establish links between entries and replies to create circular reference
        entry1.links.append(DLGLink(node=reply1))
        reply1.links.append(DLGLink(node=entry2))
        entry2.links.append(DLGLink(node=reply2))
        reply2.links.append(DLGLink(node=entry1))  # Circular reference

        # Serialize the entry1
        serialized = entry1.to_dict()
        # Deserialize back to object
        deserialized = DLGEntry.from_dict(serialized)

        # Assert top-level comment
        self.assertEqual(entry1.comment, deserialized.comment)
        
        # Assert first level link
        self.assertEqual(len(deserialized.links), 1)
        deserialized_reply1 = deserialized.links[0].node
        self.assertEqual(deserialized_reply1.text.get(Language.ENGLISH, Gender.MALE), "R222")

        # Assert second level link
        self.assertEqual(len(deserialized_reply1.links), 1)
        deserialized_entry2 = deserialized_reply1.links[0].node
        self.assertEqual(deserialized_entry2.comment, "E221")

        # Assert third level link
        self.assertEqual(len(deserialized_entry2.links), 1)
        deserialized_reply2 = deserialized_entry2.links[0].node
        self.assertEqual(deserialized_reply2.text.get(Language.ENGLISH, Gender.MALE), "R249")

        # Assert circular reference back to the original entry1
        self.assertEqual(len(deserialized_reply2.links), 1)
        deserialized_entry1_circular = deserialized_reply2.links[0].node
        self.assertEqual(deserialized_entry1_circular.comment, "E248")

    def test_dlg_entry_with_multiple_levels(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        entry1.links.append(DLGLink(node=reply1))
        reply1.links.extend([DLGLink(node=entry2), DLGLink(node=reply2)])
        reply2.links.append(DLGLink(node=entry3))
        entry3.links.append(DLGLink(node=reply4))
        reply4.links.append(DLGLink(node=reply5))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        serialized = entry1.to_dict()
        deserialized = DLGEntry.from_dict(serialized)

        self.assertEqual(entry1.comment, deserialized.comment)
        self.assertEqual(len(deserialized.links), 1)
        self.assertEqual(deserialized.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R222")
        self.assertEqual(len(deserialized.links[0].node.links), 2)
        self.assertEqual(deserialized.links[0].node.links[0].node.comment, "E221")
        self.assertEqual(deserialized.links[0].node.links[1].node.text.get(Language.ENGLISH, Gender.MALE), "R223")
        self.assertEqual(len(deserialized.links[0].node.links[1].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[1].node.links[0].node.comment, "E250")
        self.assertEqual(len(deserialized.links[0].node.links[1].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[1].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R225")
        self.assertEqual(len(deserialized.links[0].node.links[1].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[1].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R224")


class TestDLGReplySerialization(unittest.TestCase):
    def test_dlg_reply_serialization_basic(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Hello")
        reply.unskippable = True

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        self.assertEqual(reply.text, deserialized.text)
        self.assertEqual(reply.unskippable, deserialized.unskippable)

    def test_dlg_reply_serialization_with_links(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Reply with links")
        link = DLGLink(reply, 2)
        reply.links.append(link)

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        self.assertEqual(reply.text, deserialized.text)
        self.assertEqual(len(deserialized.links), 1)
        self.assertEqual(deserialized.links[0].list_index, 2)

    def test_dlg_reply_serialization_all_attributes(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Reply with all attributes")
        reply.vo_resref = ResRef("vo_resref")
        reply.wait_flags = 5

        serialized = reply.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        self.assertEqual(reply.text, deserialized.text)
        self.assertEqual(reply.vo_resref, deserialized.vo_resref)
        self.assertEqual(reply.wait_flags, deserialized.wait_flags)

    def test_dlg_reply_with_nested_entries(self):
        # Create replies with localized text
        reply1 = DLGReply()
        reply1.text.set_data(Language.ENGLISH, Gender.MALE, "R222")
        reply2 = DLGReply()
        reply2.text.set_data(Language.ENGLISH, Gender.MALE, "R223")
        reply3 = DLGReply()
        reply3.text.set_data(Language.ENGLISH, Gender.MALE, "R249")

        # Create entries with comments
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        # Link entries and replies together
        reply1.links.append(DLGLink(node=entry1))
        entry1.links.append(DLGLink(node=reply2))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249

        # Serialize and deserialize reply1
        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        # Debug prints
        print("Serialized reply1:", serialized)
        print("Deserialized reply1:", deserialized)

        # Assertions
        # Check the text of the first reply
        original_text = reply1.text.get(Language.ENGLISH, Gender.MALE)
        deserialized_text = deserialized.text.get(Language.ENGLISH, Gender.MALE)
        self.assertEqual(original_text, deserialized_text)

        # Check the first link in the deserialized reply
        deserialized_entry1 = deserialized.links[0].node
        self.assertEqual(len(deserialized.links), 1)
        self.assertEqual(deserialized_entry1.comment, "E248")

        # Check the first link in the deserialized entry1
        deserialized_reply2 = deserialized_entry1.links[0].node
        self.assertEqual(len(deserialized_entry1.links), 1)
        self.assertEqual(deserialized_reply2.text.get(Language.ENGLISH, Gender.MALE), "R223")

        # Check the first link in the deserialized reply2
        deserialized_entry2 = deserialized_reply2.links[0].node
        self.assertEqual(deserialized_entry2.comment, "E221")
        self.assertEqual(len(deserialized_entry2.links), 1)

        # Check the first link in the deserialized entry2
        deserialized_reply3 = deserialized_entry2.links[0].node
        self.assertEqual(deserialized_reply3.text.get(Language.ENGLISH, Gender.MALE), "R249")

    def test_dlg_reply_with_circular_reference(self):
        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1.links.append(DLGLink(node=entry1))
        entry1.links.append(DLGLink(node=reply2))
        reply2.links.append(DLGLink(node=entry2))
        entry2.links.append(DLGLink(node=reply1))  # Circular reference

        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        self.assertEqual(reply1.text, deserialized.text)
        self.assertEqual(len(deserialized.links), 1)
        self.assertEqual(deserialized.links[0].node.comment, "E248")
        self.assertEqual(len(deserialized.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R249")
        self.assertEqual(len(deserialized.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.links[0].node.comment, "E221")
        self.assertEqual(len(deserialized.links[0].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R222")

    def test_dlg_reply_with_multiple_levels(self):
        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1.links.append(DLGLink(node=entry1))
        reply2.links.append(DLGLink(node=entry2))
        entry1.links.append(DLGLink(node=reply2))
        entry2.links.append(DLGLink(node=reply3))  # Reuse R249
        reply3.links.append(DLGLink(node=entry3))
        entry3.links.append(DLGLink(node=reply4))
        reply4.links.append(DLGLink(node=reply5))

        serialized = reply1.to_dict()
        deserialized = DLGReply.from_dict(serialized)

        self.assertEqual(reply1.text, deserialized.text)
        self.assertEqual(len(deserialized.links), 1)
        self.assertEqual(deserialized.links[0].node.comment, "E248")
        self.assertEqual(len(deserialized.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R223")
        self.assertEqual(len(deserialized.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.links[0].node.comment, "E221")
        self.assertEqual(len(deserialized.links[0].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R249")
        self.assertEqual(len(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.comment, "E250")
        self.assertEqual(len(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R225")
        self.assertEqual(len(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R224")


class TestDLGLinkSerialization(unittest.TestCase):
    def test_dlg_link_serialization_basic(self):
        link = DLGLink(DLGEntry())
        link.list_index = 3

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        self.assertEqual(link.list_index, deserialized.list_index)

    def test_dlg_link_serialization_with_node(self):
        entry = DLGEntry()
        entry.comment = "Linked entry"
        link = DLGLink(entry)

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        self.assertEqual(link.node.comment, deserialized.node.comment)

    def test_dlg_link_serialization_all_attributes(self):
        reply = DLGReply()
        reply.text = LocalizedString.from_english("Linked reply")
        link = DLGLink(reply, 5)
        link.node = reply

        serialized = link.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        self.assertEqual(link.list_index, deserialized.list_index)
        self.assertEqual(link.node.text, deserialized.node.text)

    def test_dlg_link_with_nested_entries_and_replies(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=reply3)

        entry1.links.append(link1)
        reply1.links.extend([link2, link3])
        entry2.links.append(link4)  # Reuse R249

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        self.assertEqual(link1.node.text, deserialized.node.text)
        self.assertEqual(len(deserialized.node.links), 2)
        self.assertEqual(deserialized.node.links[0].node.comment, "E221")
        self.assertEqual(deserialized.node.links[1].node.text.get(Language.ENGLISH, Gender.MALE), "R223")
        self.assertEqual(len(deserialized.node.links[1].node.links), 1)
        self.assertEqual(deserialized.node.links[1].node.links[0].node.comment, "E248")

    def test_dlg_link_with_circular_references(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R249"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=entry1)  # Circular reference

        entry1.links.append(link1)
        reply1.links.append(link2)
        entry2.links.append(link3)  # Reuse R249
        reply2.links.append(link4)

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        self.assertEqual(link1.node.text, deserialized.node.text)
        self.assertEqual(len(deserialized.node.links), 1)
        self.assertEqual(deserialized.node.links[0].node.comment, "E221")
        self.assertEqual(len(deserialized.node.links[0].node.links), 1)
        self.assertEqual(deserialized.node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R249")
        self.assertEqual(len(deserialized.node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.node.links[0].node.links[0].node.links[0].node.comment, "E248")

    def test_dlg_link_with_multiple_levels(self):
        entry1 = DLGEntry(comment="E248")
        entry2 = DLGEntry(comment="E221")
        entry3 = DLGEntry(comment="E250")

        reply1 = DLGReply(text=LocalizedString.from_english("R222"))
        reply2 = DLGReply(text=LocalizedString.from_english("R223"))
        reply3 = DLGReply(text=LocalizedString.from_english("R249"))
        reply4 = DLGReply(text=LocalizedString.from_english("R225"))
        reply5 = DLGReply(text=LocalizedString.from_english("R224"))

        link1 = DLGLink(node=reply1)
        link2 = DLGLink(node=entry2)
        link3 = DLGLink(node=reply2)
        link4 = DLGLink(node=reply3)
        link5 = DLGLink(node=entry3)
        link6 = DLGLink(node=reply4)
        link7 = DLGLink(node=reply5)

        entry1.links.append(link1)
        reply1.links.append(link3)
        reply1.links.append(link2)
        entry2.links.append(link4)  # Reuse R249
        reply3.links.append(link5)
        entry3.links.append(link6)
        reply4.links.append(link7)

        serialized = link1.to_dict()
        deserialized = DLGLink.from_dict(serialized)

        self.assertEqual(link1.node.text, deserialized.node.text)
        self.assertEqual(len(deserialized.node.links), 2)
        self.assertEqual(deserialized.node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R223")
        self.assertEqual(deserialized.node.links[1].node.comment, "E221")
        self.assertEqual(len(deserialized.node.links[1].node.links), 1)
        self.assertEqual(deserialized.node.links[1].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R249")
        self.assertEqual(len(deserialized.node.links[1].node.links[0].node.links), 1)
        self.assertEqual(deserialized.node.links[1].node.links[0].node.links[0].node.comment, "E250")
        self.assertEqual(len(deserialized.node.links[1].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R225")
        self.assertEqual(len(deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.links), 1)
        self.assertEqual(deserialized.node.links[1].node.links[0].node.links[0].node.links[0].node.links[0].node.text.get(Language.ENGLISH, Gender.MALE), "R224")



class TestDLGAnimationSerialization(unittest.TestCase):
    def test_dlg_animation_serialization_basic(self):
        animation = DLGAnimation()
        animation.animation_id = 1200
        animation.participant = "Player"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        self.assertEqual(animation.animation_id, deserialized.animation_id)
        self.assertEqual(animation.participant, deserialized.participant)

    def test_dlg_animation_serialization_default(self):
        animation = DLGAnimation()

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        self.assertEqual(animation.animation_id, deserialized.animation_id)
        self.assertEqual(animation.participant, deserialized.participant)

    def test_dlg_animation_serialization_with_custom_values(self):
        animation = DLGAnimation()
        animation.animation_id = 2400
        animation.participant = "NPC"

        serialized = animation.to_dict()
        deserialized = DLGAnimation.from_dict(serialized)

        self.assertEqual(animation.animation_id, deserialized.animation_id)
        self.assertEqual(animation.participant, deserialized.participant)


class TestDLGStuntSerialization(unittest.TestCase):
    def test_dlg_stunt_serialization_basic(self):
        stunt = DLGStunt()
        stunt.participant = "Player"
        stunt.stunt_model = ResRef("model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        self.assertEqual(stunt.participant, deserialized.participant)
        self.assertEqual(stunt.stunt_model, deserialized.stunt_model)

    def test_dlg_stunt_serialization_default(self):
        stunt = DLGStunt()

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        self.assertEqual(stunt.participant, deserialized.participant)
        self.assertEqual(stunt.stunt_model, deserialized.stunt_model)

    def test_dlg_stunt_serialization_with_custom_values(self):
        stunt = DLGStunt()
        stunt.participant = "NPC"
        stunt.stunt_model = ResRef("npc_model")

        serialized = stunt.to_dict()
        deserialized = DLGStunt.from_dict(serialized)

        self.assertEqual(stunt.participant, deserialized.participant)
        self.assertEqual(stunt.stunt_model, deserialized.stunt_model)


if __name__ == "__main__":
    unittest.main()
