from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from .builder import Builder
from .util import HTML


def Document(
    *title,
    _urls: Iterable[str] | None = None,
    _viewport: bool | str = False,
    **html_attrs,
) -> Builder:
    """Construct a new document with a DOCTYPE and minimal structure.

    The html tag is added if any attributes are provided for it.
    If a title is provided, meta charset and title element are added in head.

    E.g. Document("Page title", lang="en") produces a valid document, whereas
    Document() produces only a DOCTYPE declaration.

    Stylesheets, scripts and favicon passed in _urls will be linked in.

    Meta viewport may be added to disable device scaling (True) or using a
    custom string value for any other setting."""
    doc = Builder("Document Builder")(HTML("<!DOCTYPE html>"))
    if html_attrs:
        doc.html(**html_attrs)
    if title:
        doc.meta(charset="utf-8")  # Always a good idea
        doc.title(*title)
    if _viewport:
        if _viewport is True:
            _viewport = "width=device-width,initial-scale=1"
        doc.meta(name="viewport", content=_viewport)
    for url in _urls or ():
        fn = url.rsplit("/", 1)[-1]
        ext = fn.rsplit(".", 1)[-1]
        args = linkarg.get(fn) or linkarg.get(ext)
        if args:
            doc.link(href=url, **args)
        elif url.endswith(".js"):
            doc.script(src=url, defer=True)
        elif url.endswith(".mjs"):
            doc.script(src=url, type="module")
        else:
            raise ValueError("Unknown extension in " + fn)
    return doc


# Arguments for link elements by filename/extension
linkarg = {
    "manifest.json": {"rel": "manifest"},
    "css": {"rel": "stylesheet"},
    "png": {"rel": "icon", "type": "image/png"},
    "svg": {"rel": "icon", "type": "image/svg+xml"},
    "ico": {"rel": "icon", "type": "image/x-icon"},
    "webp": {"rel": "icon", "type": "image/webp"},
    "avif": {"rel": "icon", "type": "image/avif"},
}
