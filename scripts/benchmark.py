"""Benchmark: stateless Template callable vs. building items from scratch.

Run with:

    uv run python benchmark.py

or, after installing the package in editable form:

    python benchmark.py
"""

from __future__ import annotations

import timeit

from html5tagger import Document, E


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
    html_scratch = render_from_scratch(products)

    print(f"Generated HTML length: {len(html_scratch)} bytes")
    print(f"Number of products:    {len(products)}")
    print()

    number = 1000
    t_scratch = timeit.timeit(lambda: render_from_scratch(products), number=number)

    print(f"Single page render time (averaged over {number} renders):")
    print(
        f"  Build from scratch: {t_scratch * 1000 / number:8.3f} ms  ({t_scratch * 1_000_000 / number / len(products):.2f} µs/item)"
    )
    print()


if __name__ == "__main__":
    main()
