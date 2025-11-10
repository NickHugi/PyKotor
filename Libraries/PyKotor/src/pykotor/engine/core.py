"""Core engine stubs used by tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generic, Iterable, Type, TypeVar

from .graphics import GUIManager

T = TypeVar("T")


class ServiceContainer:
    """Simple type-aware service registry."""

    def __init__(self, services: Iterable[object] | None = None) -> None:
        self._services: Dict[Type[object], object] = {}
        if services is not None:
            for service in services:
                self.register(service)

    def register(self, service: object) -> None:
        """Register a service instance keyed by its type."""
        self._services[type(service)] = service

    def get(self, service_type: Type[T]) -> T:
        """Retrieve a registered service instance."""
        service = self._services.get(service_type)
        if service is None:
            raise KeyError(f"No service registered for {service_type!r}")
        return service  # type: ignore[return-value]


@dataclass(frozen=True)
class EngineState:
    """Represents high-level engine state information."""

    game_path: Path
    exit_requested: bool = False


class KotorEngine:
    """Minimal stand-in for the real engine used in tests."""

    def __init__(self, game_path: Path) -> None:
        self._state = EngineState(game_path=Path(game_path))
        self.services = ServiceContainer(services=[GUIManager()])

    @property
    def game_path(self) -> Path:
        """Path to the KotOR installation."""
        return self._state.game_path

    def request_exit(self) -> None:
        """Request shutdown of the engine."""
        self._state = EngineState(game_path=self._state.game_path, exit_requested=True)

