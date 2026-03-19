"""
contractual.config
=================
Runtime configuration for contractual.

Set ``contractual.config.enabled = False`` (or call ``disable()``) to
zero-cost skip all checks — useful in production.

Example::

    import contractual
    contractual.disable()   # turn off
    contractual.enable()    # turn back on

    import contractual.config as cfg
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
