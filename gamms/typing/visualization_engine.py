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
    def add_artist(self, name: str, data: Dict[str, Any]) -> None:
        """
        Add a custom artist or object to the visualization.

        This method adds a custom artist or object to the visualization, allowing
        for additional elements to be displayed alongside the graph and agents.
        The artist can be used to render custom shapes, text, images, or other
        visual components within the visualization.

        Args:
            name (str): The unique name identifier for the custom artist.
            data (Dict[str, Any]): A dictionary containing the data and settings
                for the custom artist. The structure of the data may vary based
                on the type of artist being added.
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
    def human_input(self, state: Dict[str, Any]) -> None:
        """
        Process input from a human player or user.

        This method handles input data provided by a human user, allowing for
        interactive control or modification of the visualization. It can be used
        to receive commands, adjust settings, or influence the simulation based
        on user actions.

        Args:
            state (Dict[str, Any]): A dictionary containing the current state of
                the system or the input data from the user. Expected keys may include:
                - `command` (str): The command issued by the user.
                - `parameters` (Dict[str, Any]): Additional parameters related to the command.
                - Other state-related information as needed.

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
