# Protocols in Python

## Overview

Python's `typing.Protocol` (introduced in Python 3.8, defined formally in [PEP 544](https://peps.python.org/pep-0544/)) enables **structural subtyping** — also called *duck typing with static-type-checker support*. A class satisfies a `Protocol` simply by having the right methods and attributes; no explicit inheritance is required.

This is the Python equivalent of Go interfaces or TypeScript's structural types.

---

## Code Walkthrough

### `protocol/JsonFileHandler.py` — the concrete handler

```python
class JsonFileHandler:           # does NOT inherit from anything special
    def __init__(self, file_path):
        self.file_path = file_path

    def serialize(self, data: dict) -> bytes:
        return json_dump(data).encode("utf-8")

    def deserialize(self, data: bytes) -> dict:
        return json_loads(data.decode("utf-8"))

    def write(self, data: dict):          # satisfies WriteHandler protocol
        serialized_data = self.serialize(data)
        with open(self.file_path, "wb") as file:
            file.write(serialized_data)

    def read(self):                       # satisfies ReadHandler protocol
        with open(self.file_path, "rb") as file:
            serialized_data = file.read()
        return self.deserialize(serialized_data)
```

`JsonFileHandler` does not inherit from any base class, yet a static type checker (mypy, pyright) will confirm it satisfies `WriteHandler` and `ReadHandler` because it structurally matches their signatures.

### `protocol_example.py` — Protocols and consumers

```python
from typing import Protocol

# ── Low-level capability protocols ──────────────────────────────────

class WriteHandler(Protocol):
    def write(self, data: dict) -> None: ...   # anything with .write() qualifies

class ReadHandler(Protocol):
    def read(self) -> str: ...                 # anything with .read() qualifies

# ── Higher-level, composed protocols ────────────────────────────────

class Writeable(Protocol):
    """An object that delegates writing to a WriteHandler."""
    def write(self, writer: WriteHandler) -> None: ...

class Readable(Protocol):
    """An object that delegates reading to a ReadHandler."""
    def read(self, reader: ReadHandler) -> str: ...

# ── Concrete class that satisfies Writeable + Readable ───────────────

class JsonElement:
    def __init__(self, data: dict):
        self.data = data

    def write(self, handler: WriteHandler) -> None:
        handler.write(self.data)          # delegates to the handler

    def read(self, handler: ReadHandler) -> str:
        return handler.read()             # delegates to the handler
```

Key points:
- The `...` body (Ellipsis) is the idiomatic way to declare protocol method stubs.
- `JsonElement` satisfies `Writeable` and `Readable` without inheriting from them.
- Any object whose `.write(data)` / `.read()` signatures match can be passed as a handler — even objects from third-party libraries.

### How it runs

```python
json_element = JsonElement({"name": "Alice", "age": 30, "city": "New York"})
handler = JsonFileHandler("test.json")

json_element.write(handler)            # handler satisfies WriteHandler
read_data = json_element.read(handler) # handler satisfies ReadHandler
```

---

## Design Pattern: Strategy + Dependency Injection

```
WriteHandler (Protocol)   ReadHandler (Protocol)
      │                          │
      └──────────┐  ┌────────────┘
                 ▼  ▼
           JsonFileHandler   ← satisfies both protocols structurally
           CsvFileHandler    ← can also satisfy them without inheritance
           NetworkHandler    ← same

JsonElement
  ├── write(handler: WriteHandler)  ← accepts any conforming writer
  └── read(handler: ReadHandler)    ← accepts any conforming reader
```

This is the **Strategy** pattern: `JsonElement` selects its I/O strategy at call time by accepting any object that matches the protocol. Combined with constructor or call-site injection, handlers are fully interchangeable.

---

## ABC vs Protocol — Quick Comparison

| Feature | ABC | Protocol |
|---|---|---|
| Subtyping | Nominal (explicit `class Foo(Base)`) | Structural (duck typing) |
| Requires inheritance | Yes | No |
| Works with third-party classes | Only via `register()` | Yes, automatically |
| Enforces contract at runtime | Yes (`TypeError` on instantiation) | No (only static checkers) |
| Shares implementation | Yes (template methods, mixins) | No |
| Best for | Owned class hierarchies | Interfaces across boundaries |

---

## Suggestions to Improve and Scale

### 1. Use `runtime_checkable` for `isinstance` support

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class WriteHandler(Protocol):
    def write(self, data: dict) -> None: ...

handler = JsonFileHandler("data.json")
print(isinstance(handler, WriteHandler))  # True — works at runtime
```

> **Caution:** `runtime_checkable` only checks method *names*, not signatures.

### 2. Compose protocols for a full file-handler interface

```python
from typing import Protocol

class FileHandlerProtocol(WriteHandler, ReadHandler, Protocol):
    """A protocol requiring both read and write capabilities."""
    pass

def process(handler: FileHandlerProtocol, data: dict) -> dict:
    handler.write(data)
    return handler.read()
```

### 3. Define a generic protocol for any data type

```python
from typing import Protocol, TypeVar

T = TypeVar("T")

class Serializer(Protocol[T]):
    def serialize(self, data: T) -> bytes: ...
    def deserialize(self, data: bytes) -> T: ...
```

### 4. Use protocols for async I/O

```python
from typing import Protocol

class AsyncWriteHandler(Protocol):
    async def write(self, data: dict) -> None: ...

class AsyncReadHandler(Protocol):
    async def read(self) -> dict: ...

class AsyncJsonFileHandler:
    def __init__(self, file_path: str):
        self.file_path = file_path

    async def write(self, data: dict) -> None:
        import aiofiles, json
        async with aiofiles.open(self.file_path, "wb") as f:
            await f.write(json.dumps(data).encode("utf-8"))

    async def read(self) -> dict:
        import aiofiles, json
        async with aiofiles.open(self.file_path, "rb") as f:
            return json.loads((await f.read()).decode("utf-8"))
```

### 5. Narrow protocols for better Single Responsibility

Instead of one large protocol, split by capability so callers only depend on what they need:

```python
class CanWrite(Protocol):
    def write(self, data: dict) -> None: ...

class CanRead(Protocol):
    def read(self) -> dict: ...

class CanDelete(Protocol):
    def delete(self) -> None: ...

# A read-only consumer never needs to know about write or delete
def display(reader: CanRead) -> None:
    print(reader.read())
```

---

## Additional Examples

### Network handler satisfying the same protocols

```python
import urllib.request, json

class HttpJsonHandler:
    """Reads from / writes to a remote JSON API — no inheritance required."""

    def __init__(self, url: str):
        self.url = url

    def write(self, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)

    def read(self) -> dict:
        with urllib.request.urlopen(self.url) as resp:
            return json.loads(resp.read().decode("utf-8"))

# Works transparently wherever WriteHandler / ReadHandler is expected
element = JsonElement({"event": "login"})
handler = HttpJsonHandler("https://api.example.com/events")
element.write(handler)
```

### In-memory handler for unit testing

```python
class InMemoryHandler:
    """Satisfies WriteHandler + ReadHandler without touching the filesystem."""

    def __init__(self):
        self._store: dict | None = None

    def write(self, data: dict) -> None:
        self._store = data

    def read(self) -> dict:
        if self._store is None:
            raise ValueError("Nothing written yet")
        return self._store

# Unit test — no files, no I/O
def test_json_element_round_trip():
    element = JsonElement({"key": "value"})
    mem = InMemoryHandler()
    element.write(mem)
    result = element.read(mem)
    assert result == {"key": "value"}
```

### Database handler

```python
import sqlite3, json

class SqliteJsonHandler:
    def __init__(self, db_path: str, table: str = "data"):
        self.db_path = db_path
        self.table = table
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} (id INTEGER PRIMARY KEY, payload TEXT)"
            )

    def write(self, data: dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {self.table}(id, payload) VALUES (1, ?)",
                (json.dumps(data),)
            )

    def read(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                f"SELECT payload FROM {self.table} WHERE id=1"
            ).fetchone()
        if row is None:
            raise ValueError("No data found")
        return json.loads(row[0])
```

### S3 / cloud-storage handler

```python
import json
import boto3  # pip install boto3

class S3JsonHandler:
    def __init__(self, bucket: str, key: str):
        self._s3 = boto3.client("s3")
        self.bucket = bucket
        self.key = key

    def write(self, data: dict) -> None:
        self._s3.put_object(
            Bucket=self.bucket,
            Key=self.key,
            Body=json.dumps(data).encode("utf-8"),
            ContentType="application/json",
        )

    def read(self) -> dict:
        response = self._s3.get_object(Bucket=self.bucket, Key=self.key)
        return json.loads(response["Body"].read().decode("utf-8"))
```

---

## When to Use Protocol

| Situation | Use Protocol? |
|---|---|
| Integrating third-party classes you cannot modify | ✅ Yes |
| You want interchangeable strategies without a shared base | ✅ Yes |
| You need fine-grained, narrow interface contracts | ✅ Yes |
| Writing library code that should not impose inheritance on users | ✅ Yes |
| Subclasses share a significant amount of common logic | ❌ Use ABC instead |
| You need runtime enforcement (`TypeError` on missing methods) | ❌ Use ABC instead |
