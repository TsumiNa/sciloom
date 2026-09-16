"""Explicit byte services; CSV parsing and error policies belong to operations."""

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Protocol


class FileService(Protocol):
    """Provide bytes without selecting a filesystem implicitly."""

    def read_bytes(self, path: str) -> bytes:
        """Read one file, raising OSError for an I/O failure."""
        ...

    def append_bytes(self, path: str, data: bytes) -> None:
        """Append bytes; an error does not promise to roll back earlier writes."""
        ...


def _validate_path(path: str) -> None:
    if type(path) is not str:
        raise TypeError("File paths must be text.")
    if not path or "\x00" in path:
        raise ValueError("File paths must be nonempty and contain no NUL characters.")


class MemoryFiles:
    """Independent in-memory files with opaque path keys and immutable byte values.

    Args:
        initial: Optional mapping copied at construction.

    Raises:
        TypeError: A path is not text or a value is not immutable bytes.
        ValueError: A path is empty or contains NUL.
    """

    def __init__(self, initial: Mapping[str, bytes] | None = None) -> None:
        self._files: dict[str, bytes] = {}
        if initial is not None:
            for path, data in initial.items():
                _validate_path(path)
                if type(data) is not bytes:
                    raise TypeError("File contents must be immutable bytes.")
                self._files[path] = data

    def read_bytes(self, path: str) -> bytes:
        """Return stored bytes, raising FileNotFoundError for a missing key."""
        _validate_path(path)
        try:
            return self._files[path]
        except KeyError:
            raise FileNotFoundError(path) from None

    def append_bytes(self, path: str, data: bytes) -> None:
        """Append bytes to one key, creating it if absent.

        Args:
            path: Nonempty opaque path key.
            data: Immutable bytes to append.

        Raises:
            TypeError: The payload is not bytes or the path is not text.
            ValueError: The path is empty or contains NUL.
        """
        _validate_path(path)
        if type(data) is not bytes:
            raise TypeError("File contents must be immutable bytes.")
        self._files[path] = self._files.get(path, b"") + data

    def snapshot(self) -> Mapping[str, bytes]:
        """Return a detached read-only mapping, unaffected by later appends."""
        return MappingProxyType(self._files.copy())


class LocalFiles:
    """Opt-in byte access within an existing local directory.

    Args:
        root: Existing directory used to resolve operation-relative paths.

    Raises:
        OSError: The root is unavailable or is not a directory.

    Absolute paths and resolved traversal/symlink escapes are rejected before
    access. This adapter is not a security sandbox against concurrent filesystem
    changes and provides no transaction or rollback guarantee.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve(strict=True)
        if not self._root.is_dir():
            raise NotADirectoryError(self._root)

    def _resolve(self, path: str) -> Path:
        _validate_path(path)
        requested = Path(path)
        if requested.is_absolute():
            raise ValueError("Local file paths must be relative to the configured root.")
        resolved = (self._root / requested).resolve()
        if not resolved.is_relative_to(self._root):
            raise ValueError("Local file path escapes the configured root.")
        return resolved

    def read_bytes(self, path: str) -> bytes:
        """Read a contained relative path; OS failures remain OSError.

        Raises:
            TypeError: The path is not text.
            ValueError: The path is invalid, absolute or escapes the root.
            OSError: The file cannot be read.
        """
        return self._resolve(path).read_bytes()

    def append_bytes(self, path: str, data: bytes) -> None:
        """Append bytes without creating parent directories or rolling back errors.

        Raises:
            TypeError: The payload is not bytes or the path is not text.
            ValueError: The path is invalid, absolute or escapes the root.
            OSError: The file cannot be opened or written.
        """
        if type(data) is not bytes:
            raise TypeError("File contents must be immutable bytes.")
        with self._resolve(path).open("ab") as stream:
            stream.write(data)
