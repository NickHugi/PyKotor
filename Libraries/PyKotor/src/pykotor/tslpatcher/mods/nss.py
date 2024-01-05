from __future__ import annotations

import os
import re
import tempfile
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter, BinaryWriterBytearray
from pykotor.resource.formats.ncs import bytes_ncs
from pykotor.resource.formats.ncs import compile_nss as compile_with_builtin
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.error_handling import universal_simplify_exception
from utility.path import Path, PurePath, PureWindowsPath

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory

class MutableString:
    def __init__(self, value: str):
        self.value: str = value
    def __str__(self):
        return self.value


class ModificationsNCS(PatcherModifications):
    def __init__(self, filename, replace=None, modifiers=None):
        super().__init__(filename, replace, modifiers)
        self.action: str = "Hack "
        self.hackdata: list[tuple[str, int, int]] = []

    def patch_resource(
        self,
        ncs_source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
        if isinstance(ncs_source, (bytes, bytearray)):
            ncs_bytes = bytearray(ncs_source)
        else:
            msg = "ncs source must be bytes due to a current bug with the read_ncs method."
            raise TypeError(msg)
        self.apply(ncs_bytes, memory, logger, game)
        return ncs_bytes

    def apply(
        self,
        ncs_bytes: bytearray,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        writer: BinaryWriterBytearray = BinaryWriter.to_bytearray(ncs_bytes)
        for this_data in self.hackdata:
            token_type, offset, token_id_or_value = this_data
            logger.add_verbose(f"HACKList {self.sourcefile}: seeking to offset {offset:#X}")
            writer.seek(offset)
            value: int = token_id_or_value
            if token_type == "StrRef":  # noqa: S105
                value = memory.memory_str[value]
            elif token_type == "2DAMEMORY":  # noqa: S105
                memory_val: str | PureWindowsPath = memory.memory_2da[value]
                if isinstance(memory_val, PureWindowsPath):
                    msg = f"Memory value cannot be !FieldPath, got '{memory_val!r}'"
                    raise ValueError(msg)
                value = int(memory_val)
            logger.add_verbose(f"HACKList {self.sourcefile}: writing WORD {value} at offset {offset:#X}")
            writer.write_int16(value)

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=PatcherModifications.DEFAULT_DESTINATION):
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        replace_file: bool | str = file_section_dict.pop("ReplaceFile", self.replace_file)
        self.replace_file = bool(int(replace_file))  # tslpatcher's hacklist doesn't prefix with an exclamation point.

class ModificationsNSS(PatcherModifications):
    def __init__(self, filename, replace=None, modifiers=None):
        super().__init__(filename, replace, modifiers)
        self.saveas = str(PurePath(filename).with_suffix(".ncs"))
        self.action: str = "Compile"
        self.nwnnsscomp_path: Path

    @staticmethod
    def load(nss_source: SOURCE_TYPES) -> bytes | None:
        if isinstance(nss_source, (bytearray, memoryview)):
            return bytes(nss_source)
        if isinstance(nss_source, bytes):
            return nss_source
        if isinstance(nss_source, (os.PathLike, str)):
            return BinaryReader.load_file(nss_source)
        return None

    def patch_resource(
        self,
        nss_source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
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
        nss_bytes: bytes | None = self.load(nss_source)
        if nss_bytes is None:
            logger.add_error("Invalid nss source provided to ModificationsNSS.apply()")
            return b""

        source = MutableString(decode_bytes_with_fallbacks(nss_bytes))
        self.apply(source, memory, logger, game)

        is_windows = os.name == "nt"
        if is_windows and self.nwnnsscomp_path.exists():
            nwnnsscompiler = ExternalNCSCompiler(self.nwnnsscomp_path)
            detected_nwnnsscomp: str = next(
                (k for k, v in ExternalNCSCompiler.NWNNSSCOMP_SHA256_HASHES.items() if v == nwnnsscompiler.filehash),
                "UNKNOWN/INVALID",
            )
            if detected_nwnnsscomp != "TSLPatcher":
                logger.add_warning(
                    "The nwnnsscomp.exe in the tslpatchdata folder is not the expected TSLPatcher version.\n"
                    f"PyKotor has detected that the provided nwnnsscomp.exe is the '{detected_nwnnsscomp}' version.\n"
                    "PyKotor will compile regardless, but this may not yield the expected result.",
                )
            try:
                return self._compile_with_external(source.value, nwnnsscompiler, logger, game)
            except Exception as e:  # noqa: BLE001
                logger.add_error(str(universal_simplify_exception(e)))

        if is_windows:
            if not self.nwnnsscomp_path.exists():
                logger.add_note("nwnnsscomp.exe was not found in the 'tslpatchdata' folder, using the built-in compilers...")
            else:
                logger.add_error(f"An error occurred while compiling '{self.sourcefile}' with nwnnsscomp.exe, falling back to the built-in compilers...")
        else:
            logger.add_note(f"Patching from a unix operating system, compiling '{self.sourcefile}' using the built-in compilers...")

        # Compile using built-in script compiler if external compiler fails.
        return bytes_ncs(compile_with_builtin(source.value, game))

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
            if isinstance(memory_val, PureWindowsPath):
                logger.add_error(str(TypeError(f"memory_2da lookup cannot be !FieldPath, got '{memory_val!r}'")))
                match = re.search(r"#2DAMEMORY\d+#", nss_source.value)
                continue

            value_str: str = memory_val
            nss_source.value = nss_source.value[: match.start()] + value_str + nss_source.value[match.end() :]
            match = re.search(r"#2DAMEMORY\d+#", nss_source.value)

        match = re.search(r"#StrRef\d+#", nss_source.value)
        while match:
            token_id = int(nss_source.value[match.start() + 7 : match.end() - 1])
            value: int = memory.memory_str[token_id]
            nss_source.value = nss_source.value[: match.start()] + str(value) + nss_source.value[match.end() :]
            match = re.search(r"#StrRef\d+#", nss_source.value)


    def _compile_with_external(
        self,
        nss_script: str,
        nwnnsscompiler: ExternalNCSCompiler,
        logger: PatchLogger,
        game: Game,
    ) -> bytes:
        # Get a temporary filename.
        temp_source_script: Path
        with tempfile.NamedTemporaryFile(mode="w+t", suffix=".nss", dir=self.nwnnsscomp_path.parent) as temp_file:
            temp_source_script = Path(temp_file.name)

        # Dump the script to a tempfile, then send to the external compiler.
        BinaryWriter.dump(temp_source_script, nss_script.encode(encoding="windows-1252", errors="ignore"))
        tempcompiled_filepath: Path = self.nwnnsscomp_path.parent / "temp_script.ncs"
        stdout, stderr = nwnnsscompiler.compile_script(temp_source_script, tempcompiled_filepath, game)

        # Parse the output.
        if stdout.strip():
            for line in stdout.split("\n"):
                if line.strip():
                    logger.add_verbose(line)
        if stderr.strip():
            for line in stdout.split("\n"):
                if line.strip():
                    logger.add_error(line)
            raise ValueError(stderr)

        # Return the compiled bytes
        return BinaryReader.load_file(tempcompiled_filepath)
