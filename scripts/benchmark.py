"""Benchmark: stateless Template callable vs. building items from scratch.

Run with:

    uv run python benchmark.py

or, after installing the package in editable form:

    python benchmark.py
"""

from __future__ import annotations

import timeit

from html5tagger import Document, E, Template


def make_products(count: int = 100) -> list[dict[str, str]]:
    return [
        {
            "Name": f"Product {i}",
            "Desc": f"This is a longer description for product number {i}.",
            "Price": f"${i + 1}.99",
            "Stock": "in stock" if i % 3 else "out of stock",
        }
        for i in range(count)
    ]


def make_item_template() -> Template:
    """A realistic product-card template, defined once."""
    tpl = E.div(class_="card")
    with tpl:
        tpl.h3(class_="title").Name
        tpl.p(class_="desc").Desc
        with tpl.div(class_="meta"):
            tpl.span(class_="price").Price
            tpl.span(class_="stock").Stock
    return tpl @ Template


def render_with_template(products: list[dict[str, str]]) -> str:
    Item = make_item_template()
    doc = Document("Shop")
    doc.ul
    for p in products:
        doc._(Item(**p))
    return str(doc)


def render_from_scratch(products: list[dict[str, str]]) -> str:
    doc = Document("Shop")
    doc.ul
    for p in products:
        item = E.div(class_="card")
        with item:
            item.h3(class_="title")(p["Name"])
            item.p(class_="desc")(p["Desc"])
            with item.div(class_="meta"):
                item.span(class_="price")(p["Price"])
                item.span(class_="stock")(p["Stock"])
        doc._(item)
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
