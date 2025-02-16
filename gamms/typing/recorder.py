from typing import List, Union, Iterator, Dict
from enum import Enum
from abc import ABC, abstractmethod


class OpCodes(Enum):
    TERMINATE = 0x00000000
    AGENT_CREATE = 0x01000000
    AGENT_GET = 0x01000001
    AGENT_DELETE = 0x01000002
    AGENT_STEP = 0x01000003
    AGENT_SET_STATE =  0x01000004
    AGENT_GET_STATE = 0x01000005
    AGENT_CURRENT_NODE = 0x01000006
    AGENT_PREV_NODE =  0x01000007
    AGENT_STRATEGY = 0x01000008
    AGENT_STATE = 0x01000009
    SENSOR_CREATE = 0x02000000
    SENSOR_SENSE = 0x02000001
    SENSOR_UPDATE = 0x02000002

MAGIC_NUMBER = 0x4D4D4752.to_bytes(4, 'big')
VERSION = 0x00000001.to_bytes(4, 'big')

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