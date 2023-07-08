import json
import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from itertools import islice, chain
from pprint import pprint
from typing import Iterable, Optional

from yarl import URL

from parser.pages import Host

logger = logging.getLogger("parser.tree")


class NodeType(Enum):
    DOMAIN = ("DOMAIN", ".")
    PATH = ("PATH", ",")

    def __init__(self, type_: str, separator: str):
        self.type = type_
        self.separator = separator

    def __repr__(self):
        return f"<NodeType {self.type}, '{self.separator}'>"


@dataclass(kw_only=True, slots=True, unsafe_hash=True)
class Node:
    type: NodeType
    value: str
    parent: Optional["Node"] = None
    children: list["Node"] = field(default_factory=list)

    def __eq__(self, other: object):
        # TODO: test
        if not isinstance(other, Node):
            raise NotImplementedError
        return (self.type, self.value) == (other.type, other.value)

    def __repr__(self):
        return f"<Node {self.type.type}, '{self.value}'>"


"""
def merge_branch(tree: dict, branch: deque[Node]):
    key = branch.popleft()

    if len(branch) == 0:
        if key not in tree:
            tree[key] = None
        return tree

    if key not in tree or tree[key] is None:
        tree[key] = merge_branch({}, branch)
    else:
        merge_branch(tree[key], branch)
        # tree[key].update(temp)

    return tree
"""


def prepare_branches(urls: Iterable[URL]) -> deque[deque[Node]]:
    # TODO: test
    branches = deque()

    for url in urls:
        domains = [Node(type=NodeType.DOMAIN, value=domain) for domain in Host(url.host).parts]
        parts = [Node(type=NodeType.PATH, value=part) for part in islice(url.parts, 1, None) if part]
        branches.append(deque(chain(domains, parts)))

    return branches


def merge_branch(parent: Optional[Node], branch: deque[Node]):
    # TODO: test
    if not branch:
        return parent

    node = branch.popleft()

    if parent is not None:
        existing_child = list(filter(lambda child: node == child, parent.children))

        if existing_child:
            merge_branch(existing_child[0], branch)
        else:
            parent.children.append(node)
            node.parent = parent
            merge_branch(node, branch)
    else:
        merge_branch(node, branch)

    return node


def build_tree(urls: Iterable[URL]) -> Node:
    # TODO: test
    branches = prepare_branches(urls)
    root = merge_branch(None, branches.popleft())

    for branch in branches:
        branch.popleft()
        merge_branch(root, branch)

    return root


def _tree_to_dict(node: Node) -> dict[str, ...]:
    tree = {}

    for child in node.children:
        tree[child.value] = _tree_to_dict(child)

    return tree


def tree_to_dict(root: Node) -> dict[str, ...]:
    return {
        root.value: _tree_to_dict(root)
    }


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)5s.%(msecs)03d [%(levelname)s] %(name)s - %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )

    u = [
        URL(u) for u in [
        "http://www.google.ru/intl/ru/services/",
        "https://www.google.ru",
        "https://www.google.ru/advanced_image_search",
        "https://www.google.ru/advanced_search",
        "https://www.google.ru/imghp",
        "https://www.google.ru/intl/ru/about.html",
        "https://www.google.ru/intl/ru/about/",
        "https://www.google.ru/intl/ru/adwords/express/",
        "https://www.google.ru/intl/ru/adwords/myclientcenter/",
        "https://www.google.ru/intl/ru/analytics/",
        "https://www.google.ru/intl/ru/analytics/features/mobile-app-analytics.html",
        "https://www.google.ru/intl/ru/analytics/tag-manager/",
        "https://www.google.ru/intl/ru/chrome/business/",
        "https://www.google.ru/intl/ru/chrome/business/devices/gettingstarted.html",
        "https://www.google.ru/intl/ru/edu/",
        "https://www.google.ru/intl/ru/insights/",
        "https://www.google.ru/intl/ru/partners/about/",
        "https://www.google.ru/intl/ru/policies/privacy/",
        "https://www.google.ru/intl/ru/policies/terms/",
        "https://www.google.ru/intl/ru/retail/adsense-for-shopping/",
        "https://www.google.ru/intl/ru/retail/merchant-center/",
        "https://www.google.ru/intl/ru/retail/shopping-campaigns/",
        "https://www.google.ru/intl/ru/retail/shopping-partners/",
        "https://www.google.ru/intl/ru/retail/solutions/performance-max/",
        "https://www.google.ru/intl/ru/retail/solutions/shopping-campaigns/",
        "https://www.google.ru/intl/ru/services/",
        "https://www.google.ru/intl/ru/webdesigner/",
        "https://www.google.ru/intl/ru/webmasters/",
        "https://www.google.ru/intl/ru_ru/retail/",
        "https://www.google.ru/preferences",
        "https://www.google.ru/retail/",
        "https://www.google.ru/retail/resources/",
        "https://www.google.ru/retail/solutions/",
        "https://www.google.ru/retail/solutions/manufacturer-center/",
        "https://www.google.ru/retail/solutions/merchant-center/",
        "https://www.google.ru/retail/solutions/performance-max/",
        "https://www.google.ru/retail/solutions/smart-shopping-campaigns",
        "https://www.google.ru/retail/why-google/",
        "https://www.google.ru/safesearch",
        "https://www.google.ru/setprefdomain",
        "https://www.google.ru/url",
        "https://www.google.ru/webhp"
        ]
    ]

    t = build_tree(u)
    d = tree_to_dict(t)
    print(json.dumps(d, indent=4))
