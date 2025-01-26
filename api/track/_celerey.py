# import asyncio
# from datetime import datetime

# from utils.logging import logger
# from api.track.model import PriceHistory
# from .scrape import TrackerWebScraper
# from api.product.model import Product

# import sentry_sdk
# from celery import Celery, shared_task
# from sentry_sdk import capture_exception
# from celery.schedules import crontab

# # sentry_sdk.init(dsn="YOUR_SENTRY_DSN")

# # Initialize Celery with ZeroMQ as the broker and backend   
# celery_app = Celery(
#     'scraper',
#     broker='zmq://127.0.0.1:5555',  # ZeroMQ broker
#     backend='db+sqlite:///celery_results.sqlite'   # SQLite result backend
# )

# # Semaphore to limit concurrency
# semaphore = asyncio.Semaphore(10)

# # Celery tasks
# @shared_task(bind=True, max_retries=3, retry_backoff=True)
# def daily_scrape_trigger(self):
#     try:
#         # Run the async function within an event loop
#         asyncio.run(scrape_products())
#     except Exception as e:
#         logger.error(f"Error triggering daily scrape: {e}")
#         capture_exception(e)
#         raise self.retry(exc=e)


# async def scrape_products():
#     try:
#         response = await Product.list()
#         product_ids = [product.id for product in response["documents"]]
#         await scrape_multiple_products(product_ids)
#     except Exception as e:
#         logger.error(f"Error in scrape_products: {e}")
#         capture_exception(e)

# async def get_price(url, product_id, source):
#     tracker = TrackerWebScraper()
#     async with semaphore:
#         try:
#             price = await tracker.get_price(url, source)
#             await PriceHistory.create(
#                 document_id=Product.get_unique_id(),
#                 data={
#                     "price": price,
#                     "timestamp": datetime.utcnow().isoformat(),  # Use UTC
#                     "product_id": product_id,
#                 },
#             )
#             logger.info(f"Scraped {url} for product {product_id}: {price}")
#         except Exception as e:
#             logger.error(f"Error scraping {url} for product {product_id}: {e}")
#             capture_exception(e)


# async def scrape_multiple_products(product_ids):
#     tasks = []
#     for product_id in product_ids:
#         try:
#             product = await Product.read(product_id)
#             if not product.url:
#                 logger.warning(f"Product {product_id} has no URL. Skipping.")
#                 continue
#             tasks.append(get_price(product.url, product.id, product.source))
#         except Exception as e:
#             logger.error(f"Error fetching product {product_id}: {e}")
#             capture_exception(e)

#     results = await asyncio.gather(*tasks, return_exceptions=True)
#     for result in results:
#         if isinstance(result, Exception):
#             logger.error(f"Task failed with error: {result}")
#             capture_exception(result)

# # Configure Celery beat schedule
# celery_app.conf.beat_schedule = {
#     'scrape-daily': {
#         'task': 'daily_scrape_trigger',
#         'schedule': crontab(hour=0, minute=0), 
#     },
# }
# celery_app.conf.timezone = 'UTC'
