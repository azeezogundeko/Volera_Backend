from typing import Dict, Any
    
from .ecommerce.types import ProductDetailSchema, ProductListSchema


def get_product_list_schema() -> Dict[str, Any]:
    """Schema for extracting product listings from e-commerce sites."""
    return {
        "name": "Product List Schema",
        "baseSelector": ".product-list, .products, .product-grid, article.prd._fb.col.c-prd, .b-list-advert__gallery__item",  # Added Jiji's selector
        "fields": [
                    {
                        "name": ProductListSchema.name,
                "selector": ".product-name, .product-title, h2, h3.name, .qa-advert-title",  # Added Jiji's selector
                        "type": "text"
                    },
                    {
                        "name": ProductListSchema.current_price,
                "selector": ".price, .product-price, .current-price, div.prc, .qa-advert-price",  # Added Jiji's selector
                        "type": "text"
                    },
                    {
                        "name": ProductListSchema.original_price,
                "selector": ".original-price, .old-price, .regular-price, .current-price, .old",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": ProductListSchema.discount,
                "selector": ".discount, .savings, .price-off, ._dsct",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": ProductListSchema.image,
                "selector": "img.img[data-src], img.img[src*='jumia'], img[data-nuxt-pic], img",  # Prioritize data-src for Jumia
                        "type": "attribute",
                "attribute": "data-src",  # Try data-src first
                "fallback": {  # Fallback to src if data-src is empty or not found
                    "attribute": "src",
                    "filter": "not_contains:data:image/gif;base64"  # Filter out base64 images
                }
            },
            {
                "name": ProductListSchema.description,
                "selector": ".b-list-advert-base__description-text",  # Added Jiji's description
                "type": "text",
                "optional": True
            },
            {
                "name": ProductListSchema.location,
                "selector": ".b-list-advert__region__text",  # Added Jiji's location
                "type": "text",
                "optional": True
            },
            {
                "name": ProductListSchema.condition,
                "selector": ".b-list-advert-base__item-attr",  # Added Jiji's condition
                "type": "text",
                "optional": True
                    },
                    {
                        "name": ProductListSchema.rating,
                "selector": ".rating, .stars, .product-rating, .stars._s",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": ProductListSchema.reviews_count,
                        "selector": ".review-count, .rating-count",
                        "type": "text",
                        "optional": True
            },
            {
                "name": ProductListSchema.url,
                "selector": "a.core, a.b-list-advert-base",  # Added Jiji's URL selector
                "type": "attribute",
                "attribute": "href",
                "optional": True
            },
            {
                "name": ProductListSchema.brand,
                "selector": "[data-ga4-item_brand], .brand",
                "type": "attribute",
                "attribute": "data-ga4-item_brand",
                "optional": True
            },
            {
                "name": ProductListSchema.category,
                "selector": "[data-ga4-item_category], .category",
                "type": "attribute",
                "attribute": "data-ga4-item_category",
                "optional": True
            },
            {
                "name": ProductListSchema.subcategory,
                "selector": "[data-ga4-item_category2], .subcategory",
                "type": "attribute",
                "attribute": "data-ga4-item_category2",
                "optional": True
            },
            {
                "name": ProductListSchema.product_id,
                "selector": "[data-ga4-item_id], [data-product-id]",
                "type": "attribute",
                "attribute": "data-ga4-item_id",
                "optional": True
            }
        ]
    }

def get_konga_product_list_schema() -> Dict[str, Any]:
    return {
        "name": "Konga Product List Schema",
        "baseSelector": ".product-list, .products, .product-grid, article.prd._fb.col.c-prd, .b-list-advert__gallery__item",
        "fields": []
    }


def get_jiji_product_detail_schema() -> Dict[str, Any]:
    """Schema for extracting detailed product information from Jiji."""
    return {
        "name": "Jiji Product Detail Schema",
        "baseSelector": ".b-advert-seller-info-wrapper",
        "fields": [
            {
                "name": ProductDetailSchema.source,
                "type": "text",   
                "default": "Jiji"
            },
            {
                "name": ProductDetailSchema.images,
                "selector": "div.b-slider-image__wrapper, picture",  # Updated to target the wrapper
                "type": "nested",
                "fields": [
                    {
                        "name": ProductDetailSchema.url,
                        "selector": "img.b-slider-image.qa-carousel-slide",
                        "type": "attribute",
                        "attribute": "src"
                    },
                    {
                        "name": ProductDetailSchema.alt,
                        "selector": "img.b-slider-image.qa-carousel-slide",
                        "attribute": "alt",
                        "type": "attribute",
                        "optional": True
                    },   
                ]
            },
            # {
            #     "name": "img_list",
            #     "selector": ".qa-carousel-thumbnails picture",
            #     "type": "list",
            #     "fields": [
            #             {
            #                 "name": "webp_srcset",
            #                 "selector": "source[type='image/webp']",
            #                 "type": "attribute",
            #                 "attribute": "srcset",
            #                 "optional": True
            #             },
            #             {
            #                 "name": "img_srcset",
            #                 "selector": "img",
            #                 "type": "attribute",
            #                 "attribute": "srcset",
            #                 "optional": True
            #             },
            #         ]
            #     }
            # },
            {
                "name": ProductDetailSchema.specifications,
                "selector": ".b-advert-attribute",
                "type": "list",
                "fields": [
                    {
                        "name": ProductDetailSchema.key,
                        "selector": ".b-advert-attribute__key",
                        "type": "text"
                    },
                    {
                        "name": ProductDetailSchema.value,
                        "selector": ".b-advert-attribute__value",
                        "type": "text"
                    }
                ]
            },
            {
                "name": ProductDetailSchema.description,
                "selector": ".qa-description-text",
                "type": "text"
            },
        ]
    }

def get_jumia_product_detail_schema() -> Dict[str, Any]:
    return {
        "name": "Product Detail Schema",
        "baseSelector": "main.-pvs",
        "fields": [
            {
                "name": ProductDetailSchema.category,
                "type": "text",
                "selector": ".brcbs a.cbs:nth-child(3)"
            },
            {
                "name": ProductDetailSchema.product_basic_info,
                "selector": "section.col12.-df.-d-co",
                "type": "nested",
                "fields": [
                    {
                        "name": ProductDetailSchema.name,
                        "selector": "h1.-fs20.-pts.-pbxs",
                        "type": "text"
                    },
                    {
                        "name": ProductDetailSchema.current_price,
                        "selector": "span.-b.-ubpt.-tal.-fs24.-prxs",
                        "type": "text"
                    },
                    {
                        "name": ProductDetailSchema.original_price,
                        "selector": "span.-tal.-gy5.-lthr.-fs16.-pvxs.-ubpt",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": ProductDetailSchema.brand,
                        "selector": "div.-pvxs a:nth-child(1)",
                        "type": "text"
                    },
                    {
                        "name": ProductDetailSchema.discount,
                        "selector": ".bdg._dsct, [data-disc]",  # Match either class combination or data-disc attribute
                        "type": "text",
                        "fallback": {  # Add fallback to check data-disc attribute
                            "attribute": "data-disc"
                        },
                        "optional": True
                    },
                    {
                        "name": ProductDetailSchema.rating,
                        "selector": ".stars._m._al",  # Updated to match the exact classes
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": ProductDetailSchema.reviews_count,
                        "selector": "a._more",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": ProductDetailSchema.images,
                        "selector": ".sldr._img._prod a.itm",  # Target the anchor tags containing images
                        "type": "list",
                        "fields": [
                            {
                                "name": ProductDetailSchema.url,
                                "selector": "img",
                                "type": "attribute",
                                "attribute": "data-src",
                                "fallback": {
                                    "attribute": "src",
                                    "filter": "not_contains:data:image/gif;base64"
                                }
                            },
                            {
                                "name": ProductDetailSchema.zoom_url,
                                "type": "attribute",
                                "attribute": "href"
                            },
                            {
                                "name": ProductDetailSchema.alt,
                                "selector": "img",
                                "type": "attribute",
                                "attribute": "alt",
                                "optional": True
                            }
                        ]
                    }
                ]
            },
            {
                "name": ProductDetailSchema.product_details,
                "selector": "section.card.aim.-mtm.-fs16",
                "type": "nested_list",
                "fields": [
                    {
                        "name": ProductDetailSchema.features,
                        "selector": "div.row.-pas > article:nth-child(1) > div > div > ul > li",
                        "type": "list",
                        "fields": [
                            {
                                "name": ProductDetailSchema.feature,
                                "type": "text",
                               
                            },
                        ]
                    },
                    {
                        "name": ProductDetailSchema.specifications,
                        "selector": ".card-b:contains('Specifications') ul.-pvs.-mvxs.-phm.-lsn li.-pvxs",
                        "type": "list",
                        "fields": [
                            {
                                "name": ProductDetailSchema.value,
                                "type": "text",
                                
                            },
                            {
                                "name": ProductDetailSchema.label,
                                "type": "text",
                                "selector": "span.-b",
                            },
                        ]
                    },
                ]
            },
            {
                "name": ProductDetailSchema.product_reviews,
                "selector": "div.cola.-phm.-df.-d-co",
                "type": "nested",
                "fields": [
                    {
                        "name": ProductDetailSchema.reviews,
                        "selector": "article.-pvs.-hr._bet",
                        "type": "list",
                        "fields": [
                            {
                                    "name": ProductDetailSchema.rating,
                                "type": "text",
                                "selector": "div.stars._m._al.-mvs"
                            },
                            {
                                "name": ProductDetailSchema.title,
                                "type": "text",
                                "selector": "h3.-m.-fs16.-pvs"
                            },
                            {
                                "name": ProductDetailSchema.comment,
                                "type": "text",
                                "selector": "p.-pvs"
                            },
                            {
                                "name": ProductDetailSchema.date,
                                "type": "text",
                                "selector": "div.-df.-j-bet.-i-ctr.-gy5 span:first-child"
                            },
                            {
                                "name": ProductDetailSchema.author,
                                "type": "text",
                                "selector": "div.-df.-j-bet.-i-ctr.-gy5 span:nth-child(2)"
                            },
                            {
                                "name": ProductDetailSchema.verified,
                                "type": "boolean",
                                "selector": "svg.ic.-f-gn5",
                                "value": True
                            }
                        ]
                    }
                ]
            }
        ]
    }


