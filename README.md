# HTML5 templating with Pure Python

If you're looking for a more efficient and streamlined way to generate HTML5, look no further than html5tagger! This is a super fast HTML generation module that can run faster than Jinja2. But the main difference is you'll be writing HTML tags with Python syntax, from your code. No special templating language control structures and no typing in HTML.

```sh
pip install html5tagger
```

## Intro

html5tagger provides two starting points for HTML generation: `E` as an empty builder for creating HTML snippets, or `Document` for generating full HTML documents with a DOCTYPE declaration. Both produce a `Builder` object, in case you need that for type annotations.

Create a snippet and add tags by dot notation:
```python
E.p("Powered by:").br.a(href="...")("html5tagger")
```
```html
<p>Powered by:<br><a href="...">html5tagger</a>
```

A complete example with template variables and other features:

```python
from html5tagger import Document, E, Template

# Create a document
doc = Document(
    "Demo",                 # The first argument is for <title>
    lang="en",              # Keyword arguments for <html> attributes

    # Just list the resources you need, no need to remember link/script tags
    _urls=[ "style.css", "favicon.png", "manifest.json" ]
)

# This has been a hard problem for DOM other such generators:
doc.p("A paragraph with ").a("a link", href="/files")(" and ").em("formatting")

# Use templates to render dynamic content
doc.h1("Demo")
doc.ul.li("Apple").li("Banana")

# Use with for complex nesting (not often needed)
with doc.table(id="data"):
    doc.tr.th("First").th("Second").th("Third")
    for row in range(3):
        doc.tr
        for col in range(3):
            doc.td(row * col)

# Add inline scripts or styles with special escaping
doc.script("console.log('</script> escaping is weird')")
```

You can `str(doc)` to get the HTML code, and using `doc` directly usually has the desired effect as well (e.g. giving HTML responses). Jupyter Notebooks render it as HTML. For debugging, use `repr(doc)`:

```html
>>> doc
《Document Builder》
<!DOCTYPE html><html lang=en><meta charset="utf-8"><title>Demo</title>
<link href="style.css" rel=stylesheet>
<link href="favicon.png" rel=icon type="image/png">
<link href="manifest.json" rel=manifest>
<p>A paragraph with <a href="/files">a link</a> and <em>formatting</em>
<h1>Demo</h1>
<ul>
  <li>Apple
  <li>Banana
</ul>
<table id=data>
  <tr><th>First<th>Second<th>Third
  <tr><td>0<td>0<td>0
  <tr><td>0<td>1<td>2
  <tr><td>0<td>2<td>4
</table>
<script>console.log('<\/script> escaping is weird')</script>
```

The actual HTML output is similar. No whitespace is added to the document, it is all on one line unless the content contains newlines. You may notice that `body` and other familiar tags are missing and that the escaping is very minimal. This is HTML5: the document is standards-compliant with a lot less cruft.

## Templating

A document builder can be turned into a template by `Template(doc)`. Templates prebuild all static content as long strings, leaving only capitalized placeholders to be filled in at render time. This provides extremely fast rendering and allows building a complex page out of clean components.

The example below defines a page with `Title` reused for both the `<title>` and `<h1>`, and an `Items` list populated from a product list. Parentheses directly after a placeholder set its default value (empty by default).

```python
from html5tagger import Document, E, Template

# Define the reusable templates once
Page = Template(Document(E.Title).h1.Title.ul.Items)
Item = Template(E.li.span[".name"].Name.span[".price"].Price("N/A"))

# Super fast rendering just fills in the dynamic data
def render(products: list) -> str:
    return Page(
        Title="Product List",
        Items=[Item(**product) for product in products],
    )

html = render([
    {"Name": "Apple", "Price": "$1.20"},
    {"Name": "Banana"},
])
```

```html
<!DOCTYPE html>
<meta charset="utf-8">
<title>Product List</title>
<h1>Product List</h1>
<ul>
  <li><span class=name>Apple</span><span class=price>$1.20</span>
  <li><span class=name>Banana</span><span class=price>N/A</span>
</ul>
```

A builder can be finalized into a template by `Template(...)`. The resulting `Template` object is immutable and is called with keyword arguments to render the placeholders. Template values follow the same escaping rules as `doc(...)`, and a list of builders or strings is expanded in place.

## Nesting

In HTML5 elements such as `<p>` do not need any closing tag, so we can keep adding content without worrying of when it should close. This module does not use closing tags for any elements where those are optional or forbidden.

A tag is automatically closed when you add content to it or when another tag is added. Setting attributes alone does not close an element, so we can do `doc.div[".foo"]("inside")` where the content still goes inside the div. `None` may be passed for content to close without content, e.g. `doc.div(None)("after")` produces `<div></div>after`.

For elements like `<table>` and `<ul>`, you can use `with` blocks, pass sub-snippet arguments, or add a template variable.

```python
with doc.ul:  # Nest using with
    doc.li("Write HTML in Python")
    doc.li("Simple syntax").ul(id="inner").InnerList  # Nest using template
    doc.li("No need for brackets or closing tags")
    doc.ul(E.li("Easy").li("Peasy"))  # Nest using (...)
```

## Escaping and special methods

All content and attributes are automatically escaped with rules depending on context where it appears. For instance, we can put the entire document into an iframe's srcdoc attribute where only the minimal but necessary escaping is applied. Methods `script`, `style` and `_comment` follow their custom escaping rules. Note that parenthesis must be added after these with optional attributes and str content: the element will immediately close without needing explicit `None` content for an empty element.

```python
doc = Document("Escaping & Context")
doc.style('h1::after {content: "</Style>"}').h1("<Escape>")
doc._comment("All-->OK")
doc.iframe(srcdoc=Document().p("&amp; is used for &"))
```

```html
<!DOCTYPE html><meta charset="utf-8"><title>Escaping &amp; Context</title>
<style>h1::after {content: "<\/Style>"}</style><h1>&lt;Escape></h1>
<!--All‒‒>OK-->
<iframe srcdoc="<!DOCTYPE html><p>&amp;amp;amp; is used for &amp;amp;"></iframe>
```

Works perfectly in browsers.

## Name mangling and boolean attributes

Underscore at the end of a name is ignored so that `for_` and other attributes may be used despite being reserved words in Python. Other underscores convert into hyphens.

Boolean values convert into short attributes.

```python
E.input(type="checkbox", id="somebox", checked=True).label(for_="somebox", aria_role="img")("🥳")
```

```html
<input type=checkbox id=somebox checked><label for=somebox aria-role=img>🥳</label>
```

## Appending classes

The special `classes` keyword argument in the call operator appends classes to the current element. It does not create a `classes` attribute; instead it merges the given classes into the existing `class` attribute (if any). This is useful for dynamic class lists, for example when combined with CSS selectors or when the class names come from variables.

`classes` accepts a whitespace-separated string, a list of class strings, or a dictionary where each key is included as a class only if its value is truthy:

```python
doc.div(classes="foo bar")
doc.div(classes=["foo", "bar"])
doc.div(classes={"foo": True, "bar": False})
```

```html
<div class="foo bar"></div>
<div class="foo bar"></div>
<div class=foo></div>
```

## CSS selector style attributes

As an alternative to keyword arguments, attributes may be set using CSS selector syntax with the subscript (`[]`) operator. This supports `#id`, `.class` and `[attribute=value]`, including boolean attributes with `[attribute]`. This is only intended to be used with static content, and for any dynamic values you should follow the `[]` with a `()`.

```python
doc.main["#lead.container.article"]("Hello")
doc.a["[href=/files]"]("a link")
doc.input["[type=checkbox][checked]"]
doc.div["#widget.foo[aria-label=Foo Widget]"](classes=["bar", "baz"], data_user=userid)
```

```html
<main id=lead class="container article">Hello</main>
<a href="/files">a link</a>
<input type=checkbox checked>
<div id=widget class="foo bar baz" aria-label="Foo Widget" data-user=user123>
```

Multiple selectors may be combined in one string and the `[]` and `()` operators may be chained. Overriding values already set is not possible. To append classes use the `classes` keyword argument in the call operator. The values can be single or double quoted or without quotes (no CSS restrictions, anything but `]` allowed). Limited support for backslash escapes is provided as well, e.g. for escaping the backslash itself or the quote character within a quoted value.

## Conditional elements

A boolean inside the subscript operator conditionally includes the element
that follows. When `False`, the tag and any chained call are skipped, but
the surrounding code still runs normally.

```python
with doc[use_highlight].mark:
    doc("Highlighted when enabled.")
```

## Preformatted HTML

All content is automatically escaped, unless it provides an `__html__` method that returns a string in HTML format. Similarly, the builder objects of this module expose `__html__` and `_repr_html_` accessors that allow them to be rendered as HTML in Jupyter Notebooks and various other systems that follow this convention.

Any preformatted HTML may be wrapped in `html5tagger.HTML(string_of_html)` to avoid it being escaped when included in a document, as the HTML class has those accessors.

⚠️ Do not use `HTML()` for text, in particular not on messages sent by users, that may contain HTML that you didn't intend to execute as HTML.

## Further development

There have been no changes to the tagging API since 2018 when this module was brought to production use, and thus the interface is considered stable with only small incremental changes like the `script` and `style` special methods being added.

The templating API added as a draft in version 1.3 is deprecated as of version 1.4 and is removed in 2.0, where it is replaced by a redesigned templating system. Users who depend on the old templating behaviour should pin `html5tagger<2`; all others are encouraged to upgrade to 2.0 which is faster and more versatile.
