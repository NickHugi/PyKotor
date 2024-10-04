from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.common.language import LocalizedString
from pykotor.common.module import Module
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.erf import ERF, ERFType, read_erf, write_erf
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.formats.lyt import write_lyt
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, write_tpc
from pykotor.resource.formats.vis import write_vis
from pykotor.resource.generics.are import dismantle_are
from pykotor.resource.generics.git import dismantle_git
from pykotor.resource.generics.ifo import dismantle_ifo
from pykotor.resource.generics.pth import dismantle_pth
from pykotor.resource.generics.utd import dismantle_utd
from pykotor.resource.generics.utp import dismantle_utp
from pykotor.resource.generics.uts import dismantle_uts
from pykotor.resource.type import ResourceType
from pykotor.tools import model
from pykotor.tools.misc import is_mod_file
from pykotor.tools.path import CaseAwarePath
from utility.common.misc_string.util import ireplace

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import Game, ResRef
    from pykotor.resource.formats.tpc.tpc_data import TPCConvertResult
    from pykotor.resource.generics.pth import PTH
    from pykotor.resource.generics.utd import UTD
    from pykotor.resource.generics.utp import UTP
    from pykotor.resource.generics.uts import UTS


def clone_module(
    root: str,
    identifier: str,
    prefix: str,
    name: str,
    installation: Installation,
    *,
    copy_textures: bool = False,
    copy_lightmaps: bool = False,
    keep_doors: bool = False,
    keep_placeables: bool = False,
    keep_sounds: bool = False,
    keep_pathing: bool = False,
):
    """Clones a module.

    Args:
    ----
        root: str - The path to the module root
        identifier: str - The resref str for the new module
        prefix: str - Prefix for generated textures and lightmaps
        name: str - Name for the new ARE file
        installation: Installation - The installation context

    Processing Logic:
    ----------------
        1. Load resources from old module
        2. Rename resources and change identifiers
        3. Copy textures and lightmaps if specified
        4. Write new module resources to file.
    """
    old_module = Module(root, installation)
    new_module = ERF(ERFType.MOD)

    git_res = old_module.git()
    git = git_res.resource() if git_res is not None else None
    if git is None:
        raise ValueError(f"No GIT file found in module '{root}'")

    ifo_res = old_module.info()
    ifo = ifo_res.resource() if ifo_res is not None else None
    if ifo is not None:
        old_resref: ResRef = ifo.resref
        ifo.resref.set_data(identifier)
        ifo.mod_name = LocalizedString.from_english(identifier.upper())
        ifo.tag = identifier.upper()
        ifo.area_name.set_data(identifier)
        ifo_data = bytearray()
        write_gff(dismantle_ifo(ifo), ifo_data)
        new_module.set_data("module", ResourceType.IFO, ifo_data)
    else:
        RobustLogger().warning(f"No IFO found in module to be cloned: '{root}'")

    are_res = old_module.are()
    are = are_res.resource() if are_res is not None else None

    if are is not None:
        are.name = LocalizedString.from_english(name)
        are_data = bytearray()

        write_gff(dismantle_are(are), are_data)
        new_module.set_data(identifier, ResourceType.ARE, are_data)
    else:
        RobustLogger().warning(f"No ARE found in module to be cloned: '{root}'")

    if keep_pathing:  # sourcery skip: extract-method
        pth_res = old_module.pth()
        pth: PTH | None = None if pth_res is None else pth_res.resource()
        if pth is not None:
            pth_data = bytearray()
            write_gff(dismantle_pth(pth), pth_data)
            new_module.set_data(identifier, ResourceType.PTH, pth_data)

    git.creatures = []
    git.encounters = []
    git.stores = []
    git.triggers = []
    git.waypoints = []
    git.cameras = []

    if keep_doors:
        for i, door in enumerate(git.doors):
            old_resname = str(door.resref)
            new_resname = f"{identifier}_dor{i}"
            door.resref.set_data(new_resname)
            door.tag = new_resname

            utd_res = old_module.door(old_resname)
            if utd_res is None:
                RobustLogger().warning(f"No UTD found for door '{old_resname}' in module '{root}'")
                continue
            utd: UTD | None = utd_res.resource()
            if utd is None:
                RobustLogger().warning(f"UTD resource is None for door '{old_resname}' in module '{root}'")
                continue

            data = bytearray()
            write_gff(dismantle_utd(utd), data)
            new_module.set_data(new_resname, ResourceType.UTD, data)
    else:
        git.doors = []

    if keep_placeables:
        for i, placeable in enumerate(git.placeables):
            old_resname = str(placeable.resref)
            new_resname = f"{identifier}_plc{i}"
            placeable.resref.set_data(new_resname)
            placeable.tag = new_resname

            utp_res = old_module.placeable(old_resname)
            if utp_res is None:
                RobustLogger().warning(f"No UTP found for placeable '{old_resname}' in module '{root}'")
                continue
            utp: UTP | None = utp_res.resource()
            if utp is None:
                RobustLogger().warning(f"UTP resource is None for placeable '{old_resname}' in module '{root}'")
                continue

            data = bytearray()
            write_gff(dismantle_utp(utp), data)
            new_module.set_data(new_resname, ResourceType.UTP, data)
    else:
        git.placeables = []

    if keep_sounds:
        for i, sound in enumerate(git.sounds):
            old_resname = str(sound.resref)
            new_resname = f"{identifier}_snd{i}"
            sound.resref.set_data(new_resname)
            sound.tag = new_resname

            uts_res = old_module.sound(old_resname)
            if uts_res is None:
                RobustLogger().warning(f"No UTS found for sound '{old_resname}' in module '{root}'")
                continue
            uts: UTS | None = uts_res.resource()
            if uts is None:
                RobustLogger().warning(f"UTS resource is None for sound '{old_resname}' in module '{root}'")
                continue

            data = bytearray()
            write_gff(dismantle_uts(uts), data)
            new_module.set_data(new_resname, ResourceType.UTS, data)
    else:
        git.sounds = []

    git_data = bytearray()

    write_gff(dismantle_git(git), git_data)
    new_module.set_data(identifier, ResourceType.GIT, git_data)

    lyt_res = old_module.layout()
    lyt = lyt_res.resource() if lyt_res is not None else None

    vis_res = old_module.vis()
    vis = vis_res.resource() if vis_res is not None else None

    new_lightmaps: dict[str, str] = {}
    new_textures: dict[str, str] = {}
    if lyt is not None:
        for room in lyt.rooms:
            old_model_name = room.model
            new_model_name = ireplace(old_model_name, str(old_resref), identifier)

            room.model = new_model_name
            if vis is not None and vis.room_exists(old_model_name):
                vis.rename_room(old_model_name, new_model_name)

            mdl_resource = installation.resource(old_model_name, ResourceType.MDL)
            mdl_data = None if mdl_resource is None else mdl_resource.data
            if mdl_data is None:
                continue
            mdx_resource = installation.resource(old_model_name, ResourceType.MDX)
            mdx_data = None if mdx_resource is None else mdx_resource.data
            if mdx_data is None:
                continue
            wok_resource = installation.resource(old_model_name, ResourceType.WOK)
            wok_data = None if wok_resource is None else wok_resource.data
            if wok_data is None:
                continue

            if copy_textures:
                for texture in model.iterate_textures(mdl_data):
                    if texture in new_textures:
                        continue
                    new_texture_name = prefix + texture[3:]
                    new_textures[texture] = new_texture_name

                    tpc: TPC | None = installation.texture(
                        texture,
                        [
                            SearchLocation.CHITIN,
                            SearchLocation.OVERRIDE,
                            SearchLocation.TEXTURES_GUI,
                            SearchLocation.TEXTURES_TPA,
                        ],
                    )
                    if tpc is None:
                        RobustLogger().warning(f"TPC/TGA resource not found for texture '{texture}' in module '{root}'")
                        continue
                    rgba: TPCConvertResult = tpc.convert(TPCTextureFormat.RGBA)

                    tga = TPC()
                    tga.set_data(rgba.width, rgba.height, [rgba.data], TPCTextureFormat.RGBA)

                    tga_data = bytearray()
                    try:
                        write_tpc(tga, tga_data, ResourceType.TGA)
                    except ValueError as e:
                        RobustLogger().warning(f"Failed to write TGA for texture '{texture}' in clone_module: {e}")
                        continue
                    new_module.set_data(new_texture_name, ResourceType.TGA, tga_data)
                mdl_data = model.change_textures(mdl_data, new_textures)

            if copy_lightmaps:
                for lightmap in model.iterate_lightmaps(mdl_data):
                    if lightmap in new_lightmaps:
                        continue
                    new_lightmap_name = f"{identifier}_lm_{len(new_lightmaps.keys())}"
                    new_lightmaps[lightmap] = new_lightmap_name

                    tpc = installation.texture(
                        lightmap,
                        [
                            SearchLocation.CHITIN,
                            SearchLocation.OVERRIDE,
                            SearchLocation.TEXTURES_GUI,
                            SearchLocation.TEXTURES_TPA,
                        ],
                    )
                    if tpc is None:
                        RobustLogger().warning(f"TPC/TGA resource not found for lightmap '{texture}' in module '{root}'")
                        continue
                    rgba = tpc.convert(TPCTextureFormat.RGBA)

                    tga = TPC()
                    tga.set_data(rgba.width, rgba.height, [rgba.data], TPCTextureFormat.RGBA)

                    tga_data = bytearray()
                    write_tpc(tga, tga_data, ResourceType.TGA)
                    new_module.set_data(new_lightmap_name, ResourceType.TGA, tga_data)
                mdl_data = model.change_lightmaps(mdl_data, new_lightmaps)

            mdl_data = model.rename(mdl_data, new_model_name)
            new_module.set_data(new_model_name, ResourceType.MDL, mdl_data)
            new_module.set_data(new_model_name, ResourceType.MDX, mdx_data)
            new_module.set_data(new_model_name, ResourceType.WOK, wok_data)

    if vis is not None:
        vis_data = bytearray()
        write_vis(vis, vis_data)
        new_module.set_data(identifier, ResourceType.VIS, vis_data)
    else:
        RobustLogger().warning(f"No VIS found in module to be cloned: '{root}'")

    if lyt is not None:
        lyt_data = bytearray()
        write_lyt(lyt, lyt_data)
        new_module.set_data(identifier, ResourceType.LYT, lyt_data)
    else:
        RobustLogger().error(f"No LYT found in module to be cloned: '{root}'")

    filepath: CaseAwarePath = installation.module_path() / f"{identifier}.mod"
    write_erf(new_module, filepath)


def rim_to_mod(
    filepath: os.PathLike | str,
    rim_folderpath: os.PathLike | str | None = None,
    module_root: str | None = None,
    game: Game | None = None,
):
    """Creates a MOD file at the given filepath and copies the resources from the corresponding RIM files.

    Raises:
    ------
        ValueError: If the file was corrupted or the format could not be determined.
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Args:
    ----
        filepath: The filepath of the MOD file you would like to create.
        rim_folderpath: Folderpath where the rims can be found for this module.
            The filestem of the filepath will be used to determine which rim to load.
    """
    r_outpath: CaseAwarePath = CaseAwarePath(filepath)
    if not is_mod_file(r_outpath):
        msg = "Specified file must end with the .mod extension"
        raise ValueError(msg)

    module_root = Installation.get_module_root(module_root or filepath)
    r_rim_folderpath = CaseAwarePath(rim_folderpath) if rim_folderpath else r_outpath.parent

    filepath_rim: CaseAwarePath = r_rim_folderpath / f"{module_root}.rim"
    filepath_rim_s: CaseAwarePath = r_rim_folderpath / f"{module_root}_s.rim"
    filepath_dlg_erf: CaseAwarePath = r_rim_folderpath / f"{module_root}_dlg.erf"

    mod = ERF(ERFType.MOD)
    for res in read_rim(filepath_rim):
        mod.set_data(str(res.resref), res.restype, res.data)

    if filepath_rim_s.is_file():
        for res in read_rim(filepath_rim_s):
            mod.set_data(str(res.resref), res.restype, res.data)

    if (game is None or game.is_k2()) and filepath_dlg_erf.is_file():
        for res in read_erf(filepath_dlg_erf):
            mod.set_data(str(res.resref), res.restype, res.data)

    write_erf(mod, filepath, ResourceType.MOD)
