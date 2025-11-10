"""Example demonstrating async resource loading in PyKotorGL.

This example shows how the async loading system works with ProcessPoolExecutor
for non-blocking MDL and texture loading.
"""

from __future__ import annotations

from pathlib import Path

# This is how the async system is used in practice
from pykotor.extract.installation import Installation
from pykotor.gl.scene import Scene


def example_basic_usage():
    """Basic example of using the scene with async loading."""
    # Setup installation
    installation = Installation(
        Path("C:/Games/KotOR"),
        "KotOR",
        tsl=False,
    )

    # Create scene - AsyncResourceLoader automatically initialized
    scene = Scene(installation=installation)

    # Request a model - returns immediately with placeholder
    # Actual loading happens in background process pools
    model = scene.model("p_bastilla")  # Returns empty model immediately

    # Request a texture - same pattern
    texture = scene.texture("P_BastillaH01")  # Returns gray placeholder

    # In render loop (called every frame):
    scene.render()  # Internally calls poll_async_resources()

    # After a few frames, resources will be loaded:
    model = scene.model("p_bastilla")  # Now returns actual model  # noqa: F841
    texture = scene.texture("P_BastillaH01")  # Now returns actual texture  # noqa: F841

    print("Async loading example complete")


def example_monitoring_progress():
    """Example showing how to monitor async loading progress."""
    from pykotor.common.module import Module

    installation = Installation(Path("C:/Games/KotOR"), "KotOR", tsl=False)
    module = Module("end_m01aa", installation)
    scene = Scene(installation=installation, module=module)

    # Request multiple resources
    models_needed = ["p_bastilla", "p_carth", "n_commoner01", "plc_chair"]
    for model_name in models_needed:
        scene.model(model_name)  # Queues async loading

    # Check progress
    print(f"Pending models: {len(scene._pending_model_futures)}")
    print(f"Pending textures: {len(scene._pending_texture_futures)}")

    # Simulate render loop
    for frame in range(100):
        scene.poll_async_resources()  # Process completed futures

        if frame % 10 == 0:
            print(f"Frame {frame}: {len(scene._pending_model_futures)} models loading, {len(scene.models)} models cached")

    print("All resources loaded")


def example_with_module_designer():
    """Example mimicking ModuleDesigner usage."""
    from pykotor.common.module import Module

    installation = Installation(Path("C:/Games/KotOR"), "KotOR", tsl=False)
    module = Module("end_m01aa", installation)

    # ModuleDesigner creates scene
    scene = Scene(installation=installation, module=module)

    # User opens module - triggers cache population
    # All model/texture requests go through async loader

    # Main render loop (e.g., in ModuleRenderer.paintGL):
    def render_frame():
        # This is called 60+ times per second
        scene.render()  # <-- Async resources converted to OpenGL here
        # ... rest of rendering

    # Simulate 60 FPS for 5 seconds
    for _ in range(300):
        render_frame()

    print("Module designer example complete")


def verify_no_threading():
    """Verify that ONLY ProcessPoolExecutor is used, NO threading."""
    import ast
    import inspect

    from pykotor.gl.scene import async_loader

    source = inspect.getsource(async_loader)
    tree = ast.parse(source)

    # Find all imports
    threading_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "thread" in alias.name.lower():
                    threading_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and "thread" in node.module.lower():
                threading_imports.append(node.module)

    if threading_imports:
        print(f"❌ FAILED: Found threading imports: {threading_imports}")
    else:
        print("✅ PASSED: No threading imports found")

    # Verify ProcessPoolExecutor is used
    if "ProcessPoolExecutor" in source:
        print("✅ PASSED: ProcessPoolExecutor is used")
    else:
        print("❌ FAILED: ProcessPoolExecutor not found")

    # Verify multiprocessing is used
    if "multiprocessing" in source:
        print("✅ PASSED: multiprocessing module is used")
    else:
        print("❌ FAILED: multiprocessing not found")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Async Loading Examples")
    print("=" * 60)

    print("\n1. Verifying no threading...")
    verify_no_threading()

    print("\n2. Basic usage example...")
    # example_basic_usage()  # Commented - needs actual game installation

    print("\n3. Monitoring progress example...")
    # example_monitoring_progress()  # Commented - needs actual game installation

    print("\n4. Module designer example...")
    # example_with_module_designer()  # Commented - needs actual game installation

    print("\n" + "=" * 60)
    print("Key Points:")
    print("- Uses 2 separate ProcessPoolExecutor instances")
    print("- Pool #1: IO operations (reading files)")
    print("- Pool #2: Parsing operations (MDL/TPC parsing)")
    print("- Main process: OpenGL rendering ONLY")
    print("- NO threading used anywhere")
    print("- Non-blocking: render loop never waits")
    print("=" * 60)


if __name__ == "__main__":
    main()
