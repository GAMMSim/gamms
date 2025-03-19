from typing import Dict, Any, Callable
from abc import ABC, abstractmethod
from enum import Enum, auto


class ArtistType(Enum):
    GENERAL = auto()
    AGENT = auto()
    GRAPH = auto()


class IArtist(ABC):
    @abstractmethod
    def set_data(self, key: str, value: Any) -> None:
        """
        Set a custom data for the artist.

        Args:
            key: The key of the data.
            value: The value of the data
        """
        pass

    @abstractmethod
    def get_data(self, key: str, default_value: Any=None) -> Any:
        """
        Get a custom data for the artist.

        Args:
            key: The key of the data.
            default_value: The default value if the key does not exist.

        Returns:
            The value of the data.
        """
        pass

    @abstractmethod
    def get_data_dict(self) -> Dict[str, Any]:
        """
        Get the dictionary containing all custom data for the artist.

        Returns:
            Dict[str, Any]: The dictionary of custom data.
        """
        pass

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
    def set_drawer(self, drawer: Callable) -> None:
        """
        Set the drawer function for the artist.

        Args:
            drawer (Callable): The drawer function to set.
        """
        pass

    @abstractmethod
    def get_drawer(self) -> Callable | None:
        """
        Get the drawer function of the artist.

        Returns:
            Callable | None: The current drawer function, or None if not set.
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