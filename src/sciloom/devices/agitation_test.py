"""Device author imports do not load source analysis or a vendor target."""

import subprocess
import sys


def test_device_import_is_independent_of_source_and_targets():
    subprocess.run(
        [sys.executable, "-c", """
import sys
class Block:
    def find_spec(self, fullname, *args):
        if fullname.startswith(("sciloom.dsl", "sciloom.contrib")):
            raise ImportError("Device contracts cannot load source or targets")
sys.meta_path.insert(0, Block())
from sciloom import Agitator
from sciloom.devices import Agitator as DeviceAgitator
assert Agitator is DeviceAgitator
assert Agitator("mixer").resource_id == "mixer"
"""],
        check=True,
    )
