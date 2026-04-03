from typing import Protocol

from JsonFileHandler import JsonFileHandler


class WriteHandler(Protocol):
    def write(self, data: dict) -> None: ...


class ReadHandler(Protocol):
    def read(self) -> str: ...


class Writeable(Protocol):
    def write(self, writer: WriteHandler) -> None: ...


class Readable(Protocol):
    def read(self, reader: ReadHandler) -> str: ...


class JsonElement:
    def __init__(self, data: dict):
        self.data = data

    def write(self, handler: WriteHandler) -> None:
        handler.write(self.data)

    def read(self, handler: ReadHandler) -> str:
        return handler.read()


if __name__ == "__main__":
    json_element = JsonElement({"name": "Alice", "age": 30, "city": "New York"})
    print("JsonElement created with data:", json_element.data)

    handler = JsonFileHandler("test.json")
    json_element.write(handler)
    read_data = json_element.read(handler)
    print("Data read from JsonFileHandler:", read_data)
