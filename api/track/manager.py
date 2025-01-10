import asyncio
from datetime import datetime

from utils.logging import logger
from agents.tools.google import GoogleSearchTool
# from utils.decorator import async_retry
from .model import Product, PriceHistory
from .schema import ProductIn
from .scrape import AsyncWebScraper
from .agent import price_extrator

import sentry_sdk
from celery import Celery, shared_task
from sentry_sdk import capture_exception
from celery.schedules import crontab


# Semaphore for limiting concurrent requests
MAX_CONCURRENT_REQUESTS = 3
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Sentry integration
web_scraper = AsyncWebScraper()
google_search = GoogleSearchTool()
sentry_sdk.init(dsn="YOUR_SENTRY_DSN")


# Celery tasks
@shared_task(bind=True, max_retries=3, retry_backoff=True)
async def daily_scrape_trigger(self):
    try:
        response = await Product.list()
        product_ids = [product.id for product in response['documents']]
        asyncio.run(scrape_multiple_products(product_ids))
    except Exception as e:
        logger.error(f"Error triggering daily scrape: {e}")
        capture_exception(e)
        self.retry(exc=e)


async def scrape_product(url, product_id):
    async with semaphore:
        try:
            docs  = await web_scraper.scrape_websites(url)
            content = await web_scraper.extract_text(docs)
            data = await price_extrator.run(str(content))
            await PriceHistory.create(
                document_id=Product.get_unique_id(),
                data = {
                    "price": data.data.price,
                    "timestamp": datetime.now().isoformat(),
                    "product_id": product_id
                }
            )

            logger.info(f"Scraped {url} for product {product_id}: {price}")
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Error scraping {url} for product {product_id}: {e}")
            capture_exception(e)


async def scrape_multiple_products(product_ids):
    tasks = []
    for product_id in product_ids:
        try:
            product = await Product.read(product_id)
            url = product.url
            if not url:
                logger.warning(f"Product {product_id} has no URL. Skipping.")
                continue
            tasks.append(scrape_product(url, product_id))
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            capture_exception(e)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Task failed with error: {result}")
            capture_exception(result)


async def search_products(query):
    response = await google_search.search(query)
    # parse response with LLM?
    # Maybe Scrape each websites and parse response to LLM
    # Rerank search Queries before parsing response to LLM

async def add_product(*args, **kwargs: ProductIn):
    await Product.create(
        document_id=Product.get_unique_id(),
        data = kwargs
    )


async def remove_product(product_id):
    await Product.delete(product_id)


async def get_price_history(product_id, user_id): 
    price_history = await PriceHistory.list([f"product_id=={product_id}", f"user_id=={user_id}"])
    return price_history['documents']
        
# Configure Celery beat schedule
celery_app.conf.beat_schedule = {
    'scrape-daily': {
        'task': 'daily_scrape_trigger',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
celery_app.conf.timezone = 'UTC'

if __name__ == '__main__':
    manager = PriceTrackerManager()