"""Represents patches specific to [CompileList] logic."""
from __future__ import annotations

import os
import re
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.ncs import bytes_ncs
from pykotor.resource.formats.ncs import compile_nss as compile_with_builtin
from pykotor.resource.formats.ncs.compiler.classes import EntryPointError
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler
from pykotor.resource.formats.ncs.optimizers import (
    RemoveMoveSPEqualsZeroOptimizer,
    RemoveNopOptimizer,
    RemoveUnusedBlocksOptimizer,
)
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.error_handling import universal_simplify_exception
from utility.system.path import Path, PurePath, PureWindowsPath

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.formats.ncs.ncs_data import NCS
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory
    from typing_extensions import Literal

class MutableString:
    def __init__(self, value: str):
        self.value: str = value
    def __str__(self):
        return self.value

class ModificationsNSS(PatcherModifications):
    def __init__(self, filename, replace=None, modifiers=None):
        super().__init__(filename, replace, modifiers)
        self.saveas = str(PurePath(filename).with_suffix(".ncs"))
        self.action: str = "Compile"
        self.nwnnsscomp_path: Path  # TODO: fix type. Default None or Path?
        self.temp_script_folder: Path
        self.skip_if_not_replace = True

    def patch_resource(
        self,
        nss_source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        """Takes the source nss bytes and replaces instances of 2DAMEMORY# and StrRef# with the values in patcher memory. Compiles the
        source bytes and returns the ncs compiled script as a bytes object.

        Args:
        ----
            nss_source: SOURCE_TYPES: NSS source object to apply modifications to
            memory: (PatcherMemory): current memory of 2damemory and strref
            logger (PatchLogger): Logging object
            game (Game): KOTOR Game enum value

        Returns:
        -------
            bytes: Compiled NCS bytes

        Processing Logic:
        ----------------
            1. Loads NSS source bytes and decodes
            2. Replaces 2DAMEMORY# and StrRef# tokens with values from patcher memory
            3. Attempts to compile with external NWN compiler if on Windows
            4. Falls back to built-in compiler if external isn't available, fails, or not on Windows
        """  # noqa: D205
        with BinaryReader.from_auto(nss_source) as reader:
            nss_bytes: bytes = reader.read_all()
        if nss_bytes is None:
            logger.add_error("Invalid nss source provided to ModificationsNSS.apply()")
            return True

        # Replace memory tokens in the script, and save to the file.
        source = MutableString(decode_bytes_with_fallbacks(nss_bytes))
        self.apply(source, memory, logger, game)
        temp_script_file = self.temp_script_folder / self.sourcefile
        BinaryWriter.dump(temp_script_file, source.value.encode(encoding="windows-1252", errors="ignore"))

        # Compile with external on windows, fall back to built-in if mac/linux or if external fails.
        is_windows = os.name == "nt"
        nwnnsscomp_exists: bool | None = self.nwnnsscomp_path.safe_isfile()
        if is_windows and self.nwnnsscomp_path and nwnnsscomp_exists:
            nwnnsscompiler = ExternalNCSCompiler(self.nwnnsscomp_path)
            try:
                detected_nwnnsscomp: str = nwnnsscompiler.get_info().name
            except ValueError:
                detected_nwnnsscomp: str = "<UNKNOWN>"
            if detected_nwnnsscomp != "TSLPatcher":
                logger.add_warning(
                    "The nwnnsscomp.exe in the tslpatchdata folder is not the expected TSLPatcher version.\n"
                    f"PyKotor has detected that the provided nwnnsscomp.exe is the '{detected_nwnnsscomp}' version.\n"
                    "PyKotor will compile regardless, but this may not yield the expected result.",
                )
            try:
                return self._compile_with_external(temp_script_file, nwnnsscompiler, logger, game)
            except Exception as e:  # noqa: BLE001
                logger.add_error(str(universal_simplify_exception(e)))

        if is_windows:
            if not self.nwnnsscomp_path or not nwnnsscomp_exists:
                logger.add_note("nwnnsscomp.exe was not found in the 'tslpatchdata' folder, using the built-in compilers...")
            else:
                logger.add_error(f"An error occurred while compiling '{self.sourcefile}' with nwnnsscomp.exe, falling back to the built-in compilers...")
        else:
            logger.add_note(f"Patching from a unix operating system, compiling '{self.sourcefile}' using the built-in compilers...")

        # Compile using built-in script compiler if external compiler fails.
        try:
            ncs: NCS = compile_with_builtin(
                source.value,
                game,
                [], #[RemoveNopOptimizer(), RemoveMoveSPEqualsZeroOptimizer(), RemoveUnusedBlocksOptimizer()],  # TODO: ncs optimizers need testing
                library_lookup=[CaseAwarePath.pathify(self.temp_script_folder)],
            )
        except EntryPointError as e:
            logger.add_note(str(e))
            return True
        return bytes(bytes_ncs(ncs))

    def apply(
        self,
        nss_source: MutableString,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        """Applies memory patches to the source script.

        Args:
        ----
            nss_source: {MutableString object containing the string to patch}
            memory: {PatcherMemory object containing memory references}
            logger: {PatchLogger object for logging (optional)}
            game: {Game object for game context (optional)}.

        Processing Logic:
        ----------------
            - Searches string for #2DAMEMORY# patterns and replaces with 2DA value
            - Searches string for #StrRef# patterns and replaces with string reference value
            - Repeats searches until no matches remain.
        """
        match: re.Match[str] | None
        match = re.search(r"#2DAMEMORY\d+#", nss_source.value)
        while match:
            token_id = int(nss_source.value[match.start() + 10 : match.end() - 1])
            memory_val: str | PureWindowsPath = memory.memory_2da[token_id]
            if memory_val is None:
                msg = f"2DAMEMORY{token_id} was not defined before use."
                raise KeyError(msg)
            if isinstance(memory_val, PureWindowsPath):
                logger.add_error(str(TypeError(f"memory_2da lookup cannot be !FieldPath for [CompileList] patches, got '2DAMEMORY{token_id}={memory_val!r}'")))
                match = re.search(r"#2DAMEMORY\d+#", nss_source.value)
                continue

            nss_source.value = nss_source.value[: match.start()] + memory_val + nss_source.value[match.end() :]
            match = re.search(r"#2DAMEMORY\d+#", nss_source.value)

        match = re.search(r"#StrRef\d+#", nss_source.value)
        while match:
            token_id = int(nss_source.value[match.start() + 7 : match.end() - 1])
            memory_strval: int | None = memory.memory_str.get(token_id, None)
            if memory_strval is None:
                msg = f"StrRef{token_id} was not defined before use."
                raise KeyError(msg)
            value: int = memory_strval
            nss_source.value = nss_source.value[: match.start()] + str(value) + nss_source.value[match.end() :]
            match = re.search(r"#StrRef\d+#", nss_source.value)


    def _compile_with_external(
        self,
        temp_script_file: Path,
        nwnnsscompiler: ExternalNCSCompiler,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        with TemporaryDirectory() as tempdir:
            tempcompiled_filepath: Path = Path(tempdir) / "temp_script.ncs"
            stdout, stderr = nwnnsscompiler.compile_script(temp_script_file, tempcompiled_filepath, game)
            result: bool | bytes = "File is an include file, ignored" in stdout
            if not result:
                # Return the compiled bytes
                result = BinaryReader.load_file(tempcompiled_filepath)

        # Parse the output.
        if stdout.strip():
            for line in stdout.split("\n"):
                if line.strip():
                    logger.add_verbose(line)
        if stderr.strip():
            for line in stderr.split("\n"):
                if line.strip():
                    logger.add_error(line)

        return result
