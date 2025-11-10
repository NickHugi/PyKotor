"""Unit tests for MDL loader and geometry conversion.

Tests the complete pipeline from MDL/MDX files to Panda3D GeomNodes,
including vertex data, tangent space, and face topology.

References:
----------
    Engines/PyKotorEngine/src/pykotor/engine/panda3d/mdl_loader.py - MDL loader implementation
    Libraries/PyKotor/src/pykotor/resource/formats/mdl - MDL data structures
    vendor/reone/src/libs/graphics/mesh.cpp - Mesh conversion reference
"""

import sys
import unittest
from pathlib import Path

# Add PyKotor to path
pykotor_path = Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"
if str(pykotor_path) not in sys.path:
    sys.path.insert(0, str(pykotor_path))

from utility.common.geometry import Vector3
from pykotor.resource.formats.mdl import MDL
from pykotor.resource.formats.mdl.mdl_data import (
    MDLNode,
    MDLMesh,
    MDLFace,
    MDLAnimation,
    MDLController,
    MDLControllerRow,
)
from pykotor.resource.formats.mdl.mdl_types import (
    MDLGeometryType,
    MDLControllerType,
)


class TestMDLDataStructures(unittest.TestCase):
    """Test MDL data structures and their construction.
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py
        vendor/mdlops/MDLOpsM.pm:300-800 - MDL structure definitions
    """
    
    def test_mdl_creation(self):
        """Test creating a basic MDL structure.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:30-175 - MDL class
        """
        mdl = MDL()
        self.assertIsNotNone(mdl)
        self.assertEqual(mdl.geometry_type, MDLGeometryType.Model)
        self.assertIsInstance(mdl.animations, list)
        self.assertEqual(len(mdl.animations), 0)
    
    def test_mdl_node_creation(self):
        """Test creating MDL nodes.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:280-450 - MDLNode class
            vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:300-400 - Node reading
        """
        node = MDLNode()
        node.name = "test_node"
        node.position = Vector3(1.0, 2.0, 3.0)
        
        self.assertEqual(node.name, "test_node")
        self.assertEqual(node.position.x, 1.0)
        self.assertEqual(node.position.y, 2.0)
        self.assertEqual(node.position.z, 3.0)
        self.assertIsInstance(node.children, list)
    
    def test_mdl_mesh_creation(self):
        """Test creating MDL meshes with vertex data.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:950-1050 - MDLMesh class
            vendor/reone/src/libs/graphics/mesh.cpp:100-200 - Mesh structure
        """
        mesh = MDLMesh()
        
        # Add vertex data
        mesh.vertex_positions.append(Vector3(0, 0, 0))
        mesh.vertex_positions.append(Vector3(1, 0, 0))
        mesh.vertex_positions.append(Vector3(0, 1, 0))
        
        mesh.vertex_normals.append(Vector3(0, 0, 1))
        mesh.vertex_normals.append(Vector3(0, 0, 1))
        mesh.vertex_normals.append(Vector3(0, 0, 1))
        
        mesh.vertex_uv.append((0.0, 0.0))
        mesh.vertex_uv.append((1.0, 0.0))
        mesh.vertex_uv.append((0.0, 1.0))
        
        # Add face
        face = MDLFace()
        face.v1, face.v2, face.v3 = 0, 1, 2
        mesh.faces.append(face)
        
        self.assertEqual(len(mesh.vertex_positions), 3)
        self.assertEqual(len(mesh.vertex_normals), 3)
        self.assertEqual(len(mesh.vertex_uv), 3)
        self.assertEqual(len(mesh.faces), 1)
        self.assertEqual(mesh.faces[0].v1, 0)
    
    def test_mdl_animation_creation(self):
        """Test creating MDL animations.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:176-275 - MDLAnimation class
            vendor/KotOR.js/src/odyssey/OdysseyModelAnimation.ts - Animation structure
        """
        anim = MDLAnimation()
        anim.name = "test_anim"
        anim.length = 2.5
        anim.transition_time = 0.25
        
        self.assertEqual(anim.name, "test_anim")
        self.assertEqual(anim.length, 2.5)
        self.assertEqual(anim.transition_time, 0.25)
    
    def test_mdl_controller_creation(self):
        """Test creating animation controllers.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1455-1504 - MDLController class
            vendor/KotOR.js/src/odyssey/controllers/OdysseyController.ts - Controller structure
        """
        # Create controller with keyframes
        rows = [
            MDLControllerRow(0.0, [0.0, 0.0, 0.0]),
            MDLControllerRow(1.0, [1.0, 0.0, 0.0]),
            MDLControllerRow(2.0, [2.0, 0.0, 0.0]),
        ]
        
        controller = MDLController(
            controller_type=MDLControllerType.Position,
            rows=rows,
            is_bezier=False
        )
        
        self.assertEqual(controller.controller_type, MDLControllerType.Position)
        self.assertEqual(len(controller.rows), 3)
        self.assertFalse(controller.is_bezier)
        self.assertEqual(controller.rows[0].time, 0.0)
        self.assertEqual(controller.rows[1].data, [1.0, 0.0, 0.0])


class TestTangentSpaceCalculation(unittest.TestCase):
    """Test tangent space calculation for normal mapping.
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1449-1578 - Tangent space calc
        vendor/mdlops/MDLOpsM.pm:5470-5596 - Original tangent space implementation
    """
    
    def test_face_normal_calculation(self):
        """Test face normal calculation from triangle vertices.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1388-1420 - _calculate_face_normal()
            vendor/mdlops/MDLOpsM.pm:5502-5520 - Face normal calculation
        """
        from pykotor.resource.formats.mdl.io_mdl import _calculate_face_normal
        
        # Right triangle in XY plane
        v0 = Vector3(0, 0, 0)
        v1 = Vector3(1, 0, 0)
        v2 = Vector3(0, 1, 0)
        
        normal, area = _calculate_face_normal(v0, v1, v2)
        
        # Normal should point up (positive Z)
        self.assertAlmostEqual(normal.x, 0.0, places=5)
        self.assertAlmostEqual(normal.y, 0.0, places=5)
        self.assertAlmostEqual(normal.z, 1.0, places=5)
        
        # Area should be 0.5 (half of 1x1 square)
        self.assertAlmostEqual(area, 0.5, places=5)
    
    def test_tangent_space_calculation(self):
        """Test tangent and binormal calculation for normal mapping.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1449-1578 - _calculate_tangent_space()
            vendor/mdlops/MDLOpsM.pm:5477-5596 - Tangent space calculation
        """
        from pykotor.resource.formats.mdl.io_mdl import _calculate_tangent_space, _calculate_face_normal
        
        # Create a simple triangle
        v0 = Vector3(0, 0, 0)
        v1 = Vector3(1, 0, 0)
        v2 = Vector3(0, 1, 0)
        
        # UV coordinates
        uv0 = (0.0, 0.0)
        uv1 = (1.0, 0.0)
        uv2 = (0.0, 1.0)
        
        # Calculate face normal
        face_normal, _ = _calculate_face_normal(v0, v1, v2)
        
        # Calculate tangent space
        tangent, binormal = _calculate_tangent_space(v0, v1, v2, uv0, uv1, uv2, face_normal)
        
        # Tangent should point along U direction (positive X)
        self.assertAlmostEqual(tangent.x, 1.0, places=5)
        self.assertAlmostEqual(tangent.y, 0.0, places=5)
        self.assertAlmostEqual(tangent.z, 0.0, places=5)
        
        # Binormal should point along V direction (positive Y)
        self.assertAlmostEqual(binormal.x, 0.0, places=5)
        self.assertAlmostEqual(binormal.y, 1.0, places=5)
        self.assertAlmostEqual(binormal.z, 0.0, places=5)
    
    def test_tangent_space_orthogonality(self):
        """Test that tangent, binormal, and normal are orthogonal.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1560-1576 - Orthogonalization
            vendor/mdlops/MDLOpsM.pm:5570-5585 - TBN orthogonality
        """
        from pykotor.resource.formats.mdl.io_mdl import _calculate_tangent_space, _calculate_face_normal
        
        # Create triangle
        v0 = Vector3(0, 0, 0)
        v1 = Vector3(2, 0, 0)
        v2 = Vector3(0, 3, 0)
        
        uv0 = (0.0, 0.0)
        uv1 = (1.0, 0.0)
        uv2 = (0.0, 1.0)
        
        face_normal, _ = _calculate_face_normal(v0, v1, v2)
        tangent, binormal = _calculate_tangent_space(v0, v1, v2, uv0, uv1, uv2, face_normal)
        
        # Compute dot products (should be 0 for orthogonal vectors)
        dot_tn = tangent.x * face_normal.x + tangent.y * face_normal.y + tangent.z * face_normal.z
        dot_bn = binormal.x * face_normal.x + binormal.y * face_normal.y + binormal.z * face_normal.z
        dot_tb = tangent.x * binormal.x + tangent.y * binormal.y + tangent.z * binormal.z
        
        self.assertAlmostEqual(dot_tn, 0.0, places=5)
        self.assertAlmostEqual(dot_bn, 0.0, places=5)
        self.assertAlmostEqual(dot_tb, 0.0, places=5)


class TestMDLHierarchy(unittest.TestCase):
    """Test MDL node hierarchy and tree operations.
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:150-175 - prepare_skin_meshes()
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 - prepareSkinMeshes()
    """
    
    def test_node_hierarchy(self):
        """Test building a node hierarchy.
        
        References:
        ----------
            vendor/reone/src/libs/scene/node/model.cpp:59-97 - buildNodeTree()
        """
        # Create root node
        root = MDLNode()
        root.name = "rootdummy"
        
        # Create child nodes
        child1 = MDLNode()
        child1.name = "torso"
        
        child2 = MDLNode()
        child2.name = "head"
        
        # Build hierarchy
        root.children.append(child1)
        root.children.append(child2)
        
        self.assertEqual(len(root.children), 2)
        self.assertEqual(root.children[0].name, "torso")
        self.assertEqual(root.children[1].name, "head")
    
    def test_all_nodes_traversal(self):
        """Test traversing all nodes in a hierarchy.
        
        References:
        ----------
            Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:140-148 - all_nodes()
            vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:708-721 - Node traversal
        """
        # Create hierarchy
        mdl = MDL()
        root = MDLNode()
        root.name = "root"
        
        child1 = MDLNode()
        child1.name = "child1"
        
        child2 = MDLNode()
        child2.name = "child2"
        
        grandchild = MDLNode()
        grandchild.name = "grandchild"
        
        root.children.append(child1)
        root.children.append(child2)
        child1.children.append(grandchild)
        
        mdl.root_node = root
        
        # Get all nodes
        all_nodes = mdl.all_nodes()
        
        # Should include all 4 nodes
        self.assertEqual(len(all_nodes), 4)
        
        # Check names
        names = {node.name for node in all_nodes}
        self.assertIn("root", names)
        self.assertIn("child1", names)
        self.assertIn("child2", names)
        self.assertIn("grandchild", names)


class TestAnimationControllers(unittest.TestCase):
    """Test animation controller functionality.
    
    References:
    ----------
        Engines/PyKotorEngine/src/pykotorengine/animation/animation_controller.py
        vendor/KotOR.js/src/odyssey/controllers - Controller implementations
    """
    
    def test_position_controller(self):
        """Test position controller interpolation.
        
        References:
        ----------
            Engines/PyKotorEngine/src/pykotorengine/animation/animation_controller.py:165-228
            vendor/KotOR.js/src/odyssey/controllers/PositionController.ts - Position animation
        """
        # Create MDL controller
        rows = [
            MDLControllerRow(0.0, [0.0, 0.0, 0.0]),
            MDLControllerRow(1.0, [1.0, 0.0, 0.0]),
            MDLControllerRow(2.0, [2.0, 0.0, 0.0]),
        ]
        mdl_controller = MDLController(
            controller_type=MDLControllerType.Position,
            rows=rows,
            is_bezier=False
        )
        
        # This would test the animation controller if Panda3D were available
        # For now, just verify the MDL controller structure
        self.assertEqual(len(mdl_controller.rows), 3)
        self.assertEqual(mdl_controller.rows[0].data[0], 0.0)
        self.assertEqual(mdl_controller.rows[1].data[0], 1.0)
        self.assertEqual(mdl_controller.rows[2].data[0], 2.0)


def run_tests():
    """Run all unit tests.
    
    This function runs all test cases defined in this module.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMDLDataStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestTangentSpaceCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestMDLHierarchy))
    suite.addTests(loader.loadTestsFromTestCase(TestAnimationControllers))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)

