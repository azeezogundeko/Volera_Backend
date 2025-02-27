from typing import Dict, Any, List, Optional
from utils.ecommerce_manager import EcommerceManager
from utils.rerank import ReRanker
from utils.logging import logger

# Initialize shared instances
reranker = ReRanker()

async def search_and_process_products(
    ecommerce_manager: EcommerceManager,
    query: str,
    max_results: int = 5,
    site: str = "all"
) -> List[Dict[str, Any]]:
    """
    Search for products and process the results.
    This function is used by both the product services and agent tools.
    """
    try:
        integrations = ecommerce_manager._integrations.values()
        if site and site != "all":
            integrations = [i for i in integrations if i.matches_url(site)]
            if not integrations:
                logger.info(f"No supported integration found for site: {site}")
                return []

        # Get results from integrations
        results = []
        for integration in integrations:
            try:
                if integration.integration_type in ["api", "graphql"]:
                    products = await integration.get_product_list(
                        url="",
                        search=query,
                        page=0,
                        limit=max_results
                    )
                    if isinstance(products, dict):
                        products = products.get("products", [])
                    for p in products:
                        p["source"] = integration.name
                    results.extend(products)
            except Exception as e:
                logger.error(f"Error with {integration.name}: {str(e)}")
                continue

        # Filter and process results
        excluded_sources = {"failed_extraction", "unsupported_site", "error"}
        successful_products = [
            p for p in results
            if isinstance(p, dict) and p.get("source") not in excluded_sources
        ]

        if successful_products:
            return await reranker.rerank(query, successful_products)

        return []
    except Exception as e:
        logger.error(f"Error in search_and_process_products: {str(e)}")
        return [] 