from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum


class SensorType(Enum):
    """
    Enumeration of different sensor types.

    Attributes:
        NEIGHBOR (Enum): Sensor type for detecting neighboring entities.
            Data Representation (`List[int]`): List of node identifiers representing neighbors.
        MAP (Enum): Sensor type for map-related data.
            Data Representation (`Tuple[Dict[int, Node], Dict[int, OSMEdge]`): Tuple containing node and edge data.
        AGENT (Enum): Sensor type for agent locations.
            Data Representation (`Dict[str, int]`): Dictionary mapping agent names to node identifiers.
    """
    NEIGHBOR = 1
    MAP = 2
    AGENT = 3
    RANGE = 4
    ARC = 5
    AGENT_RANGE = 6
    AGENT_ARC = 7


class ISensor(ABC):
    """
    Abstract base class representing a generic sensor.

    Sensors are responsible for collecting data related to specific aspects of the system.
    Each sensor has a type and maintains its own data state.
    
    Attributes:
        type (SensorType): The type of the sensor.
        data (Dict[str, Any]): The data collected or maintained by the sensor.
    """

    type: SensorType
    data: Dict[str, Any]

    @abstractmethod
    def data(self) -> Dict[str, Any]:
        """
        Get the current data maintained by the sensor.

        Returns:
            Dict[str, Any]: The data maintained by the sensor.
        """
        return self.data

    @abstractmethod
    def sense(self, node_id: int) -> Dict[str, Any]:
        """
        Perform sensing operations for a given node.

        This method collects data related to the specified node and returns the sensed information.

        Args:
            node_id (int): The unique identifier of the node to sense.

        Returns:
            Dict[str, Any]: A dictionary containing the sensed data.

        Raises:
            ValueError: If the provided node_id is invalid.
            RuntimeError: If the sensing operation fails due to system constraints.
        """
        pass

    @abstractmethod
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update the sensor's data.

        This method modifies the sensor's internal data based on the provided information.

        Args:
            data (Dict[str, Any]): A dictionary containing the data to update the sensor with.

        Raises:
            KeyError: If the provided data contains invalid keys.
            ValueError: If the provided data is malformed or incomplete.
        """
        pass


class ISensorEngine(ABC):
    """
    Abstract base class representing a sensor engine.

    The sensor engine manages the lifecycle of sensors, including their creation, retrieval,
    and termination. It serves as a central point for interacting with various sensors
    within the system.
    """

    @abstractmethod
    def create_sensor(self, sensor_type: SensorType, sensor_data: Dict[str, Any]) -> ISensor:
        """
        Create a new sensor of the specified type.

        This method initializes a sensor based on the provided type and data, and registers
        it within the sensor engine for management.

        Args:
            sensor_type (SensorType): The type of sensor to create.
            sensor_data (Dict[str, Any]): A dictionary containing initial data for the sensor.

        Returns:
            ISensor: The newly created sensor instance.

        Raises:
            ValueError: If the sensor_type is unsupported or sensor_data is invalid.
            RuntimeError: If the sensor cannot be created due to system constraints.
        """
        pass

    @abstractmethod
    def get_sensor(self, sensor_id: Any) -> ISensor:
        """
        Retrieve a sensor by its unique identifier.

        This method fetches the sensor instance corresponding to the provided sensor_id.

        Args:
            sensor_id (Any): The unique identifier of the sensor to retrieve.

        Returns:
            ISensor: The sensor instance associated with the provided sensor_id.

        Raises:
            KeyError: If no sensor with the specified sensor_id exists.
            TypeError: If the sensor_id is of an incorrect type.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the sensor engine and perform necessary cleanup operations.

        This method gracefully shuts down the sensor engine, ensuring that all sensors
        are properly terminated and that resources are released.

        Raises:
            RuntimeError: If the sensor engine fails to terminate gracefully.
            IOError: If there are issues during the cleanup process.
        """
        pass

    def custom(self) -> None:
        """
        Decorator for custom sensor
        For example, if the user create a new custom sensor, add a new type to SensorType enum
        and implement the new sensor class, the user can add the custom sensor to the sensor engine
        using this method.
        """
