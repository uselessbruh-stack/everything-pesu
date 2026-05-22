"""
Scraper service — wraps the existing PESUScraper for API integration.

Selenium cannot run on Vercel serverless, so this service:
  - Runs the scraper in a background thread (local dev only)
  - Updates attendance_data.json on disk
  - Reloads the data_loader cache after scraping
  - Provides status tracking for long-running scrape jobs

On Vercel, the sync endpoint returns a message explaining
that live scraping is unavailable in serverless mode.
"""

import asyncio
import json
import os
import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to the root scraper module
ROOT_DIR = Path(__file__).resolve().parent.parent
SCRAPER_PATH = ROOT_DIR / "scraper.py"
DATA_FILE = ROOT_DIR / "attendance_data.json"

# Background task tracking
_scrape_status = {
    "running": False,
    "last_run": None,
    "last_status": "idle",
    "last_error": None,
    "progress": "",
}

# Thread pool for running the synchronous scraper
_executor = ThreadPoolExecutor(max_workers=1)


def is_scraper_available() -> bool:
    """Check if the scraper module and its dependencies are available."""
    if not SCRAPER_PATH.exists():
        return False
    try:
        import selenium  # noqa: F401
        return True
    except ImportError:
        return False


def get_scrape_status() -> dict:
    """Return current scrape job status."""
    return {**_scrape_status}


def _run_scraper_sync(username: str, password: str) -> dict:
    """
    Run the PESU scraper synchronously (called inside a thread).
    Imports the scraper module dynamically to avoid import errors
    when Selenium is not installed.
    """
    global _scrape_status
    _scrape_status["running"] = True
    _scrape_status["progress"] = "Starting scraper…"
    _scrape_status["last_error"] = None

    try:
        # Add root dir to path so we can import scraper
        if str(ROOT_DIR) not in sys.path:
            sys.path.insert(0, str(ROOT_DIR))

        # Dynamic import to avoid failing when selenium isn't installed
        import importlib
        scraper_module = importlib.import_module("scraper")
        PESUScraper = scraper_module.PESUScraper

        scraper = PESUScraper(username, password)

        _scrape_status["progress"] = "Setting up browser…"
        scraper.setup_driver()

        _scrape_status["progress"] = "Logging in to PESU Academy…"
        if not scraper.login():
            raise RuntimeError("Failed to login to PESU Academy")

        _scrape_status["progress"] = "Fetching attendance data…"
        scraper.fetch_attendance_data()

        _scrape_status["progress"] = "Fetching timetable…"
        timetable = scraper.fetch_timetable_data()
        scraper.timetable_data = timetable

        _scrape_status["progress"] = "Fetching results…"
        raw_results = scraper.fetch_results_data()
        if raw_results:
            parsed_results = scraper.parse_results_data(raw_results)
            scraper.results_data = parsed_results
        else:
            scraper.results_data = {}

        _scrape_status["progress"] = "Fetching calendar…"
        calendar = scraper.fetch_calendar_data()
        scraper.calendar_data = calendar

        _scrape_status["progress"] = "Saving data…"
        if scraper.attendance_structured:
            result = scraper.save_full_data_to_json(
                scraper.attendance_structured,
                scraper.credentials_data,
                scraper.timetable_data,
                scraper.results_data,
                scraper.calendar_data,
            )
        else:
            raise RuntimeError("No attendance data was scraped")

        scraper.close()

        _scrape_status["running"] = False
        _scrape_status["last_run"] = time.time()
        _scrape_status["last_status"] = "success"
        _scrape_status["progress"] = "Complete"

        # Reload the data_loader cache
        try:
            from . import data_loader
        except ImportError:
            import data_loader
        data_loader.clear_cache()

        logger.info("Scraper completed successfully")
        return {"status": "success", "message": "Data scraped and saved"}

    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        _scrape_status["running"] = False
        _scrape_status["last_run"] = time.time()
        _scrape_status["last_status"] = "error"
        _scrape_status["last_error"] = str(e)
        _scrape_status["progress"] = f"Failed: {e}"
        return {"status": "error", "message": str(e)}

    finally:
        # Make sure browser is closed even on error
        try:
            scraper.close()
        except Exception:
            pass


async def run_scraper_async(username: str, password: str) -> dict:
    """
    Run the scraper in a background thread so it doesn't block the event loop.
    Returns immediately with a status message.
    """
    if _scrape_status["running"]:
        return {
            "status": "already_running",
            "message": "A scrape job is already in progress",
            "progress": _scrape_status["progress"],
        }

    loop = asyncio.get_event_loop()

    # Fire-and-forget in the thread pool
    loop.run_in_executor(_executor, _run_scraper_sync, username, password)

    return {
        "status": "started",
        "message": "Scraper started in background. Check /api/attendance/sync/status for progress.",
    }
