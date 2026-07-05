from .util import HTML, escape


class Slot:
    """A named hole inside a Template."""

    __slots__ = ("name", "default")

    def __init__(self, name: str, default: str = ""):
        self.name = name
        self.default = default

    def __repr__(self):
        return f"Slot({self.name!r})"


class Template:
    """A read-only, callable HTML template.

    Define a template by wrapping a Builder. Uppercase placeholders inside the
    builder become named slots. Calling the template with keyword arguments
    fills the slots, escapes the values, and returns an HTML string.

    The template object never stores the values passed to it; they are used
    once during the call and then discarded.

    A template can be created explicitly::

        Item = Template(E.li.Name(""))

    or with the ``@`` operator::

        Item = E.li.Name("") @ Template
    """

    __slots__ = ("_fragments",)

    def __init__(self, builder):
        from .builder import Builder

        if not isinstance(builder, Builder):
            raise TypeError("Template expects a Builder instance")
        self._fragments = tuple(self._flatten(builder, builder._templates))

    @staticmethod
    def _flatten(builder, templates):
        """Convert a Builder into a flat list of strings and Slots."""
        fragments: list[str | Slot] = []
        buffer: list[str] = []

        def flush():
            if buffer:
                fragments.append("".join(buffer))
                buffer.clear()

        for piece in builder._allpieces:
            if isinstance(piece, str):
                buffer.append(piece)
            else:
                # piece is a Builder
                if piece.name in templates:
                    flush()
                    default = str(piece)
                    fragments.append(Slot(piece.name, default))
                else:
                    # Nested, non-slot builder: render once now.
                    buffer.append(str(piece))
        flush()
        return fragments

    def __call__(self, **values):
        """Render the template with the supplied slot values."""
        parts = []
        for fragment in self._fragments:
            if isinstance(fragment, str):
                parts.append(fragment)
            else:
                value = values.get(fragment.name, fragment.default)
                parts.append(self._render_value(value))
        return HTML("".join(parts))

    @staticmethod
    def _render_value(value):
        if value is None:
            return ""
        if hasattr(value, "__html__"):
            return str(value.__html__())
        if isinstance(value, (str, bytes, bytearray)):
            return str(escape(value))
        if hasattr(value, "__iter__"):
            return "".join(Template._render_value(v) for v in value)
        return str(escape(value))

    def __repr__(self):
        return f"Template({self._fragments!r})"
