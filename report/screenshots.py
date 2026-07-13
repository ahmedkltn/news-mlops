"""
Capture live screenshots of the running News Insight stack for the report
(chapters 1, 7, 8, 10). Assumes the docker-compose stack is already up
(``docker-compose up -d`` / ``make db-full``) — this script does not start
or stop containers, and does not seed the database.

Output: report/img/screen-{dashboard,search,chat,apidocs,prefect,mlflow}.png

Usage:
    pip install playwright && python -m playwright install chromium
    python report/screenshots.py

Host ports — NOTE: this machine also runs an unrelated project that occupies
the "standard" 8000/5173/5000 ports, so this project's docker-compose.yml
remaps its services (see comments there). The defaults below match that
remap; override via env vars if your setup differs.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5180")
API_URL = os.environ.get("API_URL", "http://localhost:8001")
PREFECT_URL = os.environ.get("PREFECT_URL", "http://localhost:4200")
MLFLOW_URL = os.environ.get("MLFLOW_URL", "http://localhost:5001")

VIEWPORT = {"width": 1600, "height": 900}
IMG_DIR = Path(__file__).parent / "img"

SEARCH_QUERY = "football"
CHAT_QUESTION_TEXT = "Dernières nouvelles sportives ?"  # a real suggestion chip

MIN_PNG_BYTES = 5_000  # sanity floor — a blank/near-empty capture is smaller than this


def _get_json(url: str, body: dict | None = None, timeout: int = 10):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def check_health() -> None:
    """Best-effort preflight — warns (does not abort) if a service looks down."""
    checks = {
        f"{FRONTEND_URL}/": "frontend",
        f"{API_URL}/docs": "api",
        f"{PREFECT_URL}/api/health": "prefect",
        f"{MLFLOW_URL}/": "mlflow",
    }
    for url, name in checks.items():
        try:
            urllib.request.urlopen(url, timeout=5)
            print(f"[health] {name:10s} OK  ({url})")
        except Exception as e:
            print(f"[health] {name:10s} WARN — {url} did not respond cleanly: {e}")


def resolve_latest_mlflow_run():
    """Look up the most recent run in the news-clustering experiment, if any.

    Returns (experiment_id, run_id) or (None, None) if nothing is logged yet
    (e.g. clustering hasn't run against this MLflow backend).
    """
    try:
        experiments = _get_json(
            f"{MLFLOW_URL}/api/2.0/mlflow/experiments/search", {"max_results": 50}
        )["experiments"]
    except Exception as e:
        print(f"[mlflow] could not list experiments: {e}")
        return None, None

    exp = next((e for e in experiments if e["name"] == "news-clustering"), None)
    if exp is None:
        print("[mlflow] no 'news-clustering' experiment found")
        return None, None

    try:
        runs = _get_json(
            f"{MLFLOW_URL}/api/2.0/mlflow/runs/search",
            {"experiment_ids": [exp["experiment_id"]], "max_results": 1,
             "order_by": ["attributes.start_time DESC"]},
        ).get("runs", [])
    except Exception as e:
        print(f"[mlflow] could not search runs: {e}")
        return exp["experiment_id"], None

    if not runs:
        print("[mlflow] experiment exists but has no runs")
        return exp["experiment_id"], None

    return exp["experiment_id"], runs[0]["info"]["run_id"]


def save_and_check(page, name: str, full_page: bool = False):
    path = IMG_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    size = path.stat().st_size
    status = "OK" if size >= MIN_PNG_BYTES else "SUSPICIOUSLY SMALL"
    print(f"[shot] {name}.png  {size:,} bytes  {status}")
    return path


def capture_dashboard(page):
    page.goto(FRONTEND_URL + "/", wait_until="networkidle", timeout=30_000)
    time.sleep(1.5)
    save_and_check(page, "screen-dashboard")


def capture_search(page):
    page.goto(FRONTEND_URL + "/search", wait_until="networkidle", timeout=30_000)
    time.sleep(1)
    page.fill("input", SEARCH_QUERY)
    btn = page.get_by_role("button", name="Rechercher")
    with page.expect_response(lambda r: "/search" in r.url and r.status == 200, timeout=15_000):
        btn.click()
    time.sleep(1.5)
    save_and_check(page, "screen-search", full_page=True)


def capture_chat(page):
    page.goto(FRONTEND_URL + "/", wait_until="networkidle", timeout=30_000)
    time.sleep(1)
    page.click('[aria-label="Ouvrir l\'assistant IA"]')
    time.sleep(1)
    try:
        with page.expect_response(lambda r: "/genai/chat" in r.url, timeout=20_000):
            page.click(f"text={CHAT_QUESTION_TEXT}")
        time.sleep(1.5)
    except PWTimeout:
        # No LLM key / chat backend unavailable — capture the open widget
        # anyway per the task brief (still shows a real, meaningful UI state).
        print("[chat] no chat response within timeout — capturing open widget as-is")
    save_and_check(page, "screen-chat")


def capture_apidocs(page):
    page.goto(API_URL + "/docs", wait_until="networkidle", timeout=30_000)
    time.sleep(1)
    save_and_check(page, "screen-apidocs", full_page=True)


def capture_prefect(page):
    page.goto(PREFECT_URL + "/runs", wait_until="load", timeout=30_000)
    time.sleep(2.5)  # SPA hydration + data fetch
    save_and_check(page, "screen-prefect")


def capture_mlflow(page):
    exp_id, run_id = resolve_latest_mlflow_run()
    if run_id:
        url = f"{MLFLOW_URL}/#/experiments/{exp_id}/runs/{run_id}"
    elif exp_id:
        url = f"{MLFLOW_URL}/#/experiments/{exp_id}"
    else:
        url = MLFLOW_URL + "/"
    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    time.sleep(2.5)
    save_and_check(page, "screen-mlflow")


CAPTURES = [
    ("screen-dashboard", capture_dashboard),
    ("screen-search", capture_search),
    ("screen-chat", capture_chat),
    ("screen-apidocs", capture_apidocs),
    ("screen-prefect", capture_prefect),
    ("screen-mlflow", capture_mlflow),
]


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    check_health()

    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, fn in CAPTURES:
            page = browser.new_page(viewport=VIEWPORT)
            try:
                fn(page)
            except Exception as e:
                print(f"[FAIL] {name}: {e}")
                failures.append(name)
            finally:
                page.close()
        browser.close()

    if failures:
        print(f"\n{len(failures)} capture(s) failed: {failures}")
        print("Use an \\fbox placeholder for these in the report chapters.")
        sys.exit(1)
    print("\nAll captures done.")


if __name__ == "__main__":
    main()
