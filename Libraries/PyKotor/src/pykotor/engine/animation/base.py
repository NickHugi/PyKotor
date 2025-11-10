"""Abstract animation base classes.

This module defines the abstract interfaces for animation systems that can be
implemented by any rendering backend.

References:
----------
    vendor/reone/src/libs/scene/animation - Animation implementation
    vendor/KotOR.js/src/odyssey/controllers/OdysseyController.ts - Controller base
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_data import MDLController, MDLControllerRow, MDLAnimation


class IAnimationController(ABC):
    """Abstract interface for animation controllers.
    
    Controllers animate node properties by interpolating between keyframes.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/OdysseyController.ts:18-47 - Base controller
        vendor/reone/src/libs/scene/animation/channel.cpp:30-80 - Animation channel
    """
    
    @abstractmethod
    def get_value_at_time(self, time: float) -> Any:
        """Get the interpolated value at a specific time.
        
        Args:
        ----
            time: Time in seconds
        
        Returns:
        -------
            Interpolated value at the given time
        
        References:
        ----------
            vendor/reone/src/libs/scene/animation/channel.cpp:150-200 - getFrame()
        """
        ...
    
    @abstractmethod
    def apply(self, node: Any, value: Any) -> None:
        """Apply animated value to a node.
        
        Args:
        ----
            node: Backend-specific node object
            value: Animated value to apply
        
        References:
        ----------
            vendor/KotOR.js/src/odyssey/controllers/OdysseyController.ts:35-37 - setFrame()
        """
        ...


class IAnimationState(ABC):
    """Abstract interface for animation playback state.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/OdysseyModelAnimation.ts:25-100 - Animation state
        vendor/reone/src/libs/scene/animation/animation.cpp:30-80 - Animation state
    """
    
    @abstractmethod
    def update(self, dt: float) -> bool:
        """Update animation state for the current frame.
        
        Args:
        ----
            dt: Delta time since last update (seconds)
        
        Returns:
        -------
            True if animation is still playing, False if finished
        
        References:
        ----------
            vendor/reone/src/libs/scene/animation/animation.cpp:100-130 - update()
        """
        ...
    
    @abstractmethod
    def play(self) -> None:
        """Start playing the animation."""
        ...
    
    @abstractmethod
    def pause(self) -> None:
        """Pause the animation."""
        ...
    
    @abstractmethod
    def stop(self) -> None:
        """Stop and reset the animation."""
        ...


class IAnimationManager(ABC):
    """Abstract interface for managing animations on a model.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/OdysseyModelAnimationManager.ts:18-250 - Animation manager
        vendor/reone/src/libs/scene/animation/animator.cpp:30-200 - Animator class
    """
    
    @abstractmethod
    def play_animation(self, animation_name: str, loop: bool = True, speed: float = 1.0) -> bool:
        """Play an animation by name.
        
        Args:
        ----
            animation_name: Name of the animation to play
            loop: Whether to loop the animation
            speed: Playback speed multiplier
        
        Returns:
        -------
            True if animation was found and started, False otherwise
        
        References:
        ----------
            vendor/reone/src/libs/scene/animation/animator.cpp:200-220 - playAnimation()
        """
        ...
    
    @abstractmethod
    def pause_animation(self) -> None:
        """Pause the current animation."""
        ...
    
    @abstractmethod
    def stop_animation(self) -> None:
        """Stop the current animation."""
        ...
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """Update animation for the current frame.
        
        Args:
        ----
            dt: Delta time since last update (seconds)
        
        References:
        ----------
            vendor/reone/src/libs/scene/animation/animator.cpp:230-280 - update()
        """
        ...
    
    @abstractmethod
    def get_animation_names(self) -> list[str]:
        """Get list of all available animation names.
        
        Returns:
        -------
            List of animation names
        """
        ...
    
    @abstractmethod
    def has_animation(self, name: str) -> bool:
        """Check if an animation exists.
        
        Args:
        ----
            name: Animation name to check
        
        Returns:
        -------
            True if animation exists, False otherwise
        """
        ...

