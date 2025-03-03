import asyncio
from .proxy_manager import ProxyManager
from .ecommerce_integrations.jumia import JumiaIntegration
from ._craw4ai import CrawlerManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .logging import logger

# Webshare rotating proxy configuration from environment variables (if available)
ROTATING_PROXY = None
logger.info("Checking rotating proxy environment variables...")
required_vars = ["WEBSHARE_ROTATING_DOMAIN", "WEBSHARE_ROTATING_USERNAME", "WEBSHARE_ROTATING_PASSWORD"]
for var in required_vars:
    value = os.getenv(var)
    if value:
        logger.info(f"Found {var}")
    else:
        logger.warning(f"Missing {var}")

if all(os.getenv(var) for var in required_vars):
    logger.info("All rotating proxy environment variables found, configuring rotating proxy...")
    ROTATING_PROXY = {
        "domain": os.getenv("WEBSHARE_ROTATING_DOMAIN"),
        "port": int(os.getenv("WEBSHARE_ROTATING_PORT", 80)),
        "username": os.getenv("WEBSHARE_ROTATING_USERNAME"),
        "password": os.getenv("WEBSHARE_ROTATING_PASSWORD")
    }
    logger.info(f"Rotating proxy configured with domain: {ROTATING_PROXY['domain']}, port: {ROTATING_PROXY['port']}")
else:
    logger.warning("Not all rotating proxy environment variables are set, rotating proxy will not be used")

# Free proxy list (no authentication required)
FREE_PROXY_LIST = [
    # Authenticated proxies
    {
        "host": "38.154.227.167",
        "port": 5868,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "38.153.152.244",
        "port": 9594,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "86.38.234.176",
        "port": 6630,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "173.211.0.148",
        "port": 6641,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "161.123.152.115",
        "port": 6360,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "23.94.138.75",
        "port": 6349,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "64.64.118.149",
        "port": 6732,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "198.105.101.92",
        "port": 5721,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "166.88.58.10",
        "port": 5735,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    {
        "host": "45.151.162.198",
        "port": 6600,
        "protocol": "http",
        "username": "nzmhzpoc",
        "password": "cpfuez5xepz7",
        "anonymity": "Elite"
    },
    # Fast proxies (< 1000ms)
    {
        "host": "168.138.55.69",
        "port": 3128,
        "protocol": "http",
        "country": "jp",
        "speed": 857,
        "anonymity": "Anonymous"
    },
    {
        "host": "85.143.70.36",
        "port": 80,
        "protocol": "http",
        "country": "ru",
        "speed": 466,
        "anonymity": "Elite"
    },
    {
        "host": "35.76.62.196",
        "port": 80,
        "protocol": "http",
        "country": "jp",
        "speed": 485,
        "anonymity": "Elite"
    },
    # Medium speed proxies (1000-2000ms)
    {
        "host": "58.209.139.144",
        "port": 8089,
        "protocol": "http",
        "country": "cn",
        "speed": 1821,
        "anonymity": "Elite"
    },
    # Reliable proxies (high uptime)
    {
        "host": "8.220.204.215",
        "port": 8888,
        "protocol": "http",
        "country": "kr",
        "speed": 2760,
        "anonymity": "Elite"
    },
    {
        "host": "47.121.133.212",
        "port": 9098,
        "protocol": "http",
        "country": "cn",
        "speed": 2457,
        "anonymity": "Elite"
    },
    # Backup proxies
    {
        "host": "47.91.29.151",
        "port": 3128,
        "protocol": "http",
        "country": "jp",
        "speed": 2665,
        "anonymity": "Elite"
    },
    {
        "host": "8.209.96.245",
        "port": 31433,
        "protocol": "http",
        "country": "de",
        "speed": 2576,
        "anonymity": "Elite"
    }
]

# Validate environment variables
def validate_env_vars():
    required_vars = [
        "WEBSHARE_ROTATING_DOMAIN",
        "WEBSHARE_ROTATING_USERNAME",
        "WEBSHARE_ROTATING_PASSWORD",
        "WEBSHARE_USERNAME",
        "WEBSHARE_PASSWORD"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please check your .env file."
        )

async def test_proxy_with_jumia(jumia: JumiaIntegration):
    """Test proxy by scraping Jumia"""
    test_url = "https://www.jumia.com.ng/catalog/?q=laptop"
    logger.info(f"Testing Jumia product list scraping from: {test_url}")
    
    try:
        products = await jumia.get_product_list(test_url)
        logger.info(f"Successfully scraped {len(products)} products from Jumia")
        
        # Test product detail scraping for first product
        if products:
            product = products[0]
            product_url = product.get('url')
            product_id = product.get('product_id')
            
            if product_url and product_id:
                logger.info(f"Testing Jumia product detail scraping from: {product_url}")
                detail = await jumia.get_product_detail(product_url, product_id)
                logger.info("Successfully scraped product details from Jumia")
                return True
    except Exception as e:
        logger.error(f"Error scraping Jumia: {str(e)}")
    return False

async def test_proxy():
    # Validate environment variables before proceeding
    validate_env_vars()
    
    # Test with Jumia integration
    try:
        async with JumiaIntegration(proxy_manager=ProxyManager()) as jumia:
            success = await test_proxy_with_jumia(jumia)
            if success:
                logger.info("Successfully tested proxy with Jumia integration")
                return
    except Exception as e:
        logger.error(f"Error testing proxy with Jumia integration: {str(e)}")
    
    try:
        # Initialize crawler manager
        await CrawlerManager.initialize(use_tor=False)
        crawler = await CrawlerManager.get_crawler()
        
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
    
    finally:
        # Cleanup
        await CrawlerManager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_proxy()) 