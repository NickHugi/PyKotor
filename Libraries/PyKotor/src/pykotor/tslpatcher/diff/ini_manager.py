#!/usr/bin/env python3
"""Enhanced INI file manager using ConfigObj for easier section merging and management.

This module provides a cleaner interface for managing TSLPatcher INI files,
replacing the complex string manipulation in incremental_writer.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from configobj import ConfigObj

if TYPE_CHECKING:
    from pathlib import Path


class INIManager:
    """Manages INI file operations with easy section merging and updating.

    Uses ConfigObj under the hood to preserve comments, order, and enable
    intuitive section merging.
    """

    def __init__(self, ini_path: Path) -> None:
        """Initialize INI manager.

        Args:
            ini_path: Path to the INI file to manage
        """
        self.ini_path = ini_path
        self.config: ConfigObj | None = None

    def load(self) -> None:
        """Load existing INI file or create empty config."""
        if self.ini_path.exists():
            self.config = ConfigObj(
                str(self.ini_path),
                encoding="utf-8",
                create_empty=True,
                write_empty_values=True,
            )
        else:
            self.config = ConfigObj(create_empty=True, write_empty_values=True)

    def initialize_sections(self, section_headers: list[str]) -> None:
        """Initialize INI with section headers in order.

        Args:
            section_headers: List of section names (e.g., ["[TLKList]", "[2DAList]"])
        """
        if self.config is None:
            self.config = ConfigObj(create_empty=True, write_empty_values=True)

        # ConfigObj doesn't use brackets in section names
        for header in section_headers:
            section_name = header.strip("[]")
            if section_name not in self.config:
                self.config[section_name] = {}

    def merge_section_lines(self, section_name: str, lines: list[str]) -> None:
        """Merge lines into a section, avoiding duplicates.

        Args:
            section_name: Section name (without brackets, e.g., "TLKList")
            lines: List of key=value lines to merge into the section
        """
        if self.config is None:
            self.load()

        # Ensure section exists
        if (
            self.config is not None
            and section_name not in self.config
        ):
            self.config[section_name] = {}

        section: dict[str, Any] = cast(
            "dict[str, Any]",
            self.config[section_name],
        ) if self.config is not None else {}

        # Parse and merge lines
        for line in lines:
            parsed_line = line.strip()
            if not parsed_line or parsed_line.startswith((";", "#")):
                continue  # Skip empty lines and comments

            if "=" not in parsed_line:
                continue

            key, value = parsed_line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # ConfigObj handles lists automatically
            # For now, treat as single value
            if key not in section:
                section[key] = value
            else:
                # Key exists - check if it's a list or merge strategy
                existing = section[key]
                if isinstance(existing, list):
                    if value not in existing:
                        existing.append(value)
                # Convert to list if different values
                elif existing != value:
                    section[key] = [existing, value]

    def merge_sections_from_serializer(
        self,
        serialized_lines: list[str],
    ) -> None:
        """Merge sections from TSLPatcherINISerializer output.

        This intelligently parses the serializer output and merges sections,
        handling nested sections like [planetary.2da] within [2DAList].

        Args:
            serialized_lines: Complete INI lines from serializer
        """
        if self.config is None:
            self.load()

        current_section: str | None = None
        current_lines: list[str] = []

        for line in serialized_lines:
            line_stripped = line.strip()

            # Skip header comments (handled separately)
            if line_stripped.startswith((";", "#")):
                continue

            # Detect section header
            if line_stripped.startswith("[") and line_stripped.endswith("]"):
                # Process previous section
                if current_section is not None and current_lines:
                    self.merge_section_lines(current_section, current_lines)

                # Start new section
                section_name = line_stripped[1:-1]
                current_section = section_name
                current_lines = []

                # Ensure section exists
                if (
                    self.config is not None
                    and section_name not in self.config
                ):
                    self.config[section_name] = {}
            # Accumulate lines for current section
            elif current_section is not None:
                current_lines.append(line)

        # Process final section
        if current_section is not None and current_lines:
            self.merge_section_lines(current_section, current_lines)

    def write(self) -> None:
        """Write config back to file."""
        if self.config is None:
            return

        self.config.write(outfile=str(self.ini_path))

    def get_section(self, section_name: str) -> ConfigObj | None:
        """Get a section by name.

        Args:
            section_name: Section name (without brackets)

        Returns:
            ConfigObj section or None if not found
        """
        if self.config is None:
            return None
        return cast(
            "ConfigObj | None",
            self.config.get(section_name),
        )

    def section_exists(self, section_name: str) -> bool:
        """Check if a section exists.

        Args:
            section_name: Section name (without brackets)

        Returns:
            True if section exists
        """
        if self.config is None:
            return False
        return section_name in self.config

