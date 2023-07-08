from collections import deque

from yarl import URL

from parser.tree import Node, NodeType, prepare_branches, merge_branch


class TestNode:
    def test_equals(self):
        assert Node(type=NodeType.PATH, value="value") == Node(type=NodeType.PATH, value="value")
        assert Node(type=NodeType.DOMAIN, value="value") != Node(type=NodeType.PATH, value="value")
        assert Node(type=NodeType.PATH, value="value") != Node(type=NodeType.PATH, value="diff")


def test_prepare_branches():
    urls = [
        URL(u) for u in [
            "https://example.org",
            "https://example.org/first",
            "https://example.org/first/nested",
            "https://level.example.org/first",
            "https://level.example.org/second",
        ]
    ]

    expected = [
        deque([
            Node.domain("org"),
            Node.domain("example"),
        ]),
        deque([
            Node.domain("org"),
            Node.domain("example"),
            Node.path("first"),
        ]),
        deque([
            Node.domain("org"),
            Node.domain("example"),
            Node.path("first"),
            Node.path("nested"),
        ]),
        deque([
            Node.domain("org"),
            Node.domain("example"),
            Node.domain("level"),
            Node.path("first"),
        ]),
        deque([
            Node.domain("org"),
            Node.domain("example"),
            Node.domain("level"),
            Node.path("second"),
        ]),
    ]

    actual = list(prepare_branches(urls))
    assert actual == expected


class TestMergeBranch:
    def test_empty_branch(self):
        assert merge_branch(None, deque()) is None
        node = Node.domain("value")
        assert merge_branch(node, deque()) is node

    def test_existing_child(self):
        pass

    def test_new_child(self):
        pass

    def test_none_parent(self):
        domain = Node.domain("org")
        branch = deque([
            domain
        ])
        root = merge_branch(None, branch)
        assert root is domain

    def test_recursion(self):
        pass


def test_build_tree():
    pass


def test_tree_to_dict():
    pass
