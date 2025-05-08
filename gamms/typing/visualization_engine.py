from gamms.typing.artist import IArtist
from typing import Dict, Any, List, Tuple, Union
from abc import ABC, abstractmethod

ColorType = Union[
    Tuple[Union[int, float], Union[int, float], Union[int, float]],
    Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]
]

class IVisualizationEngine(ABC):
    """
    Abstract base class representing a visualization engine.

    The visualization engine is responsible for rendering the graph and agents,
    handling simulation updates, processing human inputs, and managing the
    overall visualization lifecycle.
    """

    @abstractmethod
    def set_graph_visual(self, **kwargs: Dict[str, Any]) -> IArtist:
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
    def set_agent_visual(self, name: str, **kwargs: Dict[str, Any]) -> IArtist:
        """
        Configure the visual representation of a specific agent.

        This method sets up visual parameters for an individual agent, allowing
        customization of how the agent is displayed within the visualization.

        Args:
            name (str): The unique name identifier of the agent to configure.
            **kwargs: Arbitrary keyword arguments representing visual settings.
                Possible keys include:
                - `color` (str): The color to represent the agent.
                - `shape` (str): The shape to use for the agent's representation.
                - `size` (float): The size of the agent in the visualization.
        """
        pass

    @abstractmethod
    def set_sensor_visual(self, name: str, **kwargs: Dict[str, Any]) -> IArtist:
        """
        Configure the visual representation of a specific sensor.

        This method sets up visual parameters for an individual sensor, allowing
        customization of how the sensor is displayed within the visualization.

        Args:
            name (str): The unique name identifier of the sensor to configure.
            **kwargs: Arbitrary keyword arguments representing visual settings.
                Possible keys include:
                - `color` (str): The color to represent the sensor.
                - `shape` (str): The shape to use for the sensor's representation.
                - `size` (float): The size of the sensor in the visualization.
        
        Raises:
            KeyError: If the sensor with the specified name does not exist.
            ValueError: If the sensor type is not supported for default visualization.        
        """
        pass

    @abstractmethod
    def add_artist(self, name: str, artist: Union[IArtist, Dict[str, Any]]) -> IArtist:
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
    def render_circle(self, x: float, y: float, radius: float, color: Tuple[Union[int, float], Union[int, float], Union[int, float]], perform_culling_test: bool):
        """
        Render a circle shape at the specified position with the given radius and color.

        Args:
            x (float): The x-coordinate of the circle's center.
            y (float): The y-coordinate of the circle's center.
            radius (float): The radius of the circle.
            color (Tuple[Union[int, float], Union[int, float], Union[int, float]]): The color of the circle in RGB format.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_rectangle(self, x: float, y: float, width: float, height: float, color: Tuple[Union[int, float], Union[int, float], Union[int, float]], perform_culling_test: bool):
        """
        Render a rectangle shape at the specified position with the given dimensions and color.

        Args:
            x (float): The x-coordinate of the rectangle's center.
            y (float): The y-coordinate of the rectangle's center.
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
            color (Tuple[Union[int, float], Union[int, float], Union[int, float]]): The color of the rectangle in RGB format.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_line(self, start_x: float, start_y: float, end_x: float, end_y: float, color: Tuple[Union[int, float], Union[int, float], Union[int, float]], width: int, is_aa: bool, perform_culling_test: bool):
        """
        Render a line segment between two points with the specified color and width.

        Args:
            start_x (float): The x-coordinate of the starting point.
            start_y (float): The y-coordinate of the starting point.
            end_x (float): The x-coordinate of the ending point.
            end_y (float): The y-coordinate of the ending point.
            color (Tuple[Union[int, float], Union[int, float], Union[int, float]]): The color of the line in RGB format.
            width (int): The width of the line in pixels. Only non-antialiasing lines supports width.
            is_aa (bool): Whether to use antialiasing for smoother rendering.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_linestring(self, points: List[Tuple[float, float]], color: Tuple[Union[int, float], Union[int, float], Union[int, float]], width: int, closed: bool, is_aa: bool, perform_culling_test: bool):
        """
        Render a series of connected line segments between multiple points.

        Args:
            points (list[Tuple[float, float]]): A list of (x, y) coordinate tuples defining the line segments.
            color (Tuple[Union[int, float], Union[int, float], Union[int, float]]): The color of the lines in RGB format.
            width (int): The width of the lines in pixels. Only non-antialiasing lines supports width.
            closed (bool): Whether the line segments form a closed shape.
            is_aa (bool): Whether to use antialiasing for smoother rendering.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_polygon(self, points: List[Tuple[float, float]], color: Tuple[Union[int, float], Union[int, float], Union[int, float]], width: int,
                       perform_culling_test: bool):
        """
        Render a polygon shape or outline defined by a list of vertices with the specified color and width.

        Args:
            points (list[Tuple[float, float]]): A list of (x, y) coordinate tuples defining the polygon vertices.
            color (Tuple[Union[int, float], Union[int, float], Union[int, float]]): The color of the polygon in RGB format.
            width (int): The width of the polygon outline in pixels. If equal to 0, the polygon is filled.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_text(self, text: str, x: float, y: float, color: Tuple[Union[int, float], Union[int, float], Union[int, float]], perform_culling_test: bool):
        """
        Render text at the specified position with the given content and color.

        Args:
            text (str): The text content to display.
            x (float): The x-coordinate of the text's center position.
            y (float): The y-coordinate of the text's center position.
            color (Tuple[Union[int, float], Union[int, float], Union[int, float]]): The color of the text in RGB format.
            perform_culling_test (bool): Whether to perform culling.
        """
        pass

    @abstractmethod
    def render_layer(self, layer_id: int) -> None:
        """
        Render the specified layer of the visualization.

        Args:
            layer_id (int): The layer number to render.
        """
        pass
