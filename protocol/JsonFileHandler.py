from abc import ABC, abstractmethod
from json import dumps as json_dump
from json import loads as json_loads


class FileHandler(ABC):
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


class JsonFileHandler(FileHandler):
    def __init__(self, file_path):
        self.file_path = file_path

    def serialize(self, data: dict) -> bytes:
        return json_dump(data).encode("utf-8")

    def deserialize(self, data: bytes) -> dict:
        return json_loads(data.decode("utf-8"))


if __name__ == "__main__":
    handler = JsonFileHandler("data.json")
    data = {"name": "Alice", "age": 30, "city": "New York"}

    handler.write(data)
    print("Data written to file.")

    read_data = handler.read()
    print("Data read from file:", read_data)
