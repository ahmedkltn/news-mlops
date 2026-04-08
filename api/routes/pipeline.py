from fastapi import APIRouter, BackgroundTasks
from flows.news_flow import news_flow
from etl.cluster import run_clustering

router = APIRouter()

@router.post("/trigger")
def trigger_pipeline(
    background_tasks: BackgroundTasks,
    max_pages: int = 3,
):
    background_tasks.add_task(news_flow, max_pages=max_pages)
    return {"status": "pipeline started", "max_pages": max_pages}

@router.post("/cluster")
def trigger_clustering(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_clustering)
    return {"status": "clustering started"}