"""Unknown directives must not inherit host strftime extensions or locale rules."""

import pytest

from .time_format import validate_wall_time_format


@pytest.mark.parametrize("format", ["", "literal 試料", "%Y-%m-%d_%H%M%S", "%%Y", "%%%Y", "%%%%"])
def test_portable_formats(format):
    validate_wall_time_format(format)


@pytest.mark.parametrize("format", ["%", "%Y%", "%f", "%z", "%Z", "%x", "%-m", "%Q", "%\n"])
def test_unknown_or_incomplete_directives(format):
    with pytest.raises(ValueError):
        validate_wall_time_format(format)
