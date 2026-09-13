import gzip
import xml.etree.ElementTree as ET
from pathlib import Path


def read_bytes(path):
    raw = Path(path).read_bytes()
    return gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw


def load(path):
    return ET.fromstring(read_bytes(path))


def decompress_app(src, dst):
    Path(dst).write_bytes(read_bytes(src))
