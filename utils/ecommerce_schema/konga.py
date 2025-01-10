from typing import Dict, Any

def get_konga_product_list_schema() -> Dict[str, Any]:
    return {
        "name": "Konga Product List Schema",
        "baseSelector": "div[class*='bbe45_3oExY']",  # Product card container
        "waitForSelector": "div[class*='_588b5_3MtNs']",  # Main products container
        "waitForTimeout": 5000,  # Wait up to 5 seconds for content to load
        "fields": [
            {
                "name": "name",
                "selector": "h3[class*='af885_1iPzH']",
                "type": "text"
            },
            {
                "name": "source",
                "default": "konga"
            },
            {
                "name": "current_price",
                "selector": "span[class*='d7c0f_sJAqi']",
                "type": "text"
            },
            {
                "name": "original_price",
                "selector": "span[class*='f6eb3_1MyTu']",
                "type": "text",
                "optional": True
            },
            {
                "name": "discount",
                "selector": "span[class*='_6c244_q2qap']",
                "type": "text",
                "optional": True
            },
            {
                "name": "url",
                "selector": "a[href*='/product/']",
                "type": "attribute",
                "attribute": "href"
            },
            {
                "name": "image",
                "selector": "img[class*='f5e10_VzEXF']",
                "type": "attribute",
                "attribute": "src",
                "fallback": {
                    "attribute": "data-src"
                }
            },
            {
                "name": "seller",
                "selector": "span[class*='_7cc7b_23GsY'] a",
                "type": "text",
                "optional": True
            }
        ]
    }

def get_konga_product_detail_schema() -> Dict[str, Any]:
    return {
        "name": "Konga Product Detail Schema",
        "baseSelector": "div[class*='_00895_34MT4']",
        "waitForSelector": "div[class*='_00895_34MT4']",
        "waitForTimeout": 5000,  # Wait up to 5 seconds for content to load
        "fields": [
            {
                "name": "name",
                "selector": "h4[class*='_24849_2Ymhg']",
                "type": "text"
            },
            {
                "name": "current_price",
                "selector": "span[class*='_678e4_e6nqh']",
                "type": "text"
            },
            {
                "name": "original_price",
                "selector": "span[class*='_10344_3PAla']",
                "type": "text",
                "optional": True
            },
            {
                "name": "discount",
                "selector": "span[class*='_678e4_e6nqh']",
                "type": "text",
                "optional": True
            },
            {
                "name": "image",
                "selector": "div[class*='_7f96a_3PgMp'] img",
                "type": "attribute",
                "attribute": "src",
                "fallback": {
                    "attribute": "data-src"
                }
            },
            {
                "name": "images",
                "type": "list",
                "selector": "div[class*='bf1a2_3kz7s'] img",
                "fields": [
                    {
                        "name": "url",
                        "type": "attribute",
                        "attribute": "src",
                        "fallback": {
                            "attribute": "data-src"
                        }
                    }
                ]
            },
            {
                "name": "specifications",
                "type": "list",
                "selector": "table[class*='_3a09a_1e-gU'] tr",
                "fields": [
                    {
                        "name": "label",
                        "selector": "td:first-child",
                        "type": "text"
                    },
                    {
                        "name": "value",
                        "selector": "td:last-child",
                        "type": "text"
                    }
                ]
            },
            {
                "name": "description",
                "selector": "div[class*='_96f69_2zWIQ'] p",
                "type": "text",
                "optional": True
            }
        ]
    } 