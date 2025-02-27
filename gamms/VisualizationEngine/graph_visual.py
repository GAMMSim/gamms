import pygame #FIXME

class GraphVisual:
    def __init__(self, graph, width=1980, height=1080):
        self.graph = graph
        self.width = width
        self.height = height
        self.screen = None
        self.screen = None
        self.zoom = 1
        # Find the min and max x, y coordinates for scaling
        self.x_min = min(node.x for node in self.graph.nodes.values())
        self.x_max = max(node.x for node in self.graph.nodes.values())
        self.y_min = min(node.y for node in self.graph.nodes.values())
        self.y_max = max(node.y for node in self.graph.nodes.values())
        self.offset = (0.0, 0.0)

        # Data Storage. INTERNAL USE ONLY
        self.__edge_list = set()
        self.__node_list = set()
        self.__node_color_list = {}
        self.__edge_color_list = {}
        self.__node_size_list = {}
        self.__edge_size_list = {}

        # Staticly updated surface object
        self.__mapObject = None
        self.__surfaceWidth = 0
        self.__surfaceHeight = 0

        # Set the data stores. 
        self._initalize_data()
        

    # Internal Methouds
    def _initalize_data(self) -> None:
        for edge in self.graph.edges.values():
            remappedEdgeID = (edge.source << 32) + edge.target
            self.__edge_list.add(remappedEdgeID)
            remappedEdgeID = (edge.target << 32) + edge.source
            self.__edge_list.add(remappedEdgeID)

        for node in self.graph.nodes.values():
            self.__node_list.add(node.id)

    def _initalize_surface(self):
        # need screen size
        (x1 , y1) = self.ScalePositionToScreen((self.x_min, self.y_min))
        (x2 , y2) = self.ScalePositionToScreen((self.x_max, self.y_max))
        self.__surfaceWidth = abs(int(x1 - x2))
        self.__surfaceHeight = abs(int(y1 - y2))

        print(self.__surfaceWidth)
        self.__mapObject = pygame.Surface((self.__surfaceWidth, self.__surfaceHeight ))

        self.__mapObject.fill((50, 50, 50))

    def getGraphSurface(self):
        return self.__mapObject
    
    def getGraphSurfaceDimentions(self):
        return (self.__surfaceWidth, self.__surfaceHeight)


    # Color Set Methouds
    def setNodeColor(self, node, color = (255, 255, 255)):
        if node.id in self.__node_list:
            self.__node_color_list[node.id] = color
        else:
            print(f"Warning: setNodeColorByID({node.id}) not found.")

    def setEdgeColor(self, source_id, target_id, color = (255, 255, 255)):
        """Edge id is a bitwise encoding."""
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_list:
            self.__edge_color_list[edge_id] = color
        else:
            print(f"Warning: setEdgeColor({edge_id}) not found.")

    def setNodeColorByID(self, node_id, color = (255, 255, 255)):
            if node_id in self.__node_list:
                self.__node_color_list[node_id] = color
            else:
                print(f"Warning: setNodeColorByID({node_id}) not found.")

    def setEdgeColorByID(self, edge_id, color = (255, 255, 255)):
        if edge_id in self.__edge_list:
            self.__edge_color_list[edge_id] = color
        else:
            print(f"Warning: setEdgeColorByID({edge_id}) not found.")

    # Color Get Methouds
    def getEdgeColorById(self, edge_id):
        if edge_id in self.__edge_color_list:
            return self.__edge_color_list[edge_id] 
        else:
            return None
        
    def getNodeColorById(self, node_id):
        if node_id in self.__node_color_list:
            return self.__node_color_list[node_id] 
        else:
            return None
        
    def getEdgeColor(self, source_id, target_id):
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_color_list:
            return self.__edge_color_list[edge_id]
        else:
            return None

    def getNodeColor(self, node):
        if node.id in self.__node_color_list:
            return self.__node_color_list[node.id]
        else:
            return None

    # Reset Color Functions
    def resetNodeColor(self):
        self.__node_color_list = {}

    def resetEdgeColor(self):
        self.__edge_color_list = {}

    def resetGraphColor(self):
        self.resetNodeColor()
        self.resetEdgeColor()

    # Graph Math Methouds
    def GraphCenter(self):
        """Gets the center of a graph."""
        return (((self.x_max - self.x_min ) / 2) + self.x_min, ((self.y_max - self.y_min) / 2) + self.y_min)

    def setZoom(self, zoom: float):
        self.zoom = zoom
        return self.zoom
    
    def setGraph(self, graph):
        self.graph = graph

    def setRenderManager(self, render_manager):
        self.render_manager = render_manager
        self.render_manager.camera_size = max(self.x_max - self.x_min, self.y_max - self.y_min)
        self._initalize_surface()

    def getRenderManager(self, render_manager):
        return self.render_manager
    
    def getUpperLeftCorner(self):
        return self.ScalePositionToScreen((self.x_min, self.y_max))

    def ScalePositionToScreen(self, position: tuple[float, float]) -> tuple[float, float]:
        """Scale a coordinate value to fit within the screen."""
        graph_center = self.GraphCenter()
        map_position = ((position[0] - graph_center[0]),(position[1] - graph_center[1]))
        map_position = self.render_manager.world_to_screen(map_position[0] + self.render_manager.camera_x, map_position[1] + self.render_manager.camera_y)
        return map_position
    
    def ScalePositionToSurface(self, position: tuple[float, float]) -> tuple[float, float]:
        """Scale a coordinate value to fit within the screen."""

        #Graph coordnates starts at 0,0 in the upper corner. 
        centerWidth = self.__surfaceWidth / 2
        centerHeight = self.__surfaceHeight / 2

        
        return map_position
