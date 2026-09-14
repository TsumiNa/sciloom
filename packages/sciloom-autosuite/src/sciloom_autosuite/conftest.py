"""Gate the tests that compare generated XML against the shared AutoSuite corpus.

The corpus is shared inside the team and is not in git, so a checkout may not
have it. Mark such a test with `@requires_corpus`; everything that only needs
this distribution keeps running. See autosuite/README.md.
"""

from pathlib import Path

import pytest

# The corpus sits at the workspace root, outside this distribution.
CORPUS = Path(__file__).resolve().parents[4] / "autosuite/corpus"

requires_corpus = pytest.mark.skipif(
    not CORPUS.is_dir(),
    reason="AutoSuite corpus is not present in this checkout; see autosuite/README.md",
)
