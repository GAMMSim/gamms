from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import enum
from typing import Optional, Dict
from gamms.typing import IComputeEngine, ITask, IInternalContext
import uuid

class TaskStatus(enum.Enum):
    PENDING = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3

class Task(ITask):
    def __init__(self, func, *args, **kwargs) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._id = uuid.uuid1().hex
        self._status: TaskStatus = TaskStatus.PENDING
        self._exception = None
        self._lock = Lock()
    
    @property
    def id(self):
        return self._id

    def run(self):
        with self._lock:
            if self._status != TaskStatus.PENDING:
                raise ValueError("Task already started or completed")
            self._status = TaskStatus.RUNNING
        try:
            self.func(*self.args, **self.kwargs)
            self._status = TaskStatus.COMPLETED
        except Exception as e:
            self._status = TaskStatus.FAILED
            self._exception = e
    
    @property
    def status(self):
        return self._status
    
class SimpleTaskLoop:
    def __init__(self, max_workers: Optional[int] = None) -> None:
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks = {}

    def submit(self, task: Task):
        future = self.executor.submit(task.run)
        self._tasks[task.id] = future

    def wait(self, task: Task):
        if task.id not in self._tasks:
            raise ValueError("Task not found")
        self._tasks[task.id].result()
        if task.status == TaskStatus.FAILED:
            raise task._exception
        del self._tasks[task.id]
        
    def shutdown(self):
        self.executor.shutdown()
        if len(self._tasks) > 0:
            raise ValueError("Some tasks are still running. This should not happen")


class ComputeEngine(IComputeEngine):
    def __init__(self, ctx: Optional[IInternalContext] = None,engine_kwargs: Optional[Dict[str, int]] = None, **kwargs) -> None:
        if engine_kwargs is None:
            engine_kwargs = {}
        self._engine = SimpleTaskLoop(**engine_kwargs)
        self.ctx = ctx
    
    def submit(self, task: Task) -> None:
        self._engine.submit(task)
    
    def wait(self, task: Task) -> None:
        self._engine.wait(task)
        
    def terminate(self):
        self._engine.shutdown()

__all__ = ["ComputeEngine", "Task", "TaskStatus"]

if __name__ == "__main__":
    import time
    def io_func():
        time.sleep(5)
    
    def pathological_function():
        i = 0
        while i < 5:
            time.sleep(1)
            i += 1
    
    engine = ComputeEngine()
    print("Starting IO tasks")
    t = time.time()
    tasks = []
    for _ in range(100):
        task = Task(io_func)
        engine.submit(task)
        tasks.append(task)
    for task in tasks:
        engine.wait(task)
    print("IO tasks completed in", time.time() - t)
    print("Starting pathological tasks")
    t = time.time()
    tasks = []
    for _ in range(100):
        task = Task(pathological_function)
        engine.submit(task)
        tasks.append(task)
    for task in tasks:
        engine.wait(task)
    print("Pathological tasks completed in", time.time() - t)
    engine.terminate()
