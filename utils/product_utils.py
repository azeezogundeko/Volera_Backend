from typing import Dict, Any, List, Optional
import asyncio

from agents.tools.search import search_tool

from utils.ecommerce_manager import EcommerceManager
from utils.rerank import ReRanker
from utils.logging import logger

# Initialize shared instances
reranker = ReRanker()

async def search_and_process_products(
    ecommerce_manager: EcommerceManager,
    query: str,
    page: int = 1,
    sort: str = None,
    max_results: int = 5,
    site: str = "all",
    limit: int = 40,
    bypass_cache: bool = False
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

        # Prepare integrations
        direct_integrations = [i for i in integrations if i.integration_type in ["api", "graphql"]]
        scraping_integrations = [i for i in integrations if i.integration_type == "scraping"]
        all_products = []

        # Parallel processing for direct integrations
        if direct_integrations:
            direct_tasks = [
                integration.get_product_list(
                    url="",
                    search=query,
                    page=page,
                    limit=limit,
                    sort=sort,
                    bypass_cache=bypass_cache
                ) for integration in direct_integrations
            ]
            direct_results = await asyncio.gather(*direct_tasks, return_exceptions=True)
            
            for integration, result in zip(direct_integrations, direct_results):
                if isinstance(result, Exception):
                    logger.error(f"Error with {integration.name}: {str(result)}")
                    continue
                products = []
                if isinstance(result, dict):
                    products = result.get("products", [])
                elif isinstance(result, list):
                    products = result
                for p in products:
                    p["source"] = integration.name
                all_products.extend(products)

        # Parallel processing for scraping integrations
        if scraping_integrations:
            # Parallel search across all scraping sites
            search_tasks = [
                search_tool.search_products(query, site="|".join(integration.url_patterns))
                for integration in scraping_integrations
            ]
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process search results
            all_search_results = []
            for integration, result in zip(scraping_integrations, search_results):
                if isinstance(result, Exception):
                    logger.error(f"Search error {integration.name}: {str(result)}")
                    continue
                if result:
                    all_search_results.extend(result)

            # Process product URLs in parallel
            if all_search_results:
                results_per_site = max(1, max_results // len(scraping_integrations))
                url_tasks = []
                url_integration_map = {}
                
                # Map URLs to their integrations
                for result in all_search_results:
                    for integration in scraping_integrations:
                        if integration.matches_url(result["link"]):
                            if url_integration_map.get(integration.name, 0) < results_per_site:
                                url_tasks.append(
                                    ecommerce_manager.process_url(
                                        url=result["link"],
                                        bypass_cache=bypass_cache,
                                        ttl=3600,
                                        query=query
                                    )
                                )
                                url_integration_map[integration.name] = url_integration_map.get(integration.name, 0) + 1
                            break

                # Process URLs in parallel
                if url_tasks:
                    url_results = await asyncio.gather(*url_tasks)
                    for result in url_results:
                        if isinstance(result, dict):
                            products = result.get("products", [])
                            all_products.extend(products)
                        elif isinstance(result, list):
                            all_products.extend(result)

        # Filter and process results
        excluded_sources = {"failed_extraction", "unsupported_site", "error"}
        successful_products = [
            p for p in all_products
            if isinstance(p, dict) and p.get("source") not in excluded_sources
        ]

        if successful_products:
            return await reranker.rerank(query, successful_products)
        
        return []

    except Exception as e:
        logger.error(e, exc_info=True)
        return []
