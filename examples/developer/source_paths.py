"""For SciLoom developers: keep generated JSON companions checkout-independent.

Lowering records the absolute path of the Python file that defines a runtime
method, so serialized IR would otherwise embed the path of whichever checkout
produced it. The developer examples commit their JSON output as learning
material, so they rewrite those diagnostic paths relative to the repository
root before writing a file. Diagnostics raised at runtime keep absolute paths.

This module is a helper for the examples, not part of the SciLoom API.
"""

from pathlib import Path
from typing import Any

from sciloom.core.ir import Program, from_dict, to_dict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def repository_relative(program: Program) -> Program:
    """Return an equivalent program whose SourceSpan paths are repository-relative.

    Args:
        program: Validated program carrying absolute source paths.

    Returns:
        A program identical except for source paths inside the repository, which
        become forward-slash relative paths such as `examples/agitation.py`.

    Raises:
        IRValidationError: The program or the rewritten document fails validation.
    """

    def relative(path: str) -> str:
        location = Path(path)
        if location.is_absolute() and location.is_relative_to(REPOSITORY_ROOT):
            return location.relative_to(REPOSITORY_ROOT).as_posix()
        return path

    def rewrite(node: Any) -> Any:
        if isinstance(node, dict):
            converted = {key: rewrite(value) for key, value in node.items()}
            source = converted.get("source")
            if isinstance(source, dict) and isinstance(source.get("path"), str):
                source["path"] = relative(source["path"])
            return converted
        if isinstance(node, list):
            return [rewrite(item) for item in node]
        return node

    return from_dict(rewrite(to_dict(program)))
