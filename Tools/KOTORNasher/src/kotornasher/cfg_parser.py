"""Configuration file parser for kotornasher.cfg (TOML format, nasher-compatible)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import Logger

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]


class KOTORNasherConfig:
    """Represents a kotornasher.cfg configuration."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.root_dir = config_path.parent
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load the configuration file."""
        if not self.config_path.exists():
            msg = f"Configuration file not found: {self.config_path}"
            raise FileNotFoundError(msg)

        with self.config_path.open("rb") as f:
            self._data = tomllib.load(f)

    def _expand_variables(self, value: str, target_name: str | None = None, variables: dict[str, str] | None = None) -> str:
        """Expand variables in a string value.

        Variables can be in the form $variable or ${variable}.
        Checks package variables, target variables, and environment variables.
        """
        if not isinstance(value, str):
            return value

        # Build variable dictionary
        var_dict = {}

        # Add package variables
        if "package" in self._data and "variables" in self._data["package"]:
            var_dict.update(self._data["package"]["variables"])

        # Add target-specific variables
        if variables:
            var_dict.update(variables)

        # Add special $target variable
        if target_name:
            var_dict["target"] = target_name

        # Add environment variables
        var_dict.update(os.environ)

        # Expand ${var} and $var patterns
        import re

        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            return var_dict.get(var_name, match.group(0))

        # Replace ${var} first, then $var
        result = re.sub(r"\$\{(\w+)\}", replace_var, value)
        result = re.sub(r"\$(\w+)", replace_var, result)

        return result

    @property
    def package(self) -> dict[str, Any]:
        """Get the package configuration."""
        return self._data.get("package", {})

    @property
    def targets(self) -> list[dict[str, Any]]:
        """Get all target configurations."""
        result: list[dict[str, Any]] = []
        for key, value in self._data.items():
            if (key == "target" or (isinstance(value, dict) and value.get("name"))) and isinstance(value, dict):
                result.append(value)
        return result

    def get_target(self, name: str | None = None) -> dict[str, Any] | None:
        """Get a target by name, or the default target if name is None."""
        targets = self.targets
        if not targets:
            return None

        if name is None:
            # Return first target (default) or target marked as default
            default_name = self.package.get("default")
            if default_name:
                for target in targets:
                    if target.get("name") == default_name:
                        return target
            return targets[0] if targets else None

        # Find target by name
        for target in targets:
            if target.get("name") == name:
                return target
        return None

    def resolve_target_value(self, target: dict[str, Any], key: str, default: Any | None = None) -> Any:
        """Resolve a target value, inheriting from parent or package if needed."""
        # Check target first
        if key in target:
            value = target[key]
            # Expand variables if it's a string
            if isinstance(value, str):
                target_vars = target.get("variables", {})
                return self._expand_variables(value, target.get("name"), target_vars)
            return value

        # Check parent target
        parent_name = target.get("parent")
        if parent_name:
            parent = self.get_target(parent_name)
            if parent and key in parent:
                value = parent[key]
                if isinstance(value, str):
                    parent_vars = parent.get("variables", {})
                    return self._expand_variables(value, parent.get("name"), parent_vars)
                return value

        # Check package
        if key in self.package:
            value = self.package[key]
            if isinstance(value, str):
                return self._expand_variables(value, target.get("name"))
            return value

        return default

    def get_target_sources(self, target: dict[str, Any]) -> dict[str, list[str]]:
        """Get source patterns for a target."""
        sources = target.get("sources", {})
        if not sources:
            sources = self.package.get("sources", {})

        return {
            "include": sources.get("include", []),
            "exclude": sources.get("exclude", []),
            "filter": sources.get("filter", []),
            "skipCompile": sources.get("skipCompile", []),
        }

    def get_target_rules(self, target: dict[str, Any]) -> dict[str, str]:
        """Get unpack rules for a target."""
        rules = target.get("rules", {})
        if not rules:
            rules = self.package.get("rules", {})
        return rules


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Find kotornasher.cfg by walking up the directory tree."""
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()
    while True:
        config_path = current / "kotornasher.cfg"
        if config_path.exists():
            return config_path

        parent = current.parent
        if parent == current:  # Reached root
            return None
        current = parent


def load_config(logger: Logger, config_path: Path | None = None) -> KOTORNasherConfig | None:
    """Load the kotornasher.cfg configuration file.

    Args:
    ----
        logger: Logger instance
        config_path: Optional explicit path to config file

    Returns:
    -------
        Loaded configuration or None if not found
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None:
        logger.error("This is not a kotornasher repository. Please run 'kotornasher init'")
        return None

    try:
        return KOTORNasherConfig(config_path)
    except Exception:
        logger.exception("Failed to load configuration")
        return None



