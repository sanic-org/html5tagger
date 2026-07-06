import re


class _OmitAttribute:
    """Sentinel for an attribute-slot default that should omit the attribute."""

    def __str__(self):
        return ""

    def __repr__(self):
        return "_OMIT"


_OMIT = _OmitAttribute()


class HTML(str):
    """A HTML string that will not be escaped."""

    __html__ = _repr_html_ = str.__str__

    def __repr__(self):
        return f"HTML({super().__repr__()})"


def escape(text):
    return HTML(str(text).replace("&", "&amp;").replace("<", "&lt;"))


def _attr_value(value):
    """Render an attribute value, including the leading '=' and optional quotes."""
    v = str(value)
    if v.isalnum():
        return "=" + v
    return '="' + v.replace("&", "&amp;").replace('"', "&quot;") + '"'


def _render_attr(attr: str, value) -> str:
    """Render a single attribute (name + value) like attributes() would.

    Supports True (short attribute), None/False (omit), and normal values.
    The leading space is included so the attribute can be dropped entirely
    when the value is None or False.
    """
    if value is None or value is False:
        return ""
    if value is True:
        return " " + attr
    if hasattr(value, "__html__"):
        v = str(value.__html__())
        if v.isalnum():
            return " " + attr + "=" + v
        return " " + attr + '="' + v.replace('"', "&quot;") + '"'
    v = str(value)
    if v.isalnum():
        return " " + attr + "=" + v
    return " " + attr + '="' + v.replace("&", "&amp;").replace('"', "&quot;") + '"'


class AttributeSlot:
    """Marker for an attribute value placeholder inside a Builder."""

    __slots__ = ("name", "attr", "default")

    def __init__(self, name: str, attr: str, default=""):
        self.name = name
        self.attr = attr
        self.default = default

    def __str__(self):
        return _render_attr(self.attr, self.default)

    def __repr__(self):
        return f"AttributeSlot({self.name!r}, {self.attr!r})"


# Inline styles and scripts only escape the specific end tag
esc_style = re.compile("</(style>)", re.IGNORECASE)
esc_script = re.compile("</(script>)", re.IGNORECASE)


def escape_special(tag: re.Pattern[str], text):
    return HTML(tag.sub(r"<\\/\1", text))


def _is_placeholder_builder(value):
    """Detect a Builder that contains only a single uppercase placeholder."""
    pieces = getattr(value, "_pieces", None)
    if not pieces or len(pieces) != 1:
        return False
    placeholder = pieces[0]
    name = getattr(placeholder, "name", "")
    return isinstance(name, str) and name and name[0].isupper()


def _placeholder_default(placeholder) -> object:
    """Extract the default value from a placeholder builder for attribute slots."""
    pieces = getattr(placeholder, "_pieces", None)
    if not pieces:
        return None
    if len(pieces) == 1:
        if pieces[0] is _OMIT or pieces[0] is None or pieces[0] is False:
            return None
        if isinstance(pieces[0], bool):
            return pieces[0]
    return HTML(str(placeholder))


def attributes(attrs):
    ret = ""
    for k, v in attrs.items():
        k = mangle(k)
        if v is None or v is False:
            continue
        if not isinstance(v, str) and _is_placeholder_builder(v):
            # Switch to list mode so the Builder/Template can preserve the slot.
            segments: list[str | AttributeSlot] = [ret] if ret else []
            placeholder = v._pieces[0]
            segments.append(AttributeSlot(placeholder.name, k, default=_placeholder_default(placeholder)))
            return _attributes_with_slots(attrs, k, segments)
        ret += " " + k
        if v is True:
            continue  # Short attribute
        ret += _attr_value(v)
    return ret


def _attributes_with_slots(attrs, current_key, segments):
    """Continue processing attrs after the first slot was found at current_key."""
    skip = True
    for k, v in attrs.items():
        if skip:
            if k == current_key:
                skip = False
            continue
        k = mangle(k)
        if v is None or v is False:
            continue
        if not isinstance(v, str) and _is_placeholder_builder(v):
            placeholder = v._pieces[0]
            segments.append(AttributeSlot(placeholder.name, k, default=_placeholder_default(placeholder)))
            continue
        segments.append(" " + k)
        if v is True:
            continue
        segments.append(_attr_value(v))
    return segments


def render_attributes(attr_result):
    """Render the result of attributes() to a plain string for non-template contexts."""
    if isinstance(attr_result, str):
        return attr_result
    return "".join(str(seg) if isinstance(seg, AttributeSlot) else seg for seg in attr_result)


def mangle(name):
    """Mangle Python identifiers into HTML tag/attribute names.

    Underscores are converted into hyphens. Underscore at end is removed."""
    return name.rstrip("_").replace("_", "-")
