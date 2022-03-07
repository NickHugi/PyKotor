from pykotor.common.language import LocalizedString
from pykotor.common.module import Module
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.formats.lyt.lyt_auto import write_lyt
from pykotor.resource.formats.tpc import TPCTextureFormat, TPC, write_tpc
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


def clone_module(
        root: str,
        identifier: str,
        prefix: str,
        name: str,
        installation: Installation,
        *,
        copyTextures: bool = False,
        copyLightmaps: bool = False,
        keepDoors: bool = False,
        keepPlaceables: bool = False,
        keepSounds: bool = False,
        keepPathing: bool = False
) -> None:
    installation = installation
    root = root
    identifier = identifier

    oldModule = Module(root, installation)
    newModule = ERF(ERFType.MOD)

    ifo = oldModule.info.resource()
    oldIdentifier = ifo.identifier.get()
    ifo.identifier.set(identifier)
    ifo.mod_name = LocalizedString.from_english(identifier.upper())
    ifo.tag = identifier.upper()
    ifo.area_name.set(identifier)
    ifo_data = bytearray()
    write_gff(dismantle_ifo(ifo), ifo_data)
    newModule.set("module", ResourceType.IFO, ifo_data)

    are = oldModule.static.resource()
    are.name = LocalizedString.from_english(name)
    are_data = bytearray()
    write_gff(dismantle_are(are), are_data)
    newModule.set(identifier, ResourceType.ARE, are_data)

    lyt = oldModule.layout.resource()
    vis = oldModule.visibility.resource()

    if keepPathing:
        pth = oldModule.path.resource()
        pth_data = bytearray()
        write_gff(dismantle_pth(pth), pth_data)
        newModule.set(identifier, ResourceType.PTH, pth_data)

    git = oldModule.dynamic.resource()
    git.creatures = []
    git.encounters = []
    git.stores = []
    git.triggers = []
    git.waypoints = []
    git.cameras = []

    if keepDoors:
        for i, door in enumerate(git.doors):
            oldResname = door.resref.get()
            newResname = "{}_dor{}".format(identifier, i)
            door.resref.set(newResname)
            door.tag = newResname

            utd = oldModule.doors[oldResname].resource()
            data = bytearray()
            write_gff(dismantle_utd(utd), data)
            newModule.set(newResname, ResourceType.UTD, data)
    else:
        git.doors = []

    if keepPlaceables:
        for i, placeable in enumerate(git.placeables):
            oldResname = placeable.resref.get()
            newResname = "{}_plc{}".format(identifier, i)
            placeable.resref.set(newResname)
            placeable.tag = newResname

            utp = oldModule.placeables[oldResname].resource()
            data = bytearray()
            write_gff(dismantle_utp(utp), data)
            newModule.set(newResname, ResourceType.UTP, data)
    else:
        git.placeables = []

    if keepSounds:
        for i, sound in enumerate(git.sounds):
            oldResname = sound.resref.get()
            newResname = "{}_snd{}".format(identifier, i)
            sound.resref.set(newResname)
            sound.tag = newResname

            uts = oldModule.sounds[oldResname].resource()
            data = bytearray()
            write_gff(dismantle_uts(uts), data)
            newModule.set(newResname, ResourceType.UTS, data)
    else:
        git.sounds = []

    git_data = bytearray()
    write_gff(dismantle_git(git), git_data)
    newModule.set(identifier, ResourceType.GIT, git_data)

    newLightmaps = {}
    newTextures = {}
    for room in lyt.rooms:
        oldModelName = room.model
        newModelName = oldModelName.lower().replace(oldIdentifier, identifier)

        room.model = newModelName
        vis.rename_room(oldModelName, newModelName)

        mdlData = installation.resource(oldModelName, ResourceType.MDL).data
        mdxData = installation.resource(oldModelName, ResourceType.MDX).data
        wokData = installation.resource(oldModelName, ResourceType.WOK).data

        if copyTextures:
            for texture in model.list_textures(mdlData):
                if texture not in newTextures:
                    newTextureName = prefix + texture[3:]
                    newTextures[texture] = newTextureName

                    tpc = installation.texture(texture)
                    tpc = TPC() if tpc is None else tpc
                    rgba = tpc.convert(TPCTextureFormat.RGBA)

                    tga = TPC()
                    tga.set(rgba.width, rgba.height, [rgba.data], TPCTextureFormat.RGBA)

                    tga_data = bytearray()
                    write_tpc(tga, tga_data, ResourceType.TGA)
                    newModule.set(newTextureName, ResourceType.TGA, tga_data)
            mdlData = model.change_textures(mdlData, newTextures)

        if copyLightmaps:
            for lightmap in model.list_lightmaps(mdlData):
                if lightmap not in newLightmaps:
                    newLightmapName = "{}_lm_{}".format(identifier, len(newLightmaps.keys()))
                    newLightmaps[lightmap] = newLightmapName

                    tpc = installation.texture(lightmap, [SearchLocation.CHITIN, SearchLocation.OVERRIDE])
                    tpc = TPC() if tpc is None else tpc
                    rgba = tpc.convert(TPCTextureFormat.RGBA)

                    tga = TPC()
                    tga.set(rgba.width, rgba.height, [rgba.data], TPCTextureFormat.RGBA)

                    tga_data = bytearray()
                    write_tpc(tga, tga_data, ResourceType.TGA)
                    newModule.set(newLightmapName, ResourceType.TGA, tga_data)
            mdlData = model.change_lightmaps(mdlData, newLightmaps)

        mdlData = model.rename(mdlData, newModelName)
        newModule.set(newModelName, ResourceType.MDL, mdlData)
        newModule.set(newModelName, ResourceType.MDX, mdxData)
        newModule.set(newModelName, ResourceType.WOK, wokData)

    vis_data = bytearray()
    write_vis(vis, vis_data)
    newModule.set(identifier, ResourceType.VIS, vis_data)

    lyt_data = bytearray()
    write_lyt(lyt, lyt_data)
    newModule.set(identifier, ResourceType.LYT, lyt_data)

    filepath = installation.module_path() + identifier + ".mod"
    write_erf(newModule, filepath)
