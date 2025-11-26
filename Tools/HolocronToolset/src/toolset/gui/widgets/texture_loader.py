"""Texture loading process for offloading texture I/O from the main thread.

This module provides a multiprocessing-based texture loader that runs in a separate
process to avoid blocking the UI when loading textures from KOTOR installations.

The TextureLoaderProcess communicates via multiprocessing queues:
- loadRequestQueue: Receives (resref, restype, context) tuples
- loadedTextureQueue: Sends back (context, tpc_mipmap_data) tuples
"""

from __future__ import annotations

import multiprocessing
import queue
import traceback
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger

from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPCMipmap
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from multiprocessing import Queue


class TextureLoaderProcess(multiprocessing.Process):
    """A separate process for loading textures from KOTOR installations.
    
    This process runs in the background and handles texture loading requests
    from the main thread, preventing UI lag during I/O operations.
    
    Communication is done via two queues:
    - request_queue: Main thread sends (resref, restype, context) tuples
    - result_queue: This process sends back (context, mipmap_data, error) tuples
    
    The context is opaque data passed through to identify which request
    corresponds to which result.
    """
    
    # Sentinel value to signal shutdown
    SHUTDOWN_SENTINEL = None
    
    def __init__(
        self,
        installation_path: str,
        is_tsl: bool,  # Note: is_tsl is stored but not used - Installation auto-detects game version
        request_queue: Queue[tuple[str, ResourceType, Any, int]],
        result_queue: Queue[tuple[Any, TPCMipmap | None, str | None]],
    ):
        """Initialize the texture loader process.
        
        Args:
            installation_path: Path to the KOTOR installation directory
            is_tsl: True if this is a TSL (KOTOR 2) installation (stored for compatibility, not used)
            request_queue: Queue to receive load requests from
            result_queue: Queue to send loaded textures to
        """
        super().__init__(daemon=True, name="TextureLoaderProcess")
        self._installation_path: str = installation_path
        self._is_tsl: bool = is_tsl  # Stored but not passed to Installation - it auto-detects
        self._request_queue: Queue[tuple[str, ResourceType, Any, int]] = request_queue
        self._result_queue: Queue[tuple[Any, TPCMipmap | None, str | None]] = result_queue
        self._shutdown = multiprocessing.Event()
    
    def run(self):
        """Main process loop - loads textures as requests come in."""
        try:
            # Initialize installation inside the process
            # (Can't pickle Installation objects across processes)
            # Note: Installation auto-detects K1 vs K2 based on game files
            installation = Installation(Path(self._installation_path))
            RobustLogger().info(f"TextureLoaderProcess started for: {self._installation_path}")
            
            while not self._shutdown.is_set():
                try:
                    # Wait for a request with timeout to allow checking shutdown
                    request = self._request_queue.get(timeout=0.5)
                    
                    # Check for shutdown sentinel
                    if request is self.SHUTDOWN_SENTINEL:
                        RobustLogger().info("TextureLoaderProcess received shutdown signal")
                        break
                    
                    # Unpack request
                    resref, restype, context, icon_size = request
                    
                    # Load the texture
                    try:
                        mipmap_data = self._load_texture(installation, resref, restype, icon_size)
                        self._result_queue.put((context, mipmap_data, None))
                    except FileNotFoundError:
                        # Missing textures are expected when browsing - use debug level
                        RobustLogger().debug(f"Texture not found: {resref}.{restype.extension}")
                        self._result_queue.put((context, None, None))
                    except Exception as e:
                        error_msg = f"Error loading texture {resref}: {e}"
                        RobustLogger().warning(error_msg)
                        self._result_queue.put((context, None, error_msg))
                        # Don't shutdown on individual texture load errors - continue processing
                        
                except queue.Empty:
                    # No request available, continue loop
                    continue
                except Exception as e:
                    # Log error but don't crash the process - continue processing other requests
                    RobustLogger().error(f"TextureLoaderProcess error processing request: {e}\n{traceback.format_exc()}")
                    # Continue the loop instead of crashing
                    
        except Exception as e:
            RobustLogger().error(f"TextureLoaderProcess fatal error: {e}\n{traceback.format_exc()}")
        finally:
            RobustLogger().info("TextureLoaderProcess shutting down")
    
    def _load_texture(
        self,
        installation: Installation,
        resref: str,
        restype: ResourceType,
        icon_size: int = 64,
    ) -> bytes:
        """Load a texture and return serialized mipmap data.
        
        Args:
            installation: The KOTOR installation to load from
            resref: Resource reference name
            restype: Resource type (TPC or TGA)
            icon_size: Target icon size for the mipmap
            
        Returns:
            Serialized TPCMipmap data that can be sent across process boundary
        """
        # Get texture data from installation
        texture_data = installation.resource(resref, restype)
        if texture_data is None:
            raise FileNotFoundError(f"Texture not found: {resref}.{restype.extension}")
        
        texture_bytes = texture_data.data
        
        if restype is ResourceType.TPC:
            tpc = read_tpc(texture_bytes)
            mipmap = self._get_best_mipmap(tpc, icon_size)
        else:
            # TGA - try to read via TPC format or use PIL
            try:
                tpc = read_tpc(texture_bytes)
                mipmap = self._get_best_mipmap(tpc, icon_size)
            except Exception:
                # Fall back to PIL for TGA
                mipmap = self._load_tga_via_pil(texture_bytes, icon_size)
        
        # Serialize mipmap data for cross-process transfer
        return self._serialize_mipmap(mipmap)
    
    def _get_best_mipmap(
        self,
        tpc: TPC,
        target_size: int,
    ) -> TPCMipmap:
        """Get the mipmap level closest to the target size."""
        mipmaps: list[TPCMipmap] = tpc.layers[0].mipmaps
        if not mipmaps:
            raise ValueError("TPC has no mipmaps")
        
        # Find mipmap closest to target size
        best_mipmap: TPCMipmap = mipmaps[0]
        best_diff: int = abs(best_mipmap.width - target_size)
        
        for mipmap in mipmaps[1:]:
            diff: int = abs(mipmap.width - target_size)
            if diff < best_diff:
                best_diff = diff
                best_mipmap = mipmap
        
        return best_mipmap
    
    def _load_tga_via_pil(
        self,
        data: bytes,
        icon_size: int,
    ) -> TPCMipmap:
        """Load a TGA file using PIL and convert to TPCMipmap."""
        try:
            from PIL import Image
            
            img: Image.Image = Image.open(BytesIO(data))
            
            # Convert to RGBA
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            
            # Resize to icon size
            img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            
            # Create TPCMipmap
            return TPCMipmap(
                width=img.width,
                height=img.height,
                tpc_format=TPCTextureFormat.RGBA,
                data=bytearray(img.tobytes()),
            )
        except ImportError:
            raise ImportError("PIL/Pillow is required to load TGA textures")
    
    def _serialize_mipmap(self, mipmap: TPCMipmap) -> bytes:
        """Serialize a TPCMipmap for cross-process transfer.
        
        Returns a bytes object containing:
        - width (4 bytes, int)
        - height (4 bytes, int)  
        - format (4 bytes, int - TPCTextureFormat value)
        - data_length (4 bytes, int)
        - data (variable length bytes)
        """
        import struct
        
        header = struct.pack(
            "<IIII",
            mipmap.width,
            mipmap.height,
            mipmap.tpc_format.value,
            len(mipmap.data),
        )
        return header + bytes(mipmap.data)
    
    def request_shutdown(self):
        """Request the process to shut down gracefully."""
        self._shutdown.set()
        try:
            self._request_queue.put(self.SHUTDOWN_SENTINEL, timeout=1.0)
        except Exception:
            pass
    
    def terminate(self):
        """Terminate the process."""
        self.request_shutdown()
        super().terminate()


def deserialize_mipmap(data: bytes) -> TPCMipmap:
    """Deserialize a TPCMipmap from bytes.
    
    This is used by the main thread to reconstruct the mipmap
    from data sent by TextureLoaderProcess.
    
    Args:
        data: Serialized mipmap bytes from TextureLoaderProcess
        
    Returns:
        Reconstructed TPCMipmap object
    """
    import struct
    
    header_size = 16  # 4 * 4 bytes
    width, height, format_value, data_length = struct.unpack("<IIII", data[:header_size])
    
    mipmap_data = bytearray(data[header_size:header_size + data_length])
    
    return TPCMipmap(
        width=width,
        height=height,
        tpc_format=TPCTextureFormat(format_value),
        data=mipmap_data,
    )

