"""Explicit file adapters isolate memory state and contain local paths."""

import pytest

from .files import LocalFiles, MemoryFiles


def test_memory_files_copy_inputs_and_return_immutable_detached_snapshots():
    initial = {"recipe.csv": b"A,1\n"}
    files = MemoryFiles(initial)
    initial["recipe.csv"] = b"changed"
    before = files.snapshot()
    files.append_bytes("recipe.csv", b"B,2\n")
    files.append_bytes("new.csv", b"first\n")
    assert files.read_bytes("recipe.csv") == b"A,1\nB,2\n"
    assert before == {"recipe.csv": b"A,1\n"}
    with pytest.raises(TypeError):
        before["recipe.csv"] = b"wrong"
    with pytest.raises(FileNotFoundError):
        MemoryFiles().read_bytes("recipe.csv")


@pytest.mark.parametrize("path", ["", "bad\x00path", None, 1])
def test_both_adapters_reject_invalid_paths_before_access(path, tmp_path):
    for files in (MemoryFiles(), LocalFiles(tmp_path)):
        for operation in (lambda: files.read_bytes(path), lambda: files.append_bytes(path, b"data")):
            with pytest.raises((TypeError, ValueError)):
                operation()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("value", ["text", bytearray(b"bytes"), None])
def test_mutable_or_nonbyte_payloads_are_rejected(value, tmp_path):
    with pytest.raises(TypeError):
        MemoryFiles({"recipe": value})
    for files in (MemoryFiles(), LocalFiles(tmp_path)):
        with pytest.raises(TypeError):
            files.append_bytes("recipe", value)
        with pytest.raises(FileNotFoundError):
            files.read_bytes("recipe")


def test_local_files_require_an_existing_root_and_never_create_parents(tmp_path):
    with pytest.raises(FileNotFoundError):
        LocalFiles(tmp_path / "missing")
    file = tmp_path / "file"
    file.write_bytes(b"value")
    with pytest.raises(NotADirectoryError):
        LocalFiles(file)
    files = LocalFiles(tmp_path)
    assert files.read_bytes("file") == b"value"
    files.append_bytes("file", b" next")
    files.append_bytes("created", b"new")
    assert files.read_bytes("file") == b"value next"
    assert files.read_bytes("created") == b"new"
    with pytest.raises(FileNotFoundError):
        files.append_bytes("missing/child", b"never")
    assert not (tmp_path / "missing").exists()


def test_local_files_reject_absolute_traversal_and_symlink_escapes(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    evidence = outside / "file"
    evidence.write_bytes(b"unchanged")
    (root / "linked_file").symlink_to(evidence)
    (root / "linked_dir").symlink_to(outside, target_is_directory=True)
    files = LocalFiles(root)
    for path in (str(evidence), "../outside/file", "linked_file", "linked_dir/new"):
        with pytest.raises(ValueError, match="root"):
            files.read_bytes(path)
        with pytest.raises(ValueError, match="root"):
            files.append_bytes(path, b"forbidden")
    assert evidence.read_bytes() == b"unchanged"
    assert not (outside / "new").exists()
