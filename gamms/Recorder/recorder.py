from gamms.typing.recorder import IRecorder, JsonType
from gamms.typing.opcodes import OpCodes, MAGIC_NUMBER, VERSION
from gamms.typing import IContext
import os 
import time
import ubjson
import typing
from gamms.Recorder.component import component

def _record_switch_case(ctx: IContext, opCode: OpCodes, data: JsonType) -> None:
    if opCode == OpCodes.AGENT_CREATE:
        print(f"Creating agent {data['name']} at node {data['kwargs']['start_node_id']}")
        ctx.agent.create_agent(data["name"], **data["kwargs"])
    elif opCode == OpCodes.AGENT_DELETE:
        print(f"Deleting agent {data}")
        ctx.agent.delete_agent(data)
    elif opCode == OpCodes.SIMULATE:
        ctx.visual.simulate()
    elif opCode == OpCodes.AGENT_CURRENT_NODE:
        print(f"Agent {data['agent_name']} moved to node {data['node_id']}")
        ctx.agent.get_agent(data["agent_name"]).current_node_id = data["node_id"]
    elif opCode == OpCodes.AGENT_PREV_NODE:
        ctx.agent.get_agent(data["agent_name"]).prev_node_id = data["node_id"]
    elif opCode == OpCodes.COMPONENT_REGISTER:
        if ctx.record.is_component_registered(data["key"]):
            print(f"Component {data['key']} already registered.")
        else:
            print(f"Registering component {data['key']} of type {data['struct']}")
            module, name = data["key"]
            cls_type = type(name, (object,), {})
            cls_type.__module__ = module
            struct = {key: eval(value) for key, value in data["struct"].items()}
            ctx.record.component(struct=struct)(cls_type)
    elif opCode == OpCodes.COMPONENT_CREATE:
        print(f"Creating component {data['name']} of type {data['type']}")
        ctx.record._component_registry[data["type"]](name=data["name"])
    elif opCode == OpCodes.COMPONENT_UPDATE:
        print(f"Updating component {data['name']} with key {data['key']} to value {data['value']}")
        obj = ctx.record.get_component(data["name"])
        setattr(obj, data["key"], data["value"])
    elif opCode == OpCodes.TERMINATE:
        print("Terminating...")
    else:
        raise ValueError(f"Invalid opcode {opCode}")

class Recorder(IRecorder):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        self.is_recording = False
        self.is_replaying = False
        self.is_paused = False
        self._fp_record = None
        self._fp_replay = None
        self._time = None
        self._components: Dict[str, Type[_T]] = {}
        self._component_registry: Dict[Tuple[str, str], Type[_T]] = {}
    
    def record(self) -> bool:
        if not self.is_paused and self.is_recording and not self.ctx.is_terminated():
            return True
        else:
            return False

    def start(self, path: str) -> None:
        if self._fp_record is not None:
            raise RuntimeError("Recording file is already open. Stop recording before starting a new one.")
        
        # Check if path has extension .ggr
        if not path.endswith('.ggr'):
            path += '.ggr'

        if os.path.exists(path):
            raise FileExistsError(f"File {path} already exists.")

        self._fp_record = open(path, 'wb')
        self.is_recording = True
        self.is_paused = False

        # Add file validity header
        self._fp_record.write(MAGIC_NUMBER)
        self._fp_record.write(VERSION)

    def stop(self) -> None:
        if not self.is_recording:
            raise RuntimeError("Recording has not started.")
        self.write(OpCodes.TERMINATE, None)
        self.is_recording = False
        self.is_paused = False
        self._fp_record.close()

    def pause(self) -> None:
        if not self.is_recording:
            print("Warning: Recording has not started.")
        elif self.is_paused:
            print("Warning: Recording is already paused.")
        else:
            self.is_paused = True
            print("Recording paused.")

    def play(self) -> None:
        if not self.is_recording:
            print("Warning: Recording has not started.")
        elif not self.is_paused:
            print("Warning: Recording is already playing.")
        else:
            self.is_paused = False
            print("Recording resumed.")

    def replay(self, path: str):
        # Check if path has extension .ggr
        if not path.endswith('.ggr'):
            path += '.ggr'

        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} does not exist.")

        self._fp_replay = open(path, 'rb')

        # Check file validity header
        if self._fp_replay.read(4) != MAGIC_NUMBER:
            raise ValueError("Invalid file format.")
        
        _version = self._fp_replay.read(4)

        # Not checking version for now        
        self.is_replaying = True

        while self.is_replaying:
            try:
                record = ubjson.load(self._fp_replay)
            except EOFError:
                raise ValueError("Recording ended unexpectedly.")
            self._time = record["timestamp"]
            opCode = OpCodes(record["opCode"])
            if opCode == OpCodes.TERMINATE:
                self.is_replaying = False
            _record_switch_case(self.ctx, opCode, record.get("data", None))

            yield record

    def time(self):
        if self.is_replaying:
            return self._time
        return time.monotonic_ns()

    def write(self, opCode: OpCodes, data: JsonType) -> None:
        if not self.record():
            raise RuntimeError("Cannot write: Not currently recording.")
        timestamp = self.time()
        if data is None:
            ubjson.dump({"timestamp": timestamp, "opCode": opCode.value}, self._fp_record)
        else:
            ubjson.dump({"timestamp": timestamp, "opCode": opCode.value, "data": data}, self._fp_record)
        
    
    def component(self, struct: Dict[str, Type[_T]]) -> Callable[[Type[_T]], Type[_T]]:
        return component(self.ctx, struct)
    
    def get_component(self, name: str) -> Type[_T]:
        if name not in self._components:
            raise KeyError(f"Component {name} not found.")
        return self._components[name]
    
    def component_iter(self) -> Iterator[str]:
        return self._components.keys()
    
    def add_component(self, name: str, obj: Type[_T]) -> None:
        if name in self._components:
            raise ValueError(f"Component {name} already exists.")
        self._components[name] = obj
    
    def is_component_registered(self, key: Tuple[str, str]) -> bool:
        return key in self._component_registry