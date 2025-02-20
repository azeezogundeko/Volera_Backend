import asyncio
from datetime import datetime, timezone
from celery import states
from celery.exceptions import MaxRetriesExceededError


from utils.scrape import TrackerWebScraper
from utils.logging import logger
from utils.celery_tasks import celery_app
from utils.email_manager import manager as email_manager

from appwrite.query import Query

tracker = TrackerWebScraper()
semaphore = asyncio.Semaphore(10)

@celery_app.task(name='price_tracking.schedule_price_tracking')
def schedule_price_tracking():
    """
    Celery task to trigger price tracking at midnight.
    This is scheduled to run every day at midnight.
    """
    logger.info("Starting price tracking schedule task")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info("Setting up event loop for price tracking")
            loop.run_until_complete(scrape_products())
            logger.info("Price tracking completed successfully")
        except Exception as e:
            logger.error(f"Error in price tracking task: {str(e)}", exc_info=True)
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Critical error in price tracking task: {str(e)}", exc_info=True)
        raise

@celery_app.task(
    name='price_tracking.scrape_single_product',
    bind=True, 
    max_retries=3, 
    default_retry_delay=300
)  # 5 minutes delay between retries
async def scrape_single_product(self, url, product_id, source, user_id, track_id, product_name):
    """
    Celery task to scrape a single product with retry mechanism.
    Will retry up to 3 times with 5 minutes delay between attempts.
    """
    from api.track.model import PriceHistory
    from api.product.model import Product

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
    from api.auth.model import UserPreferences
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
                email_manager.choose_account("no-reply")
                email_manager.send_email(user_id, subject, content)
                logger.info(f"Price alert sent to user {user_id} for product {product_name}")
    except Exception as e:
        logger.error(f"Error sending price notification: {e}")

async def scrape_products():
    """
    Main function to scrape all tracked products using batching.
    """
    from api.track.model import TrackedItem
    
    batch_size = 100
    offset = 0
    total_processed = 0
    
    while True:
        # Get batch of tracked items
        response = await TrackedItem.list(
            queries=[
                Query.equal("notification_enabled", True),  # Only get items with notifications enabled
                Query.limit(batch_size),
                Query.offset(offset)
            ]
        )
        
        tracked_items = response["documents"]
        if not tracked_items:
            break
            
        logger.info(f"Processing batch of {len(tracked_items)} tracked items (offset: {offset})")
        await scrape_multiple_products(tracked_items)
        
        total_processed += len(tracked_items)
        offset += batch_size
        
        if len(tracked_items) < batch_size:  # Last batch
            break
    
    if total_processed > 0:
        logger.info(f"Completed processing {total_processed} tracked items")
    else:
        logger.info("No tracked items found to process")

async def scrape_multiple_products(tracked_items):
    """
    Handles the scraping of multiple products concurrently.
    Delegates each tracked item to individual Celery tasks with retry mechanism.
    """
    failed_items = []
    
    for item in tracked_items:
        try:
            if not item.url:
                logger.warning(f"Tracked item {item.id} has no URL. Skipping.")
                continue

            # Schedule individual Celery task for each tracked item
            task = scrape_single_product.delay(
                item.url, 
                item.product_id,  # Using product_id from tracked item
                item.source, 
                item.user_id, 
                item.id,  # Using tracked item id as track_id
                item.name if hasattr(item, 'name') else 'Unknown Product'
            )
            
            # Track failed tasks
            if task.status == states.FAILURE:
                failed_items.append(item.id)
                logger.error(f"Initial scheduling failed for tracked item {item.id}")

        except Exception as e:
            logger.error(f"Error processing tracked item {item.id}: {e}")
            failed_items.append(item.id)
    
    if failed_items:
        logger.warning(f"Failed to process {len(failed_items)} tracked items: {failed_items}") 