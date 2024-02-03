from __future__ import annotations

import cProfile
import logging
import os
import pathlib
import sys
from io import StringIO
from logging.handlers import RotatingFileHandler
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").is_dir():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").is_dir():
    add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game  # noqa: E402
from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS  # noqa: E402
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.resource.formats.ncs.compiler.classes import CompileError, EntryPointError  # noqa: E402
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer  # noqa: E402
from pykotor.resource.formats.ncs.compiler.parser import NssParser  # noqa: E402
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, InbuiltNCSCompiler  # noqa: E402
from pykotor.resource.formats.ncs.ncs_auto import compile_nss  # noqa: E402
from pykotor.resource.formats.ncs.ncs_data import NCS, NCSCompiler  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402
from utility.error_handling import format_exception_with_variables, universal_simplify_exception  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from _pytest.reports import TestReport
    from ply import yacc
    from pykotor.extract.file import FileResource

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
NWNNSSCOMP_PATH: str | None = r"C:/Program Files (x86)/KotOR Scripting Tool/nwnnsscomp.exe"
NWNNSSCOMP_PATH2: str | None = r"C:\Program Files (x86)\Kotor Tool\nwnnsscomp.exe"
NWNNSSCOMP_PATH3: str | None = r"C:\Users\boden\Documents\k1 mods\KillCzerkaJerk\tslpatchdata\nwnnsscomp.exe"
LOG_FILENAME = "test_ncs_compilers_install"


def setup_logger():
    # Configure logger for failed test cases
    logger = logging.getLogger('failed_tests_logger')
    logger.setLevel(logging.DEBUG)

    # Primary log file handler
    fh = RotatingFileHandler('FAILED_TESTS.log', maxBytes=5*1024*1024, backupCount=5, mode='a')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Additional fallback file handlers
    fallback_filenames = ['FAILED_TESTS_1.log', 'FAILED_TESTS_2.log', 'FAILED_TESTS_3.log', 'FAILED_TESTS_4.log']
    for filename in fallback_filenames:
        fh_fallback = logging.FileHandler(filename, mode='a')
        fh_fallback.setFormatter(formatter)
        logger.addHandler(fh_fallback)

    return logger

logger = setup_logger()


# pytest hook to check test outcomes
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> TestReport | None:
    if "setup" in call.when:
        # Skip setup phase
        return None
    if call.excinfo is not None and call.when == "call":
        # This means the test has failed
        longrepr = format_exception_with_variables(call.excinfo.value, call.excinfo.type, call.excinfo.tb)  # alternatively use call.excinfo.getrepr() for full traceback
        logger.error("Test failed with exception!", extra={"item.nodeid": item.nodeid, "Traceback: ": longrepr})

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

# Don't trust pytest's logger, use fallbacks to ensure information isn't lost.
def _handle_compile_exc(e: Exception, nss_path: Path, compiler_id_str: str, game: Game):
    exc_type_name, exc_basic_info_str = universal_simplify_exception(e)
    exc_debug_info_str = format_exception_with_variables(e)

    prefix_msg = "Could not compile " if e.__class__ is CompileError else f"Unexpected exception of type '{exc_type_name}' occurred when compiling"
    msg = f"{prefix_msg} '{nss_path.name}' with '{compiler_id_str}' compiler!"
    exc_separator_str = "-" * len(msg)

    msg_info_level = os.linesep.join((msg, exc_basic_info_str, exc_separator_str))
    msg_debug_level = os.linesep.join((msg, exc_debug_info_str, exc_separator_str))

    log_file(msg_info_level, filepath=f"fallback_level_info_{game}.txt")
    log_file(msg_debug_level, filepath=f"fallback_level_debug_{game}.txt")
    log_file(f'"{nss_path.name}",', filepath=f"{compiler_id_str}_incompatible_{game}.txt")  # for quick copy/paste into the known_issues hashset
    logger.log(level=40, msg=msg_debug_level)
    pytest.fail(msg_info_level)

def compile_with_abstract_compatible(
    compiler: NCSCompiler,
    nss_path: Path,
    ncs_path: Path,
    game: Game,
):
    compiler_id_str = "inbuilt"
    try:
        if isinstance(compiler, ExternalNCSCompiler):
            compiler_id_str = "nwnnsscomp.exe"
            try:
                stdout, stderr = compiler.compile_script(nss_path, ncs_path, game)
            except EntryPointError as e:
                pytest.xfail(f"Inbuilt: No entry point in with '{nss_path.name}': {e}")
            else:
                if stderr:
                    raise CompileError(f"{stdout}: {stderr}")
        else:
            try:
                compiler.compile_script(nss_path, ncs_path, game, debug=False)
            except EntryPointError as e:
                pytest.xfail(f"Inbuilt: No entry point in with '{nss_path.name}': {e}")

        if not ncs_path.is_file():
            # raise it so _handle_compile_exc can be used to reduce duplicated logging code.
            new_exc = FileNotFoundError(f"Could not find NCS compiled script on disk, {compiler_id_str} compiler failed.")
            new_exc.filename = ncs_path
            raise new_exc  # noqa: TRY301

    except Exception as e:  # noqa: BLE001
        _handle_compile_exc(e, nss_path, compiler_id_str, game)

def test_external_compiler_compiles(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    compilers: dict[str | None, ExternalNCSCompiler | None] = {
        NWNNSSCOMP_PATH: ExternalNCSCompiler(NWNNSSCOMP_PATH) if NWNNSSCOMP_PATH and Path(NWNNSSCOMP_PATH).is_file() else None,
        NWNNSSCOMP_PATH2: ExternalNCSCompiler(NWNNSSCOMP_PATH2) if NWNNSSCOMP_PATH2 and Path(NWNNSSCOMP_PATH2).is_file() else None,
        NWNNSSCOMP_PATH3: ExternalNCSCompiler(NWNNSSCOMP_PATH3) if NWNNSSCOMP_PATH3 and Path(NWNNSSCOMP_PATH3).is_file() else None,
    }
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    for compiler_path, compiler in compilers.items():
        if compiler is None or compiler_path is None:
            continue  # don't test nonexistent compilers
        compile_with_abstract_compatible(compiler, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_{Path(compiler_path).stem}"), game)
        # TODO: save result of above and compare.

def test_inbuilt_compiler_compiles(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    compiler = InbuiltNCSCompiler()
    game, script_info = script_data
    _file_res, nss_path, ncs_path = script_info
    compile_with_abstract_compatible(compiler, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_inbuilt"), game)

def test_bizarre_compiler_compiles(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    try:
        nss_source_str: str = file_res.data().decode(encoding="windows-1252", errors="ignore")
        ncs_result: NCS = bizarre_compiler(nss_source_str, game, library_lookup=nss_path.parent)
        if not isinstance(ncs_result, NCS):
            log_file(f"Failed bizarre compilation, no NCS returned: {nss_path}", filepath="fallback_out.txt")
            pytest.fail(f"Failed bizarre compilation, no NCS returned: {nss_path}")
        if not ncs_path.is_file():
            new_exc = FileNotFoundError("Could not find NCS compiled script on disk, bizarre compiler failed.")
            new_exc.filename = ncs_path
            raise new_exc  # noqa: TRY301
    except EntryPointError as e:
        pytest.xfail(f"Bizarre Compiler: No entry point in with '{nss_path.name}': {e}")
    except Exception as e:
        _handle_compile_exc(e, nss_path, "Bizarre Compiler", game)


def test_pykotor_compile_nss_function(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    try:
        nss_source_str: str = file_res.data().decode(encoding="windows-1252", errors="ignore")
        ncs_result: NCS = compile_nss(nss_source_str, game, library_lookup=nss_path.parent)
        if not isinstance(ncs_result, NCS):
            log_file(f"Failed bizarre compilation, no NCS returned: {nss_path}", filepath="fallback_out.txt")
            pytest.fail(f"Failed bizarre compilation, no NCS returned: {nss_path}")
        if not ncs_path.is_file():
            new_exc = FileNotFoundError("Could not find NCS compiled script on disk, bizarre compiler failed.")
            new_exc.filename = ncs_path
            raise new_exc  # noqa: TRY301
    except EntryPointError as e:
        pytest.xfail(f"compile_nss: No entry point in with '{nss_path.name}': {e}")
    except Exception as e:  # noqa: BLE001
        _handle_compile_exc(e, nss_path, "compile_nss", game)


def save_profiler_output(profiler: cProfile.Profile, filepath: os.PathLike | str):
    profiler.disable()
    profiler_output_file = Path.pathify(filepath)
    profiler_output_file_str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)

if __name__ == "__main__":
    profiler = True  # type: ignore[reportAssignmentType]
    if profiler:
        profiler: cProfile.Profile = cProfile.Profile()
        profiler.enable()

    result = pytest.main([__file__, "-v", "-ra", f"--log-file={LOG_FILENAME}.txt", "-o", "log_cli=true"])#, "-n", "4"])

    if profiler:
        save_profiler_output(profiler, "profiler_output.pstat")
        # Generate reports from the profile stats
        #stats = pstats.Stats(profiler_output_file_str).sort_stats('cumulative')
        #stats.print_stats()

        # Generate some line-execution graphs for flame graphs
        #profiler.create_stats()
        #stats_text = pstats.Stats(profiler).sort_stats('cumulative')
        #stats_text.print_stats()
        #stats_text.dump_stats(f"{LOG_FILENAME}.pstats")
        #stats_text.print_callers()
        #stats_text.print_callees()
        # Cumulative list of the calls
        #stats_text.print_stats(100)
        # Cumulative list of calls per function
        #stats_text.print_callers(100, 'cumulative')
        #stats_text.print_callees(100, 'cumulative')

        # Generate some flat line graphs
        #profiler.print_stats(sort='time')  # (Switch to sort='cumulative' then scroll up to see where time was spent!)
        #profiler.print_stats(sort='name')  # (toString of OBJ is called the most often, followed by compiler drivers)
        #profiler.print_stats(sort='cinit') # (A constructor for NCS is where most (<2%) of time is spent)

    sys.exit(result)
    # Cleanup temporary directories after use
    #for temp_dir in temp_dirs.values():
    #    temp_dir.cleanup()  # noqa: ERA001
