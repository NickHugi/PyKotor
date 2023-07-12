import os

from pathlib import Path
from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tlk import read_tlk


def uninstall_all_mods(installation: Installation):
    root_path = installation.path()
    override_path = installation.override_path()
    modules_path = installation.module_path()

    # Remove any TLK changes
    dialog_tlk = read_tlk(Path(root_path, "dialog.tlk"))
    dialog_tlk.entries = dialog_tlk.entries[:49265] if installation.game() == Game.K1 else dialog_tlk.entries[:136329]

    # Remove all override files
    for filename in os.listdir(override_path):
        filepath = Path(override_path, filename)
        os.remove(filepath.resolve())

    # Remove any .MOD files
    for filename in os.listdir(modules_path):
        if filename.endswith(".mod"):
            filepath = Path(modules_path, filename)
            os.remove(filepath.resolve())