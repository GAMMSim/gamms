from gamms.typing.recorder import IRecorder, JsonType
from gamms.typing.opcodes import OpCodes, MAGIC_NUMBER, VERSION
from gamms.typing import IContext
import os 
import time
import ubjson

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
    elif opCode == OpCodes.TERMINATE:
        print("Terminating...")

class Recorder(IRecorder):
    def __init__(self, ctx: IContext):
        self.ctx = ctx
        self.is_recording = False
        self.is_replaying = False
        self.is_paused = False
        self._fp_record = None
        self._fp_replay = None
        self._time = None
    
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