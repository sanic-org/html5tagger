import re

from .html5 import omit_endtag
from .util import attributes, esc_script, esc_style, escape, escape_special, mangle

CSS_SELECTOR = re.compile(
    r"(?:#(?P<id>[\w-]+))|(?:\.(?P<class>[\w-]+))|(?:\[(?P<attribute>[\w-]+)(?:=(?P<value>[^\]]*))?\])"
)

# Matches a class attribute already set on a tag string, e.g. class=foo or class="foo bar".
_CLASS_ATTR_RE = re.compile(r' class=(?:"([^"]*)"|\'([^\']*)\'|([^\s>]*))')


class Builder:
    """Builder generates a document with .elemname(attr1="value", ...) syntax.

    Create a HTML5 document by calling Document or by the E shorthand for
    creating empty snippets.

    E.g. Document("page title", lang="en").div(id="main")("Hello World!")
    """

    def __init__(self, name):
        self.name = name
        self._clear()

    def _clear(self):
        self._pieces = []  # Document content
        self._templates = {}  # Template builders
        self._endtag = ""
        self._stack = []

    @property
    def _allpieces(self):
        retval = []
        retval.extend(self._pieces)
        retval.append(self._endtag)
        retval.extend(self._stack[::-1])
        return tuple(retval)

    def _endtag_close(self):
        if self._endtag:
            self._pieces.append(self._endtag)
            self._endtag = ""

    @property
    def brief(self):
        """A shorter output for the repr() of the document."""
        value = str(self)
        if len(value) > 100:
            value = f":{value[:20]} ···"
        elif value:
            value = f":{value}"
        return f"《{self.name}{value}》"

    def __repr__(self):
        ret = "".join([frag.brief if isinstance(frag, Builder) else frag for frag in self._allpieces])
        if len(ret) > 10000:
            ret = f"{ret[:1000]} ··· {ret[-1000:]}"
        return f"《{self.name}》\n{ret}" if len(ret) > 100 else self.brief

    def __str__(self):
        return "".join([str(frag) for frag in self._allpieces])

    _repr_html_ = __html__ = __str__

    def __iter__(self):
        return str(self).__iter__()

    def __getattr__(self, name):
        """Names that don't begin with underscore are HTML tag names or template blocks."""
        if name[0] == "_":
            return object.__getattribute__(self, name)
        # If name is uppercase, it is a Template placeholder
        if name[0].isupper():
            add_to_doc = name.endswith("_")
            if add_to_doc:
                name = name[:-1]
            builder = self._templates.get(name)
            if not builder:
                if not add_to_doc:
                    raise AttributeError(f"Template {name} not found. Use doc.{name}_ to add it to the document.")
                builder = self._templates[name] = Builder(name=name)
            if add_to_doc:
                self._pieces.append(builder)
                return self
            else:
                return builder
        # Otherwise it is a tag
        tagname = mangle(name)
        self._endtag_close()
        self._pieces.append(f"<{tagname}>")
        if tagname not in omit_endtag:
            self._endtag = f"</{tagname}>"
        return self

    def __setattr__(self, name, value):
        if not name[0].isupper():
            return object.__setattr__(self, name, value)
        # Set the value of a Template placeholder
        template = self._templates[name]
        template._clear()
        template(value)

    def __call__(self, *_inner_content, classes=None, **_attrs):
        """Add attributes and content to the current tag, or append to the document."""
        # Template placeholder just added
        if self._pieces and isinstance(self._pieces[-1], Builder):
            assert not _attrs and classes is None, "Cannot add attributes to a template placeholder"
            self._pieces[-1](*_inner_content)
            return self
        # Add attributes and content to the current tag
        if _attrs or classes is not None:
            tag = self._pieces[-1]
            assert tag[0] == "<" and tag[-1] == ">" and not tag.startswith("</"), (
                f"Can only add attrs to opening tags, got {tag!r}"
            )
            if classes is not None:
                extra = classes.split() if isinstance(classes, str) else list(classes)
                base = None
                if "class_" in _attrs:
                    base = str(_attrs.pop("class_"))
                match = _CLASS_ATTR_RE.search(tag)
                if match:
                    if base is None:
                        base = next(g for g in match.groups() if g is not None)
                    tag = tag[: match.start()] + tag[match.end() :]
                if base is None:
                    base = ""
                combined = base.split() + extra
                if combined:
                    _attrs["class_"] = " ".join(combined)
            self._pieces[-1] = f"{tag[:-1]}{attributes(_attrs)}>"
        if _inner_content:
            self._(*_inner_content)
            self._endtag_close()
        return self

    def __getitem__(self, item):
        """Add attributes to the current tag using CSS selector syntax.

        Supports #id, .class and [attribute=value] (or [attribute] for boolean
        attributes). Multiple selectors may be combined in a single string.
        """
        assert isinstance(item, str), "Attribute names must be strings in CSS selector syntax."

        classes = []
        kwargs = {}
        for match in CSS_SELECTOR.finditer(item):
            if match["id"]:
                kwargs["id_"] = match["id"]
            elif match["class"]:
                classes.append(match["class"])
            elif match["attribute"]:
                value = match["value"]
                if value is None:
                    kwargs[match["attribute"]] = True
                else:
                    value = value.strip("\"'")
                    kwargs[match["attribute"]] = value
        if classes:
            kwargs["class_"] = " ".join(classes)
        return self(**kwargs)

    def _(self, *_content):
        """Append new content without closing the current tag."""
        for c in _content:
            if c is None:
                continue
            assert c is not self, "Cannot add document to itself. Use E.elemname for sub snippets."
            # If it is our template, add the Builder, otherwise expand pieces
            if isinstance(c, Builder):
                if c.name in self._templates:
                    self._pieces.append(c)
                else:
                    self._templates.update(c._templates)
                    self._pieces += c._pieces
            # Other type of data, convert to HTML str
            else:
                self._pieces.append(str(c.__html__() if hasattr(c, "__html__") else escape(c)))
        return self

    def _optimize(self):
        """Join adjacent text fragments."""
        print("optimize")
        newfrags = []
        strfrags = []
        for frag in self._pieces:
            if isinstance(frag, str) or frag.name not in self._templates:
                print("str", frag)
                strfrags.append(str(frag))
            else:
                if strfrags:
                    print(strfrags)
                    newfrags.append("".join(strfrags))
                    strfrags = []
                newfrags.append(frag)
        if strfrags:
            newfrags.append("".join(strfrags))
        self._pieces = newfrags

    ## With statement support for nested elements

    def __enter__(self):
        assert self._endtag, "With statement may only be used with non-void elements."
        self._stack.append(self._endtag)
        self._endtag = ""
        return self

    def __exit__(self, w, t, f):
        self._endtag_close()
        self._pieces.append(self._stack.pop())

    ## HTML5 elements and comments special methods

    def _comment(self, text):
        """Add an HTML comment."""
        text = str(text).replace("-->", "‒‒>")
        self._pieces.append(f"<!--{text}-->")
        return self

    def script(self, code: str | None = None, **attrs):
        """Add inline JavaScript correctly escaped."""
        self._endtag_close()
        code = escape_special(esc_script, code) if code else ""
        self._pieces.append(f"<script{attributes(attrs)}>{code}</script>")
        return self

    def style(self, code: str | None = None, **attrs):
        """Add inline CSS correctly escaped."""
        self._endtag_close()
        code = escape_special(esc_style, code) if code else ""
        self._pieces.append(f"<style{attributes(attrs)}>{code}</style>")
        return self

    # compat: until version 1.3.0 underscores had to be used
    _style = style
    _script = script
