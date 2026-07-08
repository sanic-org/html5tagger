# HTML5 Generation with html5tagger: Fast, Pure Python, No Dependencies

If you're looking for a more efficient and streamlined way to generate HTML5, look no further than html5tagger! This module provides a simplified HTML5 syntax, so you can create your entire document template using only Python. Say goodbye to the clunky and error-prone process of manually writing HTML tags.

With html5tagger, you can safely and quickly generate HTML5 without any dependencies, making it the perfect solution for developers who value speed and simplicity. And with its pure Python implementation, you'll never have to worry about compatibility issues or adding extra libraries to your project.

Ready to streamline your page rendering process? It is super fast to get started. Trust us, once you try html5tagger, you'll never go back to Jinja2 or manual HTML writing again!

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
from html5tagger import Document, E

# Create a document
doc = Document(
    E.TitleText_,           # The first argument is for <title>, adding variable TitleText
    lang="en",              # Keyword arguments for <html> attributes

    # Just list the resources you need, no need to remember link/script tags
    _urls=[ "style.css", "favicon.png", "manifest.json" ]
)

# Upper case names are template variables. You can modify them later.
doc.Head_
doc.h1.TitleText_("Demo")   # Goes inside <h1> and updates <title> as well

# This has been a hard problem for DOM other such generators:
doc.p("A paragraph with ").a("a link", href="/files")(" and ").em("formatting")

# Use with for complex nesting (not often needed)
with doc.table(id="data"):
    doc.tr.th("First").th("Second").th("Third")
    doc.TableRows_

# Let's add something to the template variables
doc.Head._script("console.log('</script> escaping is weird')")

table = doc.TableRows
for row in range(10):
    table.tr
    for col in range(3):
        table.td(row * col)

# Or remove the table data we just added
doc.TableRows = None
```

You can `str(doc)` to get the HTML code, and using `doc` directly usually has the desired effect as well (e.g. giving HTML responses). Jupyter Notebooks render it as HTML. For debugging, use `repr(doc)` where the templating variables are visible:

```html
>>> doc
《Document Builder》
<!DOCTYPE html><html lang=en><meta charset="utf-8">
<title>《TitleText:Demo》</title>
<link href="style.css" rel=stylesheet>
<link href="favicon.png" rel=icon type="image/png">
<link href="manifest.json" rel=manifest>
《Head:<script>console.log('<\/script> escaping is weird')</script>》
<h1>《TitleText:Demo》</h1>
<p>A paragraph with <a href="/files">a link</a> and <em>formatting</em>
<table id=data>
  <tr><th>First<th>Second<th>Third
  《TableRows》
</table>
```

The actual HTML output is similar. No whitespace is added to the document, it is all on one line unless the content contains newlines. You may notice that `body` and other familiar tags are missing and that the escaping is very minimal. This is HTML5: the document is standards-compliant with a lot less cruft.

## Templating

Use template variables to build a document once and only update the dynamic parts at render time for faster performance. Access template variables via doc.TitleText and add content in parenthesis after the tag name. The underscore at the end of a tag name indicates the tag is added to the document and can have content in parenthesis, but any further tags on the same line go to the original document, not the template.

## Nesting

In HTML5 elements such as `<p>` do not need any closing tag, so we can keep adding content without worrying of when it should close. This module does not use closing tags for any elements where those are optional or forbidden.

A tag is automatically closed when you add content to it or when another tag is added. Setting attributes alone does not close an element. Use `(None)` to close an empty element if any subsequent content is not meant to go inside it, e.g. `doc.script(None, src="...")`.

For elements like `<table>` and `<ul>`, you can use `with` blocks, pass sub-snippet arguments, or add a template variable. Unlike adding another tag, adding a template does NOT close its preceding tag but instead the variable goes inside any open element.

```python
with doc.ul:  # Nest using with
    doc.li("Write HTML in Python")
    doc.li("Simple syntax").ul(id="inner").InnerList_  # Nest using template
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

Underscore at the end of name is ignored so that `for_` and other attributes may be used despite being reserved words in Python. Other underscores convert into hyphens.

⚠️ The above only is true for HTML elements and attributes, but template placeholders only use an ending underscore to denote that the it is to be placed on the document, rather than be fetched for use.

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


## Preformatted HTML

All content is automatically escaped, unless it provides an `__html__` method that returns a string in HTML format. Similarly, the builder objects of this module expose `__html__` and `_repr_html_` accessors that allow them to be rendered as HTML in Jupyter Notebooks and various other systems that follow this convention.

Any preformatted HTML may be wrapped in `html5tagger.HTML(string_of_html)` to avoid it being escaped when included in a document, as the HTML class has those accessors.

⚠️ Do not use `HTML()` for text, in particular not on messages sent by users, that may contain HTML that you didn't intend to execute as HTML.

## Performance

```python
%timeit str(Document("benchmarking", lang="en", _urls=("foo.js", "bar.js")))
14 µs ± 153 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)
```

Jinja2 renders similar document from memory template within about 10 µs but it doesn't need to format any of the HTML. When Templating is similarly used with html5tagger, the rendering times drop to about 4 µs.

In the above benchmark html5tagger created the entire document from scratch, one element and attribute at a time. Unless you are creating very large documents dynamically, this should be quite fast enough.

## Further development

There have been no changes to the tagging API since 2018 when this module was brought to production use, and thus the interface is considered stable.

In 2023 support for templating was added, allowing documents to be preformatted for all their static parts (as long strings), with only templates filled in between. This is a work on progress and has not been optimized yet.

Pull requests are still welcome.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management,
[nox](https://nox.thea.codes/) for task automation, [ruff](https://docs.astral.sh/ruff/)
for linting and formatting, and [ty](https://docs.astral.sh/ty/) for type checking.

Set up the environment and run the full test suite:

```sh
uv sync
uv run nox
```

Run only linting or tests:

```sh
uv run nox -s lint
uv run nox -s test
```
