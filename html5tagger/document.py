from .builder import Builder
from .util import HTML


def Document(*title, _urls=None, **html_attrs) -> Builder:
    """Construct a new document with a DOCTYPE and minimal structure.

    The html tag is added if any attributes are provided for it.
    If a title is provided, meta charset and title element are added in head.

    E.g. Document("Page title", lang="en") produces a valid document, whereas
    Document() produces only a DOCTYPE declaration.

    Stylesheets, scripts and favicon passed in _urls will be linked in."""
    doc = Builder("Document Builder")(HTML("<!DOCTYPE html>"))
    if html_attrs:
        doc.html(**html_attrs)
    if title:
        doc.meta(charset="utf-8")  # Always a good idea
        doc.title(*title)
    for url in _urls or ():
        fn = url.rsplit("/", 1)[-1]
        ext = fn.rsplit(".", 1)[-1]
        args = linkarg.get(fn) or linkarg.get(ext)
        if args:
            doc.link(href=url, **args)
        elif url.endswith(".js"):
            doc.script(None, src=url)
        else:
            raise ValueError("Unknown extension in " + fn)
    return doc

# Arguments for link elements by filename/extension
linkarg = {
    "manifest.json": dict(rel="manifest"),
    "css": dict(rel="stylesheet"),
    "png": dict(rel="icon", type="image/png"),
    "svg": dict(rel="icon", type="image/svg+xml"),
    "ico": dict(rel="icon", type="image/x-icon"),
    "webp": dict(rel="icon", type="image/webp"),
    "avif": dict(rel="icon", type="image/avif"),
}
