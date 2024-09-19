from __future__ import annotations

import shutil

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QUndoCommand
from loggerplus import RobustLogger

if TYPE_CHECKING:
    from pathlib import Path


class BaseUndoCommand(QUndoCommand):
    def __init__(self, description: str):
        super().__init__(description)

    def redo(self):
        try:
            self._redo()
        except Exception as e:
            RobustLogger().exception(f"Error during redo of {self.text()}: {e!s}")

    def undo(self):
        try:
            self._undo()
        except Exception as e:
            RobustLogger().exception(f"Error during undo of {self.text()}: {e!s}")

    def _redo(self):
        raise NotImplementedError("Subclasses must implement _redo")

    def _undo(self):
        raise NotImplementedError("Subclasses must implement _undo")


class CutCommand(BaseUndoCommand):
    def __init__(self, source_paths: list[Path], destination_path: Path):
        super().__init__("Cut")
        self.source_paths: list[Path] = source_paths
        self.destination_path: Path = destination_path
        self.moved_items: list[tuple[Path, Path]] = []

    def _redo(self):
        for source in self.source_paths:
            dest = self.destination_path / source.name
            shutil.move(str(source), str(dest))
            self.moved_items.append((source, dest))

    def _undo(self):
        for source, dest in reversed(self.moved_items):
            shutil.move(str(dest), str(source))
        self.moved_items.clear()


class CopyCommand(BaseUndoCommand):
    def __init__(self, source_paths: list[Path], destination_path: Path):
        super().__init__("Copy")
        self.source_paths: list[Path] = source_paths
        self.destination_path: Path = destination_path
        self.copied_paths: list[Path] = []

    def _redo(self):
        for source in self.source_paths:
            dest = self.destination_path / source.name
            if source.is_dir():
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            self.copied_paths.append(dest)

    def _undo(self):
        for path in self.copied_paths:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        self.copied_paths.clear()


class MoveCommand(BaseUndoCommand):
    def __init__(self, source_paths: list[Path], destination_path: Path):
        super().__init__("Move")
        self.source_paths: list[Path] = source_paths
        self.destination_path: Path = destination_path
        self.moved_paths: list[tuple[Path, Path]] = []

    def _redo(self):
        for source in self.source_paths:
            dest = self.destination_path / source.name
            shutil.move(str(source), str(dest))
            self.moved_paths.append((source, dest))

    def _undo(self):
        for source, dest in reversed(self.moved_paths):
            shutil.move(str(dest), str(source))
        self.moved_paths.clear()


class DeleteCommand(BaseUndoCommand):
    def __init__(self, paths: list[Path]):
        super().__init__("Delete")
        self.paths: list[Path] = paths
        self.deleted_items: list[tuple[str, Path]] = []

    def _redo(self):
        for path in self.paths:
            if path.is_dir():
                shutil.rmtree(path)
                self.deleted_items.append(("dir", path))
            else:
                path.unlink()
                self.deleted_items.append(("file", path))

    def _undo(self):
        for item_type, path in reversed(self.deleted_items):
            if item_type == "dir":
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.touch()
        self.deleted_items.clear()


class RenameCommand(BaseUndoCommand):
    def __init__(self, old_path: Path, new_path: Path):
        super().__init__("Rename")
        self.old_path: Path = old_path
        self.new_path: Path = new_path

    def _redo(self):
        self.old_path.rename(self.new_path)

    def _undo(self):
        self.new_path.rename(self.old_path)
