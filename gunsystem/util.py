def to_int(value, default: int | None) -> int | None:
    """value as an int, or default when it is not one."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
