from gamms.typing.recorder import IRecorder
import os 
import time
import pickle
import numpy as np

class Recorder(IRecorder):
    def __init__(self):
        self.is_recording = False
        self.is_paused = False
        self.file_path = None
        self.record_buffer = []
        self.start_time = None
        self.memory = {}
    
    def record(self) -> bool:
        if not self.is_paused and self.is_recording:
            return True
        else:
            return False

    def start(self, path: str) -> None:
        if os.path.exists(path):
            raise FileExistsError(f"File {path} already exists.")
        self.file_path = path
        self.is_recording = True
        self.is_paused = False
        self.start_time = time.time()
        self.record_buffer = []
        #print(f"Recording started: {path}")

    def stop(self) -> None:
        if not self.is_recording:
            raise RuntimeError("Recording has not started.")
        self.is_recording = False
        with open(self.file_path, 'wb') as file:
            pickle.dump(self.record_buffer, file)
        #print(f"Recording stopped and saved to: {self.file_path}")

    def pause(self) -> None:
        if not self.is_recording:
            print("Warning: Recording has not started.")
        elif self.is_paused:
            print("Warning: Recording is already paused.")
        else:
            self.is_paused = True
            print("Recording paused.")

    def play(self, path: str) -> None:
        if not self.is_recording:
            print("Warning: Recording has not started.")
        elif not self.is_paused:
            print("Warning: Recording is already playing.")
        else:
            self.is_paused = False
            print("Recording resumed.")

    def replay(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} does not exist.")
        with open(path, 'rb') as file:
            record_buffer = pickle.load(file)
        for call in record_buffer:
            yield call

    def time(self):
        if self.is_recording:
            return np.int64(time.time() - self.start_time)
        return np.int64(time.time())

    def write(self, opCode, data):
        if not self.record():
            raise RuntimeError("Cannot write: Not currently recording.")
        timestamp = self.time()
        self.record_buffer.append({"timestamp": timestamp, "opCode": opCode, "data": data})

    def memory_get(self, keys):
        value = self.memory
        try:
            for key in keys:
                value = value[key]
            return value
        except KeyError:
            raise KeyError(f"Key {keys} not found in memory.")

    def memory_set(self, keys, value):
        target = self.memory
        for key in keys[:-1]:
            if key not in target:
                raise KeyError(f"Key {key} not found in memory for path {keys}.")
            target = target[key]
        target[keys[-1]] = value

        if self.record():
            self.write("memory_set", {"keys": keys, "value": value})