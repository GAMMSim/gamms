from abc import ABC, abstractmethod
from typing import Optional, Any, List


class IMessageEngine(ABC):
    """
    Abstract base class representing a messaging engine.

    The messaging engine facilitates communication between different components
    through channels. It allows the creation of publishers and subscribers,
    manages active channels, and handles the lifecycle of the messaging system.
    """

    @abstractmethod
    def generate_channel_name(self) -> str:
        """
        Generate a unique channel name.

        This method creates a unique identifier for a communication channel,
        ensuring that each channel name is distinct within the messaging system.

        Returns:
            str: A unique channel name.
        """
        pass

    @abstractmethod
    def create_publisher(
        self,
        tensor: Any,
        channel_name: Optional[str],
        ttl: int,
    ) -> None:
        """
        Create a publisher for a specific channel.

        This method initializes a publisher that can send messages (tensors)
        to the specified communication channel. If no channel name is provided,
        a unique channel name is generated automatically.

        Args:
            tensor (Any): The data or message to be published. It can be of any type
                that the messaging system supports.
            channel_name (Optional[str]): The name of the channel to publish to.
                If `None`, a unique channel name is generated.
            ttl (int): Time-to-live for the publisher in seconds. After this duration,
                the publisher will be automatically terminated.

        Raises:
            ValueError: If the provided tensor is invalid or unsupported.
            RuntimeError: If the publisher cannot be created due to system constraints.
        """
        pass

    @abstractmethod
    def create_subscriber(
        self,
        channel_name: str,
    ) -> None:
        """
        Create a subscriber for a specific channel.

        This method initializes a subscriber that listens for messages on the specified
        communication channel. Subscribers receive messages published to their channels.

        Args:
            channel_name (str): The name of the channel to subscribe to.

        Raises:
            KeyError: If the specified channel does not exist.
            RuntimeError: If the subscriber cannot be created due to system constraints.
        """
        pass

    @abstractmethod
    def list_active_channels(self) -> List[str]:
        """
        List all active communication channels.

        This method retrieves a list of all currently active channel names managed
        by the messaging engine.

        Returns:
            List[str]: A list of active channel names.

        Raises:
            RuntimeError: If the messaging engine is not properly initialized.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the messaging engine and perform necessary cleanup operations.

        This method gracefully shuts down the messaging system, ensuring that all
        publishers and subscribers are properly terminated and that resources are
        released.

        Raises:
            RuntimeError: If the engine fails to terminate gracefully.
            IOError: If there are issues during the cleanup process.
        """
        pass
