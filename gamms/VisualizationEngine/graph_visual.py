
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

        # Set the data stores. 
        self._initalize_data()

    # Internal Methouds
    def _initalize_data(self) -> None:
        for edge in self.graph.edges.values():
            self.__edge_list.add(edge.id)

        for node in self.graph.nodes.values():
            self.__node_list.add(node.id)

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
        if edge_id is self.__edge_color_list[edge_id]:
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
    
    def setCamera(self, camera):
        self.camera = camera

    def ScalePositionToScreen(self, position: tuple[float, float]) -> tuple[float, float]:
        """Scale a coordinate value to fit within the screen."""
        graph_center = self.GraphCenter()
        # Graph comes in the form of KM. Need to convert the KM to scale for M. One unit = 1m
        screen_scale = 111139 / 100

        map_position = (screen_scale * (position[0] - graph_center[0]),screen_scale * (position[1] - graph_center[1]))
        map_position = self.camera.world_to_screen(map_position[0] + self.camera.x, map_position[1] + self.camera.y)
        #map_position = (map_position[0] + self.offset[0], map_position[1] + self.offset[1])
        return map_position
