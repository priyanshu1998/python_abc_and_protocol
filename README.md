# Python ABC and Protocol

A hands-on comparison of two complementary Python mechanisms for defining and enforcing interfaces: **Abstract Base Classes (ABC)** and **typing.Protocol**.

---

## Repository Layout

```
.
├── abstract_base_class/
│   ├── JsonFileHandler.py    # ABC approach — JSON serialization
│   ├── PickleFileHandler.py  # ABC approach — Pickle serialization
│   └── README.md             # Deep-dive: ABC pattern, examples, scaling tips
│
├── protocol/
│   ├── JsonFileHandler.py    # Protocol-compatible handler (no base class)
│   ├── protocol_example.py   # Protocol definitions + JsonElement consumer
│   └── README.md             # Deep-dive: Protocol pattern, examples, scaling tips
│
├── data.json                 # Sample output from JsonFileHandler
├── data.pkl                  # Sample output from PickleFileHandler
└── test.json                 # Sample output from protocol example
```

---

## What Problem Do These Patterns Solve?

Both patterns answer the same question:

> **"How do I write code that works with any object that has certain capabilities, without caring about its concrete type?"**

They differ in *how* they express that contract:

| | ABC | Protocol |
|---|---|---|
| Contract enforcement | Nominal (via inheritance) | Structural (via shape/duck typing) |
| Requires subclassing | Yes | No |
| Shared implementation | Yes (template methods) | No |
| Works with third-party code | Via `register()` only | Automatically |
| Runtime `isinstance` check | ✅ built-in | ✅ with `@runtime_checkable` |
| Static type-checker support | ✅ | ✅ |

---

## Abstract Base Class (ABC) — Summary

The `abstract_base_class/` folder shows the **Template Method** design pattern:

```
FileHandler (ABC)
├── write()        ← template: open file → serialize → write bytes
└── read()         ← template: read bytes → deserialize → return dict
      │
      ├── JsonFileHandler   serialize/deserialize with JSON
      └── PickleFileHandler serialize/deserialize with Pickle
```

`FileHandler` owns the file-I/O algorithm. Subclasses only supply the format-specific hooks (`serialize` / `deserialize`). Python refuses to instantiate any subclass that forgets to implement an abstract method.

➡ See [`abstract_base_class/README.md`](abstract_base_class/README.md) for the full walkthrough, improvement ideas, and more examples.

---

## Protocol — Summary

The `protocol/` folder shows the **Strategy + Dependency Injection** pattern:

```
WriteHandler (Protocol)    ReadHandler (Protocol)
        │                          │
        └──────────┐  ┌────────────┘
                   ▼  ▼
             JsonFileHandler   ← satisfies both protocols (no inheritance)
             HttpJsonHandler   ← also satisfies them, from a different module
             InMemoryHandler   ← great for tests

JsonElement
  ├── write(handler: WriteHandler)
  └── read(handler: ReadHandler)
```

`JsonElement` accepts *any* object whose `write` / `read` signatures match—completely decoupled from the I/O implementation.

➡ See [`protocol/README.md`](protocol/README.md) for the full walkthrough, improvement ideas, and more examples.

---

## Choosing Between ABC and Protocol

Use **ABC** when:
- You control the entire class hierarchy.
- Subclasses share significant common logic (template methods, mixins).
- You want a hard runtime error if a subclass misses a required method.

Use **Protocol** when:
- You want to describe an interface without forcing inheritance.
- You need to work with third-party or legacy classes you cannot modify.
- You are writing library code and don't want to impose a base class on users.
- You want narrow, single-responsibility interfaces.

---

## Running the Examples

```bash
# ABC examples
python abstract_base_class/JsonFileHandler.py
python abstract_base_class/PickleFileHandler.py

# Protocol example (run from the protocol/ directory so the import resolves)
cd protocol
python protocol_example.py
```
