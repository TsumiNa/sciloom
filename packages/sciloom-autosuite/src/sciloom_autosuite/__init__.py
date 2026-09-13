"""AutoSuite target backend."""

from .agitation import AutoSuiteIndividualShaker
from .target import AutoSuiteTarget
from .xml import AutoSuiteVersion

__all__ = ["AutoSuiteTarget", "AutoSuiteVersion", "AutoSuiteIndividualShaker"]
