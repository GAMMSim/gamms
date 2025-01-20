from abc import ABC, abstractmethod
from enum import Enum

from abc import ABC, abstractmethod
from enum import Enum


class ITask(ABC):
    """
    Abstract base class representing a generic task.

    Tasks encapsulate units of work that can be executed by a compute engine.
    Each task has a unique identifier and a status indicating its current state.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Get the unique identifier of the task.

        Returns:
            str: The unique ID of the task.
        """
        pass

    @property
    @abstractmethod
    def status(self) -> Enum:
        """
        Get the current status of the task.

        Returns:
            Enum: An enumeration representing the task's status.
                  Possible statuses might include PENDING, RUNNING, COMPLETED, FAILED, etc.
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """
        Execute the task's logic.

        This method contains the core functionality that the task is supposed to perform.
        It should update the task's status accordingly based on the execution outcome.
        """
        pass


class IComputeEngine(ABC):
    """
    Abstract base class representing a compute engine.

    The compute engine is responsible for managing and executing tasks.
    It handles task submission, monitors task execution, and manages the lifecycle of tasks.
    """

    @abstractmethod
    def submit(self, task: ITask) -> None:
        """
        Submit a task to the compute engine for execution.

        Args:
            task (ITask): The task instance to be executed by the compute engine.

        Raises:
            ValueError: If the task is invalid or cannot be submitted.
            RuntimeError: If the compute engine is not in a state to accept new tasks.
        """
        pass

    @abstractmethod
    def wait(self, task: ITask) -> None:
        """
        Wait for the specified task to complete execution.

        This method blocks until the task's status indicates completion, failure, or termination.

        Args:
            task (ITask): The task instance to wait for.

        Raises:
            TimeoutError: If the wait operation times out.
            RuntimeError: If the task encounters an unexpected error during execution.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """
        Terminate the compute engine and perform necessary cleanup operations.

        This method should ensure that all running tasks are gracefully stopped
        and that all resources allocated to the compute engine are properly released.
        """
        pass
