from __future__ import annotations

import multiprocessing
import struct
import traceback

from concurrent.futures import Future, ProcessPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Protocol

from loggerplus import RobustLogger

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc.tpc_auto import read_tpc

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc.tpc_data import TPC


class ResourceLoader(Protocol):
    """Protocol for loading resources - implemented by caller (e.g., HolocronToolset)."""
    
    def load_texture_data(self, name: str) -> bytes | None:
        """Load texture bytes by name. Returns None if not found."""
        ...
    
    def load_model_data(self, name: str) -> tuple[bytes | None, bytes | None]:
        """Load model bytes (MDL, MDX) by name. Returns (mdl_bytes, mdx_bytes)."""
        ...


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


# ===== Combined IO + Parsing Workers (Child Process) =====
# CRITICAL: NO Installation objects here! Only raw file IO + parsing

def _load_and_parse_texture(
    name: str,
    filepath: str,
    offset: int,
    size: int,
) -> tuple[str, IntermediateTexture | None, str | None]:
    """Load texture bytes from file AND parse in child process.
    
    Args:
    ----
        name: Resource name
        filepath: Absolute path to file
        offset: Byte offset in file
        size: Number of bytes to read
    
    Returns:
    -------
        tuple[resource_name, intermediate_texture, error_message]
    """
    try:
        from pathlib import Path
        
        # IO: Read raw bytes from file
        path = Path(filepath)
        if not path.exists():
            return (name, None, f"File not found: {filepath}")
        
        with path.open("rb") as f:
            f.seek(offset)
            tpc_bytes = f.read(size)
        
        # Parsing: Convert bytes to intermediate texture
        return _parse_texture_data(name, tpc_bytes)
    except Exception as e:  # noqa: BLE001
        return (name, None, f"IO+parse error for texture '{name}': {e!s}\n{traceback.format_exc()}")


def _load_and_parse_model(
    name: str,
    mdl_filepath: str,
    mdl_offset: int,
    mdl_size: int,
    mdx_filepath: str,
    mdx_offset: int,
    mdx_size: int,
) -> tuple[str, IntermediateModel | None, str | None]:
    """Load model bytes from files AND parse in child process.
    
    Args:
    ----
        name: Resource name
        mdl_filepath: Absolute path to MDL file
        mdl_offset: Byte offset in MDL file
        mdl_size: Number of bytes to read from MDL
        mdx_filepath: Absolute path to MDX file
        mdx_offset: Byte offset in MDX file
        mdx_size: Number of bytes to read from MDX
    
    Returns:
    -------
        tuple[resource_name, intermediate_model, error_message]
    """
    try:
        from pathlib import Path
        
        # IO: Read MDL bytes
        mdl_path = Path(mdl_filepath)
        if not mdl_path.exists():
            return (name, None, f"MDL file not found: {mdl_filepath}")
        
        with mdl_path.open("rb") as f:
            f.seek(mdl_offset)
            mdl_bytes = f.read(mdl_size)
        
        # IO: Read MDX bytes
        mdx_path = Path(mdx_filepath)
        if not mdx_path.exists():
            return (name, None, f"MDX file not found: {mdx_filepath}")
        
        with mdx_path.open("rb") as f:
            f.seek(mdx_offset)
            mdx_bytes = f.read(mdx_size)
        
        # Parsing: Convert bytes to intermediate model
        return _parse_model_data(name, mdl_bytes, mdx_bytes)
    except Exception as e:  # noqa: BLE001
        return (name, None, f"IO+parse error for model '{name}': {e!s}\n{traceback.format_exc()}")


# ===== Parsing Functions =====
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
        from pykotor.resource.formats.tpc.tpc_data import TPCTextureFormat
        
        tpc: TPC = read_tpc(tpc_bytes)
        
        # Get the first mipmap
        mm = tpc.get(0, 0)
        width = mm.width
        height = mm.height
        
        # Convert to RGBA if needed
        if mm.tpc_format != TPCTextureFormat.RGBA:
            tpc.convert(TPCTextureFormat.RGBA)
            mm = tpc.get(0, 0)
        
        rgba_data = bytes(mm.data)  # Ensure it's bytes, not bytearray
        
        return (
            name,
            IntermediateTexture(
                width=width,
                height=height,
                rgba_data=rgba_data,
                mipmap_count=1,  # We only use the first mipmap
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
        mdl_reader = BinaryReader.from_bytes(mdl_bytes, 12)  # Skip 12-byte header
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
    """Manages asynchronous resource loading using ProcessPoolExecutor.
    
    CRITICAL: ALL IO happens in child processes, NEVER in the main process.
    
    NOTE: This class does NOT use Installation directly. The caller provides
    loader functions that handle resource loading using whatever mechanism they want
    (Installation, HTInstallation, direct file access, etc.)
    """
    
    def __init__(
        self,
        texture_location_resolver: Callable[[str], tuple[str, int, int] | None] | None = None,
        model_location_resolver: Callable[[str], tuple[tuple[str, int, int] | None, tuple[str, int, int] | None]] | None = None,
        max_workers: int | None = None,
    ):
        """Initialize the async loader with ProcessPoolExecutor.
        
        Args:
        ----
            texture_location_resolver: Function that resolves texture name to (filepath, offset, size) in MAIN process
            model_location_resolver: Function that resolves model name to ((mdl_path, offset, size), (mdx_path, offset, size)) in MAIN process
            max_workers: Max workers for process pool (default: CPU count)
        """
        self.texture_location_resolver = texture_location_resolver
        self.model_location_resolver = model_location_resolver
        
        cpu_count = multiprocessing.cpu_count()
        self.max_workers = max_workers or max(1, cpu_count // 2)
        self.process_pool: ProcessPoolExecutor | None = None
        
        self.pending_textures: dict[str, Future] = {}
        self.pending_models: dict[str, Future] = {}
        
        self.logger = RobustLogger()
        
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.shutdown()
    
    def start(self):
        """Start the ProcessPoolExecutor for async IO operations."""
        if self.process_pool is None:
            self.process_pool = ProcessPoolExecutor(
                max_workers=self.max_workers,
                mp_context=multiprocessing.get_context("spawn"),
            )
            self.logger.debug(f"Started ProcessPoolExecutor with {self.max_workers} workers for async IO")
    
    def shutdown(self, *, wait: bool = True):
        """Shutdown ProcessPoolExecutor and cleanup pending futures."""
        # Cancel any pending futures
        for future in self.pending_textures.values():
            if not future.done():
                future.cancel()
        for future in self.pending_models.values():
            if not future.done():
                future.cancel()
        
        self.pending_textures.clear()
        self.pending_models.clear()
        
        if self.process_pool is not None:
            self.process_pool.shutdown(wait=wait)
            self.process_pool = None
            self.logger.debug("Shutdown ProcessPoolExecutor")
        
        self.logger.debug("Async loader shutdown complete")
    
    def load_texture_async(
        self,
        name: str,
    ) -> Future[tuple[str, IntermediateTexture | None, str | None]]:
        """Load and parse texture asynchronously.
        
        Main process: Resolve file location
        Child process: Do raw file IO + parsing
        
        Returns:
        -------
            Future that resolves to (name, intermediate_texture, error)
        """
        self.logger.debug(f"load_texture_async called for: {name}")
        
        if self.texture_location_resolver is None:
            # No resolver provided, return immediate failure
            self.logger.warning(f"No texture location resolver provided for: {name}")
            result: Future = Future()
            result.set_result((name, None, "No texture location resolver provided"))
            return result
        
        if self.process_pool is None:
            self.logger.debug("Process pool is None, starting...")
            self.start()
        
        # Resolve file location in main process
        result_future: Future = Future()
        
        try:
            self.logger.debug(f"Resolving texture location in main process: {name}")
            location = self.texture_location_resolver(name)
            
            if location is None:
                self.logger.warning(f"Texture '{name}' not found")
                result_future.set_result((name, None, f"Texture '{name}' not found"))
            else:
                filepath, offset, size = location
                # Submit IO + parsing to child process
                self.logger.debug(f"Submitting IO+parse for texture: {name} at {filepath}:{offset}:{size}")
                assert self.process_pool is not None
                io_parse_future = self.process_pool.submit(_load_and_parse_texture, name, filepath, offset, size)
                    
                def on_complete(pf: Future):
                    try:
                        self.logger.debug(f"IO+parse complete for texture: {name}")
                        result_future.set_result(pf.result())
                    except Exception as e:  # noqa: BLE001
                        self.logger.error(f"IO+parse exception for texture '{name}': {e!s}")
                        result_future.set_result((name, None, f"IO+parse error: {e!s}"))
                    
                io_parse_future.add_done_callback(on_complete)
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Resolution exception for texture '{name}': {e!s}")
            result_future.set_result((name, None, f"Resolution error: {e!s}"))
        
        self.pending_textures[name] = result_future
        return result_future
    
    def load_model_async(
        self,
        name: str,
    ) -> Future[tuple[str, IntermediateModel | None, str | None]]:
        """Load and parse model asynchronously.
        
        Main process: Resolve file locations
        Child process: Do raw file IO + parsing
        
        Returns:
        -------
            Future that resolves to (name, intermediate_model, error)
        """
        if self.model_location_resolver is None:
            # No resolver provided, return immediate failure
            result: Future = Future()
            result.set_result((name, None, "No model location resolver provided"))
            return result
        
        if self.process_pool is None:
            self.start()
        
        # Resolve file locations in main process
        result_future: Future = Future()
        
        try:
            self.logger.debug(f"Resolving model locations in main process: {name}")
            mdl_loc, mdx_loc = self.model_location_resolver(name)
            
            if mdl_loc is None or mdx_loc is None:
                self.logger.warning(f"Model '{name}' MDL or MDX not found")
                result_future.set_result((name, None, f"Model '{name}' MDL or MDX not found"))
            else:
                mdl_filepath, mdl_offset, mdl_size = mdl_loc
                mdx_filepath, mdx_offset, mdx_size = mdx_loc
                # Submit IO + parsing to child process
                self.logger.debug(f"Submitting IO+parse for model: {name}")
                assert self.process_pool is not None
                io_parse_future = self.process_pool.submit(
                    _load_and_parse_model,
                    name,
                    mdl_filepath, mdl_offset, mdl_size,
                    mdx_filepath, mdx_offset, mdx_size,
                )
                    
                def on_complete(pf: Future):
                        try:
                            result_future.set_result(pf.result())
                        except Exception as e:  # noqa: BLE001
                            self.logger.error(f"IO+parse exception for model '{name}': {e!s}")
                            result_future.set_result((name, None, f"IO+parse error: {e!s}"))                    
                io_parse_future.add_done_callback(on_complete)
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Resolution exception for model '{name}': {e!s}")
            result_future.set_result((name, None, f"Resolution error: {e!s}"))
        
        self.pending_models[name] = result_future
        return result_future


# ===== OpenGL Object Creation (Main Process Only) =====
def create_texture_from_intermediate(
    intermediate: IntermediateTexture,
) -> Any:  # Returns Texture but avoid circular import
    """Create OpenGL Texture from intermediate data in main process."""
    from pykotor.gl.shader.texture import Texture
    
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
    import glm
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

