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


def test_template_placeholder_rejects_attributes():
    with pytest.raises(TypeError):
        E.li.Name(class_="foo")


## HTML/str conversion edge cases


def test_template_default_preserves_html_escaping():
    """Slot defaults are pre-rendered HTML and must not be double-escaped."""
    item = Template(E.li.Name("<b>default</b>"))
    assert str(item()) == "<li>&lt;b>default&lt;/b>"


def test_template_default_with_html_literal():
    """Slot defaults containing HTML literals should render as HTML."""
    item = Template(E.li.Name(HTML("<b>default</b>")))
    assert str(item()) == "<li><b>default</b>"


def test_template_default_with_builder():
    """Slot defaults containing a Builder should render the builder's HTML."""
    item = Template(E.li.Name(E.b("default")))
    assert str(item()) == "<li><b>default</b>"


## Attribute slots


def test_template_classes_slot_dict():
    item = E.div(classes=E.ClassesTag) @ Template
    assert str(item(ClassesTag={"foo": True, "bar": False, "baz": True})) == '<div class="foo baz"></div>'


def test_template_classes_slot_str():
    item = E.div(classes=E.ClassesTag) @ Template
    assert str(item(ClassesTag="foo bar")) == '<div class="foo bar"></div>'


def test_template_classes_slot_list():
    item = E.div(classes=E.ClassesTag) @ Template
    assert str(item(ClassesTag=["foo", "bar"])) == '<div class="foo bar"></div>'


def test_template_classes_slot_omits_when_missing():
    item = E.div(classes=E.ClassesTag) @ Template
    assert str(item()) == "<div></div>"


def test_template_classes_slot_combines_with_static_class():
    item = E.div(class_="base", classes=E.ClassesTag) @ Template
    assert str(item(ClassesTag="foo")) == '<div class="base foo"></div>'


def test_template_classes_slot_combines_with_selector_class():
    item = E.div[".base"](classes=E.ClassesTag) @ Template
    assert str(item(ClassesTag="foo")) == '<div class="base foo"></div>'


def test_template_classes_slot_default_str():
    item = E.div(classes=E.ClassesTag("foo bar")) @ Template
    assert str(item()) == '<div class="foo bar"></div>'
    assert str(item(ClassesTag="baz")) == "<div class=baz></div>"


def test_template_classes_slot_default_omits():
    item = E.div(classes=E.ClassesTag(None)) @ Template
    assert str(item()) == "<div></div>"


def test_template_classes_slot_with_other_attributes():
    item = E.div(id_="x", classes=E.ClassesTag, data_role="y") @ Template
    assert str(item(ClassesTag="foo")) == "<div id=x class=foo data-role=y></div>"


def test_template_classes_slot_non_template_rendering():
    assert str(E.div(classes=E.ClassesTag("foo"))) == "<div class=foo></div>"
    assert str(E.div(class_="base", classes=E.ClassesTag)) == "<div class=base></div>"
    assert str(E.div(class_="base", classes=E.ClassesTag("foo"))) == '<div class="base foo"></div>'


def test_template_attribute_slot():
    item = E.article(data_sku=E.Sku) @ Template
    assert str(item(Sku="ABC-123")) == '<article data-sku="ABC-123"></article>'


def test_template_attribute_slot_default():
    item = E.article(data_sku=E.Sku("unknown")) @ Template
    assert str(item()) == "<article data-sku=unknown></article>"
    assert str(item(Sku="ABC")) == "<article data-sku=ABC></article>"


def test_template_attribute_slot_escapes_value():
    item = E.article(data_sku=E.Sku) @ Template
    assert str(item(Sku='a"b&c')) == '<article data-sku="a&quot;b&amp;c"></article>'


def test_template_attribute_slot_default_is_escaped():
    item = E.article(data_sku=E.Sku("<b>")) @ Template
    assert str(item()) == '<article data-sku="&lt;b>"></article>'


def test_template_attribute_slot_multiple():
    item = E.a(href=E.Href, title=E.Title) @ Template
    assert str(item(Href="/x", Title="X")) == '<a href="/x" title=X></a>'


def test_template_attribute_slot_mixed_with_static():
    item = E.input(type="text", value=E.Value, class_="foo") @ Template
    assert str(item(Value="bar")) == "<input type=text value=bar class=foo>"


def test_template_attribute_slot_in_document():
    page = Document("Shop").div(class_="product", data_id=E.Id) @ Template
    assert (
        str(page(Id="42"))
        == '<!DOCTYPE html><meta charset="utf-8"><title>Shop</title><div class=product data-id=42></div>'
    )


def test_attribute_slot_renders_default_without_template():
    """A Builder with a Slot attribute renders its default when not templated."""
    item = E.article(data_sku=E.Sku("UNKNOWN"))
    assert str(item) == "<article data-sku=UNKNOWN></article>"


def test_template_attribute_slot_boolean_true():
    item = E.input(disabled=E.Disabled) @ Template
    assert str(item(Disabled=True)) == "<input disabled>"


def test_template_attribute_slot_boolean_false():
    item = E.input(disabled=E.Disabled) @ Template
    assert str(item(Disabled=False)) == "<input>"


def test_template_attribute_slot_none_omits():
    item = E.input(disabled=E.Disabled) @ Template
    assert str(item(Disabled=None)) == "<input>"


def test_template_attribute_slot_true_among_static():
    item = E.input(type="text", disabled=E.Disabled, class_="foo") @ Template
    assert str(item(Disabled=True)) == "<input type=text disabled class=foo>"
    assert str(item(Disabled=False)) == "<input type=text class=foo>"


def test_template_attribute_slot_default_true():
    item = E.input(disabled=E.Disabled(True)) @ Template
    assert str(item()) == "<input disabled>"
    assert str(item(Disabled=False)) == "<input>"


def test_template_attribute_slot_default_false():
    item = E.input(disabled=E.Disabled(False)) @ Template
    assert str(item()) == "<input>"
    assert str(item(Disabled=True)) == "<input disabled>"


## Attribute slot default/render value matrix


def _attr_slot_matrix():
    """Return expected outputs for each (default_factory, render_value) pair."""
    # default_factories: how the attribute slot default is declared
    # render_values: what is passed when rendering the template
    defaults = {
        "E.Tag": lambda: E.Tag,
        "E.Tag(None)": lambda: E.Tag(None),
        "E.Tag(False)": lambda: E.Tag(False),
        "E.Tag(True)": lambda: E.Tag(True),
        'E.Tag("")': lambda: E.Tag(""),
    }
    render_values = {
        "missing": (False, None),
        "None": (True, None),
        "False": (True, False),
        "True": (True, True),
        '""': (True, ""),
    }
    expected = {
        ("E.Tag", "missing"): "<div></div>",
        ("E.Tag", "None"): "<div></div>",
        ("E.Tag", "False"): "<div></div>",
        ("E.Tag", "True"): "<div data-id></div>",
        ("E.Tag", '""'): '<div data-id=""></div>',
        ("E.Tag(None)", "missing"): "<div></div>",
        ("E.Tag(None)", "None"): "<div></div>",
        ("E.Tag(None)", "False"): "<div></div>",
        ("E.Tag(None)", "True"): "<div data-id></div>",
        ("E.Tag(None)", '""'): '<div data-id=""></div>',
        ("E.Tag(False)", "missing"): "<div></div>",
        ("E.Tag(False)", "None"): "<div></div>",
        ("E.Tag(False)", "False"): "<div></div>",
        ("E.Tag(False)", "True"): "<div data-id></div>",
        ("E.Tag(False)", '""'): '<div data-id=""></div>',
        ("E.Tag(True)", "missing"): "<div data-id></div>",
        ("E.Tag(True)", "None"): "<div></div>",
        ("E.Tag(True)", "False"): "<div></div>",
        ("E.Tag(True)", "True"): "<div data-id></div>",
        ("E.Tag(True)", '""'): '<div data-id=""></div>',
        ('E.Tag("")', "missing"): '<div data-id=""></div>',
        ('E.Tag("")', "None"): "<div></div>",
        ('E.Tag("")', "False"): "<div></div>",
        ('E.Tag("")', "True"): "<div data-id></div>",
        ('E.Tag("")', '""'): '<div data-id=""></div>',
    }
    return defaults, render_values, expected


def test_template_attribute_slot_matrix():
    defaults, render_values, expected = _attr_slot_matrix()
    for default_name, factory in defaults.items():
        for value_name, (provide, value) in render_values.items():
            slot = factory()
            item = E.div(data_id=slot) @ Template
            kwargs = {"Tag": value} if provide else {}
            result = str(item(**kwargs))
            assert result == expected[(default_name, value_name)], (
                f"default={default_name!r}, value={value_name!r}: "
                f"got {result!r}, expected {expected[(default_name, value_name)]!r}"
            )


def test_template_content_slot_none_not_rendered_as_text():
    """A None/False default in a content slot must render as empty, not 'None'."""
    item = E.div(E.Name(None)) @ Template
    assert str(item()) == "<div></div>"
    item = E.div(E.Name(False)) @ Template
    assert str(item()) == "<div></div>"
    item = E.div(E.Name(True)) @ Template
    assert str(item()) == "<div>True</div>"


def test_template_content_slot_none_value():
    item = E.div(E.Name("default")) @ Template
    assert str(item(Name=None)) == "<div></div>"


def test_template_content_slot_non_string_non_iterable_value():
    item = E.div(E.Name("default")) @ Template
    assert str(item(Name=42)) == "<div>42</div>"


def test_attributed_tag_brief():
    from html5tagger.builder import AttributedTag

    tag = E.div(data_id=E.Id("x"))
    attributed = tag._pieces[0]
    assert isinstance(attributed, AttributedTag)
    assert attributed.brief.startswith(":<div data-id=x>")


def test_attributed_tag_brief_long():
    from html5tagger.builder import AttributedTag

    tag = E.div(data_id=E.Id("x" * 200))
    attributed = tag._pieces[0]
    assert isinstance(attributed, AttributedTag)
    assert "···" in attributed.brief


def test_template_with_nested_non_slot_builder():
    span = E.span("static")
    item = Template(E.div(span))
    assert str(item()) == "<div><span>static</span></div>"


def test_template_placeholder_call_sets_default():
    doc = Document()
    doc.title.Title_("Default Title")
    assert str(doc) == "<!DOCTYPE html><title>Default Title</title>"


def test_attributes_with_slots_skips_false_and_renders_true():
    from html5tagger.util import attributes

    result = attributes({"href": E.Href("/x"), "disabled": False, "readonly": True})
    rendered = "".join(str(seg) for seg in result)
    assert 'href="/x"' in rendered
    assert "disabled" not in rendered
    assert "readonly" in rendered


def test_render_attributes_with_segments():
    from html5tagger.util import attributes, render_attributes

    attr_result = attributes({"href": E.Href("/default"), "title": "foo"})
    rendered = render_attributes(attr_result)
    assert 'href="/default"' in rendered
    assert "title=foo" in rendered


def test_placeholder_default_with_multiple_pieces():
    from html5tagger.builder import Builder
    from html5tagger.util import _placeholder_default

    placeholder = Builder("Tag")
    placeholder._("a")
    placeholder._("b")
    default = _placeholder_default(placeholder)
    assert str(default) == "ab"
