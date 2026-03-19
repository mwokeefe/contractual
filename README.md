# contractual

Design by Contract for Python — write constraints directly in type annotations.
No lambdas. No strings. Just natural Python expressions.

```python
from contractual import contract, invariant, Int, Float, Str

@contract
def power(base: Float >= 0, exponent: Int.between(0, 10)) -> Float >= 0:
    return base ** exponent

@invariant
class BankAccount:
    balance: Float >= 0
    owner:   Str.non_empty()

    def __init__(self, owner: str, balance: float) -> None:
        self.owner   = owner
        self.balance = balance

    def withdraw(self, amount: float) -> None:
        self.balance -= amount
```

---

## Contents

- [Installation](#installation)
- [Why contractual?](#why-contractual)
- [Quick start](#quick-start)
- [Constraint reference](#constraint-reference)
- [Combining constraints](#combining-constraints)
- [Cross-parameter references](#cross-parameter-references)
- [Return value constraints](#return-value-constraints)
- [Class invariants](#class-invariants)
- [Using with `Annotated`](#using-with-annotated)
- [Disabling checks](#disabling-checks)
- [Error types](#error-types)
- [Package layout](#package-layout)
- [Requirements](#requirements)

---

## Installation

```bash
pip install contractual
```

Development install (includes pytest):

```bash
git clone https://github.com/you/contractual
cd contractual
pip install -e ".[dev]"
pytest
```

---

## Why contractual?

Design by Contract is a technique where you specify *what must be true* about
inputs and outputs, rather than writing defensive `if` checks scattered through
your code. Contracts live at the boundary of a function, are easy to read at a
glance, and can be turned off entirely in production.

Most Python DBC libraries require you to write lambdas or decorator arguments:

```python
# Before — other libraries
@require(lambda n: n >= 0)
@ensure(lambda result: result >= 0)
def factorial(n): ...
```

contractual puts constraints directly in the annotation, where they belong:

```python
# After — contractual
@contract
def factorial(n: Int >= 0) -> Int >= 0: ...
```

This works because `Int`, `Float`, `Str` etc. are objects that override
Python's comparison operators (`__gt__`, `__ge__`, …) to return lazy
constraint objects rather than evaluating immediately. The decorator reads those
objects at decoration time and checks them on every call.

---

## Quick start

```python
from contractual import contract, invariant, Int, Float, Str, List
```

**1. Decorate a function with `@contract`:**

```python
@contract
def divide(x: Float, y: Float != 0) -> Float:
    return x / y

divide(10.0, 2.0)   # 5.0
divide(10.0, 0.0)   # raises PreconditionError: 'y=0.0' violates — value != 0
```

**2. Annotate class attributes and decorate with `@invariant`:**

```python
@invariant
class Stack:
    items: List

    def __init__(self) -> None:
        self.items = []

    @contract
    def push(self, value) -> None:
        self.items.append(value)

    @contract
    def pop(self, ): ...   # can combine both decorators
```

**3. Disable checks in production:**

```python
import contractual
contractual.disable()
```

---

## Constraint reference

### Numeric — `Int`, `Float`

`Int` accepts `int` values. `Float` accepts `float` **and** `int` values
(matching the mathematical notion of a real number).

| Expression | Meaning |
|---|---|
| `Int > 0` | strictly greater than zero |
| `Int >= 0` | non-negative |
| `Int < 100` | less than 100 |
| `Int <= 100` | at most 100 |
| `Int == 42` | exactly 42 |
| `Int != 0` | non-zero |
| `Int.between(1, 100)` | inclusive range [1, 100] |
| `Int.between(0, 1, inclusive=False)` | exclusive range (0, 1) |
| `Float >= 0` | non-negative float or int |
| `Float.between(0.0, 1.0)` | probability / unit range |

### String — `Str`

| Expression | Meaning |
|---|---|
| `Str` | any `str` value |
| `Str.non_empty()` | at least one character (`bool(value)` is truthy) |
| `Str.min_len(3)` | `len(value) >= 3` |
| `Str.max_len(255)` | `len(value) <= 255` |
| `Str.len(8)` | `len(value) == 8` |
| `Str.matches(r"\w+")` | full regex match (`re.fullmatch`) |

### Collections — `List`, `Tuple`, `Dict`

| Expression | Meaning |
|---|---|
| `List.non_empty()` | at least one element |
| `List.min_len(2)` | at least 2 elements |
| `List.max_len(100)` | at most 100 elements |
| `Tuple.len(3)` | exactly 3 elements |
| `Dict.non_empty()` | at least one key |

### Other types — `Bool`, `Any_`

| Expression | Meaning |
|---|---|
| `Bool` | must be `bool` (not just truthy — `isinstance` checked) |
| `Any_` | any type; useful as a base to combine with `&` |

---

## Combining constraints

Use `&` (and), `|` (or), and `~` (not) to build compound constraints:

```python
# Both conditions must hold
@contract
def percentage(n: (Int >= 0) & (Int <= 100)) -> str:
    return f"{n}%"

# Either condition is acceptable
@contract
def id_or_name(value: (Int > 0) | Str.non_empty()):
    ...

# Negation
@contract
def non_zero(x: ~(Int == 0)) -> float:
    return 1 / x
```

> **Note:** Always wrap individual constraints in parentheses before combining —
> `(Int > 0) & (Int < 100)` not `Int > 0 & Int < 100` — because Python's
> operator precedence evaluates `&` before `>`.

---

## Cross-parameter references

Pass a **string** as the comparison bound to reference another parameter by
name. The value is resolved at call time from the bound arguments:

```python
@contract
def clamp(value: Int, lo: Int, hi: Int > "lo") -> Int:
    """hi must be greater than lo."""
    return max(lo, min(hi, value))

clamp(5, 0, 10)   # ok
clamp(5, 10, 5)   # raises PreconditionError: 'hi=5' violates — value > "lo"
```

This works for any comparison operator: `Int > "other"`, `Float <= "limit"`, etc.

---

## Return value constraints

Annotate the return type with a constraint to enforce postconditions:

```python
@contract
def sqrt(x: Float >= 0) -> Float >= 0:
    return x ** 0.5

@contract
def normalise(values: List.non_empty()) -> List.non_empty():
    total = sum(values)
    return [v / total for v in values]
```

A `PostconditionError` is raised if the return value fails the constraint.
This is useful for catching bugs where a valid input produces a logically
invalid output.

---

## Class invariants

`@invariant` reads `Constraint` annotations declared at the class body level
and checks them after `__init__` and after every public method call.

```python
@invariant
class Temperature:
    kelvin: Float >= 0   # absolute zero is the floor

    def __init__(self, kelvin: float) -> None:
        self.kelvin = kelvin

    def heat(self, delta: Float >= 0) -> None:
        self.kelvin += delta

    def cool(self, delta: Float >= 0) -> None:
        self.kelvin -= delta   # invariant checked here — raises if kelvin < 0
```

**Rules:**
- Only class-level annotations are checked — instance variables set inside
  methods without a class annotation are ignored.
- Dunder methods (e.g. `__repr__`, `__str__`) are not wrapped.
- `@contract` and `@invariant` can be combined on the same class: apply
  `@contract` to individual methods and `@invariant` to the class.

---

## Using with `Annotated`

If you want to keep standard Python type hints for type checkers (mypy,
pyright) while still using contractual constraints, use `typing.Annotated`:

```python
from typing import Annotated
from contractual import contract, Int, Float

@contract
def interest(principal: Annotated[float, Float > 0],
             rate:      Annotated[float, Float.between(0, 1)],
             years:     Annotated[int,   Int > 0]) -> float:
    return principal * (1 + rate) ** years
```

The type checker sees `float` / `int`; contractual sees the constraint in the
second `Annotated` argument. Both are happy.

---

## Disabling checks

Set `contractual.config.enabled = False` (or call the helper functions) to skip
all constraint checks globally. The wrappers become transparent pass-throughs
with no measurable overhead — useful when you trust your production inputs and
want zero overhead.

```python
import contractual

# Disable
contractual.disable()

# Re-enable
contractual.enable()

# Check current state
print(contractual.config.enabled)  # True / False
```

You can also drive this from an environment variable in your app's entry point:

```python
import os, contractual

if os.getenv("ENV") == "production":
    contractual.disable()
```

---

## Error types

All exceptions inherit from `ContractError`:

```
ContractError
├── PreconditionError   — a parameter failed its constraint
├── PostconditionError  — the return value failed its constraint
└── InvariantError      — a class attribute violated its invariant
```

Catch them specifically or together:

```python
from contractual import PreconditionError, ContractError

try:
    divide(10, 0)
except PreconditionError as e:
    print(f"Bad input: {e}")
except ContractError as e:
    print(f"Contract violated: {e}")
```

Error messages include the function name, the parameter name, the offending
value, and a description of the constraint:

```
contractual.exceptions.PreconditionError:
    divide: 'y=0.0' violates — value != 0
```

---

## Package layout

```
contractual/
├── __init__.py        # public API — import everything from here
├── config.py          # enabled flag, enable() / disable()
├── constraints.py     # Constraint base class + internal nodes
│                        (_Compare, _Between, _Matches, _And, _Or, _Not, …)
├── types.py           # Int, Float, Str, Bool, List, Tuple, Dict, Any_
│                        (_TypeConstraint singleton builder)
├── decorators.py      # @contract and @invariant
├── exceptions.py      # ContractError hierarchy
└── py.typed           # PEP 561 marker — package ships type information
```

If you want to define a custom constraint type, subclass `Constraint` from
`contractual.constraints` and implement `check(value, bound_args)` and
`describe()`:

```python
from contractual.constraints import Constraint

class Positive(Constraint):
    def check(self, value, bound_args=None) -> bool:
        return isinstance(value, (int, float)) and value > 0

    def describe(self) -> str:
        return "value is positive"

positive = Positive()

@contract
def sqrt(x: positive) -> float:
    return x ** 0.5
```

---

## Requirements

- Python 3.10 or later
- No runtime dependencies — pure standard library
