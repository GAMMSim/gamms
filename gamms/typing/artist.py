from typing import Dict, Any, Callable, Union, Optional
from abc import ABC, abstractmethod
from enum import Enum, auto

class ArtistType(Enum):
    GENERAL = auto()
    AGENT = auto()
    GRAPH = auto()


class IArtist(ABC):
    """
    Interface for the artist.

    Attributes:
        data (Union[Dict[str, Any] , Any]): The custom data associated with the artist. Default is an empty dictionary but users can set it to any type.
    """

    data: Union[Dict[str, Any] , Any]

    @abstractmethod
    def set_layer(self, layer: int) -> None:
        """
        Set the layer of the artist.

        Args:
            layer (int): The layer to set.
        """
        pass

    @abstractmethod
    def get_layer(self) -> int:
        """
        Get the layer of the artist.

        Returns:
            int: The current layer of the artist.
        """
        pass

    @abstractmethod
    def set_visible(self, visible: bool) -> None:
        """
        Set the visibility of the artist.

        Args:
            visible (bool): The visibility state to set.
        """
        pass

    @abstractmethod
    def get_visible(self) -> bool:
        """
        Get the visibility of the artist.

        Returns:
            bool: The current visibility state of the artist.
        """
        pass

    @abstractmethod
    def set_drawer(self, drawer: Callable[["IContext", Dict[str, Any]], None]) -> None:
        """
        Set the drawer function for the artist.

        Args:
            drawer (Callable[[IContext, Dict[str, Any]], None]): The drawer function to set.
        """
        pass

    @abstractmethod
    def get_drawer(self) -> Optional[Callable[["IContext", Dict[str, Any]], None]]:
        """
        Get the drawer function of the artist.

        Returns:
            Optional[Callable[[IContext, Dict[str, Any]], None]]: The current drawer function, or None if not set.
        """
        pass

    @abstractmethod
    def get_will_draw(self) -> bool:
        """
        Get whether the artist will draw.

        Returns:
            bool: True if the artist will draw, False otherwise.
        """
        pass

    @abstractmethod
    def set_will_draw(self, will_draw: bool) -> None:
        """
        Set whether the artist will draw.

        Args:
            will_draw (bool): The will_draw state to set.
        """
        pass

    @abstractmethod
    def get_artist_type(self) -> ArtistType:
        """
        Get the type of the artist.

        Returns:
            ArtistType: The current type of the artist.
        """
        pass

    @abstractmethod
    def set_artist_type(self, artist_type: ArtistType) -> None:
        """
        Set the type of the artist.

        Args:
            artist_type (ArtistType): The artist type to set.
        """
        pass

    @abstractmethod
    def draw(self) -> None:
        """
        Draw the artist immediately.
        """
        pass
    
    @property
    @abstractmethod
    def layer_dirty(self) -> bool:
        """
        Check if the layer is dirty.

        Returns:
            bool: True if the layer is dirty, False otherwise.
        """
        pass

    @layer_dirty.setter
    @abstractmethod
    def layer_dirty(self, value: bool) -> None:
        """
        Set the layer dirty state.

        Args:
            value (bool): The dirty state to set.
        """
        pass