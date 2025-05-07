from abc import ABC, abstractmethod
from gamms.typing.internal_context import IInternalContext
from gamms.typing.sensor_engine import ISensorEngine
from gamms.typing.visualization_engine import IVisualizationEngine
from gamms.typing.agent_engine import IAgentEngine
from gamms.typing.graph_engine import IGraphEngine
from gamms.typing.recorder import IRecorder
from gamms.typing.logger import ILogger


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

    @property
    @abstractmethod
    def record(self) -> IRecorder:
        """
        Retrieve the recorder.

        The recorder is responsible for recording and replaying system events.
        It captures information about system states and interactions for analysis and
        debugging purposes.

        Returns:
            IRecorder: An instance of the recorder engine.

        Raises:
            RuntimeError: If the recorder engine is not properly initialized.
        """
        pass

    @property
    @abstractmethod
    def logger(self) -> ILogger:
        """
        Retrieve the logger.

        The logger is responsible for logging messages and events within the system.
        It provides various logging levels (debug, info, warning, error, critical)
        for structured logging.

        Returns:
            ILogger: An instance of the logger engine.

        Raises:
            RuntimeError: If the logger engine is not properly initialized.
        """
        pass

    @abstractmethod
    def is_terminated(self) -> bool:
        """
        Check if the context is terminated.

        This method determines whether the context has been terminated, indicating
        that no further operations should be performed.

        Returns:
            bool: True if the context is terminated, False otherwise.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the context.

        This method performs necessary cleanup operations and releases resources
        associated with the context. It should be called when the context is no
        longer needed.

        Raises:
            RuntimeError: If the termination process encounters an error.
        """
        pass