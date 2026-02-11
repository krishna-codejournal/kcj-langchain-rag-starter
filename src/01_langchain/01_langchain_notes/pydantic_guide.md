# Pydantic – Detailed Guide with Practical Examples (Like `TypedDict`, but Runtime-Validated)

Pydantic is a Python library for **data validation**, **parsing**, and **settings management** using Python type hints.

If `TypedDict` is a “blueprint for type checkers”, Pydantic is a “blueprint with a bouncer at the door” 🛂:
- ✅ **Validates at runtime**
- ✅ **Coerces/parses** common input shapes (e.g., `"123"` → `123`)
- ✅ Produces **helpful error messages**
- ✅ Great for **APIs**, **ETL**, **config**, **JSON payloads**

---

## 1) The core idea

You define a model class with type hints:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    active: bool = True
```

Then you can create it from messy input:

```python
u = User(id="101", name="Harry", active="true")
print(u)
# User(id=101, name='Harry', active=True)

print(u.id, type(u.id))  # 101 <class 'int'>
```

### What’s happening
- Pydantic **parses** input (string → int, string → bool)
- If input is invalid, it raises a `ValidationError` with structured details.

---

## 2) Basic validation example (with errors you can actually use)

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str
    active: bool

try:
    User(id="oops", name=123, active="maybe")
except ValidationError as e:
    print(e)
```

Typical error output includes:
- the field name (`id`, `name`, `active`)
- what went wrong (e.g., “Input should be a valid integer”)
- where in nested data it failed (very helpful for JSON)

---

## 3) Realistic nested JSON example (API payload style)

```python
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    city: str
    state: str
    zip: str

class UserProfile(BaseModel):
    id: int
    name: str
    address: Address
    tags: List[str] = []

payload = {
    "id": "10",
    "name": "Krishna",
    "address": {"city": "Cary", "state": "NC", "zip": "27519"},
    "tags": ["vip", "newsletter"],
}

profile = UserProfile(**payload)
print(profile.address.city)  # Cary
```

**Why this is powerful:**
- Deep parsing and validation for nested dicts
- Clean attribute access (`profile.address.city`)
- Safer than raw dicts

---

## 4) Exporting to dict/JSON

Pydantic models are easy to serialize:

```python
profile_dict = profile.model_dump()
profile_json = profile.model_dump_json()

print(profile_dict["address"]["zip"])
print(profile_json)
```

Common options:
- exclude unset values
- exclude defaults
- exclude `None` fields

Example:

```python
profile.model_dump(exclude_none=True)
```

---

## 5) Field constraints (numbers, strings, length, regex)

Pydantic provides constrained types via `Field(...)`.

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    sku: str = Field(min_length=3, max_length=12)
    price: float = Field(gt=0)
    qty: int = Field(ge=0, le=10_000)

p = Product(sku="ABC123", price=12.5, qty=10)
```

### Common constraints you’ll use
- `gt`, `ge`, `lt`, `le` for numbers
- `min_length`, `max_length` for strings/lists
- `pattern` for regex validation (Pydantic v2)

---

## 6) Optional fields and defaults

```python
from pydantic import BaseModel
from typing import Optional

class Employee(BaseModel):
    emp_id: int
    name: str
    email: Optional[str] = None  # can be None or missing

e1 = Employee(emp_id=1, name="Ava")
e2 = Employee(emp_id=2, name="Ben", email=None)
```

**Key concept:**
- `Optional[str]` means the *value* can be `None`
- Whether the *key* can be missing depends on default:
  - no default → required
  - default provided → optional

---

## 7) Data cleaning: computed fields and custom validation

### A) Custom field validation
Pydantic v2 uses `field_validator`.

```python
from pydantic import BaseModel, field_validator

class Customer(BaseModel):
    name: str
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("email must contain '@'")
        return v

c = Customer(name="Harry", email="  HARRY@EXAMPLE.COM ")
print(c.email)  # harry@example.com
```

### B) Cross-field validation
Use `model_validator`.

```python
from pydantic import BaseModel, model_validator
from datetime import date

class Contract(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self
```

---

## 8) Discriminated unions (multiple shapes, one payload)

This is extremely common in event pipelines.

```python
from pydantic import BaseModel
from typing import Union, Literal

class LoginEvent(BaseModel):
    type: Literal["login"]
    user_id: int
    ip: str

class PurchaseEvent(BaseModel):
    type: Literal["purchase"]
    user_id: int
    amount: float

Event = Union[LoginEvent, PurchaseEvent]

def parse_event(payload: dict) -> Event:
    # Pydantic can validate unions; discriminators make it cleaner (see below)
    return LoginEvent(**payload) if payload.get("type") == "login" else PurchaseEvent(**payload)

print(parse_event({"type": "purchase", "user_id": "7", "amount": "12.30"}))
```

### Discriminator style (recommended for larger unions)
Pydantic supports a discriminator field so it picks the right model based on `type`.

(Exact syntax can vary by version; conceptually it’s: “use `type` to decide the model”.)

---

## 9) `TypedDict` vs Pydantic (quick decision guide)

### Use `TypedDict` when:
- you mostly want **static typing**
- data stays inside your program (trusted)
- you don’t want runtime overhead

### Use Pydantic when:
- data comes from outside: **API**, **DB**, **files**, **Kafka**, **user input**
- you need **runtime safety** and good error reporting
- you want structured objects with `.model_dump()` and `.model_dump_json()`

**In real systems:**
- `TypedDict` is great for internal dict schemas
- Pydantic is great at boundaries and for validation

---

## 10) Pydantic for ETL / reconciliation style workflows (very relevant for data engineers)

### Example: validating a “report row” pulled from a CSV or API
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ReportRow(BaseModel):
    report_name: str
    as_of_date: str  # could be date; keeping str for CSV simplicity
    total_balance: float
    currency: Optional[str] = "USD"
    flags: List[str] = Field(default_factory=list)

row = ReportRow(
    report_name="AMS 8.3",
    as_of_date="2026-01-25",
    total_balance="12345.67",
    flags=["reconciled", "audited"]
)

print(row.total_balance)          # 12345.67 (float)
print(row.model_dump())           # dict ready for DB insert / logging
```

This pattern is extremely handy when:
- reading from MongoDB/JSON and writing to Oracle
- normalizing incoming data
- ensuring required fields exist before DB operations

---

## 11) Settings management (env vars, config files)

Pydantic includes a “Settings” pattern (commonly used in FastAPI apps).

Conceptually:
- define config fields
- Pydantic loads from environment variables and validates types

Example:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    oracle_dsn: str
    mongo_uri: str
    batch_size: int = 1000

settings = Settings()
print(settings.batch_size)
```

If `batch_size` is set to `"5000"` in env vars, it becomes an `int`.

---

## 12) Best practices

- **Validate at boundaries**: API requests, file ingestion, message queues.
- Use `Field(default_factory=...)` for mutable defaults:
  - ✅ `flags: list[str] = Field(default_factory=list)`
  - ❌ `flags: list[str] = []`
- Keep models small and composable; compose nested models.
- Prefer `date`, `datetime`, `Decimal` when precision matters (finance).

---

## 13) Mini-exercise

Create a Pydantic model for:

```python
{
  "report_name": "AMS 8.3",
  "as_of_date": "2026-01-25",
  "total_balance": 12345.67,
  "currency": "USD",
  "flags": ["reconciled", "audited"]
}
```

Requirements:
- `report_name`, `as_of_date`, `total_balance` required
- `currency` optional, default `"USD"`
- `flags` default empty list
- `total_balance` must be `> 0`

---

## Appendix: Version notes (high-level)

Pydantic has major versions (v1 and v2) with some API differences:
- v2 commonly uses `model_dump()` (instead of `dict()` in v1)
- validators are `field_validator` / `model_validator` in v2

If you see older code using:
- `@validator(...)` and `.dict()`, that’s typically v1 style.

---

### Quick reference snippet (Pydantic v2 style)

```python
from pydantic import BaseModel, Field

class Example(BaseModel):
    a: int
    b: str = Field(min_length=2)
```
