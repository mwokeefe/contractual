"""
pycontract.constraints
======================
The ``Constraint`` base class and every concrete constraint node.

Users never instantiate these directly — they are produced by expressions
such as ``Int > 0``, ``Str.matches(r"\\w+")``, or ``c1 & c2``.

Internal nodes
--------------
_Compare    — single comparison  (>, >=, <, <=, ==, !=)
_Between    — range check        lo <= v <= hi
_Matches    — regex full-match
_MinLen     — len(v) >= n
_MaxLen     — len(v) <= n
_ExactLen   — len(v) == n
_NonEmpty   — bool(v) is truthy
_IsInstance — isinstance(v, types)
_And        — left AND right
_Or         — left OR  right
_Not        — NOT inner
"""

from __future__ import annotations

import re as _re
from typing import Any


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Constraint:
    """
    Abstract base for all constraint objects.

    Concrete subclasses implement :meth:`check` and :meth:`describe`.
    Operator overloads produce compound constraints without any lambdas::

        (Int > 0) & (Int < 100)   →  _And(_Compare(">", 0), _Compare("<", 100))
        ~(Str.non_empty())         →  _Not(_NonEmpty())
    """

    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        """Return True iff *value* satisfies this constraint."""
        raise NotImplementedError

    def describe(self) -> str:
        """Human-readable description used in error messages."""
        return repr(self)

    def __and__(self, other: "Constraint") -> "_And":    return _And(self, other)
    def __or__(self, other: "Constraint") -> "_Or":      return _Or(self, other)
    def __invert__(self) -> "_Not":                      return _Not(self)

    __hash__ = object.__hash__


# ---------------------------------------------------------------------------
# Helper: cross-parameter reference resolution
# ---------------------------------------------------------------------------

def _resolve(value: Any, bound_args: dict | None) -> Any:
    """If *value* is a string key present in *bound_args*, return that arg."""
    if isinstance(value, str) and bound_args and value in bound_args:
        return bound_args[value]
    return value


# ---------------------------------------------------------------------------
# Concrete constraint nodes
# ---------------------------------------------------------------------------

class _Compare(Constraint):
    _OPS = {
        ">":  lambda a, b: a >  b,
        ">=": lambda a, b: a >= b,
        "<":  lambda a, b: a <  b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    def __init__(self, op: str, other: Any) -> None:
        self._op    = op
        self._other = other

    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        try:
            return bool(self._OPS[self._op](value, _resolve(self._other, bound_args)))
        except TypeError:
            return False

    def describe(self) -> str:
        ref = f'"{self._other}"' if isinstance(self._other, str) else repr(self._other)
        return f"value {self._op} {ref}"


class _Between(Constraint):
    def __init__(self, lo: Any, hi: Any, *, inclusive: bool = True) -> None:
        self._lo = lo; self._hi = hi; self._inclusive = inclusive

    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        lo = _resolve(self._lo, bound_args)
        hi = _resolve(self._hi, bound_args)
        return (lo <= value <= hi) if self._inclusive else (lo < value < hi)

    def describe(self) -> str:
        b = "[]" if self._inclusive else "()"
        return f"value in {b[0]}{self._lo}, {self._hi}{b[1]}"


class _Matches(Constraint):
    def __init__(self, pattern: str) -> None:
        self._pattern = pattern
        self._re      = _re.compile(pattern)

    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        return bool(self._re.fullmatch(str(value)))

    def describe(self) -> str:
        return f"value matches r'{self._pattern}'"


class _MinLen(Constraint):
    def __init__(self, n: int) -> None: self._n = n
    def check(self, value: Any, bound_args: dict | None = None) -> bool: return len(value) >= self._n
    def describe(self) -> str: return f"len(value) >= {self._n}"


class _MaxLen(Constraint):
    def __init__(self, n: int) -> None: self._n = n
    def check(self, value: Any, bound_args: dict | None = None) -> bool: return len(value) <= self._n
    def describe(self) -> str: return f"len(value) <= {self._n}"


class _ExactLen(Constraint):
    def __init__(self, n: int) -> None: self._n = n
    def check(self, value: Any, bound_args: dict | None = None) -> bool: return len(value) == self._n
    def describe(self) -> str: return f"len(value) == {self._n}"


class _NonEmpty(Constraint):
    def check(self, value: Any, bound_args: dict | None = None) -> bool: return bool(value)
    def describe(self) -> str: return "value is non-empty"


class _IsInstance(Constraint):
    def __init__(self, types) -> None:
        self._types = types if isinstance(types, tuple) else (types,)

    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        return isinstance(value, self._types)

    def describe(self) -> str:
        return "isinstance(value, {})".format(" | ".join(t.__name__ for t in self._types))


class _And(Constraint):
    def __init__(self, a: Constraint, b: Constraint) -> None: self._a = a; self._b = b
    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        return self._a.check(value, bound_args) and self._b.check(value, bound_args)
    def describe(self) -> str: return f"({self._a.describe()} and {self._b.describe()})"


class _Or(Constraint):
    def __init__(self, a: Constraint, b: Constraint) -> None: self._a = a; self._b = b
    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        return self._a.check(value, bound_args) or self._b.check(value, bound_args)
    def describe(self) -> str: return f"({self._a.describe()} or {self._b.describe()})"


class _Not(Constraint):
    def __init__(self, inner: Constraint) -> None: self._inner = inner
    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        return not self._inner.check(value, bound_args)
    def describe(self) -> str: return f"not ({self._inner.describe()})"


__all__ = [
    "Constraint",
    "_Compare", "_Between", "_Matches",
    "_MinLen", "_MaxLen", "_ExactLen", "_NonEmpty", "_IsInstance",
    "_And", "_Or", "_Not",
]