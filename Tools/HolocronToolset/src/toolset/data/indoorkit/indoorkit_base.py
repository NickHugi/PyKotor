from __future__ import annotations

from typing import TYPE_CHECKING

from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:
    from pathlib import Path

    from qtpy.QtGui import QImage

    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.utd import UTD
    from utility.common.geometry import Vector3


class Kit:
    def __init__(
        self,
        name: str,
    ):
        self.name: str = name
        self.always: dict[Path, bytes] = {}
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.skyboxes: CaseInsensitiveDict[MDLMDXTuple] = CaseInsensitiveDict()
        self.doors: list[KitDoor] = []
        self.components: list[KitComponent] = []
        self.name: str = name
        self.components: list[KitComponent] = []
        self.doors: list[KitDoor] = []
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.always: dict[Path, bytes] = {}
        self.side_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.top_padding: dict[int, dict[int, MDLMDXTuple]] = {}


class KitComponentHook:
    def __init__(
        self,
        position: Vector3,
        rotation: float,
        edge: str,
        door: KitDoor,
    ):
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.edge: str = edge
        self.door: KitDoor = door


class KitDoor:
    def __init__(
        self,
        utd_k1: UTD,
        utd_k2: UTD,
        width: float,
        height: float,
    ):
        self.utd_k1: UTD = utd_k1
        self.utd_k2: UTD = utd_k2
        self.width: float = width
        self.height: float = height


class MDLMDXTuple:
    def __init__(
        self,
        mdl: bytes,
        mdx: bytes,
    ):
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx


class KitComponent:
    def __init__(
        self,
        kit: Kit,
        name: str,
        image: QImage,
        bwm: BWM,
        mdl: bytes,
        mdx: bytes,
    ):
        self.kit: Kit = kit
        self.image: QImage = image
        self.name: str = name
        self.hooks: list[KitComponentHook] = []

        self.bwm: BWM = bwm
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx
