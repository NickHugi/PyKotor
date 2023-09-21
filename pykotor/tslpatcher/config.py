from __future__ import annotations

from configparser import ConfigParser
from datetime import datetime, timezone
from enum import IntEnum
from typing import TYPE_CHECKING

try:
    import chardet
except ImportError:
    chardet = None

from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.erf import ERF, read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERFType
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.formats.ssf import read_ssf, write_ssf
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.resource.formats.twoda import read_2da, write_2da
from pykotor.tools.misc import is_capsule_file, is_mod_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFolder, create_backup
from pykotor.tslpatcher.mods.tlk import ModificationsTLK

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.tslpatcher.mods.gff import ModificationsGFF
    from pykotor.tslpatcher.mods.nss import ModificationsNSS
    from pykotor.tslpatcher.mods.ssf import ModificationsSSF
    from pykotor.tslpatcher.mods.twoda import Modifications2DA


class LogLevel(IntEnum):
    # Docstrings taken from ChangeEdit docs

    NOTHING = 0
    """No feedback at all. The text from "info.rtf" will continue to be displayed during installation"""

    GENERAL = 1
    """Only general progress information will be displayed. Not recommended."""

    ERRORS = 2
    """General progress information is displayed, along with any serious errors encountered."""

    WARNINGS = 3
    """General progress information, serious errors and warnings are displayed. This is
    recommended for the release version of your mod."""

    FULL = 4
    """Full feedback. On top of what is displayed at level 3, it also shows verbose progress
    information that may be useful for a Modder to see what is happening. Intended for
    Debugging."""


class PatcherConfig:
    def __init__(self):
        self.window_title: str = ""
        self.confirm_message: str = ""
        self.game_number: int | None = None

        self.required_file: str | None = None
        self.required_message: str = ""

        self.install_list: list[InstallFolder] = []
        self.patches_2da: list[Modifications2DA] = []
        self.patches_gff: list[ModificationsGFF] = []
        self.patches_ssf: list[ModificationsSSF] = []
        self.patches_nss: list[ModificationsNSS] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()

    def load(self, ini_text: str, mod_path: os.PathLike | str, logger: PatchLogger | None = None) -> None:
        from pykotor.tslpatcher.reader import ConfigReader

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        ini.optionxform = lambda optionstr: optionstr  # use case sensitive keys
        ini.read_string(ini_text)

        ConfigReader(ini, CaseAwarePath(mod_path), logger).load(self)

    def patch_count(self) -> int:
        return (
            len(self.patches_2da)
            + len(self.patches_gff)
            + len(self.patches_ssf)
            + 1
            + len(self.install_list)
            + len(self.patches_nss)
        )


class PatcherNamespace:
    def __init__(self):
        self.namespace_id: str = ""
        self.ini_filename: str = ""
        self.info_filename: str = ""
        self.data_folderpath: str = ""
        self.name: str = ""
        self.description: str = ""


class ModInstaller:
    def __init__(
        self,
        mod_path: os.PathLike | str,
        game_path: os.PathLike | str,
        changes_ini_path: os.PathLike | str,
        logger: PatchLogger | None = None,
    ):
        self.log: PatchLogger = logger or PatchLogger()
        self.game_path: CaseAwarePath = CaseAwarePath(game_path)
        self.mod_path: CaseAwarePath = CaseAwarePath(mod_path)
        self.changes_ini_path: CaseAwarePath = CaseAwarePath(changes_ini_path)
        if not self.changes_ini_path.exists():  # handle legacy syntax
            self.changes_ini_path = self.mod_path / self.changes_ini_path.name
            if not self.changes_ini_path.exists():
                self.changes_ini_path = self.mod_path / "tslpatchdata" / self.changes_ini_path.name
            if self.changes_ini_path.exists():
                self.log.add_warning(
                    "The ModInstaller's changes ini argument has had its string filename type deprecated, please update your code to send a full changes ini path.",
                )
            else:
                msg = f"Could not find the changes ini file {self.changes_ini_path} on disk! Could not start install!"
                raise FileNotFoundError(msg)

        self._config: PatcherConfig | None = None

    def config(self) -> PatcherConfig:
        """
        Returns the PatcherConfig object associated with the mod installer. The object is created when the method is
        first called then cached for future calls.
        """
        if self._config is not None:
            return self._config

        ini_file_bytes = BinaryReader.load_file(self.changes_ini_path)

        ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        ini.optionxform = lambda optionstr: optionstr  # use case sensitive keys

        if chardet:
            encoding = chardet.detect(ini_file_bytes, should_rename_legacy=True)["encoding"]
            assert encoding is not None
            ini_text = ini_file_bytes.decode(encoding)
        else:
            ini_text: str | None = None
            try:
                ini_text = ini_file_bytes.decode()
            except UnicodeDecodeError:
                try:
                    ini_text = ini_file_bytes.decode("cp1252")
                except UnicodeDecodeError:
                    ini_text = ini_file_bytes.decode(errors="replace")

        self._config = PatcherConfig()
        self._config.load(ini_text, self.mod_path, self.log)

        return self._config

    # extract into multiple funcs perhaps?
    def install(self) -> None:
        config = self.config()

        installation = Installation(self.game_path, self.log)
        memory = PatcherMemory()
        twodas = {}
        soundsets = {}
        templates = {}

        # Create a timestamped backup directory
        tz_aware_datetime = datetime.now(tz=timezone.utc)
        timestamp = tz_aware_datetime.strftime("%Y.%m.%d_%H.%M.%S")
        backup_dir = self.mod_path.parent / "backup" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        self.log.add_note(f"Using backup directory: '{backup_dir}'")

        processed_files = set()

        self.log.add_note("Applying patches from [TLKList]...")
        if len(config.patches_tlk.modifiers) > 0:  # skip if no patches need to be made (faster)
            dialog_tlk_path = (
                self.game_path / "dialog.tlk"
            )  # sourcery skip: extract-method, move-assign-in-block, use-fstring-for-concatenation
            dialog_tlk = read_tlk(dialog_tlk_path)
            create_backup(self.log, dialog_tlk_path, backup_dir, processed_files)
            self.log.add_note("Patching dialog.tlk...")
            config.patches_tlk.apply(dialog_tlk, memory)
            write_tlk(dialog_tlk, dialog_tlk_path)
            self.log.complete_patch()

        # Move nwscript.nss to Override if there are any nss patches to do
        # if len(config.patches_nss) > 0:
        #    folder_install = InstallFolder("Override")  # noqa: ERA001
        #    if folder_install not in config.install_list:
        #        config.install_list.append(folder_install)  # noqa: ERA001
        #    file_install = InstallFile("nwscript.nss", replace_existing=True)  # noqa: ERA001
        #    folder_install.files.append(file_install)  # noqa: ERA001

        self.log.add_note("Applying patches from [InstallList]...")
        for folder in config.install_list:
            folder.apply(self.log, self.mod_path, self.game_path, backup_dir, processed_files)
            self.log.complete_patch()

        self.log.add_note("Applying patches from [2DAList]...")
        for twoda_patch in config.patches_2da:
            resname, restype = ResourceIdentifier.from_path(twoda_patch.filename)
            twoda_output_folder: CaseAwarePath = self.game_path / "Override"
            search = installation.resource(
                resname,
                restype,
                [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS],
                folders=[self.mod_path],
            )
            if search is None or search.data is None:
                self.log.add_error(
                    f"Didn't patch '{twoda_patch.filename}' because search data is `None`.",
                )
                continue
            twoda: TwoDA = read_2da(search.data)
            twodas[twoda_patch.filename] = twoda

            create_backup(
                self.log,
                twoda_output_folder / twoda_patch.filename,
                backup_dir,
                processed_files,
                subdirectory_path="Override",
            )
            self.log.add_note(f"Patching '{twoda_patch.filename}'")
            twoda_patch.apply(twoda, memory)
            write_2da(twoda, twoda_output_folder / twoda_patch.filename)

            self.log.complete_patch()

        self.log.add_note("Applying patches from [GFFList]...")
        for gff_patch in config.patches_gff:
            resname, restype = ResourceIdentifier.from_path(gff_patch.filename)

            capsule = None
            gff_destination_path: CaseAwarePath = self.game_path / gff_patch.destination
            if is_capsule_file(gff_patch.destination.name):
                capsule = Capsule(gff_destination_path)

            search = installation.resource(
                resname,
                restype,
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.CUSTOM_FOLDERS,
                    SearchLocation.CUSTOM_MODULES,
                ],
                folders=[self.mod_path],
                capsules=[] if capsule is None else [capsule],
            )
            if search is None or search.data is None:
                self.log.add_error(
                    f"Didn't patch '{gff_patch.filename}' because search data is `None`.",
                )
                continue

            norm_game_path = self.game_path
            norm_file_path = norm_game_path / CaseAwarePath(gff_patch.destination)
            output_container_path = norm_file_path.relative_to(norm_game_path)

            if capsule is None:
                create_backup(
                    self.log,
                    gff_destination_path / gff_patch.filename,
                    backup_dir,
                    processed_files,
                    output_container_path.parent,
                )
                self.log.add_note(
                    f"Patching '{gff_patch.filename}' in the '{output_container_path.parent}' folder.",
                )
            else:
                create_backup(self.log, gff_destination_path, backup_dir / gff_destination_path.name, processed_files)
                self.log.add_note(
                    f"Patching '{gff_patch.filename}' in the '{output_container_path}' archive.",
                )
                if not capsule._path.exists():
                    self.log.add_warning(
                        f"The capsule '{output_container_path}' did not exist when patching GFF '{gff_patch.filename}'! Please note that TSLPatcher would have errored in this scenario.",
                    )
                    self.log.add_warning(
                        "The above warning most likely indicates a different problem existed beforehand, such as a missing mod dependency.",
                    )

            template = templates[gff_patch.filename] = read_gff(search.data)
            assert template is not None

            gff_patch.apply(template, memory, self.log)
            self.write(
                gff_destination_path,
                gff_patch.filename,
                bytes_gff(template),
                replace=True,
            )

            self.log.complete_patch()

        self.log.add_note("Applying patches from [CompileList]...")
        for nss_patch in config.patches_nss:
            capsule: Capsule | None = None
            output_container_path = self.game_path / nss_patch.destination
            rel_output_container_path = output_container_path.relative_to(self.game_path)

            if is_capsule_file(output_container_path.name):
                capsule = Capsule(output_container_path)
                create_backup(
                    self.log,
                    output_container_path,
                    backup_dir,
                    processed_files,
                    rel_output_container_path.parent,
                )
                self.log.add_note(
                    f"Patching '{nss_patch.filename}' in the '{rel_output_container_path}' archive.",
                )
                if not output_container_path.exists():
                    self.log.add_warning(
                        f"The capsule '{rel_output_container_path}' did not exist when patching GFF '{nss_patch.filename}'! Please note that TSLPatcher would have errored in this scenario!"
                        " This most likely indicates a different problem existed beforehand, such as a missing mod dependency.",
                    )
            else:
                create_backup(
                    self.log,
                    output_container_path / nss_patch.filename,
                    backup_dir,
                    processed_files,
                    nss_patch.destination,
                )
                self.log.add_note(
                    f"Patching '{nss_patch.filename}' in the '{rel_output_container_path}' folder.",
                )

            ncs_compiled_filename = f"{nss_patch.filename.rsplit('.', 1)[0]}.ncs"
            self.log.add_note(
                f"Compiling '{nss_patch.filename}' and saving to '{rel_output_container_path / ncs_compiled_filename}'",
            )

            nss_bytes = BinaryReader.load_file(self.mod_path / nss_patch.filename)
            encoding = chardet.detect(nss_bytes, should_rename_legacy=True)["encoding"] if chardet else None
            nss: list[str] = [nss_bytes.decode(encoding=encoding, errors="replace")]  # type: ignore[reportGeneralTypeIssues] already defaults to utf-8

            nss_patch.apply(nss, memory, self.log)

            self.write(
                output_container_path,
                ncs_compiled_filename,
                bytes_ncs(compile_nss(nss[0], installation.game())),
                nss_patch.replace_file,
            )

            self.log.complete_patch()

        self.log.add_note("Applying patches from [SSFList]...")
        for ssf_patch in config.patches_ssf:
            resname, restype = ResourceIdentifier.from_path(ssf_patch.filename)
            search = installation.resource(
                resname,
                restype,
                [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS],
                folders=[self.mod_path],
            )
            if search is None or search.data is None:
                self.log.add_error(
                    f"Didn't patch '{ssf_patch.filename}' because search data is `None`.",
                )
                continue

            soundset = soundsets[ssf_patch.filename] = read_ssf(search.data)
            ssf_output_filepath: CaseAwarePath = self.game_path / "Override" / ssf_patch.filename

            create_backup(self.log, ssf_output_filepath, backup_dir, processed_files, "Override")
            self.log.add_note(f"Patching '{ssf_patch.filename}' in the 'Override' folder.")
            ssf_patch.apply(soundset, memory)
            write_ssf(soundset, ssf_output_filepath)

            self.log.complete_patch()

    def write(
        self,
        destination: CaseAwarePath,
        filename: str,
        data: bytes,
        replace: bool = False,
    ) -> None:
        resname, restype = ResourceIdentifier.from_path(filename)
        if is_rim_file(destination.name):
            rim = read_rim(BinaryReader.load_file(destination)) if destination.exists() else RIM()
            if not rim.get(resname, restype) or replace:
                rim.set_data(resname, restype, data)
                write_rim(rim, destination)
        elif is_mod_file(destination.name):
            erf = (
                read_erf(BinaryReader.load_file(destination))
                if destination.exists()
                else ERF(ERFType.from_extension(destination.name))
            )
            if not erf.get(resname, restype) or replace:
                erf.set_resource(resname, restype, data)
                write_erf(erf, destination)
        elif not destination.exists() or replace:
            BinaryWriter.dump(destination, data)
