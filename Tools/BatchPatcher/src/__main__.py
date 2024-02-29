from __future__ import annotations

import concurrent.futures
import os
import pathlib
import platform
import sys
import tkinter as tk
import traceback

from contextlib import suppress
from copy import deepcopy
from io import StringIO
from threading import Thread
from tkinter import (
    colorchooser,
    filedialog,
    font as tkfont,
    messagebox,
    ttk,
)
from typing import TYPE_CHECKING, Any

from pykotor.common.misc import ResRef
from utility.error_handling import format_exception_with_variables, universal_simplify_exception

if getattr(sys, "frozen", False) is False:
    def add_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    absolute_file_path = pathlib.Path(__file__).resolve()
    pykotor_font_path = absolute_file_path.parents[3] / "Libraries" / "PyKotorFont" / "src" / "pykotor"
    if pykotor_font_path.is_dir():
        add_sys_path(pykotor_font_path.parent)
    pykotor_path = absolute_file_path.parents[3] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.is_dir():
        add_sys_path(pykotor_path.parent)
    utility_path = absolute_file_path.parents[3] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.is_dir():
        add_sys_path(utility_path.parent)


from pykotor.common.language import Language, LocalizedString
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.font.draw import write_bitmap_fonts
from pykotor.resource.formats.erf.erf_auto import write_erf
from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.formats.gff import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct, read_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.rim.rim_auto import write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.resource.formats.tpc.io_tga import TPCTGAReader, TPCTGAWriter
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.misc import is_any_erf_type_file, is_capsule_file
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.tslpatcher.logger import PatchLogger
from translate.language_translator import TranslationOption, Translator
from utility.system.path import Path, PurePath

if TYPE_CHECKING:

    from collections.abc import Callable

    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.formats.tlk.tlk_data import TLKEntry
    from pykotor.tslpatcher.logger import PatchLog

APP: KOTORPatchingToolUI
OUTPUT_LOG: Path
LOGGING_ENABLED: bool
processed_files: set[Path] = set()

gff_types: list[str] = list(GFFContent.get_extensions())
fieldtype_to_fieldname: dict[GFFFieldType, str] = {
    GFFFieldType.UInt8: "Byte",
    GFFFieldType.Int8: "Char",
    GFFFieldType.UInt16: "Word",
    GFFFieldType.Int16: "Short",
    GFFFieldType.UInt32: "DWORD",
    GFFFieldType.Int32: "Int",
    GFFFieldType.Int64: "Int64",
    GFFFieldType.Single: "Float",
    GFFFieldType.Double: "Double",
    GFFFieldType.String: "ExoString",
    GFFFieldType.ResRef: "ResRef",
    GFFFieldType.LocalizedString: "ExoLocString",
    GFFFieldType.Vector3: "Position",
    GFFFieldType.Vector4: "Orientation",
    GFFFieldType.Struct: "Struct",
    GFFFieldType.List: "List",
}

ALIEN_SOUNDS = {  # Same in k1 and tsl.
    "n_genwook_grts1": {"_id": "0", "comment": "Gen_Wookiee_Greeting_Short"},
    "n_genwook_coms1": {"_id": "1", "comment": "Gen_Wookiee_Generic_Comment_-_Short_1"},
    "n_genwook_coms2": {"_id": "2", "comment": "Gen_Wookiee_Generic_Comment_-_Short_2"},
    "n_genwook_comm1": {"_id": "3", "comment": "Gen_Wookiee_Generic_Comment_-_Medium_1"},
    "n_genwook_comm2": {"_id": "4", "comment": "Gen_Wookiee_Generic_Comment_-_Medium_2"},
    "n_genwook_angs": {"_id": "5", "comment": "Gen_Wookiee_Angry_Short"},
    "n_genwook_angm": {"_id": "6", "comment": "Gen_Wookiee_Angry_Medium"},
    "n_genwook_ques": {"_id": "7", "comment": "Gen_Wookiee_Question_-_Short"},
    "n_genwook_quem": {"_id": "8", "comment": "Gen_Wookiee_Question_-_Medium"},
    "n_genwook_scrs": {"_id": "9", "comment": "Gen_Wookiee_Scared_-_Short"},
    "n_genwook_scrm": {"_id": "10", "comment": "Gen_Wookiee_Scared_-_Medium"},
    "n_genwook_lghs": {"_id": "11", "comment": "Gen_Wookiee_Laughter_(mocking)_-_short"},
    "n_genwook_lghm": {"_id": "12", "comment": "Gen_Wookiee_Laughter_(mocking)_-_medium"},
    "n_genwook_hpys": {"_id": "13", "comment": "Gen_Wookiee_Happy_(thankful)_-_short"},
    "n_genwook_hpym": {"_id": "14", "comment": "Gen_Wookiee_Happy_(thankful)_-_medium"},
    "n_genwook_sads": {"_id": "15", "comment": "Gen_Wookiee_Sad_-_Short"},
    "n_genwook_sadm": {"_id": "16", "comment": "Gen_Wookiee_Sad_-_Medium"},
    "n_genfwook_grts1": {"_id": "17", "comment": "Female_Wookiee_Greeting_Short"},
    "n_genfwook_coms1": {"_id": "18", "comment": "Female_Wookiee_Generic_Comment_-_Short_1"},
    "n_genfwook_coms2": {"_id": "19", "comment": "Female_Wookiee_Generic_Comment_-_Short_2"},
    "n_genfwook_comm1": {"_id": "20", "comment": "Female_Wookiee_Generic_Comment_-_Medium_1"},
    "n_genfwook_comm2": {"_id": "21", "comment": "Female_Wookiee_Generic_Comment_-_Medium_2"},
    "n_genfwook_angs": {"_id": "22", "comment": "Female_Wookiee_Angry_Short"},
    "n_genfwook_angm": {"_id": "23", "comment": "Female_Wookiee_Angry_Medium"},
    "n_genfwook_ques": {"_id": "24", "comment": "Female_Wookiee_Question_-_Short"},
    "n_genfwook_quem": {"_id": "25", "comment": "Female_Wookiee_Question_-_Medium"},
    "n_genfwook_scrs": {"_id": "26", "comment": "Female_Wookiee_Scared_-_Short"},
    "n_genfwook_scrm": {"_id": "27", "comment": "Female_Wookiee_Scared_-_Medium"},
    "n_genfwook_lghs": {"_id": "28", "comment": "Female_Wookiee_Laughter_(mocking)_-_short"},
    "n_genfwook_lghm": {"_id": "29", "comment": "Female_Wookiee_Laughter_(mocking)_-_medium"},
    "n_genfwook_hpys": {"_id": "30", "comment": "Female_Wookiee_Happy_(thankful)_-_short"},
    "n_genfwook_hpym": {"_id": "31", "comment": "Female_Wookiee_Happy_(thankful)_-_medium"},
    "n_genfwook_sads": {"_id": "32", "comment": "Female_Wookiee_Sad_-_Short"},
    "n_genfwook_sadm": {"_id": "33", "comment": "Female_Wookiee_Sad_-_Medium"},
    "n_gentwook_grts1": {"_id": "34", "comment": "Gen_Tough_Wooki_ee_Greeting_Short"},
    "n_gentwook_coms1": {"_id": "35", "comment": "Gen_Tough_Wookiee_Generic_Comment"},
    "n_gentwook_coms2": {"_id": "36", "comment": "Gen_Tough_Wookiee_Generic_Comment"},
    "n_gentwook_comm1": {"_id": "37", "comment": "Gen_Tough_Wookiee_Generic_Comment"},
    "n_gentwook_comm2": {"_id": "38", "comment": "Gen_Tough_Wookiee_Generic_Comment"},
    "n_gentwook_angs": {"_id": "39", "comment": "Gen_Tough_Wookiee_Angry_Short"},
    "n_gentwook_angm": {"_id": "40", "comment": "Gen_Tough_Wookiee_Angry_Medium"},
    "n_gentwook_ques": {"_id": "41", "comment": "Gen_Tough_Wookiee_Question_-_Short"},
    "n_gentwook_quem": {"_id": "42", "comment": "Gen_Tough_Wookiee_Question_-_Medium"},
    "n_gentwook_scrs": {"_id": "43", "comment": "Gen_Tough_Wookiee_Scared_-_Short"},
    "n_gentwook_scrm": {"_id": "44", "comment": "Gen_Tough_Wookiee_Scared_-_Medium"},
    "n_gentwook_lghs": {"_id": "45", "comment": "Gen_Tough_Wookiee_Laughter_(mocking)_-_short"},
    "n_gentwook_lghm": {"_id": "46", "comment": "Gen_Tough_Wookiee_Laughter_(mocking)_-_medium"},
    "n_gentwook_hpys": {"_id": "47", "comment": "Gen_Tough_Wookiee_Happy_(thankful)_-_short"},
    "n_gentwook_hpym": {"_id": "48", "comment": "Gen_Tough_Wookiee_Happy_(thankful)_-_medium"},
    "n_gentwook_sads": {"_id": "49", "comment": "Gen_Tough_Wookiee_Sad_-_Short"},
    "n_gentwook_sadm": {"_id": "50", "comment": "Gen_Tough_Wookiee_Sad_-_Medium"},
    "n_genwwook_grts1": {"_id": "51", "comment": "Gen_Wise_Wookiee_Greeting_Short"},
    "n_genwwook_coms1": {"_id": "52", "comment": "Gen_Wise_Wookiee_Generic_Comment_-_Short_1"},
    "n_genwwook_coms2": {"_id": "53", "comment": "Gen_Wise_Wookiee_Generic_Comment_-_Short_2"},
    "n_genwwook_comm1": {"_id": "54", "comment": "Gen_Wise_Wookiee_Generic_Comment_-_Medium_1"},
    "n_genwwook_comm2": {"_id": "55", "comment": "Gen_Wise_Wookiee_Generic_Comment_-_Medium_2"},
    "n_genwwook_angs": {"_id": "56", "comment": "Gen_Wise_Wookiee_Angry_Short"},
    "n_genwwook_angm": {"_id": "57", "comment": "Gen_Wise_Wookiee_Angry_Medium"},
    "n_genwwook_ques": {"_id": "58", "comment": "Gen_Wise_Wookiee_Question_-_Short"},
    "n_genwwook_quem": {"_id": "59", "comment": "Gen_Wise_Wookiee_Question_-_Medium"},
    "n_genwwook_scrs": {"_id": "60", "comment": "Gen_Wise_Wookiee_Scared_-_Short"},
    "n_genwwook_scrm": {"_id": "61", "comment": "Gen_Wise_Wookiee_Scared_-_Medium"},
    "n_genwwook_lghs": {"_id": "62", "comment": "Gen_Wise_Wookiee_Laughter_(mocking)_-_short"},
    "n_genwwook_lghm": {"_id": "63", "comment": "Gen_Wise_Wookiee_Laughter_(mocking)_-_medium"},
    "n_genwwook_hpys": {"_id": "64", "comment": "Gen_Wise_Wookiee_Happy_(thankful)_-_short"},
    "n_genwwook_hpym": {"_id": "65", "comment": "Gen_Wise_Wookiee_Happy_(thankful)_-_medium"},
    "n_genwwook_sads": {"_id": "66", "comment": "Gen_Wise_Wookiee_Sad_-_Short"},
    "n_genwwook_sadm": {"_id": "67", "comment": "Gen_Wise_Wookiee_Sad_-_Medium"},
    "n_gftwilek_grts": {"_id": "68", "comment": "Female_Twilek_Greeting_Short"},
    "n_gftwilek_grtm": {"_id": "69", "comment": "Female_Twilek_Greeting_Medium"},
    "n_gftwilek_coms1": {"_id": "70", "comment": "Female_Twilek_Generic_Comment_-_Short_1"},
    "n_gftwilek_coms2": {"_id": "71", "comment": "Female_Twilek_Generic_Comment_-_Short_2"},
    "n_gftwilek_comm1": {"_id": "72", "comment": "Female_Twilek_Generic_Comment_-_Medium_1"},
    "n_gftwilek_comm2": {"_id": "73", "comment": "Female_Twilek_Generic_Comment_-_Medium_2"},
    "n_gftwilek_coml1": {"_id": "74", "comment": "Female_Twilek_Generic_Comment_-_Long_1"},
    "n_gftwilek_coml2": {"_id": "75", "comment": "Female_Twilek_Generic_Comment_-_Long_2"},
    "n_gftwilek_angs": {"_id": "76", "comment": "Female_Twilek_Angry_Short"},
    "n_gftwilek_angm": {"_id": "77", "comment": "Female_Twilek_Angry_Medium"},
    "n_gftwilek_angl": {"_id": "78", "comment": "Female_Twilek_Angry_Long"},
    "n_gftwilek_ques": {"_id": "79", "comment": "Female_Twilek_Question_-_Short"},
    "n_gftwilek_quel": {"_id": "80", "comment": "Female_Twilek_Question_-_Long"},
    "n_gftwilek_scrs": {"_id": "81", "comment": "Female_Twilek_Scared_-_Short"},
    "n_gftwilek_scrm": {"_id": "82", "comment": "Female_Twilek_Scared_-_Medium"},
    "n_gftwilek_scrl": {"_id": "83", "comment": "Female_Twilek_Scared_-_Long"},
    "n_gftwilek_ples": {"_id": "84", "comment": "Female_Twilek_Pleading_-_Short"},
    "n_gftwilek_plem": {"_id": "85", "comment": "Female_Twilek_Pleading_-_Medium"},
    "n_gftwilek_lghs": {"_id": "86", "comment": "Female_Twilek_Laughter_(mocking)_-_short"},
    "n_gftwilek_lghm": {"_id": "87", "comment": "Female_Twilek_Laughter_(mocking)_-_medium"},
    "n_gftwilek_hpys": {"_id": "88", "comment": "Female_Twilek_Happy_(thankful)_-_short"},
    "n_gftwilek_hpym": {"_id": "89", "comment": "Female_Twilek_Happy_(thankful)_-_medium"},
    "n_gftwilek_hpyl": {"_id": "90", "comment": "Female_Twilek_Happy_(thankful)_-_long"},
    "n_gftwilek_sads": {"_id": "91", "comment": "Female_Twilek_Sad_-_Short"},
    "n_gftwilek_sadm": {"_id": "92", "comment": "Female_Twilek_Sad_-_Medium"},
    "n_gftwilek_sadl": {"_id": "93", "comment": "Female_Twilek_Sad_-_Long"},
    "n_gftwilek_seds": {"_id": "94", "comment": "Female_Twilek_Seductive_-_Short"},
    "n_gftwilek_sedm": {"_id": "95", "comment": "Female_Twilek_Seductive_-_Medium"},
    "n_gftwilek_sedl": {"_id": "96", "comment": "Female_Twilek_Seductive_-_Long"},
    "n_gmtwilek_grts": {"_id": "97", "comment": "Gen_Male_Twilek_Greeting_Short"},
    "n_gmtwilek_grtm": {"_id": "98", "comment": "Gen_Male_Twilek_Greeting_Medium"},
    "n_gmtwilek_coms1": {"_id": "99", "comment": "Gen_Male_Twilek_Generic_Comment_-_Short_1"},
    "n_gmtwilek_coms2": {"_id": "100", "comment": "Gen_Male_Twilek_Generic_Comment_-_Short_2"},
    "n_gmtwilek_comm1": {"_id": "101", "comment": "Gen_Male_Twilek_Generic_Comment_-_Medium_1"},
    "n_gmtwilek_comm2": {"_id": "102", "comment": "Gen_Male_Twilek_Generic_Comment_-_Medium_2"},
    "n_gmtwilek_coml1": {"_id": "103", "comment": "Gen_Male_Twilek_Generic_Comment_-_Long_1"},
    "n_gmtwilek_coml2": {"_id": "104", "comment": "Gen_Male_Twilek_Generic_Comment_-_Long_2"},
    "n_gmtwilek_angs": {"_id": "105", "comment": "Gen_Male_Twilek_Angry_Short"},
    "n_gmtwilek_angm": {"_id": "106", "comment": "Gen_Male_Twilek_Angry_Medium"},
    "n_gmtwilek_angl": {"_id": "107", "comment": "Gen_Male_Twilek_Angry_Long"},
    "n_gmtwilek_ques": {"_id": "108", "comment": "Gen_Male_Twilek_Question_-_Short"},
    "n_gmtwilek_quem": {"_id": "109", "comment": "Gen_Male_Twilek_Question_-_Medium"},
    "n_gmtwilek_quel": {"_id": "110", "comment": "Gen_Male_Twilek_Question_-_Long"},
    "n_gmtwilek_scrs": {"_id": "111", "comment": "Gen_Male_Twilek_Scared_-_Short"},
    "n_gmtwilek_scrm": {"_id": "112", "comment": "Gen_Male_Twilek_Scared_-_Medium"},
    "n_gmtwilek_scrl": {"_id": "113", "comment": "Gen_Male_Twilek_Scared_-_Long"},
    "n_gmtwilek_ples": {"_id": "114", "comment": "Gen_Male_Twilek_Pleading_-_Short"},
    "n_gmtwilek_plem": {"_id": "115", "comment": "Gen_Male_Twilek_Pleading_-_Medium"},
    "n_gmtwilek_lghs": {"_id": "116", "comment": "Gen_Male_Twilek_Laughter_(mocking)_-_short"},
    "n_gmtwilek_lghm": {"_id": "117", "comment": "Gen_Male_Twilek_Laughter_(mocking)_-_medium"},
    "n_gmtwilek_hpys": {"_id": "118", "comment": "Gen_Male_Twilek_Happy_(thankful)_-_short"},
    "n_gmtwilek_hpym": {"_id": "119", "comment": "Gen_Male_Twilek_Happy_(thankful)_-_medium"},
    "n_gmtwilek_hpyl": {"_id": "120", "comment": "Gen_Male_Twilek_Happy_(thankful)_-_long"},
    "n_gmtwilek_sads": {"_id": "121", "comment": "Gen_Male_Twilek_Sad_-_Short"},
    "n_gmtwilek_sadm": {"_id": "122", "comment": "Gen_Male_Twilek_Sad_-_Medium"},
    "n_gmtwilek_sadl": {"_id": "123", "comment": "Gen_Male_Twilek_Sad_-_Long"},
    "n_gmtwilek_seds": {"_id": "124", "comment": "Gen_Male_Twilek_Seductive_-_Short"},
    "n_gmtwilek_sedm": {"_id": "125", "comment": "Gen_Male_Twilek_Seductive_-_Medium"},
    "n_gmtwilek_sedl": {"_id": "126", "comment": "Gen_Male_Twilek_Seductive_-_Long"},
    "n_gtmtwlek_grts": {"_id": "127", "comment": "Gen_Tough_Male_Twilek_Greeting_Short"},
    "n_gtmtwlek_grtm": {"_id": "128", "comment": "Gen_Tough_Male_Twilek_Greeting_Medium"},
    "n_gtmtwlek_coms1": {"_id": "129", "comment": "Gen_Tough_Male_Twilek_Generic_Comment_-_Short_1"},
    "n_gtmtwlek_coms2": {"_id": "130", "comment": "Gen_Tough_Male_Twilek_Generic_Comment_-_Short_2"},
    "n_gtmtwlek_comm1": {"_id": "131", "comment": "Gen_Tough_Male_Twilek_Generic_Comment_-_Medium_1"},
    "n_gtmtwlek_comm2": {"_id": "132", "comment": "Gen_Tough_Male_Twilek_Generic_Comment_-_Medium_2"},
    "n_gtmtwlek_coml1": {"_id": "133", "comment": "Gen_Tough_Male_Twilek_Generic_Comment_-_Long_1"},
    "n_gtmtwlek_coml2": {"_id": "134", "comment": "Gen_Tough_Male_Twilek_Generic_Comment_-_Long_2"},
    "n_gtmtwlek_angs": {"_id": "135", "comment": "Gen_Tough_Male_Twilek_Angry_Short"},
    "n_gtmtwlek_angm": {"_id": "136", "comment": "Gen_Tough_Male_Twilek_Angry_Medium"},
    "n_gtmtwlek_angl": {"_id": "137", "comment": "Gen_Tough_Male_Twilek_Angry_Long"},
    "n_gtmtwlek_ques": {"_id": "138", "comment": "Gen_Tough_Male_Twilek_Question_-_Short"},
    "n_gtmtwlek_quem": {"_id": "139", "comment": "Gen_Tough_Male_Twilek_Question_-_Medium"},
    "n_gtmtwlek_quel": {"_id": "140", "comment": "Gen_Tough_Male_Twilek_Question_-_Long"},
    "n_gtmtwlek_scrs": {"_id": "141", "comment": "Gen_Tough_Male_Twilek_Scared_-_Short"},
    "n_gtmtwlek_scrm": {"_id": "142", "comment": "Gen_Tough_Male_Twilek_Scared_-_Medium"},
    "n_gtmtwlek_scrl": {"_id": "143", "comment": "Gen_Tough_Male_Twilek_Scared_-_Long"},
    "n_gtmtwlek_ples": {"_id": "144", "comment": "Gen_Tough_Male_Twilek_Pleading_-_Short"},
    "n_gtmtwlek_plem": {"_id": "145", "comment": "Gen_Tough_Male_Twilek_Pleading_-_Medium"},
    "n_gtmtwlek_lghs": {"_id": "146", "comment": "Gen_Tough_Male_Twilek_Laughter_(mocking)_-_short"},
    "n_gtmtwlek_lghm": {"_id": "147", "comment": "Gen_Tough_Male_Twilek_Laughter_(mocking)_-_medium"},
    "n_gtmtwlek_hpys": {"_id": "148", "comment": "Gen_Tough_Male_Twilek_Happy_(thankful)_-_short"},
    "n_gtmtwlek_hpym": {"_id": "149", "comment": "Gen_Tough_Male_Twilek_Happy_(thankful)_-_medium"},
    "n_gtmtwlek_hpyl": {"_id": "150", "comment": "Gen_Tough_Male_Twilek_Happy_(thankful)_-_long"},
    "n_gtmtwlek_sads": {"_id": "151", "comment": "Gen_Tough_Male_Twilek_Sad_-_Short"},
    "n_gtmtwlek_sadm": {"_id": "152", "comment": "Gen_Tough_Male_Twilek_Sad_-_Medium"},
    "n_gtmtwlek_sadl": {"_id": "153", "comment": "Gen_Tough_Male_Twilek_Sad_-_Long"},
    "n_grodian_grts": {"_id": "154", "comment": "Gen_Rodian_Greeting_Short"},
    "n_grodian_grtm": {"_id": "155", "comment": "Gen_Rodian_Greeting_Medium"},
    "n_grodian_coms1": {"_id": "156", "comment": "Gen_Rodian_Generic_Comment_-_Short_1"},
    "n_grodian_coms2": {"_id": "157", "comment": "Gen_Rodian_Generic_Comment_-_Short_2"},
    "n_grodian_comm1": {"_id": "158", "comment": "Gen_Rodian_Generic_Comment_-_Medium_1"},
    "n_grodian_comm2": {"_id": "159", "comment": "Gen_Rodian_Generic_Comment_-_Medium_2"},
    "n_grodian_coml1": {"_id": "160", "comment": "Gen_Rodian_Generic_Comment_-_Long_1"},
    "n_grodian_coml2": {"_id": "161", "comment": "Gen_Rodian_Generic_Comment_-_Long_2"},
    "n_grodian_angs": {"_id": "162", "comment": "Gen_Rodian_Angry_Short"},
    "n_grodian_angm": {"_id": "163", "comment": "Gen_Rodian_Angry_Medium"},
    "n_grodian_angl": {"_id": "164", "comment": "Gen_Rodian_Angry_Long"},
    "n_grodian_ques": {"_id": "165", "comment": "Gen_Rodian_Question_-_Short"},
    "n_grodian_quem": {"_id": "166", "comment": "Gen_Rodian_Question_-_Medium"},
    "n_grodian_quel": {"_id": "167", "comment": "Gen_Rodian_Question_-_Long"},
    "n_grodian_scrs": {"_id": "168", "comment": "Gen_Rodian_Scared_-_Short"},
    "n_grodian_scrm": {"_id": "169", "comment": "Gen_Rodian_Scared_-_Medium"},
    "n_grodian_scrl": {"_id": "170", "comment": "Gen_Rodian_Scared_-_Long"},
    "n_grodian_ples": {"_id": "171", "comment": "Gen_Rodian_Pleading_-_Short"},
    "n_grodian_plem": {"_id": "172", "comment": "Gen_Rodian_Pleading_-_Medium"},
    "n_grodian_lghs": {"_id": "173", "comment": "Gen_Rodian_Laughter_(mocking)_-_short"},
    "n_grodian_lghm": {"_id": "174", "comment": "Gen_Rodian_Laughter_(mocking)_-_medium"},
    "n_grodian_hpys": {"_id": "175", "comment": "Gen_Rodian_Happy_(thankful)_-_short"},
    "n_grodian_hpym": {"_id": "176", "comment": "Gen_Rodian_Happy_(thankful)_-_medium"},
    "n_grodian_hpyl": {"_id": "177", "comment": "Gen_Rodian_Happy_(thankful)_-_long"},
    "n_grodian_sads": {"_id": "178", "comment": "Gen_Rodian_Sad_-_Short"},
    "n_grodian_sadm": {"_id": "179", "comment": "Gen_Rodian_Sad_-_Medium"},
    "n_grodian_sadl": {"_id": "180", "comment": "Gen_Rodian_Sad_-_Long"},
    "n_gtrodian_grts": {"_id": "181", "comment": "Gen_Tough_Rodian_Greeting_Short"},
    "n_gtrodian_grtm": {"_id": "182", "comment": "Gen_Tough_Rodian_Greeting_Medium"},
    "n_gtrodian_coms1": {"_id": "183", "comment": "Gen_Tough_Rodian_Generic_Comment_-_Short_1"},
    "n_gtrodian_coms2": {"_id": "184", "comment": "Gen_Tough_Rodian_Generic_Comment_-_Short_2"},
    "n_gtrodian_comm1": {"_id": "185", "comment": "Gen_Tough_Rodian_Generic_Comment_-_Medium_1"},
    "n_gtrodian_comm2": {"_id": "186", "comment": "Gen_Tough_Rodian_Generic_Comment_-_Medium_2"},
    "n_gtrodian_coml1": {"_id": "187", "comment": "Gen_Tough_Rodian_Generic_Comment_-_Long_1"},
    "n_gtrodian_coml2": {"_id": "188", "comment": "Gen_Tough_Rodian_Generic_Comment_-_Long_2"},
    "n_gtrodian_angs": {"_id": "189", "comment": "Gen_Tough_Rodian_Angry_Short"},
    "n_gtrodian_angm": {"_id": "190", "comment": "Gen_Tough_Rodian_Angry_Medium"},
    "n_gtrodian_angl": {"_id": "191", "comment": "Gen_Tough_Rodian_Angry_Long"},
    "n_gtrodian_ques": {"_id": "192", "comment": "Gen_Tough_Rodian_Question_-_Short"},
    "n_gtrodian_quem": {"_id": "193", "comment": "Gen_Tough_Rodian_Question_-_Medium"},
    "n_gtrodian_quel": {"_id": "194", "comment": "Gen_Tough_Rodian_Question_-_Long"},
    "n_gtrodian_scrs": {"_id": "195", "comment": "Gen_Tough_Rodian_Scared_-_Short"},
    "n_gtrodian_scrm": {"_id": "196", "comment": "Gen_Tough_Rodian_Scared_-_Medium"},
    "n_gtrodian_scrl": {"_id": "197", "comment": "Gen_Tough_Rodian_Scared_-_Long"},
    "n_gtrodian_ples": {"_id": "198", "comment": "Gen_Tough_Rodian_Pleading_-_Short"},
    "n_gtrodian_plem": {"_id": "199", "comment": "Gen_Tough_Rodian_Pleading_-_Medium"},
    "n_gtrodian_lghs": {"_id": "200", "comment": "Gen_Tough_Rodian_Laughter_(mocking)_-_short"},
    "n_gtrodian_lghm": {"_id": "201", "comment": "Gen_Tough_Rodian_Laughter_(mocking)_-_medium"},
    "n_gtrodian_hpys": {"_id": "202", "comment": "Gen_Tough_Rodian_Happy_(thankful)_-_short"},
    "n_gtrodian_hpym": {"_id": "203", "comment": "Gen_Tough_Rodian_Happy_(thankful)_-_medium"},
    "n_gtrodian_hpyl": {"_id": "204", "comment": "Gen_Tough_Rodian_Happy_(thankful)_-_long"},
    "n_gtrodian_sads": {"_id": "205", "comment": "Gen_Tough_Rodian_Sad_-_Short"},
    "n_gtrodian_sadm": {"_id": "206", "comment": "Gen_Tough_Rodian_Sad_-_Medium"},
    "n_gtrodian_sadl": {"_id": "207", "comment": "Gen_Tough_Rodian_Sad_-_Long"},
    "n_grakata_grts": {"_id": "208", "comment": "Gen_Rakatan_Greeting_Short"},
    "n_grakata_grtm": {"_id": "209", "comment": "Gen_Rakatan_Greeting_Medium"},
    "n_grakata_coms1": {"_id": "210", "comment": "Gen_Rakatan_Generic_Comment_-_Short_1"},
    "n_grakata_coms2": {"_id": "211", "comment": "Gen_Rakatan_Generic_Comment_-_Short_2"},
    "n_grakata_comm1": {"_id": "212", "comment": "Gen_Rakatan_Generic_Comment_-_Medium_1"},
    "n_grakata_comm2": {"_id": "213", "comment": "Gen_Rakatan_Generic_Comment_-_Medium_2"},
    "n_grakata_coml1": {"_id": "214", "comment": "Gen_Rakatan_Generic_Comment_-_Long_1"},
    "n_grakata_coml2": {"_id": "215", "comment": "Gen_Rakatan_Generic_Comment_-_Long_2"},
    "n_grakata_angs": {"_id": "216", "comment": "Gen_Rakatan_Angry_Short"},
    "n_grakata_angm": {"_id": "217", "comment": "Gen_Rakatan_Angry_Medium"},
    "n_grakata_angl": {"_id": "218", "comment": "Gen_Rakatan_Angry_Long"},
    "n_grakata_ques": {"_id": "219", "comment": "Gen_Rakatan_Question_-_Short"},
    "n_grakata_quem": {"_id": "220", "comment": "Gen_Rakatan_Question_-_Medium"},
    "n_grakata_quel": {"_id": "221", "comment": "Gen_Rakatan_Question_-_Long"},
    "n_grakata_scrs": {"_id": "222", "comment": "Gen_Rakatan_Scared_-_Short"},
    "n_grakata_scrm": {"_id": "223", "comment": "Gen_Rakatan_Scared_-_Medium"},
    "n_grakata_scrl": {"_id": "224", "comment": "Gen_Rakatan_Scared_-_Long"},
    "n_grakata_ples": {"_id": "225", "comment": "Gen_Rakatan_Pleading_-_Short"},
    "n_grakata_plem": {"_id": "226", "comment": "Gen_Rakatan_Pleading_-_Medium"},
    "n_grakata_lghs": {"_id": "227", "comment": "Gen_Rakatan_Laughter_(mocking)_-_short"},
    "n_grakata_lghm": {"_id": "228", "comment": "Gen_Rakatan_Laughter_(mocking)_-_medium"},
    "n_grakata_hpys": {"_id": "229", "comment": "Gen_Rakatan_Happy_(thankful)_-_short"},
    "n_grakata_hpym": {"_id": "230", "comment": "Gen_Rakatan_Happy_(thankful)_-_medium"},
    "n_grakata_hpyl": {"_id": "231", "comment": "Gen_Rakatan_Happy_(thankful)_-_long"},
    "n_grakata_sads": {"_id": "232", "comment": "Gen_Rakatan_Sad_-_Short"},
    "n_grakata_sadm": {"_id": "233", "comment": "Gen_Rakatan_Sad_-_Medium"},
    "n_grakata_sadl": {"_id": "234", "comment": "Gen_Rakatan_Sad_-_Long"},
    "n_genwrakata_grts": {"_id": "235", "comment": "Gen_Wise_Rakatan_Greeting_Short"},
    "n_genwrakata_grtm": {"_id": "236", "comment": "Gen_Wise_Rakatan_Greeting_Medium"},
    "n_genwrakata_coms1": {"_id": "237", "comment": "Gen_Wise_Rakatan_Generic_Comment_-_Short_1"},
    "n_genwrakata_coms2": {"_id": "238", "comment": "Gen_Wise_Rakatan_Generic_Comment_-_Short_2"},
    "n_genwrakata_comm1": {"_id": "239", "comment": "Gen_Wise_Rakatan_Generic_Comment_-_Medium_1"},
    "n_genwrakata_comm2": {"_id": "240", "comment": "Gen_Wise_Rakatan_Generic_Comment_-_Medium_2"},
    "n_genwrakata_coml1": {"_id": "241", "comment": "Gen_Wise_Rakatan_Generic_Comment_-_Long_1"},
    "n_genwrakata_coml2": {"_id": "242", "comment": "Gen_Wise_Rakatan_Generic_Comment_-_Long_2"},
    "n_genwrakata_angs": {"_id": "243", "comment": "Gen_Wise_Rakatan_Angry_Short"},
    "n_genwrakata_angm": {"_id": "244", "comment": "Gen_Wise_Rakatan_Angry_Medium"},
    "n_genwrakata_angl": {"_id": "245", "comment": "Gen_Wise_Rakatan_Angry_Long"},
    "n_genwrakata_ques": {"_id": "246", "comment": "Gen_Wise_Rakatan_Question_-_Short"},
    "n_genwrakata_quem": {"_id": "247", "comment": "Gen_Wise_Rakatan_Question_-_Medium"},
    "n_genwrakata_quel": {"_id": "248", "comment": "Gen_Wise_Rakatan_Question_-_Long"},
    "n_genwrakata_scrs": {"_id": "249", "comment": "Gen_Wise_Rakatan_Scared_-_Short"},
    "n_genwrakata_scrm": {"_id": "250", "comment": "Gen_Wise_Rakatan_Scared_-_Medium"},
    "n_genwrakata_scrl": {"_id": "251", "comment": "Gen_Wise_Rakatan_Scared_-_Long"},
    "n_genwrakata_ples": {"_id": "252", "comment": "Gen_Wise_Rakatan_Pleading_-_Short"},
    "n_genwrakata_plem": {"_id": "253", "comment": "Gen_Wise_Rakatan_Pleading_-_Medium"},
    "n_genwrakata_lghs": {"_id": "254", "comment": "Gen_Wise_Rakatan_Laughter_(mocking)_-_short"},
    "n_genwrakata_lghm": {"_id": "255", "comment": "Gen_Wise_Rakatan_Laughter_(mocking)_-_medium"},
    "n_genwrakata_hpys": {"_id": "256", "comment": "Gen_Wise_Rakatan_Happy_(thankful)_-_short"},
    "n_genwrakata_hpym": {"_id": "257", "comment": "Gen_Wise_Rakatan_Happy_(thankful)_-_medium"},
    "n_genwrakata_hpyl": {"_id": "258", "comment": "Gen_Wise_Rakatan_Happy_(thankful)_-_long"},
    "n_genwrakata_sads": {"_id": "259", "comment": "Gen_Wise_Rakatan_Sad_-_Short"},
    "n_genwrakata_sadm": {"_id": "260", "comment": "Gen_Wise_Rakatan_Sad_-_Medium"},
    "n_genwrakata_sadl": {"_id": "261", "comment": "Gen_Wise_Rakatan_Sad_-_Long"},
    "n_genjawa_grts1": {"_id": "262", "comment": "Gen_Jawa_Greeting_Short_1"},
    "n_genjawa_grts2": {"_id": "263", "comment": "Gen_Jawa_Greeting_Short_2"},
    "n_genjawa_coms1": {"_id": "264", "comment": "Gen_Jawa_Generic_Comment_-_Short_1"},
    "n_genjawa_coms2": {"_id": "265", "comment": "Gen_Jawa_Generic_Comment_-_Short_2"},
    "n_genjawa_comm1": {"_id": "266", "comment": "Gen_Jawa_Generic_Comment_-_Medium_1"},
    "n_genjawa_comm2": {"_id": "267", "comment": "Gen_Jawa_Generic_Comment_-_Medium_2"},
    "n_genjawa_ques": {"_id": "268", "comment": "Gen_Jawa_Question_-_Short"},
    "n_genjawa_quem": {"_id": "269", "comment": "Gen_Jawa_Question_-_Medium"},
    "n_genhutt_grts": {"_id": "270", "comment": "Gen_Hutt_Greeting_Short"},
    "n_genhutt_coms1": {"_id": "271", "comment": "Gen_Hutt_Generic_Comment_-_Short_1"},
    "n_genhutt_coms2": {"_id": "272", "comment": "Gen_Hutt_Generic_Comment_-_Short_2"},
    "n_genhutt_comm1": {"_id": "273", "comment": "Gen_Hutt_Generic_Comment_-_Medium_1"},
    "n_genhutt_comm2": {"_id": "274", "comment": "Gen_Hutt_Generic_Comment_-_Medium_2"},
    "n_genhutt_coml1": {"_id": "275", "comment": "Gen_Hutt_Generic_Comment_-_Long_1"},
    "n_genhutt_coml2": {"_id": "276", "comment": "Gen_Hutt_Generic_Comment_-_Long_2"},
    "n_genhutt_angm": {"_id": "277", "comment": "Gen_Hutt_Angry_Medium"},
    "n_genhutt_angl": {"_id": "278", "comment": "Gen_Hutt_Angry_Long"},
    "n_genhutt_ques": {"_id": "279", "comment": "Gen_Hutt_Question_-_Short"},
    "n_genhutt_quem": {"_id": "280", "comment": "Gen_Hutt_Question_-_Medium"},
    "n_genhutt_quel": {"_id": "281", "comment": "Gen_Hutt_Question_-_Long"},
    "n_genhutt_scrs": {"_id": "282", "comment": "Gen_Hutt_Scared_-_Short"},
    "n_genhutt_scrm": {"_id": "283", "comment": "Gen_Hutt_Scared_-_Medium"},
    "n_genhutt_lghs": {"_id": "284", "comment": "Gen_Hutt_Laughter_(mocking)_-_short"},
    "n_genhutt_lghm": {"_id": "285", "comment": "Gen_Hutt_Laughter_(mocking)_-_medium"},
    "n_genhutt_hpys": {"_id": "286", "comment": "Gen_Hutt_Happy_(thankful)_-_short"},
    "n_genhutt_hpyl": {"_id": "287", "comment": "Gen_Hutt_Happy_(thankful)_-_long"},
    "n_genduros_grt": {"_id": "288", "comment": "Duros_Greeting_Short"},
    "n_genduros_coms1": {"_id": "289", "comment": "Duros_Generic_Comment_-_Short_1"},
    "n_genduros_coms2": {"_id": "290", "comment": "Duros_Generic_Comment_-_Short_2"},
    "n_genduros_comm1": {"_id": "291", "comment": "Duros_Generic_Comment_-_Medium_1"},
    "n_genduros_comm2": {"_id": "292", "comment": "Duros_Generic_Comment_-_Medium_2"},
    "n_genduros_coml1": {"_id": "293", "comment": "Duros_Generic_Comment_-_Long_1"},
    "n_genduros_coml2": {"_id": "294", "comment": "Duros_Generic_Comment_-_Long_2"},
    "n_genbith_grt": {"_id": "295", "comment": "Bith_Greeting_Short"},
    "n_genbith_coms1": {"_id": "296", "comment": "Bith_Generic_Comment_-_Short_1"},
    "n_genbith_comm1": {"_id": "297", "comment": "Bith_Generic_Comment_-_Medium_1"},
    "n_genbith_coml1": {"_id": "298", "comment": "Bith_Generic_Comment_-_Long_1"}
}


class Globals:
    def __init__(self):
        self.chosen_languages: list[Language] = []
        self.create_fonts: bool = False
        self.convert_tga: bool = False
        self.custom_scaling: float = 1.0
        self.draw_bounds: bool = False
        self.fix_dialog_skipping: bool = False
        self.font_color: float
        self.font_path: Path
        self.install_running: bool = False
        self.install_thread: Thread
        self.max_threads: int = 2
        self.output_log = "log_batch_patcher.log"
        self.patchlogger = PatchLogger()
        self.path: Path
        self.pytranslator: Translator = Translator(Language.ENGLISH)
        self.resolution: int = 2048
        self.set_unskippable: bool = False
        self.translate: bool = False
        self.translation_applied = True

    def __setitem__(self, key, value):
        # Equivalent to setting an attribute
        setattr(self, key, value)

    def __getitem__(self, key):
        # Equivalent to getting an attribute, returns None if not found
        return self.__dict__.get(key, None)

SCRIPT_GLOBALS = Globals()


def get_font_paths_linux() -> list[Path]:
    font_dirs: list[Path] = [Path("/usr/share/fonts/"), Path("/usr/local/share/fonts/"), Path.home() / ".fonts"]
    return [font for font_dir in font_dirs for font in font_dir.glob("**/*.ttf")]


def get_font_paths_macos() -> list[Path]:
    font_dirs: list[Path] = [Path("/Library/Fonts/"), Path("/System/Library/Fonts/"), Path.home() / "Library/Fonts"]
    return [font for font_dir in font_dirs for font in font_dir.glob("**/*.ttf")]


def get_font_paths_windows() -> list[Path]:
    import winreg
    font_registry_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    fonts_dir = Path("C:/Windows/Fonts")
    font_paths = set()

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, font_registry_path) as key:
        for i in range(winreg.QueryInfoKey(key)[1]):  # Number of values in the key
            value: tuple[str, Any, int] = winreg.EnumValue(key, i)
            font_path: Path = fonts_dir / value[1]
            if font_path.suffix.lower() == ".ttf":  # Filtering for .ttf files
                font_paths.add(font_path)
    for file in fonts_dir.safe_rglob("*"):
        if file.suffix.lower() == ".ttf" and file.safe_isfile():
            font_paths.add(file)

    return list(font_paths)


def get_font_paths() -> list[Path]:
    with suppress(Exception):
        os_str = platform.system()
        if os_str == "Linux":
            return get_font_paths_linux()
        if os_str == "Darwin":
            return get_font_paths_macos()
        if os_str == "Windows":
            return get_font_paths_windows()
    msg = "Unsupported operating system"
    raise NotImplementedError(msg)


def relative_path_from_to(src: PurePath, dst: PurePath) -> Path:
    src_parts = list(src.parts)
    dst_parts = list(dst.parts)

    common_length = next(
        (
            i
            for i, (src_part, dst_part) in enumerate(zip(src_parts, dst_parts))
            if src_part != dst_part
        ),
        len(src_parts),
    )
    rel_parts: list[str] = dst_parts[common_length:]
    return Path(*rel_parts)


def log_output(*args, **kwargs):
    # Create an in-memory text stream
    buffer = StringIO()

    # Print to the in-memory stream
    print(*args, file=buffer, **kwargs)

    # Retrieve the printed content
    msg: str = buffer.getvalue()

    # Write the captured output to the file
    with Path("log_batch_patcher.log").open("a", encoding="utf-8", errors="ignore") as f:
        f.write(msg)

    # Print the captured output to console
    # print(*args, **kwargs)
    SCRIPT_GLOBALS.patchlogger.add_note("\t".join(str(arg) for arg in args))


def visual_length(s: str, tab_length=8) -> int:
    if "\t" not in s:
        return len(s)

    # Split the string at tabs, sum the lengths of the substrings,
    # and add the necessary spaces to account for the tab stops.
    parts: list[str] = s.split("\t")
    vis_length: int = sum(len(part) for part in parts)
    for part in parts[:-1]:  # all parts except the last one
        vis_length += tab_length - (len(part) % tab_length)
    return vis_length


def log_output_with_separator(message, below=True, above=False, surround=False):
    if above or surround:
        log_output(visual_length(message) * "-")
    log_output(message)
    if (below and not above) or surround:
        log_output(visual_length(message) * "-")


def patch_nested_gff(
    gff_struct: GFFStruct,
    gff_content: GFFContent,
    gff: GFF,
    current_path: PurePath | Path = None,  # type: ignore[pylance, assignment]
    made_change: bool = False,
    alien_vo_count=-1,
) -> tuple[bool, int]:
    if gff_content != GFFContent.DLG and not SCRIPT_GLOBALS.translate:
        # print(f"Skipping file at '{current_path}', translate not set.")
        return False, alien_vo_count
    if gff_content == GFFContent.DLG:
        if SCRIPT_GLOBALS.fix_dialog_skipping:
            delay = gff_struct.acquire("Delay", None)
            if delay == 0:
                vo_resref = gff_struct.acquire("VO_ResRef", "")
                if vo_resref and vo_resref.strip():
                    log_output(f"Changing Delay at '{current_path}' from {delay} to -1")
                    gff_struct.set_uint32("Delay", 0xFFFFFFFF)
                    made_change = True
        sound: ResRef | None = gff_struct.acquire("Sound", None, ResRef)
        sound_str = str(sound).strip().lower() if sound is not None else ""
        if sound and sound_str.strip() and sound_str in ALIEN_SOUNDS:
            log_output(sound_str, "found in:", str(current_path))
            alien_vo_count += 1

    current_path = PurePath.pathify(current_path or "GFFRoot")
    for label, ftype, value in gff_struct:
        if label.lower() == "mod_name":
            continue
        child_path: PurePath = current_path / label

        if ftype == GFFFieldType.Struct:
            assert isinstance(value, GFFStruct)  # noqa: S101
            result_made_change, alien_vo_count = patch_nested_gff(value, gff_content, gff, child_path, made_change, alien_vo_count)
            made_change |= result_made_change
            continue

        if ftype == GFFFieldType.List:
            assert isinstance(value, GFFList)  # noqa: S101
            result_made_change, alien_vo_count = recurse_through_list(value, gff_content, gff, child_path, made_change, alien_vo_count)
            made_change |= result_made_change
            continue

        if ftype == GFFFieldType.LocalizedString and SCRIPT_GLOBALS.translate:  # and gff_content.value == GFFContent.DLG.value:
            assert isinstance(value, LocalizedString)  # noqa: S101
            new_substrings: dict[int, str] = deepcopy(value._substrings)
            for lang, gender, text in value:
                if SCRIPT_GLOBALS.pytranslator is not None and text is not None and text.strip():
                    log_output_with_separator(f"Translating CExoLocString at {child_path} to {SCRIPT_GLOBALS.pytranslator.to_lang.name}", above=True)
                    translated_text = SCRIPT_GLOBALS.pytranslator.translate(text, from_lang=lang)
                    log_output(f"Translated {text} --> {translated_text}")
                    substring_id = LocalizedString.substring_id(SCRIPT_GLOBALS.pytranslator.to_lang, gender)
                    new_substrings[substring_id] = str(translated_text)
                    made_change = True
            value._substrings = new_substrings
    return made_change, alien_vo_count


def recurse_through_list(
    gff_list: GFFList,
    gff_content: GFFContent,
    gff: GFF,
    current_path: PurePath | Path = None,  # type: ignore[pylance, assignment]
    made_change: bool = False,
    alien_vo_count=-1,
) -> tuple[bool, int]:
    current_path = PurePath.pathify(current_path or "GFFListRoot")
    for list_index, gff_struct in enumerate(gff_list):
        result_made_change, alien_vo_count = patch_nested_gff(gff_struct, gff_content, gff, current_path / str(list_index), made_change, alien_vo_count)
        made_change |= result_made_change
    return made_change, alien_vo_count


def fix_encoding(text: str, encoding: str):
    return text.encode(encoding=encoding, errors="ignore").decode(encoding=encoding, errors="ignore").strip()


def patch_resource(resource: FileResource) -> GFF | TPC | None:
    def translate_entry(tlkentry: TLKEntry, from_lang: Language) -> tuple[str, str]:
        text = tlkentry.text
        if not text.strip() or text.isdigit():
            return text, ""
        if "Do not translate this text" in text:
            return text, text
        if "actual text to be translated" in text:
            return text, text
        return text, SCRIPT_GLOBALS.pytranslator.translate(text, from_lang=from_lang)

    def process_translations(tlk: TLK, from_lang):
        with concurrent.futures.ThreadPoolExecutor(max_workers=SCRIPT_GLOBALS.max_threads) as executor:
            # Create a future for each translation task
            future_to_strref: dict[concurrent.futures.Future[tuple[str, str]], int] = {executor.submit(translate_entry, tlkentry, from_lang): strref for strref, tlkentry in tlk}

            for future in concurrent.futures.as_completed(future_to_strref):
                strref: int = future_to_strref[future]
                try:
                    log_output(f"Translating TLK text at {resource.filepath()} to {SCRIPT_GLOBALS.pytranslator.to_lang.name}")
                    original_text, translated_text = future.result()
                    if translated_text.strip():
                        translated_text = fix_encoding(translated_text, SCRIPT_GLOBALS.pytranslator.to_lang.get_encoding())
                        tlk.replace(strref, translated_text)
                        log_output(f"#{strref} Translated {original_text} --> {translated_text}")
                except Exception as exc:  # pylint: disable=W0718  # noqa: BLE001
                    log_output(format_exception_with_variables(e, message=f"tlk strref {strref} generated an exception: {universal_simplify_exception(exc)}"))
                    print(format_exception_with_variables(exc))

    if resource.restype().extension.lower() == "tlk" and SCRIPT_GLOBALS.translate and SCRIPT_GLOBALS.pytranslator:
        tlk: TLK | None = None
        try:
            log_output(f"Loading TLK '{resource.filepath()}'")
            tlk = read_tlk(resource.data())
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            log_output(format_exception_with_variables(e, message=f"[Error] loading TLK '{resource.identifier()}' at '{resource.filepath()}'!"))
            print(format_exception_with_variables(e))
            return None

        if not tlk:
            message = f"TLK resource missing in memory:\t'{resource.filepath()}'"
            log_output(message)
            return None

        from_lang: Language = tlk.language
        new_filename_stem = f"{resource.resname()}_" + (SCRIPT_GLOBALS.pytranslator.to_lang.get_bcp47_code() or "UNKNOWN")
        new_file_path = (
            resource.filepath().parent
            / f"{new_filename_stem}.{resource.restype().extension}"
        )
        tlk.language = SCRIPT_GLOBALS.pytranslator.to_lang
        process_translations(tlk, from_lang)
        write_tlk(tlk, new_file_path)
        processed_files.add(new_file_path)

    if resource.restype().extension.lower() == "tga" and SCRIPT_GLOBALS.convert_tga:
        log_output(f"Converting TGA at {resource._path_ident_obj} to TPC...")
        return TPCTGAReader(resource.data()).load()

    if resource.restype().name.upper() in {x.name for x in GFFContent}:
        gff: GFF | None = None
        try:
            # log_output(f"Loading {resource.resname()}.{resource.restype().extension} from '{resource.filepath().name}'")
            gff = read_gff(resource.data())
            made_change = False
            if gff.content == GFFContent.DLG and SCRIPT_GLOBALS.set_unskippable:
                skippable = gff.root.acquire("Skippable", None)
                if skippable not in {0, "0"}:
                    conversationtype = gff.root.acquire("ConversationType", None)
                    if conversationtype not in {"1", 1}:
                        alien_owner: str | None = gff.root.acquire("AlienRaceOwner", None)  # TSL only
                        if alien_owner in {"0", 0}:
                            made_change = True
                            gff.root.set_uint8("Skippable", 0)
                            log_output(f"ConversationType: {conversationtype}", f"alien_owner: {alien_owner}", f"Conditions passed, setting dialog unskippable for {resource._path_ident_obj}")
            result_made_change, alien_vo_count = patch_nested_gff(
                gff.root,
                gff.content,
                gff,
                resource._path_ident_obj  # noqa: SLF001
            )
            if not made_change and alien_vo_count < 3 and alien_vo_count != -1 and SCRIPT_GLOBALS.set_unskippable and gff.content == GFFContent.DLG:
                skippable = gff.root.acquire("Skippable", None)
                if skippable not in {0, "0"}:
                    conversationtype = gff.root.acquire("ConversationType", None)
                    if conversationtype not in {"1", 1}:
                        log_output("Skippable", skippable, "alien_vo_count", alien_vo_count, "ConversationType", conversationtype, f"Setting dialog as unskippable in {resource._path_ident_obj}")
                        made_change = True
                        gff.root.set_uint8("Skippable", 0)
            if made_change or result_made_change:
                return gff
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            log_output(format_exception_with_variables(e, message=f"[Error] loading GFF '{resource._path_ident_obj}'!"))
            # raise
            return None

        if not gff:
            log_output(f"GFF resource '{resource._path_ident_obj}' missing in memory")
            return None
    return None


def patch_and_save_noncapsule(resource: FileResource, savedir: Path | None = None):
    patched_data: GFF | TPC | None = patch_resource(resource)
    if patched_data is None:
        return
    capsule = Capsule(resource.filepath()) if resource.inside_capsule else None
    if isinstance(patched_data, GFF):
        new_data = bytes_gff(patched_data)

        new_gff_filename = resource.filename()
        if SCRIPT_GLOBALS.translate:
            new_gff_filename = f"{resource.resname()}_{SCRIPT_GLOBALS.pytranslator.to_lang.get_bcp47_code()}.{resource.restype().extension}"

        new_path = (savedir or resource.filepath().parent) / new_gff_filename
        if new_path.exists() and savedir:
            log_output(f"Skipping '{new_gff_filename}', already exists on disk")
        else:
            log_output(f"Saving patched gff to '{new_path}'")
            BinaryWriter.dump(new_path, new_data)
    elif isinstance(patched_data, TPC):
        if capsule is None:
            txi_file = resource.filepath().with_suffix(".txi")
            if txi_file.is_file():
                log_output("Embedding TXI information...")
                data: bytes = BinaryReader.load_file(txi_file)
                txi_text: str = decode_bytes_with_fallbacks(data)
                patched_data.txi = txi_text
        else:
            txi_data = capsule.resource(resource.resname(), ResourceType.TXI)
            if txi_data is not None:
                log_output("Embedding TXI information from resource found in capsule...")
                txi_text = decode_bytes_with_fallbacks(txi_data)
                patched_data.txi = txi_text

        new_path = (savedir or resource.filepath().parent) / resource.resname()
        new_path = new_path.with_suffix(".tpc")
        if new_path.exists():
            log_output(f"Skipping '{new_path}', already exists on disk")
        else:
            log_output(f"Saving converted tpc to '{new_path}'")
            TPCTGAWriter(patched_data, new_path.with_suffix(".tpc")).write()


def patch_capsule_file(c_file: Path):
    new_data: bytes
    log_output(f"Load {c_file.name}")
    try:
        file_capsule = Capsule(c_file)
    except ValueError as e:
        log_output(f"Could not load '{c_file}'. Reason: {universal_simplify_exception(e)}")
        return

    new_filepath: Path = c_file
    if SCRIPT_GLOBALS.translate:
        new_filepath = c_file.parent / f"{c_file.stem}_{SCRIPT_GLOBALS.pytranslator.to_lang.get_bcp47_code()}{c_file.suffix}"

    new_resources: list[tuple[str, ResourceType, bytes]] = []
    omitted_resources: list[ResourceIdentifier] = []
    for resource in file_capsule:

        patched_data: GFF | TPC | None = patch_resource(resource)
        if isinstance(patched_data, GFF):
            new_data = bytes_gff(patched_data) if patched_data else resource.data()
            log_output(f"Adding patched GFF resource '{resource.identifier()}' to capsule {new_filepath.name}")
            new_resources.append((resource.resname(), resource.restype(), new_data))
            omitted_resources.append(resource.identifier())

        elif isinstance(patched_data, TPC):
            txi_resource = file_capsule.resource(resource.resname(), ResourceType.TXI)
            if txi_resource is not None:
                patched_data.txi = txi_resource.decode("ascii", errors="ignore")
                omitted_resources.append(ResourceIdentifier(resource.resname(), ResourceType.TXI))

            new_data = bytes_tpc(patched_data)
            log_output(f"Adding patched TPC resource '{resource.identifier()}' to capsule {new_filepath.name}")
            new_resources.append((resource.resname(), ResourceType.TPC, new_data))
            omitted_resources.append(resource.identifier())

    erf_or_rim: ERF | RIM = ERF(ERFType.from_extension(new_filepath)) if is_any_erf_type_file(c_file) else RIM()
    for resource in file_capsule:
        if resource.identifier() not in omitted_resources:
            erf_or_rim.set_data(resource.resname(), resource.restype(), resource.data())
    for resinfo in new_resources:
        erf_or_rim.set_data(*resinfo)

    log_output(f"Saving back to {new_filepath.name}")
    if is_any_erf_type_file(c_file):
        write_erf(erf_or_rim, new_filepath)  # type: ignore[arg-type, reportArgumentType]
    else:
        write_rim(erf_or_rim, new_filepath)  # type: ignore[arg-type, reportArgumentType]


def patch_erf_or_rim(resources: list[FileResource], filename: str, erf_or_rim: RIM | ERF) -> PurePath:
    omitted_resources: list[ResourceIdentifier] = []
    new_filename = PurePath(filename)
    if SCRIPT_GLOBALS.translate:
        new_filename = PurePath(f"{new_filename.stem}_{SCRIPT_GLOBALS.pytranslator.to_lang.name}{new_filename.suffix}")

    for resource in resources:
        patched_data: GFF | TPC | None = patch_resource(resource)
        if isinstance(patched_data, GFF):
            log_output(f"Adding patched GFF resource '{resource.identifier()}' to {new_filename}")
            new_data: bytes = bytes_gff(patched_data) if patched_data else resource.data()
            erf_or_rim.set_data(resource.resname(), resource.restype(), new_data)
            omitted_resources.append(resource.identifier())

        elif isinstance(patched_data, TPC):
            log_output(f"Adding patched TPC resource '{resource.resname()}' to {new_filename}")
            txi_resource: FileResource | None = next(
                (
                    res
                    for res in resources
                    if res.resname() == resource.resname()
                    and res.restype() == ResourceType.TXI
                ),
                None,
            )
            if txi_resource:
                patched_data.txi = txi_resource.data().decode("ascii", errors="ignore")
                omitted_resources.append(txi_resource.identifier())

            new_data = bytes_tpc(patched_data)
            erf_or_rim.set_data(resource.resname(), ResourceType.TPC, new_data)
            omitted_resources.append(resource.identifier())
    for resource in resources:
        if resource.identifier() not in omitted_resources:
            erf_or_rim.set_data(resource.resname(), resource.restype(), resource.data())
    return new_filename


def patch_file(file: os.PathLike | str):
    c_file = Path.pathify(file)
    if c_file in processed_files:
        return

    if is_capsule_file(c_file):
        patch_capsule_file(c_file)

    else:
        resname, restype = ResourceIdentifier.from_path(c_file).unpack()
        if restype == ResourceType.INVALID:
            return

        patch_and_save_noncapsule(
            FileResource(
                resname,
                restype,
                c_file.stat().st_size,
                0,
                c_file,
            ),
        )


def patch_folder(folder_path: os.PathLike | str):
    c_folderpath = Path.pathify(folder_path)
    log_output_with_separator(f"Recursing through resources in the '{c_folderpath.name}' folder...", above=True)
    for file_path in c_folderpath.safe_rglob("*"):
        patch_file(file_path)


def patch_install(install_path: os.PathLike | str):
    log_output()
    log_output_with_separator(f"Patching install dir:\t{install_path}", above=True)
    log_output()

    k_install = Installation(install_path)
    k_install.reload_all()
    log_output_with_separator("Patching modules...")
    for module_name, resources in k_install._modules.items():
        res_ident = ResourceIdentifier.from_path(module_name)
        filename = str(res_ident)
        filepath = k_install.path().joinpath("Modules", filename)
        if res_ident.restype == ResourceType.RIM:
            if filepath.with_suffix(".mod").safe_isfile():
                log_output(f"Skipping {filepath}, a .mod already exists at this path.")
                continue
            new_rim = RIM()
            new_rim_filename = patch_erf_or_rim(resources, module_name, new_rim)
            log_output(f"Saving rim {new_rim_filename}")
            write_rim(new_rim, filepath.parent / new_rim_filename, res_ident.restype)

        elif res_ident.restype.name in ERFType.__members__:
            new_erf = ERF(ERFType.__members__[res_ident.restype.name])
            new_erf_filename = patch_erf_or_rim(resources, module_name, new_erf)
            log_output(f"Saving erf {new_erf_filename}")
            write_erf(new_erf, filepath.parent / new_erf_filename, res_ident.restype)

        else:
            log_output("Unsupported module:", module_name, " - cannot patch")

    # nothing by the game uses these rims as far as I can tell
    # log_output_with_separator("Patching rims...")
    # for rim_name, resources in k_install._rims.items():
    #    new_rim = RIM()
    #    res_ident = ResourceIdentifier.from_path(module_name)
    #    filename = str(res_ident)
    #    filepath = k_install.path().joinpath("rims", filename)
    #    new_rim_filename = patch_erf_or_rim(resources, rim_name, new_rim)
    #    log_output(f"Patching {new_rim_filename} in the 'rims' folder ")
    #    write_rim(new_rim, filepath.parent / new_rim_filename)

    log_output_with_separator("Patching Override...")
    override_path = k_install.override_path()
    override_path.mkdir(exist_ok=True, parents=True)
    for folder in k_install.override_list():
        for resource in k_install.override_resources(folder):
            patch_and_save_noncapsule(resource)

    log_output_with_separator("Extract and patch BIF data, saving to Override")
    for resource in k_install.chitin_resources():
        patch_and_save_noncapsule(resource, savedir=override_path)

    patch_file(k_install.path().joinpath("dialog.tlk"))


def is_kotor_install_dir(path: os.PathLike | str) -> bool:
    c_path: CaseAwarePath = CaseAwarePath(path)
    return bool(c_path.safe_isdir() and c_path.joinpath("chitin.key").safe_isfile())


def determine_input_path(path: Path):
    # sourcery skip: assign-if-exp, reintroduce-else
    if not path.safe_exists() or path.resolve() == Path.cwd().resolve():
        msg = "Path does not exist"
        raise FileNotFoundError(msg)

    if is_kotor_install_dir(path):
        return patch_install(path)

    if path.safe_isdir():
        return patch_folder(path)

    if path.safe_isfile():
        return patch_file(path)
    return None


def execute_patchloop_thread():
    try:
        SCRIPT_GLOBALS.install_running = True
        do_main_patchloop()
        SCRIPT_GLOBALS.install_running = False
    except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
        log_output(format_exception_with_variables(e, message="Unhandled exception during the patching process."))
        SCRIPT_GLOBALS.install_running = False
        return messagebox.showerror("Error", f"An error occurred during patching\n{e!r}")


def do_main_patchloop():
    # Validate args
    if not SCRIPT_GLOBALS.chosen_languages:
        if SCRIPT_GLOBALS.translate:
            return messagebox.showwarning("No language chosen", "Select a language first if you want to translate")
        if SCRIPT_GLOBALS.create_fonts:
            return messagebox.showwarning("No language chosen", "Select a language first to create fonts.")
    if SCRIPT_GLOBALS.create_fonts and (not Path(SCRIPT_GLOBALS.font_path).name or not Path(SCRIPT_GLOBALS.font_path).safe_isfile()):
        return messagebox.showwarning(f"Font path not found {SCRIPT_GLOBALS.font_path}", "Please set your font path to a valid TTF font file.")
    if SCRIPT_GLOBALS.translate and not SCRIPT_GLOBALS.translation_applied:
        return messagebox.showwarning("Bad translation args", "Cannot start translation, you have not applied your translation options. (api key, db path, server url etc)")

    # Patching logic
    has_action = False
    if SCRIPT_GLOBALS.create_fonts:
        for lang in SCRIPT_GLOBALS.chosen_languages:
            create_font_pack(lang)
        has_action = True
    if SCRIPT_GLOBALS.translate:
        has_action = True
        for lang in SCRIPT_GLOBALS.chosen_languages:
            main_translate_loop(lang)
    if SCRIPT_GLOBALS.set_unskippable or SCRIPT_GLOBALS.convert_tga or SCRIPT_GLOBALS.fix_dialog_skipping:
        determine_input_path(Path(SCRIPT_GLOBALS.path))
        has_action = True
    if not has_action:
        return messagebox.showwarning("No options chosen", "Select what you want to do.")

    log_output(f"Completed batch patcher of {SCRIPT_GLOBALS.path}")
    return messagebox.showinfo("Patching complete!", "Check the log file log_batch_patcher.log for more information.")


def main_translate_loop(lang: Language):
    print(f"Translating to {lang.name}...")
    SCRIPT_GLOBALS.pytranslator.to_lang = lang
    determine_input_path(Path(SCRIPT_GLOBALS.path))


def create_font_pack(lang: Language):
    print(f"Creating font pack for '{lang.name}'...")
    write_bitmap_fonts(
        Path.cwd() / lang.name,
        SCRIPT_GLOBALS.font_path,
        (SCRIPT_GLOBALS.resolution, SCRIPT_GLOBALS.resolution),
        lang,
        SCRIPT_GLOBALS.draw_bounds,
        SCRIPT_GLOBALS.custom_scaling,
        font_color=SCRIPT_GLOBALS.font_color,
    )


def assign_to_globals(instance: KOTORPatchingToolUI):
    for attr, value in instance.__dict__.items():
        # Convert tkinter variables to their respective Python types
        if isinstance(value, tk.StringVar):
            SCRIPT_GLOBALS[attr] = value.get()
        elif isinstance(value, tk.BooleanVar):
            SCRIPT_GLOBALS[attr] = bool(value.get())
        elif isinstance(value, tk.IntVar):
            SCRIPT_GLOBALS[attr] = int(value.get())
        elif isinstance(value, tk.DoubleVar):
            SCRIPT_GLOBALS[attr] = float(value.get())
        else:
            # Directly assign if it's not a tkinter variable
            SCRIPT_GLOBALS[attr] = value
    SCRIPT_GLOBALS.font_path = Path(instance.font_path.get())
    SCRIPT_GLOBALS.path = Path(instance.path.get())


class KOTORPatchingToolUI:
    def __init__(self, root: tk.Tk):
        self.root: tk.Tk = root
        root.title("KOTOR Translate Tool")

        self.path = tk.StringVar()
        self.set_unskippable = tk.BooleanVar(value=SCRIPT_GLOBALS.set_unskippable)
        self.translate = tk.BooleanVar(value=SCRIPT_GLOBALS.translate)
        self.create_fonts = tk.BooleanVar(value=SCRIPT_GLOBALS.create_fonts)
        self.font_path = tk.StringVar()
        self.resolution = tk.IntVar(value=SCRIPT_GLOBALS.resolution)
        self.custom_scaling = tk.DoubleVar(value=SCRIPT_GLOBALS.custom_scaling)
        self.font_color = tk.StringVar()
        self.draw_bounds = tk.BooleanVar(value=False)
        self.fix_dialog_skipping = tk.BooleanVar(value=False)
        self.convert_tga = tk.BooleanVar(value=False)

        # Middle area for text and scrollbar
        self.output_frame = tk.Frame(self.root)
        self.output_frame.grid_remove()

        self.description_text = tk.Text(self.output_frame, wrap=tk.WORD)
        font_obj = tkfont.Font(font=self.description_text.cget("font"))
        font_obj.configure(size=9)
        self.description_text.configure(font=font_obj)
        self.description_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(self.output_frame, command=self.description_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.lang_vars: dict[Language, tk.BooleanVar] = {}
        self.language_row: int
        self.install_running = False
        self.install_button: ttk.Button
        self.language_frame = ttk.Frame(root)  # Frame to contain language checkboxes
        self.translation_applied: bool = True

        self.initialize_logger()
        self.setup_ui()

    def write_log(self, log: PatchLog):
        """Writes a message to the log.

        Args:
        ----
            message (str): The message to write to the log.

        Returns:
        -------
            None
        Processes the log message by:
            - Setting the description text widget to editable
            - Inserting the message plus a newline at the end of the text
            - Scrolling to the end of the text
            - Making the description text widget not editable again.
        """
        self.description_text.config(state=tk.NORMAL)
        self.description_text.insert(tk.END, log.formatted_message + os.linesep)
        self.description_text.see(tk.END)
        self.description_text.config(state=tk.DISABLED)

    def initialize_logger(self):
        SCRIPT_GLOBALS.patchlogger.verbose_observable.subscribe(self.write_log)
        SCRIPT_GLOBALS.patchlogger.note_observable.subscribe(self.write_log)
        SCRIPT_GLOBALS.patchlogger.warning_observable.subscribe(self.write_log)
        SCRIPT_GLOBALS.patchlogger.error_observable.subscribe(self.write_log)

    def on_gamepaths_chosen(self, event: tk.Event):
        """Adjust the combobox after a short delay."""
        self.root.after(10, lambda: self.move_cursor_to_end(event.widget))

    def move_cursor_to_end(self, combobox: ttk.Combobox):
        """Shows the rightmost portion of the specified combobox as that's the most relevant."""
        combobox.focus_set()
        position: int = len(combobox.get())
        combobox.icursor(position)
        combobox.xview(position)
        self.root.focus_set()

    def setup_ui(self):
        row = 0
        # Path to K1/TSL install
        ttk.Label(self.root, text="Path to K1/TSL install:").grid(row=row, column=0)
        # Gamepaths Combobox
        self.gamepaths = ttk.Combobox(self.root, textvariable=self.path)
        self.gamepaths.grid(row=row, column=1, columnspan=2, sticky="ew")
        self.gamepaths["values"] = [str(path) for game in find_kotor_paths_from_default().values() for path in game]
        self.gamepaths.bind("<<ComboboxSelected>>", self.on_gamepaths_chosen)

        # Browse button
        browse_button = ttk.Button(self.root, text="Browse", command=self.browse_path)
        browse_button.grid(row=row, column=3, padx=2)  # Stick to both sides within its cell
        browse_button.config(width=15)
        row += 1

        # Skippable
        ttk.Label(self.root, text="Make all dialog unskippable:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.set_unskippable).grid(row=row, column=1)
        row += 1

        # Fix skippable dialog bug
        ttk.Label(self.root, text="(experimental) Fix TSL engine dialog skipping bug:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.fix_dialog_skipping).grid(row=row, column=1)
        row += 1

        # TGA -> TPC
        ttk.Label(self.root, text="Convert TGAs to TPCs:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.convert_tga).grid(row=row, column=1)
        row += 1

        # Translate
        ttk.Label(self.root, text="Translate:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.translate).grid(row=row, column=1)
        row += 1

        # Translation Option
        ttk.Label(self.root, text="Translation Option:").grid(row=row, column=0)
        self.translation_option = ttk.Combobox(self.root)
        self.translation_option.grid(row=row, column=1)
        self.translation_option["values"] = [v.name for v in TranslationOption.get_available_translators()]
        self.translation_option.set("GOOGLE_TRANSLATE")
        self.translation_option.bind("<<ComboboxSelected>>", self.on_translation_option_chosen)
        row += 1

        # Max threads
        def on_value_change():
            SCRIPT_GLOBALS.max_threads = int(spinbox_value.get())
        ttk.Label(self.root, text="Max Translation Threads:").grid(row=row, column=0)
        spinbox_value = tk.StringVar(value=str(SCRIPT_GLOBALS.max_threads))
        self.spinbox = tk.Spinbox(root, from_=1, to=2, increment=1, command=on_value_change, textvariable=spinbox_value)
        self.spinbox.grid(row=row, column=1)
        row += 1

        # Upper area for the translation options
        self.translation_ui_options_row = row
        self.translation_options_frame = tk.Frame(self.root)
        self.translation_options_frame.grid(row=row, column=0, sticky="nsew")
        self.translation_options_frame.grid_rowconfigure(0, weight=1)
        self.translation_options_frame.grid_columnconfigure(0, weight=1)
        row += 1

        # Create Fonts
        ttk.Label(self.root, text="Create Fonts:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, text="Yes", variable=self.create_fonts).grid(row=row, column=1)
        row += 1

        # Font Path
        ttk.Label(self.root, text="Font Path:").grid(row=row, column=0)
        ttk.Combobox(self.root, textvariable=self.font_path, values=[str(path_str) for path_str in get_font_paths()]).grid(row=row, column=1)
        ttk.Button(self.root, text="Browse", command=self.browse_font_path).grid(row=row, column=2)
        row += 1

        # Font - Draw Rectangles
        ttk.Label(self.root, text="Draw borders:").grid(row=row, column=0)
        ttk.Checkbutton(self.root, variable=self.draw_bounds).grid(row=row, column=1)
        row += 1

        # Font Resolution
        ttk.Label(self.root, text="Font Resolution:").grid(row=row, column=0)
        ttk.Entry(self.root, textvariable=self.resolution).grid(row=row, column=1)
        row += 1

        def choose_color():
            color_code: tuple[None, None] | tuple[tuple[float, float, float], str] = colorchooser.askcolor(title="Choose a color")
            if color_code[1]:
                self.font_color.set(color_code[1])

        # TODO: parse the .gui or wherever the actual color is stored.
        # self.font_color = tk.StringVar()
        # ttk.Label(self.root, text="Font Color:").grid(row=row, column=0)
        # ttk.Entry(self.root, textvariable=self.font_color).grid(row=row, column=1)
        # tk.Button(self.root, text="Choose Color", command=choose_color).grid(row=row, column=2)
        # row += 1

        # Font Scaling
        ttk.Label(self.root, text="Font Scaling:").grid(row=row, column=0)
        ttk.Entry(self.root, textvariable=self.custom_scaling).grid(row=row, column=1)
        row += 1

        # Logging Enabled
        # ttk.Label(self.root, text="Enable Logging:").grid(row=row, column=0)
        # ttk.Checkbutton(self.root, text="Yes", variable=self.logging_enabled).grid(row=row, column=1)
        # row += 1

        # Use Profiler
        # ttk.Label(self.root, text="Use Profiler:").grid(row=row, column=0)
        # ttk.Checkbutton(self.root, text="Yes", variable=self.use_profiler).grid(row=row, column=1)
        # row += 1

        # Show/Hide output window
        self.show_hide_output = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.root, text="Show Output:", command=lambda: self.toggle_output_frame(self.show_hide_output)).grid(row=row, column=1)
        row += 1

        # To Language
        self.create_language_checkbuttons(row)
        row += len(Language)
        self.output_frame = tk.Frame(self.root)
        self.output_frame.grid(row=self.language_row, column=0, sticky="nsew")
        self.output_frame.grid_rowconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_remove()

        self.description_text = tk.Text(self.output_frame, wrap=tk.WORD)
        font_obj = tkfont.Font(font=self.description_text.cget("font"))
        font_obj.configure(size=9)
        self.description_text.configure(font=font_obj)
        self.description_text.grid(row=0, column=0, sticky="nsew")

        # Start Patching Button
        self.install_button = ttk.Button(self.root, text="Run All Operations", command=self.start_patching)
        self.install_button.grid(row=row, column=1)

    def on_translation_option_chosen(self, event):
        """Create Checkbuttons for each translator option and assign them to the translator.
        Needs rewriting or cleaning, difficult readability lies ahead if you're reading this.
        """
        for widget in self.translation_options_frame.winfo_children():
            widget.destroy()  # remove controls from a different translationoption before adding new ones below

        row = self.translation_ui_options_row
        t_option = TranslationOption.__members__[self.translation_option.get()]
        ui_lambdas_dict: dict[str, Callable[[tk.Frame], ttk.Combobox | ttk.Label | ttk.Checkbutton | ttk.Entry]] = t_option.get_specific_ui_controls()
        varname = None
        value = None
        for varname, ui_control_lambda in ui_lambdas_dict.items():
            ui_control: ttk.Combobox | ttk.Label | ttk.Checkbutton | ttk.Entry = ui_control_lambda(self.translation_options_frame)
            if varname.startswith("descriptor_label") or isinstance(ui_control, ttk.Label):
                ui_control.grid(row=row, column=1)
                continue
            value = ui_control.instate(["selected"]) if isinstance(ui_control, ttk.Checkbutton) else ui_control.get()
            ui_control.grid(row=row, column=2)
            row += 1

        if value is not None and varname is not None:
            self.translation_applied = False
            ttk.Button(self.translation_options_frame, text="Apply Options", command=lambda: self.apply_translation_option(varname=varname, value=value)).grid(row=row, column=2)
        else:
            self.translation_applied = True

    def apply_translation_option(self, varname, value):
        setattr(SCRIPT_GLOBALS.pytranslator, varname, value)  # TODO: add all the variable names to __init__ of Translator class
        self.write_log(f"Applied Options for {self.translation_option.get()}: {varname} = {value}")
        cur_toption: TranslationOption = TranslationOption.__members__[self.translation_option.get()]
        msg: str = cur_toption.validate_args(SCRIPT_GLOBALS.pytranslator)
        if msg:
            messagebox.showwarning("Invalid translation options", msg)
            return
        self.translation_applied = True

    def create_language_checkbuttons(self, row):

        # Show/Hide Languages
        self.show_hide_language = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.root, text="Show/Hide Languages:", command=lambda: self.toggle_language_frame(self.show_hide_language)).grid(row=row, column=1)
        row += 1

        # Middle area for text and scrollbar
        self.language_row = row
        self.language_frame = ttk.Frame(self.root)
        self.language_frame.grid(row=row, column=0, sticky="nsew")
        self.language_frame.grid_rowconfigure(0, weight=1)
        self.language_frame.grid_columnconfigure(0, weight=1)
        self.language_frame.grid_remove()
        row += 1

        # Create a Checkbutton for "ALL"
        all_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.language_frame,
            text="ALL",
            variable=all_var,
            command=lambda: self.toggle_all_languages(all_var),
        ).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        # Sort the languages in alphabetical order
        sorted_languages: list[Language] = sorted(Language, key=lambda lang: lang.name)

        # Create Checkbuttons for each language
        column = 0
        for lang in sorted_languages:
            lang_var = tk.BooleanVar()
            self.lang_vars[lang] = lang_var  # Store reference to the language variable
            ttk.Checkbutton(
                self.language_frame,
                text=lang.name,
                variable=lang_var,
                command=lambda lang=lang, lang_var=lang_var: self.update_chosen_languages(lang, lang_var),
            ).grid(row=row, column=column, sticky="w")

            # Alternate between columns
            column = (column + 1) % 4
            if column == 0:
                row += 1

    def update_chosen_languages(self, lang: Language, lang_var: tk.BooleanVar):
        if lang_var.get():
            SCRIPT_GLOBALS.chosen_languages.append(lang)
        else:
            SCRIPT_GLOBALS.chosen_languages.remove(lang)

    def toggle_all_languages(self, all_var: tk.BooleanVar):
        all_value = all_var.get()
        for lang, lang_var in self.lang_vars.items():
            lang_var.set(all_value)  # Set each language variable to the state of the "ALL" checkbox
            if all_value:
                if lang not in SCRIPT_GLOBALS.chosen_languages:
                    SCRIPT_GLOBALS.chosen_languages.append(lang)
            elif lang in SCRIPT_GLOBALS.chosen_languages:
                SCRIPT_GLOBALS.chosen_languages.remove(lang)

    def toggle_language_frame(self, show_var: tk.BooleanVar):
        show_var.set(not show_var.get())
        if show_var.get():
            self.language_frame.grid(row=self.language_row, column=0, columnspan=4, sticky="ew")
        else:
            self.language_frame.grid_remove()  # Hide the frame

    def toggle_output_frame(self, show_var: tk.BooleanVar):
        show_var.set(not show_var.get())
        if show_var.get():
            self.output_frame.grid(row=self.language_row, column=0, columnspan=4, sticky="ew")
        else:
            self.output_frame.grid_remove()  # Hide the frame

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path.set(directory)

    def browse_font_path(self):
        file = filedialog.askopenfilename()
        if file:
            self.font_path.set(file)

    def start_patching(self):
        if SCRIPT_GLOBALS.install_running:
            return messagebox.showerror("Install already running", "Please wait for all operations to complete. Check the console/output for details.")
        self.install_button.config(state="normal")
        try:
            assign_to_globals(self)
            # Mapping UI input to script logic
            try:
                path = Path(SCRIPT_GLOBALS.path).resolve()
            except OSError as e:
                return messagebox.showerror("Error", f"Invalid path '{SCRIPT_GLOBALS.path}'\n{universal_simplify_exception(e)}")
            else:
                if not path.safe_exists():
                    return messagebox.showerror("Error", "Invalid path")
            SCRIPT_GLOBALS.pytranslator = Translator(Language.ENGLISH)
            SCRIPT_GLOBALS.pytranslator.translation_option = TranslationOption[self.translation_option.get()]
            self.toggle_output_frame(tk.BooleanVar(value=False))

            SCRIPT_GLOBALS.install_thread = Thread(target=execute_patchloop_thread)
            SCRIPT_GLOBALS.install_thread.start()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            messagebox.showerror("Unhandled exception", str(universal_simplify_exception(e)))
            SCRIPT_GLOBALS.install_running = False
            self.install_button.config(state=tk.DISABLED)
        return None

if __name__ == "__main__":
    try:
        root = tk.Tk()
        APP = KOTORPatchingToolUI(root)
        root.mainloop()
    except Exception:  # pylint: disable=W0718  # noqa: BLE001, RUF100
        log_output(traceback.format_exc())
        raise
