import asyncio
from datetime import datetime, timezone
from celery import states
from celery.exceptions import MaxRetriesExceededError
from functools import wraps
import time

from utils.scrape import TrackerWebScraper
from utils.logging import logger
from utils.celery_tasks import celery_app
from utils.email_manager import manager as email_manager

from appwrite.query import Query

tracker = TrackerWebScraper()
semaphore = asyncio.Semaphore(10)  # Limit concurrent scraping

def with_scraping_rate_limit(func):
    """Decorator to implement rate limiting for scraping"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with semaphore:  # Use semaphore for concurrent request limiting
            # Add small delay between requests
            await asyncio.sleep(0.5)
            return await func(*args, **kwargs)
    return wrapper

@celery_app.task(name='price_tracking.schedule_price_tracking')
def schedule_price_tracking():
    """
    Celery task to trigger price tracking at midnight.
    This is scheduled to run every day at midnight.
    """
    start_time = time.time()
    logger.info("Starting price tracking schedule task")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info("Setting up event loop for price tracking")
            loop.run_until_complete(scrape_products())
            duration = time.time() - start_time
            logger.info(f"Price tracking completed successfully in {duration:.2f} seconds")
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
    default_retry_delay=300,
    rate_limit='60/m'  # Limit to 60 tasks per minute
)
def scrape_single_product(self, url, product_id, source, user_id, track_id, product_name, target_price):
    """
    Celery task to scrape a single product with retry mechanism.
    Will retry up to 3 times with 5 minutes delay between attempts.
    """
    from api.track.model import PriceHistory, TrackedItem
    from api.product.model import Product

    start_time = time.time()
    try:
        # Create new event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run async operations in the loop
            price = loop.run_until_complete(tracker.get_price(url, source))
            
            if price is None or price <= 0:
                raise ValueError(f"Invalid price {price} for product {product_id}")

            # Update tracked item with current price
            loop.run_until_complete(
                TrackedItem.update(track_id, data={
                    "current_price": price
                })
            )
            
            # Store price history
            loop.run_until_complete(
                PriceHistory.create(
                    document_id=Product.get_unique_id(),
                    data={
                        "price": price,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "tracked_id": track_id,
                        "user_id": user_id,
                    },
                )
            )
            
            # Notify user if price is within range
            loop.run_until_complete(
                notify_user_price_change(user_id, product_name, price, url, target_price)
            )
            
            duration = time.time() - start_time
            logger.info(f"Scraped {url} for product {product_id}: {price} in {duration:.2f} seconds")
            return {"status": "success", "price": price, "duration": duration}
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error scraping {url} for product {product_id}: {e}")
        try:
            # Exponential backoff for retries
            retry_delay = self.default_retry_delay * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=retry_delay)
        except MaxRetriesExceededError:
            # After all retries are exhausted, schedule for next run
            logger.error(f"Max retries exceeded for product {product_id}. Will try again in next scheduled run.")
            # Update tracked item to indicate failure
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    TrackedItem.update(track_id, data={
                        "last_error": str(e),
                        "last_checked": datetime.now(timezone.utc).isoformat()
                    })
                )
                loop.close()
            except Exception as update_error:
                logger.error(f"Failed to update tracked item status: {update_error}")
            return {"status": "failed", "error": str(e)}

@with_scraping_rate_limit
async def notify_user_price_change(user_id: str, product_name: str, current_price: float, url: str, target_price: float):
    """Send email notification to user about price changes"""
    try:
        if target_price is not None and current_price > 0:
            if current_price <= target_price:  # Changed to notify when price is at or below target
                subject = f"Price Alert: {product_name} is at or below your target price!"
                content = f"""
                Good news! The price of {product_name} has reached your target price.
                Current Price: ₦{current_price:,.2f}
                Your Target Price: ₦{target_price:,.2f}
                
                Check it out here: {url}
                """
                email_manager.choose_account("no-reply")
                email_manager.send_email(user_id, subject, content)
                logger.info(f"Price alert sent to user {user_id} for product {product_name}")
    except Exception as e:
        logger.error(f"Error sending price notification: {e}")
        # Don't raise the exception to prevent task failure

async def scrape_products():
    """
    Main function to scrape all tracked products using batching.
    """
    from api.track.model import TrackedItem
    
    batch_size = 100
    offset = 0
    total_processed = 0
    start_time = time.time()
    
    while True:
        batch_start_time = time.time()
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
        
        batch_duration = time.time() - batch_start_time
        logger.info(f"Batch processed in {batch_duration:.2f} seconds")
        
        if len(tracked_items) < batch_size:  # Last batch
            break
    
    total_duration = time.time() - start_time
    if total_processed > 0:
        logger.info(f"Completed processing {total_processed} tracked items in {total_duration:.2f} seconds")
    else:
        logger.info("No tracked items found to process")

async def scrape_multiple_products(tracked_items):
    """
    Handles the scraping of multiple products concurrently.
    Delegates each tracked item to individual Celery tasks with retry mechanism.
    """
    from api.product.model import Product

    failed_items = []
    batch_start = time.time()
    processed = 0
    
    for item in tracked_items:
        try:
            try:
                product = await Product.read(item.product_id)
            except Exception as e:
                logger.error(f"Product {item.product_id} not found: {e}")
                continue

            if not product.url: 
                logger.warning(f"Tracked item {item.id} has no URL. Skipping.")
                continue

            # Schedule individual Celery task for each tracked item
            task = scrape_single_product.apply_async(
                args=(
                    product.url, 
                    product.id,
                    product.source, 
                    item.user_id, 
                    item.id,
                    product.name if hasattr(product, 'name') else 'Unknown Product',
                    item.target_price
                ),
                expires=3600  # Task expires after 1 hour
            )
            
            processed += 1
            
            # Track failed tasks
            if task.status == states.FAILURE:
                failed_items.append(item.id)
                logger.error(f"Initial scheduling failed for tracked item {item.id}")

        except Exception as e:
            logger.error(f"Error processing tracked item {item.id}: {e}")
            failed_items.append(item.id)
    
    batch_duration = time.time() - batch_start
    if failed_items:
        logger.warning(f"Failed to process {len(failed_items)} tracked items: {failed_items}")
    
    logger.info(f"Processed {processed} items in {batch_duration:.2f} seconds") 