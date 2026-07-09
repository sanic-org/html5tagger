class _NullBuilder:
    """Silently discards any attempts to add content."""

    def __getattr__(self, name: str):
        return object.__getattribute__(self, name) if name[0] == "_" and name != "_" else self

    def __call__(self, *_content, **_attrs):
        return self

    def __getitem__(self, _item):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def __repr__(self):
        return "<NullBuilder>"


NullBuilder = _NullBuilder()
