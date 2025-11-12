from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from OpenGL.raw.GL.VERSION.GL_1_0 import GL_BACK, GL_DEPTH_TEST, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, glBlendFunc, glCullFace, glEnable
from loggerplus import RobustLogger
from typing_extensions import Literal

from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
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
from pykotor.gl.scene.async_loader import AsyncResourceLoader, create_model_from_intermediate, create_texture_from_intermediate
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


# DO NOT USE INSTALLATION IN CHILD PROCESSES
# Both IO AND parsing should be in child process(es). ONE PROCESS PER FILE!!


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

        self.git: GIT | None = None
        self.layout: LYT | None = None
        self.clear_cache_buffer: list[ResourceIdentifier] = []
        
        # Async resource loading
        # Main thread: Use Installation to RESOLVE file locations ONLY (no Installation in child!)
        # Child process: Do raw file IO + parsing (one process per file)
        
        def _resolve_texture_location(name: str) -> tuple[str, int, int] | None:
            """Resolve texture file location in main thread using Installation ONLY.
            
            Returns (filepath, offset, size) or None.
            """
            if self.installation is None:
                return None
            
            # Installation.location() returns LocationResult which has offset/size as fields
            # Signature: location(resname: str, restype: ResourceType, order: list[SearchLocation] | None = None, ...)
            locations = self.installation.location(
                name,
                ResourceType.TPC,
                [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN],
            )
            if locations:
                loc = locations[0]
                # LocationResult has: filepath (Path field), offset (int field), size (int field)
                return (str(loc.filepath), loc.offset, loc.size)
            return None
        
        def _resolve_model_location(name: str) -> tuple[tuple[str, int, int] | None, tuple[str, int, int] | None]:
            """Resolve model file locations in main thread using Installation ONLY.
            
            Returns ((mdl_path, offset, size), (mdx_path, offset, size)) or (None, None).
            """
            if self.installation is None:
                return (None, None)
            
            search_locs = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
            # ModulePieceResource extends Capsule, but list types are invariant - pass None if empty
            module_capsules = self._module.capsules() if self._module is not None else []
            capsules: list[Capsule] = list(module_capsules) if module_capsules else []
            
            # Installation.location() returns list[LocationResult] with offset/size fields
            # Signature: location(resname: str, restype: ResourceType, order: list[SearchLocation] | None = None, ...)
            mdl_locs = self.installation.location(name, ResourceType.MDL, search_locs, capsules=capsules)
            mdx_locs = self.installation.location(name, ResourceType.MDX, search_locs, capsules=capsules)
            
            mdl_loc = None
            mdx_loc = None
            
            if mdl_locs:
                loc = mdl_locs[0]
                mdl_loc = (str(loc.filepath), loc.offset, loc.size)
            
            if mdx_locs:
                loc = mdx_locs[0]
                mdx_loc = (str(loc.filepath), loc.offset, loc.size)
            
            return (mdl_loc, mdx_loc)
        
        self.async_loader: AsyncResourceLoader = AsyncResourceLoader(
            texture_location_resolver=_resolve_texture_location,
            model_location_resolver=_resolve_model_location,
        )
        self.async_loader.start()
        self._pending_texture_futures: dict[str, Any] = {}  # name -> Future
        self._pending_model_futures: dict[str, Any] = {}  # name -> Future

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
    
    def __del__(self):
        """Cleanup async resources when scene is destroyed."""
        try:
            if hasattr(self, "async_loader") and self.async_loader is not None:
                self.async_loader.shutdown(wait=False)
                RobustLogger().debug("Scene cleanup: shutdown async loader")
        except Exception:  # noqa: BLE001, S110
            pass  # Don't raise exceptions in __del__

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
    
    def invalidate_cache(self):
        """Invalidate resource caches and cancel pending async operations."""
        # Cancel pending operations
        for future in self._pending_texture_futures.values():
            future.cancel()
        for future in self._pending_model_futures.values():
            future.cancel()
        
        self._pending_texture_futures.clear()
        self._pending_model_futures.clear()
        
        # Clear caches (but keep predefined models/textures)
        predefined_models = {"waypoint", "sound", "store", "entry", "encounter", "trigger", "camera", "empty", "cursor", "unknown"}
        self.models = CaseInsensitiveDict({k: v for k, v in self.models.items() if k in predefined_models})
        self.textures = CaseInsensitiveDict({"NULL": self.textures.get("NULL", Texture.from_color())})
        
        RobustLogger().debug("Invalidated resource cache")
    
    def poll_async_resources(self):
        """Poll for completed async resource loading and create OpenGL objects.
        
        MUST be called from main thread with active OpenGL context.
        This is non-blocking and processes only completed futures.
        """
        # Debug: Log polling status
        if self._pending_texture_futures or self._pending_model_futures:
            RobustLogger().debug(f"Polling async resources: {len(self._pending_texture_futures)} textures, {len(self._pending_model_futures)} models pending")
        
        # Check completed texture futures
        completed_textures: list[str] = []
        for name, future in self._pending_texture_futures.items():
            if future.done():
                try:
                    resource_name, intermediate, error = future.result()
                    if error:
                        RobustLogger().warning(f"Async texture load FAILED for '{resource_name}': {error}")
                        self.textures[resource_name] = Texture.from_color(255, 0, 255)  # Magenta placeholder for failures
                    elif intermediate:
                        # Success! Replace the gray placeholder with the real texture
                        self.textures[resource_name] = create_texture_from_intermediate(intermediate)
                        RobustLogger().info(f"✓ Async loaded texture SUCCESS: {resource_name} (width={intermediate.width}, height={intermediate.height})")
                    else:
                        RobustLogger().warning(f"Async texture load returned no data and no error for '{resource_name}'")
                        self.textures[resource_name] = Texture.from_color(255, 0, 255)  # Magenta for missing data
                    completed_textures.append(name)
                except Exception:  # noqa: BLE001
                    RobustLogger().exception(f"Error processing completed texture future for '{name}'")
                    self.textures[name] = Texture.from_color(255, 0, 255)
                    completed_textures.append(name)
        
        for name in completed_textures:
            del self._pending_texture_futures[name]
        
        # Check completed model futures
        completed_models: list[str] = []
        for name, future in self._pending_model_futures.items():
            if future.done():
                try:
                    resource_name, intermediate, error = future.result()
                    if error:
                        RobustLogger().warning(f"Async model load failed for '{resource_name}': {error}")
                        # Load empty model as fallback
                        self.models[resource_name] = gl_load_stitched_model(
                            self,  # pyright: ignore[reportArgumentType]
                            BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                            BinaryReader.from_bytes(EMPTY_MDX_DATA),
                        )
                    elif intermediate:
                        self.models[resource_name] = create_model_from_intermediate(self, intermediate)
                        RobustLogger().info(f"✓ Async loaded model: {resource_name}")
                    else:
                        RobustLogger().warning(f"Async model load returned no data and no error for '{resource_name}'")
                    completed_models.append(name)
                except Exception:  # noqa: BLE001
                    RobustLogger().exception(f"Error processing completed model future for '{name}'")
                    self.models[name] = gl_load_stitched_model(
                        self,  # pyright: ignore[reportArgumentType]
                        BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                        BinaryReader.from_bytes(EMPTY_MDX_DATA),
                    )
                    completed_models.append(name)
        
        for name in completed_models:
            del self._pending_model_futures[name]

    def texture(
        self,
        name: str,
        *,
        lightmap: bool = False,
    ) -> Texture:
        # Already cached?
        if name in self.textures:
            return self.textures[name]
        
        # Already loading? Return cached placeholder
        if name in self._pending_texture_futures:
            # Texture is loading, return cached placeholder if it exists
            if name in self.textures:
                return self.textures[name]
            # Shouldn't happen but create placeholder if missing
            placeholder = Texture.from_color(128, 128, 128) if lightmap else Texture.from_color(128, 128, 128)
            self.textures[name] = placeholder
            return placeholder
        
        # Start async loading if location resolver available
        if self.async_loader.texture_location_resolver is not None:
            RobustLogger().info(f"→ Starting async load for texture: {name}")
            # Create and cache placeholder immediately - will be replaced when loaded
            placeholder = Texture.from_color(128, 128, 128) if lightmap else Texture.from_color(128, 128, 128)
            self.textures[name] = placeholder
            future = self.async_loader.load_texture_async(name)
            self._pending_texture_futures[name] = future
            RobustLogger().debug(f"Started async loading for texture: {name}, future: {future}")
            return placeholder
        
        # Fallback to synchronous loading (e.g., if process pools unavailable)
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
        # Already cached?
        if name in self.models:
            return self.models[name]
        
        # Special/predefined models - load synchronously
        predefined_models = {
            "waypoint": (WAYPOINT_MDL_DATA, WAYPOINT_MDX_DATA),
            "sound": (SOUND_MDL_DATA, SOUND_MDX_DATA),
            "store": (STORE_MDL_DATA, STORE_MDX_DATA),
            "entry": (ENTRY_MDL_DATA, ENTRY_MDX_DATA),
            "encounter": (ENCOUNTER_MDL_DATA, ENCOUNTER_MDX_DATA),
            "trigger": (TRIGGER_MDL_DATA, TRIGGER_MDX_DATA),
            "camera": (CAMERA_MDL_DATA, CAMERA_MDX_DATA),
            "empty": (EMPTY_MDL_DATA, EMPTY_MDX_DATA),
            "cursor": (CURSOR_MDL_DATA, CURSOR_MDX_DATA),
            "unknown": (UNKNOWN_MDL_DATA, UNKNOWN_MDX_DATA),
        }
        
        if name in predefined_models:
            mdl_data, mdx_data = predefined_models[name]
            try:
                mdl_reader: BinaryReader = BinaryReader.from_bytes(mdl_data, 12)
                mdx_reader: BinaryReader = BinaryReader.from_bytes(mdx_data)
                model: Model = gl_load_stitched_model(self, mdl_reader, mdx_reader)  # pyright: ignore[reportArgumentType]
                self.models[name] = model
                return model
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Could not load predefined model '{name}'.")
                # Fall through to empty model
        
        # Already loading?
        if name in self._pending_model_futures:
            # Return empty model placeholder while loading
            if "empty" not in self.models:
                empty_model = gl_load_stitched_model(
                    self,  # pyright: ignore[reportArgumentType]
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )
                self.models["empty"] = empty_model
            return self.models["empty"]
        
        # Start async loading if location resolver available
        if self.async_loader.model_location_resolver is not None:
            RobustLogger().info(f"→ Starting async load for model: {name}")
            future = self.async_loader.load_model_async(name)
            self._pending_model_futures[name] = future
            RobustLogger().debug(f"Started async loading for model: {name}, future: {future}")
            # Return empty model immediately as placeholder
            if "empty" not in self.models:
                empty_model = gl_load_stitched_model(
                    self,  # pyright: ignore[reportArgumentType]
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )
                self.models["empty"] = empty_model
            return self.models["empty"]
        
        # Fallback to synchronous loading
        fallback_mdl_data: bytes = EMPTY_MDL_DATA
        fallback_mdx_data: bytes = EMPTY_MDX_DATA
        
        if self.installation is not None:
            capsules: list[ModulePieceResource] = [] if self._module is None else self.module.capsules()
            mdl_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=capsules)
            mdx_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=capsules)
            if mdl_search is not None and mdx_search is not None:
                fallback_mdl_data = mdl_search.data
                fallback_mdx_data = mdx_search.data

        try:
            mdl_reader = BinaryReader.from_bytes(fallback_mdl_data, 12)
            mdx_reader = BinaryReader.from_bytes(fallback_mdx_data)
            model = gl_load_stitched_model(self, mdl_reader, mdx_reader)  # pyright: ignore[reportArgumentType]
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Could not load model '{name}'.")
            model = gl_load_stitched_model(
                self,  # pyright: ignore[reportArgumentType]
                BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                BinaryReader.from_bytes(EMPTY_MDX_DATA),
            )

        self.models[name] = model
        return model
