import os
import datetime

from utils.logging import logger
from utils.decorator import async_retry
from db._appwrite.base import AsyncAppWriteClient
from celery import Celery, shared_task

from celery.schedules import crontab
import httpx
import asyncio

async_db = AsyncAppWriteClient()

# Replace with actual collection IDs from Appwrite
PRODUCTS_COLLECTION_ID = '640a69f1b136b2b77a9e'
PRICE_HISTORY_COLLECTION_ID = '640a6a2160a0f200a102'

# Semaphore for limiting concurrent requests
MAX_CONCURRENT_REQUESTS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Sentry integration
import sentry_sdk
from sentry_sdk import capture_exception

sentry_sdk.init(dsn="YOUR_SENTRY_DSN")

# Celery tasks
@shared_task(bind=True, max_retries=3, retry_backoff=True)
async def daily_scrape_trigger(self):
    try:
        products_response = await async_db.list_documents(PRODUCTS_COLLECTION_ID)
        product_ids = [product['$id'] for product in products_response['documents']]
        asyncio.run(scrape_multiple_products(product_ids))
    except Exception as e:
        logger.error(f"Error triggering daily scrape: {e}")
        capture_exception(e)
        self.retry(exc=e)


async def scrape_product(url, product_id):
    async with semaphore:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                # Adjust the selector to match the website
                price_tag = soup.find('span', class_='price')
                price = price_tag.text.strip() if price_tag else 'Not found'

                # Save price data to Appwrite
                document_id = f'{product_id}_{datetime.datetime.now().isoformat()}'

                await async_db.create_document(PRICE_HISTORY_COLLECTION_ID, document_id=document_id, document_data={'product_id': product_id,
                    'price': price,
                    'timestamp': datetime.datetime.now().isoformat(),
                })

                logger.info(f"Scraped {url} for product {product_id}: {price}")
        except Exception as e:
            logger.error(f"Error scraping {url} for product {product_id}: {e}")
            capture_exception(e)


async def scrape_multiple_products(product_ids):
    tasks = []
    for product_id in product_ids:
        try:
            product = await async_db.get_document(PRODUCTS_COLLECTION_ID, product_id)
            url = product.get('url')
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


# PriceTrackerManager class
class PriceTrackerManager:

    def __init__(self) -> None:
        self.db = async_db


    async def add_product(self, product_id, url):
        try:
            await self.db.create_document(PRODUCTS_COLLECTION_ID, {'url': url}, product_id)
        except Exception as e:
            logger.error(f"Error adding product {product_id}: {e}")
            capture_exception(e)

    async def remove_product(self, product_id):
        try:
            await self.db.delete_document(PRODUCTS_COLLECTION_ID, product_id)
        except Exception as e:
            logger.error(f"Error removing product {product_id}: {e}")
            capture_exception(e)

    async def get_price_history(self, product_id):
        try:
            price_history = await self.db.list_documents(
                PRICE_HISTORY_COLLECTION_ID,
                filter=f"product_id=={product_id}"
            )
            return price_history['documents']
        except Exception as e:
            logger.error(f"Error fetching price history for {product_id}: {e}")
            capture_exception(e)
            return []

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