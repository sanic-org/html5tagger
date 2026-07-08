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


def test_css_selector_id():
    snippet = E.div["#main"]("Hello")
    assert str(snippet) == "<div id=main>Hello</div>"


def test_css_selector_class():
    snippet = E.div[".container"]("Hello")
    assert str(snippet) == "<div class=container>Hello</div>"


def test_css_selector_multiple_classes():
    snippet = E.div[".foo.bar.baz"]("Hello")
    assert str(snippet) == '<div class="foo bar baz">Hello</div>'


def test_css_selector_attribute():
    snippet = E.a["[href=/path]"]("Link")
    assert str(snippet) == '<a href="/path">Link</a>'


def test_css_selector_quoted_attribute():
    snippet = E.div['[data-value="foo bar"]']("Hello")
    assert str(snippet) == '<div data-value="foo bar">Hello</div>'


def test_css_selector_boolean_attribute():
    snippet = E.input["[disabled]"]()
    assert str(snippet) == "<input disabled>"


def test_css_selector_combined():
    snippet = E.div["#main.container[data-role=widget]"]("Hello", classes="extra", foo=True)
    assert str(snippet) == '<div id=main class="container extra" data-role=widget foo>Hello</div>'

    snippet = E.div(classes="extra", foo=True)["#main.container[data-role=widget]"]("Hello")
    assert str(snippet) == '<div foo id=main class="extra container" data-role=widget>Hello</div>'


def test_css_selector_chained():
    snippet = E.div[".card[data=foo]"]["#main.container"]("Hello")
    assert str(snippet) == '<div data=foo id=main class="card container">Hello</div>'


def test_css_selector_hyphenated_value():
    snippet = E.div["[data-value=foo-bar]"]("Hello")
    assert str(snippet) == '<div data-value="foo-bar">Hello</div>'


def test_css_selector_underscore_attribute_not_mangled():
    snippet = E.div["[data_test=value]"]("Hello")
    assert str(snippet) == "<div data_test=value>Hello</div>"


def test_css_selector_escaped_double_quote_in_double_quotes():
    snippet = E.div[r'[data-value="foo\"bar"]']("Hello")
    assert str(snippet) == '<div data-value="foo&quot;bar">Hello</div>'


def test_css_selector_escaped_single_quote_in_single_quotes():
    snippet = E.div[r"[data-value='foo\'bar']"]("Hello")
    assert str(snippet) == """<div data-value="foo'bar">Hello</div>"""


def test_css_selector_escaped_backslash_in_double_quotes():
    snippet = E.div[r'[data-value="foo\\bar"]']("Hello")
    assert str(snippet) == '<div data-value="foo\\bar">Hello</div>'


def test_css_selector_escaped_backslash_unquoted():
    snippet = E.div[r"[data-value=foo\\bar]"]("Hello")
    assert str(snippet) == '<div data-value="foo\\bar">Hello</div>'


def test_css_selector_only_escaped_quote():
    snippet = E.div[r'[data-value="\""]']("Hello")
    assert str(snippet) == '<div data-value="&quot;">Hello</div>'


def test_css_selector_only_escaped_backslash():
    snippet = E.div[r'[data-value="\\"]']("Hello")
    assert str(snippet) == '<div data-value="\\">Hello</div>'


def test_css_selector_invalid_type_raises():
    with pytest.raises(AssertionError):
        E.div[123]


def test_css_selector_invalid_gap_raises():
    with pytest.raises(AssertionError):
        E.div["#main!.container"]


def test_css_selector_invalid_trailing_junk_raises():
    with pytest.raises(AssertionError):
        E.div["#main bad"]


def test_css_selector_invalid_leading_junk_raises():
    with pytest.raises(AssertionError):
        E.div["bad#main"]


def test_css_selector_invalid_space_between_selectors_raises():
    with pytest.raises(AssertionError):
        E.div["#main .container"]


def test_classes_str_appends():
    snippet = E.div[".foo"]("Hello", classes="bar baz")
    assert str(snippet) == '<div class="foo bar baz">Hello</div>'


def test_classes_list_appends():
    snippet = E.div[".foo"]("Hello", classes=["bar", "baz"])
    assert str(snippet) == '<div class="foo bar baz">Hello</div>'


def test_classes_dict_appends():
    snippet = E.div[".foo"]("Hello", classes={"bar": True, "baz": False, "qux": True})
    assert str(snippet) == '<div class="foo bar qux">Hello</div>'


def test_classes_generator_appends():
    snippet = E.div[".foo"]("Hello", classes=(c for c in ["bar", "baz"]))
    assert str(snippet) == '<div class="foo bar baz">Hello</div>'


def test_classes_appends_to_class_attr():
    snippet = E.div(class_="foo")("Hello", classes="bar")
    assert str(snippet) == '<div class="foo bar">Hello</div>'


def test_classes_preserve_class_kwarg_position():
    snippet = E.div(id_="main", class_="foo", data_role="widget")("Hello", classes="bar")
    assert str(snippet) == '<div id=main class="foo bar" data-role=widget>Hello</div>'


def test_classes_preserve_classes_kwarg_position():
    snippet = E.div(id_="me", classes=["foz", "baz"], foo="bar")
    assert str(snippet) == '<div id=me class="foz baz" foo=bar></div>'


def test_classes_empty_str_no_class():
    snippet = E.div[".foo"]("Hello", classes="")
    assert str(snippet) == "<div class=foo>Hello</div>"


def test_classes_empty_list_no_class():
    snippet = E.div[".foo"]("Hello", classes=[])
    assert str(snippet) == "<div class=foo>Hello</div>"


def test_classes_no_existing_class():
    snippet = E.div("Hello", classes="foo bar")
    assert str(snippet) == '<div class="foo bar">Hello</div>'


def test_classes_on_template_placeholder_raises():
    doc = Document()
    assert doc.Head_ is doc
    with pytest.raises(AssertionError):
        doc(classes="foo")


def test_builder_no_content_creates_empty():
    snippet = Builder("Empty")
    assert str(snippet) == ""


def test_builder_underscore_appends_none_is_ignored():
    doc = Document()
    doc._(None, "hello", None)
    assert str(doc) == "<!DOCTYPE html>hello"


def test_builder_underscore_appends_own_template_directly():
    doc = Document(E.Title_)
    title = doc._templates["Title"]
    doc._(title)
    assert doc._pieces[-1] is title
