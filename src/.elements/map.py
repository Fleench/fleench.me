
class Node:
    def __init__(self, name: str, value: str, parent = None):
        self.name = name
        self.children = {}
        self.parent = parent
        self.value = value
    def add_child(self, node):
        self.children[node.name] = node
    def add_parent(self, node):
        self.parent = node
    def add_value(self, value):
        self.value = value
    def get_children(self):
        return self.children
    def get_parent(self):
        return self.parent
    def get_value(self):
        return self.value
    def get_name(self):
        return self.name
    def get_child(self, name):
        return self.children.get(name)
    def __str__(self):
        return str(f"Name: {self.name}, Value: {self.value}, Children: {self.children}")
def print_nodes(t_node: Node, deep:int):
    build = []
    for node in t_node.children.values():
        if not node.name:
            print("Err")
        item = f"{"-"*deep},{node.name},{node.value}"
        build.append(item)
        if node.get_children() is not {}:
            #print("\n")
            x = print_nodes(node, deep+1)
            for item in x:
                build.append(item)
    return build
def main(**config):
    files = config["opages"]
    print("INIT")
    top_node = Node("Top Node", 0)
    for page in files:
        _ = page.parse_content()
        p = page.parsed.metadata
        #print(p)
        if not p.get("hidden",False):
            parts = page.rel_url.split("/")
            cur_node = top_node
            used_parts = []
            for part in parts:
                used_parts.append(part)
                if part.strip() == "":
                    continue
                n_node = cur_node.children.get(part)
                if n_node:
                    cur_node = n_node
                else:
                    n_node = Node(part, "https://flench.me"+"/".join(used_parts), parent = cur_node)
                    cur_node.add_child(n_node)
                    cur_node = n_node
    print("PRINTING NODES")
    z = print_nodes(top_node, 0)
    li = ["<ul style: "column-count: 2">"]
    for item in z:
        it =item.split(",")
        if len(it) == 3:
            tab = len(it[0])
        else:
            tab = 0
        name = it[1]
        value = it[2]
        li.append(f'<li style="margin-left:{tab*15}px"><a href="{value}">{name}</a></li>')
    li.append("</ul")
    return "\n".join(li)
