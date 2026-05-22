from pathlib import Path


class Node:
    def __init__(self, name: str, value: str, parent=None):
        self.name = name
        self.children = {}
        self.parent = parent
        self.value = value

    def add_child(self, node):
        self.children[node.name] = node

    def get_children(self):
        return self.children


def _page_url(page, src_dir: Path, out_dir: Path) -> str:
    relative = page.md_file.relative_to(src_dir)
    if relative.as_posix() == "index.md":
        output_path = out_dir / "index.html"
    else:
        output_path = out_dir / relative.with_suffix("") / "index.html"

    rel_url = "/" + output_path.relative_to(out_dir).as_posix()
    if rel_url.endswith("/index.html"):
        rel_url = rel_url[: -len("index.html")]
    return rel_url


def _walk_nodes(node: Node, depth: int = 0):
    for child in node.children.values():
        yield depth, child.name, child.value
        yield from _walk_nodes(child, depth + 1)


def main(**config):
    files = config["opages"]
    src_dir = Path(config["src_dir"])
    out_dir = Path(config["out_dir"])
    parse_frontmatter = config["config"]["API"]["parse_frontmatter"]

    top_node = Node("Top Node", "")
    for page in files:
        parsed = parse_frontmatter(page.md_file.read_text(encoding="utf-8"))
        if parsed.metadata.get("hidden", False):
            continue

        cur_node = top_node
        used_parts = []
        for part in _page_url(page, src_dir, out_dir).split("/"):
            used_parts.append(part)
            if not part.strip():
                continue

            next_node = cur_node.children.get(part)
            if next_node is None:
                next_node = Node(part, "/".join(used_parts), parent=cur_node)
                cur_node.add_child(next_node)
            cur_node = next_node

    items = ['<ul style="columns: 2;-webkit-columns: 2;-moz-columns: 2;column-width: 5px">']
    for depth, name, value in _walk_nodes(top_node):
        items.append(f'<li style="margin-left:{depth * 15}px"><a href="{value}">{name}</a></li>')
    items.append("</ul>")
    return "\n".join(items)
