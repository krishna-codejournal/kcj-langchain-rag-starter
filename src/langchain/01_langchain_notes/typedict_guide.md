# Python `TypedDict` (typing) – Detailed Guide with Practical Examples

`TypedDict` lets you describe the **expected keys and value types of a dictionary** in a way that static type checkers (mypy, pyright, pylance, etc.) can understand.

It’s especially useful when you:
- consume/produce **JSON-like dicts**
- pass dict “records” between functions
- want **type checking** without converting dicts into classes

> Important: `TypedDict` is mainly for **static typing**. At runtime, it’s still just a normal `dict`.

---

## 1) Why `TypedDict` exists (the problem it solves)

Consider a typical “record” dict:

```python
user = {"id": 101, "name": "Harry", "active": True}
```

Without `TypedDict`, you often end up with types like:

```python
from typing import Any

def send_welcome_email(user: dict[str, Any]) -> None:
    # type checker can't help you much here
    if user["active"]:
        print("Sending email to", user["name"])
```

Problems:
- You can accidentally do `user["actve"]` (typo) and only find it at runtime.
- You can store wrong types like `"id": "101"` and nobody warns you.
- You can’t easily communicate what keys are required vs optional.

`TypedDict` fixes this by declaring the schema of the dict.

---

## 2) Basic `TypedDict` example (required keys)

```python
from typing import TypedDict

class User(TypedDict):
    id: int
    name: str
    active: bool

def send_welcome_email(user: User) -> None:
    if user["active"]:
        print(f"Sending email to {user['name']} (id={user['id']})")

u1: User = {"id": 101, "name": "Harry", "active": True}
send_welcome_email(u1)
```

### What the type checker now catches
```python
bad_user: User = {"id": "101", "name": "Harry", "active": True}  # ❌ id should be int
bad_user2: User = {"id": 101, "name": "Harry"}                  # ❌ missing "active"
bad_user3: User = {"id": 101, "name": "Harry", "active": True, "age": 30}  # depends on checker settings
```

---

## 3) Optional keys (two common ways)

### A) Make all keys optional: `total=False`
`total=False` means: “keys may be missing”.

```python
from typing import TypedDict

class UserPatch(TypedDict, total=False):
    name: str
    active: bool

def apply_patch(user: dict, patch: UserPatch) -> dict:
    user.update(patch)
    return user

patch1: UserPatch = {"active": False}  # OK
patch2: UserPatch = {}                 # OK (everything optional)
```

**Use-case:** HTTP PATCH payloads, partial updates, “only the fields that changed”.

### B) Mix required and optional keys: `Required` / `NotRequired`
This is the most expressive approach (Python 3.11+ in `typing`, earlier via `typing_extensions`).

```python
from typing import TypedDict, Required, NotRequired

class UserRecord(TypedDict):
    id: Required[int]
    name: Required[str]
    active: NotRequired[bool]  # optional key, but if present must be bool
    email: NotRequired[str]

u_ok: UserRecord = {"id": 1, "name": "Ava"}                # OK
u_ok2: UserRecord = {"id": 2, "name": "Ben", "active": True}  # OK
u_bad: UserRecord = {"name": "NoId"}                       # ❌ missing required "id"
```

**Use-case:** JSON responses where some fields are guaranteed and some are “maybe”.

> If you’re on Python < 3.11, do:
>
> ```python
> from typing_extensions import Required, NotRequired
> ```

---

## 4) A realistic nested JSON example

Many APIs return nested JSON (dicts containing dicts/lists). `TypedDict` helps a lot here.

```python
from typing import TypedDict

class Address(TypedDict):
    city: str
    state: str
    zip: str

class UserProfile(TypedDict):
    id: int
    name: str
    address: Address
    tags: list[str]

def format_shipping_label(profile: UserProfile) -> str:
    addr = profile["address"]
    return (
        f"{profile['name']}\n"
        f"{addr['city']}, {addr['state']} {addr['zip']}\n"
        f"Tags: {', '.join(profile['tags'])}"
    )

p: UserProfile = {
    "id": 10,
    "name": "Krishna",
    "address": {"city": "Cary", "state": "NC", "zip": "27519"},
    "tags": ["vip", "newsletter"]
}

print(format_shipping_label(p))
```

**What you gain:**
- autocomplete on `profile["address"]["city"]`
- fewer key typos
- correct list element typing (e.g., `list[str]`)

---

## 5) `TypedDict` vs `dataclass` vs `pydantic` (when to choose what)

### `TypedDict`
- ✅ best when your data is naturally dict/JSON and you want **static typing**
- ✅ zero runtime overhead (it’s still a dict)
- ❌ no runtime validation (a bad dict can still appear at runtime)

### `dataclass`
- ✅ good when you want a structured Python object, methods, defaults
- ✅ can convert to/from dict, but that’s extra work
- ❌ not “naturally” JSON unless you serialize

### `pydantic` (or other validators)
- ✅ runtime validation + parsing
- ✅ excellent for API boundaries
- ❌ adds dependency + runtime cost

**Rule of thumb:**
- Inside your codebase where you just want typing for dicts → `TypedDict`
- At boundaries (API inputs, external JSON, user input) → consider runtime validation

---

## 6) Inheritance and composition

You can extend a schema:

```python
from typing import TypedDict

class BaseEvent(TypedDict):
    event_id: str
    timestamp: str

class LoginEvent(BaseEvent):
    user_id: int
    ip: str

e: LoginEvent = {
    "event_id": "evt-1",
    "timestamp": "2026-01-25T20:00:00-05:00",
    "user_id": 42,
    "ip": "10.0.0.5",
}
```

**Use-case:** event pipelines, audit logs, shared fields across payloads.

---

## 7) “Discriminated union” style patterns with `Literal`

If you have “one of several shapes”:

```python
from typing import TypedDict, Literal, Union

class Cat(TypedDict):
    type: Literal["cat"]
    meows: bool

class Dog(TypedDict):
    type: Literal["dog"]
    barks: bool

Pet = Union[Cat, Dog]

def speak(pet: Pet) -> str:
    if pet["type"] == "cat":
        return "meow" if pet["meows"] else "(silent cat)"
    else:
        return "woof" if pet["barks"] else "(silent dog)"

print(speak({"type": "cat", "meows": True}))
print(speak({"type": "dog", "barks": False}))
```

**What you gain:** type checkers narrow the dict shape based on `type`.

---

## 8) Runtime reality: it’s still a `dict`

`TypedDict` does *not* enforce anything at runtime:

```python
from typing import TypedDict

class User(TypedDict):
    id: int
    name: str

u: User = {"id": 1, "name": "Ava"}

print(type(u))  # <class 'dict'>
```

This will not raise an error at runtime even though it’s wrong (but type checker would warn):

```python
u2: User = {"id": "oops", "name": "Ava"}  # runtime still fine unless you validate
```

---

## 9) Best practices and tips

### Tip 1: Use `TypedDict` for “schemas”, not for arbitrary dicts
If the dict is unstructured or free-form, keep it as `dict[str, Any]` or use a validator.

### Tip 2: Prefer `Required/NotRequired` for mixed schemas
It’s clearer than `total=False` + workarounds.

### Tip 3: Name your TypedDicts like API objects
Examples:
- `OrderResponse`
- `UserPatch`
- `ReportRow`
- `InvoiceLineItem`

### Tip 4: Keep nesting manageable
If a payload gets huge, split it into smaller TypedDicts and compose them.

---

## 10) Mini-exercise (for practice)

Define a `TypedDict` for a report row that looks like:

```python
{
  "report_name": "AMS 8.3",
  "as_of_date": "2026-01-25",
  "total_balance": 12345.67,
  "currency": "USD",
  "flags": ["reconciled", "audited"]
}
```

Try:
- Make `report_name`, `as_of_date`, `total_balance` required
- Make `currency` optional
- Ensure `flags` is `list[str]`

---

## Appendix: Version notes

- `TypedDict` exists in `typing` (Python 3.8+), and earlier in `typing_extensions`.
- `Required` / `NotRequired` are in `typing` in Python 3.11+, else use `typing_extensions`.

---

### Quick reference snippet

```python
from typing import TypedDict, Required, NotRequired

class Example(TypedDict):
    a: Required[int]
    b: NotRequired[str]
```
