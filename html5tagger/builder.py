from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .nullbuilder import _NullBuilder

from .html5 import omit_endtag
from .nullbuilder import NullBuilder
from .util import (
    _OMIT,
    AttributeSlot,
    ClassesAttributeSlot,
    _is_placeholder_builder,
    _placeholder_default,
    attributes,
    esc_script,
    esc_style,
    escape,
    escape_attr_value,
    escape_special,
    mangle,
    render_attributes,
)

CSS_SELECTOR = re.compile(
    r"(?:#(?P<id>[\w-]+))|(?:\.(?P<class>[\w-]+))|(?:\[(?P<attribute>[\w-]+)(?:=(?P<value>[^\]]*))?\])"
)
TAG_ATTR = re.compile(r' class=(?:"([^"]*)"|([^\s>]*))')  # Matches class="..." or class=... in a tag
BACKSLASH_ESC = re.compile(r"\\(.)")


class AttributedTag:
    """An opening tag whose attributes may contain dynamic slots."""

    __slots__ = ("prefix", "segments")

    def __init__(self, prefix: str, segments: list[str | AttributeSlot | ClassesAttributeSlot]):
        self.prefix = prefix
        self.segments = segments

    def __str__(self) -> str:
        return f"{self.prefix}{''.join(str(s) for s in self.segments)}>"

    @property
    def brief(self) -> str:
        """A shorter output for the repr() of the document."""
        value = str(self)
        value = f":{value[:20]} ···" if len(value) > 100 else f":{value}"
        return value


class Builder:
    """Builder generates a document with .elemname(attr1="value", ...) syntax.

    Create a HTML5 document by calling Document or by the E shorthand for
    creating empty snippets.

    E.g. Document("page title", lang="en").div(id="main")("Hello World!")
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._clear()

    def _clear(self) -> None:
        self._pieces: list = []  # Document content
        self._templates: dict[str, Builder] = {}  # Template builders
        self._endtag = ""
        self._stack: list[str] = []
        self._pending_slot: Builder | None = None

    def _set_default(self, *_content) -> None:
        """Set a placeholder's default value.

        ``None``/``False``/no argument produces a sentinel that omits the
        attribute when used as an attribute slot, while keeping content slots
        empty. ``True`` is preserved so attribute slots can render a short
        attribute. Everything else is escaped as usual.
        """
        self._clear()
        if not _content or _content[0] is None or _content[0] is False:
            self._pieces.append(_OMIT)
        elif len(_content) == 1 and isinstance(_content[0], bool):
            self._pieces.append(_content[0])
        else:
            self._(*_content)

    @property
    def _allpieces(self):
        return *self._pieces, self._endtag, *self._stack[::-1]

    def _endtag_close(self) -> None:
        if self._endtag:
            self._pieces.append(self._endtag)
            self._endtag = ""

    @property
    def brief(self) -> str:
        """A shorter output for the repr() of the document."""
        value = str(self)
        if len(value) > 100:
            value = f":{value[:20]} ···"
        elif value:
            value = f":{value}"
        return f"《{self.name}{value}》"

    def __repr__(self) -> str:
        def fmt(frag) -> str:
            if isinstance(frag, Builder):
                return frag.brief
            if isinstance(frag, AttributedTag):
                return frag.brief
            if frag is _OMIT:
                return ""
            return frag

        ret = "".join(fmt(frag) for frag in self._allpieces)
        if len(ret) > 10000:
            ret = f"{ret[:1000]} ··· {ret[-1000:]}"
        return f"《{self.name}》\n{ret}" if len(ret) > 100 else self.brief

    def __str__(self) -> str:
        return "".join([str(frag) for frag in self._allpieces])

    _repr_html_ = __html__ = __str__

    def __iter__(self):
        return str(self).__iter__()

    def __getattr__(self, name: str) -> Builder:
        """Names that don't begin with underscore are HTML tag names or template blocks."""
        if name[0] == "_":
            return object.__getattribute__(self, name)
        # If name is uppercase, it is a Template placeholder.
        if name[0].isupper():
            add_to_doc = name.endswith("_")
            if add_to_doc:
                name = name[:-1]
            builder = self._templates.get(name)
            if not builder:
                builder = self._templates[name] = Builder(name=name)
            if add_to_doc:
                # Main style: doc.Head_ adds the placeholder and returns self.
                self._pending_slot = None
                self._pieces.append(builder)
                return self
            # Templating-redux style: accessing a placeholder inserts it and
            # closes any open tag (e.g. ``doc.span.Tag.br`` == ``<span>Tag</span><br>``).
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

    def __call__(self, *_content, **_attrs) -> Builder:
        """Add attributes and content to the current tag, or append to the document."""
        # Immediate call after a template placeholder access sets default value.
        if self._pending_slot is not None:
            if _attrs:
                raise TypeError("Cannot add attributes to a template placeholder")
            slot = self._pending_slot
            self._pending_slot = None
            slot._set_default(*_content)
            return self

        # Template placeholder just added
        if self._pieces and isinstance(self._pieces[-1], Builder):
            assert not _attrs, "Cannot add attributes to a template placeholder"
            # Calling an uppercase placeholder sets/replaces its default value.
            # Use ._(...) after the placeholder for content that should come after it.
            slot = self._pieces[-1]
            slot._set_default(*_content)
            return self

        self._pending_slot = None
        # Add attributes and content to the current tag
        if _attrs:
            tag = self._pieces[-1]
            assert tag[0] == "<" and tag[-1] == ">" and not tag.startswith("</"), (
                f"Can only add attrs to opening tags, got {tag!r}"
            )
            if (classes := _attrs.get("classes")) is not None:
                if not isinstance(classes, str) and _is_placeholder_builder(classes):
                    # Defer classes= to render time so templates can supply
                    # string/list/dict class specifications dynamically.
                    static_class = _attrs.pop("class_", "")
                    base = static_class.split() if static_class else []
                    if m := TAG_ATTR.search(tag):
                        existing = (g if (g := m.group(1)) is not None else m.group(2)).split()
                        base = existing + base
                        tag = tag[: m.start()] + tag[m.end() : -1] + ">"
                    placeholder = classes._pieces[0]
                    _attrs["classes"] = ClassesAttributeSlot(
                        placeholder.name,
                        base=" ".join(base) or None,
                        default=_placeholder_default(placeholder),
                    )
                else:
                    assert "class_" not in _attrs, "Cannot specify both classes= and class_="
                    if isinstance(classes, str):
                        classes = classes.split()
                    elif isinstance(classes, dict):
                        classes = [k for k, v in classes.items() if v]
                    else:
                        classes = list(classes)
                    if m := TAG_ATTR.search(tag):
                        # Combine with existing class (from earlier [] or ())
                        classes = (g if (g := m.group(1)) is not None else m.group(2)).split() + classes
                        classes = " ".join(classes)
                        tag = tag[: m.start()] + f" class={escape_attr_value(classes)}" + tag[m.end() :]
                        del _attrs["classes"]
                    else:
                        # New attribute, keeping ordering of kwargs
                        _attrs["classes"] = " ".join(classes)
                        _attrs = {"class" if k == "classes" else k: v for k, v in _attrs.items()}
            attr_result = attributes(_attrs)
            if isinstance(attr_result, str):
                self._pieces[-1] = f"{tag[:-1]}{attr_result}>"
            else:
                self._pieces[-1] = AttributedTag(tag[:-1], attr_result)
        if _content:
            self._(*_content)
            self._endtag_close()
        return self

    def __getitem__(self, item: bool | str) -> Builder | _NullBuilder:
        """Add CSS selector attributes, or return NullBuilder for False."""
        if isinstance(item, bool):
            return self if item else NullBuilder

        assert isinstance(item, str), f"CSS selector syntax [] requires a string or bool, got {item!r}."

        tag = self._pieces[-1]
        assert tag[0] == "<" and tag[-1] == ">" and not tag.startswith("</"), (
            f"Can only add attrs to opening tags, got {tag!r}"
        )

        frags = [tag[:-1]]
        class_value_idx = None
        last_end = 0
        for m in CSS_SELECTOR.finditer(item):
            assert m.start() == last_end, f"Invalid CSS selector: {item!r}"
            last_end = m.end()
            if m["id"]:
                value = escape_attr_value(m["id"])
                frags.extend([" id=", value])
            elif m["class"]:
                if class_value_idx is None:
                    class_value_idx = len(frags) + 1
                    frags += " class=", m["class"]
                else:
                    frags[class_value_idx] = f"{frags[class_value_idx]} {m['class']}"
            else:
                attr = m["attribute"]
                value = m["value"]
                if value is None:
                    frags += " ", attr
                else:
                    # Unquote and unescape CSS selector value
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                        value = value[1:-1]
                    value = BACKSLASH_ESC.sub(r"\1", value)
                    frags += " ", attr, "=", escape_attr_value(value)
        assert last_end == len(item), f"Invalid CSS selector: {item!r}"
        if class_value_idx is not None:
            base = None
            if m := TAG_ATTR.search(tag):  # type: ignore[assignment]
                base = g if (g := m.group(1)) is not None else m.group(2)
                frags[0] = tag[: m.start()] + tag[m.end() : -1]  # Remove class attribute and >
                frags[class_value_idx] = f"{base} {frags[class_value_idx]}"
            frags[class_value_idx] = escape_attr_value(frags[class_value_idx])
        frags.append(">")
        self._pieces[-1] = "".join(frags)
        return self

    def _(self, *_content) -> Builder:
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

    def __enter__(self) -> Builder:
        assert self._endtag, "With statement may only be used with non-void elements."
        self._stack.append(self._endtag)
        self._endtag = ""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._endtag_close()
        self._pieces.append(self._stack.pop())

    ## HTML5 elements and comments special methods

    def _comment(self, text) -> Builder:
        """Add an HTML comment."""
        text = str(text).replace("-->", "‒‒>")
        self._pieces.append(f"<!--{text}-->")
        return self

    def script(self, code: str | None = None, **attrs) -> Builder:
        """Add inline JavaScript correctly escaped."""
        self._endtag_close()
        code = escape_special(esc_script, code) if code else ""
        self._pieces.append(f"<script{render_attributes(attributes(attrs))}>{code}</script>")
        return self

    def style(self, code: str | None = None, **attrs) -> Builder:
        """Add inline CSS correctly escaped."""
        self._endtag_close()
        code = escape_special(esc_style, code) if code else ""
        self._pieces.append(f"<style{render_attributes(attributes(attrs))}>{code}</style>")
        return self

    # compat: until version 1.3.0 underscores had to be used
    _style = style
    _script = script
