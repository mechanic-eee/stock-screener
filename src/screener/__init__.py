"""stock-screener: drawdown-based stock screener with pluggable filters."""
from . import filters  # noqa: F401  (registers all filters on import)

__all__ = ["filters"]
