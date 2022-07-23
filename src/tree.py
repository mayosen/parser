from yarl import URL

from scantools import Host


def merge_branch(tree: dict, branch: list) -> dict:
    """
    Merges branch as a list into nested dictionary.
    """

    if len(branch) == 1:
        temp = {branch[0]: None}
        tree.update(temp)
        return tree

    key = branch.pop(0)

    if key not in tree or tree[key] is None:
        tree[key] = merge_branch({}, branch)
    else:
        temp = merge_branch(tree[key], branch)
        tree[key].update(temp)

    return tree


def build_tree(main_url: str, found: list[str]) -> dict:
    """
    Builds tree-structure from found links.
    """

    main_host = Host(URL(main_url).host).rebuild()
    branches = []

    for link in found:
        url = URL(link)
        host = Host(url.host)
        domains = [f"domain:{domain}" for domain in host.domains[2:]]
        parts = list(filter(lambda item: item, url.parts[1:]))
        items = domains + parts

        if items:
            branches.append(items)

    tree = {}

    for branch in branches:
        tree = merge_branch(tree, branch)

    return {
        main_host: tree,
    }
