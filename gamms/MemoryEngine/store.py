from gamms.typing.memory_engine import IStore, StoreType, IPathLike
import os
from typing import Any

class PathLike(IPathLike):
    def __init__(self, path: str):
        if not path:
            raise ValueError("Path cannot be empty.")
        self.path = os.path.abspath(path)
        
    def exists(self) -> bool:
        return os.path.exists(self.path)

    def as_str(self) -> str:
        return self.path

class Store(IStore):
    def __init__(self, name: str, store_type: StoreType, path: PathLike):
        self.name = name
        self.store_type = store_type
        self.path = path

    def save(self, obj: Any) -> None:
        if self.store_type == StoreType.FILESYSTEM:
            os.makedirs(self.path.as_str(), exist_ok=True)
            file_path = os.path.join(self.path.as_str(), self.name)
            with open(file_path, 'w') as file:
                if isinstance(obj, str) and os.path.exists(obj):
                    with open(obj, 'r') as object_file:
                        file.write(object_file.read())
                else:
                    file.write(str(obj))
        else:
            raise NotImplementedError(f"Save operation not implemented for {self.store_type}.")

    def load(self) -> Any:
        if self.store_type == StoreType.FILESYSTEM:
            file_path = os.path.join(self.path.as_str(), self.name)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Store file '{file_path}' does not exist.")
            with open(file_path, 'r') as file:
                return file.read()
        else:
            raise NotImplementedError(f"Load operation not implemented for {self.store_type}.")

    def delete(self) -> None:
        if self.store_type == StoreType.FILESYSTEM:
            file_path = os.path.join(self.path.as_str(), self.name)
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                raise FileNotFoundError(f"Store file '{file_path}' does not exist.")
        else:
            raise NotImplementedError(f"Delete operation not implemented for {self.store_type}.")
