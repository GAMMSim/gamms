from gamms.VisualizationEngine import Shape
from typing import Dict, Any


class RenderNode:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    @property
    def x(self) -> float | None:
        return self._data.get('x', None)

    @property
    def y(self) -> float | None:
        return self._data.get('y', None)
    
    @property
    def color(self) -> tuple | None:
        return self._data.get('color', None)
    
    @property
    def shape(self) -> Shape | None:
        return self._data.get('shape', None)
    
    @property
    def drawer(self):
        return self._data.get('drawer', None)
    
    @property
    def layer(self) -> int | None:
        return self._data.get('layer', None)

