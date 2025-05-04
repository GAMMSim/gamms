from abc import ABC, abstractmethod
from typing import Any, List
from enum import Enum

class IStoreType(Enum):
    """
    Enumeration representing different types of storage backends.

    This enum can be extended to include various storage mechanisms such as
    file-based, database, or cloud storage.
    """
    SQLITE = 0
    # Add more storage types as needed
    
class IPathLike(ABC):
    """
    Abstract base class representing a path-like object.

    This interface defines the structure for objects that behave like filesystem paths.
    It can be extended to support various path representations and operations.
    """
    pass


class IStore(ABC):
    """
    Abstract base class representing a generic storage mechanism.

    The store provides methods to save, load, and delete objects, facilitating
    persistent storage and retrieval of data.
    """

    @abstractmethod
    def save(self, obj: Any) -> None:
        """
        Save an object to the storage.

        This method persists the provided object to the underlying storage medium.

        Args:
            obj (Any): The object to be saved. It can be of any type that the store supports.

        Raises:
            IOError: If an error occurs during the save operation.
            ValueError: If the object is invalid or cannot be serialized.
        """
        pass

    @abstractmethod
    def load(self) -> Any:
        """
        Load and retrieve an object from the storage.

        This method fetches the stored object from the underlying storage medium.

        Returns:
            Any: The retrieved object. The type depends on what was originally saved.

        Raises:
            IOError: If an error occurs during the load operation.
            FileNotFoundError: If there is no object to load.
            ValueError: If the stored data is corrupted or cannot be deserialized.
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Delete the stored object from the storage.

        This method removes the persisted object from the underlying storage medium.

        Raises:
            IOError: If an error occurs during the delete operation.
            FileNotFoundError: If there is no object to delete.
        """
        pass


class IMemoryEngine(ABC):
    """
    Abstract base class representing a memory engine for managing stores.

    The memory engine is responsible for creating, listing, loading, and terminating
    storage stores. It acts as a manager that oversees various storage instances.
    """

    @abstractmethod
    def create_store(self, store_type: Enum, name: str, path: IPathLike) -> IStore:
        """
        Create a new store within the memory engine.

        This method initializes a new storage instance based on the specified type,
        assigns it a name, and associates it with a path-like object.

        Args:
            store_type (Enum): An enumeration specifying the type of store to create.
                This could represent different storage backends or configurations.
            name (str): The unique name identifier for the store.
            path (IPathLike): A path-like object specifying where the store's data
                should be located or managed.

        Returns:
            IStore: The newly created store instance.

        Raises:
            ValueError: If the provided store_type is unsupported or invalid.
            FileExistsError: If a store with the given name already exists.
            IOError: If there is an issue creating the store at the specified path.
        """
        pass

    @abstractmethod
    def list_stores(self) -> List[str]:
        """
        List all store names managed by the memory engine.

        This method retrieves the names of all existing stores within the engine.

        Returns:
            List[str]: A list of store names currently managed by the engine.

        Raises:
            RuntimeError: If the memory engine is not properly initialized.
        """
        pass

    @abstractmethod
    def load_store(self, name: str) -> IStore:
        """
        Load an existing store by its name.

        This method retrieves a store instance based on its unique name identifier.

        Args:
            name (str): The unique name identifier of the store to load.

        Returns:
            IStore: The loaded store instance.

        Raises:
            KeyError: If no store with the specified name exists.
            IOError: If there is an issue accessing the store's data.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the memory engine and perform necessary cleanup operations.

        This method ensures that all stores are properly closed and that any
        allocated resources are released. It prepares the engine for shutdown.

        Raises:
            RuntimeError: If the engine fails to terminate gracefully.
            IOError: If there are issues during the cleanup process.
        """
        pass
