from prefect.client.schemas.schedules import CronSchedule
from prefect.deployments import Deployment
from flows.news_flow import news_flow

deployment = Deployment.build_from_flow(
    flow=news_flow,
    name="daily-news-pipeline",
    schedule=CronSchedule(cron="0 6 * * *", timezone="Africa/Tunis"),
    parameters={"max_pages": 5},
)

if __name__ == "__main__":
    deployment.apply()
    print("Deployment registered.")