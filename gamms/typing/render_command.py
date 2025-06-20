from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any

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

    @property
    @abstractmethod
    def data(self) -> Any:
        """
        Get the data associated with the render command.

        Returns:
            Any: The data associated with the render command.
        """
        pass