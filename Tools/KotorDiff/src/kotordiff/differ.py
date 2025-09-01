"""
Enhanced diffing algorithms for KOTOR file formats.

This module provides improved diffing capabilities for all KOTOR file formats,
converting them to text representations for standardized diffing.
"""

from __future__ import annotations

import difflib
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pykotor.extract.capsule import Capsule
from pykotor.resource.formats import gff, lip, ssf, tlk, twoda
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pykotor.extract.file import FileResource


class FileChange:
    """Represents a change to a file or resource."""
    
    def __init__(
        self,
        path: str,
        change_type: str,  # 'added', 'removed', 'modified'
        resource_type: str | None = None,
        old_content: str | None = None,
        new_content: str | None = None,
        diff_lines: list[str] | None = None,
    ):
        self.path = path
        self.change_type = change_type
        self.resource_type = resource_type
        self.old_content = old_content
        self.new_content = new_content
        self.diff_lines = diff_lines or []


class DiffResult:
    """Container for diff results between two installations."""
    
    def __init__(self):
        self.changes: list[FileChange] = []
        self.errors: list[str] = []
    
    def add_change(self, change: FileChange):
        """Add a file change to the results."""
        self.changes.append(change)
    
    def add_error(self, error: str):
        """Add an error message to the results."""
        self.errors.append(error)
    
    def get_changes_by_type(self, change_type: str) -> list[FileChange]:
        """Get all changes of a specific type."""
        return [change for change in self.changes if change.change_type == change_type]
    
    def get_changes_by_resource_type(self, resource_type: str) -> list[FileChange]:
        """Get all changes for a specific resource type."""
        return [change for change in self.changes if change.resource_type == resource_type]


class KotorDiffer:
    """Enhanced differ for KOTOR installations."""
    
    def __init__(self):
        self.gff_types = set(gff.GFFContent.get_extensions())
    
    def diff_installations(self, path1: Path, path2: Path) -> DiffResult:
        """Compare two KOTOR installations and return comprehensive diff results.
        
        Args:
        ----
            path1: Path to the first installation
            path2: Path to the second installation
            
        Returns:
        -------
            DiffResult: Comprehensive diff results
        """
        result = DiffResult()
        
        # Check if paths are KOTOR installations
        if not self._is_kotor_install(path1):
            result.add_error(f"Path {path1} is not a valid KOTOR installation")
            return result
        if not self._is_kotor_install(path2):
            result.add_error(f"Path {path2} is not a valid KOTOR installation")
            return result
        
        # Compare key directories and files
        self._diff_dialog_tlk(path1, path2, result)
        self._diff_directory(path1 / "Override", path2 / "Override", result)
        self._diff_directory(path1 / "Modules", path2 / "Modules", result)
        
        # Optional directories
        if (path1 / "rims").exists() or (path2 / "rims").exists():
            self._diff_directory(path1 / "rims", path2 / "rims", result)
        if (path1 / "Lips").exists() or (path2 / "Lips").exists():
            self._diff_directory(path1 / "Lips", path2 / "Lips", result)
        
        return result
    
    def _is_kotor_install(self, path: Path) -> bool:
        """Check if a path is a valid KOTOR installation."""
        return path.is_dir() and (path / "chitin.key").exists()
    
    def _diff_dialog_tlk(self, path1: Path, path2: Path, result: DiffResult):
        """Compare dialog.tlk files."""
        tlk1_path = path1 / "dialog.tlk"
        tlk2_path = path2 / "dialog.tlk"
        
        if tlk1_path.exists() and tlk2_path.exists():
            change = self._diff_tlk_files(tlk1_path, tlk2_path, "dialog.tlk")
            if change:
                result.add_change(change)
        elif tlk1_path.exists() and not tlk2_path.exists():
            result.add_change(FileChange("dialog.tlk", "removed", "tlk"))
        elif not tlk1_path.exists() and tlk2_path.exists():
            result.add_change(FileChange("dialog.tlk", "added", "tlk"))
    
    def _diff_directory(self, dir1: Path, dir2: Path, result: DiffResult):
        """Compare two directories recursively."""
        if not dir1.exists() and not dir2.exists():
            return
        
        # Get all files from both directories
        files1 = set()
        files2 = set()
        
        if dir1.exists():
            files1 = {f.relative_to(dir1) for f in dir1.rglob("*") if f.is_file()}
        if dir2.exists():
            files2 = {f.relative_to(dir2) for f in dir2.rglob("*") if f.is_file()}
        
        # Find added, removed, and common files
        added_files = files2 - files1
        removed_files = files1 - files2
        common_files = files1 & files2
        
        # Process each type of change
        for file_path in added_files:
            full_path = str(dir2.name / file_path)
            result.add_change(FileChange(full_path, "added", self._get_resource_type(file_path)))
        
        for file_path in removed_files:
            full_path = str(dir1.name / file_path)
            result.add_change(FileChange(full_path, "removed", self._get_resource_type(file_path)))
        
        for file_path in common_files:
            file1 = dir1 / file_path
            file2 = dir2 / file_path
            change = self._diff_files(file1, file2, str(dir1.name / file_path))
            if change:
                result.add_change(change)
    
    def _diff_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare two individual files."""
        try:
            if is_capsule_file(file1.name):
                return self._diff_capsule_files(file1, file2, relative_path)
            else:
                return self._diff_regular_files(file1, file2, relative_path)
        except Exception as e:
            # Return an error change
            return FileChange(
                relative_path,
                "error",
                self._get_resource_type(file1),
                None,
                None,
                [f"Error comparing files: {str(e)}"]
            )
    
    def _diff_capsule_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare capsule files (ERF, MOD, etc.)."""
        try:
            capsule1 = Capsule(file1)
            capsule2 = Capsule(file2)
            
            # Get resources from both capsules
            resources1 = {res.resname(): res for res in capsule1}
            resources2 = {res.resname(): res for res in capsule2}
            
            # Check if contents are different
            if set(resources1.keys()) != set(resources2.keys()):
                return FileChange(relative_path, "modified", "capsule")
            
            # Compare individual resources
            for resname in resources1:
                if resname in resources2:
                    res1 = resources1[resname]
                    res2 = resources2[resname]
                    if not self._compare_resource_data(res1, res2):
                        return FileChange(relative_path, "modified", "capsule")
            
            return None  # No changes
        except Exception:
            # Fall back to hash comparison
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_regular_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare regular files based on their type."""
        ext = file1.suffix.lower().lstrip('.')
        
        if ext in self.gff_types:
            return self._diff_gff_files(file1, file2, relative_path)
        elif ext == "2da":
            return self._diff_2da_files(file1, file2, relative_path)
        elif ext == "tlk":
            return self._diff_tlk_files(file1, file2, relative_path)
        elif ext == "ssf":
            return self._diff_ssf_files(file1, file2, relative_path)
        elif ext == "lip":
            return self._diff_lip_files(file1, file2, relative_path)
        else:
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_gff_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare GFF files."""
        try:
            gff1 = gff.read_gff(file1)
            gff2 = gff.read_gff(file2)
            
            # Convert to text representation
            text1 = self._gff_to_text(gff1)
            text2 = self._gff_to_text(gff2)
            
            if text1 != text2:
                diff_lines = list(difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=f"original/{relative_path}",
                    tofile=f"modified/{relative_path}",
                    lineterm=""
                ))
                return FileChange(relative_path, "modified", "gff", text1, text2, diff_lines)
            
            return None
        except Exception as e:
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_2da_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare 2DA files."""
        try:
            twoda1 = twoda.read_2da(file1)
            twoda2 = twoda.read_2da(file2)
            
            # Convert to text representation
            text1 = self._2da_to_text(twoda1)
            text2 = self._2da_to_text(twoda2)
            
            if text1 != text2:
                diff_lines = list(difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=f"original/{relative_path}",
                    tofile=f"modified/{relative_path}",
                    lineterm=""
                ))
                return FileChange(relative_path, "modified", "2da", text1, text2, diff_lines)
            
            return None
        except Exception:
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_tlk_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare TLK files."""
        try:
            tlk1 = tlk.read_tlk(file1)
            tlk2 = tlk.read_tlk(file2)
            
            # Convert to text representation
            text1 = self._tlk_to_text(tlk1)
            text2 = self._tlk_to_text(tlk2)
            
            if text1 != text2:
                diff_lines = list(difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=f"original/{relative_path}",
                    tofile=f"modified/{relative_path}",
                    lineterm=""
                ))
                return FileChange(relative_path, "modified", "tlk", text1, text2, diff_lines)
            
            return None
        except Exception:
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_ssf_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare SSF files."""
        try:
            ssf1 = ssf.read_ssf(file1)
            ssf2 = ssf.read_ssf(file2)
            
            # Convert to text representation
            text1 = self._ssf_to_text(ssf1)
            text2 = self._ssf_to_text(ssf2)
            
            if text1 != text2:
                diff_lines = list(difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=f"original/{relative_path}",
                    tofile=f"modified/{relative_path}",
                    lineterm=""
                ))
                return FileChange(relative_path, "modified", "ssf", text1, text2, diff_lines)
            
            return None
        except Exception:
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_lip_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare LIP files."""
        try:
            lip1 = lip.read_lip(file1)
            lip2 = lip.read_lip(file2)
            
            # Convert to text representation
            text1 = self._lip_to_text(lip1)
            text2 = self._lip_to_text(lip2)
            
            if text1 != text2:
                diff_lines = list(difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=f"original/{relative_path}",
                    tofile=f"modified/{relative_path}",
                    lineterm=""
                ))
                return FileChange(relative_path, "modified", "lip", text1, text2, diff_lines)
            
            return None
        except Exception:
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_by_hash(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare files by hash if no specific handler exists."""
        try:
            hash1 = self._calculate_file_hash(file1)
            hash2 = self._calculate_file_hash(file2)
            
            if hash1 != hash2:
                return FileChange(relative_path, "modified", self._get_resource_type(file1))
            
            return None
        except Exception:
            return FileChange(relative_path, "error", self._get_resource_type(file1))
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hasher = hashlib.sha256()
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _compare_resource_data(self, res1: FileResource, res2: FileResource) -> bool:
        """Compare data from two resources."""
        return self._calculate_data_hash(res1.data()) == self._calculate_data_hash(res2.data())
    
    def _calculate_data_hash(self, data: bytes) -> str:
        """Calculate SHA256 hash of data."""
        return hashlib.sha256(data).hexdigest()
    
    def _get_resource_type(self, file_path: Path | str) -> str:
        """Get the resource type from a file path."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower().lstrip('.')
    
    # Text conversion methods
    def _gff_to_text(self, gff_obj: gff.GFF) -> str:
        """Convert GFF object to text representation."""
        return str(gff_obj.root)  # Simplified - this would need enhancement
    
    def _2da_to_text(self, twoda_obj: twoda.TwoDA) -> str:
        """Convert 2DA object to text representation."""
        lines = []
        lines.append("2DA V2.b")
        lines.append("")
        
        # Column headers
        if twoda_obj.columns:
            lines.append("\t".join([""] + twoda_obj.columns))
        
        # Rows
        for i, row in enumerate(twoda_obj.rows):
            row_data = [str(i)]
            for col in twoda_obj.columns:
                value = row.get(col, "****")
                row_data.append(str(value) if value is not None else "****")
            lines.append("\t".join(row_data))
        
        return "\n".join(lines)
    
    def _tlk_to_text(self, tlk_obj: tlk.TLK) -> str:
        """Convert TLK object to text representation."""
        lines = []
        lines.append(f"TLK Language: {tlk_obj.language}")
        lines.append("")
        
        for i, entry in enumerate(tlk_obj.entries):
            if entry.text or entry.voiceover or entry.sound_length:
                lines.append(f"Entry {i}:")
                if entry.text:
                    lines.append(f"  Text: {entry.text}")
                if entry.voiceover:
                    lines.append(f"  Voiceover: {entry.voiceover}")
                if entry.sound_length:
                    lines.append(f"  Sound Length: {entry.sound_length}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _ssf_to_text(self, ssf_obj: ssf.SSF) -> str:
        """Convert SSF object to text representation."""
        lines = []
        for sound_name, sound_obj in ssf_obj.sounds.items():
            lines.append(f"{sound_name}: {sound_obj.resref}")
        return "\n".join(lines)
    
    def _lip_to_text(self, lip_obj: lip.LIP) -> str:
        """Convert LIP object to text representation."""
        lines = []
        lines.append(f"LIP Duration: {lip_obj.length}")
        for i, keyframe in enumerate(lip_obj.keyframes):
            lines.append(f"Keyframe {i}: Time={keyframe.time}, Shape={keyframe.shape}")
        return "\n".join(lines)