from typing import List, Union, Iterator, Dict
from abc import ABC, abstractmethod

JsonType = Union[None, int, str, bool, List["JsonType"], Dict[str, "JsonType"]]

class IRecorder(ABC):
    @abstractmethod
    def record(self) -> bool:
        """
        Boolean to inform whether game is being recorded or not and ctx is alive
        """
        pass

    @abstractmethod
    def start(self, path: str) -> None:
        """
        Start recording to the path. Raise error if file already exists
        """
        pass
    @abstractmethod
    def stop(self, path: str) -> None:
        """
        Stop recording to the path and close the file handler.
        """
        pass
    @abstractmethod
    def pause(self) -> None:
        """
        Pause the recording process. `self.record()` should return false if paused.  If not started or stopped, give warning.
        """
        pass
    @abstractmethod
    def play(self, path: str) -> None:
        """
        Resume recording if paused. If not started or stopped, give warning.
        """
        pass
    @abstractmethod    
    def replay(self, path: str) -> Iterator:
        """
        Checks validity of the file and output an iterator.
        """
        pass
    @abstractmethod
    def time(self) -> int:
        """
        Return record time if replaying. Else return the local time `(time.time())`
        """
        pass
    @abstractmethod
    def write(self, opCode, data) -> None:
        """
        Write to record buffer if recording. If not recording raise error as it should not happen.
        """
        pass