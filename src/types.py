"""
pycontract.types
================
Constraint-builder singletons: ``Int``, ``Float``, ``Str``, ``Bool``,
``List``, ``Tuple``, ``Dict``, ``Any_``.

Each is an instance of ``_TypeConstraint`` which:

* acts as a standalone constraint (passes if isinstance(value, T))
* overrides comparison operators to produce richer constraints:

      Int > 0            ->  isinstance AND value > 0
      Float.between(0,1) ->  isinstance AND 0 <= value <= 1
      Str.matches(r"…")  ->  isinstance AND re.fullmatch(…)
"""

from __future__ import annotations

from typing import Any

from .constraints import (
    Constraint,
    _And,
    _Between,
    _Compare,
    _ExactLen,
    _IsInstance,
    _Matches,
    _MaxLen,
    _MinLen,
    _NonEmpty,
)


class _TypeConstraint(Constraint):
    """
    A constraint that checks isinstance(value, *types) and acts as a
    fluent builder for richer constraints.
    """

    def __init__(self, *types: type, name: str = "") -> None:
        self._types = types
        self._name = name or " | ".join(t.__name__ for t in types)
        self._tc = _IsInstance(types)

    def _c(self, constraint: Constraint) -> _And:
        """Bundle isinstance check with *constraint*."""
        return _And(self._tc, constraint)

    # Comparison operators -> _And(isinstance, _Compare)
    def __gt__(self, other: Any) -> _And:
        return self._c(_Compare(">", other))

    def __ge__(self, other: Any) -> _And:
        return self._c(_Compare(">=", other))

    def __lt__(self, other: Any) -> _And:
        return self._c(_Compare("<", other))

    def __le__(self, other: Any) -> _And:
        return self._c(_Compare("<=", other))

    def __eq__(self, other: Any) -> _And:
        return self._c(_Compare("==", other))  # type: ignore[override]

    def __ne__(self, other: Any) -> _And:
        return self._c(_Compare("!=", other))  # type: ignore[override]

    __hash__ = object.__hash__

    # Standalone use (no operator) — passes if value is the right type
    def check(self, value: Any, bound_args: dict | None = None) -> bool:
        return self._tc.check(value, bound_args)

    def describe(self) -> str:
        return f"isinstance(value, {self._name})"

    def __repr__(self) -> str:
        return f"<{self._name} constraint>"

    # Named shorthands
    def between(self, lo: Any, hi: Any, *, inclusive: bool = True) -> _And:
        """Value in [lo, hi] (inclusive=True) or (lo, hi) (inclusive=False)."""
        return self._c(_Between(lo, hi, inclusive=inclusive))

    def non_empty(self) -> _And:
        """Collection / string must be truthy (len > 0)."""
        return self._c(_NonEmpty())

    def min_len(self, n: int) -> _And:
        """len(value) >= n."""
        return self._c(_MinLen(n))

    def max_len(self, n: int) -> _And:
        """len(value) <= n."""
        return self._c(_MaxLen(n))

    def len(self, n: int) -> _And:
        """len(value) == n."""
        return self._c(_ExactLen(n))

    def matches(self, pattern: str) -> _And:
        """re.fullmatch(pattern, str(value)) must succeed."""
        return self._c(_Matches(pattern))

    def one_of(self, *choices: Any) -> _And:
        """Value must be one of the supplied options."""
        from .constraints import _Or  # avoid circular at module level

        node: Constraint = _Compare("==", choices[0])
        for ch in choices[1:]:
            node = _Or(node, _Compare("==", ch))
        return self._c(node)


# Singletons — the public API
Int = _TypeConstraint(int, name="int")
Float = _TypeConstraint(float, int, name="float")
Str = _TypeConstraint(str, name="str")
Bool = _TypeConstraint(bool, name="bool")
List = _TypeConstraint(list, name="list")
Tuple = _TypeConstraint(tuple, name="tuple")
Dict = _TypeConstraint(dict, name="dict")
Any_ = _TypeConstraint(object, name="any")


__all__ = [
    "_TypeConstraint",
    "Int",
    "Float",
    "Str",
    "Bool",
    "List",
    "Tuple",
    "Dict",
    "Any_",
]
