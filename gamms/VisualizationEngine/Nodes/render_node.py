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
        return self._data['x']

    @property
    def y(self) -> float | None:
        return self._data['y']
    
    @property
    def color(self) -> tuple | None:
        return self._data['color']
    
    @property
    def shape(self) -> Shape | None:
        return self._data['shape']
    
    @property
    def drawer(self) -> callable | None:
        return self._data['drawer']
