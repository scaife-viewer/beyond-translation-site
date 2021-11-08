"""
Extracted from https://github.com/springload/draftjs_exporter/blob/9cb8643b0bea9bb10c3749f6e2388e324a390f19/example.py
"""
import logging
import re

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML
from draftjs_exporter.types import Element, Props


def blockquote(props: Props) -> Element:
    block_data = props["block"]["data"]

    return DOM.create_element(
        "blockquote", {"cite": block_data.get("cite")}, props["children"]
    )


def list_item(props: Props) -> Element:
    depth = props["block"]["depth"]

    return DOM.create_element(
        "li", {"class": f"list-item--depth-{depth}"}, props["children"]
    )


def ordered_list(props: Props) -> Element:
    depth = props["block"]["depth"]

    return DOM.create_element(
        "ol", {"class": f"list--depth-{depth}"}, props["children"]
    )


def image(props: Props) -> Element:
    return DOM.create_element(
        "img",
        {
            "src": props.get("src"),
            "width": props.get("width"),
            "height": props.get("height"),
            "alt": props.get("alt"),
        },
    )


def link(props: Props) -> Element:
    return DOM.create_element("a", {"href": props["url"]}, props["children"])


def br(props: Props) -> Element:
    """
    Replace line breaks (\n) with br tags.
    """
    # Do not process matches inside code blocks.
    if props["block"]["type"] == BLOCK_TYPES.CODE:
        return props["children"]

    return DOM.create_element("br")


def hashtag(props: Props) -> Element:
    """
    Wrap hashtags in spans with a specific class.
    """
    # Do not process matches inside code blocks.
    if props["block"]["type"] == BLOCK_TYPES.CODE:
        return props["children"]

    return DOM.create_element("span", {"class": "hashtag"}, props["children"])


# See http://pythex.org/?regex=(http%3A%2F%2F%7Chttps%3A%2F%2F%7Cwww%5C.)(%5Ba-zA-Z0-9%5C.%5C-%25%2F%5C%3F%26_%3D%5C%2B%23%3A~!%2C%5C%27%5C*%5C%5E%24%5D%2B)&test_string=search%20http%3A%2F%2Fa.us%20or%20https%3A%2F%2Fyahoo.com%20or%20www.google.com%20for%20%23github%20and%20%23facebook&ignorecase=0&multiline=0&dotall=0&verbose=0
LINKIFY_RE = re.compile(
    r"(http://|https://|www\.)([a-zA-Z0-9\.\-%/\?&_=\+#:~!,\'\*\^$]+)"
)


def linkify(props: Props) -> Element:
    """
    Wrap plain URLs with link tags.
    """
    match = props["match"]
    protocol = match.group(1)
    url = match.group(2)
    href = protocol + url

    if props["block"]["type"] == BLOCK_TYPES.CODE:
        return href

    link_props = {"href": href}

    if href.startswith("www"):
        link_props["href"] = "http://" + href

    return DOM.create_element("a", link_props, href)


def block_fallback(props: Props) -> Element:
    type_ = props["block"]["type"]

    if type_ == "example-discard":
        logging.warning(
            f'Missing config for "{type_}". Discarding block, keeping content.'
        )
        # Directly return the block's children to keep its content.
        return props["children"]
    elif type_ == "example-delete":
        logging.error(f'Missing config for "{type_}". Deleting block.')
        # Return None to not render anything, removing the whole block.
        return None
    else:
        logging.warning(f'Missing config for "{type_}". Using div instead.')
        # Provide a fallback.
        return DOM.create_element("div", {}, props["children"])


def entity_fallback(props: Props) -> Element:
    type_ = props["entity"]["type"]
    key = props["entity"]["entity_range"]["key"]
    logging.warning(f'Missing config for "{type_}", key "{key}".')
    return DOM.create_element("span", {"class": "missing-entity"}, props["children"])


def style_fallback(props: Props) -> Element:
    type_ = props["inline_style_range"]["style"]
    logging.warning(f'Missing config for "{type_}". Deleting style.')
    return props["children"]


def generate_config():
    return {
        # `block_map` is a mapping from Draft.js block types to a definition of their HTML representation.
        # Extend BLOCK_MAP to start with sane defaults, or make your own from scratch.
        "block_map": dict(
            BLOCK_MAP,
            **{
                # The most basic mapping format, block type to tag name.
                BLOCK_TYPES.HEADER_TWO: "h2",
                # Use a dict to define props on the block.
                BLOCK_TYPES.HEADER_THREE: {
                    "element": "h3",
                    "props": {"class": "u-text-center"},
                },
                # Add a wrapper (and wrapper_props) to wrap adjacent blocks.
                BLOCK_TYPES.UNORDERED_LIST_ITEM: {
                    "element": "li",
                    "wrapper": "ul",
                    "wrapper_props": {"class": "bullet-list"},
                },
                # Use a custom component for more flexibility (reading block data or depth).
                BLOCK_TYPES.BLOCKQUOTE: blockquote,
                BLOCK_TYPES.ORDERED_LIST_ITEM: {
                    "element": list_item,
                    "wrapper": ordered_list,
                },
                # Provide a fallback component (advanced).
                BLOCK_TYPES.FALLBACK: block_fallback,
            },
        ),
        # `style_map` defines the HTML representation of inline elements.
        # Extend STYLE_MAP to start with sane defaults, or make your own from scratch.
        "style_map": dict(
            STYLE_MAP,
            **{
                # Use the same mapping format as in the `block_map`.
                "KBD": "kbd",
                # The `style` prop can be defined as a dict, that will automatically be converted to a string.
                "HIGHLIGHT": {
                    "element": "strong",
                    "props": {"style": {"textDecoration": "underline"}},
                },
                # Provide a fallback component (advanced).
                INLINE_STYLES.FALLBACK: style_fallback,
            },
        ),
        "entity_decorators": {
            # Map entities to components so they can be rendered with their data.
            ENTITY_TYPES.IMAGE: image,
            ENTITY_TYPES.LINK: link,
            # Lambdas work too.
            ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element("hr"),
            # Discard those entities.
            ENTITY_TYPES.EMBED: None,
            # Provide a fallback component (advanced).
            ENTITY_TYPES.FALLBACK: entity_fallback,
        },
        "composite_decorators": [
            # Use composite decorators to replace text based on a regular expression.
            {"strategy": re.compile(r"\n"), "component": br},
            {"strategy": re.compile(r"#\w+"), "component": hashtag},
            {"strategy": LINKIFY_RE, "component": linkify},
        ],
        # Specify which DOM backing engine to use.
        "engine": DOM.STRING,
    }


def create_exporter():
    config = generate_config()
    return HTML(config)
