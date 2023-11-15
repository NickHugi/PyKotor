from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tlk import read_tlk, write_tlk
from pykotor.tools.misc import is_mod_file
from pykotor.tools.path import CaseAwarePath


# TODO: the aspyr patch contains some required files in the override folder, hardcode them and ignore those here.
def uninstall_all_mods(installation: Installation):
    """Uninstalls all mods from the game.

    What this method really does is delete all the contents of the override folder and delete all .MOD files from
    the modules folder. Then it removes all appended TLK entries using
    the hardcoded number of entries depending on the game. There are 49,265 TLK entries in KOTOR 1, and 136,329 in TSL.
    """
    root_path = installation.path()
    override_path = installation.override_path()
    modules_path = installation.module_path()

    # Remove any TLK changes
    dialog_tlk_path = CaseAwarePath(root_path, "dialog.tlk")
    dialog_tlk = read_tlk(dialog_tlk_path)
    dialog_tlk.entries = dialog_tlk.entries[:49265] if installation.game() == Game.K1 else dialog_tlk.entries[:136329]
    # TODO: With the new Replace TLK syntax, the above TLK reinstall isn't possible anymore.
    # Here, we should write the dialog.tlk and then check it's sha1 hash compared to vanilla.
    # We could keep the vanilla TLK entries in a tlkdefs.py file, similar to our nwscript.nss defs in scriptdefs.py.
    # This implementation would be required regardless in K2 anyway as this function currently isn't determining if the Aspyr patch and/or TSLRCM is installed.
    write_tlk(dialog_tlk, dialog_tlk_path)

    # Remove all override files
    for file_path in override_path.iterdir():
        file_path.unlink()

    # Remove any .MOD files
    for file_path in modules_path.iterdir():
        if is_mod_file(file_path.name):
            file_path.unlink()
