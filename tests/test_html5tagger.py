"""Tests for html5tagger."""

import pytest

from html5tagger import HTML, Builder, Document, E


def test_empty_document():
    doc = Document()
    assert str(doc) == "<!DOCTYPE html>"


def test_document_with_title_and_lang():
    doc = Document("Page title", lang="en")
    assert "<html lang=en>" in str(doc)
    assert '<meta charset="utf-8">' in str(doc)
    assert "<title>Page title</title>" in str(doc)


def test_element_chain():
    snippet = E.p("Powered by:").br.a(href="...")("html5tagger")
    assert str(snippet) == '<p>Powered by:<br><a href="...">html5tagger</a>'


def test_with_context_manager():
    doc = Document("Table demo")
    with doc.table(id="data"):
        doc.tr.th("First").th("Second")
    html = str(doc)
    assert "<table id=data>" in html
    assert "</table>" in html
    assert "<tr><th>First<th>Second" in html


def test_with_context_manager_on_void_element_raises():
    doc = Document()
    with pytest.raises(AssertionError), doc.br:
        pass


def test_nested_snippet():
    doc = Document()
    doc.ul(E.li("Easy").li("Peasy"))
    assert str(doc) == "<!DOCTYPE html><ul><li>Easy<li>Peasy</ul>"


def test_escaping():
    doc = Document("Escaping & Context")
    doc.h1("<Escape>")
    assert "<title>Escaping &amp; Context</title>" in str(doc)
    assert "<h1>&lt;Escape></h1>" in str(doc)


def test_html_literal_not_escaped():
    doc = Document()
    doc._(HTML("<custom>"))
    assert str(doc) == "<!DOCTYPE html><custom>"


def test_script_escaping():
    doc = Document()
    doc.script("console.log('</script>')")
    assert "<script>console.log('<\\/script>')</script>" in str(doc)


def test_style_escaping():
    doc = Document()
    doc.style('h1::after {content: "</Style>"}')
    assert '<style>h1::after {content: "<\\/Style>"}</style>' in str(doc)


def test_comment():
    doc = Document()
    doc._comment("All-->OK")
    assert "<!--All‒‒>OK-->" in str(doc)


def test_boolean_attribute():
    snippet = E.input(type="checkbox", checked=True)
    assert str(snippet) == "<input type=checkbox checked>"


def test_underscore_mangling():
    snippet = E.label(for_="somebox", aria_role="img")("🥳")
    assert str(snippet) == "<label for=somebox aria-role=img>🥳</label>"


def test_urls_linking():
    doc = Document(_urls=["style.css", "favicon.png", "manifest.json"])
    html = str(doc)
    assert '<link href="style.css" rel=stylesheet>' in html
    assert '<link href="favicon.png" rel=icon type="image/png">' in html
    assert '<link href="manifest.json" rel=manifest>' in html


def test_urls_script():
    doc = Document(_urls=["app.js"])
    assert '<script src="app.js" defer></script>' in str(doc)


def test_urls_module():
    doc = Document(_urls=["app.mjs"])
    assert '<script src="app.mjs" type=module></script>' in str(doc)


def test_unknown_url_extension_raises():
    with pytest.raises(ValueError):
        Document(_urls=["unknown.xyz"])


def test_viewport_bool():
    doc = Document(_viewport=True)
    assert '<meta name=viewport content="width=device-width,initial-scale=1">' in str(doc)


def test_viewport_string():
    doc = Document(_viewport="width=500")
    assert '<meta name=viewport content="width=500">' in str(doc)


def test_cannot_add_self():
    doc = Document()
    with pytest.raises(AssertionError):
        doc._(doc)


def test_repr_and_brief():
    doc = Document("Demo")
    assert "Document Builder" in repr(doc)
    assert "Document Builder" in doc.brief


def test_iter():
    doc = Document("Demo")
    assert "".join(doc) == str(doc)


def test_brief_empty_short_and_long():
    empty = Builder("Empty")
    assert empty.brief == "《Empty》"

    short = Document("Demo")
    assert short.brief == '《Document Builder:<!DOCTYPE html><meta charset="utf-8"><title>Demo</title>》'

    long_text = "x" * 200
    long_doc = Document(long_text)
    assert long_doc.brief == f"《Document Builder:{str(long_doc)[:20]} ···》"


def test_repr_long_truncation():
    doc = Document()
    doc._("x" * 20000)
    rep = repr(doc)
    assert " ··· " in rep


def test_makebuilder_call():
    snippet = E("Hello")
    assert str(snippet) == "Hello"
    snippet2 = E.div("World")
    assert str(snippet2) == "<div>World</div>"


def test_attribute_skipping():
    snippet = E.input(type="text", disabled=False, hidden=None, checked=True)
    assert str(snippet) == "<input type=text checked>"
