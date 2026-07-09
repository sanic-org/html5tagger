from __future__ import annotations


class _NullBuilder:
    """Silently discards any attempts to add content."""

    __slots__ = ()

    def __getattr__(self, name: str) -> _NullBuilder:
        return object.__getattribute__(self, name) if name[0] == "_" and name != "_" else self

    def __call__(self, *_content, **_attrs) -> _NullBuilder:
        return self

    def __getitem__(self, _item) -> _NullBuilder:
        return self

    def __enter__(self) -> _NullBuilder:
        return self

    def __exit__(self, *_args) -> None:
        return None

    def __repr__(self) -> str:
        return "<NullBuilder>"


NullBuilder = _NullBuilder()
