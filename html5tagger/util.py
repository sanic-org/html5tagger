import re


class HTML(str):
    """A HTML string that will not be escaped."""

    __html__ = _repr_html_ = str.__str__

    def __repr__(self):
        return f"HTML({super().__repr__()})"


def escape(text):
    return HTML(str(text).replace("&", "&amp;").replace("<", "&lt;"))


# Inline styles and scripts only escape the specific end tag
esc_style = re.compile("</(style>)", re.IGNORECASE)
esc_script = re.compile("</(script>)", re.IGNORECASE)


def escape_special(tag: re.Pattern[str], text):
    return HTML(tag.sub(r"<\\/\1", text))


def escape_attr_value(value: str):
    return value if value.isalnum() else f'''"{value.replace("&", "&amp;").replace('"', "&quot;")}"'''


def attributes(attrs):
    ret = ""
    for k, v in attrs.items():
        k = mangle(k)
        if v is None or v is False:
            continue
        ret += " " + k
        if v is True:
            continue  # Short attribute
        v = escape_attr_value(f"{v}")
        ret += "=" + v
    return ret


def mangle(name):
    """Mangle Python identifiers into HTML tag/attribute names.

    Underscores are converted into hyphens. Underscore at end is removed."""
    return name.rstrip("_").replace("_", "-")
