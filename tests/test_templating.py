"""Tests for html5tagger templating."""

import pytest

from html5tagger import Document, E


def test_template_placeholder():
    doc = Document(E.TitleText_)
    doc.h1.TitleText_("Hello")
    assert "<title>Hello</title>" in str(doc)
    assert "<h1>Hello</h1>" in str(doc)


def test_template_fetch_and_update():
    doc = Document(E.TitleText_)
    doc.h1.TitleText_("Hello")
    title = doc.TitleText
    title("World")
    assert "<title>HelloWorld</title>" in str(doc)
    assert "<h1>HelloWorld</h1>" in str(doc)


def test_template_not_found_raises():
    doc = Document("Demo")
    with pytest.raises(AttributeError):
        _ = doc.MissingTemplate


def test_clear_template():
    doc = Document("Demo")
    assert doc.Head_ is doc
    doc.Head = None
    assert doc.Head is not None


def test_template_reuse_in_doc():
    doc = Document("Demo")
    assert doc.Head_ is doc
    head = doc.Head
    doc._(head)
    assert "<title>Demo</title>" in str(doc)
    # Adding the same template builder back appends it directly.
    assert doc._pieces[-1] is head
