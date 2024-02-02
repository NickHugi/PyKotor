from __future__ import annotations

import logging
import os
import pathlib
import sys
from io import StringIO
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest
from pykotor.resource.formats.ncs.ncs_auto import compile_nss
from utility.error_handling import format_exception_with_variables

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game
from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY
from pykotor.extract.installation import Installation
from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import CompileError, EntryPointError
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, InbuiltNCSCompiler
from pykotor.resource.formats.ncs.ncs_data import NCS, NCSCompiler, NCSOptimizer
from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.system.path import Path

if TYPE_CHECKING:
    from ply import yacc
    from pykotor.extract.file import FileResource
    from typing_extensions import Literal

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
NWNNSSCOMP_PATH: str | None = r"C:/Program Files (x86)/KotOR Scripting Tool/nwnnsscomp.exe"
NWNNSSCOMP_PATH2: str | None = r"C:\Program Files (x86)\Kotor Tool\nwnnsscomp.exe"
NWNNSSCOMP_PATH3: str | None = r"C:\Users\boden\Documents\k1 mods\KillCzerkaJerk\tslpatchdata\nwnnsscomp.exe"
LOG_FILENAME = "test_ncs_compilers_install"
ORIG_LOGSTEM = "test_ncs_compilers_install"

CANNOT_COMPILE_EXT: dict[Game, set[str]] = {
    Game.K1: {
        "nwscript.nss"
    },
    Game.K2: {
        "nwscript.nss"
        "a_262imprison_ext3.ncs"  # tslpatcher's nwnnsscomp.exe fails
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
        "k_inc_ebonhawk.nss",
    },
    Game.K2: {
        "nwscript.nss",
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
    nssParser = NssParser(
        library=library,
        constants=KOTOR_CONSTANTS,
        functions=KOTOR_FUNCTIONS,
        library_lookup=library_lookup
    )

    parser: yacc.LRParser = nssParser.parser
    t = parser.parse(script, tracking=True)

    ncs = NCS()
    t.compile(ncs)
    return ncs

@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler("test_output.log"),
                            logging.StreamHandler()
                        ])

    logger = logging.getLogger()
    logger.info("Starting tests")

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

    filepath = (
        Path.cwd().joinpath(f"{LOG_FILENAME}.txt")
        if filepath is None
        else Path.pathify(filepath)
    )
    with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
        f.write(msg)


ALL_INSTALLATIONS: dict[Game, Installation] = {}
if K1_PATH and Path(K1_PATH).joinpath("chitin.key").exists():
    ALL_INSTALLATIONS[Game.K1] = Installation(K1_PATH)
#if K2_PATH and Path(K2_PATH).joinpath("chitin.key").exists():
#    ALL_INSTALLATIONS[Game.K2] = Installation(K2_PATH)

ALL_SCRIPTS: dict[Game, list[tuple[FileResource, Path, Path]]] = {Game.K1: [], Game.K2: []}
TEMP_NSS_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory()
}
TEMP_NCS_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory()
}
for game, installation in ALL_INSTALLATIONS.items():
    for resource in installation:
        if resource.identifier() in CANNOT_COMPILE_EXT[game]:
            log_file(f"Skipping {resource.identifier()}, known incompatible...")
            continue
        if resource.restype() != ResourceType.NSS:
            continue
        nss_path: Path = Path(TEMP_NSS_DIRS[game].name).joinpath(str(resource.identifier()))
        ncs_path: Path = Path(TEMP_NCS_DIRS[game].name).joinpath(resource.resname()).with_suffix(".ncs")
        with nss_path.open("wb") as f:
            f.write(resource.data())
        ALL_SCRIPTS[game].append((resource, nss_path, ncs_path))

def compile_with_abstract_compatible(
    compiler: NCSCompiler,
    nss_path: Path,
    ncs_path: Path,
    game: Game,
) -> Path | None:
    if isinstance(compiler, ExternalNCSCompiler):
        stdout, stderr = compiler.compile_script(nss_path, ncs_path, game)
        log_file(f"{game} {compiler.nwnnsscomp_path} path: {nss_path} stdout: {stdout} stderr: {stderr}")
    else:
        compiler.compile_script(nss_path, ncs_path, game, debug=True)
    return ncs_path if ncs_path.exists() else None

@pytest.mark.parametrize(
    "script_data",
    [
        (game, script)
        for game, scripts in ALL_SCRIPTS.items()
        for script in scripts
    ],
    ids=[f"{'K1' if game == Game.K1 else 'TSL'}_{script[0].identifier}_nwnnsscomp" for game, scripts in ALL_SCRIPTS.items() for script in scripts],
)
def test_external_compiler_compiles(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    compilers: dict[str | None, ExternalNCSCompiler | None] = {
        NWNNSSCOMP_PATH: ExternalNCSCompiler(NWNNSSCOMP_PATH) if NWNNSSCOMP_PATH and Path(NWNNSSCOMP_PATH).exists() else None,
        NWNNSSCOMP_PATH2: ExternalNCSCompiler(NWNNSSCOMP_PATH2) if NWNNSSCOMP_PATH2 and Path(NWNNSSCOMP_PATH2).exists() else None,
        NWNNSSCOMP_PATH3: ExternalNCSCompiler(NWNNSSCOMP_PATH3) if NWNNSSCOMP_PATH3 and Path(NWNNSSCOMP_PATH3).exists() else None,
    }
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    for compiler_path, compiler in compilers.items():
        if compiler is None or compiler_path is None:
            continue
        compiled_path: Path | None = compile_with_abstract_compatible(compiler, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_{Path(compiler_path).stem}"), game)
        if not compiled_path.exists():
            pytest.fail(f"Compilation failed: {compiled_path}")

@pytest.mark.parametrize(
    "script_data",
    [
        (game, script)
        for game, scripts in ALL_SCRIPTS.items()
        for script in scripts
    ],
    ids=[f"{'K1' if game == Game.K1 else 'TSL'}_{script[0].identifier()}_inbuilt" for game, scripts in ALL_SCRIPTS.items() for script in scripts],
)
def test_inbuilt_compiler_compiles(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    compiler = InbuiltNCSCompiler()
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    if file_res.identifier() in CANNOT_COMPILE_BUILTIN[game]:
        return
    compiled_path: Path | None = compile_with_abstract_compatible(compiler, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_inbuilt"), game)
    if not compiled_path.exists():
        pytest.fail(f"Inbuilt compilation failed: {compiled_path}")

@pytest.mark.parametrize(
    "script_data",
    [
        (game, script)
        for game, scripts in ALL_SCRIPTS.items()
        for script in scripts
    ],
    ids=[f"{'K1' if game == Game.K1 else 'TSL'}_{script[0].identifier()}_bizarre" for game, scripts in ALL_SCRIPTS.items() for script in scripts],
)
def test_bizarre_compiler_compiles(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    if file_res.identifier() in CANNOT_COMPILE_BUILTIN[game]:
        return
    try:
        nss_source_str: str = decode_bytes_with_fallbacks(file_res.data())
        ncs_result: NCS = bizarre_compiler(nss_source_str, game, library_lookup=nss_path.parent)
    except EntryPointError as e:
        ...  # these can always be ignored.
    except CompileError as e:
        #self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
        pytest.fail(f"Could not compile '{nss_path.name}' with bizarre!{os.linesep*2} {format_exception_with_variables(e)}")
    except Exception as e:
        #self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
        pytest.fail(f"Unexpected exception compiling '{nss_path.name}' with bizarre!{os.linesep*2} {format_exception_with_variables(e)}")
    else:
        #if not ncs_path.exists():
        #    self.log_file(nss_path.name, filepath="bizarre_incompatible.txt")
        if not isinstance(ncs_result, NCS):
            pytest.fail(f"Failed bizarre compilation, no NCS returned: {nss_path}")
        if not ncs_path.exists():
            pytest.fail(f"{ncs_path} could not be found on disk, bizarre compiler failed.")


@pytest.mark.parametrize(
    "script_data",
    [
        (game, script)
        for game, scripts in ALL_SCRIPTS.items()
        for script in scripts
    ],
    ids=[f"{'K1' if game == Game.K1 else 'TSL'}_{script[0].identifier()}_compile_nss" for game, scripts in ALL_SCRIPTS.items() for script in scripts],
)
def test_pykotor_compile_nss_function(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    if file_res.identifier() in CANNOT_COMPILE_BUILTIN[game]:
        return
    try:
        nss_source_str: str = decode_bytes_with_fallbacks(file_res.data())
        ncs_result: NCS = compile_nss(nss_source_str, game, library_lookup=nss_path.parent)
    except EntryPointError as e:
        ...  # these can always be ignored.
    except CompileError as e:
        pytest.fail(f"Could not compile '{nss_path.name}' with compile_nss!{os.linesep*2} {format_exception_with_variables(e)}")
    except Exception as e:
        pytest.fail(f"Unexpected exception compiling '{nss_path.name}' with compile_nss!{os.linesep*2} {format_exception_with_variables(e)}")
    else:
        if not isinstance(ncs_result, NCS):
            pytest.fail(f"Failed bizarre compilation, no NCS returned: {nss_path}")
        if not ncs_path.exists():
            pytest.fail(f"{ncs_path} could not be found on disk, bizarre compiler failed.")

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-vv"]))
    # Cleanup temporary directories after use
    #for temp_dir in temp_dirs.values():
    #    temp_dir.cleanup()
