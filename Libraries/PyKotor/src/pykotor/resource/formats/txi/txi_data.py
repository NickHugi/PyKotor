# From https://nwn.wiki/display/NWN1/TXI#TXI-TextureRelatedFields
# From DarthParametric and Drazgar in the DeadlyStream Discord.
from __future__ import annotations

import math

from typing import ClassVar

from pykotor.resource.formats._base import ComparableMixin


class TXIBaseInformation(ComparableMixin):
    COMPARABLE_FIELDS = ("mipmap", "filter", "downsamplemin", "downsamplemax")
    """Fields used within all txi files."""

    def __init__(self):
        #  Mipmap and Filter settings (0/1) can apply different graphical "softening" on the fonts (not affecting spacing etc.). Don't use it though, in most case it would hurt your eyes.
        #  The engine has broken mip use implementation. It incorrectly mixes mip levels, even on objects filling the screen.
        self.mipmap: int = 0  # The mipmap 0 setting shouldn't be changed. That tells the engine to use mip 0, i.e. the highest resolution of the image
        self.filter: int = 0  # (???)
        self.downsamplemin: int = 0  # (???) (probably unsupported or broken related to above)
        self.downsamplemax: int = 0  # (???) (probably unsupported or broken related to above)

    def __eq__(self, other):
        if not isinstance(other, TXIBaseInformation):
            return NotImplemented
        return (
            self.mipmap == other.mipmap
            and self.filter == other.filter
            and self.downsamplemin == other.downsamplemin
            and self.downsamplemax == other.downsamplemax
        )

    def __hash__(self):
        return hash((self.mipmap, self.filter, self.downsamplemin, self.downsamplemax))


class TXIMaterialInformation(TXIBaseInformation):
    COMPARABLE_FIELDS = (
        *TXIBaseInformation.COMPARABLE_FIELDS,
        "bumpmaptexture",
        "bumpyshinytexture",
        "envmaptexture",
        "bumpreplacementtexture",
        "blending",
        "decal",
    )
    def __init__(self):
        super().__init__()
        self.bumpmaptexture: int = 0
        self.bumpyshinytexture: int = 0
        self.envmaptexture: int = 0
        self.bumpreplacementtexture: int = 0
        self.blending: int = 0
        self.decal: int = 0

    def __eq__(self, other):
        if not isinstance(other, TXIMaterialInformation):
            return NotImplemented
        return (
            super().__eq__(other)
            and self.bumpmaptexture == other.bumpmaptexture
            and self.bumpyshinytexture == other.bumpyshinytexture
            and self.envmaptexture == other.envmaptexture
            and self.bumpreplacementtexture == other.bumpreplacementtexture
            and self.blending == other.blending
            and self.decal == other.decal
        )

    def __hash__(self):
        return hash((
            super().__hash__(),
            self.bumpmaptexture,
            self.bumpyshinytexture,
            self.envmaptexture,
            self.bumpreplacementtexture,
            self.blending,
            self.decal
        ))


class TXITextureInformation(TXIBaseInformation):
    COMPARABLE_FIELDS = (
        *TXIBaseInformation.COMPARABLE_FIELDS,
        "proceduretype",
        "filerange",
        "defaultwidth",
        "defaultheight",
        "filter",
        "maptexelstopixels",
        "gamma",
        "isbumpmap",
        "clamp",
        "alphamean",
        "isdiffusebumpmap",
        "isspecularbumpmap",
        "bumpmapscaling",
        "specularcolor",
        "numx",
        "numy",
        "cube",
        "bumpintensity",
        "temporary",
        "useglobalalpha",
        "isenvironmentmapped",
        "pltreplacement",
    )
    def __init__(self):
        super().__init__()
        self.proceduretype: int = 0
        self.filerange: int = 0
        self.defaultwidth: int = 0
        self.defaultheight: int = 0
        self.filter: int = 0
        self.maptexelstopixels: int = 0
        self.gamma: int = 0
        self.isbumpmap: int = 0
        self.clamp: int = 0
        self.alphamean: int = 0
        self.isdiffusebumpmap: int = 0
        self.isspecularbumpmap: int = 0
        self.bumpmapscaling: int = 0
        self.specularcolor: int = 0
        self.numx: int = 0
        self.numy: int = 0
        self.cube: int = 0
        self.bumpintensity: int = 0
        self.temporary: int = 0
        self.useglobalalpha: int = 0
        self.isenvironmentmapped: int = 0
        self.pltreplacement: int = 0

    def __eq__(self, other):
        if not isinstance(other, TXITextureInformation):
            return NotImplemented
        return (
            super().__eq__(other)
            and self.proceduretype == other.proceduretype
            and self.filerange == other.filerange
            and self.defaultwidth == other.defaultwidth
            and self.defaultheight == other.defaultheight
            and self.filter == other.filter
            and self.maptexelstopixels == other.maptexelstopixels
            and self.gamma == other.gamma
            and self.isbumpmap == other.isbumpmap
            and self.clamp == other.clamp
            and self.alphamean == other.alphamean
            and self.isdiffusebumpmap == other.isdiffusebumpmap
            and self.isspecularbumpmap == other.isspecularbumpmap
            and self.bumpmapscaling == other.bumpmapscaling
            and self.specularcolor == other.specularcolor
            and self.numx == other.numx
            and self.numy == other.numy
            and self.cube == other.cube
            and self.bumpintensity == other.bumpintensity
            and self.temporary == other.temporary
            and self.useglobalalpha == other.useglobalalpha
            and self.isenvironmentmapped == other.isenvironmentmapped
            and self.pltreplacement == other.pltreplacement
        )

    def __hash__(self):
        return hash((
            super().__hash__(),
            self.proceduretype,
            self.filerange,
            self.defaultwidth,
            self.defaultheight,
            self.filter,
            self.maptexelstopixels,
            self.gamma,
            self.isbumpmap,
            self.clamp,
            self.alphamean,
            self.isdiffusebumpmap,
            self.isspecularbumpmap,
            self.bumpmapscaling,
            self.specularcolor,
            self.numx,
            self.numy,
            self.cube,
            self.bumpintensity,
            self.temporary,
            self.useglobalalpha,
            self.isenvironmentmapped,
            self.pltreplacement
        ))


class TXIFontInformation(TXIBaseInformation):
    DEFAULT_RESOLUTION: ClassVar[int] = 512
    FONT_TEXTURES: ClassVar[list[str]] = [  # TODO(th3w1zard1): figure out which ones the game actually uses.
        "fnt_galahad14",  # Main menu?
        "dialogfont10x10",
        "dialogfont10x10a",
        "dialogfont10x10b",
        "dialogfont12x16",
        "dialogfont16x16",
        "dialogfont16x16a",
        "dialogfont16x16a",
        "dialogfont16x16b",
        "dialogfont32x32",
        "fnt_console",  # 127 chars, also has a large horizontally-wide rectangle probably used as the consolebox display
        "fnt_credits",
        "fnt_creditsa",
        "fnt_creditsb",
        "fnt_d10x10b",
        "fnt_d16x16",
        "fnt_d16x16a",
        "fnt_d16x16b",
        "fnt_dialog16x16",
    ]

    TSL_ADDED_FONTS: ClassVar[list[str]] = [
        "dialogfont16x16b",
        "d2xfnt_d16x16b",
        "d2xfont16x16b",
        "d2xfont16x16b_ps",
        "d3xfnt_d16x16b",
        "d3xfont16x16b",
        "d3xfont16x16b_ps",
        "diafnt16x16b_ps",
    ]

    ASPYR_CONTROLLER_BUTTON_TEXTURES: ClassVar[list[str]] = [
        "cus_button_a",
        "cus_button_aps",
        "cus_button_b",
        "cus_button_bps",
        "cus_button_x",
        "cus_button_xps",
        "cus_button_y",
        "cus_button_yps",
    ]

    def __init__(self):
        super().__init__()
        # Actual fields
        self.numchars: int = 256  # Tested. Unsure if this is actually required, or if the game simply takes from the 'upperleftcoords' and 'lowerrightcoords' sizes.
        self.spacingR: float = 0  # Untested. Float between 0 and 1. According to research, should NEVER exceed the maximum of 0.002600
        self.spacingB: float = 0  # Confirmed. Float between 0 and 1. Spacing between each multiline string rendered ingame.
        self.caretindent: float = (
            -0.010000
        )  # Untested. Probably determines the accent information above the character. Probably negative since Y is inverted so this checks out.
        self.fontwidth: float = 1.000000  # Tested. Float between 0 and 1. Was told this actually stretches text down somehow. But in k1 tests, changing this does not yield any noticeable ingame result.  # noqa: E501

        # This could easily be used for DBCS (double byte encodings).
        # It may be unimplemented in KOTOR. Or hopefully, nobody's figured out how to use it.
        # Figuring this out would likely be the solution for supporting languages like Korean, Japanese, Chinese, and Vietnamese.
        # Otherwise a new engine, or implementing an overlay (like discord/steam/rivatuner's) into kotor to bypass kotor's bitmap fonts for displayed text.
        self.isdoublebyte: bool = False  # (???) Potentially for dbcs multi-byte encodings? Might not even be a bool.
        self.dbmapping: object = None  # (???) Potentially for dbcs multi-byte encodings?

        self.fontheight: float  # Tested. Float between 0 and 1.
        self.baselineheight: float  # Untested. Float between 0 and 1.
        self.texturewidth: float  # Tested. Float between 0 and 1. Actual displayed width of the texture, allows stretching/compressing along the X axis.

        self.upper_left_coords: list[tuple[float, float, int]] = []  # Confirmed. The top left coordinates for the character box the game draws. each float is 0 to 1. 3rd tuple int is always 0  # noqa: E501
        self.lower_right_coords: list[tuple[float, float, int]] = []  # Confirmed. The bottom right coordinates for the character box the game draws. each float is 0 to 1. 3rd tuple int is always 0  # noqa: E501

    COMPARABLE_FIELDS = (
        *TXIBaseInformation.COMPARABLE_FIELDS,
        "numchars",
        "spacingR",
        "spacingB",
        "caretindent",
        "fontwidth",
        "isdoublebyte",
        "dbmapping",
    )
    COMPARABLE_SEQUENCE_FIELDS = ("upper_left_coords", "lower_right_coords")

    def __hash__(self):
        return hash((
            super().__hash__(),
            self.numchars,
            self.spacingR,
            self.spacingB,
            self.caretindent,
            self.fontwidth,
            self.isdoublebyte,
            id(self.dbmapping),  # Use id for object comparison
            getattr(self, "fontheight", None),
            getattr(self, "baselineheight", None),
            getattr(self, "texturewidth", None),
            tuple(self.upper_left_coords),
            tuple(self.lower_right_coords)
        ))
        #
        # The 3rd int in the upperleftcoords and bottomright coords is unknown. It could be any of the following:
        #
        # Layer or Depth Information: In some graphic systems, a third coordinate can be used to represent the depth or
        # layer, especially in 3D rendering contexts. However, for 2D font rendering, this is less
        # likely unless there is some form of layering or depth effect involved.
        #
        # Reserved for Future Use or Extension: It's common in software development to include elements
        # in data structures that are reserved for potential future use. This allows for extending the
        # functionality without breaking existing formats or compatibility.
        #
        # Indicator or Flag: This integer could serve as a flag or an indicator for specific conditions or states.
        #
        # Alignment or Padding: In some data structures, additional elements
        # are included for alignment purposes, ensuring that the data aligns well with memory boundaries

    def __str__(self):
        # Format the coordinates (left 4 spaces are not required, but make formatting cleaner)
        ul_coords_str = "\n".join([f"    {x:.6f} {y:.6f} {not_z}" for x, y, not_z in self.upper_left_coords])
        lr_coords_str = "\n".join([f"    {x:.6f} {y:.6f} {not_z}" for x, y, not_z in self.lower_right_coords])

        return f"""
mipmap {self.mipmap}
filter {self.filter}
numchars {self.numchars}
fontheight {self.fontheight:.6f}
baselineheight {self.baselineheight:.6f}
texturewidth {self.texturewidth:.6f}
fontwidth {self.fontwidth:.6f}
spacingR {self.spacingR:.6f}
spacingB {self.spacingB:.6f}
caretindent {self.caretindent:.6f}
isdoublebyte {int(self.isdoublebyte)}
upperleftcoords {self.ul_coords_count}
{ul_coords_str}
lowerrightcoords {self.lr_coords_count}
{lr_coords_str}
"""

    @property
    def ul_coords_count(self) -> int:
        return len(self.upper_left_coords)

    @property
    def lr_coords_count(self) -> int:
        return len(self.upper_left_coords)

    def get_scaling_factor(self) -> float:
        return 2 ** (math.log2(self.DEFAULT_RESOLUTION) - 1)

    def coords_from_normalized(self, upper_left_coords, lower_right_coords, resolution):
        """Converts normalized coordinates to bounding boxes.

        Args:
        ----
            upper_left_coords: List of tuples containing normalized upper left coordinates of boxes
            lower_right_coords: List of tuples containing normalized lower right coordinates of boxes
            resolution: Tuple containing image width and height

        Returns:
        -------
            boxes: List of bounding boxes as lists of [x1,y1,x2,y2] coordinates

        Processing Logic:
        ----------------
            - Loops through upper_left_coords and lower_right_coords and zips them
            - Converts normalized coords to pixel coords using resolution
            - Appends pixel coords as a list representing a bounding box
            - Returns list of bounding boxes.
        """
        boxes = []
        for (ulx, uly, _), (lrx, lry, _) in zip(upper_left_coords, lower_right_coords):
            # Convert normalized coords back to pixel coords
            pixel_ulx = ulx * resolution[0]
            pixel_uly = (1 - uly) * resolution[1]  # Y is inverted
            pixel_lrx = lrx * resolution[0]
            pixel_lry = (1 - lry) * resolution[1]  # Y is inverted
            boxes.append([int(pixel_ulx), int(pixel_uly), int(pixel_lrx), int(pixel_lry)])
        return boxes

    def normalize_coords(
        self, boxes: list[tuple[float, float, float, float]], resolution: tuple[int, int]
    ) -> tuple[list[tuple[float, float, int]], list[tuple[float, float, int]]]:
        """Converts boxes to normalized coordinates.

        Args:
        ----
            boxes: list of bounding boxes as tuples of floats
            resolution: tuple of ints specifying image width and height

        Returns:
        -------
            tuple: tuple containing lists of normalized upper left and lower right box coordinates

        Processing Logic:
        ----------------
            - Loops through each bounding box
            - Extracts upper left and lower right coordinates from each box
            - Normalizes the coordinates by dividing by image width/height
            - Appends normalized upper left and lower right coords to separate lists
            - Returns a tuple of the two lists of normalized coordinates.
        """
        upper_left_coords: list[tuple[float, float, int]] = []
        lower_right_coords: list[tuple[float, float, int]] = []

        for box in boxes:
            ulx, uly, lrx, lry = box
            # Convert pixel coords to normalized coords
            norm_ulx = ulx / resolution[0]
            norm_uly = 1 - (uly / resolution[1])  # Y is inverted
            norm_lrx = lrx / resolution[0]
            norm_lry = 1 - (lry / resolution[1])  # Y is inverted
            upper_left_coords.append((norm_ulx, norm_uly, 0))
            lower_right_coords.append((norm_lrx, norm_lry, 0))

        return upper_left_coords, lower_right_coords

    def set_font_metrics(
        self,
        resolution: tuple[int, int],
        max_char_height: float,
        baseline_height: float,
        custom_scaling: float,
    ):
        self.texturewidth = 128 * custom_scaling / 25
        self.fontheight = 128 * custom_scaling * max_char_height / (25 * resolution[1])
        self.baselineheight = baseline_height / resolution[1]

        # self.texturewidth: float = self.numchars * custom_scaling / 50  # maybe?
        # self.fontheight: float = (self.numchars * custom_scaling * max_char_height) / (50 * resolution[1])  # maybe?

        # TODO(th3w1zard1): I'm pretty sure fontwidth could be calculated here too. During testing, it's been easier to leave that at 1.000000 so there's less variables to worry about.  # noqa: E501
        # We should figure out the relationship for proper readability. I think vanilla K1 defines texturewidth as 'resolution_x / 100'.
        # Also worth mentioning the above math doesn't even work if the resolution isn't a perfect square.
        # EDIT: Editing fontwidth yields no changes in K1. Might do something in K2.
        # self.fontwidth = self.texturewidth / self.fontheight * max_char_height / resolution[0]
        # assert int(round(self.fontwidth)) == 1
