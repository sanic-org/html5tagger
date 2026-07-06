"""Benchmark: stateless Template callable vs. building items from scratch.

Run with:

    uv run python benchmark.py

or, after installing the package in editable form:

    python benchmark.py
"""

from __future__ import annotations

import timeit

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


def main() -> None:
    products = make_products(100)

    # Warm up and verify identical output.
    html_template = render_with_template(products)
    html_scratch = render_from_scratch(products)
    assert html_template == html_scratch, "Outputs differ!"

    print(f"Generated HTML length: {len(html_template)} bytes")
    print(f"Number of products:    {len(products)}")
    print()

    number = 1000
    t_template = timeit.timeit(lambda: render_with_template(products), number=number)
    t_scratch = timeit.timeit(lambda: render_from_scratch(products), number=number)

    print(f"Single page render time (averaged over {number} renders):")
    print(
        f"  Template callable:  {t_template * 1000 / number:8.3f} ms  ({t_template * 1_000_000 / number / len(products):.2f} µs/item)"
    )
    print(
        f"  Build from scratch: {t_scratch * 1000 / number:8.3f} ms  ({t_scratch * 1_000_000 / number / len(products):.2f} µs/item)"
    )
    print()
    print(f"Template is {t_scratch / t_template:.1f}x faster")


if __name__ == "__main__":
    main()
