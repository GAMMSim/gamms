from typing import Optional

from gamms.typing import IComputeEngine, IMemoryEngine, IMessageEngine, IInternalContext


class InternalContext(IInternalContext):
    def __init__(
        self,
        compute_engine: Optional[IComputeEngine] = None,
        memory_engine: Optional[IMemoryEngine] = None,
        message_engine: Optional[IMessageEngine] = None,
    ) -> None:
        self.compute_engine = compute_engine
        self.memory_engine = memory_engine
        self.message_engine = message_engine

    @property
    def compute(self) -> Optional[IComputeEngine]:
        return self.compute_engine

    @property
    def memory(self) -> Optional[IMemoryEngine]:
        return self.memory_engine

    @property
    def message(self) -> Optional[IMessageEngine]:
        return self.message_engine

    def terminate(self) -> None:
        if self.compute_engine is not None:
            self.compute_engine.terminate()
        if self.memory_engine is not None:
            self.memory_engine.terminate()
        if self.message_engine is not None:
            self.message_engine.terminate()
