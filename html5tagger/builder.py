from __future__ import annotations

from typing import TYPE_CHECKING

from .html5 import omit_endtag
from .util import attributes, esc_script, esc_style, escape, escape_special, mangle

if TYPE_CHECKING:
    from .template import Template


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
        self._pending_slot = None

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

    def __matmul__(self, other: type[Template]) -> Template:
        """Support ``builder @ Template`` to create a Template."""
        # Avoid a circular import at module load time.
        from .template import Template

        if other is Template:
            return Template(self)
        return NotImplemented

    def __getattr__(self, name):
        """Names that don't begin with underscore are HTML tag names or template blocks."""
        if name[0] == "_":
            return object.__getattribute__(self, name)
        # If name is uppercase, it is a Template placeholder.
        # Uppercase names always insert the placeholder.
        # If a tag is currently open, the placeholder becomes its content and
        # the tag is closed (e.g. ``doc.span.Tag.br`` == ``<span>Tag</span><br>``).
        if name[0].isupper():
            builder = self._templates.get(name)
            if not builder:
                builder = self._templates[name] = Builder(name=name)
            self._pending_slot = builder
            self._pieces.append(builder)
            self._endtag_close()
            return self
        # Otherwise it is a tag
        self._pending_slot = None
        tagname = mangle(name)
        self._endtag_close()
        self._pieces.append(f"<{tagname}>")
        if tagname not in omit_endtag:
            self._endtag = f"</{tagname}>"
        return self

    def __call__(self, *_inner_content, **_attrs):
        """Add attributes and content to the current tag, or append to the document."""
        # Immediate call after a template placeholder access sets default value.
        if self._pending_slot is not None:
            if _attrs:
                raise TypeError("Cannot add attributes to a template placeholder")
            slot = self._pending_slot
            self._pending_slot = None
            slot._clear()
            slot._(*_inner_content)
            return self

        # Template placeholder just added
        if self._pieces and isinstance(self._pieces[-1], Builder):
            if _attrs:
                raise TypeError("Cannot add attributes to a template placeholder")
            # Calling an uppercase placeholder sets/replaces its default value.
            # Use ._(...) after the placeholder for content that should come after it.
            slot = self._pieces[-1]
            slot._clear()
            slot._(*_inner_content)
            return self

        self._pending_slot = None
        # Add attributes and content to the current tag
        if _attrs:
            tag = self._pieces[-1]
            assert tag[0] == "<" and tag[-1] == ">" and not tag.startswith("</"), (
                f"Can only add attrs to opening tags, got {tag!r}"
            )
            self._pieces[-1] = f"{tag[:-1]}{attributes(_attrs)}>"
        if _inner_content:
            self._(*_inner_content)
            self._endtag_close()
        return self

    def _(self, *_content):
        """Append new content without closing the current tag."""
        self._pending_slot = None
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
