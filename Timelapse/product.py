import anytree
import httpx


def get_product_dict():
    product_url = "https://www.mosdac.gov.in/gallery/product.json?v=0.4"
    response = httpx.get(url=product_url)
    return response.json()


def parse_dict_into_tree(dictionary: dict, parent: anytree.Node):
    new_parent_node = parent
    for key, value in dictionary.items():
        if isinstance(value, str):
            new_parent_node = anytree.Node(value, type=key, parent=parent)
        elif isinstance(value, list):
            if key == "prodlist":
                for item in value:
                    anytree.Node(
                        item["prod"], pattern=item["pat"], parent=new_parent_node
                    )
            else:
                for item in value:
                    parse_dict_into_tree(item, parent=new_parent_node)
        elif isinstance(value, dict):
            parse_dict_into_tree(value, parent=new_parent_node)


def get_settings_tree():
    settings = anytree.Node("Settings")
    products = get_product_dict()
    for satellite in products:
        parse_dict_into_tree(satellite, parent=settings)
    return settings


if __name__ == "__main__":
    tree = get_settings_tree()
    print(anytree.RenderTree(tree))
