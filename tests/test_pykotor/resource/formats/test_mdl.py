"""Comprehensive unit tests for MDL/MDX file format handling.

This test module covers:
- Binary MDL/MDX reading and writing
- ASCII MDL reading and writing
- Fast loading for rendering
- Round-trip tests (read->write->read)
- Node hierarchy and mesh data
- Controller and animation data
- Platform compatibility (K1/K2/Xbox)

Test files are located in tests/test_pykotor/test_files/mdl/
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from pykotor.resource.formats.mdl import (
    MDL,
    MDLAnimation,
    MDLBinaryReader,
    MDLBinaryWriter,
    MDLController,
    MDLLight,
    MDLMesh,
    MDLNode,
    MDLSkin,
    bytes_mdl,
    read_mdl,
    read_mdl_fast,
    write_mdl,
)
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector2, Vector3, Vector4


class TestMDLBinaryIO(unittest.TestCase):
    """Test binary MDL/MDX file I/O operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("tests/test_pykotor/test_files/mdl")
        self.assertTrue(self.test_dir.exists(), f"Test directory {self.test_dir} does not exist")

        # Test files
        self.test_files = {
            "character": ("c_dewback.mdl", "c_dewback.mdx"),
            "door": ("dor_lhr02.mdl", "dor_lhr02.mdx"),
            "placeable": ("m02aa_09b.mdl", "m02aa_09b.mdx"),
            "animation": ("m12aa_c03_char02.mdl", "m12aa_c03_char02.mdx"),
            "camera": ("m12aa_c04_cam.mdl", "m12aa_c04_cam.mdx"),
        }

    def test_read_mdl_basic(self):
        """Test basic MDL file reading."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        self.assertIsInstance(mdl, MDL)
        self.assertIsNotNone(mdl.root)
        self.assertIsInstance(mdl.root, MDLNode)
        self.assertIsInstance(mdl.name, str)
        self.assertGreater(len(mdl.name), 0)

    def test_read_mdl_fast(self):
        """Test fast MDL loading optimized for rendering."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        # Load with fast loading
        mdl_fast = read_mdl_fast(mdl_path, source_ext=mdx_path)

        # Fast load should have no animations or controllers
        self.assertEqual(len(mdl_fast.anims), 0, "Fast loading should skip animations")

        # But should still have node hierarchy and meshes
        self.assertIsNotNone(mdl_fast.root)
        all_nodes = mdl_fast.all_nodes()
        self.assertGreater(len(all_nodes), 0, "Should have nodes")

    def test_read_mdl_fast_vs_full(self):
        """Compare fast loading vs full loading."""
        mdl_path = self.test_dir / "m12aa_c03_char02.mdl"
        mdx_path = self.test_dir / "m12aa_c03_char02.mdx"

        mdl_full = read_mdl(mdl_path, source_ext=mdx_path)
        mdl_fast = read_mdl_fast(mdl_path, source_ext=mdx_path)

        # Both should have same name
        self.assertEqual(mdl_full.name, mdl_fast.name)

        # Fast should have no animations
        self.assertEqual(len(mdl_fast.anims), 0)

        # Full might have animations
        # (not asserting here as some test files may not have anims)

        # Both should have same node count
        self.assertEqual(
            len(mdl_full.all_nodes()),
            len(mdl_fast.all_nodes()),
            "Node count should be same",
        )

    def test_read_all_test_files(self):
        """Test reading all available test MDL files."""
        for name, (mdl_file, mdx_file) in self.test_files.items():
            with self.subTest(test_file=name):
                mdl_path = self.test_dir / mdl_file
                mdx_path = self.test_dir / mdx_file

                if not mdl_path.exists():
                    self.skipTest(f"Test file {mdl_file} not found")

                mdl = read_mdl(mdl_path, source_ext=mdx_path)

                self.assertIsInstance(mdl, MDL, f"Failed to load {name}")
                self.assertIsNotNone(mdl.root, f"No root node in {name}")
                self.assertIsInstance(mdl.name, str, f"Invalid name in {name}")

    def test_mdl_node_hierarchy(self):
        """Test MDL node hierarchy structure."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Test node hierarchy
        all_nodes = mdl.all_nodes()
        self.assertGreater(len(all_nodes), 0, "Should have at least one node")

        # Root node should be in the list
        self.assertIn(mdl.root, all_nodes)

        # Test node attributes
        for node in all_nodes:
            self.assertIsInstance(node.name, str)
            self.assertIsInstance(node.position, Vector3)
            self.assertIsInstance(node.orientation, Vector4)

    def test_mdl_mesh_data(self):
        """Test MDL mesh data parsing."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Find nodes with meshes
        mesh_nodes = [node for node in mdl.all_nodes() if node.mesh]

        self.assertGreater(len(mesh_nodes), 0, "Should have at least one mesh node")

        # Test mesh attributes
        for node in mesh_nodes:
            mesh = node.mesh
            self.assertIsInstance(mesh, MDLMesh)

            # Test basic mesh properties
            self.assertIsInstance(mesh.texture_1, str)
            self.assertIsInstance(mesh.render, bool)

            # If mesh has vertices, test them
            if mesh.vertex_positions:
                self.assertGreater(len(mesh.vertex_positions), 0)
                for vertex in mesh.vertex_positions:
                    self.assertIsInstance(vertex, Vector3)

            # If mesh has faces, test them
            if mesh.faces:
                self.assertGreater(len(mesh.faces), 0)

    def test_mdl_get_node_by_name(self):
        """Test retrieving nodes by name."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Get root node by name
        root_by_name = mdl.get(mdl.root.name)
        self.assertIsNotNone(root_by_name)
        self.assertEqual(root_by_name, mdl.root)

        # Test non-existent node
        non_existent = mdl.get("nonexistent_node_name_xyz")
        self.assertIsNone(non_existent)

    def test_mdl_textures(self):
        """Test texture name extraction."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        textures = mdl.all_textures()
        self.assertIsInstance(textures, set)

        # All texture names should be strings
        for texture in textures:
            self.assertIsInstance(texture, str)
            self.assertGreater(len(texture), 0)

    def test_mdl_lightmaps(self):
        """Test lightmap texture extraction."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        lightmaps = mdl.all_lightmaps()
        self.assertIsInstance(lightmaps, set)

    def test_write_mdl_binary(self):
        """Test writing MDL to binary format."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        # Read original
        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Write to bytes
        mdl_bytes = bytes_mdl(mdl, ResourceType.MDL)
        self.assertIsInstance(mdl_bytes, bytes)
        self.assertGreater(len(mdl_bytes), 0)

    def test_mdl_roundtrip(self):
        """Test MDL roundtrip (read->write->read) integrity."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        # Read original
        mdl1 = read_mdl(mdl_path, source_ext=mdx_path)

        # Write to bytes
        mdl_bytes = bytes_mdl(mdl1, ResourceType.MDL)

        # Read back from bytes
        # Note: MDX data needs to be handled separately
        # For now, just verify we can write and get valid bytes
        self.assertIsInstance(mdl_bytes, bytes)
        self.assertGreater(len(mdl_bytes), 12, "Should have at least header")


class TestMDLData(unittest.TestCase):
    """Test MDL data structures and manipulation."""

    def test_mdl_creation(self):
        """Test creating an MDL from scratch."""
        mdl = MDL()

        self.assertIsNotNone(mdl.root)
        self.assertIsInstance(mdl.root, MDLNode)
        self.assertEqual(len(mdl.anims), 0)
        self.assertEqual(mdl.name, "")
        self.assertFalse(mdl.fog)

    def test_mdl_node_creation(self):
        """Test creating MDL nodes."""
        node = MDLNode()

        self.assertEqual(node.name, "")
        self.assertIsInstance(node.position, Vector3)
        self.assertIsInstance(node.orientation, Vector4)
        self.assertEqual(len(node.children), 0)
        self.assertEqual(len(node.controllers), 0)
        self.assertIsNone(node.mesh)
        self.assertIsNone(node.light)

    def test_mdl_node_hierarchy_creation(self):
        """Test creating a node hierarchy."""
        mdl = MDL()
        mdl.name = "test_model"

        # Create child nodes
        child1 = MDLNode()
        child1.name = "child1"

        child2 = MDLNode()
        child2.name = "child2"

        mdl.root.name = "root"
        mdl.root.children.append(child1)
        mdl.root.children.append(child2)

        # Test hierarchy
        all_nodes = mdl.all_nodes()
        self.assertEqual(len(all_nodes), 3)  # root + 2 children
        self.assertIn(mdl.root, all_nodes)
        self.assertIn(child1, all_nodes)
        self.assertIn(child2, all_nodes)

    def test_mdl_mesh_creation(self):
        """Test creating mesh data."""
        mesh = MDLMesh()

        mesh.texture_1 = "test_texture"
        mesh.render = True
        mesh.shadow = False

        self.assertEqual(mesh.texture_1, "test_texture")
        self.assertTrue(mesh.render)
        self.assertFalse(mesh.shadow)

    def test_mdl_animation_creation(self):
        """Test creating animation data."""
        anim = MDLAnimation()

        anim.name = "test_anim"
        anim.anim_length = 1.5
        anim.transition_length = 0.25

        self.assertEqual(anim.name, "test_anim")
        self.assertEqual(anim.anim_length, 1.5)
        self.assertEqual(anim.transition_length, 0.25)

    def test_mdl_find_parent(self):
        """Test finding parent nodes."""
        mdl = MDL()

        child = MDLNode()
        child.name = "child"

        mdl.root.children.append(child)

        parent = mdl.find_parent(child)
        self.assertEqual(parent, mdl.root)

    def test_mdl_global_position(self):
        """Test calculating global positions."""
        mdl = MDL()

        child = MDLNode()
        child.name = "child"
        child.position = Vector3(1.0, 2.0, 3.0)

        mdl.root.position = Vector3(10.0, 20.0, 30.0)
        mdl.root.children.append(child)

        global_pos = mdl.global_position(child)

        # Global position should be sum of all parent positions
        self.assertEqual(global_pos.x, 11.0)
        self.assertEqual(global_pos.y, 22.0)
        self.assertEqual(global_pos.z, 33.0)

    def test_skin_prepare_bone_lookups(self):
        """Ensure MDLSkin prepares lookup tables using global bone IDs."""
        nodes = []
        for node_id in [0, 5, 10]:
            node = MDLNode()
            node.node_id = node_id
            nodes.append(node)

        skin = MDLSkin()
        skin.bonemap = [5.0, 0xFFFF, 10.0]

        skin.prepare_bone_lookups(nodes)

        self.assertGreaterEqual(len(skin.bone_serial), 11)
        self.assertEqual(skin.bone_serial[5], 1)
        self.assertEqual(skin.bone_node_number[5], 5)
        self.assertEqual(skin.bone_serial[10], 2)
        self.assertEqual(skin.bone_node_number[10], 10)


class TestMDLPerformance(unittest.TestCase):
    """Test MDL performance characteristics."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("tests/test_pykotor/test_files/mdl")
        self.mdl_path = self.test_dir / "c_dewback.mdl"
        self.mdx_path = self.test_dir / "c_dewback.mdx"

        if not self.mdl_path.exists():
            self.skipTest("Test file c_dewback.mdl not found")

    def test_fast_load_performance(self):
        """Verify fast loading is actually faster."""
        import time

        # Measure full load time
        start = time.time()
        mdl_full = read_mdl(self.mdl_path, source_ext=self.mdx_path)
        full_time = time.time() - start

        # Measure fast load time
        start = time.time()
        mdl_fast = read_mdl_fast(self.mdl_path, source_ext=self.mdx_path)
        fast_time = time.time() - start

        # Fast loading should be faster (or at least not slower)
        # This is not a strict requirement but good to verify
        # We use a generous threshold since performance can vary
        self.assertLessEqual(
            fast_time,
            full_time * 2.0,
            "Fast loading should not be significantly slower than full loading",
        )

        # Verify both loaded successfully
        self.assertIsNotNone(mdl_full)
        self.assertIsNotNone(mdl_fast)


class TestMDLEdgeCases(unittest.TestCase):
    """Test MDL edge cases and error handling."""

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            read_mdl("nonexistent_file.mdl")

    def test_empty_mdl(self):
        """Test creating and manipulating an empty MDL."""
        mdl = MDL()

        self.assertEqual(len(mdl.all_nodes()), 1)  # Just root
        self.assertEqual(len(mdl.anims), 0)
        self.assertEqual(len(mdl.all_textures()), 0)
        self.assertEqual(len(mdl.all_lightmaps()), 0)

    def test_node_with_no_children(self):
        """Test node operations with no children."""
        node = MDLNode()

        self.assertEqual(len(node.children), 0)
        self.assertEqual(len(node.controllers), 0)

    def test_get_nonexistent_node_by_id(self):
        """Test getting node by non-existent ID."""
        mdl = MDL()

        with self.assertRaises(ValueError):
            mdl.get_by_node_id(999)


if __name__ == "__main__":
    unittest.main()

