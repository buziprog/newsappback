from celery import shared_task
# or wherever your `fetch_and_store_articles` function resides
from .models import Articles
from .views import fetch_and_store_articles


@shared_task
def fetch_articles():
    fetch_and_store_articles()
