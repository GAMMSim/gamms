from typing import List, Union, Iterator, Enum
from abc import ABC, abstractmethod
import numpy as np

class OpCodes(Enum):

    AGENT_CREATE = 0
    AGENT_GET = 1
    AGENT_DELETE = 2
    AGENT_STEP = 3
    AGENT_SET_STATE = 4
    AGENT_GET_STATE = 5
    AGENT_CURRENT_NODE = 5
    AGENT_PREV_NODE = 7
    AGENT_STRATEGY = 8
    AGENT_STATE = 9
    SENSOR_CREATE = 10
    NEIGHBOR_SENSOR_SENSE = 11
    MAP_SENSOR_SENSE = 12
    AGENT_SENSOR_SENSE = 13
    


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
    def time(self) -> np.float64:
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
    @abstractmethod
    def memory_get(self, keys: List[Union[str, int]]):
        """
        Return the value in the memory for the nested keys
        """
        pass
    @abstractmethod
    def memory_set(self, keys: List[Union[str, int]], value):
        """
        Set the value for the nested key. If second last key does not already exist then raise KeyError
        """
        pass