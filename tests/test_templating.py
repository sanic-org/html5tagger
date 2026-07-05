"""Tests for html5tagger templating."""

import pytest

from html5tagger import HTML, Document, E, Template

## Placeholder creation


def test_template_insert_placeholder():
    doc = Document(E.TitleText)
    doc.h1.TitleText
    item = doc @ Template
    assert str(item(TitleText="Hello")) == '<!DOCTYPE html><meta charset="utf-8"><title>Hello</title><h1>Hello</h1>'


def test_template_closes_open_tag():
    """doc.span.Tag.br == <span>Tag</span><br>"""
    doc = Document()
    doc.span.Tag.br
    item = doc @ Template
    assert str(item(Tag="content")) == "<!DOCTYPE html><span>content</span><br>"


def test_template_creates_on_access():
    """Accessing an unknown uppercase name creates and inserts the placeholder."""
    doc = Document()
    doc.Missing
    assert "Missing" in doc._templates


## Stateless Template callable


def test_template_constructor():
    item = Template(E.li.Name(""))
    assert str(item(Name="Apple")) == "<li>Apple"


def test_template_matmul_operator():
    item = E.li.Name("") @ Template
    assert str(item(Name="Apple")) == "<li>Apple"


def test_template_default_value():
    item = Template(E.li.Name("unknown"))
    assert str(item()) == "<li>unknown"
    assert str(item(Name="Apple")) == "<li>Apple"


def test_template_slot_call_replaces_default():
    item = Template(E.li.Name("first").Name("second"))
    assert str(item()) == "<li>secondsecond"


def test_template_slot_default_stays_in_place_when_called_after_access():
    item = Template(E.li.span.Name("NONAME").span.Price)
    assert str(item(Price="$1.20")) == "<li><span>NONAME</span><span>$1.20</span>"
    assert str(item(Name="Banana", Price="$0.80")) == "<li><span>Banana</span><span>$0.80</span>"


def test_template_slot_followed_by_append_goes_after_parent_tag():
    item = Template(E.li.span.Name._("X"))
    assert str(item(Name="A")) == "<li><span>A</span>X"


def test_template_escapes_values():
    item = Template(E.li.Name(""))
    assert str(item(Name="<script>")) == "<li>&lt;script>"


def test_template_accepts_html_literal():
    item = Template(E.li.Name(""))
    assert str(item(Name=HTML("<b>bold</b>"))) == "<li><b>bold</b>"


def test_template_multiple_slots():
    item = Template(E.li.Name("").span.Price(""))
    assert str(item(Name="Apple", Price="1.99")) == "<li>Apple<span>1.99</span>"


def test_template_with_e_nesting():
    """Template slots can be placed with nested E(...) builders."""
    item = Template(
        E.div(class_="card")(
            E.h3(class_="title")(E.Name),
            E.p(class_="desc")(E.Desc),
            E.div(class_="meta")(
                E.span(class_="price")(E.Price),
                E.span(class_="stock")(E.Stock),
            ),
        )
    )
    html = str(item(Name="X", Desc="Y", Price="Z", Stock="ok"))
    assert (
        html
        == "<div class=card><h3 class=title>X</h3><p class=desc>Y<div class=meta><span class=price>Z</span><span class=stock>ok</span></div></div>"
    )


def test_template_multiple_references_use_same_value():
    item = Template(E.li.Name("").span.Name(""))
    assert str(item(Name="X")) == "<li>X<span>X</span>"


def test_template_slot_renders_list_of_values():
    page = Template(Document("X").ul.Items)
    html = str(page(Items=[E.li("A"), E.li("B")]))
    assert html == '<!DOCTYPE html><meta charset="utf-8"><title>X</title><ul><li>A<li>B</ul>'


def test_template_slot_renders_generator_of_values():
    page = Template(Document("X").ul.Items)
    items = (E.li(name) for name in ("A", "B"))
    html = str(page(Items=items))
    assert html == '<!DOCTYPE html><meta charset="utf-8"><title>X</title><ul><li>A<li>B</ul>'


def test_template_reuse_in_loop():
    item = Template(E.li.Name(""))
    doc = Document("List")
    doc.ul
    for name in ("A", "B", "C"):
        doc._(item(Name=name))
    html = str(doc)
    assert "<li>A<li>B<li>C" in html


def test_template_does_not_mutate_builder():
    tpl = E.li.Name("default")
    item = Template(tpl)
    _ = item(Name="Apple")
    _ = item(Name="Banana")
    # The original builder is untouched.
    assert str(tpl) == "<li>default"


def test_template_only_accepts_builder():
    with pytest.raises(TypeError):
        Template("not a builder")
