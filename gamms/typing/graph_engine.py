from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass

from sympy import N

from hashman.faiss.benchs.bench_for_interrupt import Di


@dataclass
class Node:
    """
    Represents a node within a graph.

    Attributes:
        id (int): The unique identifier for the node.
        x (float): The x-coordinate of the node's position.
        y (float): The y-coordinate of the node's position.
    """
    id: int
    x: float
    y: float


@dataclass
class OSMEdge:
    """
    Represents an OpenStreetMap (OSM) edge within a graph.

    Attributes:
        id (int): The unique identifier for the edge.
        source (int): The ID of the source node.
        target (int): The ID of the target node.
        length (float): The length of the edge.
        linestring (List[Tuple[float, float]], optional): A list of (x, y) tuples representing the geometry of the edge.
            Defaults to None.
    """
    id: int
    source: int  # Node ID
    target: int  # Node ID
    length: float
    linestring: List[Tuple[float, float]] = None


class IGraph(ABC):
    """
    Abstract base class representing a graph structure.

    The graph consists of nodes and edges, allowing for addition, removal, and retrieval of these elements.
    """

    @abstractmethod
    def add_node(self, node_data: Dict[str, Any]) -> None:
        """
        Add a new node to the graph.

        Args:
            node_data (Dict[str, Any]): A dictionary containing the node's attributes. Expected keys include:
                - 'id' (int): Unique identifier for the node.
                - 'x' (float): X-coordinate of the node.
                - 'y' (float): Y-coordinate of the node.

        Raises:
            ValueError: If the node_data is missing required fields or contains invalid data.
            KeyError: If a node with the same ID already exists in the graph.
        """
        pass

    @abstractmethod
    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        """
        Add a new edge to the graph.

        Args:
            edge_data (Dict[str, Any]): A dictionary containing the edge's attributes. Expected keys include:
                - 'id' (int): Unique identifier for the edge.
                - 'source' (int): ID of the source node.
                - 'target' (int): ID of the target node.
                - 'length' (float): Length of the edge.
                - 'linestring' (List[Tuple[float, float]], optional): Geometry of the edge.

        Raises:
            ValueError: If the edge_data is missing required fields, contains invalid data, or references non-existent nodes.
            KeyError: If an edge with the same ID already exists in the graph.
        """
        pass

    @abstractmethod
    def get_nodes(self) -> List[int]:
        """
        Retrieve a list of all node IDs in the graph.

        Returns:
            List[int]: A list containing the IDs of all nodes.
        """
        pass

    @abstractmethod
    def get_edges(self) -> Dict[int, OSMEdge]:
        """
        Retrieve a list of all edge IDs in the graph.

        Returns:
            Dict[int, OSMEdge]: A dictionary mapping edge IDs to their corresponding OSMEdge objects.
        """
        pass

    @abstractmethod
    def update_node(self, node_data: Dict[str, Any]) -> None:
        """
        Update an existing node's attributes.

        Args:
            node_data (Dict[str, Any]): A dictionary containing the node's updated attributes. Must include:
                - 'id' (int): Unique identifier for the node.
                - Any other attributes to be updated (e.g., 'x', 'y').

        Raises:
            KeyError: If the node with the specified ID does not exist.
            ValueError: If the provided data is invalid.
        """
        pass

    @abstractmethod
    def update_edge(self, edge_data: Dict[str, Any]) -> None:
        """
        Update an existing edge's attributes.

        Args:
            edge_data (Dict[str, Any]): A dictionary containing the edge's updated attributes. Must include:
                - 'id' (int): Unique identifier for the edge.
                - Any other attributes to be updated (e.g., 'source', 'target', 'length', 'linestring').

        Raises:
            KeyError: If the edge with the specified ID does not exist.
            ValueError: If the provided data is invalid or references non-existent nodes.
        """
        pass

    @abstractmethod
    def remove_node(self, node_id: int) -> None:
        """
        Remove a node from the graph.

        Args:
            node_id (int): The unique identifier of the node to be removed.

        Raises:
            KeyError: If the node with the specified ID does not exist.
            ValueError: If removing the node would leave edges without valid source or target nodes.
        """
        pass

    @abstractmethod
    def remove_edge(self, edge_id: int) -> None:
        """
        Remove an edge from the graph.

        Args:
            edge_id (int): The unique identifier of the edge to be removed.

        Raises:
            KeyError: If the edge with the specified ID does not exist.
        """
        pass

    @abstractmethod
    def get_node(self, node_id: int) -> Node:
        """
        Retrieve the attributes of a specific node.

        Args:
            node_id (int): The unique identifier of the node to retrieve.

        Returns:
            Dict[str, Any]: A dictionary containing the node's attributes.

        Raises:
            KeyError: If the node with the specified ID does not exist.
        """
        pass

    @abstractmethod
    def get_edge(self, edge_id: int) -> Dict[str, Any]:
        """
        Retrieve the attributes of a specific edge.

        Args:
            edge_id (int): The unique identifier of the edge to retrieve.

        Returns:
            Dict[str, Any]: A dictionary containing the edge's attributes.

        Raises:
            KeyError: If the edge with the specified ID does not exist.
        """
        pass


class IGraphEngine(ABC):
    """
    Abstract base class representing the graph engine.

    The graph engine manages the underlying graph structure, providing access and control over graph operations.
    """

    @property
    @abstractmethod
    def graph(self) -> IGraph:
        """
        Get the current graph managed by the engine.

        Returns:
            IGraph: The graph instance being managed.

        Raises:
            RuntimeError: If the graph has not been initialized.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the graph engine and perform necessary cleanup operations.

        This method should ensure that all resources allocated to the graph engine are properly released
        and that any ongoing operations are gracefully stopped.
        """
        pass