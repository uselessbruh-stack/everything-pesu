"""
PESU Academy HTTP Scraper — direct HTTP requests to pesuacademy.com.
Replicates the Selenium scraper logic from scraper.py using httpx + BeautifulSoup.
No browser needed — works on Vercel serverless.
"""

import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.pesuacademy.com/Academy"
LOGIN_PAGE = f"{BASE_URL}/s/studentProfilePESU"
LOGIN_POST = f"{BASE_URL}/j_spring_security_check"

# Mimic a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class PESUSession:
    """Authenticated HTTP session to PESU Academy."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers=HEADERS,
            follow_redirects=True,
            timeout=30.0,
        )
        self.logged_in = False

    async def login(self, username: str, password: str) -> bool:
        """Login to PESU Academy via Spring Security form POST."""
        try:
            # Step 1: GET the login page to establish session cookie
            resp = await self.client.get(LOGIN_PAGE)
            logger.info(f"Login page status: {resp.status_code}")

            # Step 2: POST credentials to j_spring_security_check
            form_data = {
                "j_username": username,
                "j_password": password,
            }
            resp = await self.client.post(
                LOGIN_POST,
                data=form_data,
                headers={
                    **HEADERS,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://www.pesuacademy.com",
                    "Referer": LOGIN_PAGE,
                },
            )
            logger.info(f"Login POST status: {resp.status_code}, URL: {resp.url}")

            # Check if login succeeded — if redirected back to login page, it failed
            page_text = resp.text
            if "Invalid credentials" in page_text or "j_username" in page_text:
                logger.error("Login failed: invalid credentials or still on login page")
                return False

            self.logged_in = True
            return True

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return parsed BeautifulSoup."""
        if not self.logged_in:
            return None
        resp = await self.client.get(url)
        if resp.status_code != 200:
            logger.error(f"GET {url} returned {resp.status_code}")
            return None
        return BeautifulSoup(resp.text, "html.parser")

    async def _navigate_to_section(self, section_name: str) -> Optional[BeautifulSoup]:
        """Navigate to a section by finding its link on the page.
        In HTTP mode, we look for the link href in the dashboard page.
        """
        # Get the dashboard/profile page first
        soup = await self._get_page(LOGIN_PAGE)
        if not soup:
            return None

        # Find navigation link matching the section name
        for link in soup.find_all("a"):
            link_text = link.get_text(strip=True).lower()
            if section_name.lower() in link_text:
                href = link.get("href")
                if href:
                    url = href if href.startswith("http") else f"{BASE_URL}/{href.lstrip('/')}"
                    return await self._get_page(url)

        # If no link found, try common URL patterns
        section_urls = {
            "attendance": f"{BASE_URL}/s/studentProfilePESU",
            "time table": f"{BASE_URL}/s/studentProfilePESU",
            "result": f"{BASE_URL}/s/studentProfilePESU",
        }
        url = section_urls.get(section_name.lower())
        if url:
            return await self._get_page(url)

        return None

    async def fetch_attendance(self) -> dict:
        """Scrape attendance data — mirrors scraper.py fetch_attendance_data()."""
        try:
            # Navigate to attendance section
            soup = await self._navigate_to_section("attendance")
            if not soup:
                return {"summary": _empty_summary(), "courses": []}

            # Find all tables and parse attendance
            courses = []
            tables = soup.find_all("table")
            logger.info(f"Found {len(tables)} tables on attendance page")

            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(["td", "th"])
                    cell_texts = [c.get_text(strip=True) for c in cells]

                    if len(cell_texts) >= 4:
                        course_code = cell_texts[0]
                        course_name = cell_texts[1]
                        classes_str = cell_texts[2]  # e.g. "14/19"
                        pct_str = cell_texts[3]      # e.g. "73"

                        try:
                            attended, total = map(int, classes_str.split("/"))
                            percentage = float(pct_str)
                            courses.append({
                                "course_code": course_code,
                                "course_name": course_name,
                                "attendance": {
                                    "attended": attended,
                                    "total": total,
                                    "percentage": round(percentage, 2),
                                },
                            })
                        except (ValueError, TypeError):
                            continue

            # Build summary
            total_attended = sum(c["attendance"]["attended"] for c in courses)
            total_classes = sum(c["attendance"]["total"] for c in courses)
            overall_pct = (total_attended / total_classes * 100) if total_classes > 0 else 0

            return {
                "summary": {
                    "total_attended": total_attended,
                    "total_classes": total_classes,
                    "overall_percentage": round(overall_pct, 2),
                    "courses_count": len(courses),
                },
                "courses": courses,
            }

        except Exception as e:
            logger.error(f"Attendance fetch error: {e}")
            return {"summary": _empty_summary(), "courses": []}

    async def fetch_profile(self) -> dict:
        """Scrape profile data from the dashboard page."""
        try:
            soup = await self._get_page(LOGIN_PAGE)
            if not soup:
                return {}

            profile = {}
            page_text = soup.get_text()

            # Extract profile fields using patterns from scraper.py
            patterns = {
                "name": r"Name\s*:?\s*([^\n]+)",
                "pesu_id": r"PESU\s*ID\s*:?\s*([^\n]+)",
                "srn": r"SRN\s*:?\s*([^\n]+)",
                "program": r"Program\s*:?\s*([^\n]+)",
                "branch": r"Branch\s*:?\s*([^\n]+)",
                "semester": r"Semester\s*:?\s*([^\n]+)",
                "section": r"Section\s*:?\s*([^\n]+)",
                "email": r"Email\s*:?\s*([^\n]+)",
                "phone": r"(?:Phone|Contact|Mobile)\s*:?\s*([^\n]+)",
            }

            for field, pattern in patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    profile[field] = match.group(1).strip()

            return profile

        except Exception as e:
            logger.error(f"Profile fetch error: {e}")
            return {}

    async def fetch_timetable(self) -> dict:
        """Scrape timetable data — mirrors scraper.py fetch_timetable_data()."""
        try:
            soup = await self._navigate_to_section("time table")
            if not soup:
                return {}

            tables = soup.find_all("table")
            if not tables:
                return {}

            # Parse the first table as timetable (same logic as scraper.py parse_timetable_data)
            table = tables[0]
            rows = table.find_all("tr")

            if len(rows) < 2:
                return {}

            # First row = time slots
            header_cells = rows[0].find_all(["td", "th"])
            time_slots = [c.get_text(strip=True) for c in header_cells[1:]]  # Skip first (day label)

            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            timetable = {}

            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                cell_texts = [c.get_text(strip=True) for c in cells]

                if cell_texts and cell_texts[0] in days:
                    day = cell_texts[0]
                    day_schedule = {}

                    for i, time_slot in enumerate(time_slots):
                        if i + 1 < len(cell_texts):
                            class_info = cell_texts[i + 1].strip()
                            if class_info and class_info not in ["Break", "No Schedule", ""]:
                                day_schedule[time_slot] = class_info

                    if day_schedule:
                        timetable[day] = day_schedule

            return timetable

        except Exception as e:
            logger.error(f"Timetable fetch error: {e}")
            return {}

    async def fetch_results(self) -> dict:
        """Scrape results data — mirrors scraper.py fetch_results_data()."""
        try:
            soup = await self._navigate_to_section("result")
            if not soup:
                return {}

            results = {}
            page_text = soup.get_text()

            # Parse course results using regex from scraper.py _parse_results_text()
            course_pattern = r'([A-Z]{2}\d{2}[A-Z]{2}\d{3}[A-Z]?\d?)\s*-\s*([^\n]+)'
            course_matches = list(re.finditer(course_pattern, page_text))

            if course_matches:
                courses = []
                for match in course_matches:
                    courses.append({
                        "course_code": match.group(1),
                        "course_name": match.group(2).strip(),
                    })
                results["courses"] = courses
                results["course_count"] = len(courses)

            # Try to find SGPA
            sgpa_match = re.search(r"SGPA\s*:?\s*([\d.]+)", page_text, re.IGNORECASE)
            if sgpa_match:
                results["sgpa"] = float(sgpa_match.group(1))

            return results

        except Exception as e:
            logger.error(f"Results fetch error: {e}")
            return {}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def _empty_summary() -> dict:
    return {
        "total_attended": 0,
        "total_classes": 0,
        "overall_percentage": 0,
        "courses_count": 0,
    }


# --- Public API functions used by the FastAPI endpoints ---


async def create_session(username: str, password: str) -> PESUSession:
    """Login to PESU Academy and return an authenticated HTTP session."""
    session = PESUSession()
    success = await session.login(username, password)
    if not success:
        await session.close()
        raise Exception("Invalid PESU Academy credentials")
    return session


async def fetch_attendance(username: str, password: str) -> dict:
    """Fetch live attendance data from PESU Academy website."""
    session = await create_session(username, password)
    try:
        return await session.fetch_attendance()
    finally:
        await session.close()


async def fetch_profile(username: str, password: str) -> dict:
    """Fetch live profile data from PESU Academy website."""
    session = await create_session(username, password)
    try:
        return await session.fetch_profile()
    finally:
        await session.close()


async def fetch_timetable(username: str, password: str) -> dict:
    """Fetch live timetable data from PESU Academy website."""
    session = await create_session(username, password)
    try:
        return await session.fetch_timetable()
    finally:
        await session.close()


async def fetch_results(username: str, password: str) -> dict:
    """Fetch live results data from PESU Academy website."""
    session = await create_session(username, password)
    try:
        return await session.fetch_results()
    finally:
        await session.close()
