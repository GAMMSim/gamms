from abc import ABC, abstractmethod
from gamms.typing import (
    IInternalContext,
    ISensorEngine,
    IVisualizationEngine,
    IAgentEngine,
    IGraphEngine,
)


class IContext(ABC):
    """
    Abstract base class representing the overall context of the system.

    The `IContext` interface serves as a central point of access to various engine
    components within the system, including sensors, visualization, agents, and
    graph management. It provides properties to retrieve instances of these engines,
    facilitating coordinated interactions and data flow between different system parts.
    """

    @property
    @abstractmethod
    def ictx(self) -> IInternalContext:
        """
        Retrieve the internal context of the system.

        The internal context encapsulates core configurations, state information,
        and shared resources necessary for the operation of various system components.

        Returns:
            IInternalContext: An instance representing the internal context.

        Raises:
            RuntimeError: If the internal context is not properly initialized.
        """
        pass

    @property
    @abstractmethod
    def sensor(self) -> ISensorEngine:
        """
        Retrieve the sensor engine.

        The sensor engine manages all sensor-related operations, including the creation,
        updating, and retrieval of sensors. It facilitates data collection from various
        sources within the system.

        Returns:
            ISensorEngine: An instance of the sensor engine.

        Raises:
            RuntimeError: If the sensor engine is not properly initialized.
        """
        pass

    @property
    @abstractmethod
    def visual(self) -> IVisualizationEngine:
        """
        Retrieve the visualization engine.

        The visualization engine handles the rendering and display of the system's
        graphical elements, such as graphs and agents. It manages visual configurations
        and updates the visualization based on simulation states.

        Returns:
            IVisualizationEngine: An instance of the visualization engine.

        Raises:
            RuntimeError: If the visualization engine is not properly initialized.
        """
        pass

    @property
    @abstractmethod
    def agent(self) -> IAgentEngine:
        """
        Retrieve the agent engine.

        The agent engine manages the lifecycle and behavior of agents within the system.
        It handles agent creation, state management, and interaction with other system
        components.

        Returns:
            IAgentEngine: An instance of the agent engine.

        Raises:
            RuntimeError: If the agent engine is not properly initialized.
        """
        pass

    @property
    @abstractmethod
    def graph(self) -> IGraphEngine:
        """
        Retrieve the graph engine.

        The graph engine manages the underlying graph structure, including nodes and
        edges. It provides functionalities to modify the graph, retrieve graph elements,
        and maintain graph integrity.

        Returns:
            IGraphEngine: An instance of the graph engine.

        Raises:
            RuntimeError: If the graph engine is not properly initialized.
        """
        pass

