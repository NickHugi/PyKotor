from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.formats.txi.txi_data import TXI, TXICommand
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class TXIReaderMode(IntEnum):
    """This class is used to store the modes of a texture."""

    NORMAL = 0
    UPPER_LEFT_COORDS = 1
    LOWER_RIGHT_COORDS = 2


class TXIBinaryReader(ResourceReader):
    """Reads TXI (Texture Information) files.
    
    TXI files contain texture metadata including blending modes, bump maps, animations,
    and other rendering properties for TPC textures.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/txireader.cpp (TXI reading)
    """
    def __init__(self, source: SOURCE_TYPES, offset: int = 0, size: int = 0):
        super().__init__(source, offset, size)
        from pykotor.resource.formats.txi.txi_data import TXI

        self._txi: TXI = TXI()

    @autoclose
    def load(self, *, auto_close: bool = True) -> TXI:  # noqa: FBT001, FBT002, ARG002
        from pykotor.resource.formats.txi.txi_data import TXI, TXICommand, TXIFeatures

        self._txi.features = TXIFeatures()
        self._empty = True
        mode = TXIReaderMode.NORMAL
        cur_coords: int = 0
        txi_bytes = self._reader.read_all()

        for line in txi_bytes.decode("ascii", errors="ignore").splitlines():
            try:
                parsed_line: str = line.strip()
                if not parsed_line:
                    continue

                if mode == TXIReaderMode.UPPER_LEFT_COORDS:
                    coords = list(map(float, map(str.strip, parsed_line.split())))
                    self._txi.features.upperleftcoords.append(coords)
                    cur_coords += 1
                    if cur_coords >= len(self._txi.features.upperleftcoords):
                        mode = TXIReaderMode.NORMAL
                    continue

                if mode == TXIReaderMode.LOWER_RIGHT_COORDS:
                    coords = list(map(float, map(str.strip, parsed_line.split())))
                    self._txi.features.lowerrightcoords.append(coords)
                    cur_coords += 1
                    if cur_coords >= len(self._txi.features.lowerrightcoords):
                        mode = TXIReaderMode.NORMAL
                    continue

                raw_cmd, args = (
                    parsed_line.split(" ", maxsplit=1)
                    if " " in parsed_line
                    else (
                        parsed_line,
                        "",
                    )
                )
                parsed_cmd_str: str = raw_cmd.strip().upper()
                if not parsed_cmd_str or parsed_cmd_str not in TXICommand.__members__:
                    #RobustLogger().warning(f"Invalid TXI command: '{raw_cmd}'")
                    continue
                command: TXICommand = TXICommand.__members__[parsed_cmd_str]
                args: str = args.strip() if args else ""

                if command == TXICommand.ALPHAMEAN:
                    self._txi.features.alphamean = float(args)
                    self._empty = False
                elif command == TXICommand.ARTUROHEIGHT:
                    self._txi.features.arturoheight = int(args)
                    self._empty = False
                elif command == TXICommand.ARTUROWIDTH:
                    self._txi.features.arturowidth = int(args)
                    self._empty = False
                elif command == TXICommand.BASELINEHEIGHT:
                    self._txi.features.baselineheight = int(args)
                    self._empty = False
                elif command == TXICommand.BLENDING:
                    self._txi.features.blending = TXI.parse_blending(args)
                    self._empty = False
                elif command == TXICommand.BUMPMAPSCALING:
                    self._txi.features.bumpmapscaling = float(args)
                    self._empty = False
                elif command == TXICommand.BUMPMAPTEXTURE:
                    self._txi.features.bumpmaptexture = args
                    self._empty = False
                elif command == TXICommand.BUMPYSHINYTEXTURE:
                    self._txi.features.bumpyshinytexture = args
                    self._empty = False
                elif command == TXICommand.CANDOWNSAMPLE:
                    self._txi.features.candownsample = bool(int(args))
                    self._empty = False
                elif command == TXICommand.CARETINDENT:
                    self._txi.features.caretindent = int(args)
                    self._empty = False
                elif command == TXICommand.CHANNELSCALE:
                    self._txi.features.channelscale = list(map(float, args.split()))
                    self._empty = False
                elif command == TXICommand.CHANNELTRANSLATE:
                    self._txi.features.channeltranslate = list(map(float, args.split()))
                    self._empty = False
                elif command == TXICommand.CLAMP:
                    self._txi.features.clamp = bool(int(args))
                    self._empty = False
                elif command == TXICommand.CODEPAGE:
                    self._txi.features.codepage = int(args)
                    self._empty = False
                elif command == TXICommand.COLS:
                    self._txi.features.cols = int(args)
                    self._empty = False
                elif command == TXICommand.COMPRESSTEXTURE:
                    self._txi.features.compresstexture = bool(int(args))
                    self._empty = False
                elif command == TXICommand.CONTROLLERSCRIPT:
                    self._txi.features.controllerscript = args
                    self._empty = False
                elif command == TXICommand.CUBE:
                    self._txi.features.cube = bool(int(args))
                    self._empty = False
                elif command == TXICommand.DBMAPPING:
                    self._txi.features.dbmapping = bool(int(args))
                    self._empty = False
                elif command == TXICommand.DECAL:
                    self._txi.features.decal = bool(int(args))
                    self._empty = False
                elif command == TXICommand.DEFAULTBPP:
                    self._txi.features.defaultbpp = int(args)
                    self._empty = False
                elif command == TXICommand.DEFAULTHEIGHT:
                    self._txi.features.defaultheight = int(args)
                    self._empty = False
                elif command == TXICommand.DEFAULTWIDTH:
                    self._txi.features.defaultwidth = int(args)
                    self._empty = False
                elif command == TXICommand.DISTORT:
                    self._txi.features.distort = bool(int(args))
                    self._empty = False
                elif command == TXICommand.DISTORTANGLE:
                    self._txi.features.distortangle = float(args)
                    self._empty = False
                elif command == TXICommand.DISTORTIONAMPLITUDE:
                    self._txi.features.distortionamplitude = float(args)
                    self._empty = False
                elif command == TXICommand.DOWNSAMPLEFACTOR:
                    self._txi.features.downsamplefactor = float(args)
                    self._empty = False
                elif command == TXICommand.DOWNSAMPLEMAX:
                    self._txi.features.downsamplemax = int(args)
                    self._empty = False
                elif command == TXICommand.DOWNSAMPLEMIN:
                    self._txi.features.downsamplemin = int(args)
                    self._empty = False
                elif command == TXICommand.ENVMAPTEXTURE:
                    self._txi.features.envmaptexture = args
                    self._empty = False
                elif command == TXICommand.FILERANGE:
                    self._txi.features.filerange = list(map(int, args.split()))
                    self._empty = False
                elif command == TXICommand.FILTER:
                    self._txi.features.filter = bool(int(args))
                    self._empty = False
                elif command == TXICommand.FONTHEIGHT:
                    self._txi.features.fontheight = int(args)
                    self._empty = False
                elif command == TXICommand.FONTWIDTH:
                    self._txi.features.fontwidth = int(args)
                    self._empty = False
                elif command == TXICommand.FPS:
                    self._txi.features.fps = float(args)
                    self._empty = False
                elif command == TXICommand.ISBUMPMAP:
                    self._txi.features.isbumpmap = bool(int(args))
                    self._empty = False
                elif command == TXICommand.ISDOUBLEBYTE:
                    self._txi.features.isdoublebyte = bool(int(args))
                    self._empty = False
                elif command == TXICommand.ISLIGHTMAP:
                    self._txi.features.islightmap = bool(int(args))
                    self._empty = False
                elif command == TXICommand.LOWERRIGHTCOORDS:
                    self._txi.features.lowerrightcoords = [[] for _ in range(int(args))]
                    mode = TXIReaderMode.LOWER_RIGHT_COORDS
                    cur_coords = 0
                    self._empty = False
                elif command == TXICommand.MAXSIZEHQ:
                    self._txi.features.maxSizeHQ = int(args)
                    self._empty = False
                elif command == TXICommand.MAXSIZELQ:
                    self._txi.features.maxSizeLQ = int(args)
                    self._empty = False
                elif command == TXICommand.MINSIZEHQ:
                    self._txi.features.minSizeHQ = int(args)
                    self._empty = False
                elif command == TXICommand.MINSIZELQ:
                    self._txi.features.minSizeLQ = int(args)
                    self._empty = False
                elif command == TXICommand.MIPMAP:
                    self._txi.features.mipmap = bool(int(args))
                    self._empty = False
                elif command == TXICommand.NUMCHARS:
                    self._txi.features.numchars = int(args)
                    self._empty = False
                elif command == TXICommand.NUMCHARSPERSHEET:
                    self._txi.features.numcharspersheet = int(args)
                    self._empty = False
                elif command == TXICommand.NUMX:
                    self._txi.features.numx = int(args)
                    self._empty = False
                elif command == TXICommand.NUMY:
                    self._txi.features.numy = int(args)
                    self._empty = False
                elif command == TXICommand.ONDEMAND:
                    self._txi.features.ondemand = bool(int(args))
                    self._empty = False
                elif command == TXICommand.PRIORITY:
                    self._txi.features.priority = int(args)
                    self._empty = False
                elif command == TXICommand.PROCEDURETYPE:
                    self._txi.features.proceduretype = args
                    self._empty = False
                elif command == TXICommand.ROWS:
                    self._txi.features.rows = int(args)
                    self._empty = False
                elif command == TXICommand.SPACINGB:
                    self._txi.features.spacingB = float(args)
                    self._empty = False
                elif command == TXICommand.SPACINGR:
                    self._txi.features.spacingR = float(args)
                    self._empty = False
                elif command == TXICommand.SPEED:
                    self._txi.features.speed = float(args)
                    self._empty = False
                elif command == TXICommand.TEMPORARY:
                    self._txi.features.temporary = bool(int(args))
                    self._empty = False
                elif command == TXICommand.TEXTUREWIDTH:
                    self._txi.features.texturewidth = int(args)
                    self._empty = False
                elif command == TXICommand.UNIQUE:
                    self._txi.features.unique = bool(int(args))
                    self._empty = False
                elif command == TXICommand.UPPERLEFTCOORDS:
                    self._txi.features.upperleftcoords = [[] for _ in range(int(args))]
                    mode = TXIReaderMode.UPPER_LEFT_COORDS
                    cur_coords = 0
                    self._empty = False
                elif command == TXICommand.WATERHEIGHT:
                    self._txi.features.waterheight = float(args)
                    self._empty = False
                elif command == TXICommand.WATERWIDTH:
                    self._txi.features.waterwidth = float(args)
                    self._empty = False
                elif command == TXICommand.XBOX_DOWNSAMPLE:
                    self._txi.features.xbox_downsample = bool(int(args))
                    self._empty = False
            except Exception as e:  # noqa: BLE001
                RobustLogger().warning(f"Invalid TXI line: '{line}'", exc_info=e)

        return self._txi


class TXIBinaryWriter(ResourceWriter):
    def __init__(self, txi: TXI, target: TARGET_TYPES):
        super().__init__(target)
        self._txi: TXI = txi

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        from pykotor.resource.formats.txi.txi_data import TXICommand

        lines: list[str] = []
        for attr, value in vars(self._txi.features).items():
            if not value:
                continue
            upper_attr = attr.upper()
            if upper_attr not in TXICommand.__members__:
                RobustLogger().error(f"Invalid TXI attribute '{attr}'")
                continue
            command = TXICommand[upper_attr]
            if isinstance(value, bool):
                lines.append(f"{command.value} {int(value)}")
            elif isinstance(value, (int, float)):
                lines.append(f"{command.value} {value}")
            elif isinstance(value, list):
                if attr in [
                    TXICommand.UPPERLEFTCOORDS.value.lower(),
                    TXICommand.LOWERRIGHTCOORDS.value.lower(),
                ]:
                    lines.append(command.value)
                    lines.extend(" ".join(map(str, coord)) for coord in value)
                else:
                    lines.append(f"{command.value} {' '.join(map(str, value))}")
            else:
                lines.append(f"{command.value} {value}")
        txi_string = "\n".join(lines)
        self._writer.write_string(txi_string)
