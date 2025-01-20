from abc import ABC, abstractmethod
from gamms.typing.compute_engine import IComputeEngine
from gamms.typing.memory_engine import IMemoryEngine
from gamms.typing.message_engine import IMessageEngine


class IInternalContext(ABC):
    """
    Abstract base class representing the internal context of the system.

    The `IInternalContext` interface serves as a foundational component that provides
    access to core system engines, including compute, memory, and messaging engines.
    It facilitates centralized management and coordination of these engines, ensuring
    cohesive operation within the system. Additionally, it handles the termination
    process for proper resource cleanup.
    """

    @property
    @abstractmethod
    def compute(self) -> IComputeEngine:
        """
        Retrieve the compute engine.

        The compute engine manages computational tasks, including task submission,
        execution, monitoring, and termination. It serves as the backbone for handling
        processing-intensive operations within the system.

        Returns:
            IComputeEngine: An instance of the compute engine.

        Raises:
            RuntimeError: If the compute engine is not properly initialized or available.
        """
        pass

    @property
    @abstractmethod
    def memory(self) -> IMemoryEngine:
        """
        Retrieve the memory engine.

        The memory engine manages data storage and retrieval operations, handling
        in-memory data structures, persistent storage interactions, and memory optimization.
        It ensures efficient data management and accessibility for various system components.

        Returns:
            IMemoryEngine: An instance of the memory engine.

        Raises:
            RuntimeError: If the memory engine is not properly initialized or available.
        """
        pass

    @property
    @abstractmethod
    def message(self) -> IMessageEngine:
        """
        Retrieve the message engine.

        The message engine facilitates communication between different system components
        through messaging channels. It handles the creation of publishers and subscribers,
        manages active communication channels, and ensures reliable message delivery.

        Returns:
            IMessageEngine: An instance of the message engine.

        Raises:
            RuntimeError: If the message engine is not properly initialized or available.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the internal context and perform necessary cleanup operations.

        This method gracefully shuts down all managed engines (compute, memory, and message),
        ensuring that all resources are properly released and that ongoing operations are
        safely concluded. It prepares the system for shutdown by handling any required
        termination protocols.

        Raises:
            RuntimeError: If the termination process fails or cannot be completed successfully.
            IOError: If there are issues during the cleanup of resources.
        """
        pass
