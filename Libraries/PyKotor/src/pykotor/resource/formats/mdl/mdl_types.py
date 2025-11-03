"""Type definitions and data structures for MDL/MDX files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, IntFlag

from pykotor.common.misc import Color
from utility.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4


# region Enums and Flags
class MDLGeometryType(IntEnum):
    """Model geometry type indicating how it should be rendered."""

    GEOMETRY_UNKNOWN = 0
    GEOMETRY_NORMAL = 1
    GEOMETRY_SKINNED = 2
    GEOMETRY_DANGLY = 3
    GEOMETRY_SABER = 4


class MDLClassification(IntEnum):
    """Model classification indicating its usage in the game."""

    INVALID = 0
    EFFECT = 1
    TILE = 2
    CHARACTER = 4
    DOOR = 8
    PLACEABLE = 16
    OTHER = 32
    GUI = 64
    ITEM = 128
    LIGHTSABER = 256
    WAYPOINT = 512
    WEAPON = 1024
    FURNITURE = 2048


class MDLNodeFlags(IntFlag):
    """Node flags indicating what type of data is attached to the node."""

    HEADER = 1
    LIGHT = 2
    EMITTER = 4
    CAMERA = 8
    REFERENCE = 16
    MESH = 32
    SKIN = 64
    DANGLY = 256
    AABB = 512
    SABER = 2048


class MDLNodeType(IntEnum):
    """Node types indicating the role of the node in the model."""

    DUMMY = 1  # Empty node for hierarchy
    TRIMESH = 2  # Basic mesh
    DANGLYMESH = 3  # Physics-enabled mesh
    LIGHT = 4  # Light source
    EMITTER = 5  # Particle emitter
    REFERENCE = 6  # Reference to another model
    PATCH = 7  # NURBS patch (unused)
    AABB = 8  # Axis-aligned bounding box
    CAMERA = 10  # Camera viewpoint
    BINARY = 11  # Binary (unknown usage)
    SABER = 12  # Lightsaber blade



# region Controller Data
class MDLControllerType(IntEnum):
    """Controller types for animations."""
    INVALID = -1
    POSITION = 8
    ORIENTATION = 20
    SCALE = 36
    COLOR = 76
    ALPHAEND = 80
    ALPHASTART = 84
    RADIUS = 88
    BIRTHRATE = 88
    BOUNCECO = 92
    SHADOWRADIUS = 96
    COMBINEETIME = 96
    VERTICALDISPLACEMENT = 100
    DRAG = 100
    ILLUM_COLOR = 100
    ILLUM = 100
    FOCUSZONETX = 104
    FOCUSZONETY = 108
    FRAME = 112
    GRAV = 116
    LIFEEXP = 120
    MASS = 124
    P2P_BEZIER2 = 128
    ALPHA = 132
    P2P_BEZIER_2 = 132
    P2P_BEZIER3 = 132
    PARTICLEROTX = 136
    MULTIPLIER = 140
    PARTICLEROTY = 140
    PARTICLEROTZ = 144
    RANDVELX = 148
    RANDVELY = 152
    RANDVELZ = 156
    SIZESTART = 160
    SIZEEND = 164
    SIZESTART_Y = 168
    SIZEEND_Y = 172
    SPREAD = 176
    THRESHOLD = 180
    VELOCITY = 184
    XSIZE = 188
    YSIZE = 192
    BLUR = 196
    LIGHTNINGDELAY = 200
    LIGHTNINGRADIUS = 204
    LIGHTNINGSCALE = 208
    DETONATE = 212
    ALPHAMID = 216
    SIZEMID = 220
    SIZEMID_Y = 224
    BOUNCE_CO = 228
    RANDOMVELX = 232
    RANDOMVELY = 236
    RANDOMVELZ = 240
    TILING = 244


class MDLTrimeshProps(IntFlag):
    """Properties for trimesh nodes."""

    NONE = 0x00
    LIGHTMAP = 0x01
    COMPRESSED = 0x02
    UNKNOWN = 0x04
    TANGENTS = 0x08
    UNKNOWNA = 0x10
    UNKNOWNB = 0x20
    UNKNOWNC = 0x40
    UNKNOWND = 0x80


class MDLEmitterType(IntEnum):
    """Types of particle emitters."""

    STATIC = 0
    FIRE = 1
    FOUNTAIN = 2
    LIGHTNING = 3


class MDLRenderType(IntEnum):
    """Particle rendering types."""

    NORMAL = 0
    LINKED = 1
    BILLBOARD_TO_LOCAL_Z = 2
    BILLBOARD_TO_WORLD_Z = 3
    ALIGNED_TO_WORLD_Z = 4
    ALIGNED_TO_PARTICLE_DIR = 5
    MOTION_BLUR = 6


class MDLBlendType(IntEnum):
    """Particle blend modes."""

    NORMAL = 0
    PUNCH = 1
    LIGHTEN = 2
    MULTIPLY = 3


class MDLUpdateType(IntEnum):
    """Particle update modes."""

    FOUNTAIN = 0
    SINGLE = 1
    EXPLOSION = 2
    LIGHTNING = 3


class MDLTrimeshFlags(IntFlag):
    """Additional trimesh flags from xoreos KotOR implementation."""
    TILEFADE = 0x0001  # Has tile fade
    HEAD = 0x0002  # Is a head mesh
    RENDER = 0x0004  # Should be rendered
    SHADOW = 0x0008  # Casts shadows
    BEAMING = 0x0010  # Has beaming
    RENDER_ENV_MAP = 0x0020  # Should render environment mapping
    LIGHTMAP = 0x0040  # Has lightmap
    SKIN = 0x0080  # Is skinned mesh


class MDLLightFlags(IntFlag):
    """Light flags from xoreos KotOR implementation."""
    ENABLED = 0x0001  # Light is enabled
    SHADOW = 0x0002  # Light casts shadows
    FLARE = 0x0004  # Light has lens flare
    FADING = 0x0008  # Light is fading
    AMBIENT = 0x0010  # Light is ambient only


class MDLEmitterFlags(IntFlag):
    """Emitter flags from xoreos KotOR implementation."""
    LOOP = 0x0001  # Particle system loops
    BOUNCE = 0x0002  # Particles bounce
    RANDOM = 0x0004  # Random initial rotation
    INHERIT = 0x0008  # Inherit parent orientation
    INHERIT_VEL = 0x0010  # Inherit parent velocity
    INHERIT_LOCAL = 0x0020  # Inherit local transform
    SPLAT = 0x0040  # Splat particles on collision
    INHERIT_PART = 0x0080  # Inherit parent particle


class MDLSaberFlags(IntFlag):
    """Lightsaber flags from xoreos KotOR implementation."""
    FLARE = 0x0001  # Has flare effect
    DYNAMIC = 0x0002  # Dynamic lighting
    TRAIL = 0x0004  # Has motion trail


# endregion


# region Model Data
@dataclass
class MDLModelHeader:
    """Header data for MDL/MDX files."""

    geometry_type: MDLGeometryType = MDLGeometryType.GEOMETRY_NORMAL
    classification: MDLClassification = MDLClassification.OTHER
    fog_enabled: bool = False
    animation_scale: float = 1.0
    model_scale: float = 1.0
    supermodel_name: str = ""
    bounding_min: Vector3 = field(default_factory=Vector3.from_null)
    bounding_max: Vector3 = field(default_factory=Vector3.from_null)
    radius: float = 0.0
    animation_offset: int = 0
    mdx_size: int = 0
    name_offset: int = 0
    node_count: int = 0
    node_offset: int = 0
    unknown_0x24: int = 0  # Always 0?
    unknown_0x28: int = 0  # Always 0?
    unknown_0x38: int = 0  # Always 0?
    unknown_0x3c: int = 0  # Always 0?
    functions: list[str] = field(default_factory=list)  # Animation/model functions
    animation_count: int = 0
    bounding_sphere_radius: float = 0.0
    root_node_offset: int = 0
    vertex_offset: int = 0
    vertex_count: int = 0
    tilefade: bool = False
    tilefade_node_offset: int = 0
    flare_radius: float = 0.0
    blur_radius: float = 0.0


# endregion


# region Animation Data
@dataclass
class MDLControllerRow:
    """A row of keyframe data in a controller."""

    time: float = 0.0
    data: list[float] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.time} {self.data}".replace(",", "").replace("[", "").replace("]", "")


@dataclass
class MDLController:
    """A controller that influences some sort of change that is either static or animated."""

    controller_type: MDLControllerType = MDLControllerType.INVALID
    rows: list[MDLControllerRow] = field(default_factory=list)
    data_offset: int = 0
    column_count: int = 0
    row_count: int = 0
    timekeys_offset: int = 0
    columns: int = 0


@dataclass
class MDLEvent:
    """An event that occurs during an animation."""

    activation_time: float = 0.0
    name: str = ""


@dataclass
class MDLAnimation:
    """Animation data for a model."""

    name: str = ""
    root_model: str = ""
    anim_length: float = 0.0
    transition_length: float = 0.0
    events: list[MDLEvent] = field(default_factory=list)
    geometry_header: MDLModelHeader | None = None


# endregion


# region Node Data
@dataclass
class MDLBoneVertex:
    """Vertex bone weight data for skinned meshes."""

    vertex_weights: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    vertex_indices: tuple[float, float, float, float] = (-1.0, -1.0, -1.0, -1.0)


@dataclass
class MDLFace:
    """Triangle face data for meshes."""

    v1: int = 0
    v2: int = 0
    v3: int = 0
    material: SurfaceMaterial = SurfaceMaterial.GRASS
    smoothing_group: int = 0
    surface_light: int = 0
    plane_distance: float = 0.0
    normal: Vector3 = field(default_factory=Vector3.from_null)


@dataclass
class MDLConstraint:
    """Constraint data that can be attached to a node."""

    name: str = ""
    type: int = 0
    target: int = 0
    target_node: int = 0


@dataclass
class MDLLight:
    """Light data that can be attached to a node."""

    flare_radius: float = 0.0
    light_priority: int = 0
    ambient_only: bool = False
    dynamic_type: int = 0
    shadow: bool = False
    flare: bool = False
    fading_light: bool = False
    flare_sizes: list[float] = field(default_factory=list)
    flare_positions: list[float] = field(default_factory=list)
    flare_color_shifts: list[float] = field(default_factory=list)
    flare_textures: list[str] = field(default_factory=list)
    flare_count: int = 0
    light_flags: MDLLightFlags = field(default_factory=lambda: MDLLightFlags(0))
    color: Color = field(default_factory=lambda: Color.WHITE)
    multiplier: float = 1.0
    cutoff: float = 0.0
    corona: bool = False
    corona_strength: float = 0.0
    corona_size: float = 0.0
    shadow_texture: str = ""
    flare_size_factor: float = 1.0
    flare_inner_strength: float = 0.0
    flare_outer_strength: float = 0.0


@dataclass
class MDLEmitter:
    """Emitter data that can be attached to a node."""

    dead_space: float = 0.0
    blast_radius: float = 0.0
    blast_length: float = 0.0
    branch_count: int = 0
    control_point_smoothing: float = 0.0
    x_grid: int = 0
    y_grid: int = 0
    render_type: MDLRenderType = MDLRenderType.NORMAL
    update_type: MDLUpdateType = MDLUpdateType.FOUNTAIN
    blend_type: MDLBlendType = MDLBlendType.NORMAL
    texture: str = ""
    chunk_name: str = ""
    twosided: bool = False
    loop: bool = False
    render_order: int = 0
    frame_blend: bool = False
    depth_texture: str = ""
    update_flags: int = 0
    render_flags: int = 0
    emitter_flags: MDLEmitterFlags = field(default_factory=lambda: MDLEmitterFlags(0))
    spawn_type: int = 0
    particle_size: Vector2 = field(default_factory=lambda: Vector2(1.0, 1.0))
    birth_rate: float = 0.0
    spawn_rate: float = 0.0
    lifespan: float = 0.0
    mass: float = 0.0
    velocity: float = 0.0
    random_velocity: float = 0.0
    emission_angle: float = 0.0
    vertical_angle: float = 0.0


@dataclass
class MDLReference:
    """Reference data that can be attached to a node."""

    model: str = ""
    reattachable: bool = False


@dataclass
class MDLWalkmesh:
    """AABB data that can be attached to a node."""

    aabbs: list[MDLNode] = field(default_factory=list)


@dataclass
class MDLSaber:
    """Saber data that can be attached to a node."""

    saber_type: int = 0
    saber_color: int = 0
    saber_length: float = 0.0
    saber_width: float = 0.0
    saber_flare_color: int = 0
    saber_flare_radius: float = 0.0
    saber_flags: MDLSaberFlags = field(default_factory=lambda: MDLSaberFlags(0))
    blur_length: float = 0.0
    blur_width: float = 0.0
    glow_size: float = 0.0
    glow_intensity: float = 0.0
    blade_texture: str = ""
    hit_texture: str = ""
    flare_texture: str = ""


@dataclass
class MDLMesh:
    """Mesh data that can be attached to a node."""

    faces: list[MDLFace] = field(default_factory=list)
    diffuse: Color = field(default_factory=lambda: Color.WHITE)
    ambient: Color = field(default_factory=lambda: Color.WHITE)
    transparency_hint: int = 0
    texture_1: str = ""  # Primary texture (diffuse)
    texture_2: str = ""  # Secondary texture (lightmap)
    saber_unknowns: tuple[int, int, int, int, int, int, int, int] = (3, 0, 0, 0, 0, 0, 0, 0)
    animate_uv: bool = False
    uv_direction_x: float = 0.0
    uv_direction_y: float = 0.0
    uv_jitter: float = 0.0
    uv_jitter_speed: float = 0.0
    radius: float = 0.0
    bb_min: Vector3 = field(default_factory=Vector3.from_null)
    bb_max: Vector3 = field(default_factory=Vector3.from_null)
    average: Vector3 = field(default_factory=Vector3.from_null)
    area: float = 0.0
    has_lightmap: bool = False
    rotate_texture: bool = False
    background_geometry: bool = False
    shadow: bool = False
    beaming: bool = False
    render: bool = True
    vertex_positions: list[Vector3] = field(default_factory=list)
    vertex_normals: list[Vector3] | None = None
    vertex_uv1: list[Vector2] | None = None
    vertex_uv2: list[Vector2] | None = None
    dirt_enabled: bool = False
    dirt_texture: int = 0
    dirt_coordinate_space: int = 0
    hide_in_hologram: bool = False
    mdx_struct_size: int = 0
    mdx_struct_offset: int = 0
    vertex_offset: int = 0
    vertex_count: int = 0
    face_offset: int = 0
    face_count: int = 0
    props: MDLTrimeshProps = MDLTrimeshProps.NONE
    shadow_radius: float = 0.0
    shadow_min: Vector3 = field(default_factory=Vector3.from_null)
    shadow_max: Vector3 = field(default_factory=Vector3.from_null)
    shadow_node: str = ""
    trimesh_flags: MDLTrimeshFlags = field(default_factory=lambda: MDLTrimeshFlags(0))
    vertex_colors: list[Color] = field(default_factory=list)
    vertex_indices: list[int] = field(default_factory=list)
    face_materials: list[int] = field(default_factory=list)
    face_material_ids: list[int] = field(default_factory=list)


@dataclass
class MDLSkin(MDLMesh):
    """Skin data that can be attached to a node."""

    bone_indices: list[int] = field(default_factory=list)
    qbones: list[Vector4] = field(default_factory=list)
    tbones: list[Vector3] = field(default_factory=list)
    bonemap: list[int] = field(default_factory=list)
    vertex_bones: list[MDLBoneVertex] = field(default_factory=list)
    bone_offset: int = 0
    bone_count: int = 0


@dataclass
class MDLDangly(MDLMesh):
    """Dangly data that can be attached to a node."""

    constraints: list[MDLConstraint] = field(default_factory=list)
    verts: list[Vector3] = field(default_factory=list)
    verts_original: list[Vector3] = field(default_factory=list)
    constraint_offset: int = 0
    constraint_count: int = 0
    data_offset: int = 0
    data_count: int = 0


@dataclass
class MDLNode:
    """A node in the MDL tree that can store additional nodes or some extra data related to the model such as geometry or lighting."""

    children: list[MDLNode] = field(default_factory=list)
    controllers: list[MDLController] = field(default_factory=list)
    name: str = ""
    node_id: int = -1
    position: Vector3 = field(default_factory=Vector3.from_null)
    orientation: Vector4 = field(default_factory=lambda: Vector4(0, 0, 0, 1))
    node_type: MDLNodeType = MDLNodeType.DUMMY
    light: MDLLight | None = None
    emitter: MDLEmitter | None = None
    reference: MDLReference | None = None
    mesh: MDLMesh | MDLDangly | MDLSkin | None = None
    skin: MDLSkin | None = None
    dangly: MDLDangly | None = None
    aabb: MDLWalkmesh | None = None
    saber: MDLSaber | None = None
    mdx_struct_size: int = 0
    mdx_struct_offset: int = 0
    parent_id: int = -1
    inherit_color: bool = True
    part_number: int = 0

    def get_flags(self) -> MDLNodeFlags:
        """Get the node flags based on attached data."""
        flags = MDLNodeFlags.HEADER
        if self.light:
            flags |= MDLNodeFlags.LIGHT
        if self.emitter:
            flags |= MDLNodeFlags.EMITTER
        if self.reference:
            flags |= MDLNodeFlags.REFERENCE
        if isinstance(self.mesh, MDLMesh):
            flags |= MDLNodeFlags.MESH
        if isinstance(self.mesh, MDLSkin):
            flags |= MDLNodeFlags.SKIN
        if isinstance(self.mesh, MDLDangly):
            flags |= MDLNodeFlags.DANGLY
        if self.aabb:
            flags |= MDLNodeFlags.AABB
        if self.saber:
            flags |= MDLNodeFlags.SABER
        return flags


@dataclass
class MDLData:
    """Represents a MDL/MDX file."""

    root: MDLNode = field(default_factory=MDLNode)
    anims: list[MDLAnimation] = field(default_factory=list)
    name: str = ""
    supermodel: str = ""
    classification: MDLClassification = MDLClassification.OTHER
    fog_enabled: bool = False
    animation_scale: float = 1.0
    model_scale: float = 1.0
    supermodel_name: str = ""
    header: MDLModelHeader = field(default_factory=MDLModelHeader)
    mdx_data: bytes | None = None
    mdx_offset: int = 0
    xbox: bool = False
    kotor2: bool = False

    def get(self, node_name: str) -> MDLNode | None:
        """Gets a node by name from the tree."""
        nodes: list[MDLNode] = [self.root]
        while nodes:
            node: MDLNode = nodes.pop()
            if node.name == node_name:
                return node
            nodes.extend(node.children)
        return None

    def all_nodes(self) -> list[MDLNode]:
        """Returns a list of all nodes in the tree including the root node and children recursively."""
        nodes: list[MDLNode] = []
        scan: list[MDLNode] = [self.root]
        while scan:
            node: MDLNode = scan.pop()
            nodes.append(node)
            scan.extend(node.children)
        return nodes

    def find_parent(self, child: MDLNode) -> MDLNode | None:
        """Find the parent node of the given child node."""
        for node in self.all_nodes():
            if child in node.children:
                return node
        return None

    def global_position(self, node: MDLNode) -> Vector3:
        """Returns the global position of a node by traversing up the parent chain."""
        position: Vector3 = node.position
        parent: MDLNode | None = self.find_parent(node)
        while parent is not None:
            position += parent.position
            parent = self.find_parent(parent)
        return position

    def get_by_node_id(self, node_id: int) -> MDLNode:
        """Get node by node id."""
        for node in self.all_nodes():
            if node.node_id == node_id:
                return node
        raise ValueError(f"No node with id {node_id}")

    def all_textures(self) -> set[str]:
        """Returns all unique texture names used in the scene."""
        return {node.mesh.texture_1 for node in self.all_nodes() if (node.mesh and node.mesh.texture_1 != "NULL" and node.mesh.texture_1)}

    def all_lightmaps(self) -> set[str]:
        """Returns a set of all lightmap textures used in the scene."""
        return {node.mesh.texture_2 for node in self.all_nodes() if (node.mesh and node.mesh.texture_2 != "NULL" and node.mesh.texture_2)}


# endregion
