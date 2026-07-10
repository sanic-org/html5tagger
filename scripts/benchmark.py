#!/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [ "html5tagger", "jinja2" ]
# tool.uv.sources.html5tagger = { path = "../", editable = true }
# ///
from __future__ import annotations

import timeit
from pathlib import Path

try:
    import jinja2
except ImportError:
    jinja2 = None

from html5tagger import Document, E, Template

# Pre-construct reusable templates once, in the style of the README example.
# A realistic product card with several nested elements and attributes.
Item = Template(
    E.article(class_="product-card", data_sku=E.SKU)(
        E.div(class_="product-image")(
            E.span(class_="placeholder")(E.Initial),
        ),
        E.div(class_="product-body")(
            E.h3(class_="product-name")(E.Name),
            E.p(class_="product-desc")(E.Desc),
            E.div(class_="product-meta")(
                E.span(class_="product-price")(E.Price),
                E.span(class_="product-stock")(E.Stock),
            ),
            E.a(class_="product-detail", href="/product/view")("Details"),
        ),
    )
)


# A realistic page shell: header, navigation, sidebar, main content, footer.
# Only the Items slot is dynamic; everything else is prebuilt static HTML.
Page = Template(
    Document(
        "Shop",
        lang="en",
        _urls=("style.css", "app.js"),
    )
    .header(class_="site-header")(
        E.div(class_="container")(
            E.a(class_="logo", href="/")("Shop"),
            E.nav(class_="main-nav")(
                E.a(href="/")("Home"),
                E.a(href="/products")("Products"),
                E.a(href="/about")("About"),
                E.a(href="/contact")("Contact"),
            ),
        ),
    )
    .main(class_="main")(
        E.div(class_="container")(
            E.aside(class_="sidebar")(
                E.h2("Categories"),
                E.ul(
                    E.li("Electronics"),
                    E.li("Clothing"),
                    E.li("Home & Garden"),
                    E.li("Sports"),
                    E.li("Books"),
                ),
            ),
            E.section(class_="content")(
                E.h1("Products"),
                E.div(class_="product-grid").Items,
            ),
        ),
    )
    .footer(class_="site-footer")(
        E.div(class_="container")(
            E.p("© 2026 Shop. All rights reserved."),
        ),
    )
)

# Equivalent Jinja template for comparison (autoescape enabled).
# Loaded from a file and pretty-formatted, as in normal Jinja use.
if jinja2 is not None:
    _jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(__file__).parent),
        autoescape=True,
    )
    JinjaPage = _jinja_env.get_template("benchmark.html.jinja")
else:
    JinjaPage = None


def make_products(count: int = 100) -> list[dict[str, str]]:
    categories = ("Electronics", "Clothing", "Home", "Sports", "Books")
    return [
        {
            "Initial": categories[i % len(categories)][0],
            "Name": f"Product {i}",
            "Desc": f"This is a longer description for product number {i}.",
            "Price": f"${i + 1}.99",
            "Stock": "in stock" if i % 3 else "out of stock",
            "SKU": f"SKU-{i}",
        }
        for i in range(count)
    ]


def render_with_template(products: list[dict[str, str]]) -> str:
    """Render using pre-built templates."""
    return Page(Items=[Item(**p) for p in products])


def render_with_jinja(products: list[dict[str, str]]) -> str:
    """Render the same page using a pre-loaded Jinja template (autoescape enabled)."""
    assert JinjaPage is not None, "Package jinja2 is not installed`"
    return JinjaPage.render(products=products)


def render_with_jinja_runtime(products: list[dict[str, str]]) -> str:
    """Render the same page by loading the Jinja template at runtime each call."""
    assert jinja2 is not None, "Package jinja2 is not installed`"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(__file__).parent),
        autoescape=True,
    )
    template = env.get_template("benchmark.html.jinja")
    return template.render(products=products)


def render_from_scratch(products: list[dict[str, str]]) -> str:
    doc = Document(
        "Shop",
        lang="en",
        _urls=("style.css", "app.js"),
    )

    with doc.header(class_="site-header"), doc.div(class_="container"):
        doc.a(class_="logo", href="/")("Shop")
        with doc.nav(class_="main-nav"):
            doc.a(href="/")("Home")
            doc.a(href="/products")("Products")
            doc.a(href="/about")("About")
            doc.a(href="/contact")("Contact")

    with doc.main(class_="main"), doc.div(class_="container"):
        with doc.aside(class_="sidebar"):
            doc.h2("Categories")
            doc.ul
            doc._(E.li("Electronics"), E.li("Clothing"), E.li("Home & Garden"))
            doc._(E.li("Sports"), E.li("Books"))
        with doc.section(class_="content"):
            doc.h1("Products")
            doc.div(class_="product-grid")
            for p in products:
                item = E.article(class_="product-card", data_sku=p["SKU"])
                with item:
                    with item.div(class_="product-image"):
                        item.span(class_="placeholder")(p["Initial"])
                    with item.div(class_="product-body"):
                        item.h3(class_="product-name")(p["Name"])
                        item.p(class_="product-desc")(p["Desc"])
                        with item.div(class_="product-meta"):
                            item.span(class_="product-price")(p["Price"])
                            item.span(class_="product-stock")(p["Stock"])
                        item.a(class_="product-detail", href="/product/view")("Details")
                doc._(item)

    with doc.footer(class_="site-footer"), doc.div(class_="container"):
        doc.p("© 2026 Shop. All rights reserved.")

    return str(doc)


def render_with_selectors(products: list[dict[str, str]]) -> str:
    """Same document as render_from_scratch, using CSS selector syntax for static attributes."""
    doc = Document(
        "Shop",
        lang="en",
        _urls=("style.css", "app.js"),
    )

    with doc.header[".site-header"], doc.div[".container"]:
        doc.a[".logo"](href="/")("Shop")
        with doc.nav[".main-nav"]:
            doc.a(href="/")("Home")
            doc.a(href="/products")("Products")
            doc.a(href="/about")("About")
            doc.a(href="/contact")("Contact")

    with doc.main[".main"], doc.div[".container"]:
        with doc.aside[".sidebar"]:
            doc.h2("Categories")
            doc.ul
            doc._(E.li("Electronics"), E.li("Clothing"), E.li("Home & Garden"))
            doc._(E.li("Sports"), E.li("Books"))
        with doc.section[".content"]:
            doc.h1("Products")
            doc.div[".product-grid"]
            for p in products:
                item = E.article[".product-card"](data_sku=p["SKU"])
                with item:
                    with item.div[".product-image"]:
                        item.span[".placeholder"](p["Initial"])
                    with item.div[".product-body"]:
                        item.h3[".product-name"](p["Name"])
                        item.p[".product-desc"](p["Desc"])
                        with item.div[".product-meta"]:
                            item.span[".product-price"](p["Price"])
                            item.span[".product-stock"](p["Stock"])
                        item.a[".product-detail"](href="/product/view")("Details")
                doc._(item)

    with doc.footer[".site-footer"], doc.div[".container"]:
        doc.p("© 2026 Shop. All rights reserved.")

    return str(doc)


def main() -> None:
    products = make_products(100)

    # Warm up and verify identical output.
    html_template = render_with_template(products)
    html_scratch = render_from_scratch(products)
    html_selectors = render_with_selectors(products)
    assert html_template == html_scratch == html_selectors, "Outputs differ!"

    html_jinja = render_with_jinja(products) if jinja2 is not None else None
    jinja_len = f" (Jinja {len(html_jinja)} bytes)" if html_jinja is not None else ""
    print(f"Generated HTML length:  {len(html_template)} bytes{jinja_len}")
    print(f"Product items on page:  {len(products)}\n")
    number = 1000
    t_full = timeit.timeit(lambda: render_from_scratch(products), number=number)
    t_full_selectors = timeit.timeit(lambda: render_with_selectors(products), number=number)
    t_template = timeit.timeit(lambda: render_with_template(products), number=number)

    def row(label: str, t: float) -> str:
        return f"  {label:<29} {t * 1000 / number:8.3f} ms  ({t * 1_000_000 / number / len(products):2.0f} µs/item)"

    print(f"Single page render time (averaged over {number} renders):")
    print(row("Full generation:", t_full))
    print(row("Full generation w/ selectors:", t_full_selectors))
    print(row("Template:", t_template))

    t_jinja_file = t_jinja_preloaded = 0
    j2 = ""
    if jinja2 is not None:
        print("\nJinja for comparison:")
        t_jinja_file = timeit.timeit(lambda: render_with_jinja_runtime(products), number=number)
        print(row("Template file:", t_jinja_file))
        t_jinja_preloaded = timeit.timeit(lambda: render_with_jinja(products), number=number)
        print(row("Template preloaded:", t_jinja_preloaded))
        j2 = f", and {(t_jinja_preloaded / t_template):.1f}x faster than Jinja (preloaded; {(t_jinja_file / t_template):.1f}x file)"

    print()
    print(f"Templating is {(t_full / t_template):.1f}x faster than full document generation{j2}")


if __name__ == "__main__":
    main()
