"""Generate HTML5 documents directly from Python code."""

from importlib.metadata import version

__all__ = "Builder", "Document", "E", "HTML"
__version__ = version("html5tagger")

from . import builder, document, makebuilder, util
from .builder import Builder
from .document import Document
from .makebuilder import E
from .util import HTML
