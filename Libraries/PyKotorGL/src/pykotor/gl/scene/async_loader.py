from __future__ import annotations

import multiprocessing
import struct
import traceback

from concurrent.futures import Future, ProcessPoolExecutor
from typing import TYPE_CHECKING, Any, NamedTuple

from loggerplus import RobustLogger

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.tpc.tpc_data import TPC


# Intermediate data structures that can be pickled and sent between processes
class IntermediateTexture(NamedTuple):
    """Parsed texture data without OpenGL objects."""
    width: int
    height: int
    rgba_data: bytes  # RGBA pixel data
    mipmap_count: int


class IntermediateMesh(NamedTuple):
    """Parsed mesh data without OpenGL objects."""
    texture: str
    lightmap: str
    vertex_data: bytes
    element_data: bytes
    block_size: int
    data_bitflags: int
    vertex_offset: int
    normal_offset: int
    texture_offset: int
    lightmap_offset: int
    render: bool


class IntermediateNode(NamedTuple):
    """Parsed node data without OpenGL objects."""
    name: str
    position: tuple[float, float, float]
    rotation: tuple[float, float, float, float]
    mesh: IntermediateMesh | None
    children: list[IntermediateNode]
    render: bool


class IntermediateModel(NamedTuple):
    """Parsed model data without OpenGL objects."""
    root: IntermediateNode
    min_point: tuple[float, float, float]
    max_point: tuple[float, float, float]


# ===== IO Workers (Process Pool #1) =====
def _io_load_texture_bytes(
    name: str,
    module_root: str | None,
    module_capsule_paths: list[str],
    installation_path: str,
    installation_name: str,
    tsl: bool,  # noqa: FBT001
) -> tuple[str, bytes | None, str | None]:
    """Load texture bytes from disk in a separate process.
    
    Returns:
    -------
        tuple[resource_name, data_bytes, error_message]
    """
    try:
        # Import here to avoid pickling issues
        from pathlib import Path

        from pykotor.extract.installation import Installation

        installation = Installation(Path(installation_path), installation_name, tsl=tsl)
        
        # Try module first if available
        if module_root:
            from pykotor.common.module import Module
            module = Module(module_root, installation)
            module_tex = module.texture(name)
            if module_tex is not None:
                data = module_tex.data()
                if data is not None:
                    return (name, data, None)
        
        # Search in installation
        search_locs = [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN]
        result = installation.resource(name, ResourceType.TPC, search_locs)
        if result is not None:
            return (name, result.data, None)
        
        return (name, None, f"Texture '{name}' not found")
    except Exception as e:  # noqa: BLE001
        return (name, None, f"IO error loading texture '{name}': {e!s}\n{traceback.format_exc()}")


def _io_load_model_bytes(
    name: str,
    module_root: str | None,
    module_capsule_paths: list[str],
    installation_path: str,
    installation_name: str,
    tsl: bool,  # noqa: FBT001
) -> tuple[str, bytes | None, bytes | None, str | None]:
    """Load model bytes (MDL+MDX) from disk in a separate process.
    
    Returns:
    -------
        tuple[resource_name, mdl_bytes, mdx_bytes, error_message]
    """
    try:
        from pathlib import Path

        from pykotor.extract.installation import Installation
        
        installation = Installation(Path(installation_path), installation_name, tsl=tsl)
        search_locs = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
        
        # Get capsules if module exists
        capsules: list[Any] = []
        if module_root:
            from pykotor.common.module import Module
            module = Module(module_root, installation)
            capsules = module.capsules()
        
        mdl_result = installation.resource(name, ResourceType.MDL, search_locs, capsules=capsules)
        mdx_result = installation.resource(name, ResourceType.MDX, search_locs, capsules=capsules)
        
        if mdl_result is None or mdx_result is None:
            return (name, None, None, f"Model '{name}' MDL or MDX not found")
        
        return (name, mdl_result.data, mdx_result.data, None)
    except Exception as e:  # noqa: BLE001
        return (name, None, None, f"IO error loading model '{name}': {e!s}\n{traceback.format_exc()}")


# ===== Parsing Workers (Process Pool #2) =====
def _parse_texture_data(
    name: str,
    tpc_bytes: bytes,
) -> tuple[str, IntermediateTexture | None, str | None]:
    """Parse TPC bytes into intermediate texture data.
    
    Returns:
    -------
        tuple[resource_name, intermediate_texture, error_message]
    """
    try:
        tpc: TPC = read_tpc(tpc_bytes)
        
        # Convert to RGBA format for OpenGL
        width, height = tpc.width, tpc.height
        rgba_data = tpc.convert(tpc.TPC_RGBA, 0).data
        
        return (
            name,
            IntermediateTexture(
                width=width,
                height=height,
                rgba_data=rgba_data,
                mipmap_count=tpc.mipmap_count,
            ),
            None,
        )
    except Exception as e:  # noqa: BLE001
        return (name, None, f"Parse error for texture '{name}': {e!s}\n{traceback.format_exc()}")


def _parse_model_data(  # noqa: C901, PLR0915, PLR0912
    name: str,
    mdl_bytes: bytes,
    mdx_bytes: bytes,
) -> tuple[str, IntermediateModel | None, str | None]:
    """Parse MDL/MDX bytes into intermediate model data.
    
    Returns:
    -------
        tuple[resource_name, intermediate_model, error_message]
    """
    try:
        mdl_reader = BinaryReader.from_bytes(mdl_bytes)
        mdx_reader = BinaryReader.from_bytes(mdx_bytes)
        
        # Read model header
        mdl_reader.seek(40)
        root_node_offset = mdl_reader.read_uint32()
        
        mdl_reader.seek(184)
        offset_to_name_offsets = mdl_reader.read_uint32()
        name_count = mdl_reader.read_uint32()
        
        # Read names
        mdl_reader.seek(offset_to_name_offsets)
        name_offsets = [mdl_reader.read_uint32() for _ in range(name_count)]
        names: list[str] = []
        for name_offset in name_offsets:
            mdl_reader.seek(name_offset)
            names.append(mdl_reader.read_terminated_string("\0"))
        
        # Parse node tree recursively
        def parse_node(offset: int) -> IntermediateNode:
            mdl_reader.seek(offset)
            node_type = mdl_reader.read_uint16()
            mdl_reader.read_uint16()  # supernode id
            name_id = mdl_reader.read_uint16()
            node_name = names[name_id]
            
            mdl_reader.seek(offset + 16)
            pos_x = mdl_reader.read_single()
            pos_y = mdl_reader.read_single()
            pos_z = mdl_reader.read_single()
            rot_x = mdl_reader.read_single()
            rot_y = mdl_reader.read_single()
            rot_z = mdl_reader.read_single()
            rot_w = mdl_reader.read_single()
            
            child_offsets_ptr = mdl_reader.read_uint32()
            child_count = mdl_reader.read_uint32()
            
            # Check if it's a mesh node
            mesh_data: IntermediateMesh | None = None
            is_mesh = bool(node_type & 0b100000)
            is_walkmesh = bool(node_type & 0b1000000000)
            render = True
            
            if is_mesh and not is_walkmesh:
                mdl_reader.seek(offset + 80)
                fp = mdl_reader.read_uint32()
                k2 = fp in {4216880, 4216816, 4216864}
                
                mdl_reader.seek(offset + 80 + 8)
                mdl_reader.read_uint32()  # offset_to_faces
                face_count = mdl_reader.read_uint32()
                
                mdl_reader.seek(offset + 80 + 88)
                texture = mdl_reader.read_terminated_string("\0", 32)
                lightmap = mdl_reader.read_terminated_string("\0", 32)
                
                mdl_reader.seek(offset + 80 + 313)
                render = bool(mdl_reader.read_uint8())
                
                mdl_reader.seek(offset + 80 + 304)
                vertex_count = mdl_reader.read_uint16()
                
                if k2:
                    mdl_reader.seek(offset + 80 + 332)
                else:
                    mdl_reader.seek(offset + 80 + 324)
                mdx_offset = mdl_reader.read_uint32()
                
                # Read element data
                element_data = b""
                mdl_reader.seek(offset + 80 + 184)
                element_offsets_count = mdl_reader.read_uint32()
                offset_to_element_offsets = mdl_reader.read_int32()
                if offset_to_element_offsets != -1 and element_offsets_count > 0:
                    mdl_reader.seek(offset_to_element_offsets)
                    offset_to_elements = mdl_reader.read_uint32()
                    mdl_reader.seek(offset_to_elements)
                    element_data = mdl_reader.read_bytes(face_count * 2 * 3)
                
                mdl_reader.seek(offset + 80 + 252)
                mdx_block_size = mdl_reader.read_uint32()
                mdx_data_bitflags = mdl_reader.read_uint32()
                mdx_vertex_offset = mdl_reader.read_int32()
                mdx_normal_offset = mdl_reader.read_int32()
                mdl_reader.skip(4)
                mdx_texture_offset = mdl_reader.read_int32()
                mdx_lightmap_offset = mdl_reader.read_int32()
                
                if render and element_offsets_count > 0:
                    mdx_reader.seek(mdx_offset)
                    vertex_data = mdx_reader.read_bytes(mdx_block_size * vertex_count)
                    
                    mesh_data = IntermediateMesh(
                        texture=texture,
                        lightmap=lightmap,
                        vertex_data=vertex_data,
                        element_data=element_data,
                        block_size=mdx_block_size,
                        data_bitflags=mdx_data_bitflags,
                        vertex_offset=mdx_vertex_offset,
                        normal_offset=mdx_normal_offset,
                        texture_offset=mdx_texture_offset,
                        lightmap_offset=mdx_lightmap_offset,
                        render=render,
                    )
            
            # Parse children
            children: list[IntermediateNode] = []
            for i in range(child_count):
                mdl_reader.seek(child_offsets_ptr + i * 4)
                child_offset = mdl_reader.read_uint32()
                children.append(parse_node(child_offset))
            
            return IntermediateNode(
                name=node_name,
                position=(pos_x, pos_y, pos_z),
                rotation=(rot_x, rot_y, rot_z, rot_w),
                mesh=mesh_data,
                children=children,
                render=render,
            )
        
        root = parse_node(root_node_offset)
        
        # Calculate bounding box
        min_x, min_y, min_z = 100000.0, 100000.0, 100000.0
        max_x, max_y, max_z = -100000.0, -100000.0, -100000.0
        
        def calc_bounds(node: IntermediateNode):
            nonlocal min_x, min_y, min_z, max_x, max_y, max_z
            
            if node.mesh and node.render:
                vertex_count = len(node.mesh.vertex_data) // node.mesh.block_size
                for i in range(vertex_count):
                    idx = i * node.mesh.block_size + node.mesh.vertex_offset
                    x, y, z = struct.unpack("fff", node.mesh.vertex_data[idx:idx+12])
                    min_x, min_y, min_z = min(min_x, x), min(min_y, y), min(min_z, z)
                    max_x, max_y, max_z = max(max_x, x), max(max_y, y), max(max_z, z)
            
            for child in node.children:
                calc_bounds(child)
        
        calc_bounds(root)
        
        return (
            name,
            IntermediateModel(
                root=root,
                min_point=(min_x - 0.1, min_y - 0.1, min_z - 0.1),
                max_point=(max_x + 0.1, max_y + 0.1, max_z + 0.1),
            ),
            None,
        )
    except Exception as e:  # noqa: BLE001
        return (name, None, f"Parse error for model '{name}': {e!s}\n{traceback.format_exc()}")


# ===== Main Async Loader Class =====
class AsyncResourceLoader:
    """Manages asynchronous resource loading using two process pools."""
    
    def __init__(
        self,
        max_io_workers: int | None = None,
        max_parse_workers: int | None = None,
    ):
        """Initialize the async loader with two process pools.
        
        Args:
        ----
            max_io_workers: Max workers for IO pool (default: CPU count)
            max_parse_workers: Max workers for parsing pool (default: CPU count)
        """
        cpu_count = multiprocessing.cpu_count()
        self.max_io_workers = max_io_workers or max(1, cpu_count // 2)
        self.max_parse_workers = max_parse_workers or max(1, cpu_count // 2)
        
        self.io_pool: ProcessPoolExecutor | None = None
        self.parse_pool: ProcessPoolExecutor | None = None
        
        self.pending_io: dict[str, Future] = {}
        self.pending_parse: dict[str, Future] = {}
        
        self.logger = RobustLogger()
        
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.shutdown()
    
    def start(self):
        """Start both process pools."""
        if self.io_pool is None:
            self.io_pool = ProcessPoolExecutor(
                max_workers=self.max_io_workers,
                mp_context=multiprocessing.get_context("spawn"),
            )
            self.logger.debug(f"Started IO process pool with {self.max_io_workers} workers")
        
        if self.parse_pool is None:
            self.parse_pool = ProcessPoolExecutor(
                max_workers=self.max_parse_workers,
                mp_context=multiprocessing.get_context("spawn"),
            )
            self.logger.debug(f"Started Parse process pool with {self.max_parse_workers} workers")
    
    def shutdown(self, *, wait: bool = True):
        """Shutdown both process pools."""
        if self.io_pool is not None:
            self.io_pool.shutdown(wait=wait)
            self.io_pool = None
            self.logger.debug("Shutdown IO process pool")
        
        if self.parse_pool is not None:
            self.parse_pool.shutdown(wait=wait)
            self.parse_pool = None
            self.logger.debug("Shutdown Parse process pool")
        
        self.pending_io.clear()
        self.pending_parse.clear()
    
    def load_texture_async(
        self,
        name: str,
        module: Module | None,
        installation: Installation,
    ) -> Future[tuple[str, IntermediateTexture | None, str | None]]:
        """Load and parse texture asynchronously.
        
        Returns:
        -------
            Future that resolves to (name, intermediate_texture, error)
        """
        if self.io_pool is None or self.parse_pool is None:
            self.start()
        
        # Chain: IO -> Parse
        module_root = module.root() if module else None
        module_capsules = [] if module is None else [str(cap.filepath()) for cap in module.capsules()]
        
        io_future = self.io_pool.submit(
            _io_load_texture_bytes,
            name,
            module_root,
            module_capsules,
            str(installation.path()),
            installation.name,
            installation.tsl,
        )
        
        def on_io_complete(io_result_future: Future):
            try:
                resource_name, tpc_bytes, error = io_result_future.result()
                if error or tpc_bytes is None:
                    # Create a failed future
                    failed_future: Future = Future()
                    failed_future.set_result((resource_name, None, error))
                    return failed_future
                
                # Submit to parse pool
                return self.parse_pool.submit(_parse_texture_data, resource_name, tpc_bytes)
            except Exception as e:  # noqa: BLE001
                failed_future = Future()
                failed_future.set_result((name, None, str(e)))
                return failed_future
        
        # Use a manual future chain since we can't use asyncio
        result_future: Future = Future()
        
        def chain_callback(fut: Future):
            try:
                parse_future = on_io_complete(fut)
                
                def parse_callback(pf: Future):
                    try:
                        result_future.set_result(pf.result())
                    except Exception as e:  # noqa: BLE001
                        result_future.set_exception(e)
                
                parse_future.add_done_callback(parse_callback)
            except Exception as e:  # noqa: BLE001
                result_future.set_exception(e)
        
        io_future.add_done_callback(chain_callback)
        self.pending_io[f"tex_{name}"] = io_future
        
        return result_future
    
    def load_model_async(
        self,
        name: str,
        module: Module | None,
        installation: Installation,
    ) -> Future[tuple[str, IntermediateModel | None, str | None]]:
        """Load and parse model asynchronously.
        
        Returns:
        -------
            Future that resolves to (name, intermediate_model, error)
        """
        if self.io_pool is None or self.parse_pool is None:
            self.start()
        
        # Chain: IO -> Parse
        module_root = module.root() if module else None
        module_capsules = [] if module is None else [str(cap.filepath()) for cap in module.capsules()]
        
        io_future = self.io_pool.submit(
            _io_load_model_bytes,
            name,
            module_root,
            module_capsules,
            str(installation.path()),
            installation.name,
            installation.tsl,
        )
        
        def on_io_complete(io_result_future: Future):
            try:
                resource_name, mdl_bytes, mdx_bytes, error = io_result_future.result()
                if error or mdl_bytes is None or mdx_bytes is None:
                    failed_future: Future = Future()
                    failed_future.set_result((resource_name, None, error))
                    return failed_future
                
                # Submit to parse pool
                return self.parse_pool.submit(_parse_model_data, resource_name, mdl_bytes, mdx_bytes)
            except Exception as e:  # noqa: BLE001
                failed_future = Future()
                failed_future.set_result((name, None, str(e)))
                return failed_future
        
        # Chain futures manually
        result_future: Future = Future()
        
        def chain_callback(fut: Future):
            try:
                parse_future = on_io_complete(fut)
                
                def parse_callback(pf: Future):
                    try:
                        result_future.set_result(pf.result())
                    except Exception as e:  # noqa: BLE001
                        result_future.set_exception(e)
                
                parse_future.add_done_callback(parse_callback)
            except Exception as e:  # noqa: BLE001
                result_future.set_exception(e)
        
        io_future.add_done_callback(chain_callback)
        self.pending_io[f"mdl_{name}"] = io_future
        
        return result_future


# ===== OpenGL Object Creation (Main Process Only) =====
def create_texture_from_intermediate(
    intermediate: IntermediateTexture,
) -> Any:  # Returns Texture but avoid circular import
    """Create OpenGL Texture from intermediate data in main process."""
    from pykotor.gl.shader import Texture
    
    return Texture.from_rgba(
        intermediate.width,
        intermediate.height,
        intermediate.rgba_data,
    )


def create_model_from_intermediate(
    scene: Any,  # Scene type but avoid circular import
    intermediate: IntermediateModel,
) -> Any:  # Returns Model but avoid circular import
    """Create OpenGL Model from intermediate data in main process.
    
    MUST be called in main process with active OpenGL context.
    """
    from pykotor.gl import glm
    from pykotor.gl.models.mdl import Mesh, Model, Node
    
    def build_node(
        parent: Node | None,
        intermediate_node: IntermediateNode,
    ) -> Node:
        node = Node(scene, parent, intermediate_node.name)
        node._position = glm.vec3(*intermediate_node.position)  # noqa: SLF001
        node._rotation = glm.quat(*intermediate_node.rotation)  # noqa: SLF001
        node._recalc_transform()  # noqa: SLF001
        node.render = intermediate_node.render
        
        if intermediate_node.mesh and intermediate_node.render:
            imesh = intermediate_node.mesh
            node.mesh = Mesh(
                scene,
                node,
                imesh.texture,
                imesh.lightmap,
                bytearray(imesh.vertex_data),
                bytearray(imesh.element_data),
                imesh.block_size,
                imesh.data_bitflags,
                imesh.vertex_offset,
                imesh.normal_offset,
                imesh.texture_offset,
                imesh.lightmap_offset,
            )
        
        for child_data in intermediate_node.children:
            child_node = build_node(node, child_data)
            node.children.append(child_node)
        
        return node
    
    root_node = build_node(None, intermediate.root)
    return Model(scene, root_node)

