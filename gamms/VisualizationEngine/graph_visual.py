import pygame

class GraphVisual:
    def __init__(self, graph, width=1980, height=1080, draw_id=False, node_color=None, edge_color=None):
        self.graph = graph
        self.width = width
        self.height = height
        self.screen = None
        self.screen = None
        self.zoom = 1
        self.draw_id = draw_id
        self.node_color = node_color
        self.edge_color = edge_color
        # Find the min and max x, y coordinates for scaling
        self.x_min = min(node.x for node in self.graph.nodes.values())
        self.x_max = max(node.x for node in self.graph.nodes.values())
        self.y_min = min(node.y for node in self.graph.nodes.values())
        self.y_max = max(node.y for node in self.graph.nodes.values())
        self.offset = (0.0, 0.0)

    def GraphCenter(self):
        """Gets the center of a graph."""
        return (((self.x_max - self.x_min ) / 2) + self.x_min, ((self.y_max - self.y_min) / 2) + self.y_min)

    def setZoom(self, zoom: float):
        self.zoom = zoom
        return self.zoom
    
    def setGraph(self, graph):
        self.graph = graph
    
    def setCamera(self, camera):
        self.camera = camera
        camera.size = max(self.x_max - self.x_min, self.y_max - self.y_min)

    def ScalePositionToScreen(self, position: tuple[float, float]) -> tuple[float, float]:
        """Scale a coordinate value to fit within the screen."""
        graph_center = self.GraphCenter()
        map_position = ((position[0] - graph_center[0]),(position[1] - graph_center[1]))
        map_position = self.camera.world_to_screen(map_position[0] + self.camera.x, map_position[1] + self.camera.y)
        return map_position

    def draw_node(self, screen, node, color=None):
        # """Draw a node as a circle with a light greenish color."""
        if color is None:
            color = self.node_color

        position = (node.x, node.y)
        (x, y) = self.ScalePositionToScreen(position)
        if self.is_map_point_viewable((x, y)):
            pygame.draw.circle(screen, color, (int(x), int(y)), 4)  # Light greenish color
            # Draw node ID if draw_id is True
            if self.draw_id:
                font = pygame.font.Font(None, 40)
                text = font.render(str(node.id), True, (0, 0, 0))
                text_rect = text.get_rect(center=(int(x), int(y) + 10))
                screen.blit(text, text_rect)

    def draw_edge(self, screen, edge, color=None):
        """Draw an edge as a curve or straight line based on the linestring."""
        if color is None:
            color = self.edge_color

        source = self.graph.nodes[edge.source]
        target = self.graph.nodes[edge.target]

        source_screen_pos = self.ScalePositionToScreen((source.x, source.y))
        target_screen_pos = self.ScalePositionToScreen((target.x, target.y))

        if self.is_map_line_viewable(source_screen_pos, target_screen_pos):
            # If linestring is present, draw it as a curve
            if edge.linestring:
                #linestring[1:-1]
                linestring = [(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] + [(target.x, target.y)]
                scaled_points = [
                    (self.ScalePositionToScreen((x, y)))
                    for x, y in linestring
                ]
                pygame.draw.aalines(screen, color, False, scaled_points, 2)
            else:
                # Straight line
                source_position = (source.x, source.y)
                target_position = (target.x, target.y)
                (x1, y1) = self.ScalePositionToScreen(source_position)
                (x2, y2) = self.ScalePositionToScreen(target_position)
                pygame.draw.line(screen, color, (int(x1), int(y1)), (int(x2), int(y2)), 2)

    def MoveGraphPosition(self, direction: tuple[float, float]):
        self.offset = (self.offset[0] + direction[0], self.offset[1] + direction[1])
        

    # Assumes map coordnates
    def is_map_point_viewable(self, position: tuple[float, float]) -> bool:
        return (position[0] >= 0 and position[0] <= self.width and position[1] >= 0 and position[1] <= self.height)

    # Assumes map coordnates
    def is_map_line_viewable(self, source: tuple[float, float], target: tuple[float, float] ) -> bool:
        # Check left side of screen
        #      |       |
        # -----A-------C-----
        #      |       |
        # -----B-------D-----
        #      |       |
        # A-B check
        if(source[0] < 0 and target[0] < 0):
            return False
        
        # C-D check
        if(source[0] > self.width and target[0] > self.width):
            return False
        
        # A-C check
        if(source[1] < 0 and target[1] < 0):
            return False
        
         # B-D check
        if(source[1] > self.height and target[1] > self.height):
            return False

        return True
    
    def draw_graph(self, screen):
        """Draw the entire graph (edges and nodes)."""
        # Center of Graph:
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        for edge in self.graph.edges.values():
            self.draw_edge(screen, edge)
        for node in self.graph.nodes.values():
            self.draw_node(screen, node)
        


