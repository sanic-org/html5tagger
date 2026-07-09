from __future__ import annotations

from .builder import Builder


class MakeBuilder:
    """Use E.elemname or E(content) to create initially empty snippets."""

    def __getattr__(self, name: str) -> Builder:
        return getattr(Builder("E Builder"), name)

    def __call__(self, *args, **kwargs) -> Builder:
        return Builder("E Builder")(*args, **kwargs)


E = MakeBuilder()
