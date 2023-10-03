from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.module import Module
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.formats.lyt.lyt_auto import write_lyt
from pykotor.resource.formats.rim import RIM, read_rim
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
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    import os


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
) -> None:
    old_module = Module(root, installation)
    new_module = ERF(ERFType.MOD)

    ifo = old_module.info().resource()
    old_identifier = ifo.identifier.get()
    ifo.identifier.set_data(identifier)
    ifo.mod_name = LocalizedString.from_english(identifier.upper())
    ifo.tag = identifier.upper()
    ifo.area_name.set_data(identifier)
    ifo_data = bytearray()
    write_gff(dismantle_ifo(ifo), ifo_data)
    new_module.set_data("module", ResourceType.IFO, ifo_data)

    are = old_module.are().resource()
    are.name = LocalizedString.from_english(name)
    are_data = bytearray()
    write_gff(dismantle_are(are), are_data)
    new_module.set_data(identifier, ResourceType.ARE, are_data)

    lyt = old_module.layout().resource()
    vis = old_module.vis().resource()
    git = old_module.git().resource()

    if keep_pathing:
        pth = old_module.pth().resource()
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
            old_resname = door.resref.get()
            new_resname = f"{identifier}_dor{i}"
            door.resref.set_data(new_resname)
            door.tag = new_resname

            utd = old_module.door(old_resname).resource()
            data = bytearray()
            write_gff(dismantle_utd(utd), data)
            new_module.set_data(new_resname, ResourceType.UTD, data)
    else:
        git.doors = []

    if keep_placeables:
        for i, placeable in enumerate(git.placeables):
            old_resname = placeable.resref.get()
            new_resname = f"{identifier}_plc{i}"
            placeable.resref.set_data(new_resname)
            placeable.tag = new_resname

            utp = old_module.placeable(old_resname).resource()
            data = bytearray()
            write_gff(dismantle_utp(utp), data)
            new_module.set_data(new_resname, ResourceType.UTP, data)
    else:
        git.placeables = []

    if keep_sounds:
        for i, sound in enumerate(git.sounds):
            old_resname = sound.resref.get()
            new_resname = f"{identifier}_snd{i}"
            sound.resref.set_data(new_resname)
            sound.tag = new_resname

            uts = old_module.sound(old_resname).resource()
            data = bytearray()
            write_gff(dismantle_uts(uts), data)
            new_module.set_data(new_resname, ResourceType.UTS, data)
    else:
        git.sounds = []

    git_data = bytearray()
    write_gff(dismantle_git(git), git_data)
    new_module.set_data(identifier, ResourceType.GIT, git_data)

    new_lightmaps = {}
    new_textures = {}
    for room in lyt.rooms:
        old_model_name = room.model
        new_model_name = old_model_name.lower().replace(old_identifier, identifier)

        room.model = new_model_name
        if vis.room_exists(old_model_name):
            vis.rename_room(old_model_name, new_model_name)

        mdl_data = installation.resource(old_model_name, ResourceType.MDL).data
        mdx_data = installation.resource(old_model_name, ResourceType.MDX).data
        wok_data = installation.resource(old_model_name, ResourceType.WOK).data

        if copy_textures:
            for texture in model.list_textures(mdl_data):
                if texture not in new_textures:
                    new_texture_name = prefix + texture[3:]
                    new_textures[texture] = new_texture_name

                    tpc = installation.texture(texture)
                    tpc = TPC() if tpc is None else tpc
                    rgba = tpc.convert(TPCTextureFormat.RGBA)

                    tga = TPC()
                    tga.set_data(rgba.width, rgba.height, [rgba.data], TPCTextureFormat.RGBA)

                    tga_data = bytearray()
                    write_tpc(tga, tga_data, ResourceType.TGA)
                    new_module.set_data(new_texture_name, ResourceType.TGA, tga_data)
            mdl_data = model.change_textures(mdl_data, new_textures)

        if copy_lightmaps:
            for lightmap in model.list_lightmaps(mdl_data):
                if lightmap not in new_lightmaps:
                    new_lightmap_name = f"{identifier}_lm_{len(new_lightmaps.keys())}"
                    new_lightmaps[lightmap] = new_lightmap_name

                    tpc = installation.texture(
                        lightmap,
                        [SearchLocation.CHITIN, SearchLocation.OVERRIDE],
                    )
                    tpc = TPC() if tpc is None else tpc
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

    vis_data = bytearray()
    write_vis(vis, vis_data)
    new_module.set_data(identifier, ResourceType.VIS, vis_data)

    lyt_data = bytearray()
    write_lyt(lyt, lyt_data)
    new_module.set_data(identifier, ResourceType.LYT, lyt_data)

    filepath = installation.module_path() / f"{identifier}.mod"
    write_erf(new_module, filepath)


def rim_to_mod(filepath: os.PathLike | str) -> None:
    """Creates a MOD file at the given filepath and copies the resources from the corresponding
    RIM files.

    Raises:
    ------
        ValueError: If the file was corrupted or the format could not be determined.
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Args:
    ----
        filepath: The filepath of the MOD file you would like to create.
    """
    resolved_file_path = CaseAwarePath(filepath)
    if resolved_file_path.suffix.lower() != ".mod":
        msg = "Specified file must end with the .mod extension"
        raise ValueError(msg)

    file_ext_rim = resolved_file_path.suffix.lower().replace(".mod", ".rim")
    file_ext_rim_s = resolved_file_path.suffix.lower().replace(".mod", "_s.rim")

    filepath_rim = resolved_file_path.with_suffix(file_ext_rim)
    filepath_rim_s = resolved_file_path.with_suffix(file_ext_rim_s)

    rim = read_rim(filepath_rim)
    rim_s = read_rim(filepath_rim_s) if filepath_rim_s.exists() else RIM()

    mod = ERF(ERFType.MOD)
    [mod.set_data(res.resref.get(), res.restype, res.data) for res in rim]
    [mod.set_data(res.resref.get(), res.restype, res.data) for res in rim_s]

    write_erf(mod, filepath, ResourceType.ERF)
