from collections import deque

from yarl import URL

from parser.tree import Node, NodeType, prepare_branches, merge_branch, build_tree, tree_to_dict


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

    def test_already_existing_child(self):
        grandpa = Node.domain("grandpa")
        parent = Node.domain("parent")
        child = Node.path("child")
        grandpa.children = [parent]
        parent.parent = grandpa
        merge_branch(grandpa, deque([parent, child]))
        assert parent.children == [child]
        assert child.parent == parent

    def test_new_child(self):
        parent = Node.domain("domain")
        child = Node.path("child")
        branch = deque([child])
        merge_branch(parent, branch)
        assert parent.children == [child]
        assert child.parent == parent

    def test_none_parent(self):
        domain = Node.domain("org")
        branch = deque([
            domain
        ])
        root = merge_branch(None, branch)
        assert root is domain


def test_build_tree():
    urls = [
        URL(u) for u in [
            "https://google.com",
            "https://google.com/privacy",
            "https://blog.google.com",
            "https://blog.google.com/about",
            "https://www.google.com/policy",
        ]
    ]
    tree = build_tree(urls)
    assert tree == Node.domain("com")
    assert tree.children == [Node.domain("google")]
    assert tree.children[0].children == [
        Node.path("privacy"),
        Node.domain("blog"),
        Node.domain("www"),
    ]
    assert tree.children[0].children[0].children == []
    assert tree.children[0].children[1].children == [Node.path("about")]
    assert tree.children[0].children[2].children == [Node.path("policy")]


def test_tree_to_dict():
    com = Node.domain("com")
    google = Node.domain("google")
    privacy = Node.path("privacy")
    blog = Node.domain("blog")
    about = Node.path("about")
    www = Node.domain("www")
    policy = Node.path("policy")

    com.children = [google]
    google.children = [
        privacy,
        blog,
        www
    ]
    blog.children = [about]
    www.children = [policy]
    tree = com

    assert tree_to_dict(tree) == {
        "com": {
            "google": {
                "privacy": {},
                "www": {
                    "policy": {}
                },
                "blog": {
                    "about": {}
                }
            }
        }
    }
