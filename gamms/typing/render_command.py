from abc import ABC, abstractmethod
from enum import Enum, auto

class RenderOpCode(Enum):
    RenderCircle = auto()
    RenderRectangle = auto()
    RenderPolygon = auto()
    RenderLine = auto()
    RenderLineString = auto()
    RenderText = auto()

class IRenderCommand(ABC):

    @property
    @abstractmethod
    def opcode(self) -> RenderOpCode:
        """
        Get the operation code for the command.

        Returns:
            RenderOpCode: The operation code for the command.
        """
        pass