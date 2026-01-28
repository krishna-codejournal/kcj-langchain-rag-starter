# Python `dataclasses` – Detailed Guide + Comparison: `TypedDict` vs `dataclass` vs Pydantic

`dataclasses` (Python 3.7+) let you create **lightweight, typed “record objects”** with almost no boilerplate.
They shine when you want **structured data + Pythonic objects** (attributes, methods, defaults), without the heaviness of full OOP.

Think of the trio like this:
- **`TypedDict`**: dict schema for type checkers (static typing, no runtime validation)
- **`dataclass`**: Python object for structured data (runtime object, minimal boilerplate)
- **Pydantic**: runtime-validated object for external/unclean data (parsing + validation + errors)

---

## 1) Why `dataclasses` exist (the problem they solve)

Before dataclasses, you wrote a lot of boilerplate for “data containers”:

```python
class User:
    def __init__(self, id: int, name: str, active: bool = True):
        self.id = id
        self.name = name
        self.active = active
```

Dataclasses generate this (and more) automatically.

---

## 2) Basic `@dataclass` example

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    active: bool = True

u = User(id=101, name="Harry")
print(u)          # User(id=101, name='Harry', active=True)
print(u.name)     # Harry
```

### What you get for free
- `__init__`
- `__repr__`
- `__eq__` (comparison by fields)
- easy defaults

---

## 3) Default values and `default_factory` (important)

Mutable defaults should use `default_factory`.

✅ Correct:
```python
from dataclasses import dataclass, field

@dataclass
class ReportRow:
    report_name: str
    flags: list[str] = field(default_factory=list)

r1 = ReportRow("AMS 8.3")
r2 = ReportRow("AMS 8.3")
r1.flags.append("reconciled")
print(r2.flags)  # []  (not shared)
```

❌ Wrong (shared list across instances):
```python
@dataclass
class BadRow:
    report_name: str
    flags: list[str] = []  # don't do this
```

---

## 4) Add methods (dataclasses are real classes)

```python
from dataclasses import dataclass

@dataclass
class Contract:
    contract_id: str
    principal: float
    rate: float

    def annual_interest(self) -> float:
        return self.principal * self.rate

c = Contract("C-001", 10000.0, 0.08)
print(c.annual_interest())  # 800.0
```

This is where dataclasses beat dict-only approaches: behavior + data together.

---

## 5) Immutability: `frozen=True`

If you want “record-like” objects that shouldn’t change:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Currency:
    code: str
    decimals: int = 2

usd = Currency("USD")
# usd.code = "EUR"  # ❌ raises FrozenInstanceError
```

Use-case: config-like objects, keys in dicts/sets, safer pipelines.

---

## 6) Ordering and comparisons

```python
from dataclasses import dataclass

@dataclass(order=True)
class Job:
    priority: int
    name: str

print(Job(1, "critical") < Job(5, "low"))  # True
```

---

## 7) `asdict`, `astuple` (serialization helpers)

```python
from dataclasses import dataclass, asdict, astuple

@dataclass
class Address:
    city: str
    state: str
    zip: str

a = Address("Cary", "NC", "27519")

print(asdict(a))   # {'city': 'Cary', 'state': 'NC', 'zip': '27519'}
print(astuple(a))  # ('Cary', 'NC', '27519')
```

Note: `asdict()` recursively converts nested dataclasses too.

---

## 8) Nested dataclasses (structured domain models)

```python
from dataclasses import dataclass

@dataclass
class Address:
    city: str
    state: str
    zip: str

@dataclass
class UserProfile:
    id: int
    name: str
    address: Address
    tags: list[str]

p = UserProfile(
    id=10,
    name="Krishna",
    address=Address("Cary", "NC", "27519"),
    tags=["vip", "newsletter"],
)
print(p.address.city)  # Cary
```

---

## 9) Dataclasses do NOT validate types at runtime by default

This is the subtle but important part.

```python
u = User(id="101", name="Harry")  # runtime allows it
print(u.id, type(u.id))           # '101' <class 'str'>
```

Static type checkers will warn, but Python won't enforce.

### If you need runtime validation
- add manual checks in `__post_init__`
- or use Pydantic instead

Example with `__post_init__`:

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str

    def __post_init__(self):
        if not isinstance(self.id, int):
            raise TypeError("id must be int")
```

---

## 10) Parse dict/JSON into dataclasses (common pattern)

Dataclasses don’t automatically parse nested dicts; you do it yourself.

```python
from dataclasses import dataclass

@dataclass
class Address:
    city: str
    state: str
    zip: str

@dataclass
class UserProfile:
    id: int
    name: str
    address: Address

def parse_user_profile(payload: dict) -> UserProfile:
    addr = Address(**payload["address"])
    return UserProfile(id=int(payload["id"]), name=str(payload["name"]), address=addr)

payload = {"id": "10", "name": "Harry", "address": {"city": "Cary", "state": "NC", "zip": "27519"}}
p = parse_user_profile(payload)
print(p)
```

If you find yourself writing a lot of parsing/validation glue… that’s a sign Pydantic may fit better.

---

# Comparison: `TypedDict` vs `dataclass` vs Pydantic

## A) Feature comparison (quick)

| Feature | `TypedDict` | `dataclass` | Pydantic |
|---|---|---|---|
| Primary goal | Static typing for dict schemas | Boilerplate-free data objects | Runtime validation + parsing |
| Runtime validation | ❌ No | ❌ (unless you add it) | ✅ Yes |
| Works naturally with JSON/dicts | ✅ Yes (it IS a dict) | ⚠️ Needs conversion/parsing | ✅ Yes (dict in/out) |
| Best for external inputs (APIs, files) | ❌ Not alone | ⚠️ With manual parsing | ✅ Yes |
| Performance | ✅ Fast | ✅ Fast | ⚠️ More overhead |
| Dependencies | ✅ None | ✅ None | ❌ External library |
| Serialization | dict already | `asdict()` | `model_dump()`, `model_dump_json()` |
| Ergonomics (attribute access) | ❌ dict indexing | ✅ attributes | ✅ attributes |
| Error messages for invalid data | ❌ None | ⚠️ manual | ✅ Excellent |

---

## B) When to use what (decision guide)

### Use `TypedDict` when:
- you **must keep data as dicts** (JSON-like everywhere)
- you mainly want **type checking** (autocomplete, key safety)
- data is “trusted enough” or validated elsewhere

**Examples:**
- internal function contracts for dict payloads
- dicts returned from stable internal code
- lightweight typing for data pipelines

---

### Use `dataclass` when:
- you want a **domain object** with attributes and methods
- you want minimal overhead and no dependency
- you control the data creation (or you don’t need heavy parsing)

**Examples:**
- internal models like `Contract`, `Invoice`, `Job`, `ReportRow`
- objects that have behavior (`annual_interest()`, `normalize()`)
- “records” used across modules

---

### Use Pydantic when:
- data comes from **outside** (API, Kafka, files, user input, DB JSON)
- you need **runtime safety** and consistent parsing
- you want standardized serialization and great validation errors

**Examples:**
- FastAPI request/response models
- parsing messy JSON into clean Python objects
- validation before DB insert (ETL/reconciliation guardrails)

---

## C) Common real-world patterns (recommended)

### Pattern 1: Pydantic at the boundary, dataclasses inside
- Validate and parse external JSON with Pydantic
- Convert to dataclass for internal domain logic

Why?
- Pydantic: great bouncer at the door
- Dataclass: light, fast, clean for internal use

---

### Pattern 2: TypedDict for dict-based pipelines + Pydantic for input validation
- TypedDict for internal dict processing functions
- Pydantic only when you accept external input

Why?
- Some pipelines prefer dicts for ease of transformation/merging

---

## D) Example: same “report row” in all three styles

### 1) `TypedDict` (static schema)
```python
from typing import TypedDict, Required, NotRequired

class ReportRowTD(TypedDict):
    report_name: Required[str]
    as_of_date: Required[str]
    total_balance: Required[float]
    currency: NotRequired[str]
    flags: NotRequired[list[str]]
```

### 2) `dataclass` (domain object)
```python
from dataclasses import dataclass, field

@dataclass
class ReportRowDC:
    report_name: str
    as_of_date: str
    total_balance: float
    currency: str = "USD"
    flags: list[str] = field(default_factory=list)

    def is_reconciled(self) -> bool:
        return "reconciled" in self.flags
```

### 3) Pydantic (validation + parsing)
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ReportRowPD(BaseModel):
    report_name: str
    as_of_date: str
    total_balance: float = Field(gt=0)
    currency: Optional[str] = "USD"
    flags: List[str] = []
```

---

## Final mental model (easy to remember)

- **TypedDict**: “a map legend” 🗺️ (tells you what keys exist)
- **dataclass**: “a neat labeled container” 📦 (data + behavior)
- **Pydantic**: “a customs checkpoint” 🛂 (validates + cleans)

---

## Appendix: notes & pitfalls

- `dataclass` doesn’t validate types unless you implement checks.
- Use `field(default_factory=...)` for lists/dicts/sets.
- For large, messy JSON parsing, Pydantic usually saves time and prevents bugs.
