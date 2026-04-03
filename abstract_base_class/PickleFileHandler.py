from abc import ABC, abstractmethod

from pickle import dumps as pickle_dumps
from pickle import loads as pickle_loads 


class FileHandler(ABC):
    def __init__(self, file_path):
        self.file_path = file_path

    @abstractmethod
    def serialize(self, data: dict) -> bytes:
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> dict:
        pass

    def write(self, data: dict):
        serialized_data = self.serialize(data)
        with open(self.file_path, "wb") as file:
            file.write(serialized_data)

    def read(self):
        with open(self.file_path, "rb") as file:
            serialized_data = file.read()
        return self.deserialize(serialized_data)


class PickleFileHandler(FileHandler):
    def serialize(self, data: dict) -> bytes:
        return pickle_dumps(data)

    def deserialize(self, data: bytes) -> dict:
        return pickle_loads(data)


if __name__ == "__main__":
    handler = PickleFileHandler("data.pkl")
    data = {"name": "Alice", "age": 30, "city": "New York"}

    handler.write(data)
    print("Data written to file.")

    read_data = handler.read()
    print("Data read from file:", read_data)
