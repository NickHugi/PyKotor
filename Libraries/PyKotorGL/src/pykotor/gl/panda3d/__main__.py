from __future__ import annotations

from typing import TYPE_CHECKING

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties

from pykotor.common.module import Module
from pykotor.extract.installation import Installation
from pykotor.gl.panda3d.scene import KotorRenderer

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation


print("Starting demo...")
demo: KotorRenderer | None = None

if __name__ == "__main__":
    from pathlib import Path

    from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DirectOptionMenu
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import TextNode, WindowProperties

    from pykotor.common.misc import Game
    from pykotor.extract.installation import Installation
    from pykotor.tools.path import find_kotor_paths_from_default

    class MyApp(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.selected_game: Game | None = None
            self.selected_installation_path: Path | None = None
            self.selected_level: str | None = None
            self.game_menu: DirectOptionMenu | None = None
            self.should_exit: bool = False

            # Set up window properties
            props = WindowProperties()
            props.setTitle("KotOR Module Viewer")
            props.setSize(800, 600)
            self.win.requestProperties(props)  # pyright: ignore[reportAttributeAccessIssue]

            # Set up background
            self.setBackgroundColor(0.12, 0.12, 0.14)  # Dark background

            self.select_game_installation_and_level()

        def select_game_installation_and_level(self):
            # Find KotOR installation paths
            paths: dict[Game, list[Path]] = find_kotor_paths_from_default()  # pyright: ignore[reportAssignmentType]
            if not paths:
                print("Could not find KotOR installation")
                self.should_exit = True
                return

            # Create main container frame with more padding
            frame = DirectFrame(
                frameColor=(0.16, 0.16, 0.18, 0.95),
                frameSize=(-1.0, 1.0, -0.7, 0.7),  # Wider frame
                pos=(0, 0, 0),
                relief=1,
            )

            # Title bar
            title_frame = DirectFrame(frameColor=(0.18, 0.18, 0.2, 1), frameSize=(-1.0, 1.0, -0.1, 0.1), pos=(0, 0, 0.6), parent=frame, relief=1)

            DirectLabel(
                text="KotOR Module Viewer",
                scale=0.08,  # Larger text
                pos=(0, 0, 0),
                parent=title_frame,
                text_fg=(0.95, 0.95, 0.95, 1),
                text_align=TextNode.ACenter,
                text_shadow=(0, 0, 0, 0.5),
                text_shadowOffset=(0.002, 0.002),
            )

            # Content container with better spacing
            content_frame = DirectFrame(frameColor=(0.16, 0.16, 0.18, 0), frameSize=(-0.9, 0.9, -0.5, 0.5), pos=(0, 0, 0), parent=frame)

            # Row height and spacing
            _row_height = 0.15
            label_scale = 0.07
            menu_scale = 0.07
            button_scale = 0.07

            # Game selection row
            _game_label = DirectLabel(text="Game", scale=label_scale, pos=(-0.85, 0, 0.3), parent=content_frame, text_align=TextNode.ALeft, text_fg=(0.9, 0.9, 0.9, 1))

            game_options = [game.name for game in paths.keys()]
            self.game_menu = DirectOptionMenu(
                text="Select Game",
                scale=menu_scale,
                items=game_options,
                initialitem=0,
                pos=(-0.3, 0, 0.3),
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.25, 0.25),
                popupMarker_scale=0.3,
                frameColor=(0.12, 0.12, 0.14, 1),  # Darker background
                highlightColor=(0.18, 0.18, 0.2, 1),
                text_fg=(0.9, 0.9, 0.9, 1),
                item_text_fg=(0.9, 0.9, 0.9, 1),
                item_frameColor=(0.12, 0.12, 0.14, 0.95),
            )

            _game_button = DirectButton(
                text="Choose",
                scale=button_scale,
                pos=(0.5, 0, 0.3),
                command=self.update_installations,
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.4, 0.4),  # Much larger clickable area
                frameColor=(0.2, 0.5, 0.9, 1),
                pressEffect=0.9,
                relief=1,
                text_fg=(1, 1, 1, 1),
            )

            # Installation selection row
            _installation_label = DirectLabel(text="Path", scale=label_scale, pos=(-0.85, 0, 0), parent=content_frame, text_align=TextNode.ALeft, text_fg=(0.9, 0.9, 0.9, 1))

            self.installation_menu = DirectOptionMenu(
                text="Select Installation",
                scale=menu_scale,
                items=["No installations found"],
                pos=(-0.3, 0, 0),
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.25, 0.25),
                popupMarker_scale=0.3,
                frameColor=(0.12, 0.12, 0.14, 1),  # Darker background
                highlightColor=(0.18, 0.18, 0.2, 1),
                text_fg=(0.9, 0.9, 0.9, 1),
                item_text_fg=(0.9, 0.9, 0.9, 1),
                item_frameColor=(0.12, 0.12, 0.14, 0.95),
            )

            _installation_button = DirectButton(
                text="Choose",
                scale=button_scale,
                pos=(0.5, 0, 0),
                command=self.update_levels,
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.4, 0.4),  # Much larger clickable area
                frameColor=(0.2, 0.5, 0.9, 1),
                pressEffect=0.9,
                relief=1,
                text_fg=(1, 1, 1, 1),
            )

            # Level selection row
            _level_label = DirectLabel(text="Level", scale=label_scale, pos=(-0.85, 0, -0.3), parent=content_frame, text_align=TextNode.ALeft, text_fg=(0.9, 0.9, 0.9, 1))

            self.level_menu = DirectOptionMenu(
                text="Select Level",
                scale=menu_scale,
                items=["No levels found"],
                pos=(-0.3, 0, -0.3),
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.25, 0.25),
                popupMarker_scale=0.3,
                frameColor=(0.12, 0.12, 0.14, 1),  # Darker background
                highlightColor=(0.18, 0.18, 0.2, 1),
                text_fg=(0.9, 0.9, 0.9, 1),
                item_text_fg=(0.9, 0.9, 0.9, 1),
                item_frameColor=(0.12, 0.12, 0.14, 0.95),
            )

            # Store paths
            self.paths = paths

            # Load button
            _load_button = DirectButton(
                text="Load Module",
                scale=0.08,
                pos=(0, 0, -0.5),
                command=self.confirm_selection,
                parent=frame,
                frameSize=(-0.8, 0.8, -0.4, 0.4),  # Much larger clickable area
                frameColor=(0.2, 0.7, 0.4, 1),
                pressEffect=0.9,
                relief=1,
                text_fg=(1, 1, 1, 1),
            )

        def update_installations(self):
            if self.game_menu is None:
                return

            selected_game = self.game_menu.get()
            game_enum = Game[selected_game]
            installation_paths = self.paths[game_enum]

            if installation_paths:
                self.installation_menu["items"] = [str(path) for path in installation_paths]
                self.installation_menu.set(0)
            else:
                self.installation_menu["items"] = ["No installations found"]
                self.installation_menu.set(0)

            # Reset level menu
            self.level_menu["items"] = ["No levels found"]
            self.level_menu.set(0)

        def update_levels(self):
            selected_path = self.installation_menu.get()
            if selected_path and selected_path != "No installations found":
                self.selected_installation = Installation(Path(selected_path))
                levels = self.selected_installation.modules_list()
                if levels:
                    self.level_menu["items"] = levels
                    self.level_menu.set(0)
                else:
                    self.level_menu["items"] = ["No levels found"]
                    self.level_menu.set(0)

        def confirm_selection(self):
            if self.game_menu is None or self.installation_menu is None or self.level_menu is None:
                return

            selected_level = self.level_menu.get()
            if selected_level == "No levels found":
                return

            self.selected_game = self.game_menu.get()
            self.selected_installation_path = self.installation_menu.get()
            self.selected_level = selected_level

            if all(
                [
                    self.selected_game,
                    self.selected_installation_path and self.selected_installation_path != "No installations found",
                    self.selected_level and self.selected_level != "No levels found",
                ]
            ):
                self.should_exit = True

        def run(self):
            """Override run to handle clean exit."""
            while not self.should_exit:
                self.taskMgr.step()

            # Clean up
            self.destroy()
            return self.selected_game, self.selected_installation, self.selected_level

    # Run the selection UI first
    app = MyApp()
    selected_game, selected_installation, selected_level = app.run()

    # Only proceed if we have valid selections
    if all([selected_game, selected_installation, selected_level]):
        print(f"Selected Game: {selected_game}")
        print(f"Selected Installation: {selected_installation}")
        print(f"Selected Level: {selected_level}")

        # Now create and run the renderer
        demo = KotorRenderer(
            installation=selected_installation,
            module=Module(str(selected_level), selected_installation),
        )
        demo.run()

print("Demo finished.")
