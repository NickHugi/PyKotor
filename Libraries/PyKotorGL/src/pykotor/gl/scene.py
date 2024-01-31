from __future__ import annotations

import math
from copy import copy
from typing import TYPE_CHECKING, Any, Callable, ClassVar

import glm
from glm import mat4, quat, vec3, vec4
from OpenGL.GL import glReadPixels
from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
from OpenGL.raw.GL.VERSION.GL_1_0 import (
    GL_BACK,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_TEST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    glBlendFunc,
    glClear,
    glClearColor,
    glCullFace,
    glDisable,
    glEnable,
)
from OpenGL.raw.GL.VERSION.GL_1_2 import GL_BGRA, GL_UNSIGNED_INT_8_8_8_8
from pykotor.common.geometry import Vector3
from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.gl.models.mdl import Boundary, Cube, Empty, Model
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
from pykotor.gl.shader import (
    KOTOR_FSHADER,
    KOTOR_VSHADER,
    PICKER_FSHADER,
    PICKER_VSHADER,
    PLAIN_FSHADER,
    PLAIN_VSHADER,
    Shader,
    Texture,
)
from pykotor.resource.formats.lyt import LYT, LYTRoom
from pykotor.resource.formats.tpc import TPC
from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.generics.git import (
    GIT,
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITInstance,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
)
from pykotor.resource.generics.uts import UTS
from pykotor.resource.type import ResourceType
from pykotor.tools import creature
from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.capsule import Capsule
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.resource.generics.utc import UTC
    from pykotor.resource.generics.utd import UTD
    from pykotor.resource.generics.utp import UTP
    from typing_extensions import Literal

SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER: list[SearchLocation] = [SearchLocation.CUSTOM_MODULES, SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class Scene:
    SPECIAL_MODELS: ClassVar[list[str]] = ["waypoint", "store", "sound", "camera", "trigger", "encounter", "unknown"]

    def __init__(self, *, installation: Installation | None = None, module: Module | None = None):
        """Initializes the renderer.

        Args:
        ----
            installation: Installation: The installation to load resources from
            module: Module: The active module

        Processing Logic:
        ----------------
            - Initializes OpenGL settings
            - Sets up default textures, shaders, camera
            - Loads 2DA tables from installation
            - Hides certain object types by default
            - Sets other renderer options.
        """
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_BACK)

        self.installation: Installation | None = installation
        self.textures: CaseInsensitiveDict[Texture] = CaseInsensitiveDict()
        self.models: CaseInsensitiveDict[Model] = CaseInsensitiveDict()
        self.objects: dict[Any, RenderObject] = {}
        self.selection: list[RenderObject] = []
        self.module: Module | None = module
        self.camera: Camera = Camera()
        self.cursor: RenderObject = RenderObject("cursor")

        self.textures["NULL"] = Texture.from_color()

        self.git: GIT | None = None
        self.layout: LYT | None = None
        self.clearCacheBuffer: list[ResourceIdentifier] = []

        self.picker_shader: Shader = Shader(PICKER_VSHADER, PICKER_FSHADER)
        self.plain_shader: Shader = Shader(PLAIN_VSHADER, PLAIN_FSHADER)
        self.shader: Shader = Shader(KOTOR_VSHADER, KOTOR_FSHADER)

        self.jump_to_entry_location()

        self.table_doors: TwoDA = TwoDA()
        self.table_placeables: TwoDA = TwoDA()
        self.table_creatures: TwoDA = TwoDA()
        self.table_heads: TwoDA = TwoDA()
        self.table_baseitems: TwoDA = TwoDA()
        if installation is not None:
            self.setInstallation(installation)

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

    def setInstallation(self, installation: Installation):
        self.table_doors = read_2da(installation.resource("genericdoors", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_placeables = read_2da(installation.resource("placeables", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_creatures = read_2da(installation.resource("appearance", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_heads = read_2da(installation.resource("heads", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_baseitems = read_2da(installation.resource("baseitems", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)

    def getCreatureRenderObject(self, instance: GITCreature, utc: UTC | None = None) -> RenderObject:
        """Generates a render object for a creature instance.

        Args:
        ----
            instance: {Creature instance}: Creature instance to generate render object for
            utc: {Optional timestamp}: Timestamp to use for generation or current time if None

        Returns:
        -------
            RenderObject: Render object representing the creature

        Processing Logic:
        ----------------
            - Gets body, head, weapon and mask models/textures based on creature appearance
            - Creates base render object and attaches head, hands and mask sub-objects
            - Catches exceptions and returns default "unknown" render object if model loading fails.
        """
        try:
            if utc is None:
                utc = self.module.creature(str(instance.resref)).resource()

            head_obj: RenderObject | None = None
            mask_hook = None

            body_model, body_texture = creature.get_body_model(
                utc,
                self.installation,
                appearance=self.table_creatures,
                baseitems=self.table_baseitems,
            )
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

            head_hook = self.model(body_model).find("headhook")
            if head_model and head_hook:
                head_obj = RenderObject(head_model, override_texture=head_texture)
                head_obj.set_transform(head_hook.global_transform())
                obj.children.append(head_obj)

            rhand_hook = self.model(body_model).find("rhand")
            if rhand_model and rhand_hook:
                self._transform_hand(rhand_model, rhand_hook, obj)
            lhand_hook = self.model(body_model).find("lhand")
            if lhand_model and lhand_hook:
                self._transform_hand(lhand_model, lhand_hook, obj)
            if head_hook is None:
                mask_hook = self.model(body_model).find("gogglehook")
            elif head_model:
                mask_hook = self.model(head_model).find("gogglehook")
            if mask_model and mask_hook:
                mask_obj = RenderObject(mask_model)
                mask_obj.set_transform(mask_hook.global_transform())
                if head_hook is None:
                    obj.children.append(mask_obj)
                elif head_obj is not None:
                    head_obj.children.append(mask_obj)

        except Exception as e:
            print(format_exception_with_variables(e))
            # If failed to load creature models, use the unknown model instead
            obj = RenderObject("unknown", data=instance)

        return obj

    def _transform_hand(self, arg0, arg1, obj):
        rhand_obj = RenderObject(arg0)
        rhand_obj.set_transform(arg1.global_transform())
        obj.children.append(rhand_obj)

    def buildCache(self, clear_cache: bool = False):
        """Builds and caches game objects from the module.

        Args:
        ----
            clear_cache (bool): Whether to clear the existing cache

        Processing Logic:
        ----------------
            - Clear existing cache if clear_cache is True
            - Delete objects matching identifiers in clearCacheBuffer
            - Retrieve/update game objects from module
            - Add/update objects in cache..
        """
        if self.module is None:
            return

        if clear_cache:
            self.objects = {}

        for identifier in self.clearCacheBuffer:
            for git_creature in copy(self.git.creatures):
                if identifier.resname == git_creature.resref and identifier.restype == ResourceType.UTC:
                    del self.objects[git_creature]
            for placeable in copy(self.git.placeables):
                if identifier.resname == placeable.resref and identifier.restype == ResourceType.UTP:
                    del self.objects[placeable]
            for door in copy(self.git.doors):
                if door.resref == identifier.resname and identifier.restype == ResourceType.UTD:
                    del self.objects[door]
            if identifier.restype in (ResourceType.TPC, ResourceType.TGA):
                del self.textures[identifier.resname]
            if identifier.restype in (ResourceType.MDL, ResourceType.MDX):
                del self.models[identifier.resname]
            if identifier.restype == ResourceType.GIT:
                for instance in self.git.instances():
                    del self.objects[instance]
                self.git = self.module.git().resource()
            if identifier.restype == ResourceType.LYT:
                for room in self.layout.rooms:
                    del self.objects[room]
                self.layout = self.module.layout().resource()
        self.clearCacheBuffer = []

        if self.git is None:
            self.git = self.module.git().resource()

        if self.layout is None:
            self.layout = self.module.layout().resource()

        for room in self.layout.rooms:
            if room not in self.objects:
                position = vec3(room.position.x, room.position.y, room.position.z)
                self.objects[room] = RenderObject(room.model, position, data=room)

        for door in self.git.doors:
            if door not in self.objects:
                try:
                    utd: UTD | None = self.module.door(str(door.resref)).resource()
                    model_name = self.table_doors.get_row(utd.appearance_id).get_string("modelname")
                except Exception as e:
                    print(format_exception_with_variables(e))
                    # If failed to load creature models, use an empty model instead
                    model_name = "unknown"

                self.objects[door] = RenderObject(model_name, vec3(), vec3(), data=door)

            self.objects[door].set_position(door.position.x, door.position.y, door.position.z)
            self.objects[door].set_rotation(0, 0, door.bearing)

        for placeable in self.git.placeables:
            if placeable not in self.objects:
                try:
                    utp: UTP | None = self.module.placeable(str(placeable.resref)).resource()
                    model_name: str = self.table_placeables.get_row(utp.appearance_id).get_string("modelname")
                except Exception as e:
                    print(format_exception_with_variables(e))
                    # If failed to load creature models, use an empty model instead
                    model_name = "unknown"

                self.objects[placeable] = RenderObject(model_name, vec3(), vec3(), data=placeable)

            self.objects[placeable].set_position(placeable.position.x, placeable.position.y, placeable.position.z)
            self.objects[placeable].set_rotation(0, 0, placeable.bearing)

        for git_creature in self.git.creatures:
            if git_creature not in self.objects:
                self.objects[git_creature] = self.getCreatureRenderObject(git_creature)

            self.objects[git_creature].set_position(git_creature.position.x, git_creature.position.y, git_creature.position.z)
            self.objects[git_creature].set_rotation(0, 0, git_creature.bearing)

        for waypoint in self.git.waypoints:
            if waypoint not in self.objects:
                obj = RenderObject("waypoint", vec3(), vec3(), data=waypoint)
                self.objects[waypoint] = obj

            self.objects[waypoint].set_position(waypoint.position.x, waypoint.position.y, waypoint.position.z)
            self.objects[waypoint].set_rotation(0, 0, waypoint.bearing)

        for store in self.git.stores:
            if store not in self.objects:
                obj = RenderObject("store", vec3(), vec3(), data=store)
                self.objects[store] = obj

            self.objects[store].set_position(store.position.x, store.position.y, store.position.z)
            self.objects[store].set_rotation(0, 0, store.bearing)

        for sound in self.git.sounds:
            if sound not in self.objects:
                try:
                    uts: UTS = self.module.sound(str(sound.resref)).resource() or UTS()
                except Exception as e:
                    print(format_exception_with_variables(e))
                    uts = UTS()

                obj = RenderObject(
                    "sound",
                    vec3(),
                    vec3(),
                    data=sound,
                    gen_boundary=lambda boundary: (boundary or Boundary.from_circle(self, uts.max_distance)),
                )
                self.objects[sound] = obj

            self.objects[sound].set_position(sound.position.x, sound.position.y, sound.position.z)
            self.objects[sound].set_rotation(0, 0, 0)

        for encounter in self.git.encounters:
            if encounter not in self.objects:
                obj = RenderObject(
                    "encounter",
                    vec3(),
                    vec3(),
                    data=encounter,
                    gen_boundary=lambda boundary: (boundary or Boundary(self, encounter.geometry.points)),
                )
                self.objects[encounter] = obj

            self.objects[encounter].set_position(encounter.position.x, encounter.position.y, encounter.position.z)
            self.objects[encounter].set_rotation(0, 0, 0)

        for trigger in self.git.triggers:
            if trigger not in self.objects:
                obj = RenderObject(
                    "trigger",
                    vec3(),
                    vec3(),
                    data=trigger,
                    gen_boundary=lambda boundary: (boundary or Boundary(self, trigger.geometry.points)),
                )
                self.objects[trigger] = obj

            self.objects[trigger].set_position(trigger.position.x, trigger.position.y, trigger.position.z)
            self.objects[trigger].set_rotation(0, 0, 0)

        for camera in self.git.cameras:
            if camera not in self.objects:
                obj = RenderObject("camera", vec3(), vec3(), data=camera)
                self.objects[camera] = obj

            self.objects[camera].set_position(camera.position.x, camera.position.y, camera.position.z + camera.height)
            euler: vec3 = glm.eulerAngles(quat(camera.orientation.w, camera.orientation.x, camera.orientation.y, camera.orientation.z))
            self.objects[camera].set_rotation(
                euler.y,
                euler.z - math.pi / 2 + math.radians(camera.pitch),
                -euler.x + math.pi / 2,
            )

        # Detect if GIT still exists; if they do not then remove them from the render list
        for obj in copy(self.objects):
            self._del_git_objects(obj)

    def _del_git_objects(self, obj):
        if isinstance(obj, GITCreature) and obj not in self.git.creatures:
            del self.objects[obj]
        if isinstance(obj, GITPlaceable) and obj not in self.git.placeables:
            del self.objects[obj]
        if isinstance(obj, GITDoor) and obj not in self.git.doors:
            del self.objects[obj]
        if isinstance(obj, GITTrigger) and obj not in self.git.triggers:
            del self.objects[obj]
        if isinstance(obj, GITStore) and obj not in self.git.stores:
            del self.objects[obj]
        if isinstance(obj, GITCamera) and obj not in self.git.cameras:
            del self.objects[obj]
        if isinstance(obj, GITWaypoint) and obj not in self.git.waypoints:
            del self.objects[obj]
        if isinstance(obj, GITEncounter) and obj not in self.git.encounters:
            del self.objects[obj]
        if isinstance(obj, GITSound) and obj not in self.git.sounds:
            del self.objects[obj]

    def render(self):
        """Renders the scene.

        Args:
        ----
            self: Renderer object containing scene data

        Returns:
        -------
            None: Does not return anything, renders directly to the framebuffer

        Processing Logic:
        ----------------
            - Clear color and depth buffers
            - Enable/disable backface culling
            - Set view and projection matrices
            - Render opaque geometry with lighting
            - Render instanced objects without lighting
            - Render selection bounding boxes
            - Render selection boundaries
            - Render non-selected boundaries
            - Render cursor if shown.
        """
        self.buildCache()

        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)

        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())
        self.shader.set_bool("enableLightmap", self.use_lightmap)
        group1: list[RenderObject] = [obj for obj in self.objects.values() if obj.model not in self.SPECIAL_MODELS]
        for obj in group1:
            self._render_object(self.shader, obj, mat4())

        # Draw all instance types that lack a proper model
        glEnable(GL_BLEND)
        self.plain_shader.use()
        self.plain_shader.set_matrix4("view", self.camera.view())
        self.plain_shader.set_matrix4("projection", self.camera.projection())
        self.plain_shader.set_vector4("color", vec4(0.0, 0.0, 1.0, 0.4))
        group2: list[RenderObject] = [obj for obj in self.objects.values() if obj.model in self.SPECIAL_MODELS]
        for obj in group2:
            self._render_object(self.plain_shader, obj, mat4())

        # Draw bounding box for selected objects
        self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
        for obj in self.selection:
            obj.cube(self).draw(self.plain_shader, obj.transform())

        # Draw boundary for selected objects
        glDisable(GL_CULL_FACE)
        self.plain_shader.set_vector4("color", vec4(0.0, 1.0, 0.0, 0.8))
        for obj in self.selection:
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        # Draw non-selected boundaries
        for obj in (obj for obj in self.objects.values() if obj.model == "sound" and not self.hide_sound_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in (obj for obj in self.objects.values() if obj.model == "encounter" and not self.hide_encounter_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in (obj for obj in self.objects.values() if obj.model == "trigger" and not self.hide_trigger_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        if self.show_cursor:
            self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
            self._render_object(self.plain_shader, self.cursor, mat4())

    def _render_object(self, shader: Shader, obj: RenderObject, transform: mat4):
        if isinstance(obj.data, GITCreature) and self.hide_creatures:
            return
        if isinstance(obj.data, GITPlaceable) and self.hide_placeables:
            return
        if isinstance(obj.data, GITDoor) and self.hide_doors:
            return
        if isinstance(obj.data, GITTrigger) and self.hide_triggers:
            return
        if isinstance(obj.data, GITEncounter) and self.hide_encounters:
            return
        if isinstance(obj.data, GITWaypoint) and self.hide_waypoints:
            return
        if isinstance(obj.data, GITSound) and self.hide_sounds:
            return
        if isinstance(obj.data, GITStore) and self.hide_sounds:
            return
        if isinstance(obj.data, GITCamera) and self.hide_cameras:
            return

        model: Model = self.model(obj.model)
        transform = transform * obj.transform()
        model.draw(shader, transform, override_texture=obj.override_texture)

        for child in obj.children:
            self._render_object(shader, child, transform)

    def picker_render(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)

        self.picker_shader.use()
        self.picker_shader.set_matrix4("view", self.camera.view())
        self.picker_shader.set_matrix4("projection", self.camera.projection())
        instances = list(self.objects.values())
        for obj in instances:
            int_rgb: int = instances.index(obj)
            r: int = int_rgb & 0xFF
            g: int = (int_rgb >> 8) & 0xFF
            b: int = (int_rgb >> 16) & 0xFF
            color = vec3(r / 0xFF, g / 0xFF, b / 0xFF)
            self.picker_shader.set_vector3("colorId", color)

            self._picker_render_object(obj, mat4())

    def _picker_render_object(self, obj: RenderObject, transform: mat4):
        if isinstance(obj.data, GITCreature) and self.hide_creatures:
            return
        if isinstance(obj.data, GITPlaceable) and self.hide_placeables:
            return
        if isinstance(obj.data, GITDoor) and self.hide_doors:
            return
        if isinstance(obj.data, GITTrigger) and self.hide_triggers:
            return
        if isinstance(obj.data, GITEncounter) and self.hide_encounters:
            return
        if isinstance(obj.data, GITWaypoint) and self.hide_waypoints:
            return
        if isinstance(obj.data, GITSound) and self.hide_sounds:
            return
        if isinstance(obj.data, GITStore) and self.hide_sounds:
            return
        if isinstance(obj.data, GITCamera) and self.hide_cameras:
            return

        model: Model = self.model(obj.model)
        model.draw(self.picker_shader, transform * obj.transform())
        for child in obj.children:
            self._picker_render_object(child, obj.transform())

    def pick(self, x, y) -> RenderObject:
        self.picker_render()
        pixel = glReadPixels(x, y, 1, 1, GL_BGRA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8  # type: ignore[]
        instances = list(self.objects.values())
        return instances[pixel] if pixel != 0xFFFFFF else None  # type: ignore[]

    def select(self, target: RenderObject | GITInstance, clear_existing: bool = True):
        if clear_existing:
            self.selection.clear()

        self.buildCache()
        actual_target: RenderObject
        if isinstance(target, GITInstance):
            for obj in self.objects.values():
                if obj.data is target:
                    actual_target = obj
                    break
        else:
            actual_target = target

        self.selection.append(actual_target)

    def screenToWorld(self, x: int, y: int) -> Vector3:
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)

        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())
        group1: list[RenderObject] = [obj for obj in self.objects.values() if isinstance(obj.data, LYTRoom)]
        for obj in group1:
            self._render_object(self.shader, obj, mat4())

        zpos = glReadPixels(x, self.camera.height - y, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[0][0]  # FIXME: "__getitem__" method not defined on type "int"
        cursor: vec3 = glm.unProject(
            vec3(x, self.camera.height - y, zpos),
            self.camera.view(),
            self.camera.projection(),
            vec4(0, 0, self.camera.width, self.camera.height),
        )
        return Vector3(cursor.x, cursor.y, cursor.z)

    def texture(self, name: str) -> Texture:
        if name not in self.textures:
            try:
                tpc = None
                # Check the textures linked to the module first
                if self.module is not None:
                    tpc = self.module.texture(name).resource() if self.module.texture(name) is not None else None
                # Otherwise just search through all relevant game files
                tpc: TPC | None = (
                    self.installation.texture(name, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN])
                    if tpc is None
                    else tpc
                )
            except (OSError, ValueError) as e:
                print(format_exception_with_variables(e))
                # If an error occurs during the loading process, just use a blank image.
                tpc = TPC()

            self.textures[name] = Texture.from_tpc(tpc) if tpc is not None else Texture.from_color(0xFF, 0, 0xFF)
        return self.textures[name]

    def model(self, name: str) -> Model:
        mdl_data = EMPTY_MDL_DATA
        mdx_data = EMPTY_MDX_DATA

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
                mdl_data = UNKNOWN_MDL_DATA
                mdx_data = UNKNOWN_MDX_DATA
            elif self.installation is not None:
                capsules: list[Capsule] = [] if self.module is None else self.module.capsules()
                mdl_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=capsules)
                mdx_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=capsules)
                if mdl_search is not None and mdx_search is not None:
                    mdl_data: bytes = mdl_search.data
                    mdx_data: bytes = mdx_search.data

            try:
                model = gl_load_stitched_model(self, BinaryReader.from_bytes(mdl_data, 12), BinaryReader.from_bytes(mdx_data))
            except Exception as e:
                print(format_exception_with_variables(e))
                model = gl_load_stitched_model(
                    self,
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )

            self.models[name] = model
        return self.models[name]

    def jump_to_entry_location(self):
        if self.module is None:
            self.camera.x = 0
            self.camera.y = 0
            self.camera.z = 0
        else:
            point: Vector3 = self.module.info().resource().entry_position
            self.camera.x = point.x
            self.camera.y = point.y
            self.camera.z = point.z + 1.8


class RenderObject:
    def __init__(
        self,
        model: str,
        position: vec3 | None = None,
        rotation: vec3 | None = None,
        *,
        data: Any = None,
        gen_boundary: Callable[[], Boundary] | None = None,
        override_texture: str | None = None,
    ):
        self.model: str = model
        self.children: list[RenderObject] = []
        self._transform: mat4 = mat4()
        self._position: vec3 = position if position is not None else vec3()
        self._rotation: vec3 = rotation if rotation is not None else vec3()
        self._cube: Cube | None = None
        self._boundary: Boundary | Empty | None = None
        self.genBoundary: Callable[[], Boundary] | None = gen_boundary
        self.data: Any = data
        self.override_texture: str | None = override_texture

        self._recalc_transform()

    def transform(self) -> mat4:
        return self._transform

    def set_transform(self, transform: mat4):
        self._transform = transform
        rotation = quat()
        glm.decompose(transform, vec3(), rotation, self._position, vec3(), vec4())  # FIXME: Type "mat4" cannot be assigned to type "F32Matrix3x3 | mat3x3 | Tuple[Tuple[Number, Number, Number]]"
        self._rotation = glm.eulerAngles(rotation)

    def _recalc_transform(self):
        self._transform = mat4() * glm.translate(self._position)
        self._transform = self._transform * glm.mat4_cast(quat(self._rotation))

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(self, x: float, y: float, z: float):
        if self._position.x == x and self._position.y == y and self._position.z == z:
            return

        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> vec3:
        return copy(self._rotation)

    def set_rotation(self, x: float, y: float, z: float):
        if self._rotation.x == x and self._rotation.y == y and self._rotation.z == z:
            return

        self._rotation = vec3(x, y, z)
        self._recalc_transform()

    def reset_cube(self):
        self._cube = None

    def cube(self, scene: Scene) -> Cube:
        if not self._cube:
            min_point = vec3(10000, 10000, 10000)
            max_point = vec3(-10000, -10000, -10000)
            self._cube_rec(scene, mat4(), self, min_point, max_point)
            self._cube = Cube(scene, min_point, max_point)
        return self._cube

    def radius(self, scene: Scene) -> float:
        cube = self.cube(scene)
        return max(
            abs(cube.min_point.x),
            abs(cube.min_point.y),
            abs(cube.min_point.z),
            abs(cube.max_point.x),
            abs(cube.max_point.y),
            abs(cube.max_point.z),
        )

    def _cube_rec(self, scene: Scene, transform: mat4, obj: RenderObject, min_point: vec3, max_point: vec3):
        obj_min, obj_max = scene.model(obj.model).box()
        obj_min = transform * obj_min
        obj_max = transform * obj_max
        min_point.x = min(min_point.x, obj_min.x, obj_max.x)
        min_point.y = min(min_point.y, obj_min.y, obj_max.y)
        min_point.z = min(min_point.z, obj_min.z, obj_max.z)
        max_point.x = max(max_point.x, obj_min.x, obj_max.x)
        max_point.y = max(max_point.y, obj_min.y, obj_max.y)
        max_point.z = max(max_point.z, obj_min.z, obj_max.z)
        for child in obj.children:
            self._cube_rec(scene, transform * child.transform(), child, min_point, max_point)

    def reset_boundary(self):
        self._boundary = None

    def boundary(self, scene: Scene) -> Boundary | Empty:
        if not self._boundary:
            if self.genBoundary is None:
                self._boundary = Empty(scene)
            else:
                self._boundary = self.genBoundary()
        return self._boundary


class Camera:
    def __init__(self):
        self.x: float = 40.0
        self.y: float = 130.0
        self.z: float = 0.5
        self.width: int = 1920
        self.height: int = 1080
        self.pitch: float = math.pi / 2
        self.yaw: float = 0.0
        self.distance: float = 10.0
        self.fov: float = 90.0

    def view(self) -> mat4:
        """Returns the view matrix for the camera.

        Args:
        ----
            self: The camera object

        Returns:
        -------
            mat4: The view matrix

        Processing Logic:
        ----------------
            - Calculate camera position based on yaw, pitch and distance from origin
            - Construct view matrix by translating to camera position and rotating by yaw and pitch
        """
        up = vec3(0, 0, 1)
        pitch = glm.vec3(1, 0, 0)

        x, y, z = self.x, self.y, self.z
        x += math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        y += math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        z += math.sin(self.pitch - math.pi / 2) * self.distance

        camera = mat4() * glm.translate(vec3(x, y, z))
        camera = glm.rotate(camera, self.yaw + math.pi / 2, up)
        camera = glm.rotate(camera, math.pi - self.pitch, pitch)
        return glm.inverse(camera)

    def projection(self) -> mat4:
        """Generate a perspective projection matrix.

        Args:
        ----
            self: The camera object

        Returns:
        -------
            mat4: The 4x4 perspective projection matrix

        Processing Logic:
        ----------------
            - Calculate the aspect ratio of the viewport from the camera's width and height
            - Use the aspect ratio and field of view to generate a perspective projection matrix using glm.perspective
            - The projection matrix transforms world coordinates into clip coordinates and maps the scene to the viewport
        """
        return glm.perspective(self.fov, self.width / self.height, 0.1, 5000)

    def translate(self, translation: vec3):
        self.x += translation.x
        self.y += translation.y
        self.z += translation.z

    def rotate(self, yaw: float, pitch: float):
        """Rotates the object by yaw and pitch angles.

        Args:
        ----
            yaw: float - Yaw angle in radians
            pitch: float - Pitch angle in radians

        Returns:
        -------
            None - Rotates object in place

        Processes rotation:
        ------------------
            - Increments pitch by pitch argument
            - Increments yaw by yaw argument
            - Clips pitch to valid range between 0 and pi radians to avoid gimbal lock
        """
        self.pitch += pitch
        self.yaw += yaw

        if self.pitch > math.pi - 0.001:
            self.pitch = math.pi - 0.001
        elif self.pitch < 0.001:
            self.pitch = 0.001

    def forward(self, ignore_z: bool = True) -> vec3:
        """Calculates the forward vector from the camera's rotation.

        Args:
        ----
            ignore_z: Whether to ignore z component of vector {True by default}.

        Returns:
        -------
            vec3: Normalized forward vector from camera rotation

        Processing Logic:
        ----------------
            - Calculate x component of eye vector from yaw and pitch
            - Calculate y component of eye vector from yaw and pitch
            - Set z component to 0 if ignore_z is True, else calculate from pitch
            - Return normalized negative of eye vector as forward vector.
        """
        eye_x: float = math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_y: float = math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_z: float | Literal[0] = 0 if ignore_z else math.sin(self.pitch - math.pi / 2)
        return glm.normalize(-vec3(eye_x, eye_y, eye_z))

    def sideward(self, ignore_z: bool = True) -> vec3:
        """Returns a normalized vector perpendicular to the forward direction.

        Args:
        ----
            ignore_z: Ignore z-component of forward vector.

        Returns:
        -------
            vec3: Normalized sideward vector.

        Processing Logic:
        ----------------
            - Calculate cross product of forward vector and (0,0,1) to get sideward vector
            - Normalize sideward vector to get unit sideward vector
            - Return normalized sideward vector
        """
        return glm.normalize(glm.cross(self.forward(ignore_z), vec3(0.0, 0.0, 1.0)))

    def upward(self, ignore_xy: bool = True) -> vec3:
        """Returns the upward vector of the entity.

        Args:
        ----
            ignore_xy (bool): Ignore x and y components of the vector if True.

        Returns:
        -------
            vec3: The normalized upward vector.

        Processing Logic:
        ----------------
            - Calculate forward vector ignoring z component
            - Calculate sideward vector ignoring z component
            - Take cross product of forward and sideward vectors
            - Return normalized cross product vector
        """
        if ignore_xy:
            return glm.normalize(vec3(0, 0, 1))
        forward: vec3 = self.forward(ignore_z=False)
        sideward: vec3 = self.sideward(ignore_z=False)
        cross: vec3 = glm.cross(forward, sideward)
        return glm.normalize(cross)

    def true_position(self) -> vec3:
        """Calculates the true position of an object based on its orientation and distance from origin.

        Args:
        ----
            self: {Object with x, y, z, yaw, pitch, and distance attributes}

        Returns:
        -------
            vec3: {Calculated true position as a 3D vector}

        Processing Logic:
        ----------------
            - Calculate x, y, z offsets based on orientation and distance
            - Add offsets to base x, y, z to get true position
            - Return true position as a 3D vector
        """
        x, y, z = self.x, self.y, self.z
        x += math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        y += math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        z += math.sin(self.pitch - math.pi / 2) * self.distance
        return vec3(x, y, z)
