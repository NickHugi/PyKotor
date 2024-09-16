from typing import Callable, List
from PyQt5.QtWidgets import QUndoCommand
from pathlib import Path
import shutil
import os

class BaseUndoCommand(QUndoCommand):
    def __init__(self, description: str):
        super().__init__(description)

    def redo(self):
        try:
            self._redo()
        except Exception as e:
            print(f"Error during redo of {self.text()}: {str(e)}")

    def undo(self):
        try:
            self._undo()
        except Exception as e:
            print(f"Error during undo of {self.text()}: {str(e)}")

    def _redo(self):
        raise NotImplementedError("Subclasses must implement _redo")

    def _undo(self):
        raise NotImplementedError("Subclasses must implement _undo")

class CopyCommand(BaseUndoCommand):
    def __init__(self, source_paths: List[Path], destination_path: Path):
        super().__init__("Copy")
        self.source_paths = source_paths
        self.destination_path = destination_path
        self.copied_paths = []

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
    def __init__(self, source_paths: List[Path], destination_path: Path):
        super().__init__("Move")
        self.source_paths = source_paths
        self.destination_path = destination_path
        self.moved_paths = []

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
    def __init__(self, paths: List[Path]):
        super().__init__("Delete")
        self.paths = paths
        self.deleted_items = []

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
        self.old_path = old_path
        self.new_path = new_path

    def _redo(self):
        self.old_path.rename(self.new_path)

    def _undo(self):
        self.new_path.rename(self.old_path)
