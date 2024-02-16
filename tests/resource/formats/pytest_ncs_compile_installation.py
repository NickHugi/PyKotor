from __future__ import annotations

import cProfile
import logging
import os
import pathlib
import sys

from io import StringIO
from logging.handlers import RotatingFileHandler
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
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.ncs.compiler.classes import CompileError, EntryPointError  # noqa: E402
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer  # noqa: E402
from pykotor.resource.formats.ncs.compiler.parser import NssParser  # noqa: E402
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, InbuiltNCSCompiler  # noqa: E402
from pykotor.resource.formats.ncs.io_ncs import NCSBinaryWriter
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs  # noqa: E402
from pykotor.resource.formats.ncs.ncs_data import NCS  # noqa: E402
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.error_handling import format_exception_with_variables, universal_simplify_exception  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from _pytest.reports import TestReport
    from ply import yacc

    from pykotor.extract.file import FileResource
    from pykotor.resource.formats.ncs.ncs_data import NCSCompiler

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
KTOOL_NWNNSSCOMP_PATH: str | None = r"C:\Program Files (x86)\Kotor Tool\nwnnsscomp.exe"
TSLPATCHER_NWNNSSCOMP_PATH: str | None = r"C:\Users\boden\Documents\k1 mods\KillCzerkaJerk\tslpatchdata\nwnnsscomp.exe"
K_SCRIPT_TOOL_NWNNSSCOMP_PATH: str | None = r"C:/Program Files (x86)/KotOR Scripting Tool/nwnnsscomp.exe"
V1_NWNNSSCOMP_PATH: str | None = r"C:\Users\boden\Desktop\kotorcomp (1)\nwnnsscomp.exe"
LOG_FILENAME = "test_ncs_compilers_install"


def setup_logger():
    # Configure logger for failed test cases
    logger = logging.getLogger("failed_tests_logger")
    logger.setLevel(logging.DEBUG)

    # Primary log file handler
    fh = RotatingFileHandler("FAILED_TESTS.log", maxBytes=5 * 1024 * 1024, backupCount=5, mode="a")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

logger = setup_logger()


# pytest hook to check test outcomes
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> TestReport | None:
    if "setup" in call.when:
        # Skip setup phase
        return None
    if call.excinfo is not None and call.when == "call":
        # This means the test has failed
        # Construct and return a TestReport object

        # longrepr = call.excinfo.getrepr()
        longrepr = format_exception_with_variables(call.excinfo.value, call.excinfo.type, call.excinfo.tb)
        logger.error("Test failed with exception!", extra={"item.nodeid": item.nodeid, "Traceback: ": longrepr})
        report = TestReport(
            nodeid=item.nodeid,
            location=item.location,
            keywords=item.keywords,
            outcome="failed",
            longrepr=longrepr,
            when=call.when,
            sections=[],
            duration=call.stop - call.start,
            user_properties=item.user_properties,
        )
        return report
    return None

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
def _handle_compile_exc(
    e: Exception,
    file_res: FileResource,
    nss_path: Path,
    compiler_identifier: str,
    game: Game,
):
    exc_type_name, exc_basic_info_str = universal_simplify_exception(e)
    exc_debug_info_str = format_exception_with_variables(e)

    prefix_msg = "Could not compile " if e.__class__ is CompileError else f"Unexpected exception of type '{exc_type_name}' occurred when compiling"
    msg = f"{prefix_msg} '{nss_path.name}' (from {file_res.filepath()}) with '{compiler_identifier}' compiler!"
    exc_separator_str = "-" * len(msg)

    msg_info_level = os.linesep.join((msg, exc_basic_info_str, exc_separator_str))
    msg_debug_level = os.linesep.join((msg, exc_debug_info_str, exc_separator_str))

    log_file(msg_info_level, filepath=f"fallback_level_info_{game}_{compiler_identifier}.txt")
    log_file(msg_debug_level, filepath=f"fallback_level_debug_{game}_{compiler_identifier}.txt")
    log_file(f'"{nss_path.name}",', filepath=f"{compiler_identifier}_incompatible_{game}.txt")  # for quick copy/paste into the known_issues hashset
    logger.log(level=40, msg=msg_debug_level)
    pytest.fail(msg_info_level)


CUR_FAILED_EXT: dict[Game, set[ResourceIdentifier]] = {
    Game.K1: set(),
    Game.K2: set(),
}
def compile_with_abstract_compatible(
    compiler: NCSCompiler,
    file_res: FileResource,
    nss_path: Path,
    ncs_path: Path,
    game: Game,
    compiler_identifier: str,
):
    global CUR_FAILED_EXT
    try:
        if isinstance(compiler, ExternalNCSCompiler):
            compiler_identifier = f"nwnnsscomp.exe({compiler_identifier})"
            try:
                stdout, stderr = compiler.compile_script(nss_path, ncs_path, game)
            except EntryPointError as e:
                pytest.xfail(f"{compiler_identifier}: No entry point found in '{nss_path.name}': {e}")
            else:
                if stderr:
                    raise CompileError(f"{stdout}: {stderr}")
        else:
            if ResourceIdentifier.from_path(nss_path) in CUR_FAILED_EXT[game]:
                return
            try:
                compiler.compile_script(nss_path, ncs_path, game, debug=False)
            except EntryPointError as e:
                pytest.xfail(f"Inbuilt: No entry point found in '{nss_path.name}': {e}")

        if not ncs_path.is_file():
            # raise it so _handle_compile_exc can be used to reduce duplicated logging code.
            new_exc = FileNotFoundError(f"Could not find NCS compiled script on disk, '{compiler_identifier}' compiler failed.")
            new_exc.filename = ncs_path
            raise new_exc

    except Exception as e:  # noqa: BLE001
        if isinstance(compiler, ExternalNCSCompiler):
            CUR_FAILED_EXT[game].add(ResourceIdentifier.from_path(nss_path))
            if isinstance(e, FileNotFoundError):
                return
        _handle_compile_exc(e, file_res, nss_path, compiler_identifier, game)


def compare_external_results(
    compiler_result: dict[str | None, bytes | None],
):
    """Compare results between compilers. No real point since having any of them match is rare."""
    # Ensure all non-None results are the same
    non_none_results: dict[str, bytes] = {
        cp: result for cp, result in compiler_result.items() if result is not None and cp is not None
    }

    if not non_none_results:
        pytest.skip("No compilers were available or produced output for comparison.")

    # Initialize containers for tracking matches and mismatches
    matches: list[str] = []
    mismatches: list[str] = []

    # Compare the results
    compiler_paths = list(non_none_results.keys())
    for i in range(len(compiler_paths)):
        for j in range(i + 1, len(compiler_paths)):
            path_i = compiler_paths[i]
            path_j = compiler_paths[j]
            result_i = non_none_results[path_i]
            result_j = non_none_results[path_j]

            if result_i == result_j:
                matches.append(f"Match: Compiler outputs for '{path_i}' and '{path_j}' are identical.")
            else:
                mismatches.append(f"Mismatch: Compiler outputs for '{path_i}' and '{path_j}' differ.")

    # Report results
    if mismatches:
        error_report = "\n".join(mismatches + matches)  # Include matches for context
        pytest.fail(error_report)

    if matches:
        print("\n".join(matches))

# def test_ktool_nwnnsscomp(
#    script_data: tuple[Game, tuple[FileResource, Path, Path]],
# ):
#    compilers: dict[str | None, ExternalNCSCompiler | None] = {
#        KTOOL_NWNNSSCOMP_PATH: ExternalNCSCompiler(KTOOL_NWNNSSCOMP_PATH) if KTOOL_NWNNSSCOMP_PATH and Path(KTOOL_NWNNSSCOMP_PATH).is_file() else None,
#    }

#    compiler_result: dict[str | None, bytes | None] = {
#        KTOOL_NWNNSSCOMP_PATH: None,
#    }

#    game, script_info = script_data
#    file_res, nss_path, ncs_path = script_info
#    for compiler_path, compiler in compilers.items():
#        if compiler is None or compiler_path is None:
#            continue  # don't test nonexistent compilers
#        if nss_path.name == "nwscript.nss":
#            continue
#        if os.path.islink(nss_path):
#            continue

#        unique_ncs_path = ncs_path.with_stem(f"{ncs_path.stem}_{Path(compiler_path).stem}_(ktool)")
#        compile_with_abstract_compatible(compiler, file_res, nss_path, unique_ncs_path, game, "ktool")
#        with unique_ncs_path.open("rb") as f:
#            compiler_result[compiler_path] = f.read()


def test_tslpatcher_nwnnsscomp(
    script_data: tuple[Game, tuple[FileResource, Path, Path]],
):
    if TSLPATCHER_NWNNSSCOMP_PATH is None or not Path(TSLPATCHER_NWNNSSCOMP_PATH).is_file():
        return

    nwscript_path = Path(TSLPATCHER_NWNNSSCOMP_PATH).parent.joinpath("nwscript.nss")
    k1_nwscript_path = nwscript_path.with_name("k1_nwscript.nss")
    k2_nwscript_path = nwscript_path.with_name("k2_nwscript_path")

    compilers: dict[str, ExternalNCSCompiler] = {
        TSLPATCHER_NWNNSSCOMP_PATH: ExternalNCSCompiler(TSLPATCHER_NWNNSSCOMP_PATH),
    }

    compiler_result: dict[str | None, bytes | None] = {
        TSLPATCHER_NWNNSSCOMP_PATH: None,
    }

    game, script_info = script_data

    # Rename the active nwscript.nss based on the game.
    if game.is_k1() and k1_nwscript_path.is_file():
        if nwscript_path.exists():
            nwscript_path.rename(k2_nwscript_path)  # Rename k2's nwscript.nss to k2_nwscript.nss
        k1_nwscript_path.rename(nwscript_path)  # Rename k1_nwscript.nss to nwscript.nss to activate
    if game.is_k2() and k2_nwscript_path.is_file():
        if nwscript_path.exists():
            nwscript_path.rename(k1_nwscript_path)  # Rename k1's nwscript.nss to k1_nwscript.nss
        k2_nwscript_path.rename(nwscript_path)  # Rename k2_nwscript.nss to nwscript.nss to activate

    file_res, nss_path, ncs_path = script_info
    for compiler_path, compiler in compilers.items():
        if compiler is None or compiler_path is None:
            continue  # don't test nonexistent compilers
        if nss_path.name == "nwscript.nss":
            continue
        if os.path.islink(nss_path):
            continue

        unique_ncs_path = ncs_path.with_stem(f"{ncs_path.stem}_{Path(compiler_path).stem}_(2)")
        compile_with_abstract_compatible(compiler, file_res, nss_path, unique_ncs_path, game, "tslpatcher_nwnnsscomp")
        with unique_ncs_path.open("rb") as f:
            compiler_result[compiler_path] = f.read()

# def test_kscript_tool_nwnnsscomp(
#    script_data: tuple[Game, tuple[FileResource, Path, Path]],
# ):
#    compilers: dict[str | None, ExternalNCSCompiler | None] = {
#        K_SCRIPT_TOOL_NWNNSSCOMP_PATH: ExternalNCSCompiler(K_SCRIPT_TOOL_NWNNSSCOMP_PATH) if K_SCRIPT_TOOL_NWNNSSCOMP_PATH and Path(K_SCRIPT_TOOL_NWNNSSCOMP_PATH).is_file() else None,
#    }

#    compiler_result: dict[str | None, bytes | None] = {
#        K_SCRIPT_TOOL_NWNNSSCOMP_PATH: None,
#    }

#    game, script_info = script_data
#    file_res, nss_path, ncs_path = script_info
#    for i, (compiler_path, compiler) in enumerate(compilers.items()):
#        if compiler is None or compiler_path is None:
#            continue  # don't test nonexistent compilers

#        unique_ncs_path = ncs_path.with_stem(f"{ncs_path.stem}_{Path(compiler_path).stem}_(kscript_tool)")
#        compile_with_abstract_compatible(compiler, file_res, nss_path, unique_ncs_path, game, "kscript_tool")
#        with unique_ncs_path.open("rb") as f:
#            compiler_result[compiler_path] = f.read()

# def test_v1_nwnnsscomp(
#    script_data: tuple[Game, tuple[FileResource, Path, Path]],
# ):
#    compilers: dict[str | None, ExternalNCSCompiler | None] = {
#        V1_NWNNSSCOMP_PATH: ExternalNCSCompiler(V1_NWNNSSCOMP_PATH) if V1_NWNNSSCOMP_PATH and Path(V1_NWNNSSCOMP_PATH).is_file() else None,
#    }

#    compiler_result: dict[str | None, bytes | None] = {
#        V1_NWNNSSCOMP_PATH: None,
#    }

#    game, script_info = script_data
#    file_res, nss_path, ncs_path = script_info
#    for i, (compiler_path, compiler) in enumerate(compilers.items()):
#        if compiler is None or compiler_path is None:
#            continue  # don't test nonexistent compilers

#        unique_ncs_path = ncs_path.with_stem(f"{ncs_path.stem}_{Path(compiler_path).stem}_(v1)")
#        compile_with_abstract_compatible(compiler, file_res, nss_path, unique_ncs_path, game, "v1")
#        with unique_ncs_path.open("rb") as f:
#            compiler_result[compiler_path] = f.read()


def test_inbuilt_compiler(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    compiler = InbuiltNCSCompiler()
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    if nss_path.name == "nwscript.nss":
        return
    if os.path.islink(nss_path):
        return
    compile_with_abstract_compatible(compiler, file_res, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_inbuilt"), game, "inbuilt")

def test_bizarre_compiler(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    if file_res.identifier() in CUR_FAILED_EXT[game]:
        return
    if nss_path.name == "nwscript.nss":
        return
    if os.path.islink(nss_path):
        return

    working_dir = nss_path.parent
    try:
        nss_source_str: str = file_res.data().decode(encoding="windows-1252", errors="ignore")
        ncs_result: NCS = bizarre_compiler(nss_source_str, game, library_lookup=nss_path.parent)
        NCSBinaryWriter(ncs_result, ncs_path).write()

        if not isinstance(ncs_result, NCS):
            log_file(f"Failed bizarre compilation, no NCS returned: '{working_dir.name}/{nss_path}'", filepath="fallback_out.txt")
            pytest.fail(f"Failed bizarre compilation, no NCS returned: '{working_dir.name}/{nss_path}'")
        if not ncs_path.is_file():
            new_exc = FileNotFoundError(f"Could not find NCS compiled script on disk at '{working_dir.name}/{nss_path}', bizarre compiler failed.")
            new_exc.filename = ncs_path
            raise new_exc  # noqa: TRY301

    except EntryPointError as e:
        pytest.xfail(f"Bizarre Compiler: No entry point found in '{working_dir.name}/{nss_path}': {e}")
    except Exception as e:
        _handle_compile_exc(e, file_res, nss_path, "Bizarre Compiler", game)


def test_pykotor_compile_nss(
    script_data: tuple[Game, tuple[FileResource, Path, Path]]
):
    game, script_info = script_data
    file_res, nss_path, ncs_path = script_info
    if file_res.identifier() in CUR_FAILED_EXT[game]:
        return
    if nss_path.name == "nwscript.nss":
        return
    if os.path.islink(nss_path):
        return

    working_dir = nss_path.parent
    try:
        nss_source_str: str = decode_bytes_with_fallbacks(file_res.data())
        ncs_result: NCS = compile_nss(nss_source_str, game, library_lookup=working_dir)
        write_ncs(ncs_result, ncs_path)

        if not isinstance(ncs_result, NCS):
            log_file(f"Failed compile_nss, no NCS returned: '{working_dir.name}/{nss_path.name}'", filepath="fallback_out.txt")
            pytest.fail(f"Failed compile_nss, no NCS returned: '{working_dir.name}/{nss_path.name}'")
        if not ncs_path.is_file():
            new_exc = FileNotFoundError("Could not find NCS compiled script on disk, compile_nss failed.")
            new_exc.filename = ncs_path
            raise new_exc  # noqa: TRY301
    except EntryPointError as e:
        pytest.xfail(f"compile_nss: No entry point in with '{working_dir.name}/{nss_path.name}': {e}")
    except Exception as e:  # noqa: BLE001
        _handle_compile_exc(e, file_res, nss_path, "compile_nss", game)


def save_profiler_output(
    profiler: cProfile.Profile,
    filepath: os.PathLike | str,
):
    profiler.disable()
    profiler_output_file = Path.pathify(filepath)
    profiler_output_file_str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)

if __name__ == "__main__":
    profiler: cProfile.Profile = True  # type: ignore[reportAssignmentType, assignment]
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()


    result: int | pytest.ExitCode = pytest.main(
        [
            __file__,
            "-v",
            # "--full-trace",
            "-ra",
            f"--log-file={LOG_FILENAME}.txt",
            "-o",
            "log_cli=true",
            "--capture=no",
            "--junitxml=pytest_report.xml",
            "--html=pytest_report.html",
            "--tb=no",
            # "--self-contained-html",
            # "-n",
            # "auto"
        ],
    )

    if profiler:
        save_profiler_output(profiler, "profiler_output.pstat")
        # Generate reports from the profile stats
        # stats = pstats.Stats(profiler_output_file_str).sort_stats('cumulative')
        # stats.print_stats()

        # Generate some line-execution graphs for flame graphs
        # profiler.create_stats()
        # stats_text = pstats.Stats(profiler).sort_stats('cumulative')
        # stats_text.print_stats()
        # stats_text.dump_stats(f"{LOG_FILENAME}.pstats")
        # stats_text.print_callers()
        # stats_text.print_callees()
        # Cumulative list of the calls
        # stats_text.print_stats(100)
        # Cumulative list of calls per function
        # stats_text.print_callers(100, 'cumulative')
        # stats_text.print_callees(100, 'cumulative')

        # Generate some flat line graphs
        # profiler.print_stats(sort='time')  # (Switch to sort='cumulative' then scroll up to see where time was spent!)
        # profiler.print_stats(sort='name')  # (toString of OBJ is called the most often, followed by compiler drivers)
        # profiler.print_stats(sort='cinit') # (A constructor for NCS is where most (<2%) of time is spent)

    sys.exit(result)
    # Cleanup temporary directories after use
    # for temp_dir in temp_dirs.values():
    #    temp_dir.cleanup()  # noqa: ERA001
