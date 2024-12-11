from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from OpenGL.raw.GL.VERSION.GL_1_0 import GL_BACK, GL_DEPTH_TEST, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, glBlendFunc, glCullFace, glEnable
from loggerplus import RobustLogger
from typing_extensions import Literal

from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.gl.models.mdl import Model, Node
from pykotor.gl.models.predefined_mdl import (
    CAMERA_MDL_DATA,
    CAMERA_MDX_DATA,
    CURSOR_MDL_DATA,
    CURSOR_MDX_DATA,
    EMPTY_MDL_DATA,
    EMPTY_MDX_DATA,
    ENCOUNTER_MDL_DATA,
    ENCOUNTER_MDX_DATA,
    ENTRY_MDL_DATA,
    ENTRY_MDX_DATA,
    SOUND_MDL_DATA,
    SOUND_MDX_DATA,
    STORE_MDL_DATA,
    STORE_MDX_DATA,
    TRIGGER_MDL_DATA,
    TRIGGER_MDX_DATA,
    UNKNOWN_MDL_DATA,
    UNKNOWN_MDX_DATA,
    WAYPOINT_MDL_DATA,
    WAYPOINT_MDX_DATA,
)
from pykotor.gl.models.read_mdl import gl_load_stitched_model
from pykotor.gl.scene import Camera, RenderObject
from pykotor.gl.shader import Texture
from pykotor.resource.formats.lyt.lyt_data import LYT
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.generics.git import GIT, GITCreature, GITInstance
from pykotor.resource.generics.ifo import IFO
from pykotor.resource.type import ResourceType
from pykotor.tools import creature
from utility.common.geometry import Vector3
from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:

    from collections.abc import Callable

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.module import Module, ModulePieceResource, ModuleResource
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.gl.models.mdl import Model, Node
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.generics.git import GITCreature, GITInstance
    from pykotor.resource.generics.utc import UTC
    from utility.common.geometry import Vector3

T = TypeVar("T")
SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class SceneBase:
    SPECIAL_MODELS: ClassVar[list[str]] = ["waypoint", "store", "sound", "camera", "trigger", "encounter", "unknown"]

    def __init__(
        self,
        *,
        installation: Installation | None = None,
        module: Module | None = None,
    ):
        module_id_part: str = "" if module is None else f" from module '{module.root()}'"
        RobustLogger().info(f"Start initialize Scene{module_id_part}")

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_BACK)

        self.installation: Installation | None = installation
        if installation is not None:
            self.set_installation(installation)
        self.textures: CaseInsensitiveDict[Texture] = CaseInsensitiveDict()
        self.textures["NULL"] = Texture.from_color()
        self.models: CaseInsensitiveDict[Model] = CaseInsensitiveDict()

        self.cursor: RenderObject = RenderObject("cursor")
        self.objects: dict[Any, RenderObject] = {}

        self.selection: list[RenderObject] = []
        self._module: Module | None = module
        self.camera: Camera = Camera()
        self.cursor: RenderObject = RenderObject("cursor")

        self.git: GIT | None = None
        self.layout: LYT | None = None
        self.clear_cache_buffer: list[ResourceIdentifier] = []

        self.hide_creatures: bool = False
        self.hide_placeables: bool = False
        self.hide_doors: bool = False
        self.hide_triggers: bool = False
        self.hide_encounters: bool = False
        self.hide_waypoints: bool = False
        self.hide_sounds: bool = False
        self.hide_stores: bool = False
        self.hide_cameras: bool = False
        self.hide_sound_boundaries: bool = True
        self.hide_trigger_boundaries: bool = True
        self.hide_encounter_boundaries: bool = True
        self.backface_culling: bool = True
        self.use_lightmap: bool = True
        self.show_cursor: bool = True
        module_id_part = "" if module is None else f" from module '{module.root()}'"
        RobustLogger().debug(f"Completed pre-initialize Scene{module_id_part}")

    def set_lyt(self, lyt: LYT):
        self.layout = lyt

    def set_installation(
        self,
        installation: Installation,
    ):
        def load_2da(name: str) -> TwoDA:
            resource: ResourceResult | None = installation.resource(name, ResourceType.TwoDA, SEARCH_ORDER_2DA)
            if resource is None:
                RobustLogger().warning(f"Could not load {name}.2da, this means its models will not be rendered")
                return TwoDA()
            return read_2da(resource.data)

        self.table_doors = load_2da("genericdoors")
        self.table_placeables = load_2da("placeables")
        self.table_creatures = load_2da("appearance")
        self.table_heads = load_2da("heads")
        self.table_baseitems = load_2da("baseitems")

    def get_creature_render_object(  # noqa: C901
        self,
        instance: GITCreature | None = None,
        utc: UTC | None = None,
    ) -> RenderObject:
        assert self.installation is not None
        try:
            if instance is not None and utc is None:
                utc = self._resource_from_gitinstance(instance, self.module.creature)
            if utc is None:
                if instance is not None:
                    RobustLogger().warning(f"Could not get UTC for GITCreature instance '{instance.identifier()}', not found in mod/override.")
                else:
                    RobustLogger().warning("Could not get UTC for GITCreature, no instance provided.")
                return RenderObject("unknown", data=instance)

            head_obj: RenderObject | None = None
            mask_hook = None

            body_model, body_texture = creature.get_body_model(
                utc,
                self.installation,
                appearance=self.table_creatures,
                baseitems=self.table_baseitems,
            )
            if not body_model or not body_model.strip():
                raise ValueError("creature.get_body_model failed to return a valid body_model resref str.")  # noqa: TRY301
            head_model, head_texture = creature.get_head_model(
                utc,
                self.installation,
                appearance=self.table_creatures,
                heads=self.table_heads,
            )
            rhand_model, lhand_model = creature.get_weapon_models(
                utc,
                self.installation,
                appearance=self.table_creatures,
                baseitems=self.table_baseitems,
            )
            mask_model = creature.get_mask_model(
                utc,
                self.installation,
            )

            obj = RenderObject(body_model, data=instance, override_texture=body_texture)

            head_hook: Node | None = self.model(body_model).find("headhook")
            if head_model and head_hook:
                head_obj = RenderObject(head_model, override_texture=head_texture)
                head_obj.set_transform(head_hook.global_transform())
                obj.children.append(head_obj)

            rhand_hook: Node | None = self.model(body_model).find("rhand")
            if rhand_model and rhand_hook:
                rhand_obj = RenderObject(rhand_model)
                rhand_obj.set_transform(rhand_hook.global_transform())
                obj.children.append(rhand_obj)
            lhand_hook: Node | None = self.model(body_model).find("lhand")
            if lhand_model and lhand_hook:
                lhand_obj = RenderObject(lhand_model)
                lhand_obj.set_transform(lhand_hook.global_transform())
                obj.children.append(lhand_obj)
            if head_hook is None:
                mask_hook: Node | None = self.model(body_model).find("gogglehook")
            elif head_model:
                mask_hook = self.model(head_model).find("gogglehook")
            if mask_model and mask_hook:
                mask_obj = RenderObject(mask_model)
                mask_obj.set_transform(mask_hook.global_transform())
                if head_hook is None:
                    obj.children.append(mask_obj)
                elif head_obj is not None:
                    head_obj.children.append(mask_obj)

        except Exception:  # noqa: BLE001
            RobustLogger().exception("Exception occurred getting the creature render object.")
            # If failed to load creature models, use the unknown model instead
            obj = RenderObject("unknown", data=instance)

        return obj

    @property
    def module(self) -> Module:
        if not self._module:
            raise RuntimeError("Module must be defined before a Scene can be rendered.")
        return self._module

    @module.setter
    def module(self, value: Module):
        self._module = value

    def _get_git(self) -> GIT:
        module_resource_git: ModuleResource[GIT] | None = self.module.git()
        result: GIT | None = self._resource_from_module(module_resource_git, "' is missing a GIT.")
        if result is None:
            RobustLogger().warning(f"Module '{self.module.root()}' is missing a GIT.")
            return GIT()
        return result

    def _get_lyt(self) -> LYT:
        layout_module_resource: ModuleResource[LYT] | None = self.module.layout()
        result: LYT | None = self._resource_from_module(layout_module_resource, "' is missing a LYT.")
        if result is None:
            RobustLogger().warning(f"Module '{self.module.root()}' is missing a LYT.")
            return LYT()
        return result

    def _get_ifo(self) -> IFO:
        info_module_resource: ModuleResource[IFO] | None = self.module.info()
        result: IFO | None = self._resource_from_module(info_module_resource, "' is missing an IFO.")
        if result is None:
            RobustLogger().warning(f"Module '{self.module.root()}' is missing an IFO.")
            return IFO()
        return result

    def _resource_from_module(
        self,
        module_res: ModuleResource[T] | None,
        errpart: str,
    ) -> T | None:
        if module_res is None:
            RobustLogger().error(f"Cannot render a frame in Scene when this module '{self.module.root()}{errpart}")
            return None
        resource: T | None = module_res.resource()
        if resource is None:
            RobustLogger().error(f"No locations found for '{module_res.identifier()}', needed to render a Scene for module '{self.module.root()}'")
            return None
        return resource

    def _resource_from_gitinstance(
        self,
        instance: GITInstance,
        lookup_func: Callable[..., ModuleResource[T] | None],
    ) -> T | None:
        resource: ModuleResource[T] | None = lookup_func(str(instance.resref))
        if resource is None:
            RobustLogger().error(f"The module '{self.module.root()}' does not store '{instance.identifier()}' needed to render a Scene.")
            return None
        resource_data: T | None = resource.resource()
        if resource_data is None:
            RobustLogger().error(f"No locations found for '{resource.identifier()}' needed by module '{self.module.root()}'")
            return None
        return resource_data

    def jump_to_entry_location(self):
        if self._module is None:
            self.camera.x = 0
            self.camera.y = 0
            self.camera.z = 0
        else:
            point: Vector3 = self._get_ifo().entry_position
            self.camera.x = point.x
            self.camera.y = point.y
            self.camera.z = point.z + 1.8

    def texture(
        self,
        name: str,
        *,
        lightmap: bool = False,
    ) -> Texture:
        if name in self.textures:
            return self.textures[name]
        type_name: Literal["lightmap", "texture"] = "lightmap" if lightmap else "texture"
        tpc: TPC | None = None
        try:
            # Check the textures linked to the module first
            if self._module is not None:
                RobustLogger().debug(f"Locating {type_name} '{name}' in module '{self.module.root()}'")
                module_tex: ModuleResource[TPC] | None = self.module.texture(name)
                if module_tex is not None:
                    RobustLogger().debug(f"Loading {type_name} '{name}' from module '{self.module.root()}'")
                    tpc = module_tex.resource()

            # Otherwise just search through all relevant game files
            if tpc is None and self.installation is not None:
                RobustLogger().debug(f"Locating and loading {type_name} '{name}' from override/bifs/texturepacks...")
                tpc = self.installation.texture(name, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN])
            if tpc is None:
                RobustLogger().warning(f"MISSING {type_name.upper()}: '{name}'")
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Could not load {type_name} '{name}'.")

        blank: Texture = Texture.from_color(0, 0, 0) if lightmap else Texture.from_color(255, 0, 255)
        self.textures[name] = blank if tpc is None else Texture.from_tpc(tpc)
        return self.textures[name]

    def model(  # noqa: C901, PLR0912
        self,
        name: str,
    ) -> Model:
        mdl_data: bytes = EMPTY_MDL_DATA
        mdx_data: bytes = EMPTY_MDX_DATA

        if name not in self.models:
            if name == "waypoint":
                mdl_data = WAYPOINT_MDL_DATA
                mdx_data = WAYPOINT_MDX_DATA
            elif name == "sound":
                mdl_data = SOUND_MDL_DATA
                mdx_data = SOUND_MDX_DATA
            elif name == "store":
                mdl_data = STORE_MDL_DATA
                mdx_data = STORE_MDX_DATA
            elif name == "entry":
                mdl_data = ENTRY_MDL_DATA
                mdx_data = ENTRY_MDX_DATA
            elif name == "encounter":
                mdl_data = ENCOUNTER_MDL_DATA
                mdx_data = ENCOUNTER_MDX_DATA
            elif name == "trigger":
                mdl_data = TRIGGER_MDL_DATA
                mdx_data = TRIGGER_MDX_DATA
            elif name == "camera":
                mdl_data = CAMERA_MDL_DATA
                mdx_data = CAMERA_MDX_DATA
            elif name == "empty":
                mdl_data = EMPTY_MDL_DATA
                mdx_data = EMPTY_MDX_DATA
            elif name == "cursor":
                mdl_data = CURSOR_MDL_DATA
                mdx_data = CURSOR_MDX_DATA
            elif name == "unknown":
                mdl_data, mdx_data = UNKNOWN_MDL_DATA, UNKNOWN_MDX_DATA
            elif self.installation is not None:
                capsules: list[ModulePieceResource] = [] if self._module is None else self.module.capsules()
                mdl_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=capsules)
                mdx_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=capsules)
                if mdl_search is not None and mdx_search is not None:
                    mdl_data = mdl_search.data
                    mdx_data = mdx_search.data

            try:
                mdl_reader: BinaryReader = BinaryReader.from_bytes(mdl_data, 12)
                mdx_reader: BinaryReader = BinaryReader.from_bytes(mdx_data)
                model: Model = gl_load_stitched_model(self, mdl_reader, mdx_reader)  # pyright: ignore[reportArgumentType]
            except Exception:  # noqa: BLE001
                RobustLogger().warning(f"Could not load model '{name}'.")
                model = gl_load_stitched_model(
                    self,  # pyright: ignore[reportArgumentType]
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )

            self.models[name] = model
        return self.models[name]