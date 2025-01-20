from gamms.typing import IComputeEngine, IMemoryEngine, IMessageEngine, IInternalContext

class InternalContext(IInternalContext):
    def __init__(
        self,
        compute_engine: IComputeEngine,
        memory_engine: IMemoryEngine,
        message_engine: IMessageEngine,
        ) -> None:
        self.compute_engine = compute_engine
        self.memory_engine = memory_engine
        self.message_engine = message_engine
    
    @property
    def compute(self) -> IComputeEngine:
        return self.compute_engine

    @property
    def memory(self) -> IMemoryEngine:
        return self.memory_engine
    
    @property
    def message(self) -> IMessageEngine:
        return self.message_engine
    
    def terminate(self):
        self.compute_engine.terminate()
        self.memory_engine.terminate()
        self.message_engine.terminate()
