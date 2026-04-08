import logging
from prefect import flow, task
from etl.pipeline import run_pipeline

logger = logging.getLogger(__name__)

@task(name="run-news-pipeline", retries=2, retry_delay_seconds=60)
def pipeline_task(max_pages: int) -> dict:
    return run_pipeline(max_pages=max_pages)

@flow(
    name="news-pipeline",
    description="Scrape, transform and load Tunisian news articles",
)
def news_flow(max_pages: int = 5):
    logger.info("Starting news pipeline flow")
    result = pipeline_task(max_pages=max_pages)
    logger.info(f"Flow completed: {result}")
    return result

if __name__ == "__main__":
    news_flow(max_pages=1)