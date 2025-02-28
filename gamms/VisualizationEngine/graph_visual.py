
class GraphVisual:
    def __init__(self, graph, width=1980, height=1080):

        # == External Variables ==
        self.graph = graph
        self.width = width
        self.height = height
        self.screen = None
        self.screen = None
        self.zoom = 1
        # == Graph Variables ==
        self.x_min = min(node.x for node in self.graph.nodes.values())
        self.x_max = max(node.x for node in self.graph.nodes.values())
        self.y_min = min(node.y for node in self.graph.nodes.values())
        self.y_max = max(node.y for node in self.graph.nodes.values())
        self.graph_center = self.GraphCenter()

        # == Data Storage ==
        self.__edge_list = set()
        self.__node_list = set()
        
        # == UI Render Cache == 
        self.__node_UI_color_list = {}
        self.__edge_UI_color_list = {}

        # == Render Cache ==
        self.__node_render_list = {} # <= (cull, position, color, size)
        self.__edge_render_list = {} # <= (cull, position, color)

        # == Single Initalization ==
        self._initalize_data()
        self._initialize_edge_data()
        self._initialize_node_data()


    #  == Internal Methouds ==
    # ========================
    def _initalize_data(self) -> None:

        # Clean and remapping
        for edge in self.graph.edges.values():
            # Forward Edge
            remappedEdgeID = (edge.source << 32) + edge.target
            self.__edge_list.add(remappedEdgeID)
            # Backward Edge
            remappedEdgeID = (edge.target << 32) + edge.source
            self.__edge_list.add(remappedEdgeID)
            
        for node in self.graph.nodes.values():
            self.__node_list.add(node.id)

        # Populate based on set
        for remappedEdgeID in self.__edge_list:
            # Populate render list.
            self.__edge_render_list[remappedEdgeID] = (True, {}, (255, 255, 255))

        for nodeID in self.__node_list:
            # Populate render list.
            self.__node_render_list[nodeID] = (True, (0.0,0.0), (255, 255, 255), 4.0 )

    def _initialize_edge_data(self) -> None:
        # If linestring is present, draw it as a curve
        for edge in self.graph.edges.values():

            source = self.graph.nodes[edge.source]
            target = self.graph.nodes[edge.target]

            if edge.linestring:
                #linestring[1:-1]
                linestring = [(source.x, source.y)] + [(x, y) for (x, y) in edge.linestring.coords] + [(target.x, target.y)]
                self.setEdgePositions(edge.source, edge.target, linestring)

            else:
                # Straight line
                source_position = (source.x, source.y)
                target_position = (target.x, target.y)
                linestring = [source_position, target_position]
                self.setEdgePositions(edge.source, edge.target, linestring)

    def _initialize_node_data(self) -> None:
        for node in self.graph.nodes.values():
            self.setNodePosition(node.id, (node.x, node.y))


    # == Graph Set Methouds ==
    # ========================
    def setNodeCull(self, node, cull: bool):
        if node in self.__node_list:
            self.__node_render_list[node] = (cull, self.__node_render_list[node][1],  self.__node_render_list[node][2], self.__node_render_list[node][3])
        else:
            print(f"Warning: setNodeCull({node}) not found.")
        return

    def setEdgeCull(self, source_id, target_id, cull: bool):
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_list:
            self.__edge_render_list[edge_id] = (cull, self.__edge_render_list[edge_id][1], self.__edge_render_list[edge_id][2])
        else:
            print(f"Warning: setEdgeCull({edge_id}) not found.")
        return

    def setNodePosition(self, node, position):
        if node in self.__node_list:
            self.__node_render_list[node] = (self.__node_render_list[node][0], position, self.__node_render_list[node][2], self.__node_render_list[node][3] )
        else:
            print(f"Warning: setNodePosition({node}) not found.")
        return

    def setEdgePositions(self, source_id, target_id, position):
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_list:
            self.__edge_render_list[edge_id] = (self.__edge_render_list[edge_id][0], position, self.__edge_render_list[edge_id][2] )
        else:
            print(f"Warning: setEdgePositions({edge_id}) not found.")
        return

    def setEdgeColor(self, source_id, target_id, color: tuple[float, float]):
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_list:
            self.__edge_render_list[edge_id] = (self.__edge_render_list[edge_id][0], self.__edge_render_list[edge_id][1], color)
        else:
            print(f"Warning: setEdgeColor({edge_id}) not found.")
        return
    
    def setNodeColor(self, node, color: tuple[float, float]):
        if node in self.__node_list:
            self.__node_render_list[node]= (self.__node_render_list[node][0], self.__node_render_list[node][1], color, self.__node_render_list[node][3] )
        else:
            print(f"Warning: setNodeColor({node}) not found.")
        return
    
    def setNodeScale(self, node, scale : float):
        if node in self.__node_list:
            self.__node_render_list[node] = (self.__node_render_list[node][0], self.__node_render_list[node][1],  self.__node_render_list[node][2], scale)
        else:
            print(f"Warning: setNodeScale({node}) not found.")
        return
    


    # == Graph Get Methouds ==
    # ========================
    def getNodeCull(self, node):
        if node in self.__node_list:
            return self.__node_render_list[node][0]
        else:
            print(f"Warning: getNodeCull({node}) not found.")
            return None

    def getEdgeCull(self, source_id, target_id):
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_list:
            return self.__edge_render_list[edge_id][0]
        else:
            print(f"Warning: getEdgeCull({edge_id}) not found.")
            return None

    def getNodePosition(self, node):
        if node in self.__node_list:
            return self.__node_render_list[node][1]
        else:
            print(f"Warning: getNodePosition({node}) not found.")
            return None

    def getEdgePositions(self, source_id, target_id):
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_list:
            return self.__edge_render_list[edge_id][1]
        else:
            print(f"Warning: getEdgePositions({edge_id}) not found.")
            return None

    def getEdgeColor(self, source_id, target_id):
        edge_id = (source_id << 32) + target_id
        
        if edge_id in self.__edge_list:
            return self.__edge_render_list[edge_id][2]
        
        else:
            print(f"Warning: getEdgeColor({edge_id}) not found.")
            return None
    
    def getNodeColor(self, node):
        if node in self.__node_list:
            return self.__node_render_list[node][2]
        else:
            print(f"Warning: getNodeColor({node}) not found.")
            return None

    def getNodeScale(self, node):
        if node in self.__node_list:
            return self.__node_render_list[node][3]
        else:
            print(f"Warning: getNodeScale({node}) not found.")
            return None



    # == Reset Methouds ==
    # ====================
    def clearNodeCache(self):
        for nodeID in self.__node_list:
            # Populate render list.
            self.__node_render_list[nodeID] = (True, self.__node_render_list[nodeID][1], self.__node_render_list[nodeID][2], self.__node_render_list[nodeID][3] )

    def clearEdgeCache(self):
        for edgeID in self.__edge_list:
            # Populate render list.
            self.__edge_render_list[edgeID] = (True, self.__edge_render_list[edgeID][1], self.__edge_render_list[edgeID][2] )

    def clearGraphCache(self):
        self.clearNodeCache()
        self.clearEdgeCache()



    # == Color UI Set Methouds ==
    # ===========================
    def setNodeUIColor(self, node, color = (255, 255, 255)):
        if node.id in self.__node_list:
            self.__node_UI_color_list[node.id] = color
        else:
            print(f"Warning: setNodeColorByID({node.id}) not found.")

    def setEdgeUIColor(self, source_id, target_id, color = (255, 255, 255)):
        """Edge id is a bitwise encoding."""
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_list:
            self.__edge_UI_color_list[edge_id] = color
        else:
            print(f"Warning: setEdgeColor({edge_id}) not found.")



    # == Color UI Get Methouds ==   
    # ===========================     
    def getEdgeUIColor(self, source_id:int, target_id:int):
        edge_id = (source_id << 32) + target_id
        if edge_id in self.__edge_UI_color_list:
            return self.__edge_UI_color_list[edge_id]
        else:
            return None

    def getNodeUIColor(self, nodeID:int):
        if nodeID in self.__node_UI_color_list:
            return self.__node_UI_color_list[nodeID]
        else:
            return None



    # == Reset Color UI Functions == 
    # ==============================
    def resetNodeUIColor(self):
        self.__node_UI_color_list = {}

    def resetEdgeUIColor(self):
        self.__edge_UI_color_list = {}

    def resetGraphUIColor(self):
        self.resetNodeUIColor()
        self.resetEdgeUIColor()



    # == Graph Math Methouds == 
    # =========================
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

    def ScalePositionToScreen(self, position: tuple[float, float]) -> tuple[float, float]:
        """Scale a coordinate value to fit within the screen."""
        map_position = ((position[0] - self.graph_center[0]),(position[1] - self.graph_center[1]))
        map_position = self.render_manager.world_to_screen(map_position[0] + self.render_manager.camera_x, map_position[1] + self.render_manager.camera_y)
        return map_position
