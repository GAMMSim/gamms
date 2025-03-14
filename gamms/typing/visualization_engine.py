from gamms.VisualizationEngine import Color
from gamms.typing.artist import IArtist
from typing import Dict, Any
from abc import ABC, abstractmethod


class IVisualizationEngine(ABC):
    """
    Abstract base class representing a visualization engine.

    The visualization engine is responsible for rendering the graph and agents,
    handling simulation updates, processing human inputs, and managing the
    overall visualization lifecycle.
    """

    @abstractmethod
    def set_graph_visual(self, **kwargs) -> None:
        """
        Configure the visual representation of the graph.

        This method sets up visual parameters such as colors, sizes, layouts,
        and other graphical attributes for the entire graph. It allows customization
        of how the graph is displayed to the user.

        Args:
            **kwargs: Arbitrary keyword arguments representing visual settings.
                Possible keys include:
                - `color_scheme` (str): The color scheme to use for nodes and edges.
                - `layout` (str): The layout algorithm for positioning nodes.
                - `node_size` (float): The size of the graph nodes.
                - `edge_width` (float): The width of the graph edges.
                - Additional visual parameters as needed.

        Raises:
            ValueError: If any of the provided visual settings are invalid.
            TypeError: If the types of the provided settings do not match expected types.
        """
        pass

    @abstractmethod
    def set_agent_visual(self, agent_name: str, **kwargs) -> None:
        """
        Configure the visual representation of a specific agent.

        This method sets up visual parameters for an individual agent, allowing
        customization of how the agent is displayed within the visualization.

        Args:
            agent_name (str): The unique name identifier of the agent to configure.
            **kwargs: Arbitrary keyword arguments representing visual settings.
                Possible keys include:
                - `color` (str): The color to represent the agent.
                - `shape` (str): The shape to use for the agent's representation.
                - `size` (float): The size of the agent in the visualization.
                - `icon` (str): Path to an icon image to represent the agent.
                - Additional visual parameters as needed.

        Raises:
            KeyError: If no agent with the specified `agent_name` exists.
            ValueError: If any of the provided visual settings are invalid.
            TypeError: If the types of the provided settings do not match expected types.
        """
        pass

    @abstractmethod
    def set_sensor_visual(self, sensor_name: str, **kwargs) -> None:
        """
        Configure the visual representation of a specific sensor.

        """
        pass

    @abstractmethod
    def add_artist(self, name: str, artist: IArtist) -> None:
        """
        Add a custom artist or object to the visualization.

        This method adds a custom artist or object to the visualization, allowing
        for additional elements to be displayed alongside the graph and agents.
        The artist can be used to render custom shapes, text, images, or other
        visual components within the visualization.

        Args:
            name (str): The unique name identifier for the custom artist.
            artist (IArtist): The artist object representing the custom visualization element.
        """
        pass

    @abstractmethod
    def remove_artist(self, name: str) -> None:
        """
        Remove a custom artist or object from the visualization.

        This method removes a custom artist or object from the visualization,
        effectively hiding or deleting the element from the display.

        Args:
            name (str): The unique name identifier of the custom artist to remove.
        """
        pass

    @abstractmethod
    def simulate(self) -> None:
        """
        Execute a simulation step to update the visualization.

        This method advances the simulation by one step, updating the positions,
        states, and visual representations of the graph and agents. It should be
        called repeatedly within a loop to animate the visualization in real-time.

        Raises:
            RuntimeError: If the simulation cannot be advanced due to internal errors.
            ValueError: If the simulation parameters are invalid or inconsistent.
        """
        pass

    @abstractmethod
    def human_input(self, agent_name: str, state: Dict[str, Any]) -> int:
        """
        Process input from a human player or user.

        This method handles input data provided by a human user, allowing for
        interactive control or modification of the visualization. It can be used
        to receive commands, adjust settings, or influence the simulation based
        on user actions.

        Args:
            agent_name (str): The unique name of the agent.
            state (Dict[str, Any]): A dictionary containing the current state of
                the system or the input data from the user. Expected keys may include:
                - `command` (str): The command issued by the user.
                - `parameters` (Dict[str, Any]): Additional parameters related to the command.
                - Other state-related information as needed.

        Returns:
            int: The target node id selected by the user.

        Raises:
            ValueError: If the input `state` contains invalid or unsupported commands.
            KeyError: If required keys are missing from the `state` dictionary.
            TypeError: If the types of the provided input data do not match expected types.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the visualization engine and clean up resources.

        This method is called when the simulation or application is exiting.
        It should handle the graceful shutdown of the visualization engine,
        ensuring that all resources are properly released and that the display
        is correctly closed.

        Raises:
            RuntimeError: If the engine fails to terminate gracefully.
            IOError: If there are issues during the cleanup process.
        """
        pass

    @abstractmethod
    def render_circle(self, x: float, y: float, radius: float, color: tuple=Color.Black, layer = -1,
                      perform_culling_test: bool=True):
        """
        Render a circle shape at the specified position with the given radius and color.

        Args:
            x (float): The x-coordinate of the circle's center.
            y (float): The y-coordinate of the circle's center.
            radius (float): The radius of the circle.
            color (tuple): The color of the circle in RGB format.
            layer (int): The layer to render the circle on.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_rectangle(self, x: float, y: float, width: float, height: float, color: tuple = Color.Black, layer = -1,
                         perform_culling_test: bool = True):
        """
        Render a rectangle shape at the specified position with the given dimensions and color.

        Args:
            x (float): The x-coordinate of the rectangle's center.
            y (float): The y-coordinate of the rectangle's center.
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
            color (tuple): The color of the rectangle in RGB format.
            layer (int): The layer to render the rectangle on.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: tuple = Color.Black,
                    width: int = 1, layer = -1, is_aa: bool = False, perform_culling_test: bool = True):
        """
        Render a line segment between two points with the specified color and width.

        Args:
            start_x (float): The x-coordinate of the starting point.
            start_y (float): The y-coordinate of the starting point.
            end_x (float): The x-coordinate of the ending point.
            end_y (float): The y-coordinate of the ending point.
            color (tuple): The color of the line in RGB format.
            width (int): The width of the line in pixels. Only non-antialiasing lines supports width.
            layer (int): The layer to render the line on.
            is_aa (bool): Whether to use antialiasing for smoother rendering.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_lines(self, points: list[tuple[float, float]], color: tuple = Color.Black, width: int = 1, layer = -1, closed=False,
                     is_aa: bool = False, perform_culling_test: bool = True):
        """
        Render a series of connected line segments between multiple points.

        Args:
            points (list[tuple[float, float]]): A list of (x, y) coordinate tuples defining the line segments.
            color (tuple): The color of the lines in RGB format.
            width (int): The width of the lines in pixels. Only non-antialiasing lines supports width.
            layer (int): The layer to render the lines on.
            closed (bool): Whether the line segments form a closed shape.
            is_aa (bool): Whether to use antialiasing for smoother rendering.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_polygon(self, points: list[tuple[float, float]], color: tuple = Color.Black, width: int = 0, layer = -1,
                       perform_culling_test: bool = True):
        """
        Render a polygon shape or outline defined by a list of vertices with the specified color and width.

        Args:
            points (list[tuple[float, float]]): A list of (x, y) coordinate tuples defining the polygon vertices.
            color (tuple): The color of the polygon in RGB format.
            width (int): The width of the polygon outline in pixels. If equal to 0, the polygon is filled.
            layer (int): The layer to render the polygon on.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_text(self, text: str, x: float, y: float, color: tuple = Color.Black, layer = -1, perform_culling_test: bool=True):
        """
        Render text at the specified position with the given content and color.

        Args:
            text (str): The text content to display.
            x (float): The x-coordinate of the text's center position.
            y (float): The y-coordinate of the text's center position.
            color (tuple): The color of the text in RGB format.
            layer (int): The layer to render the text on.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def fill_layer(self, layer_id: int, color: tuple):
        """
        Fill a layer with the specified color.

        Args:
            layer_id (int): The unique identifier of the layer to fill.
            color (tuple): The color to fill the layer with in RGB format.
        """
        pass

    @abstractmethod
    def render_layer(self, layer_id: int, left: float, top: float, width: float, height: float):
        """
        Render a layer to the screen with the specified dimensions at the given position.

        Args:
            layer_id (int): The unique identifier of the layer to render.
            left (float): The x-coordinate of the left edge of the layer.
            top (float): The y-coordinate of the top edge of the layer.
            width (float): The width of the layer.
            height (float): The height of the layer.
        """
        pass

    @abstractmethod
    def is_waiting_simulation(self) -> bool:
        """
        Check if the visualization engine is waiting for simulation to complete.

        Returns:
            bool: A boolean indicating whether the engine is waiting for simulation.
        """
        pass

    @abstractmethod
    def is_waiting_input(self) -> bool:
        """
        Check if the visualization engine is waiting for user input.

        Returns:
            bool: A boolean indicating whether the engine is waiting for user input.
        """
        pass

    @abstractmethod
    def on_artist_change_layer(self) -> None:
        """
        Notify the visualization engine that one or more artists has changed its layer.

        This method should be called whenever an artist changes its layer to
        ensure that the visualization engine updates the rendering accordingly.
        """
        pass