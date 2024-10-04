from __future__ import annotations

import os
import pathlib
import sys
import unittest
from io import StringIO
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, ClassVar

THIS_SCRIPT_PATH = pathlib.Path(__file__)
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

from utility.error_handling import format_exception_with_variables
from pathlib import Path

from pykotor.common.misc import Game
from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY
from pykotor.extract.installation import Installation
from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import CompileError, EntryPointError
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.compilers import (
    ExternalNCSCompiler,
    InbuiltNCSCompiler,
)
from pykotor.resource.formats.ncs.ncs_auto import compile_nss
from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks

if TYPE_CHECKING:
    from ply import yacc

    from pykotor.extract.file import FileResource
    from pykotor.resource.formats.ncs.ncs_data import NCSCompiler

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
NWNNSSCOMP_PATH: str | None = r"C:/Program Files (x86)/KotOR Scripting Tool/nwnnsscomp.exe"
NWNNSSCOMP_PATH2: str | None = r"C:\Program Files (x86)\Kotor Tool\nwnnsscomp.exe"
NWNNSSCOMP_PATH3: str | None = r"C:\Users\boden\Documents\k1 mods\KillCzerkaJerk\tslpatchdata\nwnnsscomp.exe"
LOG_FILENAME = "test_ncs_compilers_install"
ORIG_LOGSTEM = "test_ncs_compilers_install"

CANNOT_COMPILE_EXT: dict[Game, set[str]] = {
    Game.K1: {"nwscript.nss"},
    Game.K2: {
        "nwscript.nss" "a_262imprison_ext3.ncs"  # tslpatcher's nwnnsscomp.exe fails
    },
}
CANNOT_COMPILE_BUILTIN: dict[Game, set[str]] = {
    Game.K1: {
        "nwscript.nss",
        "e3_scripts.nss",
        "k_act_bandatt.nss",
        # AddPartyMember takes two arguments but only one was provided:
        "k_act_bastadd.nss",
        "k_act_canderadd.nss",
        "k_act_carthadd.nss",
        "k_act_hk47add.nss",
        "k_act_juhaniadd.nss",
        "k_act_joleeadd.nss",
        "k_act_missionadd.nss",
        "k_act_t3m3add.nss",
        "k_act_zaaladd.nss",
        # Wrong type passed to RemovePartyMember:
        "k_act_bastrmv.nss",
        "k_act_canderrmv.nss",
        "k_act_carthrmv.nss",
        "k_act_hki47rmv.nss",
        "k_act_juhanirmv.nss",
        "k_act_joleermv.nss",
        "k_act_missionrmv.nss",
        "k_act_t3m3rmv.nss",
        "k_act_zaalrmv.nss",
        # Function 'EBO_BastilaStartConversation2' already has a prototype or been defined.
        "k_act_makeitem.nss",
        "k_con_makeitem.nss",
        "k_hen_leadchng.nss",
        "k_inc_ebonhawk.nss",
        "k_inc_cheat.nss",
        "k_inc_dan.nss",
        "k_inc_debug.nss",
        "k_inc_end.nss",
        "k_inc_endgame.nss",
        "k_inc_force.nss",
        "k_inc_generic.nss",
        "k_inc_tat.nss",
        "k_inc_treasure.nss",
        "k_inc_unk.nss",
        "k_pebn_galaxy.nss",
        "k_pdan_belaya02.nss",
        "k_pdan_droid06.nss",
        "k_pdan_droid15.nss",
        "k_pdan_droid50.nss",
        "k_pdan_elise_d.nss",
        "k_pdan_murder55.nss",
        "k_pman_notpaid_c.nss",
        "k_cht_n_zaalbar.nss",
        "k_pdan_kath02.nss",
        "k_pdan_kath04.nss",
        "k_pdan_bastila11.nss",
        "k_pdan_droid02.nss",
        "k_pdan_droid07.nss",
        "k_pdan_droid08.nss",
        "k_pman_door20.nss",
        "k_pdan_droid09.nss",
        "k_pdan_droid13.nss",
        "k_pman_door32.nss",
        "k_pdan_rapid01.nss",
        "k_pdan_rapid02.nss",
        "k_pdan_rapid03.nss",
        "k_pdan_rapid04.nss",
        "k_pend_door04.nss",
        "k_trg_stealth.nss",
        "nw_g0_conversat.nss",
        "nw_s0_lghtnbolt.nss",
        "a_atkonend.nss",
        "a_attonspirit.nss",
        "a_clear_inv.nss",
        "a_force_combat.nss",
        "a_give_quest_hk.nss",
        "a_give_quest_ls.nss",
        "a_give_q_reward.nss",
        "a_master_atck.nss",
        "a_master_half.nss",
        "a_master_kill.nss",
        "a_master_setup.nss",
        "a_rumble.nss",
        "a_walkways.nss",
        "a_walkways2.nss",
        "k_plc_it_eq_glov.nss",
        "k_plc_it_eq_helm.nss",
        "k_plc_it_eq_imp.nss",
        "k_plc_it_up.nss",
        "k_plc_it_up_a.nss",
        "k_plc_it_up_l.nss",
        "k_plc_it_up_l_cr.nss",
        "k_plc_it_up_m.nss",
        "k_plc_it_up_r.nss",
        "k_plc_it_weap.nss",
        "k_plc_it_weap_bp.nss",
        "k_plc_it_weap_br.nss",
        "k_plc_it_weap_l.nss",
        "k_plc_it_weap_m.nss",
        "k_plc_treas_disp.nss",
        "k_plc_treas_empt.nss",
        "k_plc_treas_less.nss",
        "k_plc_treas_more.nss",
        "k_plc_treas_norm.nss",
        "k_plc_treas_per.nss",
        "k_plc_tresciv.nss",
        "k_plc_trescorhig.nss",
        "k_plc_trescorlow.nss",
        "k_plc_trescormid.nss",
        "k_plc_tresdrdhig.nss",
        "k_plc_tresdrdlow.nss",
        "k_plc_tresdrdmid.nss",
        "k_plc_tresmilhig.nss",
        "k_plc_tresmillow.nss",
        "k_plc_tresmilmid.nss",
        "k_plc_tresrakat.nss",
        "k_plc_tresshahig.nss",
        "k_plc_tresshalow.nss",
        "k_plc_tresshamid.nss",
        "k_plc_tressndppl.nss",
        "k_sithas_spawn01.nss",
        "k_sp1_generic.nss",
        "k_sup_galaxymap.nss",
        "k_sup_grenade.nss",
        "k_sup_healing.nss",
        "k_zon_catalog.nss",
        "k_zon_control.nss",
        "unused_conversat.nss",
        "unused_lghtnbolt.nss",
        "unused_sandper.nss",
        "unused_stealth.nss",
        "k_inc_treas_k2.nss",
        "a_next_scene.nss",
        "k_003ebo_enter.nss",
        "k_inc_hawk.nss",
        "a_grenn_cut.nss",
        "k_pman_28c_sur01.nss",
        "k_pman_arg01.nss",
        "c_pc_party_not.nss",
        "k_act_com45.nss",
        "k_ai_master.nss",
        "k_amb_prey_spawn.nss",
        "k_amb_prey_ude.nss",
        "k_combat_rnd.nss",
        "k_contain_bash.nss",
        "k_contain_unlock.nss",
        "k_death_give_ls.nss",
        "k_def_ambient.nss",
        "k_def_ambmob.nss",
        "k_def_ambmobtrea.nss",
        "k_def_grenspn.nss",
        "k_def_repairsp.nss",
        "k_def_repairsptr.nss",
        "k_def_rependd.nss",
        "k_def_repuser.nss",
        "k_def_spawn01.nss",
        "k_def_spn_t_drd.nss",
        "k_def_spn_t_empt.nss",
        "k_def_spn_t_jedi.nss",
        "k_def_spn_t_less.nss",
        "k_def_spn_t_more.nss",
        "k_def_spn_t_none.nss",
        "k_def_spn_t_per.nss",
        "k_def_userdef01.nss",
        "k_fmine_spawn.nss",
        "k_hen_attondlg.nss",
        "k_hen_baodurdlg.nss",
        "k_hen_discipdlg.nss",
        "k_hen_g0t0dlg.nss",
        "k_hen_hanharrdlg.nss",
        "k_hen_hk47dlg.nss",
        "k_hen_hndmaiddlg.nss",
        "k_hen_kreiadlg.nss",
        "k_hen_manddlg.nss",
        "k_hen_miradlg.nss",
        "k_hen_remotedlg.nss",
        "k_hen_retreat.nss",
        "k_hen_spawn01.nss",
        "k_hen_t3m4dlg.nss",
        "k_hen_visasdlg.nss",
        "k_inc_fakecombat.nss",
        "k_inc_quest_hk.nss",
        "k_inc_zone.nss",
        "k_oei_hench_inc.nss",
        "k_oei_spawn.nss",
        "k_oei_userdef.nss",
        "k_plc_it_arm.nss",
        "k_plc_it_arm_h.nss",
        "k_plc_it_arm_l.nss",
        "k_plc_it_arm_m.nss",
        "k_plc_it_arm_r.nss",
        "k_plc_it_d_shld.nss",
        "k_plc_it_d_stim.nss",
        "k_plc_it_eq.nss",
        "k_plc_it_eq_belt.nss",
    },
    Game.K2: {
        "nwscript.nss",
        "a_move_wp.nss",
        "a_rumble.nss",
        "a_set000cheat.nss",
        "k_plc_it_up_m.nss",
        "k_plc_it_up_r.nss",
        "k_plc_it_weap.nss",
        "k_plc_it_weap_bp.nss",
        "k_plc_it_weap_br.nss",
        "k_act_makeitem.nss",
        "k_con_makeitem.nss",
        "k_hen_leadchng.nss",
        "k_inc_ebonhawk.nss",
        "k_inc_cheat.nss",
        "k_inc_dan.nss",
        "k_inc_debug.nss",
        "k_inc_end.nss",
        "k_inc_endgame.nss",
        "k_inc_force.nss",
        "k_inc_generic.nss",
        "k_inc_tat.nss",
        "k_inc_treasure.nss",
        "k_inc_unk.nss",
        "k_pebn_galaxy.nss",
        "k_pdan_belaya02.nss",
        "k_pdan_droid06.nss",
        "k_pdan_droid15.nss",
        "k_pdan_droid50.nss",
        "k_pdan_elise_d.nss",
        "k_pdan_murder55.nss",
        "k_pman_notpaid_c.nss",
        "k_cht_n_zaalbar.nss",
        "k_pdan_kath02.nss",
        "k_pdan_kath04.nss",
        "e3_scripts.nss",
        "k_act_bastadd.nss",
        "k_pdan_bastila11.nss",
        "k_act_bastrmv.nss",
        "k_act_canderrmv.nss",
        "k_act_carthrmv.nss",
        "k_pdan_droid02.nss",
        "k_act_hki47rmv.nss",
        "k_act_joleermv.nss",
        "k_act_juhanirmv.nss",
        "k_act_missionrmv.nss",
        "k_act_t3m3rmv.nss",
        "k_pdan_droid07.nss",
        "k_pdan_droid08.nss",
        "k_act_zaalrmv.nss",
        "k_pman_door20.nss",
        "k_pdan_droid09.nss",
        "k_pdan_droid13.nss",
        "k_pman_door32.nss",
        "k_pdan_rapid01.nss",
        "k_pdan_rapid02.nss",
        "k_pdan_rapid03.nss",
        "k_pdan_rapid04.nss",
        "k_pend_door04.nss",
        "k_trg_stealth.nss",
        "nw_g0_conversat.nss",
        "nw_s0_lghtnbolt.nss",
        "a_atkonend.nss",
        "a_attonspirit.nss",
        "a_clear_inv.nss",
        "a_force_combat.nss",
        "a_give_quest_hk.nss",
        "a_give_quest_ls.nss",
        "a_give_q_reward.nss",
        "a_master_atck.nss",
        "a_master_half.nss",
        "a_master_kill.nss",
        "a_master_setup.nss",
        "a_walkways.nss",
        "a_walkways2.nss",
        "k_plc_it_eq_glov.nss",
        "k_plc_it_eq_helm.nss",
        "k_plc_it_eq_imp.nss",
        "k_plc_it_up.nss",
        "k_plc_it_up_a.nss",
        "k_plc_it_up_l.nss",
        "k_plc_it_up_l_cr.nss",
        "k_plc_it_weap_l.nss",
        "k_plc_it_weap_m.nss",
        "k_plc_treas_disp.nss",
        "k_plc_treas_empt.nss",
        "k_plc_treas_less.nss",
        "k_plc_treas_more.nss",
        "k_plc_treas_norm.nss",
        "k_plc_treas_per.nss",
        "k_plc_tresciv.nss",
        "k_plc_trescorhig.nss",
        "k_plc_trescorlow.nss",
        "k_plc_trescormid.nss",
        "k_plc_tresdrdhig.nss",
        "k_plc_tresdrdlow.nss",
        "k_plc_tresdrdmid.nss",
        "k_plc_tresmilhig.nss",
        "k_plc_tresmillow.nss",
        "k_plc_tresmilmid.nss",
        "k_plc_tresrakat.nss",
        "k_plc_tresshahig.nss",
        "k_plc_tresshalow.nss",
        "k_plc_tresshamid.nss",
        "k_plc_tressndppl.nss",
        "k_sithas_spawn01.nss",
        "k_sp1_generic.nss",
        "k_sup_galaxymap.nss",
        "k_sup_grenade.nss",
        "k_sup_healing.nss",
        "k_zon_catalog.nss",
        "k_zon_control.nss",
        "unused_conversat.nss",
        "unused_lghtnbolt.nss",
        "unused_sandper.nss",
        "unused_stealth.nss",
        "k_inc_treas_k2.nss",
        "a_next_scene.nss",
        "k_003ebo_enter.nss",
        "k_inc_hawk.nss",
        "a_grenn_cut.nss",
        "k_pman_28c_sur01.nss",
        "k_pman_arg01.nss",
        "c_pc_party_not.nss",
        "k_act_com45.nss",
        "k_ai_master.nss",
        "k_amb_prey_spawn.nss",
        "k_amb_prey_ude.nss",
        "k_combat_rnd.nss",
        "k_contain_bash.nss",
        "k_contain_unlock.nss",
        "k_death_give_ls.nss",
        "k_def_ambient.nss",
        "k_def_ambmob.nss",
        "k_def_ambmobtrea.nss",
        "k_def_grenspn.nss",
        "k_def_repairsp.nss",
        "k_def_repairsptr.nss",
        "k_def_rependd.nss",
        "k_def_repuser.nss",
        "k_def_spawn01.nss",
        "k_def_spn_t_drd.nss",
        "k_def_spn_t_empt.nss",
        "k_def_spn_t_jedi.nss",
        "k_def_spn_t_less.nss",
        "k_def_spn_t_more.nss",
        "k_def_spn_t_none.nss",
        "k_def_spn_t_per.nss",
        "k_def_userdef01.nss",
        "k_fmine_spawn.nss",
        "k_hen_attondlg.nss",
        "k_hen_baodurdlg.nss",
        "k_hen_discipdlg.nss",
        "k_hen_g0t0dlg.nss",
        "k_hen_hanharrdlg.nss",
        "k_hen_hk47dlg.nss",
        "k_hen_hndmaiddlg.nss",
        "k_hen_kreiadlg.nss",
        "k_hen_manddlg.nss",
        "k_hen_miradlg.nss",
        "k_hen_remotedlg.nss",
        "k_hen_retreat.nss",
        "k_hen_spawn01.nss",
        "k_hen_t3m4dlg.nss",
        "k_hen_visasdlg.nss",
        "k_inc_fakecombat.nss",
        "k_inc_quest_hk.nss",
        "k_inc_zone.nss",
        "k_oei_hench_inc.nss",
        "k_oei_spawn.nss",
        "k_oei_userdef.nss",
        "k_plc_it_arm.nss",
        "k_plc_it_arm_h.nss",
        "k_plc_it_arm_l.nss",
        "k_plc_it_arm_m.nss",
        "k_plc_it_arm_r.nss",
        "k_plc_it_d_shld.nss",
        "k_plc_it_d_stim.nss",
        "k_plc_it_eq.nss",
        "k_plc_it_eq_belt.nss",
    },
}


def bizarre_compiler(
    script: str,
    game: Game,
    library: dict[str, bytes] | None = None,
    library_lookup: list[str | Path] | list[str] | list[Path] | str | Path | None = None,
) -> NCS:
    if not library:
        library = KOTOR_LIBRARY if game == Game.K1 else TSL_LIBRARY
    _nssLexer = NssLexer()
    nssParser = NssParser(library=library, constants=KOTOR_CONSTANTS, functions=KOTOR_FUNCTIONS, library_lookup=library_lookup)

    parser: yacc.LRParser = nssParser.parser
    t = parser.parse(script, tracking=True)

    ncs = NCS()
    t.compile(ncs)
    return ncs


@unittest.skipIf(
    (
        not NWNNSSCOMP_PATH
        or not Path(NWNNSSCOMP_PATH).exists()
        or ((not K1_PATH or not Path(K1_PATH).joinpath("chitin.key").exists()) and (not K2_PATH or not Path(K2_PATH).joinpath("chitin.key").exists()))
    ),
    "K1_PATH/K2_PATH/NWNNSSCOMP_PATH environment variable is not set or not found on disk.",
)
class TestCompileInstallation(unittest.TestCase):
    # define these here otherwise mypy complains
    ext_compiler1: ExternalNCSCompiler | None = ExternalNCSCompiler(NWNNSSCOMP_PATH) if NWNNSSCOMP_PATH and Path(NWNNSSCOMP_PATH).exists() else None
    ext_compiler2: ExternalNCSCompiler | None = ExternalNCSCompiler(NWNNSSCOMP_PATH2) if NWNNSSCOMP_PATH2 and Path(NWNNSSCOMP_PATH2).exists() else None
    ext_compiler3: ExternalNCSCompiler | None = ExternalNCSCompiler(NWNNSSCOMP_PATH3) if NWNNSSCOMP_PATH3 and Path(NWNNSSCOMP_PATH3).exists() else None
    inbuilt_compiler = InbuiltNCSCompiler()
    all_scripts: ClassVar[dict[Game, list[tuple[FileResource, Path, Path]]]] = {
        Game.K1: [],
        Game.K2: [],
    }
    all_nss_paths: ClassVar[dict[Game, Path]] = {Game.K1: Path(TemporaryDirectory().name), Game.K2: Path(TemporaryDirectory().name)}
    installations: ClassVar[dict[Game, Installation]] = {}

    @classmethod
    def setUpClass(cls):
        try:
            # Remove old files
            Path.cwd().joinpath("pykotor_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("inbuilt_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("nwnnsscomp_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("nwnnsscomp2_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("nwnnsscomp3_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath(f"{ORIG_LOGSTEM}_k1.txt").unlink(missing_ok=True)
            Path.cwd().joinpath(f"{ORIG_LOGSTEM}_k2.txt").unlink(missing_ok=True)

            for path in cls.all_nss_paths.values():
                path.mkdir(parents=True)

            # Load installations
            if K1_PATH is not None and Path(K1_PATH).joinpath("chitin.key").exists():
                cls.installations[Game.K1] = Installation(K1_PATH)
                cls.setup_extracted_scripts(Game.K1)
            if K2_PATH is not None and Path(K2_PATH).joinpath("chitin.key").exists():
                cls.installations[Game.K2] = Installation(K2_PATH)
                cls.setup_extracted_scripts(Game.K2)
        except Exception:
            cls.tearDownClass()
            raise  # to still mark the test as failed.

    @classmethod
    def tearDownClass(cls):
        import shutil

        shutil.rmtree(cls.all_nss_paths[Game.K1], ignore_errors=True)
        shutil.rmtree(cls.all_nss_paths[Game.K2], ignore_errors=True)

    @classmethod
    def setup_extracted_scripts(
        cls,
        game: Game,
    ):
        for resource in cls.installations[game]:
            if resource.identifier() in CANNOT_COMPILE_EXT[game]:
                cls.log_file(f"Skipping {resource.identifier()}, known incompatible...")
                continue
            if resource.restype() is not ResourceType.NSS:
                continue

            temp_nss_path: Path = cls.all_nss_paths[game].joinpath(str(resource.identifier()))
            temp_ncs_path: Path = temp_nss_path.with_suffix(".ncs")
            with temp_nss_path.open("w", encoding="utf-8") as f:
                str_script: str = decode_bytes_with_fallbacks(resource.data())
                f.write(str_script)

            cls.all_scripts[game].append((resource, temp_nss_path, temp_ncs_path))

    @staticmethod
    def log_file(
        *args,
        filepath: os.PathLike | str | None = None,
        file: StringIO | None = None,
        **kwargs,
    ):
        # Create an in-memory text stream
        buffer: StringIO = file or StringIO()
        # Print to the in-memory stream
        print(*args, file=buffer, **kwargs)

        # Retrieve the printed content
        msg: str = buffer.getvalue()

        # Print the captured output to console
        print(*args, **kwargs)  # noqa: T201

        filepath = Path.cwd().joinpath(f"{LOG_FILENAME}.txt") if filepath is None else Path(filepath)
        with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
            f.write(msg)

    def compile_with_abstract_compatible(
        self,
        compiler: NCSCompiler | None,
        nss_path: Path,
        ncs_path: Path,
        game: Game,
    ) -> Path | None:
        if compiler is None:
            return None
        if isinstance(compiler, ExternalNCSCompiler):
            stdout, stderr = compiler.compile_script(nss_path, ncs_path, game)
            self.log_file(game, compiler.nwnnsscomp_path, "path:", nss_path, "stdout:", stdout, f"stderr:\t{stderr}" if stderr else "")
        else:
            compiler.compile_script(nss_path, ncs_path, game, debug=False)
        return ncs_path

    def _test_nwnnsscomp_compiles(self, game):
        for script_info in self.all_scripts[game]:
            file_res, nss_path, ncs_path = script_info
            compiled_paths: list[Path | None] = [
                self.compile_with_abstract_compatible(self.ext_compiler1, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_ext1"), game),
                self.compile_with_abstract_compatible(self.ext_compiler2, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_ext2"), game),
                self.compile_with_abstract_compatible(self.ext_compiler3, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_ext3"), game),
            ]

            # Filter out None paths (from compilers that weren't defined)
            compiled_paths = [path for path in compiled_paths if path is not None]

            # Check if all existing paths have the same existence status
            if not compiled_paths:
                return

            existence_status: list[bool] = [path.exists() for path in compiled_paths]
            assert all(
                status == existence_status[0] for status in existence_status
            ), f"Mismatch in compilation results: {[path for path, exists in zip(compiled_paths, existence_status) if not exists]}"  # noqa: S101
            assert all(existence_status), f"Compilation failed: {[path for path, exists in zip(compiled_paths, existence_status) if not exists]}"

    def _test_inbuilt_compiler(self, game: Game):
        for script_info in self.all_scripts[game]:
            file_res, nss_path, ncs_path = script_info
            if file_res.identifier() in CANNOT_COMPILE_BUILTIN[game]:
                self.log_file(f"Skipping {file_res.identifier()}, known incompatible with inbuilt...")
                continue

            try:
                compiled_path: Path | None = self.compile_with_abstract_compatible(self.inbuilt_compiler, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_inbuilt"), game)
            except EntryPointError as e:
                ...
            except CompileError as e:
                # self.log_file(nss_path.name, filepath="inbuilt_incompatible.txt")
                self.fail(f"Could not compile {nss_path.name} with inbuilt!{os.linesep * 2} {format_exception_with_variables(e)}")
            except Exception as e:
                # self.log_file(nss_path.name, filepath="inbuilt_incompatible.txt")
                self.fail(f"Unexpected exception compiling '{nss_path.name}' with inbuilt!{os.linesep * 2} {format_exception_with_variables(e)}")
            else:
                # if not compiled_path.exists():
                #    self.log_file(nss_path.name, filepath="inbuilt_incompatible.txt")
                assert compiled_path.exists(), f"{compiled_path} could not be found on disk, inbuilt compiler failed."  # noqa: S101

    def _test_bizarre_compiler(self, game: Game):
        for script_info in self.all_scripts[game]:
            file_res, nss_path, ncs_path = script_info
            if file_res.identifier() in CANNOT_COMPILE_BUILTIN[game]:
                self.log_file(f"Skipping {file_res.identifier()}, known incompatible with inbuilt...")
                continue

            try:
                nss_source_str: str = decode_bytes_with_fallbacks(file_res.data())
                ncs_result: NCS = bizarre_compiler(nss_source_str, game, library_lookup=nss_path.parent)
            except EntryPointError as e:
                ...
            except CompileError as e:
                # self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
                self.fail(f"Could not compile {nss_path.name} with bizarre compiler!{os.linesep * 2} {format_exception_with_variables(e)}")
            else:
                # if not isinstance(ncs_result, NCS):
                #    self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
                assert isinstance(ncs_result, NCS), f"{nss_path.name} was compiled and return as {ncs_result.__class__.__name__} instead of NCS."  # noqa: S101

    def _test_builtin_compile_nss(self, game: Game):
        for script_info in self.all_scripts[game]:
            file_res, nss_path, ncs_path = script_info
            if file_res.identifier() in CANNOT_COMPILE_BUILTIN[game]:
                self.log_file(f"Skipping {file_res.identifier()}, known incompatible with inbuilt...")
                continue
            try:
                nss_source_str: str = decode_bytes_with_fallbacks(file_res.data())
                ncs_result: NCS = compile_nss(nss_source_str, game, library_lookup=nss_path.parent, debug=False)
            except EntryPointError as e:
                ...
            except CompileError as e:
                # self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
                self.fail(f"Could not compile {nss_path.name} with compile_nss!{os.linesep * 2} {format_exception_with_variables(e)}")
            except Exception as e:
                # self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
                self.fail(
                    f"Unexpected exception besides CompileError thrown while compiling {nss_path.name} with compile_nss!{os.linesep * 2} {format_exception_with_variables(e)}"
                )
            else:
                # if not isinstance(ncs_result, NCS):
                #    self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
                assert isinstance(ncs_result, NCS), f"{nss_path.name} was compiled and return as {ncs_result.__class__.__name__} instead of NCS."  # noqa: S101

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_nwnnsscomp_compiles(self):
        self._test_nwnnsscomp_compiles(Game.K1)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_nwnnsscomp_compiles(self):
        self._test_nwnnsscomp_compiles(Game.K2)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_inbuilt_compiler(self):
        self._test_inbuilt_compiler(Game.K1)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_inbuilt_compiler(self):
        self._test_inbuilt_compiler(Game.K2)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_bizarre_compiler(self):
        self._test_bizarre_compiler(Game.K1)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_bizarre_compiler(self):
        self._test_bizarre_compiler(Game.K2)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_compile_nss(self):
        self._test_builtin_compile_nss(Game.K1)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_compile_nss(self):
        self._test_builtin_compile_nss(Game.K2)


if __name__ == "__main__":
    unittest.main()
