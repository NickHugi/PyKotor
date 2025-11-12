#!/usr/bin/env python3
from __future__ import annotations

import shutil

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.common.module import Module
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_mod_file
from pykotor.tools.model import iterate_lightmaps, iterate_textures

if TYPE_CHECKING:
    from pykotor.common.misc import ResRef
    from pykotor.common.module import ModuleResource
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.gff.gff_data import GFF


class ResourceInfo:
    def __init__(self):
        self.modules: set[str] = set()  # Modules where the resource appears
        self.file_resources: list[FileResource] = []  # FileResource instances across all locations
        self.is_missing: bool = False  # Whether the resource is missing
        self.is_unused: bool = False  # Whether the resource is unused
        self.dependent_resources: set[ResourceIdentifier] = set()  # Other resources this one depends on
        self.resource_hashes: dict[str, str] = {}  # Hashes of the resource data (e.g., SHA-256)
        self.impact_of_missing: str | None = None  # Impact description if the resource is missing


class ModuleManager:
    def __init__(self, installation: Installation):
        """Initializes the ModuleManager with a given game installation.

        Args:
            installation (Installation): The game installation instance.
        """
        self.installation: Installation = installation
        self.resources_info: dict[ResourceIdentifier, ResourceInfo] = {}
        self.conflicting_resources: dict[ResourceIdentifier, set[str]] = defaultdict(set)
        self.missing_resources: dict[str, list[ResourceIdentifier]] = defaultdict(list)
        self.unused_resources: dict[str, list[ResourceIdentifier]] = defaultdict(list)
        self.resource_to_modules: dict[str, set[str]] = defaultdict(set)

    def analyze_modules(self, modules: list[Module]) -> None:
        """Analyzes a list of Module objects and stores relevant information.

        Args:
            modules (list[Module]): A list of Module objects to analyze.
        """
        for module in modules:
            module_name: str = module.root()
            print(f"Analyzing module '{module_name}'...")

            # First Pass: Collect Resource Information
            for identifier, mod_res in module.resources.items():
                resource_info: ResourceInfo = self.resources_info.setdefault(identifier, ResourceInfo())
                resource_info.modules.add(module_name)

                # Create FileResource instances for each location and add them to the resource info
                for location in mod_res.locations():
                    file_resource = FileResource(
                        resname=mod_res.resname(),
                        restype=mod_res.restype(),
                        size=location.stat().st_size,
                        offset=0,  # Assuming no offset for simplicity
                        filepath=location,
                    )
                    resource_info.file_resources.append(file_resource)
                    resource_hash: str = file_resource.get_sha1_hash()
                    resource_info.resource_hashes[file_resource.filepath().as_posix()] = resource_hash

                # Check for unused resources
                if not mod_res.isActive():
                    resource_info.is_unused = True

                # If the resource data is missing, mark it as missing
                if not mod_res.data():
                    resource_info.is_missing = True
                    resource_info.impact_of_missing = "Critical resource missing, could impact module functionality."

            # Second Pass: Identify Dependencies and Conflicts
            for identifier, mod_res in module.resources.items():
                resource_info = self.resources_info[identifier]

                # Find dependencies within the module
                dependent_resources: set[ResourceIdentifier] = self._find_dependencies(module, mod_res)
                resource_info.dependent_resources.update(dependent_resources)

                # Check for resource conflicts across multiple modules
                if len(resource_info.modules) > 1:
                    self.conflicting_resources[identifier].update(resource_info.modules)

    def _find_dependencies(self, module: Module, mod_res: ModuleResource) -> set[ResourceIdentifier]:
        """Finds and returns a set of resources that the given ModuleResource depends on.

        Args:
            module (Module): The module object being analyzed.
            mod_res: A ModuleResource instance from a Module.

        Returns:
            Set[ResourceIdentifier]: A set of dependent resources.
        """
        dependencies = set()

        # Search for linked resources like GIT, LYT, VIS
        if mod_res.restype() in {ResourceType.GIT, ResourceType.LYT, ResourceType.VIS}:
            linked_resources: set[ResourceIdentifier] = self._search_linked_resources(module, mod_res)
            dependencies.update(linked_resources)

        # Extract dependencies from GFF files
        if mod_res.restype() in {ResourceType.GFF, ResourceType.ARE, ResourceType.IFO, ResourceType.DLG}:
            dependencies.update(self._extract_references_from_gff(mod_res.data()))

        # Extract texture and model dependencies
        if mod_res.restype() in {ResourceType.MDL, ResourceType.MDX}:
            model_data: bytes | None = mod_res.data()
            dependencies.update(self._extract_references_from_model(model_data))

        return dependencies

    def _search_linked_resources(self, module: Module, mod_res: ModuleResource) -> set[ResourceIdentifier]:
        """Searches for linked resources in GIT, LYT, VIS and related files.

        Args:
            module (Module): The module being analyzed.
            mod_res (ModuleResource): The resource being analyzed.

        Returns:
            Set[ResourceIdentifier]: A set of linked resources.
        """
        link_resname: ResRef | None = module.module_id()
        linked_resources = set()

        queries: list[ResourceIdentifier] = [
            ResourceIdentifier(link_resname, ResourceType.LYT),
            ResourceIdentifier(link_resname, ResourceType.GIT),
            ResourceIdentifier(link_resname, ResourceType.VIS),
        ]

        search_results = module._search_resource_locations(module, queries)
        for query, locations in search_results.items():
            for _location in locations:
                linked_resources.add(query)

        return linked_resources

    def _extract_references_from_gff(self, data: bytes) -> set[ResourceIdentifier]:
        """Extracts resource references from GFF-based data.

        Args:
            data (bytes): GFF data from the resource.

        Returns:
            Set[ResourceIdentifier]: Set of found resource identifiers.
        """
        references = set()
        gff: GFF = read_gff(data)

        # Traverse GFF fields looking for references to other resources
        for field in gff.fields():
            if field.type == GFFFieldType.ResRef:
                resref: ResRef = field.value
                references.add(ResourceIdentifier(resref.get(), ResourceType.UNKNOWN))  # ResourceType.UNKNOWN is a placeholder
        return references

    def _extract_references_from_model(self, model_data: bytes) -> set[ResourceIdentifier]:
        """Extracts resource references from model data."""
        lookup_texture_queries = set()

        try:
            lookup_texture_queries.update(iterate_textures(model_data))
            lookup_texture_queries.update(iterate_lightmaps(model_data))
        except Exception as e:  # noqa: BLE001
            print(f"Warning: Failed to extract texture/lightmap references: {e}")

        return {ResourceIdentifier(texture, ResourceType.TGA) for texture in lookup_texture_queries}

    def summarize(self) -> None:
        """Prints a summary of the analysis including conflicts, missing resources, and unused resources."""
        print("\nSummary:")
        print("--------")

        if self.resources_info:
            print("\nResources Information:")
            for identifier, info in self.resources_info.items():
                print(f"Resource '{identifier}':")
                print(f"  - Appears in modules: {', '.join(info.modules)}")
                if info.is_missing:
                    print("  - Status: Missing")
                    if info.impact_of_missing:
                        print(f"  - Impact: {info.impact_of_missing}")
                elif info.is_unused:
                    print("  - Status: Unused")
                if info.dependent_resources:
                    print(f"  - Depends on: {', '.join(map(str, info.dependent_resources))}")
                if len(info.modules) > 1:
                    print("  - Conflict: Appears in multiple modules")
                print(f"  - File Resources: {len(info.file_resources)} instances found.")
                print(f"  - Resource Hashes: {info.resource_hashes}")

        if self.conflicting_resources:
            print("\nConflicting Resources:")
            for resname, modules in self.conflicting_resources.items():
                print(f"Resource '{resname}' found in modules: {', '.join(modules)}")

    def extract_all_resources(self, module_name: str, output_dir: str) -> None:
        """Extracts all resources from the specified module and saves them into a subfolder named after the module.

        Args:
            module_name (str): The name of the module to extract resources from.
            output_dir (str): The directory where the module subfolder will be created.
        """
        module = Module(module_name, self.installation, use_dot_mod=is_mod_file(module_name))
        module_dir = Path(output_dir) / module_name
        module_dir.mkdir(parents=True, exist_ok=True)

        print(f"Extracting resources from module '{module_name}' to '{module_dir}'...")

        for identifier, mod_res in module.resources.items():
            resource_data: bytes | None = mod_res.data()
            if resource_data is None:
                print(f"Missing resource: {identifier}")
                self.missing_resources[module_name].append(identifier)
                continue

            resource_filename: str = f"{identifier.resname}.{identifier.restype.extension}"
            resource_path: Path = module_dir / resource_filename

            try:
                with resource_path.open("wb") as file:
                    file.write(resource_data)
                print(f"Extracted: {resource_filename}")
            except Exception as e:  # noqa: BLE001
                print(f"Failed to extract {resource_filename}: {e}")

    def build_resource_to_modules_mapping(self) -> None:
        """Builds a mapping from resource names to the modules they are found in."""
        print("Building resource to modules mapping...")
        module_names: dict[str, str] = self.installation.module_names()
        for module_name in module_names:
            module = Module(module_name, self.installation, use_dot_mod=is_mod_file(module_name))
            for identifier in module.resources:
                self.resource_to_modules[identifier.resname.lower()].add(module_name)

    def check_for_conflicts(self) -> None:
        """Identifies resources with identical names across different modules and records the conflicts."""
        if not self.resource_to_modules:
            self.build_resource_to_modules_mapping()

        print("Checking for conflicting resources across modules...")
        for resname, modules in self.resource_to_modules.items():
            if len(modules) > 1:
                self.conflicting_resources[resname] = modules
                print(f"Conflict: Resource '{resname}' found in modules {modules}")

    def find_missing_resources(self, module_name: str) -> None:
        """Identifies missing resources within the specified module.

        Args:
            module_name (str): The name of the module to check.
        """
        module = Module(module_name, self.installation, use_dot_mod=is_mod_file(module_name))
        print(f"Checking for missing resources in module '{module_name}'...")

        for identifier, mod_res in module.resources.items():
            if mod_res.data() is None:
                self.missing_resources[module_name].append(identifier)
                print(f"Missing resource: {identifier}")

    def find_unused_resources(self, module_name: str) -> None:
        """Identifies unused resources within the specified module.

        Args:
            module_name (str): The name of the module to check.
        """
        module = Module(module_name, self.installation, use_dot_mod=is_mod_file(module_name))
        print(f"Checking for unused resources in module '{module_name}'...")

        # Assuming that ModuleResource has a method or property 'is_active' to determine usage
        for identifier, mod_res in module.resources.items():
            if not mod_res.is_active():
                self.unused_resources[module_name].append(identifier)
                print(f"Unused resource: {identifier}")

    def move_override_to_modules(self, override_dir: str, output_dir: str) -> None:
        """Moves resources from the override directory into their respective module folders.
        If a resource belongs to multiple modules, it is duplicated.

        Args:
            override_dir (str): The path to the override directory containing global resources.
            output_dir (str): The base directory where module subfolders are located.
        """
        override_path = Path(override_dir)
        if not override_path.exists() or not override_path.is_dir():
            print(f"Override directory '{override_dir}' does not exist.")
            return

        if not self.resource_to_modules:
            self.build_resource_to_modules_mapping()

        print(f"Moving resources from override directory '{override_dir}' to module folders...")

        for resource_file in override_path.iterdir():
            if resource_file.is_file():
                resname: str = resource_file.stem
                restype: ResourceType = ResourceType.from_extension(resource_file.suffix[1:])  # Remove the dot
                identifier = ResourceIdentifier(resname, restype)

                modules: set[str] = self.resource_to_modules.get(resname.lower(), set())
                if not modules:
                    print(f"Resource '{resource_file.name}' does not belong to any module.")
                    continue

                for module_name in modules:
                    module_dir: Path = Path(output_dir) / module_name
                    module_dir.mkdir(parents=True, exist_ok=True)
                    destination: Path = module_dir / resource_file.name

                    try:
                        shutil.copy2(resource_file, destination)
                        print(f"Copied '{resource_file.name}' to '{destination}'.")
                    except Exception as e:  # noqa: BLE001
                        print(f"Failed to copy '{resource_file.name}' to '{destination}': {e}")

    def summarize(self) -> None:
        """Prints a summary of the missing, unused, and conflicting resources."""
        print("\nSummary:")
        print("--------")

        if self.missing_resources:
            print("\nMissing Resources:")
            for module, resources in self.missing_resources.items():
                print(f"Module '{module}':")
                for res in resources:
                    print(f"  - {res}")
        else:
            print("\nNo missing resources found.")

        if self.unused_resources:
            print("\nUnused Resources:")
            for module, resources in self.unused_resources.items():
                print(f"Module '{module}':")
                for res in resources:
                    print(f"  - {res}")
        else:
            print("\nNo unused resources found.")

        if self.conflicting_resources:
            print("\nConflicting Resources:")
            for resname, modules in self.conflicting_resources.items():
                print(f"Resource '{resname}' found in modules: {', '.join(modules)}")
        else:
            print("\nNo conflicting resources found.")
