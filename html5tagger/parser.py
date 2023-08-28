from __future__ import annotations

import re
from typing import List, cast

from .builder import Builder
from .html5 import omit_endtag

DEFAULT = object()
# fmt: off
BASIC_INLINE = {"a", "abbr", "area", "b", "bdi", "bdo", "br", "button", "cite",
                "code", "data", "datalist", "del", "dfn", "em", "i", "input",
                "ins", "kbd", "label", "map", "mark", "meter", "noscript",
                "output", "q", "ruby", "s", "samp", "select", "slot", "small",
                "span", "strong", "sub", "sup", "u", "var", "wbr"}
MEDIA_ELEMENTS = {"audio", "canvas", "embed", "iframe", "img", "object",
                  "picture", "svg", "video"}
FORM_ELEMENTS = {"fieldset", "form", "option", "textarea"}
SCRIPT_SUPPORTING_ELEMENTS = {"script", "template"}
HEADING_ELEMENTS = {"h1", "h2", "h3", "h4", "h5", "h6"}
PHRASING_CONTENT = BASIC_INLINE | MEDIA_ELEMENTS | {"time", "template"}
HEADING_CONTENT = PHRASING_CONTENT | HEADING_ELEMENTS
SECTIONING_CONTENT = {"article", "aside", "nav", "section"}
FLOW_CONTENT = (BASIC_INLINE | MEDIA_ELEMENTS | FORM_ELEMENTS |
                {"address", "article", "aside", "blockquote", "caption",
                 "details", "dialog", "div", "dl", "dt", "fieldset", "figure",
                 "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header",
                 "hgroup", "hr", "main", "math", "menu", "nav", "ol", "p",
                 "pre", "progress", "section", "table", "template", "time",
                 "ul"})
ROOT_CONTENT = {"html", "body"}
TEXT_ALLOWED_ELEMENTS = {"a", "abbr", "address", "article", "aside", "b",
                         "bdi", "bdo", "blockquote", "button", "caption",
                         "cite", "code", "data", "datalist", "dd", "del",
                         "details", "dfn", "div", "dl", "dt", "em", "fieldset",
                         "figcaption", "figure", "footer", "form", "h1", "h2",
                         "h3", "h4", "h5", "h6", "header", "hgroup", "i",
                         "ins", "kbd", "label", "legend", "li", "main", "mark",
                         "menu", "meter", "nav", "noscript", "ol", "option",
                         "output", "p", "pre", "progress", "q", "rb", "rp",
                         "rt", "rtc", "ruby", "s", "samp", "section", "select",
                         "small", "span", "strong", "sub", "summary", "sup",
                         "table", "tbody", "td", "textarea", "tfoot", "th",
                         "thead", "time", "tr", "u", "ul", "var"}
ALLOWED_CONTENT_MODEL = {
    # Transparent items specifically are not included
    #     - a
    #     - ins
    #     - del
    #     - map
    #     - object
    #     - video
    #     - audio
    #     - noscript
    #     - slot
    #     - canvas
    # Also specifically left out are special elements
    #     - template
    "abbr": PHRASING_CONTENT,
    "address": (FLOW_CONTENT - HEADING_CONTENT - SECTIONING_CONTENT - {"address", "header", "footer"}),  # noqa: E501
    "area": None,
    "article": FLOW_CONTENT,
    "aside": FLOW_CONTENT,
    "b": PHRASING_CONTENT,
    "bdi": PHRASING_CONTENT,
    "bdo": PHRASING_CONTENT,
    "blockquote": FLOW_CONTENT,
    "body": FLOW_CONTENT,
    "br": None,
    "br": None,
    "button": PHRASING_CONTENT,
    "canvas": None,
    "caption": FLOW_CONTENT - {"table"},
    "cite": PHRASING_CONTENT,
    "code": PHRASING_CONTENT,
    "col": None,
    "colgroup": {"col", "template"},
    "data": PHRASING_CONTENT,
    "datalist": {"option"} | SCRIPT_SUPPORTING_ELEMENTS | PHRASING_CONTENT,
    "dd": FLOW_CONTENT,
    "details": FLOW_CONTENT - {"summary"},
    "dfn": PHRASING_CONTENT - {"dfn"},
    "dialog": FLOW_CONTENT,
    "div": FLOW_CONTENT | SCRIPT_SUPPORTING_ELEMENTS | {"dt", "dd"},
    "dl": {"dt", "dd", "div"} | SCRIPT_SUPPORTING_ELEMENTS,
    "dt": (FLOW_CONTENT - {"header", "footer"} - SECTIONING_CONTENT - HEADING_CONTENT),  # noqa: E501
    "em": PHRASING_CONTENT,
    "embed": None,
    "fieldset": {"legend"} | FLOW_CONTENT,
    "figcaption": FLOW_CONTENT,
    "figure": {"figcaption"} | FLOW_CONTENT,
    "footer": FLOW_CONTENT - {"header", "footer"},
    "form": FLOW_CONTENT - {"form"},
    "h1": PHRASING_CONTENT,
    "h2": PHRASING_CONTENT,
    "h3": PHRASING_CONTENT,
    "h4": PHRASING_CONTENT,
    "h5": PHRASING_CONTENT,
    "h6": PHRASING_CONTENT,
    "header": FLOW_CONTENT - {"header", "footer"},
    "hgroup": HEADING_ELEMENTS | {"p"},
    "hr": None,
    "i": PHRASING_CONTENT,
    "iframe": None,
    "img": None,
    "input": None,
    "kbd": PHRASING_CONTENT,
    "label": PHRASING_CONTENT - {"label"},
    "legend": PHRASING_CONTENT | HEADING_CONTENT,
    "li": FLOW_CONTENT,
    "link": None,
    "main": FLOW_CONTENT,
    "mark": PHRASING_CONTENT,
    "menu": {"li"} | SCRIPT_SUPPORTING_ELEMENTS,
    "meta": None,
    "meter": PHRASING_CONTENT - {"meter"},
    "nav": FLOW_CONTENT,
    "ol": {"li"} | SCRIPT_SUPPORTING_ELEMENTS,
    "optgroup": {"option"} | SCRIPT_SUPPORTING_ELEMENTS,
    "option": None,
    "output": PHRASING_CONTENT,
    "p": PHRASING_CONTENT,
    "picture": {"source", "img"},
    "pre": PHRASING_CONTENT,
    "progress": PHRASING_CONTENT - {"progress"},
    "q": PHRASING_CONTENT,
    "rp": None,
    "rt": PHRASING_CONTENT,
    "ruby": PHRASING_CONTENT | {"rt", "rp"},
    "s": PHRASING_CONTENT,
    "samp": PHRASING_CONTENT,
    "script": None,
    "search": FLOW_CONTENT,
    "section": FLOW_CONTENT,
    "select": {"option", "optgroup", "hr"},
    "small": PHRASING_CONTENT,
    "source": None,
    "span": PHRASING_CONTENT,
    "strong": PHRASING_CONTENT,
    "style": None,
    "sub": PHRASING_CONTENT,
    "summary": PHRASING_CONTENT | HEADING_CONTENT,
    "sup": PHRASING_CONTENT,
    "table": {"tbody", "thead", "tfoot", "tr", "caption", "colgroup"} | SCRIPT_SUPPORTING_ELEMENTS,  # noqa: E501
    "tbody": {"tr"},
    "td": FLOW_CONTENT,
    "textarea": None,
    "tfoot": {"tr"},
    "th": FLOW_CONTENT - {"header", "footer"} - SECTIONING_CONTENT - HEADING_CONTENT,  # noqa: E501
    "thead": {"tr"},
    "time": PHRASING_CONTENT,
    "title": None,
    "tr": {"th", "td"},
    "track": None,
    "u": PHRASING_CONTENT,
    "ul": {"li"} | SCRIPT_SUPPORTING_ELEMENTS,
    "var": PHRASING_CONTENT,
    "wbr": None,
}
TAG_MATCH_PATTERN = re.compile(r"<(\w+)")
ATTRIBUTE_MATCH_PATTERN = re.compile(r'(\w+)=("[^"]*"|\w+)')
PARSE_TAG_PATTERN = re.compile(r"<(/?)(\w+)|([\w-]+)=('[^']*'|\"[^\"]*\"|\w+)")
# fmt: on


class HTMLNode:
    ROOT_KEY = "__root__"
    DOCTYPE_KEY = "__doctype__"
    COMMENT_KEY = "__comment__"
    TEXT_KEY = "__text__"
    DOCTYPE = "<!DOCTYPE html>"

    __slots__ = (
        "_name",
        "_attributes",
        "_content",
        "_children",
        "_endtag",
        "_parent",
        "_closed",
    )

    def __init__(self, name: str, attributes: dict[str, str]) -> None:
        self._name = name
        self._attributes = attributes
        self._content = ""
        self._children: List[HTMLNode] = []
        self._endtag = name not in omit_endtag
        self._parent: HTMLNode | None = None
        self._closed = False

    def __repr__(self) -> str:
        display = f"{self._name!r}, {self._attributes!r}"
        return f"HTMLNode({display})"

    def __str__(self) -> str:
        return f"<HTMLNode {self._name}>"

    def add_child(self, child: HTMLNode) -> None:
        if self._closed:
            message = (
                f"Tag {self._name!r} is already closed. "
                f"Trying to add {child}"
            )
            raise ValueError(message)
        self._children.append(child)

    def add_text_content(self, text: str) -> None:
        if self._closed:
            message = (
                f"Tag {self._name!r} is already closed. "
                "Trying to add text content."
            )
            raise ValueError(message)
        self._content += text

    def can_contain(self, tag_name: str) -> bool:
        limited = ALLOWED_CONTENT_MODEL.get(self._name, DEFAULT)
        if limited is DEFAULT:
            return True
        if not limited:
            return False
        return tag_name in cast(set[str], limited)

    def __iter__(self):
        return iter(self._children)

    @property
    def children(self):
        return self._children

    @property
    def content(self):
        return self._content

    @property
    def name(self):
        return self._name

    @property
    def opening_tag(self):
        tag = f"<{self._name}"
        if self._attributes:
            tag += " " + " ".join(
                f"{key}={value}" for key, value in self._attributes.items()
            )
        tag += ">"
        return tag

    @property
    def closing_tag(self):
        if not self._endtag:
            return ""
        return f"</{self._name}>"

    @property
    def is_allowed_text_content(self) -> bool:
        return self._name in TEXT_ALLOWED_ELEMENTS

    def close(self) -> None:
        for child in (child for child in self._children if not child._closed):
            child.close()
        self._closed = True


class RootNode(HTMLNode):
    def __init__(self) -> None:
        super().__init__(HTMLNode.ROOT_KEY, {})
        self._endtag = False

    @property
    def opening_tag(self):
        return ""

    def can_contain(self, tag_name: str) -> bool:
        return True


class DoctypeNode(HTMLNode):
    def __init__(self) -> None:
        super().__init__(HTMLNode.DOCTYPE_KEY, {})
        self._endtag = False

    @property
    def opening_tag(self):
        return self.DOCTYPE


class CommentNode(HTMLNode):
    def __init__(self) -> None:
        super().__init__(HTMLNode.COMMENT_KEY, {})
        self._endtag = False

    @property
    def opening_tag(self):
        return f"<!-- {self._content} -->"

    @property
    def content(self):
        return ""


class NodeCreator:
    def create(self, builder: Builder) -> HTMLNode:
        root = self._create_root()
        stack: list[HTMLNode] = [root]

        for piece in [
            p
            for maybe_tag in builder._allpieces
            for p in (
                maybe_tag._allpieces
                if isinstance(maybe_tag, Builder)
                else [maybe_tag]
            )
        ]:
            tag_name, is_closing, attributes = self._parse_tag(piece)

            if piece == HTMLNode.DOCTYPE:
                self._handle_doctype(stack)
                continue
            elif tag_name == HTMLNode.COMMENT_KEY:
                self._handle_comment(piece[4:-3], stack)
                continue
            elif tag_name == HTMLNode.TEXT_KEY:
                self._handle_text(piece, stack)
                continue

            if is_closing:
                self._close_node_by_name(tag_name, stack)
                continue

            self._handle_new_node(tag_name, attributes, stack)

        self._close_node(root, stack)

        return root

    def _create_root(self) -> RootNode:
        return RootNode()

    def _handle_doctype(self, stack: list[HTMLNode]) -> None:
        if len(stack) > 1:
            raise ValueError("Doctype must be the first element")
        doctype = DoctypeNode()
        stack[0].add_child(doctype)

    def _handle_comment(self, text: str, stack: list[HTMLNode]) -> None:
        comment = CommentNode()
        comment.add_text_content(text)
        for node in reversed(stack):
            if not node._closed:
                node.add_child(comment)
                break

    def _handle_text(self, text: str, stack: list[HTMLNode]) -> None:
        for node in reversed(stack):
            if node.is_allowed_text_content:
                node.add_text_content(text)
                break

    def _handle_new_node(
        self, tag_name: str, attributes: dict[str, str], stack: list[HTMLNode]
    ) -> None:
        new_node = HTMLNode(tag_name, attributes)
        for node in reversed(stack):
            if node.can_contain(new_node.name):
                node.add_child(new_node)
                break
            self._close_node(node, stack)
        stack.append(new_node)

    def _close_node(self, node: HTMLNode, stack: list[HTMLNode]) -> None:
        node.close()
        stack.pop()

    def _close_node_by_name(self, name: str, stack: list[HTMLNode]) -> None:
        for node in reversed(stack):
            self._close_node(node, stack)
            if node.name == name:
                break

    @staticmethod
    def _parse_tag(tag: str) -> tuple[str, bool, dict[str, str]]:
        if tag.startswith("<!"):
            return HTMLNode.COMMENT_KEY, False, {}

        matches = list(PARSE_TAG_PATTERN.finditer(tag))
        if not matches:
            return HTMLNode.TEXT_KEY, False, {}

        is_end_tag, tagname = matches[0].groups()[:2]
        attrs = {m.group(3): m.group(4) for m in matches[1:]}

        return tagname, bool(is_end_tag), attrs


class HTMLSyntaxTree:
    def __init__(self, root: HTMLNode, builder: Builder) -> None:
        self._root = root
        self._builder = builder

    def __iter__(self):
        return iter(self._root)

    @property
    def root(self) -> HTMLNode:
        return self._root

    def to_html(self, pretty: bool = False, indent: str = "    ") -> str:
        if not pretty:
            return str(self._builder)
        return self._to_html(self.root, indent)

    def _to_html(self, node: HTMLNode, indent: str, level: int = 0) -> str:
        output = ""
        output += indent * level + node.opening_tag + "\n"
        if node.content:
            output += indent * (level + 1) + node.content + "\n"
        for child in node.children:
            increment = 0 if isinstance(node, (RootNode,)) else 1
            output += self._to_html(child, indent, level + increment)
        if node.closing_tag:
            output += indent * level + node.closing_tag + "\n"
        return output

    def display_tree(self, indent: str = "    "):
        self._display_node(self.root, indent)

    def _display_node(self, node: HTMLNode, indent: str, level: int = 0):
        print(indent * level, node)
        for child in node.children:
            self._display_node(child, indent, level + 1)

    @classmethod
    def create(cls, builder: Builder) -> HTMLSyntaxTree:
        root = NodeCreator().create(builder)
        return cls(root, builder)
