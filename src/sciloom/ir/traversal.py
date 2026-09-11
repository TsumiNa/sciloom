"""Walk semantic occurrences with diagnostic paths, without target knowledge."""

from collections.abc import Iterator
from dataclasses import fields, is_dataclass
from typing import Any

from .model import Node


def iter_nodes(value: Any, path: str = "$") -> Iterator[tuple[Node, str]]:
    if isinstance(value, Node):
        yield value, path
    if is_dataclass(value):
        for field in fields(value):
            yield from iter_nodes(getattr(value, field.name), f"{path}.{field.name}")
    elif isinstance(value, tuple):
        for i, item in enumerate(value):
            yield from iter_nodes(item, f"{path}[{i}]")
