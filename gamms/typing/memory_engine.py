from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type
from enum import IntEnum


class StoreType(IntEnum):
    """
    Enumeration of supported store backends.

    Attributes:
        MEMORY: Pure in-memory store backed by Python dictionaries.
        FILESYSTEM: Filesystem-backed store (kept for compatibility with the
            previous artefact-style API). Not used by the structured
            map/table backends.
        DATABASE: SQLite-backed store with on-disk persistence.
    """
    MEMORY = 0
    FILESYSTEM = 1
    DATABASE = 2


class IPathLike(ABC):
    """
    Abstract base class representing a path-like object.

    PathLike objects are used to identify the on-disk (or remote) location of a
    store. Implementations should normalise the path so that absolute paths
    can be converted to a representation appropriate for the backend.
    """

    @abstractmethod
    def as_str(self) -> str:
        """
        Return the path as a string.
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """
        Return True if the path exists on the underlying medium.
        """
        pass


class IStore(ABC):
    """
    Abstract base class representing a structured storage instance.

    Primarily this is so that there is an abstraction over storage type
    Based on individual implementations, there can be a variety in implementation

    The objective is that there are multiple places where basic storage operations are needed
    but want it to be agnostic to the underlying storage implementation. The base API is not
    supposed to be optimal way to access it.
    """

    @abstractmethod
    def name(self) -> str:
        """The unique name of this store."""
        pass

    @abstractmethod
    def path(self) -> IPathLike:
        """The path to the store."""
        pass

    @property
    @abstractmethod
    def type(self) -> StoreType:
        """The backend type of this store."""
        pass

    @abstractmethod
    def create_map(self, map_name: str, struct: Dict[str, Type], primary_key: str) -> None:
        """
        Create a new key/value map within the store.

        Args:
            map_name: Unique name of the map within this store.
            struct: Defines the schema for the map.
            primary_key: The key to use as the primary key for the map. It needs to be unique within the map.

        Raises:
            ValueError: If a map with the given name already exists.
            TypeError: If there is unsupported strutures in the schema.
            IndexError: If the primary key is not found in the schema or is not indexable
        """
        pass

    @abstractmethod
    def delete_map(self, map_name: str) -> None:
        """
        Delete a map from the store.

        Args:
            map_name: Name of the map to delete.

        Raises:
            KeyError: If the map does not exist.
        """
        pass

    @abstractmethod
    def list_maps(self) -> List[str]:
        """Return the names of all maps currently in the store."""
        pass

    @abstractmethod
    def insert_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        """
        Insert a key/value pair into a map.

        Args:
            map_name: Name of the target map.
            struct: A dictionary containing the key-value pairs to insert.

        Raises:
            KeyError: If the map does not exist.
            IndexError: If there is an issue with the primary key.
            ValueError: If there is an issue with struct insertion
        """
        pass

    @abstractmethod
    def get_data(self, map_name: str, key: Any) -> Tuple[Tuple[str, Any], ...]:
        """
        Retrieve the value associated with the key

        Args:
            map_name: Name of the target map.
            key: The key for which to retrieve the value.

        Raises:
            KeyError: If the map does not exist.
            IndexError: If the key is not found in the map.
        """
        pass

    @abstractmethod
    def update_data(self, map_name: str, struct: Dict[str, Any]) -> None:
        """
        Update an entry in the map

        Args:
            map_name: Name of the target map.
            struct: A dictionary containing the key-value pairs to update.

        Raises:
            KeyError: If the map does not exist.
            IndexError: If there is an issue with the primary key.
            ValueError: If there is an issue with struct insertion
        """
        pass

    @abstractmethod
    def delete_data(self, map_name: str, key: Any) -> None:
        """
        Delete a key from a map

        Args:
            map_name: Name of the target map.
            key: The key to delete.

        Raises:
            KeyError: If the map does not exist.
            IndexError: If the key is not found in the map.
        """
        pass

    @abstractmethod
    def query_keys(self, map_name: str) -> Iterator[Any]:
        """
        Query all keys in a map.

        Args:
            map_name: Name of the target map.

        Raises:
            KeyError: If the map does not exist.
        """
        pass


class IMemoryEngine(ABC):
    """
    Abstract base class for the memory engine.

    The memory engine is a low level abstraction over different storage
    backends. It owns a collection of named stores; each store is itself a
    keyed collection of typed maps.
    """

    @abstractmethod
    def create_store(
        self,
        store_type: StoreType,
        name: str,
        path: Optional[IPathLike] = None,
    ) -> IStore:
        """
        Create a new store and register it with the engine.

        Args:
            store_type: Backend type for the new store.
            name: Unique store name.
            path: Optional path for backends that require persistence.

        Returns:
            IStore: The newly created store instance.

        Raises:
            ValueError: If a store with the same name already exists, or if
                the requested ``store_type`` is unsupported.
        """
        pass

    @abstractmethod
    def get_store(self, name: str) -> IStore:
        """
        Retrieve an existing store.

        Args:
            name: Unique name of the store.

        Raises:
            KeyError: If no store with the specified name exists.
        """
        pass

    @abstractmethod
    def list_stores(self) -> Iterator[str]:
        """
        Return the names of all stores.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """Tear down the memory engine and release all store resources."""
        pass
