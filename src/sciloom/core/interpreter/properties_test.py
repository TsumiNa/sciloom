"""Stored metadata is copied, validated before mutation and explicitly shared."""

import pytest

from .properties import WellProperties


def test_copy_snapshot_and_whole_write_validation():
    source = {("rack/1", "sample_ID"): "A"}
    store = WellProperties(source)
    source[("rack/1", "sample_ID")] = "changed"
    old = store.snapshot()
    store.set(("rack/1", "rack/2"), "sample_ID", "B")
    assert old == {("rack/1", "sample_ID"): "A"}
    assert store.get("rack/2", "sample_ID") == "B"
    with pytest.raises(TypeError):
        old[("rack/1", "sample_ID")] = "bad"
    before = store.snapshot()
    with pytest.raises(ValueError):
        store.set(("rack/1", ""), "sample_ID", "bad")
    assert store.snapshot() == before
    store.set((), "sample_ID", "unused")
    assert store.snapshot() == before
    with pytest.raises(KeyError):
        WellProperties().get("rack/1", "sample_ID")


@pytest.mark.parametrize("initial", [{("a", "x"): 3}, {("", "x"): "a"}, {("a", ""): "a"}, {"ax": "a"}])
def test_invalid_initial_metadata(initial):
    with pytest.raises((TypeError, ValueError)):
        WellProperties(initial)
