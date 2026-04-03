# Abstract Base Classes (ABC) in Python

## Overview

Python's `abc` module provides the `ABC` class and `@abstractmethod` decorator to define **Abstract Base Classes** — classes that cannot be instantiated directly and that enforce a contract: every subclass *must* implement the abstract methods before it can be instantiated.

This pattern is an implementation of the **Template Method** design pattern: the base class defines the overall algorithm skeleton (`write` / `read`), and concrete subclasses supply the format-specific details (`serialize` / `deserialize`).

---

## Code Walkthrough

### `FileHandler` — the abstract base

```python
from abc import ABC, abstractmethod

class FileHandler(ABC):
    def __init__(self, file_path):
        self.file_path = file_path   # shared state for all subclasses

    @abstractmethod
    def serialize(self, data: dict) -> bytes:
        pass   # subclasses MUST implement this

    @abstractmethod
    def deserialize(self, data: bytes) -> dict:
        pass   # subclasses MUST implement this

    # ── Template Method ─────────────────────────────────────────────
    def write(self, data: dict):
        serialized_data = self.serialize(data)      # delegated to subclass
        with open(self.file_path, "wb") as file:
            file.write(serialized_data)

    def read(self):
        with open(self.file_path, "rb") as file:
            serialized_data = file.read()
        return self.deserialize(serialized_data)    # delegated to subclass
```

Key points:
- Inheriting from `ABC` marks `FileHandler` as abstract; trying to do `FileHandler("x")` raises `TypeError`.
- `@abstractmethod` forces every concrete subclass to provide `serialize` and `deserialize`.
- `write` and `read` are *concrete* template methods: they express the invariant algorithm (open file, call hook, close file) without knowing the wire format.

### `JsonFileHandler` — JSON concrete implementation

```python
from json import dumps as json_dump, loads as json_loads

class JsonFileHandler(FileHandler):
    def __init__(self, file_path):
        super().__init__(file_path)   # always delegate __init__ to the base

    def serialize(self, data: dict) -> bytes:
        return json_dump(data).encode("utf-8")   # dict → JSON string → bytes

    def deserialize(self, data: bytes) -> dict:
        return json_loads(data.decode("utf-8"))  # bytes → JSON string → dict
```

### `PickleFileHandler` — Pickle concrete implementation

```python
from pickle import dumps as pickle_dumps, loads as pickle_loads

class PickleFileHandler(FileHandler):
    # __init__ is inherited automatically — no need to override it

    def serialize(self, data: dict) -> bytes:
        return pickle_dumps(data)   # Python pickle protocol

    def deserialize(self, data: bytes) -> dict:
        return pickle_loads(data)
```

---

## Design Pattern: Template Method

```
FileHandler (Abstract)
├── __init__(file_path)      ← shared constructor
├── serialize()              ← abstract hook
├── deserialize()            ← abstract hook
├── write()                  ← template method (calls serialize)
└── read()                   ← template method (calls deserialize)
        │
        ├── JsonFileHandler  ← implements serialize / deserialize with JSON
        └── PickleFileHandler ← implements serialize / deserialize with Pickle
```

The Template Method pattern lets you change the *steps* of an algorithm (serialization format) without rewriting the *structure* (how a file is opened, written, and closed).

---

## Suggestions to Improve and Scale

### 1. Add error handling

```python
import os

def write(self, data: dict):
    serialized_data = self.serialize(data)
    tmp_path = self.file_path + ".tmp"
    try:
        with open(tmp_path, "wb") as file:
            file.write(serialized_data)
        os.replace(tmp_path, self.file_path)   # atomic rename
    except OSError as exc:
        raise IOError(f"Failed to write to {self.file_path}") from exc
```

Writing to a temp file and renaming atomically prevents data corruption if the process crashes mid-write.

### 2. Support streaming / large files

For large datasets, avoid loading the entire file into memory:

```python
import json, io

class StreamingJsonFileHandler(FileHandler):
    def write(self, data: dict):
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(data, file)   # streams directly to disk

    def read(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)  # streams directly from disk
```

### 3. Add compression support via a mixin

```python
import gzip

class GzipMixin:
    """Mixin that transparently compresses / decompresses file I/O."""

    def write(self, data: dict):
        serialized_data = self.serialize(data)
        with gzip.open(self.file_path, "wb") as file:
            file.write(serialized_data)

    def read(self):
        with gzip.open(self.file_path, "rb") as file:
            serialized_data = file.read()
        return self.deserialize(serialized_data)


class GzipJsonFileHandler(GzipMixin, JsonFileHandler):
    pass   # inherits compressed I/O + JSON serialization
```

### 4. Use a factory / registry for dynamic handler selection

```python
_HANDLERS: dict[str, type[FileHandler]] = {}

def register_handler(extension: str):
    def decorator(cls):
        _HANDLERS[extension] = cls
        return cls
    return decorator

@register_handler(".json")
class JsonFileHandler(FileHandler): ...

@register_handler(".pkl")
class PickleFileHandler(FileHandler): ...

def get_handler(file_path: str) -> FileHandler:
    ext = os.path.splitext(file_path)[1]
    handler_cls = _HANDLERS.get(ext)
    if handler_cls is None:
        raise ValueError(f"No handler registered for extension '{ext}'")
    return handler_cls(file_path)
```

### 5. Add a validation hook

```python
class FileHandler(ABC):
    ...
    def validate(self, data: dict) -> None:
        """Optional validation hook; subclasses may override."""
        pass

    def write(self, data: dict):
        self.validate(data)              # run validation before writing
        serialized_data = self.serialize(data)
        with open(self.file_path, "wb") as file:
            file.write(serialized_data)
```

---

## Additional Examples

### YAML file handler

```python
import yaml   # pip install pyyaml

class YamlFileHandler(FileHandler):
    def serialize(self, data: dict) -> bytes:
        return yaml.dump(data, default_flow_style=False).encode("utf-8")

    def deserialize(self, data: bytes) -> dict:
        return yaml.safe_load(data.decode("utf-8"))

# Usage
handler = YamlFileHandler("config.yaml")
handler.write({"host": "localhost", "port": 5432})
config = handler.read()
```

### TOML file handler

```python
import tomllib, tomli_w   # pip install tomli-w (tomllib is in stdlib ≥ 3.11)

class TomlFileHandler(FileHandler):
    def serialize(self, data: dict) -> bytes:
        return tomli_w.dumps(data).encode("utf-8")

    def deserialize(self, data: bytes) -> dict:
        return tomllib.loads(data.decode("utf-8"))
```

### CSV file handler (list of dicts)

```python
import csv, io

class CsvFileHandler(FileHandler):
    def serialize(self, data: dict) -> bytes:
        # data is expected to be {"rows": [...], "fieldnames": [...]}
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=data["fieldnames"])
        writer.writeheader()
        writer.writerows(data["rows"])
        return buf.getvalue().encode("utf-8")

    def deserialize(self, data: bytes) -> dict:
        buf = io.StringIO(data.decode("utf-8"))
        reader = csv.DictReader(buf)
        return {"fieldnames": reader.fieldnames, "rows": list(reader)}
```

### Encrypted file handler (using cryptography)

```python
from cryptography.fernet import Fernet   # pip install cryptography

class EncryptedJsonFileHandler(JsonFileHandler):
    def __init__(self, file_path: str, key: bytes):
        super().__init__(file_path)
        self._fernet = Fernet(key)

    def serialize(self, data: dict) -> bytes:
        return self._fernet.encrypt(super().serialize(data))

    def deserialize(self, data: bytes) -> dict:
        return super().deserialize(self._fernet.decrypt(data))

# Usage
key = Fernet.generate_key()
handler = EncryptedJsonFileHandler("secrets.json.enc", key)
handler.write({"password": "s3cr3t"})
```

---

## When to Use ABC

| Situation | Use ABC? |
|---|---|
| You own the class hierarchy and want to enforce a contract | ✅ Yes |
| Subclasses share significant common logic (template methods) | ✅ Yes |
| You need `isinstance` / `issubclass` checks to work correctly | ✅ Yes |
| You want structural (duck-type) checking without inheritance | ❌ Use `Protocol` instead |
| You're integrating with third-party classes you cannot modify | ❌ Use `Protocol` instead |
