"""Kit extraction from RIM and ERF files.

This module contains the core extraction logic moved from pykotor.tools.kit,
with support for both RIM and ERF file formats.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.bwm import BWMEdge, BWMFace
    from pykotor.resource.formats.erf import ERF
    from pykotor.resource.formats.rim import RIM

# Configure sys.path for development mode
if getattr(__import__("sys"), "frozen", False) is False:
    import pathlib
    import sys

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    # Try to find PyKotor and Utility libraries
    current_file = pathlib.Path(__file__)
    repo_root = current_file.parents[4]
    pykotor_path = repo_root / "Libraries" / "PyKotor" / "src"
    utility_path = repo_root / "Libraries" / "Utility" / "src"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    if utility_path.exists():
        update_sys_path(utility_path.parent)

from pykotor.common.module import Module
from pykotor.extract.file import LocationResult, ResourceIdentifier, ResourceResult
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.bwm import BWM, read_bwm
from pykotor.resource.formats.erf import read_erf
from pykotor.resource.formats.mdl import MDL, MDLNode, read_mdl
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import door as door_tools
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from utility.common.geometry import Vector2, Vector3

# Qt imports for minimap generation
# Set offscreen mode by default to avoid display issues in headless environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QT_AVAILABLE = False
try:
    from qtpy.QtGui import QColor, QImage, QPainter, QPainterPath

    QT_AVAILABLE = True
except ImportError:
    # Qt not available - will use Pillow fallback
    QImage = None  # type: ignore[assignment, misc]
    QColor = None  # type: ignore[assignment, misc]
    QPainter = None  # type: ignore[assignment, misc]
    QPainterPath = None  # type: ignore[assignment, misc]

# Pillow fallback for minimap generation
PIL_AVAILABLE = False
try:
    from PIL import Image, ImageDraw

    PIL_AVAILABLE = True
except ImportError:
    Image = None  # type: ignore[assignment, misc]
    ImageDraw = None  # type: ignore[assignment, misc]


def extract_kit(
    installation: Installation,
    module_name: str,
    output_path: Path,
    *,
    kit_id: str | None = None,
    logger: RobustLogger | None = None,
) -> None:
    """Extract kit resources from module RIM or ERF files.

    Supports both RIM files (module_name.rim, module_name_s.rim) and ERF files
    (module_name.mod, module_name.erf, module_name.hak, module_name.sav).

    Args:
    ----
        installation: The game installation instance
        module_name: The module name (e.g., "danm13" or "danm13.mod")
        output_path: Path where the kit should be generated
        kit_id: Optional kit identifier (defaults to module_name.lower())
        logger: Optional logger instance for progress reporting

    Processing Logic:
    -----------------
        1. Determine file type from module_name extension or search for RIM/ERF files
        2. Load archive files (RIM or ERF)
        3. Extract all relevant resources (MDL, MDX, WOK, TGA, TXI, UTD)
        4. Organize resources into kit structure
        5. Generate JSON file with component definitions

    Raises:
    ------
        FileNotFoundError: If no valid RIM or ERF files are found for the module
        ValueError: If the module name format is invalid
    """
    if logger is None:
        logger = RobustLogger()

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    module_path = Path(module_name)
    module_name_clean = module_path.stem.lower()
    logger.info(f"Processing module: {module_name_clean}")

    if kit_id is None:
        kit_id = module_name_clean
    
    kit_id = re.sub(r'[<>:"/\\|?*]', '_', str(kit_id))
    kit_id = kit_id.strip('. ')
    if not kit_id:
        kit_id = module_name_clean
    kit_id = kit_id.lower()

    # Determine file type from extension
    extension = module_path.suffix.lower() if module_path.suffix else None

    # ERF extensions: .erf, .mod, .hak, .sav
    # RIM extension: .rim
    is_erf = extension in {".erf", ".mod", ".hak", ".sav"}
    is_rim = extension == ".rim"

    rims_path = installation.rims_path()
    modules_path = installation.module_path()

    main_archive: RIM | ERF | None = None
    data_archive: RIM | ERF | None = None

    if is_erf:
        # ERF file specified - try to load it directly or search for it
        logger.info(f"Detected ERF format from extension: {extension}")
        erf_path = None

        # If it's a full path, use it directly
        if module_path.is_absolute() or module_path.exists():
            erf_path = module_path
        else:
            # Search in modules directory
            for ext in [".erf", ".mod", ".hak", ".sav"]:
                candidate = modules_path / f"{module_name_clean}{ext}"
                if candidate.exists():
                    erf_path = candidate
                    break

        if erf_path and erf_path.exists():
            logger.info(f"Loading ERF file: {erf_path}")
            main_archive = read_erf(erf_path)
        else:
            raise FileNotFoundError(f"ERF file not found: {module_name}")

    elif is_rim:
        # RIM file specified - try to load it directly or search for it
        logger.info("Detected RIM format from extension")
        rim_path = None

        # If it's a full path, use it directly
        if module_path.is_absolute() or module_path.exists():
            rim_path = module_path
        else:
            # Search in rims and modules directories
            for search_path in [rims_path, modules_path]:
                if search_path.exists():
                    candidate = search_path / f"{module_name_clean}.rim"
                    if candidate.exists():
                        rim_path = candidate
                        break

        if rim_path and rim_path.exists():
            logger.info(f"Loading RIM file: {rim_path}")
            main_archive = read_rim(rim_path)
        else:
            raise FileNotFoundError(f"RIM file not found: {module_name}")

    else:
        # No extension - search for both RIM and ERF files
        logger.info("No extension detected, searching for RIM or ERF files...")

        # Try RIM files first (module_name.rim and module_name_s.rim)
        main_rim_path = None
        data_rim_path = None

        for search_path in [rims_path, modules_path]:
            if search_path.exists():
                candidate_main = search_path / f"{module_name_clean}.rim"
                candidate_data = search_path / f"{module_name_clean}_s.rim"
                if candidate_main.exists():
                    main_rim_path = candidate_main
                if candidate_data.exists():
                    data_rim_path = candidate_data

        if main_rim_path or data_rim_path:
            logger.info(f"Found RIM files: main={main_rim_path}, data={data_rim_path}")
            if main_rim_path and main_rim_path.exists():
                try:
                main_archive = read_rim(main_rim_path)
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Failed to read RIM file '{main_rim_path}': {e}")
                    raise
            if data_rim_path and data_rim_path.exists():
                try:
                data_archive = read_rim(data_rim_path)
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Failed to read RIM file '{data_rim_path}': {e}")
                    raise
        else:
            # Try ERF files
            erf_path = None
            for ext in [".erf", ".mod", ".hak", ".sav"]:
                candidate = modules_path / f"{module_name_clean}{ext}"
                if candidate.exists():
                    erf_path = candidate
                    break

            if erf_path and erf_path.exists():
                logger.info(f"Found ERF file: {erf_path}")
                try:
                main_archive = read_erf(erf_path)
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Failed to read ERF file '{erf_path}': {e}")
                    raise
            else:
                msg = f"Neither RIM nor ERF files found for module '{module_name_clean}'"
                raise FileNotFoundError(msg)

    if main_archive is None and data_archive is None:
        msg = f"No valid archive files found for module '{module_name_clean}'"
        raise FileNotFoundError(msg)

    # Collect all resources from archive files
    all_resources: dict[tuple[str, ResourceType], bytes] = {}
    logger.info("Collecting resources from archive files...")

    for archive in [main_archive, data_archive]:
        if archive is None:
            continue
        resource_count = 0
        for resource in archive:  # Both RIM and ERF are iterable and yield ArchiveResource objects
            key = (str(resource.resref).lower(), resource.restype)
            if key not in all_resources:
                all_resources[key] = resource.data
                resource_count += 1
        logger.info(f"  Extracted {resource_count} resources from archive")

    logger.info(f"Total unique resources collected: {len(all_resources)}")

    # Organize resources by type
    components: dict[str, dict[str, bytes]] = {}  # component_id -> {mdl, mdx, wok}
    textures: dict[str, bytes] = {}  # texture_name -> tga_data
    texture_txis: dict[str, bytes] = {}  # texture_name -> txi_data
    lightmaps: dict[str, bytes] = {}  # lightmap_name -> tga_data
    lightmap_txis: dict[str, bytes] = {}  # lightmap_name -> txi_data
    doors: dict[str, bytes] = {}  # door_name -> utd_data
    skyboxes: dict[str, dict[str, bytes]] = {}  # skybox_name -> {mdl, mdx}

    # Identify components (MDL files that have corresponding WOK files)
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.MDL:
            # Check if there's a corresponding WOK file
            wok_key = (resname, ResourceType.WOK)
            mdx_key = (resname, ResourceType.MDX)
            if wok_key in all_resources:
                components[resname] = {
                    "mdl": data,
                    "mdx": all_resources.get(mdx_key, b""),
                    "wok": all_resources[wok_key],
                }
        elif restype == ResourceType.UTD:
            doors[resname] = data
        elif restype == ResourceType.MDX:
            # Check if this is a skybox (MDX without corresponding MDL/WOK)
            mdl_key = (resname, ResourceType.MDL)
            wok_key = (resname, ResourceType.WOK)
            if mdl_key in all_resources and wok_key not in all_resources:
                # Likely a skybox
                skyboxes[resname] = {
                    "mdl": all_resources[mdl_key],
                    "mdx": data,
                }

    # Extract textures and lightmaps from MDL files using iterate_textures/iterate_lightmaps
    # This is the same approach used in main.py _extract_mdl_textures
    # Use Module class to get all models (including from chitin) that reference textures/lightmaps
    all_texture_names: set[str] = set()
    all_lightmap_names: set[str] = set()

    # Create a Module instance to access all module resources (including from chitin)
    logger.info("Loading module resources...")
    module = Module(module_name_clean, installation, use_dot_mod=False)

    # Get all models from the module (including those loaded from chitin)
    for model_resource in module.models():
        try:
            model_data = model_resource.data()
            if model_data:
                try:
                all_texture_names.update(iterate_textures(model_data))
                all_lightmap_names.update(iterate_lightmaps(model_data))
                except Exception as e:  # noqa: BLE001
                    # Log which model failed to extract textures/lightmaps from
                    logger.warning(f"Failed to extract textures/lightmaps from model '{model_resource.resref}' (type: {model_resource.restype}): {e}")
        except Exception as e:  # noqa: BLE001
            # Skip models that can't be loaded, but log which one failed
            logger.warning(f"Failed to load model resource '{model_resource.resref}' (type: {model_resource.restype}): {e}")
            pass

    # Also extract all TPC/TGA files from RIM that might be textures/lightmaps
    # Some kits (like jedienclave) only have textures/lightmaps without components
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.TPC:
            # Determine if it's a texture or lightmap based on naming
            resname_lower = resname.lower()
            if "_lm" in resname_lower or resname_lower.endswith("_lm"):
                all_lightmap_names.add(resname)
            else:
                all_texture_names.add(resname)
        elif restype == ResourceType.TGA:
            # Determine if it's a texture or lightmap based on naming
            resname_lower = resname.lower()
            if "_lm" in resname_lower or resname_lower.endswith("_lm"):
                all_lightmap_names.add(resname)
            else:
                all_texture_names.add(resname)

    # Also check module resources for textures that might not be in RIM files
    # This catches textures that are in the module but not directly in the RIM
    for res_ident, loc_list in module.resources.items():
        if res_ident.restype in (ResourceType.TPC, ResourceType.TGA):
            resname_lower = res_ident.resname.lower()
            if "_lm" in resname_lower or resname_lower.endswith("_lm") or resname_lower.startswith("l_"):
                all_lightmap_names.add(res_ident.resname)
            else:
                all_texture_names.add(res_ident.resname)

    def extract_texture_or_lightmap(name: str, is_lightmap: bool) -> None:
        """Extract a texture or lightmap from RIM files or installation.

        This matches the implementation in Tools/HolocronToolset/src/toolset/gui/windows/main.py
        _locate_texture, _process_texture, and _save_texture methods.
        """
        name_lower: str = name.lower()
        target_dict: dict[str, bytes] = lightmaps if is_lightmap else textures
        target_txis: dict[str, bytes] = lightmap_txis if is_lightmap else texture_txis

        if name_lower in target_dict:
            return  # Already extracted

        # Use the same search locations as main.py _locate_texture
        try:
            location_results: dict[ResourceIdentifier, list[LocationResult]] = installation.locations(
                [ResourceIdentifier(resname=name, restype=rt) for rt in (ResourceType.TPC, ResourceType.TGA)],
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.TEXTURES_GUI,
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.CHITIN,
                ],
            )

            # Process like main.py _process_texture and _save_texture
            for res_ident, loc_list in location_results.items():
                if not loc_list:
                    continue

                location: LocationResult = loc_list[0]

                # Always convert to TGA format (like main.py with tpcDecompileCheckbox)
                if res_ident.restype == ResourceType.TPC:
                    # Read TPC from location
                    with location.filepath.open("rb") as f:
                        f.seek(location.offset)
                        tpc_data = f.read(location.size)
                    try:
                        tpc = read_tpc(tpc_data)
                        tga_data = bytearray()
                        write_tpc(tpc, tga_data, ResourceType.TGA)
                        target_dict[name_lower] = bytes(tga_data)
                        # Extract TXI if present (like main.py _extract_txi)
                        if tpc.txi and tpc.txi.strip():
                            target_txis[name_lower] = tpc.txi.encode("ascii", errors="ignore")
                    except Exception as e:  # noqa: BLE001
                        # If TPC can't be read, log it and skip it
                        logger.warning(f"Failed to read TPC file '{name}' (location: {location.filepath}, offset: {location.offset}, size: {location.size}): {e}")
                        continue
                else:
                    # TGA file - read directly
                    with location.filepath.open("rb") as f:
                        f.seek(location.offset)
                        target_dict[name_lower] = f.read(location.size)
                # Try to find corresponding TXI file for both TPC and TGA (like main.py tpcTxiCheckbox)
                # Only if we haven't already extracted TXI from TPC
                if name_lower not in target_txis:
                    try:
                        txi_results = installation.locations(
                            [ResourceIdentifier(resname=name, restype=ResourceType.TXI)],
                            [
                                SearchLocation.OVERRIDE,
                                SearchLocation.TEXTURES_GUI,
                                SearchLocation.TEXTURES_TPA,
                                SearchLocation.CHITIN,
                            ],
                        )
                        for txi_res_ident, txi_loc_list in txi_results.items():
                            if txi_loc_list:
                                txi_location = txi_loc_list[0]
                                with txi_location.filepath.open("rb") as f:
                                    f.seek(txi_location.offset)
                                    target_txis[name_lower] = f.read(txi_location.size)
                                break
                    except Exception:  # noqa: BLE001
                        pass
                break  # Use first available location
        except Exception:  # noqa: BLE001
            pass  # Texture/lightmap not found, skip it

    # Extract all textures
    logger.info(f"Extracting {len(all_texture_names)} textures...")
    for texture_name in all_texture_names:
        extract_texture_or_lightmap(texture_name, is_lightmap=False)

    # Extract all lightmaps
    logger.info(f"Extracting {len(all_lightmap_names)} lightmaps...")
    for lightmap_name in all_lightmap_names:
        extract_texture_or_lightmap(lightmap_name, is_lightmap=True)

    # After extracting all textures/lightmaps, try to find TXI files for any that don't have them yet
    # This ensures we get TXI files even if they weren't found during initial extraction
    # Use the actual texture names from the textures dict (which are lowercase)
    # Also try the original names from all_texture_names in case case matters
    texture_name_map: dict[str, str] = {}  # Map lowercase -> original case
    for orig_name in all_texture_names:
        texture_name_map[orig_name.lower()] = orig_name

    missing_txi_count: int = 0
    found_txi_count: int = 0

    for texture_name_lower in textures.keys():
        if texture_name_lower not in texture_txis:
            missing_txi_count += 1
            # Try to find TXI file for this texture
            # Try both lowercase and original case
            names_to_try = [texture_name_lower]
            if texture_name_lower in texture_name_map:
                orig_name = texture_name_map[texture_name_lower]
                if orig_name != texture_name_lower:
                    names_to_try.append(orig_name)

            found: bool = False
            for name_to_try in names_to_try:
                try:
                    txi_results = installation.locations(
                        [ResourceIdentifier(resname=name_to_try, restype=ResourceType.TXI)],
                        [
                            SearchLocation.OVERRIDE,
                            SearchLocation.TEXTURES_GUI,
                            SearchLocation.TEXTURES_TPA,
                            SearchLocation.CHITIN,
                        ],
                    )
                    for txi_res_ident, txi_loc_list in txi_results.items():
                        if txi_loc_list:
                            txi_location = txi_loc_list[0]
                            with txi_location.filepath.open("rb") as f:
                                f.seek(txi_location.offset)
                                texture_txis[texture_name_lower] = f.read(txi_location.size)
                            found = True
                            found_txi_count += 1
                            break
                    if found:
                        break  # Found it, no need to try other names
                except Exception:  # noqa: BLE001
                    pass

            if not found:
                # Create empty TXI file as placeholder (many TXI files in the game are empty)
                # This matches the expected kit structure where textures have corresponding TXI files
                texture_txis[texture_name_lower] = b""

    # Same for lightmaps
    lightmap_name_map: dict[str, str] = {}  # Map lowercase -> original case
    for orig_name in all_lightmap_names:
        lightmap_name_map[orig_name.lower()] = orig_name

    missing_lm_txi_count = 0
    found_lm_txi_count = 0

    for lightmap_name_lower in lightmaps.keys():
        if lightmap_name_lower not in lightmap_txis:
            missing_lm_txi_count += 1
            # Try to find TXI file for this lightmap
            # Try both lowercase and original case
            names_to_try: list[str] = [lightmap_name_lower]
            if lightmap_name_lower in lightmap_name_map:
                orig_name = lightmap_name_map[lightmap_name_lower]
                if orig_name != lightmap_name_lower:
                    names_to_try.append(orig_name)

            found_lm = False
            for name_to_try in names_to_try:
                try:
                    txi_results = installation.locations(
                        [ResourceIdentifier(resname=name_to_try, restype=ResourceType.TXI)],
                        [
                            SearchLocation.OVERRIDE,
                            SearchLocation.TEXTURES_GUI,
                            SearchLocation.TEXTURES_TPA,
                            SearchLocation.CHITIN,
                        ],
                    )
                    for txi_res_ident, txi_loc_list in txi_results.items():
                        if txi_loc_list:
                            txi_location = txi_loc_list[0]
                            with txi_location.filepath.open("rb") as f:
                                f.seek(txi_location.offset)
                                lightmap_txis[lightmap_name_lower] = f.read(txi_location.size)
                            found_lm = True
                            found_lm_txi_count += 1
                            break
                    if found_lm:
                        break  # Found it, no need to try other names
                except Exception:  # noqa: BLE001
                    pass

            if not found_lm:
                # Create empty TXI file as placeholder (many TXI files in the game are empty)
                lightmap_txis[lightmap_name_lower] = b""

    # Create kit directory structure
    kit_dir: Path = output_path / kit_id
    kit_dir.mkdir(parents=True, exist_ok=True)

    textures_dir: Path = kit_dir / "textures"
    textures_dir.mkdir(exist_ok=True)
    lightmaps_dir: Path = kit_dir / "lightmaps"
    lightmaps_dir.mkdir(exist_ok=True)
    skyboxes_dir: Path = kit_dir / "skyboxes"
    skyboxes_dir.mkdir(exist_ok=True)

    # Write component files
    logger.info(f"Writing {len(components)} components...")
    component_list: list[dict[str, str | int | list[dict]]] = []
    for component_id, component_data in components.items():
        logger.info(f"  Processing component: {component_id}")
        try:
        # Write component files directly in kit_dir (not in subdirectory)
        (kit_dir / f"{component_id}.mdl").write_bytes(component_data["mdl"])
        if component_data["mdx"]:
            (kit_dir / f"{component_id}.mdx").write_bytes(component_data["mdx"])
            
            # Read and validate WOK file before writing
            try:
                bwm: BWM = read_bwm(component_data["wok"])
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read WOK file for component '{component_id}': {e}")
                logger.debug(f"WOK data size: {len(component_data['wok'])} bytes")
                raise
        (kit_dir / f"{component_id}.wok").write_bytes(component_data["wok"])

        # Generate minimap PNG from BWM
            try:
        minimap_image = _generate_component_minimap(bwm)
        minimap_path: Path = kit_dir / f"{component_id}.png"
        # Save image - both QImage and PIL Image support save() with same signature
        minimap_image.save(str(minimap_path), "PNG")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to generate minimap for component '{component_id}': {e}")
                # Continue without minimap

        # Extract doorhooks from BWM edges with transitions
            try:
        doorhooks: list[dict] = _extract_doorhooks_from_bwm(bwm, len(doors))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to extract doorhooks for component '{component_id}': {e}")
                doorhooks = []

        # Create component entry with extracted doorhooks
        component_list.append({
            "name": component_id.replace("_", " ").title(),
            "id": component_id,
            "native": 1,
            "doorhooks": doorhooks,
        })
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to process component '{component_id}': {e}")
            logger.exception(f"Exception details for component '{component_id}'")
            # Continue with next component instead of aborting
            continue

    # Write texture files
    logger.info(f"Writing {len(textures)} textures...")
    for texture_name, texture_data in textures.items():
        try:
        (textures_dir / f"{texture_name}.tga").write_bytes(texture_data)
        # Always write TXI file (even if empty) to match expected kit structure
        if texture_name in texture_txis:
            (textures_dir / f"{texture_name}.txi").write_bytes(texture_txis[texture_name])
        else:
            # Create empty TXI placeholder if not found
            (textures_dir / f"{texture_name}.txi").write_bytes(b"")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to write texture '{texture_name}': {e}")
            logger.debug(f"Texture data size: {len(texture_data)} bytes")
            continue

    # Write lightmap files
    logger.info(f"Writing {len(lightmaps)} lightmaps...")
    for lightmap_name, lightmap_data in lightmaps.items():
        try:
        (lightmaps_dir / f"{lightmap_name}.tga").write_bytes(lightmap_data)
        # Always write TXI file (even if empty) to match expected kit structure
        if lightmap_name in lightmap_txis:
            (lightmaps_dir / f"{lightmap_name}.txi").write_bytes(lightmap_txis[lightmap_name])
        else:
            # Create empty TXI placeholder if not found
            (lightmaps_dir / f"{lightmap_name}.txi").write_bytes(b"")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to write lightmap '{lightmap_name}': {e}")
            logger.debug(f"Lightmap data size: {len(lightmap_data)} bytes")
            continue

    # Write door files
    logger.info(f"Processing {len(doors)} doors...")
    door_list: list[dict] = []
    for door_idx, (door_name, door_data) in enumerate(doors.items()):
        logger.info(f"  Processing door {door_idx + 1}/{len(doors)}: {door_name}")
        try:
            # Validate UTD file before writing
            try:
                utd = read_utd(door_data)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read UTD file for door '{door_name}': {e}")
                logger.debug(f"UTD data size: {len(door_data)} bytes")
                raise
            
            # Write door UTD files (k1 and k2 variants)
        (kit_dir / f"{door_name}_k1.utd").write_bytes(door_data)
        # For K1, we use the same UTD for K2 (in real kits, these might differ)
        (kit_dir / f"{door_name}_k2.utd").write_bytes(door_data)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to process door '{door_name}': {e}")
            logger.exception(f"Exception details for door '{door_name}'")
            # Continue with next door instead of aborting
            continue

        # Extract width and height from door model
        door_width = 2.0  # Default fallback
        door_height = 3.0  # Default fallback

        logger.debug(f"[DOOR DEBUG] Processing door '{door_name}' (appearance_id={utd.appearance_id})")

        model_name: str | None = None
        mdl: MDL | None = None
        model_extracted = False

        # Try method 1: Get dimensions from model bounding box
        try:
            # Get door model name from UTD
            # Try to get genericdoors.2da using locations() (more reliable than resource())
            genericdoors_2da = None

            # Use locations() to find genericdoors.2da (more reliable)
            try:
                location_results = installation.locations(
                    [ResourceIdentifier(resname="genericdoors", restype=ResourceType.TwoDA)],
                    order=[SearchLocation.OVERRIDE, SearchLocation.CHITIN],
                )
                for res_ident, loc_list in location_results.items():
                    if loc_list:
                        loc = loc_list[0]  # Use first location (Override takes precedence)
                        if loc.filepath and Path(loc.filepath).exists():
                            from pykotor.resource.formats.twoda import read_2da

                            # Read from file (handles both direct files and BIF files)
                            with loc.filepath.open("rb") as f:
                                f.seek(loc.offset)
                                data = f.read(loc.size)
                            genericdoors_2da = read_2da(data)
                            break
            except Exception as e:  # noqa: BLE001
                logger.debug(f"locations() failed for genericdoors.2da: {e}")

            # Fallback: try resource() if locations() didn't work
            if genericdoors_2da is None:
                try:
                    genericdoors_result = installation.resource("genericdoors", ResourceType.TwoDA)
                    if genericdoors_result and genericdoors_result.data:
                        from pykotor.resource.formats.twoda import read_2da

                        genericdoors_2da = read_2da(genericdoors_result.data)
                except Exception as e:  # noqa: BLE001
                    logger.debug(f"resource() also failed for genericdoors.2da: {e}")

            if genericdoors_2da is None:
                logger.warning(f"Could not load genericdoors.2da for door '{door_name}', using defaults")
            else:
                # Get model name using the loaded 2DA
                try:
                    model_name = door_tools.get_model(utd, installation, genericdoors=genericdoors_2da)
                    if not model_name:
                        logger.warning(
                            f"Could not get model name for door '{door_name}' (appearance_id={utd.appearance_id}), using defaults"
                        )
                    else:
                        # Try multiple variations of the model name to find the resource
                        # Some doors have models that don't exist, so we try various name formats
                        model_variations = [
                            model_name,  # Original case
                            model_name.lower(),  # Lowercase
                            model_name.upper(),  # Uppercase
                            model_name.lower().replace(".mdl", "").replace(".mdx", ""),  # Normalized lowercase
                        ]
                        
                        # Remove duplicates while preserving order
                        seen = set()
                        model_variations = [v for v in model_variations if v not in seen and not seen.add(v)]
                        
                        mdl_data: bytes | None = None
                        mdl_result: ResourceResult | None = None
                        
                        # Try locations() first (more reliable, searches multiple locations)
                        for model_var in model_variations:
                            try:
                                location_results = installation.locations(
                                    [ResourceIdentifier(resname=model_var, restype=ResourceType.MDL)],
                                    [
                                        SearchLocation.OVERRIDE,
                                        SearchLocation.MODULES,
                                        SearchLocation.CHITIN,
                                    ],
                                )
                                for res_ident, loc_list in location_results.items():
                                    if loc_list:
                                        loc = loc_list[0]
                                        try:
                                            with loc.filepath.open("rb") as f:
                                                f.seek(loc.offset)
                                                mdl_data = f.read(loc.size)
                                            mdl = read_mdl(mdl_data)
                                            model_extracted = True
                                            break
                                        except Exception:  # noqa: BLE001
                                            continue
                                if model_extracted:
                                    break
                            except Exception:  # noqa: BLE001
                                continue
                        
                        # Fallback to resource() if locations() didn't work
                        if not model_extracted:
                            for model_var in model_variations:
                                try:
                                    mdl_result = installation.resource(model_var, ResourceType.MDL)
                                    if mdl_result and mdl_result.data:
                                        mdl_data = mdl_result.data
                                        mdl = read_mdl(mdl_data)
                                        model_extracted = True
                                        break
                                except Exception:  # noqa: BLE001
                                    continue
                        
                        if not model_extracted:
                            logger.warning(
                                f"Could not load MDL '{model_name}' (tried variations: {model_variations}) "
                                f"for door '{door_name}' (appearance_id={utd.appearance_id}), using defaults"
                            )
                            logger.debug(f"[DOOR DEBUG] Door '{door_name}': Using default dimensions (2.0 x 3.0) - model not found")
                        else:
                            mdl = read_mdl(mdl_result.data)
                            model_extracted = True

                            # Calculate overall bounding box from all meshes
                            bb_min = Vector3(1000000, 1000000, 1000000)
                            bb_max = Vector3(-1000000, -1000000, -1000000)

                            # Iterate through all nodes and their meshes
                            nodes_to_check: list[MDLNode] = [mdl.root]
                            mesh_count = 0
                            while nodes_to_check:
                                node: MDLNode = nodes_to_check.pop()
                                if node.mesh:
                                    mesh_count += 1
                                    # Use mesh bounding box if available
                                    if node.mesh.bb_min and node.mesh.bb_max:
                                        bb_min.x = min(bb_min.x, node.mesh.bb_min.x)
                                        bb_min.y = min(bb_min.y, node.mesh.bb_min.y)
                                        bb_min.z = min(bb_min.z, node.mesh.bb_min.z)
                                        bb_max.x = max(bb_max.x, node.mesh.bb_max.x)
                                        bb_max.y = max(bb_max.y, node.mesh.bb_max.y)
                                        bb_max.z = max(bb_max.z, node.mesh.bb_max.z)
                                    # Fallback: calculate from vertex positions if bounding box not set
                                    elif node.mesh.vertex_positions:
                                        for vertex in node.mesh.vertex_positions:
                                            bb_min.x = min(bb_min.x, vertex.x)
                                            bb_min.y = min(bb_min.y, vertex.y)
                                            bb_min.z = min(bb_min.z, vertex.z)
                                            bb_max.x = max(bb_max.x, vertex.x)
                                            bb_max.y = max(bb_max.y, vertex.y)
                                            bb_max.z = max(bb_max.z, vertex.z)

                                # Check child nodes
                                nodes_to_check.extend(node.children)

                            # Calculate dimensions from bounding box
                            # Doors are typically oriented along Y axis (width) and Z axis (height)
                            # X is typically depth/thickness
                            if bb_min.x < 1000000:  # Valid bounding box calculated
                                # Width is typically the Y dimension (horizontal when door is closed)
                                # Height is typically the Z dimension (vertical)
                                width = abs(bb_max.y - bb_min.y)
                                height = abs(bb_max.z - bb_min.z)

                                # Only use calculated values if they're reasonable (not zero or extremely large)
                                if 0.1 < width < 50.0 and 0.1 < height < 50.0:
                                    door_width = width
                                    door_height = height
                                    logger.debug(
                                        f"[DOOR DEBUG] Extracted dimensions for door '{door_name}': {door_width:.2f} x {door_height:.2f} (from {mesh_count} meshes, model='{model_name}')"
                                    )
                                else:
                                    logger.warning(
                                        f"Calculated dimensions for door '{door_name}' out of range: {width:.2f} x {height:.2f}, using defaults"
                                    )
                            else:
                                logger.warning(
                                    f"Could not calculate bounding box for door '{door_name}' (processed {mesh_count} meshes), using defaults"
                                )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Error getting model or calculating dimensions for door '{door_name}': {e}")
        except Exception as e:  # noqa: BLE001
            # If we can't get dimensions from model, try texture-based fallback
            logger.warning(f"Failed to get dimensions from model for '{door_name}' using method 1: {e}")

        # Fallback: Get dimensions from door texture if model-based extraction failed
        if door_width == 2.0 and door_height == 3.0 and not model_extracted:
            try:
                # Try to get model using the same variations as before
                if model_name:
                    model_variations = [
                        model_name,
                        model_name.lower(),
                        model_name.upper(),
                        model_name.lower().replace(".mdl", "").replace(".mdx", ""),
                    ]
                    seen = set()
                    model_variations = [v for v in model_variations if v not in seen and not seen.add(v)]
                    
                    for model_var in model_variations:
                        try:
                            location_results = installation.locations(
                                [ResourceIdentifier(resname=model_var, restype=ResourceType.MDL)],
                                [
                                    SearchLocation.OVERRIDE,
                                    SearchLocation.MODULES,
                                    SearchLocation.CHITIN,
                                ],
                            )
                            for res_ident, loc_list in location_results.items():
                                if loc_list:
                                    loc = loc_list[0]
                                    with loc.filepath.open("rb") as f:
                                        f.seek(loc.offset)
                                        mdl_data = f.read(loc.size)
                                    mdl = read_mdl(mdl_data)
                                    model_extracted = True
                                    break
                            if model_extracted:
                                break
                        except Exception:  # noqa: BLE001
                            continue
                    
                    # Fallback to resource()
                    if not model_extracted:
                        for model_var in model_variations:
                            try:
                                mdl_result = installation.resource(model_var, ResourceType.MDL)
                    if mdl_result and mdl_result.data:
                        mdl = read_mdl(mdl_result.data)
                        model_extracted = True
                                    break
                            except Exception:  # noqa: BLE001
                                continue

                # Get textures from the model
                texture_names: list[str] = []
                if mdl and model_name:
                    # Try to get model data as bytes for iterate_textures
                    model_variations_fallback = [
                        model_name,
                        model_name.lower(),
                        model_name.upper(),
                        model_name.lower().replace(".mdl", "").replace(".mdx", ""),
                    ]
                    seen_fallback = set()
                    model_variations_fallback = [v for v in model_variations_fallback if v not in seen_fallback and not seen_fallback.add(v)]
                    
                    for model_var in model_variations_fallback:
                        try:
                            mdl_result_fallback = installation.resource(model_var, ResourceType.MDL)
                    if mdl_result_fallback and mdl_result_fallback.data:
                        texture_names = list(iterate_textures(mdl_result_fallback.data))
                                break
                        except Exception:  # noqa: BLE001
                            continue

                if texture_names:
                    # Try to load the first texture
                    texture_name = texture_names[0]
                    texture_result = installation.resource(texture_name, ResourceType.TPC)
                    if not texture_result:
                        # Try TGA as fallback
                        texture_result = installation.resource(texture_name, ResourceType.TGA)

                    if texture_result and texture_result.data:
                        # Read TPC to get dimensions
                        if texture_result.restype == ResourceType.TPC:
                            tpc = read_tpc(texture_result.data)
                            tex_width, tex_height = tpc.dimensions()
                        elif texture_result.restype == ResourceType.TGA:
                            # TGA header: width at offset 12, height at offset 14 (little-endian)
                            if len(texture_result.data) >= 18:
                                tex_width = int.from_bytes(texture_result.data[12:14], "little")
                                tex_height = int.from_bytes(texture_result.data[14:16], "little")
                            else:
                                tex_width = tex_height = 0
                        else:
                            tex_width = tex_height = 0

                        if tex_width > 0 and tex_height > 0:
                            # Convert texture pixels to world units
                            # Typical door textures are 256x512 or 512x1024 pixels
                            # Typical door dimensions are 2-6 units wide, 2.5-3.5 units tall
                            # Assuming 1 pixel ≈ 0.01-0.02 world units for doors
                            # Use aspect ratio to determine which dimension is width vs height
                            # Doors are typically taller than wide, so height > width
                            if tex_height > tex_width:
                                # Portrait orientation - height is vertical, width is horizontal
                                # Typical: 256x512 = 2.0x4.0, 512x1024 = 4.0x8.0
                                # Scale factor: ~0.008-0.01 units per pixel
                                scale_factor = 0.008  # Conservative estimate
                                door_width = tex_width * scale_factor
                                door_height = tex_height * scale_factor
                            else:
                                # Landscape or square - assume standard door proportions
                                # Use height as the primary dimension
                                scale_factor = 0.008
                                door_height = tex_height * scale_factor
                                # Width is typically 0.6-0.8x height for doors
                                door_width = door_height * 0.7

                            # Clamp to reasonable values
                            door_width = max(1.0, min(door_width, 10.0))
                            door_height = max(1.5, min(door_height, 10.0))
            except Exception:  # noqa: BLE001
                logger.exception(f"Texture fallback also failed, keep defaults for '{door_name}'")

        logger.debug(f"[DOOR DEBUG] Final dimensions for door '{door_name}': width={door_width:.2f}, height={door_height:.2f}")
        door_list.append({
            "utd_k1": f"{door_name}_k1",
            "utd_k2": f"{door_name}_k2",
            "width": door_width,
            "height": door_height,
        })

    # Write skybox files
    logger.info(f"Writing {len(skyboxes)} skyboxes...")
    for skybox_name, skybox_data in skyboxes.items():
        try:
            # Validate MDL file before writing
            try:
                mdl = read_mdl(skybox_data["mdl"])
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read MDL file for skybox '{skybox_name}': {e}")
                logger.debug(f"MDL data size: {len(skybox_data['mdl'])} bytes")
                raise
            
        (skyboxes_dir / f"{skybox_name}.mdl").write_bytes(skybox_data["mdl"])
        (skyboxes_dir / f"{skybox_name}.mdx").write_bytes(skybox_data["mdx"])
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to process skybox '{skybox_name}': {e}")
            logger.exception(f"Exception details for skybox '{skybox_name}'")
            # Continue with next skybox instead of aborting
            continue

    # Generate JSON file
    logger.info("Generating kit JSON file...")
    kit_json = {
        "name": module_name.replace("_", " ").title(),
        "id": kit_id,
        "ht": "2.0.2",
        "version": 1,
        "components": component_list,
        "doors": door_list,
    }

    json_path: Path = output_path / f"{kit_id}.json"
    with json_path.open("w", encoding="utf-8") as f:  # type: ignore[assignment]
        json.dump(kit_json, f, indent=4, ensure_ascii=False)  # type: ignore[arg-type]

    logger.info(f"Kit generation complete! Output: {output_path}")


def _generate_component_minimap(bwm: BWM):  # type: ignore[return-value]
    """Generate a minimap PNG image from a BWM walkmesh.

    Uses Qt (QImage) if available, otherwise falls back to Pillow (PIL Image).

    Args:
    ----
        bwm: BWM walkmesh object

    Returns:
    -------
        QImage or PIL.Image: Minimap image (top-down view of walkmesh)
    """
    if not QT_AVAILABLE and not PIL_AVAILABLE:
        raise ImportError("Neither Qt bindings nor Pillow available - cannot generate minimap")

    # Calculate bounding box
    vertices: list[Vector3] = list(bwm.vertices())
    if not vertices:
        # Empty walkmesh - return small blank image
        if QT_AVAILABLE:
            image = QImage(256, 256, QImage.Format.Format_RGB888)  # type: ignore[misc, call-overload]
            image.fill(QColor(0, 0, 0))  # type: ignore[misc, call-overload]
            return image
        else:
            return Image.new("RGB", (256, 256), (0, 0, 0))  # type: ignore[misc, call-overload]

    bbmin: Vector3 = Vector3(min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices))
    bbmax: Vector3 = Vector3(max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices))

    # Add padding
    padding: float = 5.0
    bbmin.x -= padding
    bbmin.y -= padding
    bbmax.x += padding
    bbmax.y += padding

    # Calculate image dimensions (scale: 10 pixels per unit)
    width: int = int((bbmax.x - bbmin.x) * 10)
    height: int = int((bbmax.y - bbmin.y) * 10)

    # Ensure minimum size
    width = max(width, 256)
    height = max(height, 256)

    # Transform to image coordinates (flip Y, scale, translate)
    def to_image_coords(v: Vector2) -> tuple[float, float]:
        x = (v.x - bbmin.x) * 10
        y = height - (v.y - bbmin.y) * 10  # Flip Y
        return x, y

    # Use Qt if available
    if importlib.util.find_spec("qtpy") is not None:
        # Create image
        q_image: QImage | Image = QImage(width, height, QImage.Format.Format_RGB888)  # type: ignore[misc, call-overload]
        q_image.fill(QColor(0, 0, 0))  # type: ignore[misc, call-overload]

        # Draw walkmesh faces
        painter = QPainter(q_image)  # type: ignore[misc, call-overload]
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # type: ignore[misc, attr-defined]

        # Draw walkable faces in white, non-walkable in gray
        for face in bwm.faces:
            # Determine if face is walkable based on material
            is_walkable = face.material.value in (1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22)
            color = QColor(255, 255, 255) if is_walkable else QColor(128, 128, 128)  # type: ignore[misc, call-overload]

            painter.setBrush(QColor(color))  # type: ignore[misc, call-overload]
            painter.setPen(QColor(color))  # type: ignore[misc, call-overload]

            # Build path from face vertices
            path = QPainterPath()  # type: ignore[misc, call-overload]
            v1 = Vector2(face.v1.x, face.v1.y)
            v2 = Vector2(face.v2.x, face.v2.y)
            v3 = Vector2(face.v3.x, face.v3.y)

            x1, y1 = to_image_coords(v1)
            x2, y2 = to_image_coords(v2)
            x3, y3 = to_image_coords(v3)

            path.moveTo(x1, y1)
            path.lineTo(x2, y2)
            path.lineTo(x3, y3)
            path.closeSubpath()

            painter.drawPath(path)

        painter.end()
        return q_image

    # Fallback to Pillow
    if importlib.util.find_spec("PIL") is not None:
        # Create image
        pil_image: Image = Image.new("RGB", (width, height), (0, 0, 0))  # type: ignore[misc, call-overload]
        draw: ImageDraw.Draw = ImageDraw.Draw(pil_image)  # type: ignore[misc, call-overload]

        # Draw walkable faces in white, non-walkable in gray
        for face in bwm.faces:
            # Determine if face is walkable based on material
            is_walkable = face.material.value in (1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22)
            color = (255, 255, 255) if is_walkable else (128, 128, 128)

            # Get face vertices
            v1 = Vector2(face.v1.x, face.v1.y)
            v2 = Vector2(face.v2.x, face.v2.y)
            v3 = Vector2(face.v3.x, face.v3.y)

            x1, y1 = to_image_coords(v1)
            x2, y2 = to_image_coords(v2)
            x3, y3 = to_image_coords(v3)

            # Draw polygon (triangle)
            draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill=color, outline=color)

        return pil_image

    raise ImportError("Neither Qt bindings nor Pillow available - cannot generate minimap")


def _extract_doorhooks_from_bwm(bwm: BWM, num_doors: int) -> list[dict[str, float | int]]:
    """Extract doorhook positions from BWM edges with transitions.

    Args:
    ----
        bwm: BWM walkmesh object
        num_doors: Number of doors in the kit (for door index)

    Returns:
    -------
        list[dict[str, float | int]]: List of doorhook dictionaries with x, y, z, rotation, door, edge
    """
    doorhooks: list[dict[str, float | int]] = []

    # Get all perimeter edges (these are the edges with transitions)
    edges: list[BWMEdge] = bwm.edges()

    # Process edges with valid transitions
    for edge in edges:
        if edge.transition < 0:  # Skip edges without transitions
            continue

        face: BWMFace = edge.face
        # Get edge vertices based on local edge index (0, 1, or 2)
        # edge.index is the global edge index (face_index * 3 + local_edge_index)
        _face_index: int = edge.index // 3
        local_edge_index: int = edge.index % 3

        # Get vertices for this edge
        if local_edge_index == 0:
            v1 = face.v1
            v2 = face.v2
        elif local_edge_index == 1:
            v1 = face.v2
            v2 = face.v3
        else:  # local_edge_index == 2
            v1 = face.v3
            v2 = face.v1

        # Calculate midpoint of edge
        mid_x: float = (v1.x + v2.x) / 2.0
        mid_y: float = (v1.y + v2.y) / 2.0
        mid_z: float = (v1.z + v2.z) / 2.0

        # Calculate rotation (angle of edge in XY plane, in degrees)
        dx: float = v2.x - v1.x
        dy: float = v2.y - v1.y
        rotation = math.degrees(math.atan2(dy, dx))
        # Normalize to 0-360
        rotation = rotation % 360
        if rotation < 0:
            rotation += 360

        # Map transition index to door index
        # Transition indices typically map directly to door indices, but clamp to valid range
        door_index: int = min(edge.transition, num_doors - 1) if num_doors > 0 else 0

        doorhooks.append({
            "x": mid_x,
            "y": mid_y,
            "z": mid_z,
            "rotation": rotation,
            "door": door_index,
            "edge": edge.index,  # Global edge index
        })

    return doorhooks
