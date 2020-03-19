# Pythonic HTML5 generation

The module is named **html5tagger** because it makes heavy use of the simplified HTML5 syntax where many opening and closing tags are optional. Tags are written with no consideration of DOM tree structure, which the browsers determine automatically based on the content that follows. No *pretty printing* is added to the HTML code because such extra whitespace would create unnecessary DOM nodes, often affecting output formatting as well.

```
pip install html5tagger
```

Since the module is a single file with no dependencies, you may also just copy [html5tagger.py](https://github.com/Tronic/html5tagger/raw/master/html5tagger.py) directly into your project.

## Intro

You can create HTML snippets by starting with `E` (for an empty builder) and adding elements with dot notation:

```python
from html5tagger import Document, E

snippet = E.table(E.tr.th("First").th("Second").th("Third").tr.td(1).td(2).td(3))

print(snippet)  # Print snippet's code
```

```html
<table><tr><th>First<th>Second<th>Third<tr><td>1<td>2<td>3</table>
```

The `Builder` object converts to HTML string when printed or by `str(snippet)`. [Jupyter Notebook](https://jupyter.org/) and others may render them automatically as HTML, unless explicitly converted into string first.

In contrast to `E` which creates snippets, `Document` creates a new document (i.e. it begins with a DOCTYPE declaration). A minimal head structure is created using any provided title and/or urls. `html` attributes may be defined by keyword arguments.

```python
Document("Test page", lang="en")
```

```html
<!DOCTYPE html><html lang=en><meta charset="utf-8"><title>Test page</title>
```

This is a valid document by itself. `</head><body>` and `</body></html>` are not needed in HTML5, and thus any content may simply be appended to this, without ever *closing* the document.

You can also add your js, css, favicon and manifest files:

```python
Document(_urls=("style.css", "logo.png", "jquery.js"))
```

```html
<!DOCTYPE html>
<link rel=stylesheet href="style.css">
<link rel=icon href="logo.png", type="image/png">
<script src="jquery.js"></script>
```

## Nesting

Explicit nesting needs to be used for elements such as `table` and `ul` where contents may be provided as sub-snippet parameters, or by `with` blocks:

```python
doc = Document("Test page", lang="en")
with doc.ul:  # Nest using the with statement
    doc.li("Write documents in Python").li("Simple syntax")
    with doc.ul:
        doc.li("No brackets or closing tags").li("Integrates with other code")
        doc.ul(E.li("Easy").li("Efficient"))  # Nest using (...)
    doc.li("Avoids whitespace problems common in templating")
```

Output formatted for readability:

```html
<!DOCTYPE html>
<html lang=en>
  <meta charset="utf-8">
  <title>Test page</title>
  <ul>
    <li>Write documents in Python
    <li>Simple syntax
      <ul>
        <li>No brackets or closing tags
        <li>Integrates with other code
          <ul>
            <li>Easy
            <li>Efficient
          </ul>
      </ul>
    <li>Avoids whitespace problems common in templating
  </ul>
```

## Escaping

All content and attributes are automatically escaped. For instance, we can put the entire document into an iframe's srcdoc attribute where only the minimal but necessary escaping is applied:

```python
E.iframe(srcdoc=doc)
```

```html
<iframe srcdoc="<!DOCTYPE html><html lang=en><meta charset=&quot;utf-8&quot;><title>Test page</title><ul><li>Write documents in Python<li>Simple syntax<ul><li>No brackets or closing tags<li>Integrates with other code<ul><li>Easy<li>Efficient</ul></ul><li>Avoids whitespace problems common in templating</ul>"></iframe>
```

## Name mangling and boolean attributes

Underscore at the end of name is ignored so that Python's reserved names such as `for` can be specified. Other underscores convert into hyphens.

Boolean values convert into short attributes.

```python
E.input(type="checkbox", id="somebox", checked=True).label(for_="somebox", aria_role="img")("🥳")
```

```html
<input type=checkbox id=somebox checked><label for=somebox aria-role=img>🥳</label>
```

## Preformatted HTML

All content is automatically escaped, unless it provides an `__html__` method that returns HTML string. Similarly, the builder objects of this module expose `__html__` and `_repr_html_` accessors that allow them to be rendered as HTML in Jupyter Notebooks and various other systems that follow this convention.

Any preformatted HTML may be wrapped in `html5tagger.HTML(string_of_html)` to avoid it being escaped when included in a document, as the HTML class has those accessors.

## Performance

```python
%timeit str(Document("benchmarking", lang="en", _urls=("foo.js", "bar.js")))
```

    35.7 µs ± 1.11 µs per loop (mean ± std. dev. of 7 runs, 10000 loops each)

Unless you are creating very large documents, this should be quite fast enough.

Traditional web frameworks like [Django](https://www.djangoproject.com/) and [Flask](https://palletsprojects.com/p/flask/) are probably much slower. [Sanic](https://sanic.readthedocs.io/en/latest/) users might need to optimise some more to stay above 20000 req/s or so.

## Further development

There have been no changes to the tagging API since 2018 when this module was brought to production use, and thus the interface is considered stable.

If there is need, a future version of this module may support templating where a document is baked into a list of string snippets, where dynamic content may be injected much faster than what Jinja2 and other regex-based templating engines can do. Other than that, no further development other than maintenance is planned.

Pull requests are still welcome.
