import os
from utils.celery_tasks import celery_app
from utils.price_tracking import schedule_price_tracking
from celery.schedules import crontab

# Get Redis URL from environment variable
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'track-prices-midnight': {
        'task': 'utils.price_tracking.schedule_price_tracking',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight
    },
}

# Configure Celery settings for Docker environment
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,  # Important for container startup order
)

if __name__ == '__main__':
    print("Price tracking system initialized in Docker environment.")
    print("Use 'docker-compose up' to start all services.")
    print("\nTo run price tracking immediately:")
    print("docker-compose exec celery-worker python -c 'from utils.price_tracking import schedule_price_tracking; schedule_price_tracking.delay()'") 