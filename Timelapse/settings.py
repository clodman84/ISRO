import logging

import anytree
import httpx

logger = logging.getLogger("Timelapse.Products")


class Product(anytree.Node):
    """
    meant to be the leaf nodes in the settings tree
    idk just felt like it needed to be its own thing ¯\\_(ツ)_/¯
    """

    def __init__(self, *args, pattern: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern = pattern


def get_product_dict():
    logger.info("GET-ting json of product types...")
    product_url = "https://www.mosdac.gov.in/gallery/product.json?v=0.4"
    response = httpx.get(url=product_url)
    return response.json()


def parse_dict_into_tree(dictionary: dict, parent: anytree.Node):
    """
    The MOSDAC response looks like this:

    [
        {
        'sat': 'EOS-06',  <-- first item is always a string, which is used to name the parent Node while recursing
        'sensor': [
            {
                'sen': 'Scatterometer'
                'type': [
                    {
                    'product': 'Value Added Product'
                    'prodlist': [
                        {
                        'prod': 'Analysed Winds' <-- The leaf nodes of the tree, we dig till we get till here
                        'pat': ...
                        },
                        {
                        'prod': ...
                        'pat': ...
                        }

                    ]
                    }
                    {
                    'product': 'Standard Products'
                    'prodlist': [...]
                    }
                ]
            },
            {
                'sen': ...
                'type': ...
            }
        ]
        },

        {
        'sat': 'INSAT..'
        'sensor': [...]
        },

        ...
    ]

    The code below turns this into a tree into a tree
    """
    new_parent_node = parent
    for key, value in dictionary.items():
        if isinstance(value, str):
            new_parent_node = anytree.Node(value, type=key, parent=parent)
        elif isinstance(value, list):
            if key == "prodlist":
                for item in value:
                    Product(item["prod"], pattern=item["pat"], parent=new_parent_node)
            else:
                for item in value:
                    parse_dict_into_tree(item, parent=new_parent_node)
        elif isinstance(value, dict):
            parse_dict_into_tree(value, parent=new_parent_node)


def make_settings_tree():
    settings = anytree.Node("Settings")
    products = get_product_dict()
    logger.debug("Building settings tree for:")
    for satellite in products:
        logger.debug(f"\t{satellite['sat']}")
        parse_dict_into_tree(satellite, parent=settings)
    logger.info("Done")
    return settings


if __name__ == "__main__":
    tree = make_settings_tree()
    print(anytree.RenderTree(tree))
