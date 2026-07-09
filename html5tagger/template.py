from __future__ import annotations

from typing import TYPE_CHECKING

from .util import HTML, ClassesAttributeSlot, _render_attr, escape

if TYPE_CHECKING:
    from .builder import Builder


class Slot:
    """A named hole inside a Template."""

    __slots__ = ("name", "default", "render")

    def __init__(self, name: str, default="", render=None):
        self.name = name
        self.default = default
        self.render = render

    def __repr__(self) -> str:
        return f"Slot({self.name!r})"


class Template:
    """A read-only, callable HTML template.

    Define a template by wrapping a Builder. Uppercase placeholders inside the
    builder become named slots. Calling the template with keyword arguments
    fills the slots, escapes the values, and returns an HTML string.

    The template object never stores the values passed to it; they are used
    once during the call and then discarded.

    A template is created by wrapping a builder::

        Item = Template(E.li.Name(""))
    """

    __slots__ = ("_fragments",)

    def __init__(self, builder: Builder):
        from .builder import Builder

        if not isinstance(builder, Builder):
            raise TypeError("Template expects a Builder instance")
        self._fragments: tuple[str | Slot, ...] = tuple(self._flatten(builder, builder._templates))

    @staticmethod
    def _flatten(builder: Builder, templates: dict[str, Builder]) -> list[str | Slot]:
        """Convert a Builder into a flat list of strings and Slots."""
        from .builder import AttributedTag

        fragments: list[str | Slot] = []
        buffer: list[str] = []

        def flush() -> None:
            if buffer:
                fragments.append("".join(buffer))
                buffer.clear()

        def make_attr_render(attr: str):
            def render(value):
                return _render_attr(attr, value)

            return render

        for piece in builder._allpieces:
            if isinstance(piece, str):
                buffer.append(piece)
            elif isinstance(piece, AttributedTag):
                buffer.append(piece.prefix)
                for segment in piece.segments:
                    if isinstance(segment, str):
                        buffer.append(segment)
                    elif isinstance(segment, ClassesAttributeSlot):
                        flush()
                        fragments.append(
                            Slot(
                                segment.name,
                                default=segment.default,
                                render=segment,
                            )
                        )
                    else:
                        # segment is an AttributeSlot
                        flush()
                        fragments.append(
                            Slot(
                                segment.name,
                                default=segment.default,
                                render=make_attr_render(segment.attr),
                            )
                        )
                buffer.append(">")
            else:
                # piece is a Builder
                assert piece.name in templates, "Builder pieces must be template slots"
                flush()
                default = HTML(piece)
                fragments.append(Slot(piece.name, default, render=Template._render_value))
        flush()
        return fragments

    def __call__(self, **values) -> HTML:
        """Render the template with the supplied slot values."""
        parts: list[str] = []
        for fragment in self._fragments:
            if isinstance(fragment, str):
                parts.append(fragment)
            else:
                value = values.get(fragment.name, fragment.default)
                parts.append(fragment.render(value))  # type: ignore
        return HTML("".join(parts))

    @staticmethod
    def _render_value(value) -> str:
        if value is None:
            return ""
        if hasattr(value, "__html__"):
            return str(value.__html__())
        if isinstance(value, (str, bytes, bytearray)):
            return str(escape(value))
        if hasattr(value, "__iter__"):
            return "".join(Template._render_value(v) for v in value)
        return str(escape(value))

    def __repr__(self) -> str:
        return f"Template({self._fragments!r})"
