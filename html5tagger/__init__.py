"""Generate HTML5 documents directly in Python."""

from __future__ import annotations

from importlib.metadata import version

__all__ = "Builder", "Document", "E", "HTML", "Template"
__version__ = version("html5tagger")

from . import builder, document, makebuilder, util
from .builder import Builder
from .document import Document
from .makebuilder import E
from .template import Template
from .util import HTML
