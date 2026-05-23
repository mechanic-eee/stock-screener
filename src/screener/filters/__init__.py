"""Importing this package registers every filter."""
from . import base
from .base import all_filters, base_filters, get, optional_filters, register

base.load_all()

__all__ = ["all_filters", "base_filters", "optional_filters", "get", "register"]
