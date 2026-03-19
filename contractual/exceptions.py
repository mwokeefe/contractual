"""
contractual.exceptions
---------------------
All exceptions raised by the library.

Hierarchy
~~~~~~~~~
    ContractError
    ├── PreconditionError   parameter failed its annotation constraint
    ├── PostconditionError  return value failed its annotation constraint
    └── InvariantError      class attribute violated a declared invariant
"""


class ContractError(Exception):
    """Base class for every contract violation."""


class PreconditionError(ContractError):
    """Raised when a parameter fails its annotation constraint."""


class PostconditionError(ContractError):
    """Raised when a return value fails its annotation constraint."""


class InvariantError(ContractError):
    """Raised when a class attribute violates a declared invariant."""
