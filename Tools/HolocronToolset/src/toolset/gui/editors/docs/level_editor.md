
# KotOR Level Editor

The LYT class (in lyt_data.py) represents the structure of a LYT file, containing rooms, tracks, obstacles, and doorhooks. The ModuleRenderer class (in module.py) is responsible for rendering the module in 3D, which could be extended to visualize LYT data.
The IndoorMapBuilder class (in indoor_builder.py) already provides functionality for building new levels using pre-constructed kits.

Use this information to create an editor for LYTs and integrate it with the Module Designer. This is our main goal: the ability to create custom maps and piece together teztures like solving a 3d puzzle.

1. Extend the ModuleRenderer to visualize LYT data, allowing users to see the layout they're creating in real-time.
2. Add a new tab or section specifically for LYT editing in the ModuleRenderer, providing tools for adding, moving, and editing rooms, tracks, obstacles, and doorhooks.
3. A pre-existing 2D top-down view that can be utilized for placing and manipulating rooms and other elements.
4. Implement functionality to import custom textures and models, associating them with rooms in the LYT.  Implement a sidebar with available textures, room templates, and other LYT components.  Utilize the Module.layout() method to access the current LYT resource.
Add a feature to generate a basic LYT structure from existing module data, which users can then modify.  Implement a system to track changes and update the LYT resource in real-time.

Texture management:

- Leverage the existing texture loading system in Module.reload_resources().
- Create a texture browser within the LYT editor UI, showing all available textures for the module.
- Allow users to import and manage custom textures directly within the tool.
Room Creation and Manipulation::
- Implement drag-and-drop functionality for placing rooms from templates or creating custom shapes.
- Allow users to resize, rotate, and reposition rooms using intuitive controls.
- Provide options for setting room properties (e.g., height, material types). Implement an intelligent system for automatically connecting adjacent rooms.  Allow manual door placement and editing of door properties.  Utilize the LYTDoorHook class to manage door connections between rooms.

Walkmesh Generation:

- Integrate the walkmesh generation logic from the IndoorMapBuilder.
- Provide options for automatic walkmesh creation based on room layouts.
- Allow manual editing and refinement of walkmeshes.

Integration with Existing Systems:

- Modify the ModuleDesigner class to include the new LYT editing functionality.
- Update the ModuleDesignerSettings to include preferences for the LYT editor.
- Ensure that changes in the LYT editor are reflected in other parts of the Module Designer (e.g., updating placeable positions).

Saving and Exporting:

- Implement methods to save the modified LYT back to the module resource.
- Provide options for exporting the layout as a standalone LYT file or as part of a module package.
- Ensure compatibility with the existing module building and packaging systems.

Performance:

- Implement efficient rendering techniques for large layouts.
- Use spatial partitioning to improve performance when working with complex layouts.
- Optimize texture and resource loading to minimize memory usage.

User Interface Enhancements::

- Create intuitive toolbars and shortcuts for common LYT editing operations.
- Implement a layering system for organizing and managing complex layouts.
- Provide customizable grid and snapping options for precise placement.

Fully integrate with the UI.

- Ensure all widgets are resizeable, all controls are intuitive, and all controls are easily accessible
- Do not ever create any widgets in pure python. Always modify the .ui xml directly. (extension will be .ui).

Relevant files:
@Tools/HolocronToolset/src/toolset/gui/windows/module_designer.py
@Tools/HolocronToolset/src/ui/windows/module_designer.ui
@Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_auto.py
@Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/walkmesh.py
@Tools/HolocronToolset/src/toolset/gui/windows/designer_controls.py
@Tools/HolocronToolset/src/toolset/gui/windows/indoor_builder.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/walkmesh.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/lyt_editor.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/lyt_editor.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/module.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/texture_browser.py
@Libraries/PyKotorGL/src/pykotor/gl/scene.py
@Libraries/PyKotorGL/src/pykotor/gl/shader.py
@Tools/HolocronToolset/src/toolset/kits/blackvulkar.json
@Libraries/PyKotor/src/pykotor/common/module.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/lyt_editor_widget.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/walkmesh_editor.py
@Tools/HolocronToolset/src/toolset/gui/widgets/renderer/texture_browser.py
@Tools/HolocronToolset/src/toolset/gui/dialogs/lyt_dialogs.py
@Tools/HolocronToolset/src/toolset/gui/widgets/settings/editor_settings/lyt.py
@Tools/HolocronToolset/src/toolset/gui/editors/lyt.py

NOTE:

- IndoorMapBuilder/blackvulkar.json are provided as reference points only as a legacy/deprecated way of modifying the lyt. They are not part of ModuleDesigner.

vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYT.cs
vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYTReader.cs
vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYTWriter.cs

vendor/NorthernLights-master/Assets/Editor/KLE/KLayoutEditor.cs
vendor/NorthernLights-master/Assets/Scripts/AuroraEngine/AuroraLayout.cs
vendor/NorthernLights-master/Assets/Scripts/AuroraEngine/AuroraLayoutRoom.cs
vendor/NorthernLights-master/Assets/Scripts/AuroraEngine/AuroraLayoutDoor.cs

vendor/xoreos/src/aurora/lytfile.h
vendor/xoreos/src/aurora/lytfile.cpp
vendor/xoreos/tests/aurora/lytfile.cpp
vendor/xoreos/src/engines/kotorbase/area.h
vendor/xoreos/src/engines/kotorbase/area.cpp

vendor/reone/src/libs/resource/format/lytreader.h
vendor/reone/src/libs/resource/format/lytreader.cpp
vendor/reone/src/libs/resource/provider/layouts.cpp
vendor/reone/src/libs/resource/typeutil.cpp
vendor/reone/src/libs/game/object/area.cpp

vendor/KotOR_IO/KotOR_IO/File Formats/LYT.cs

vendor/KotOR-Unity/Assets/Scripts/ResourceLoader/LayoutLoader.cs
vendor/KotOR-Unity/Assets/Scripts/ResourceLoader/Resources.cs

vendor/KotOR.js/src/resource/LYTObject.ts
vendor/KotOR.js/src/interface/resource/ILayoutDoorHook.ts
vendor/KotOR.js/src/interface/resource/ILayoutObstacle.ts
vendor/KotOR.js/src/interface/resource/ILayoutRoom.ts
vendor/KotOR.js/src/interface/resource/ILayoutTrack.ts
vendor/KotOR.js/src/module/ModuleArea.ts

vendor/kotorblender/io_scene_kotor/ops/lyt/importop.py
vendor/kotorblender/io_scene_kotor/ops/lyt/export.py
vendor/kotorblender/io_scene_kotor/io/lyt.py

### **Functionality Descriptions**

1. **Interactive Grid System:** A dynamic, snap-to-grid interface that simplifies precise object placement.
2. **Drag-and-Drop Features:** Intuitive dragging of game elements directly into the scene.
3. **Multi-Layer Support:** Seamlessly manage and toggle between background, midground, and foreground layers.
4. **Object Hierarchy View:** A collapsible tree view to manage objects and their parent-child relationships.
5. **Undo/Redo Stack:** A robust history mechanism for easily reverting or reapplying changes.
6. **Customizable Tile Palettes:** User-defined tile sets to quickly populate terrains or structures.
7. **Real-Time Preview Mode:** Instantly playtest created levels within the editor.
8. **Hotkey Integration:** Fully customizable hotkeys for quick tool access and workflow efficiency.
9. **Resizable Canvas:** A workspace that adjusts dynamically to project size and resolution.
10. **Object Snapping:** Automatic alignment for objects to maintain consistent spacing.
11. **Scripting Integration:** Support for adding custom behaviors with embedded scripting tools.
12. **Smart Selections:** Intelligent grouping and selection tools for rapid modifications.
13. **Prefab System:** Save and reuse common level elements with drag-and-drop prefab objects.
14. **Collision Visualization:** Highlight areas with collision boundaries to debug physics interactions.
15. **Data Export Options:** Flexible saving formats, such as JSON, XML, or binary data for game engines.
16. **Asset Preview Panel:** Thumbnail previews of textures, sprites, or models for quick identification.
17. **Color-Coded Layers:** Assign unique colors to layers for clarity during editing.
18. **Zoom and Pan:** Smooth zooming and panning capabilities for both close-up details and an overall view.
19. **Custom Tool Plugins:** Extend functionality by integrating additional user-made plugins.
20. **AI-Assisted Suggestions:** Use AI to auto-generate layouts or suggest edits based on patterns.

---

### **Visual and UX Descriptions**

1. **Modern UI Design:** Sleek, flat design language with minimalistic yet powerful controls.
2. **Dark and Light Modes:** Toggleable themes for user comfort in varying lighting conditions.
3. **Floating Toolbars:** Context-sensitive toolbars that appear when certain tools are in use.
4. **Snap Animations:** Smooth visual feedback when objects snap into place.
5. **Interactive Cursor Changes:** Dynamic cursor styles that change to reflect active tools.
6. **Hover Effects:** Subtle highlights or tooltips when hovering over elements or icons.
7. **Grid Customization:** Adjustable gridlines with options for colors, spacing, and visibility.
8. **Contextual Menus:** Right-click options tailored to the selected object or tool.
9. **Minimal Clutter:** A clean interface with collapsible panels to maximize the workspace.
10. **Real-Time Updates:** Instant visual feedback as objects are manipulated or edited.
11. **Widget Docking:** Movable and dockable tool panels for flexible workspace organization.
12. **Palette Swatches:** Quick color selection for creating visually cohesive designs.
13. **Thumbnail Previews:** Large, clear previews for all assets in an organized library.
14. **Animated Transitions:** Smooth transitions between tool activations and mode changes.
15. **3D Viewport Option:** Optional support for visualizing 3D elements or depth layers.
16. **Highlight Selected Objects:** Add glowing outlines or shading to identify selected items.
17. **Layer Transparency Sliders:** Adjustable opacity for individual layers to focus on specific details.
18. **Tooltip-Enhanced Buttons:** Clear explanations for each tool via informative tooltips.
19. **Multi-Viewport Layout:** Split views to observe the level from different angles or scales.
20. **Grid Alignment Indicators:** Visual guidelines that assist in perfect alignment.

---

### **Outcome Phrasings**

1. **"Craft intricate, visually stunning levels with precision and ease."**
2. **"Enable developers to design, edit, and test immersive environments seamlessly."**
3. **"A flexible and intuitive platform for creating diverse gaming worlds."**
4. **"Empower designers with a user-friendly toolkit that balances power and simplicity."**
5. **"Transform abstract ideas into fully functional, visually polished levels."**
6. **"Achieve a perfect blend of artistic creativity and logical structure in level design."**
7. **"Deliver a feature-rich editor that caters to beginners and professionals alike."**
8. **"Streamline the game development pipeline with efficient, integrated tools."**
9. **"Provide a playground for endless experimentation and creativity in game design."**
10. **"Build a bridge between technical functionality and artistic freedom."**
11. **"Bring game environments to life with a toolkit tailored for innovation."**
12. **"Offer unparalleled customization and control to game developers."**
13. **"Foster collaboration by enabling shared projects and real-time editing."**
14. **"Create levels that are as fun to build as they are to play."**
15. **"Maximize productivity while minimizing complexity in level creation."**
16. **"Let creators focus on ideas, not on the technical hurdles."**
17. **"A robust and elegant solution for designing any type of level."**
18. **"Make level design feel intuitive, exciting, and effortlessly efficient."**
19. **"Seamlessly integrate artistic vision with technical precision."**
20. **"Turn ambitious game ideas into tangible, playable realities."**
