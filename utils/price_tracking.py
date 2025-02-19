import asyncio
from datetime import datetime, timezone
from celery import states
from celery.exceptions import MaxRetriesExceededError

from api.tracker.models import PriceHistory, TrackedItem
from api.product.models import Product
from api.auth.model import UserPreferences
from utils.scrape import TrackerWebScraper
from utils.logging import logger
from utils.celery_tasks import celery_app
from utils.email_manager import send_email

tracker = TrackerWebScraper()
semaphore = asyncio.Semaphore(10)

@celery_app.task
def schedule_price_tracking():
    """
    Celery task to trigger price tracking at midnight.
    This is scheduled to run every day at midnight.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(scrape_products())
    finally:
        loop.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)  # 5 minutes delay between retries
async def scrape_single_product(self, url, product_id, source, user_id, track_id, product_name):
    """
    Celery task to scrape a single product with retry mechanism.
    Will retry up to 3 times with 5 minutes delay between attempts.
    """
    try:
        price = await tracker.get_price(url, source)
        # Store price history
        await PriceHistory.create(
            document_id=Product.get_unique_id(),
            data={
                "price": price,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tracked_id": track_id,
                "user_id": user_id,
            },
        )
        # Notify user if price is within range
        await notify_user_price_change(user_id, product_name, price, url)
        logger.info(f"Scraped {url} for product {product_id}: {price}")
        return {"status": "success", "price": price}
    except Exception as e:
        logger.error(f"Error scraping {url} for product {product_id}: {e}")
        try:
            # Retry the task
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            # After all retries are exhausted, schedule for next run
            logger.error(f"Max retries exceeded for product {product_id}. Will try again in next scheduled run.")
            return {"status": "failed", "error": str(e)}

async def get_user_price_range(user_id: str):
    """Get user's price range preferences"""
    try:
        preferences = await UserPreferences.read(user_id)
        return preferences.min_price, preferences.max_price
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return None, None

async def notify_user_price_change(user_id: str, product_name: str, current_price: float, url: str):
    """Send email notification to user about price changes"""
    try:
        min_price, max_price = await get_user_price_range(user_id)
        if min_price is not None and max_price is not None:
            if min_price <= current_price <= max_price:
                subject = f"Price Alert: {product_name} is within your range!"
                content = f"""
                Good news! The price of {product_name} is now within your preferred range.
                Current Price: ₦{current_price:,.2f}
                Your Range: ₦{min_price:,.2f} - ₦{max_price:,.2f}
                
                Check it out here: {url}
                """
                await send_email(user_id, subject, content)
                logger.info(f"Price alert sent to user {user_id} for product {product_name}")
    except Exception as e:
        logger.error(f"Error sending price notification: {e}")

async def scrape_products():
    """
    Main function to scrape all tracked products.
    """
    response = await Product.list()
    product_ids = [product.id for product in response["documents"]]
    if len(product_ids) > 0:
        logger.info(f"Scraping {len(product_ids)} products.")
        await scrape_multiple_products(product_ids)

async def scrape_multiple_products(product_ids):
    """
    Handles the scraping of multiple products concurrently.
    Delegates each product to individual Celery tasks with retry mechanism.
    """
    failed_products = []
    
    for product_id in product_ids:
        try:
            # Fetch product details
            item = await TrackedItem.read(product_id)

            if not item.url:
                logger.warning(f"Product {product_id} has no URL. Skipping.")
                continue

            # Schedule individual Celery task for each product
            task = scrape_single_product.delay(
                item.url, 
                item.id, 
                item.source, 
                item.user_id, 
                item.track_id,
                item.name
            )
            
            # Track failed tasks
            if task.status == states.FAILURE:
                failed_products.append(product_id)
                logger.error(f"Initial scheduling failed for product {product_id}")

        except Exception as e:
            logger.error(f"Error processing product {product_id}: {e}")
            failed_products.append(product_id)
    
    if failed_products:
        logger.warning(f"Failed to process {len(failed_products)} products: {failed_products}")
