# Project Overview: Holocron Toolset and Spyder Plugin Integration

## Core Objective

Transform the existing standalone game modding toolset into a fully functional Spyder IDE plugin, ensuring complete functionality in both standalone and plugin modes.

## Core Principles

1. **Modularity**
   - **Separation of Concerns:** Clearly separate standalone and plugin components to prevent updates in one from affecting the other.
   - **Extensible Architecture:** Design the system to easily add new features, editors, or widgets without major overhauls.

2. **Consistency**
   - **Feature Parity:** Ensure all standalone features are accessible and functional within the Spyder plugin.
   - **Unified UI/UX:** Maintain a consistent user interface and experience across both modes to enhance usability and reduce the learning curve.

3. **Non-Invasive Integration**
   - **Minimal Footprint:** Limit changes to the existing toolset codebase, making only essential modular modifications for dual operation.
   - **Respecting Spyder’s Ecosystem:** Utilize Spyder’s native functionalities (e.g., docking, theming) without compromising the toolset’s integrity or Spyder’s performance.

## Key Components and Features

1. **Dual-Mode Operation**
   - Seamlessly switch between standalone and plugin modes with consistent functionality and user experience.

2. **Flexible Editor Architecture**
   - Adapt the base `Editor` class for both standalone (`QMainWindow`) and Spyder-compatible widgets.
   - Implement approximately 30 specialized subclasses for various file types.
   - Enable view switching between 'editor' and 'raw contents'.
   - Special handling for `NSSEditor` to leverage Spyder's code editing features.

3. **Widget Integration and UI Management**
   - Dynamically place widgets within Spyder IDE (toolbars, side panels, status bars).
   - Utilize Spyder’s interactive features like drag-and-drop and context menus.
   - Embed custom UIs into Spyder's tabbed interface with state preservation across sessions and modes.

4. **Resource and Installation Management**
   - Implement a resource management system using the `ResourceType` enum.
   - Develop systems for adding, removing, and switching between game installations.
   - Ensure efficient handling and scalability for various resource types.

5. **Configuration and Preferences**
   - Integrate with Spyder's preferences system for unified settings management.
   - Provide persistent storage for installation configurations and user preferences accessible in both modes.

6. **Plugin-Specific Enhancements**
   - Customize Spyder's toolbar and status bar integration.
   - Leverage Spyder's native features to enhance functionality.

## General Ideas and Considerations

1. **Leverage Existing Projects**
   - Incorporate best practices from existing Spyder plugins and similar dual-mode applications to inform design decisions and avoid common pitfalls.

2. **User-Centric Design**
   - Create an intuitive and efficient user experience tailored to game modders' workflows, enhancing their productivity.

3. **Flexible Editor Architecture**
   - Ensure editors are easily embeddable within both the standalone application and Spyder, supporting view switching and interactive content manipulation.

4. **Signal and Communication Systems**
   - Utilize robust inter-component communication mechanisms (e.g., signals and slots) to facilitate seamless interaction between toolset and plugin components without tight coupling.

## Development Approach

- Maintain strict separation between standalone toolset and plugin-specific code.
- Use signals for communication between toolset and plugin components.
- Create wrapper classes to bridge standalone and plugin functionalities.
- Design modularly to allow easy extension and maintenance.
- We should not, create a ToolWindow object instance in the plugin at all. ToolWindow represents the standalone app, all functionality from it should be migrated to the plugin, if any must be.

## Implementation Strategy

1. Modify existing `ToolWindow` and `Editor` classes to support both standalone and plugin modes.
2. Develop plugin-specific classes (e.g., `HolocronToolset`, `HolocronToolsetContainer`).
3. Implement a robust signal system for inter-component communication.
4. Create configuration and preference management systems compatible with Spyder.

## Challenges and Considerations

- Maintain feature parity and consistent behavior across standalone and plugin modes.
- Optimize performance for both usage scenarios.
- Balance modularity with integration requirements.
- Manage potential conflicts between toolset and Spyder functionalities.

## Requirements and Constraints

1. **Codebase Integrity**
   - Preserve the core toolset by limiting modifications to areas necessary for modularity and integration, ensuring standalone functionality remains unaffected.

2. **Robust Framework Utilization**
   - **Spyder’s Plugin System:** Leverage Spyder’s existing plugin infrastructure for compatibility and reduced redundant development.
   - **Cross-Platform Compatibility:** Ensure the plugin operates seamlessly across all platforms supported by Spyder and the standalone toolset.

This document outlines the current state and direction of the Holocron Toolset project, focusing on Spyder IDE integration while maintaining standalone functionality. It will be updated as the project evolves.
