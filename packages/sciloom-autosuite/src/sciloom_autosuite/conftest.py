"""Reach the shared AutoSuite corpus, skipping when a file is not in this checkout.

The corpus is shared inside the team and is not in git, and developers keep only
the files their own work needed. A test therefore names the evidence it reads and
skips on that file, not on the directory. See autosuite/README.md.
"""

from pathlib import Path

import pytest

# The corpus sits at the workspace root, outside this distribution.
CORPUS = Path(__file__).resolve().parents[4] / "autosuite/corpus"


def corpus_file(relative: str) -> Path:
    """Return an evidence file, skipping the calling test when it is absent."""
    path = CORPUS / relative
    if not path.is_file():
        pytest.skip(f"AutoSuite corpus file is not in this checkout: {relative}; see autosuite/README.md")
    return path
