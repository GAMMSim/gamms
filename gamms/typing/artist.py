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
        pass

    @abstractmethod
    def get_data(self, key: str, default_value: Any=None) -> Any:
        pass

    @abstractmethod
    def get_data_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_layer(self, layer: int) -> None:
        pass

    @abstractmethod
    def get_layer(self) -> int:
        pass

    @abstractmethod
    def set_visible(self, visible: bool) -> None:
        pass

    @abstractmethod
    def get_visible(self) -> bool:
        pass

    @abstractmethod
    def set_drawer(self, drawer: Callable) -> None:
        pass

    @abstractmethod
    def get_drawer(self) -> Callable | None:
        pass

    @abstractmethod
    def get_will_draw(self) -> bool:
        pass

    @abstractmethod
    def set_will_draw(self, will_draw: bool) -> None:
        pass

    @abstractmethod
    def get_artist_type(self) -> ArtistType:
        pass

    @abstractmethod
    def set_artist_type(self, artist_type: ArtistType) -> None:
        pass

    @abstractmethod
    def draw(self, data: Dict[str, Any]) -> None:
        pass