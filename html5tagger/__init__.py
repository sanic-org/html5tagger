"""Generate HTML5 documents directly from Python code."""

__all__ = "Document", "E", "HTML"
__version__ = "1.0.1"

class HTML(str):
    """A HTML string that will not be escaped."""

    __html__ = _repr_html_ = str.__str__

    def __repr__(self):
        return f"HTML({super().__repr__()})"


def escape(text):
    text = str(text)
    for rep in [
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
    ]:
        text = text.replace(*rep)
    return HTML(text)


def attributes(attrs):
    ret = ""
    for k, v in attrs.items():
        k = mangle(k)
        if v is None or v is False:
            continue
        ret += " " + k
        if v is True:
            continue  # Short attribute
        v = str(v)
        if not v.isalnum():
            v = '"' + v.replace("&", "&amp;").replace('"', "&quot;") + '"'
        ret += "=" + v
    return ret


def mangle(name):
    """Mangle Python identifiers into HTML tag/attribute names.

    Underscores are converted into hyphens. Underscore at end is removed."""
    return name.rstrip("_").replace("_", "-")


omit_endtag = {
    # Void elements:
    "area",
    "base",
    "br",
    "col",
    "emdeb",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "menuitem",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
    # End tag optional:
    "html",
    "head",
    "body",
    "p",
    "colgroup",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "li",
    "dt",
    "dd",
    "optgroup",
    "option",
}


class Builder:
    """Builder generates a document with .elemname(attr1="value", ...) syntax.

    Create a HTML5 document by calling Document or by the E shorthand for
    creating empty snippets.

    E.g. Document("page title", lang="en").div(id="main")("Hello World!")
    """

    def __init__(self):
        self._fragments = {}
        self._html = ""
        self._endtag = ""
        self._stack = []

    def __str__(self):
        ret = ""
        for n, (fhtml, builder) in self._fragments.items():
            ret += fhtml
            if builder:
                ret += builder.__html__()
        return HTML(ret + self._html + self._endtag)

    __html__ = _repr_html_ = __str__

    def __iter__(self):
        return str(self).__iter__()

    def __getattr__(self, name):
        """Names that don't begin with underscore are HTML tag names or template blocks."""
        if name[0] == "_":
            return object.__getattr__(self, name)
        self._html += self._endtag
        self._endtag = ""
        if name[0].isupper():
            if name in self._fragments:
                return self._fragments[name][1]
            self._fragments[name] = [self._html, Builder()]
            self._html = ""
            return self
        tagname = mangle(name)
        self._html += "<" + tagname + ">"
        if not tagname in omit_endtag:
            self._endtag = "</" + tagname + ">"
        return self

    def __setattr__(self, name, value):
        if not name[0].isupper():
            return object.__setattr__(self, name, value)
        self._fragments[name][1] = value

    def __call__(self, *_inner_content, **_attrs):
        if _attrs:
            assert self._html[-1:] == ">", "Attributes may only be added to tags"
            # Note: No protection against adding attrs to end tags!
            self._html = self._html[:-1] + attributes(_attrs) + ">"
        if _inner_content:
            self._(*_inner_content)
            if self._endtag:
                self._html += self._endtag
                self._endtag = ""
        return self

    def _(self, *_content):
        """Add new content."""
        for c in _content:
            if c is None:
                continue
            assert (
                c is not self
            ), "Cannot add document to itself. Use E.elemname for subelements."
            if isinstance(c, Builder) and c._fragments:
                if self._html:
                    self._fragments[id(self._html)] = [self._html, None]
                self._fragments.update(c._fragments)
                self._html = c._html + c._endtag
            else:
                self._html += c.__html__() if hasattr(c, "__html__") else escape(c)
        return self

    def _comment(self, text):
        self._html += "<!--" + str(text).replace("-->", "--&gt;") + "-->"
        return self

    def __enter__(self):
        assert self._endtag, "With statement may only be used with non-void elements."
        self._stack.append(self._endtag)
        self._endtag = ""
        return self

    def __exit__(self, w, t, f):
        self._html += self._endtag + self._stack.pop()
        self._endtag = ""

    def __iadd__(self, builder):
        assert isinstance(
            builder, Builder
        ), "Only Builders may be added. Use () for content."
        self._html += builder.__html__()


def Document(*title, _urls=None, **html_attrs):
    """Construct a new document with a DOCTYPE and minimal structure.

    The html tag is added if any attributes are provided for it.
    If a title is provided, meta charset and title element are added in head.

    E.g. Document("Page title", lang="en") produces a valid document, whereas
    Document() produces only a DOCTYPE declaration.

    Stylesheets, scripts and favicon passed in _urls will be linked in."""
    doc = Builder()(HTML("<!DOCTYPE html>"))
    if html_attrs:
        doc.html(**html_attrs)
    if title:
        doc.meta(charset="utf-8")  # Always a good idea
        doc.title(*title)
    for url in _urls or ():
        if url.endswith(".js"):
            doc.script(None, src=url)
        elif url.endswith(".css"):
            doc.link(rel="stylesheet", href=url)
        elif url.endswith(".ico"):
            doc.link(rel="icon", href=url, type="image/x-icon")
        elif url.endswith(".svg"):
            doc.link(rel="icon", href=url, type="image/svg+xml")
        elif url.endswith(".png"):
            doc.link(rel="icon", href=url, type="image/png")
        elif url.endswith(".webp"):
            doc.link(rel="icon", href=url, type="image/webp")
        elif url.endswith("manifest.json"):
            doc.link(rel="manifest", href=url)
        else:
            raise ValueError("Unknown extension in " + url)
    return doc


class MakeBuilder:
    """Use E.elemname or E(content) to create initially empty snippets."""

    def __getattr__(self, name):
        return getattr(Builder(), name)

    def __call__(self, *args, **kwargs):
        return Builder()(*args, **kwargs)


E = MakeBuilder()
