import pygame
import math
from gamms.VisualizationEngine import Color
from gamms.VisualizationEngine.utils import string_to_color
from shapely.geometry import LineString
from typing import Optional


class AgentVisual:
    def __init__(self, name, start_position, **kwargs):
        """
        Initialize AgentVisual with an AgentEngine.
        """
        self.name = name
        color = kwargs.get('color', (255, 0, 0))
        self.color = string_to_color(color)
        self.size = kwargs.get('size', 8)
        self.shape = kwargs.get('shape', None)
        self.prev_position = None
        self.target_position = None
        self._current_edge: Optional[LineString] = None
        self.position = start_position

    def start_simulation_lerp(self, prev_position, target_position, edge):
        self.prev_position = prev_position
        self.target_position = target_position
        self._current_edge = edge
    
    def follow_path(self, path):
        pass

    def update_simulation(self, alpha: float):
        """
        Update the simulation with the alpha value.
        """
        if self.prev_position is not None and self.target_position is not None:
            if self._current_edge is not None:
                point = self._current_edge.interpolate(alpha, True)
                self.position = (point.x, point.y)
            else:
                self.position = (self.prev_position[0] + alpha * (self.target_position[0] - self.prev_position[0]), self.prev_position[1] + alpha * (self.target_position[1] - self.prev_position[1]))

    def draw_agent(self, screen, scale_func, is_waiting_agent=False):
        color = self.color if not is_waiting_agent else Color.Magenta
        (scaled_x, scaled_y) = scale_func(self.position)
        # Draw each agent as a triangle at its current position
        angle = math.radians(45)
        point1 = (scaled_x + self.size * math.cos(angle), scaled_y + self.size * math.sin(angle))
        point2 = (scaled_x + self.size * math.cos(angle + 2.5), scaled_y + self.size * math.sin(angle + 2.5))
        point3 = (scaled_x + self.size * math.cos(angle - 2.5), scaled_y + self.size * math.sin(angle - 2.5))

        pygame.draw.polygon(screen, color, [point1, point2, point3])