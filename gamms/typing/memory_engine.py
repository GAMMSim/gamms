from abc import ABC, abstractmethod
from typing import Any, Iterator, List, Optional, Type
from enum import Enum


class StoreType(Enum):
    """
    Enumeration of supported store backends.

    Attributes:
        MEMORY: Pure in-memory store backed by Python dictionaries.
        FILESYSTEM: Filesystem-backed store (kept for compatibility with the
            previous artefact-style API). Not used by the structured
            map/table backends.
        REMOTE: Reserved for future remote stores (e.g., HTTP/REST).
        DATABASE: SQLite-backed store with on-disk persistence.
    """
    MEMORY = 0
    FILESYSTEM = 1
    REMOTE = 2
    DATABASE = 3


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

    A store is a named collection of "maps" (think tables / hashmaps). Each
    map stores key/value pairs and can optionally be typed.

    The store also exposes legacy ``save``/``load``/``delete`` methods that
    operate on the entire store (used for whole-store snapshots).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of this store."""
        pass

    @property
    @abstractmethod
    def store_type(self) -> StoreType:
        """The backend type of this store."""
        pass

    @abstractmethod
    def create_map(self, map_name: str, value_type: Optional[Type] = None) -> None:
        """
        Create a new key/value map within the store.

        Args:
            map_name: Unique name of the map within this store.
            value_type: Optional Python type associated with the values stored
                in the map. Implementations may ignore this hint.

        Raises:
            ValueError: If a map with the given name already exists.
        """
        pass

    @abstractmethod
    def has_map(self, map_name: str) -> bool:
        """Return True if a map with the given name exists."""
        pass

    @abstractmethod
    def list_maps(self) -> List[str]:
        """Return the names of all maps currently in the store."""
        pass

    @abstractmethod
    def insert_data(self, map_name: str, key: Any, value: Any) -> None:
        """
        Insert a key/value pair into a map.

        Args:
            map_name: Name of the target map.
            key: Key under which to store the value.
            value: Value to store.

        Raises:
            KeyError: If the map does not exist.
            ValueError: If the key already exists in the map.
        """
        pass

    @abstractmethod
    def get_data(self, map_name: str, key: Any) -> Any:
        """Retrieve the value associated with ``key`` in the named map."""
        pass

    @abstractmethod
    def update_data(self, map_name: str, key: Any, value: Any) -> None:
        """Update an existing key with a new value (raises if missing)."""
        pass

    @abstractmethod
    def delete_data(self, map_name: str, key: Any) -> None:
        """Delete a key from a map (raises if missing)."""
        pass

    @abstractmethod
    def has_data(self, map_name: str, key: Any) -> bool:
        """Return True if the key exists in the map."""
        pass

    @abstractmethod
    def keys(self, map_name: str) -> Iterator[Any]:
        """Iterate over all keys in the named map."""
        pass

    @abstractmethod
    def items(self, map_name: str) -> Iterator[Any]:
        """Iterate over all (key, value) pairs in the named map."""
        pass

    @abstractmethod
    def save(self, obj: Any = None) -> None:
        """
        Persist the store (or an artefact). Behaviour depends on the backend.
        """
        pass

    @abstractmethod
    def load(self) -> Any:
        """Load and return the contents of the store from its backing medium."""
        pass

    @abstractmethod
    def delete(self) -> None:
        """Delete the underlying storage of this store."""
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
    def list_stores(self) -> List[str]:
        """Return the names of all stores managed by this engine."""
        pass

    @abstractmethod
    def load_store(
        self,
        store_type: StoreType,
        name: str,
        path: IPathLike,
    ) -> IStore:
        """
        Load an existing store from the backing medium and register it.
        """
        pass

    @abstractmethod
    def save_store(self, name: str, path: Optional[IPathLike] = None) -> None:
        """Persist the named store to its backing medium."""
        pass

    @abstractmethod
    def terminate(self) -> None:
        """Tear down the memory engine and release all store resources."""
        pass
