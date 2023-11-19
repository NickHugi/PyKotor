from __future__ import annotations

import contextlib
import os
import re
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.ncs import bytes_ncs
from pykotor.resource.formats.ncs import compile_nss as compile_with_builtin
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from pykotor.tslpatcher.mods.template import PatcherModifications
from pykotor.utility.path import Path, PurePath

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
    def __init__(self, filename, replace=None, modifiers=None) -> None:
        super().__init__(filename, replace, modifiers)
        self.action: str = "Hacking"
        self.hackdata: list[tuple[str, int, int]] = []

    def execute_patch(self, ncs_source: SOURCE_TYPES, *args) -> bytes:
        if isinstance(ncs_source, (bytes, bytearray)):
            ncs_bytes = bytearray(ncs_source)
        else:
            msg = "ncs source must be bytes due to a current bug with the read_ncs method."
            raise TypeError(msg)
        self.apply(ncs_bytes, *args)
        return ncs_bytes

    def apply(self, ncs_bytes: bytearray, memory: PatcherMemory, log: PatchLogger | None = None, game: Game | None = None) -> None:
        writer = BinaryWriter.to_bytearray(ncs_bytes)
        for this_data in self.hackdata:
            token_type, offset, token_id_or_value = this_data
            log.add_note(f"HACKList {self.sourcefile}: seeking to offset {offset:#X}")
            writer.seek(offset)
            value = token_id_or_value
            if token_type == "StrRef":  # noqa: S105
                value = memory.memory_str[value]
            elif token_type == "2DAMemory":  # noqa: S105
                value = int(memory.memory_2da[value])
            log.add_note(f"HACKList {self.sourcefile}: writing WORD {value} at offset {offset:#X}")
            writer.write_int16(value)
            writer.seek(offset * -1)
        ncs_bytes.clear()
        ncs_bytes.extend(writer.data())

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=PatcherModifications.DEFAULT_DESTINATION):
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        self.replace_file = file_section_dict.pop("ReplaceFile", self.replace_file)  # for some reason, hacklist doesn't prefix with an exclamation point.

class ModificationsNSS(PatcherModifications):
    def __init__(self, filename, replace=None, modifiers=None) -> None:
        super().__init__(filename, replace, modifiers)
        self.saveas = str(PurePath(filename).with_suffix(".ncs"))
        self.action: str = "Compile"
        self.nwnnsscomp_path: Path

    @staticmethod
    def load(nss_source: SOURCE_TYPES) -> bytes | None:
        if isinstance(nss_source, bytearray):
            return bytes(nss_source)
        if isinstance(nss_source, bytes):
            return nss_source
        if isinstance(nss_source, (os.PathLike, str)):
            return BinaryReader.load_file(nss_source)
        return None

    def execute_patch(self, nss_source: SOURCE_TYPES, memory: PatcherMemory, logger: PatchLogger | None = None, game: Game | None = None) -> bytes:
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
        1. Loads NSS source bytes and decodes
        2. Replaces #2DAMEMORY and StrRef# tokens with values from patcher memory
        3. Attempts to compile with external NWN compiler if on Windows
        4. Falls back to built-in compiler if external isn't available, fails, or not on Windows
        """
        nss_bytes: bytes | None = self.load(nss_source)
        if nss_bytes is None:
            logger.add_error(f"Invalid nss source provided to ModificationsNSS.apply(), got {type(nss_source)}")
            return b""

        source: str = decode_bytes_with_fallbacks(nss_bytes)

        match = re.search(r"#2DAMEMORY\d+#", source)
        while match:
            token_id = int(source[match.start() + 10 : match.end() - 1])
            value_str: str = memory.memory_2da[token_id]
            source = source[: match.start()] + value_str + source[match.end() :]
            match = re.search(r"#2DAMEMORY\d+#", source)

        match = re.search(r"#StrRef\d+#", source)
        while match:
            token_id = int(source[match.start() + 7 : match.end() - 1])
            value = memory.memory_str[token_id]
            source = source[: match.start()] + str(value) + source[match.end() :]
            match = re.search(r"#StrRef\d+#", source)

        if os.name == "nt" and self.nwnnsscomp_path.exists():
            nwnnsscompiler = ExternalNCSCompiler(self.nwnnsscomp_path)
            detected_nwnnsscomp = next((key for key, value in ExternalNCSCompiler.NWNNSSCOMP_SHA256_HASHES.items() if value == nwnnsscompiler.filehash), None)
            if detected_nwnnsscomp != "TSLPatcher":
                logger.add_warning(
                    "The nwnnsscomp.exe in the tslpatchdata folder is not the expected TSLPatcher version.\n"
                    f"PyKotor has detected that the provided nwnnsscomp.exe is the '{detected_nwnnsscomp}' version.\n"
                    "PyKotor will compile regardless, but this may not yield the expected result.",
                )
            with contextlib.suppress(Exception), TemporaryDirectory() as tempdir:
                source_script = self.nwnnsscomp_path.parent / self.sourcefile
                tempcompiled_filepath = Path(tempdir, "temp_script.ncs")
                nwnnsscompiler.compile_script(source_script, tempcompiled_filepath, game)
                return BinaryReader.load_file(tempcompiled_filepath)

        if os.name == "nt":
            if not self.nwnnsscomp_path.exists():
                logger.add_note("nwnnsscomp.exe was not found in the 'tslpatchdata' folder, using the built-in compilers...")
            else:
                logger.add_error(f"An error occurred while compiling {self.sourcefile} with nwnnsscomp.exe, falling back to the built-in compilers...")
        else:
            logger.add_note(f"Patching from a unix operating system, compiling '{self.sourcefile}' using the built-in compilers...")

        # Compile using built-in script compiler if external compiler fails.
        source = MutableString(decode_bytes_with_fallbacks(nss_bytes))
        self.apply(source, memory, logger, game)
        return bytes_ncs(compile_with_builtin(source.value, game))

    def apply(self, nss_source: MutableString, memory: PatcherMemory, logger: PatchLogger | None = None, game: Game | None = None) -> None:
        match = re.search(r"#2DAMEMORY\d+#", nss_source.value)
        while match:
            token_id = int(nss_source.value[match.start() + 10 : match.end() - 1])
            value_str: str = memory.memory_2da[token_id]
            nss_source.value = nss_source.value[: match.start()] + value_str + nss_source.value[match.end() :]
            match = re.search(r"#2DAMEMORY\d+#", nss_source.value)

        match = re.search(r"#StrRef\d+#", nss_source.value)
        while match:
            token_id = int(nss_source.value[match.start() + 7 : match.end() - 1])
            value = memory.memory_str[token_id]
            nss_source.value = nss_source.value[: match.start()] + str(value) + nss_source.value[match.end() :]
            match = re.search(r"#StrRef\d+#", nss_source.value)
