"""
pycontract.decorators
=====================
The two public decorators: :func:`contract` and :func:`invariant`.

``@contract``
-------------
Enforces ``Constraint`` annotations on function parameters *and* return
values.  Reads annotations at decoration time (once), then checks on
every call.  Respects ``pycontract.config.enabled`` for zero-cost bypass.

    @contract
    def divide(x: Float, y: Float != 0) -> Float:
        return x / y

``@invariant``
--------------
Enforces ``Constraint`` class-body annotations after every public method
call (and after ``__init__``).

    @invariant
    class BankAccount:
        balance: Float >= 0
        owner:   Str.non_empty()

        def __init__(self, owner: str, balance: float) -> None:
            self.owner   = owner
            self.balance = balance

        def withdraw(self, amount: float) -> None:
            self.balance -= amount
"""

from __future__ import annotations

import functools
import inspect
import typing
from typing import Any, Callable, get_args, get_origin, get_type_hints

from . import config
from .constraints import Constraint
from .exceptions import InvariantError, PostconditionError, PreconditionError


# ---------------------------------------------------------------------------
# Helper: extract a Constraint from an annotation
# ---------------------------------------------------------------------------

def _extract_constraint(annotation: Any) -> Constraint | None:
    """Return the first Constraint found in *annotation*, or None."""
    if isinstance(annotation, Constraint):
        return annotation
    if get_origin(annotation) is typing.Annotated:
        for meta in get_args(annotation)[1:]:
            if isinstance(meta, Constraint):
                return meta
    return None


def _collect_constraints(fn: Callable) -> dict[str, Constraint]:
    """Return {param_name: Constraint} for all annotated params + 'return'."""
    try:
        hints = get_type_hints(fn, include_extras=True)
    except Exception:
        hints = getattr(fn, "__annotations__", {})
    return {
        name: c
        for name, ann in hints.items()
        if (c := _extract_constraint(ann)) is not None
    }


# ---------------------------------------------------------------------------
# @contract
# ---------------------------------------------------------------------------

def contract(fn: Callable) -> Callable:
    """
    Enforce Constraint annotations on a function's parameters and return value.

    Usage — annotate and decorate, no extra arguments::

        @contract
        def power(base: Float >= 0, exponent: Int.between(0, 10)) -> Float >= 0:
            return base ** exponent

    When ``pycontract.config.enabled`` is False the wrapper is a transparent
    pass-through with zero overhead.
    """
    sig     = inspect.signature(fn)
    all_c   = _collect_constraints(fn)
    ret_c   = all_c.pop("return", None)
    param_c = all_c

    # Optimisation: if there is nothing to check, return the original function
    # unchanged — no wrapper, no overhead, identity preserved.
    if not param_c and ret_c is None:
        return fn

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not config.enabled:
            return fn(*args, **kwargs)

        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        ba = dict(bound.arguments)

        # Preconditions
        for param, c in param_c.items():
            if param not in ba:
                continue
            value = ba[param]
            try:
                ok = c.check(value, ba)
            except Exception as exc:
                raise PreconditionError(
                    f"{fn.__qualname__}: constraint for '{param}' raised: {exc}"
                ) from exc
            if not ok:
                raise PreconditionError(
                    f"{fn.__qualname__}: '{param}={value!r}' violates — {c.describe()}"
                )

        result = fn(*args, **kwargs)

        # Postcondition (return value)
        if ret_c is not None:
            try:
                ok = ret_c.check(result, ba)
            except Exception as exc:
                raise PostconditionError(
                    f"{fn.__qualname__}: return value constraint raised: {exc}"
                ) from exc
            if not ok:
                raise PostconditionError(
                    f"{fn.__qualname__}: return value {result!r} violates — {ret_c.describe()}"
                )

        return result

    wrapper.__param_constraints__ = param_c  # type: ignore[attr-defined]
    wrapper.__return_constraint__  = ret_c   # type: ignore[attr-defined]
    return wrapper


# ---------------------------------------------------------------------------
# @invariant
# ---------------------------------------------------------------------------

def invariant(cls: type) -> type:
    """
    Enforce Constraint class-body annotations after every public method call.

    Usage::

        @invariant
        class Rectangle:
            width:  Float > 0
            height: Float > 0

            def __init__(self, w: float, h: float) -> None:
                self.width  = w
                self.height = h

            def scale(self, factor: Float > 0) -> None:
                self.width  *= factor
                self.height *= factor
    """
    attr_constraints: dict[str, Constraint] = {
        name: c
        for name, ann in getattr(cls, "__annotations__", {}).items()
        if (c := _extract_constraint(ann)) is not None
    }
    cls_name = cls.__qualname__

    def _check_invariants(instance: Any) -> None:
        for attr, c in attr_constraints.items():
            value = getattr(instance, attr, None)
            try:
                ok = c.check(value)
            except Exception as exc:
                raise InvariantError(
                    f"{cls_name}.{attr}: invariant check raised: {exc}"
                ) from exc
            if not ok:
                raise InvariantError(
                    f"{cls_name}.{attr}={value!r} violates — {c.describe()}"
                )

    def _wrap_method(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if not config.enabled:
                return method(self, *args, **kwargs)
            result = method(self, *args, **kwargs)
            _check_invariants(self)
            return result
        return wrapper

    for name, obj in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name == "__init__" or not name.startswith("_"):
            setattr(cls, name, _wrap_method(obj))

    cls.__invariant_constraints__ = attr_constraints  # type: ignore[attr-defined]
    return cls


__all__ = ["contract", "invariant"]