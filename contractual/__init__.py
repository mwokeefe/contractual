"""
contractual
==========
Design by Contract for Python — no lambdas, no strings, just expressions.

Quick start::

    from contractual import contract, invariant, Int, Float, Str

    @contract
    def divide(x: Float, y: Float != 0) -> Float:
        return x / y

    @invariant
    class BankAccount:
        balance: Float >= 0
        owner:   Str.non_empty()

        def __init__(self, owner: str, balance: float) -> None:
            self.owner   = owner
            self.balance = balance

        def withdraw(self, amount: float) -> None:
            self.balance -= amount

Disabling checks (e.g. in production)::

    import contractual
    contractual.disable()
    # ... later ...
    contractual.enable()
"""

from .config import enable, disable
from . import config

from .exceptions import (
    ContractError,
    InvariantError,
    PostconditionError,
    PreconditionError,
)

from .constraints import Constraint

from .types import (
    Any_,
    Bool,
    Dict,
    Float,
    Int,
    List,
    Str,
    Tuple,
)

from .decorators import contract, invariant

__version__ = "0.1.0"

__all__ = [
    "contract",
    "invariant",
    "Int",
    "Float",
    "Str",
    "Bool",
    "List",
    "Tuple",
    "Dict",
    "Any_",
    "Constraint",
    "ContractError",
    "PreconditionError",
    "PostconditionError",
    "InvariantError",
    "enable",
    "disable",
    "config",
]
