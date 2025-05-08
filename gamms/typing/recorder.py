from typing import List, Union, Iterator, Dict, Type, TypeVar, Callable, BinaryIO, Tuple, Any
from abc import ABC, abstractmethod

from gamms.typing.opcodes import OpCodes

JsonType = Union[None, int, str, bool, List["JsonType"], Dict[str, "JsonType"]]
_T = TypeVar('_T')

class IRecorder(ABC):
    @abstractmethod
    def record(self) -> bool:
        """
        Boolean to inform whether game is being recorded or not and ctx is alive

        Returns:
            bool: True if recording, False otherwise
        """
        pass

    @abstractmethod
    def start(self, path: Union[str, BinaryIO]) -> None:
        """
        Start recording to the path. Raise error if file already exists
        Adds ".ggr" extension if not present.

        If path is a file object, it will be used as the file handler.

        Args:
            path (Union[str, BinaryIO]): Path to record the game.
        
        Raises:
            FileExistsError: If the file already exists.
            TypeError: If the path is not a string or file object.
        """
        pass
    @abstractmethod
    def stop(self) -> None:
        """
        Stop recording to the path and close the file handler.

        Raises:
            RuntimeError: If recording has not started.
        """
        pass
    @abstractmethod
    def pause(self) -> None:
        """
        Pause the recording process. `self.record()` should return false if paused.  If not started or stopped, give warning.
        """
        pass
    @abstractmethod
    def play(self) -> None:
        """
        Resume recording if paused. If not started or stopped, give warning.
        """
        pass
    @abstractmethod    
    def replay(self, path: Union[str, BinaryIO]) -> Iterator[Dict[str, Any]]:
        """
        Checks validity of the file and output an iterator.

        Args:
            path (Union[str, BinaryIO]): Path to the recording file.
        
        Returns:
            Iterator: Iterator to replay the recording.
        
        Raises:
            RuntimeError: If replay is already in progress.
            FileNotFoundError: If the file does not exist.
            TypeError: If the path is not a string or file object.
            ValueError: If the file is not a valid recording file or if recording terminated unexpectedly.
        """
        pass
    @abstractmethod
    def time(self) -> int:
        """
        Return record time if replaying. Else return the local time `(time.time())` in nano seconds.

        Returns:
            int: Time in nanoseconds.
        """
        pass
    @abstractmethod
    def write(self, opCode: OpCodes, data: Dict[str, JsonType]) -> None:
        """
        Write to record buffer if recording. If not recording raise error as it should not happen.

        WARNING: This function should not be required to be called by the user in most cases.
        """
        pass

    @abstractmethod
    def component(self, struct: Dict[str, Type[_T]]) -> Callable[[Type[_T]], Type[_T]]:
        """
        Decorator to add a component to the recorder.

        Args:
            struct (Dict[str, Type[_T]]): Dictionary with component name and type.

        Returns:
            Callable[[Type[_T]], Type[_T]]: Decorator function.
        
        """
        pass

    @abstractmethod
    def get_component(self, name: str) -> object:
        """
        Get the component from the name.

        Args:
            name (str): Name of the component.
        
        Returns:
            Type[_T]: Component object.
        
        Raises:
            KeyError: If the component is not found.
        """
        pass

    @abstractmethod
    def delete_component(self, name: str) -> None:
        """
        Delete the component from the name.

        Args:
            name (str): Name of the component.
        
        Raises:
            KeyError: If the component is not found.
        
        """
        pass

    @abstractmethod
    def component_iter(self) -> Iterator[str]:
        """
        Iterator for the component names.
        """
        pass

    @abstractmethod
    def add_component(self, name: str, obj: Type[_T]) -> None:
        """
        Add a component to the recorder.

        Args:
            name (str): Name of the component.
            obj (Type[_T]): Component object.
        
        Raises:
            ValueError: If the component already exists.
        """
        pass

    @abstractmethod
    def is_component_registered(self, key: Tuple[str, str]) -> bool:
        """
        Check if the component is registered.
        Key is (module_name, qualname)

        Args:
            key (Tuple[str, str]): Key to check.
        
        Returns:
            bool: True if registered, False otherwise.
        """
        pass

    @abstractmethod
    def unregister_component(self, key: Tuple[str, str]) -> None:
        """
        Unregister the component.
        Key is (module_name, qualname)

        Args:
            key (Tuple[str, str]): Key to unregister.
        
        Raises:
            KeyError: If the component is not found.
        """
        pass