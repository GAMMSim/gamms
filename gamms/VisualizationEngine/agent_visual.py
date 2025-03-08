# from gamms.VisualizationEngine.utils import string_to_color
# from shapely.geometry import LineString
# from typing import Optional


# class AgentVisual:
#     def __init__(self, name, start_position, **kwargs):
#         """
#         Initialize AgentVisual with an AgentEngine.
#         """
#         self.name = name
#         color = kwargs.get('color', 'black')
        
#         self.color = string_to_color(color)
#         self.size = kwargs.get('size', 8)
#         # self.shape = kwargs.get('shape', None)
#         self.prev_position = None
#         self.target_position = None
#         self._current_edge: Optional[LineString] = None
#         self.position = start_position

#     def set_color(self, color = (255, 255, 255)):
#         self.color = color
#         return
    
#     def set_size(self, size = 8):
#         self.size = size
#         return
    
#     def start_simulation_lerp(self, prev_position, target_position, edge):
#         self.prev_position = prev_position
#         self.target_position = target_position
#         self._current_edge = edge

#     def update_simulation(self, alpha: float):
#         """
#         Update the simulation with the alpha value.
#         """
#         if self.prev_position is not None and self.target_position is not None:
#             if self._current_edge is not None:
#                 point = self._current_edge.interpolate(alpha, True)
#                 self.position = (point.x, point.y)
#             else:
#                 self.position = (self.prev_position[0] + alpha * (self.target_position[0] - self.prev_position[0]),
#                                  self.prev_position[1] + alpha * (self.target_position[1] - self.prev_position[1]))
