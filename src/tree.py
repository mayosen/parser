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


def build_tree(url: str, found_links: list) -> dict:
    """
    Builds tree-structure from found links.
    """

    links = [link[link.find("//") + 2:].rstrip("/") for link in found_links]
    branches = []

    for link in links:
        if "/" in link:
            domains, endpoints = link.split("/", maxsplit=1)
            endpoints = endpoints.split("/")
        else:
            domains = link
            endpoints = []

        domains = domains.split(".")[:-2][::-1]
        domains = [domain + ":domain" for domain in domains]
        items = domains + endpoints

        if items:
            branches.append(items)

    tree = {}

    for branch in branches:
        tree = merge_branch(tree, branch)

    return tree
