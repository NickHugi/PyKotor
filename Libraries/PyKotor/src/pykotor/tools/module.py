from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.module import Module
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
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
from utility.error_handling import assert_with_variable_trace
from utility.string import ireplace

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import ResRef
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.formats.tpc.tpc_data import TPCConvertResult
    from pykotor.resource.formats.vis import VIS
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import GIT
    from pykotor.resource.generics.ifo import IFO
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

    ifo: IFO | None = old_module.info().resource()
    assert_with_variable_trace(ifo is not None, f"ifo {ifo!r} cannot be None in clone_module")
    assert ifo is not None, f"ifo {ifo!r} cannot be None in clone_module"

    old_resref: ResRef = ifo.resref
    ifo.resref.set_data(identifier)
    ifo.mod_name = LocalizedString.from_english(identifier.upper())
    ifo.tag = identifier.upper()
    ifo.area_name.set_data(identifier)
    ifo_data = bytearray()

    write_gff(dismantle_ifo(ifo), ifo_data)
    new_module.set_data("module", ResourceType.IFO, ifo_data)

    are_res = old_module.are()
    assert are_res is not None, assert_with_variable_trace(are_res is not None, "old_module.are() returned None in clone_module")  # noqa: S101
    are: ARE | None = are_res.resource()
    assert are is not None, assert_with_variable_trace(are is not None, "old_module.are().resource() returned None in clone_module")  # noqa: S101, E501

    are.name = LocalizedString.from_english(name)
    are_data = bytearray()

    write_gff(dismantle_are(are), are_data)
    new_module.set_data(identifier, ResourceType.ARE, are_data)

    lyt_res = old_module.layout()
    assert lyt_res is not None, assert_with_variable_trace(lyt_res is not None, "old_module.layout() returned None in clone_module")  # noqa: S101, E501
    lyt: LYT | None = lyt_res.resource()
    assert lyt is not None, assert_with_variable_trace(lyt is not None, "old_module.layout().resource() returned None in clone_module")  # noqa: S101, E501

    vis_res = old_module.vis()
    assert vis_res is not None, assert_with_variable_trace(vis_res is not None, "old_module.vis() returned None in clone_module")  # noqa: S101
    vis: VIS | None = vis_res.resource()
    assert vis is not None, assert_with_variable_trace(vis is not None, "old_module.vis().resource() returned None in clone_module")  # noqa: S101, E501

    git_res = old_module.git()
    assert git_res is not None, assert_with_variable_trace(git_res is not None, "old_module.git() returned None in clone_module")  # noqa: S101
    git: GIT | None = git_res.resource()
    assert git is not None, assert_with_variable_trace(git is not None, "old_module.git().resource() returned None in clone_module")  # noqa: S101, E501

    if keep_pathing:  # sourcery skip: extract-method
        pth_res = old_module.pth()
        assert pth_res is not None, assert_with_variable_trace(pth_res is not None, "old_module.pth() returned None in clone_module")  # noqa: S101, E501
        pth: PTH | None = pth_res.resource()
        assert pth is not None, assert_with_variable_trace(pth is not None, "old_module.pth().resource() returned None in clone_module")  # noqa: S101, E501

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
            assert utd_res is not None, assert_with_variable_trace(utd_res is not None, "old_module.door() returned None in clone_module")  # noqa: S101, E501
            utd: UTD | None = utd_res.resource()
            assert utd is not None, assert_with_variable_trace(utd is not None, "old_module.door().resource() returned None in clone_module")  # noqa: S101, E501

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
            assert utp_res is not None, assert_with_variable_trace(utp_res is not None, "old_module.placeable() returned None in clone_module")  # noqa: S101, E501
            utp: UTP | None = utp_res.resource()
            assert utp is not None, assert_with_variable_trace(utp is not None, "old_module.placeable().resource() returned None in clone_module")  # noqa: S101, E501

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
            assert uts_res is not None, assert_with_variable_trace(uts_res is not None, "old_module.sound() returned None in clone_module")  # noqa: S101, E501
            uts: UTS | None = uts_res.resource()
            assert uts is not None, assert_with_variable_trace(uts is not None, "old_module.sound().resource() returned None in clone_module")  # noqa: S101, E501

            data = bytearray()
            write_gff(dismantle_uts(uts), data)
            new_module.set_data(new_resname, ResourceType.UTS, data)
    else:
        git.sounds = []

    git_data = bytearray()

    write_gff(dismantle_git(git), git_data)
    new_module.set_data(identifier, ResourceType.GIT, git_data)

    new_lightmaps: dict[str, str] = {}
    new_textures: dict[str, str] = {}
    for room in lyt.rooms:
        old_model_name = room.model
        new_model_name = ireplace(old_model_name, str(old_resref), identifier)

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

                    tpc: TPC = installation.texture(texture) or TPC()
                    rgba: TPCConvertResult = tpc.convert(TPCTextureFormat.RGBA)

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
                    ) or TPC()
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

    assert vis is not None, "vis cannot be None in clone_module"
    vis_data = bytearray()
    write_vis(vis, vis_data)
    new_module.set_data(identifier, ResourceType.VIS, vis_data)

    assert lyt is not None, "lyt cannot be None in clone_module"
    lyt_data = bytearray()
    write_lyt(lyt, lyt_data)
    new_module.set_data(identifier, ResourceType.LYT, lyt_data)

    filepath: CaseAwarePath = installation.module_path() / f"{identifier}.mod"
    write_erf(new_module, filepath)


def rim_to_mod(filepath: os.PathLike | str):
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
    """
    resolved_file_path: CaseAwarePath = CaseAwarePath.pathify(filepath)
    if not is_mod_file(resolved_file_path):
        msg = "Specified file must end with the .mod extension"
        raise ValueError(msg)

    filepath_rim: CaseAwarePath = resolved_file_path.with_suffix(".rim")
    filepath_rim_s: CaseAwarePath = resolved_file_path.parent / f"{resolved_file_path.stem}_s.rim"

    mod = ERF(ERFType.MOD)
    for res in read_rim(filepath_rim):
        mod.set_data(str(res.resref), res.restype, res.data)
    if filepath_rim_s.is_file():
        for res in read_rim(filepath_rim_s):
            mod.set_data(str(res.resref), res.restype, res.data)

    write_erf(mod, filepath, ResourceType.MOD)
