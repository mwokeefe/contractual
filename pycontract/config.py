"""
pycontract.config
=================
Runtime configuration for pycontract.

Set ``pycontract.config.enabled = False`` (or call ``disable()``) to
zero-cost skip all checks — useful in production.

Example::

    import pycontract
    pycontract.disable()   # turn off
    pycontract.enable()    # turn back on

    import pycontract.config as cfg
    cfg.disable()
    cfg.enabled            # False
"""

enabled: bool = True


def disable() -> None:
    """Disable all contract checks globally."""
    global enabled
    enabled = False


def enable() -> None:
    """Re-enable all contract checks globally."""
    global enabled
    enabled = True


__all__ = ["enabled", "enable", "disable"]
