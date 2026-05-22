"""
PESU Academy HTTP Scraper — direct AJAX calls to pesuacademy.com.
Discovered endpoints by reverse-engineering the JS on the student portal.
No browser needed — pure httpx + BeautifulSoup. Works on Vercel serverless.
"""

import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.pesuacademy.com/Academy"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# AJAX endpoints discovered from studentprofilepesu.js
ENDPOINTS = {
    "semesters": "/a/studentProfilePESU/getStudentSemestersPESU",
    "admin": "/s/studentProfilePESUAdmin",
}

# controllerMode IDs from data-url attributes on menu items
CONTROLLER = {
    "attendance": 6407,
    "timetable": 6415,
    "results": 6402,
    "profile": 6414,
    "courses": 6403,
}


class PESUSession:
    """Authenticated HTTP session to PESU Academy."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers=HEADERS,
            follow_redirects=True,
            timeout=30.0,
        )
        self._csrf = ""
        self.logged_in = False

    async def login(self, username: str, password: str) -> bool:
        """Login via Spring Security form POST."""
        try:
            # Step 1: GET login page → session cookie + CSRF token
            r1 = await self.client.get(f"{BASE_URL}/s/studentProfilePESU")
            soup = BeautifulSoup(r1.text, "html.parser")
            csrf_input = soup.find("input", {"name": "_csrf"})
            self._csrf = csrf_input.get("value", "") if csrf_input else ""

            # Step 2: POST credentials
            r2 = await self.client.post(
                f"{BASE_URL}/j_spring_security_check",
                data={
                    "j_username": username,
                    "j_password": password,
                    "_csrf": self._csrf,
                },
                headers={
                    **HEADERS,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": str(r1.url),
                },
            )

            # Update CSRF from the post-login page
            soup2 = BeautifulSoup(r2.text, "html.parser")
            csrf2 = soup2.find("input", {"name": "_csrf"})
            if csrf2:
                self._csrf = csrf2.get("value", self._csrf)

            # Check login success: if still on login page, it failed
            if "j_username" in r2.text:
                return False

            self.logged_in = True
            return True

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def _ajax_headers(self) -> dict:
        """Headers for AJAX requests."""
        return {
            **HEADERS,
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-TOKEN": self._csrf,
            "Referer": f"{BASE_URL}/s/studentProfilePESU",
        }

    async def _get_semesters(self) -> list[tuple[str, str]]:
        """Fetch available semesters → list of (id, name) tuples."""
        r = await self.client.get(
            f"{BASE_URL}{ENDPOINTS['semesters']}",
            headers=self._ajax_headers(),
        )
        # Response is JSON-quoted HTML string: "<option value=\"3309\">Sem-2</option>..."
        text = r.text.strip('"').replace('\\"', '"')
        soup = BeautifulSoup(text, "html.parser")
        return [
            (o.get("value"), o.get_text(strip=True))
            for o in soup.find_all("option")
            if o.get("value")
        ]

    async def _post_admin(self, controller_mode: int, action_type: int, **extra) -> BeautifulSoup:
        """POST to the admin endpoint with form data."""
        data = {
            "controllerMode": str(controller_mode),
            "actionType": str(action_type),
            "_csrf": self._csrf,
            **{k: str(v) for k, v in extra.items()},
        }
        r = await self.client.post(
            f"{BASE_URL}{ENDPOINTS['admin']}",
            data=data,
            headers={
                **self._ajax_headers(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        return BeautifulSoup(r.text, "html.parser")

    async def _get_admin(self, controller_mode: int, action_type: int) -> BeautifulSoup:
        """GET the admin endpoint with query params."""
        r = await self.client.get(
            f"{BASE_URL}{ENDPOINTS['admin']}",
            params={
                "controllerMode": str(controller_mode),
                "actionType": str(action_type),
            },
            headers=self._ajax_headers(),
        )
        return BeautifulSoup(r.text, "html.parser")

    # ── Attendance ──────────────────────────────────────────────

    async def fetch_attendance(self) -> dict:
        """Fetch attendance for all semesters."""
        semesters = await self._get_semesters()
        all_courses = []

        for sem_id, sem_name in semesters:
            # POST with controllerMode=6407, actionType=8, batchClassId=<semId>
            soup = await self._post_admin(
                CONTROLLER["attendance"], 8, batchClassId=sem_id
            )

            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all("td")]
                    if len(cells) >= 4:
                        code, name, classes_str, pct_str = cells[0], cells[1], cells[2], cells[3]
                        try:
                            if classes_str == "NA" or pct_str == "NA":
                                attended, total, pct = 0, 0, 0.0
                            else:
                                attended, total = map(int, classes_str.split("/"))
                                pct = float(pct_str)

                            all_courses.append({
                                "course_code": code,
                                "course_name": name,
                                "semester": sem_name,
                                "attendance": {
                                    "attended": attended,
                                    "total": total,
                                    "percentage": round(pct, 2),
                                },
                            })
                        except (ValueError, TypeError):
                            continue

        total_attended = sum(c["attendance"]["attended"] for c in all_courses)
        total_classes = sum(c["attendance"]["total"] for c in all_courses)
        overall = (total_attended / total_classes * 100) if total_classes > 0 else 0

        return {
            "summary": {
                "total_attended": total_attended,
                "total_classes": total_classes,
                "overall_percentage": round(overall, 2),
                "courses_count": len(all_courses),
            },
            "courses": all_courses,
        }

    # ── Profile ─────────────────────────────────────────────────

    async def fetch_profile(self) -> dict:
        """Fetch profile via GET controllerMode=6414, actionType=5."""
        soup = await self._get_admin(CONTROLLER["profile"], 5)
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        profile = {}
        field_map = {
            "Name": "name",
            "PESU Id": "pesu_id",
            "SRN": "srn",
            "Program": "program",
            "Branch": "branch",
            "Semester": "semester",
            "Section": "section",
            "Email ID": "email",
            "Contact No": "phone",
        }

        for i, line in enumerate(lines):
            for label, key in field_map.items():
                if line == label and i + 1 < len(lines):
                    profile[key] = lines[i + 1]
                    break

        return profile

    # ── Timetable ───────────────────────────────────────────────

    async def fetch_timetable(self) -> dict:
        """Fetch timetable via GET controllerMode=6415, actionType=5."""
        soup = await self._get_admin(CONTROLLER["timetable"], 5)

        # Timetable page has batch/room info and an embedded table
        timetable = {}

        # Extract metadata
        text = soup.get_text(separator="\n", strip=True)
        batch_match = re.search(r"Batch:\s*(.+)", text)
        room_match = re.search(r"Room:\s*(.+)", text)
        timetable["batch"] = batch_match.group(1).strip() if batch_match else ""
        timetable["room"] = room_match.group(1).strip() if room_match else ""

        # Parse schedule table if present
        tables = soup.find_all("table")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        schedule = {}

        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            # First row = time headers
            header_cells = rows[0].find_all(["td", "th"])
            time_slots = [c.get_text(strip=True) for c in header_cells[1:]]

            for row in rows[1:]:
                cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                if cells and cells[0] in days:
                    day_schedule = {}
                    for i, slot in enumerate(time_slots):
                        if i + 1 < len(cells):
                            val = cells[i + 1].strip()
                            if val and val not in ["", "Break", "No Schedule"]:
                                day_schedule[slot] = val
                    if day_schedule:
                        schedule[cells[0]] = day_schedule

        timetable["schedule"] = schedule
        return timetable

    # ── Results ─────────────────────────────────────────────────

    async def fetch_results(self) -> dict:
        """Fetch results for all semesters."""
        semesters = await self._get_semesters()
        all_results = {}

        for sem_id, sem_name in semesters:
            # Results: controllerMode=6402, actionType=8 or 9
            soup = await self._post_admin(
                CONTROLLER["results"], 8, batchClassId=sem_id
            )

            text = soup.get_text(separator="\n", strip=True)

            # Parse SGPA
            sgpa_match = re.search(r"SGPA\s*:?\s*([\d.]+)", text, re.IGNORECASE)

            # Parse course results from text
            course_pattern = r"([A-Z]{2}\d{2}[A-Z]{2}\d{3}[A-Z]?\d?)\s*-?\s*([^\n]+)"
            courses = []
            for match in re.finditer(course_pattern, text):
                courses.append({
                    "course_code": match.group(1),
                    "course_name": match.group(2).strip(),
                })

            # Also try parsing tables
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all("td")]
                    if len(cells) >= 2 and re.match(r"[A-Z]{2}\d{2}", cells[0]):
                        if not any(c["course_code"] == cells[0] for c in courses):
                            courses.append({
                                "course_code": cells[0],
                                "course_name": cells[1] if len(cells) > 1 else "",
                                "grade": cells[-1] if len(cells) > 2 else "",
                            })

            all_results[sem_name] = {
                "sgpa": float(sgpa_match.group(1)) if sgpa_match else None,
                "courses": courses,
                "course_count": len(courses),
            }

        return all_results

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# ── Public API functions for FastAPI endpoints ──────────────────


async def create_session(username: str, password: str) -> PESUSession:
    """Login to PESU Academy and return an authenticated session."""
    session = PESUSession()
    success = await session.login(username, password)
    if not success:
        await session.close()
        raise Exception("Invalid PESU Academy credentials")
    return session


async def fetch_attendance(username: str, password: str) -> dict:
    """Fetch live attendance data from PESU Academy."""
    session = await create_session(username, password)
    try:
        return await session.fetch_attendance()
    finally:
        await session.close()


async def fetch_profile(username: str, password: str) -> dict:
    """Fetch live profile data from PESU Academy."""
    session = await create_session(username, password)
    try:
        return await session.fetch_profile()
    finally:
        await session.close()


async def fetch_timetable(username: str, password: str) -> dict:
    """Fetch live timetable data from PESU Academy."""
    session = await create_session(username, password)
    try:
        return await session.fetch_timetable()
    finally:
        await session.close()


async def fetch_results(username: str, password: str) -> dict:
    """Fetch live results data from PESU Academy."""
    session = await create_session(username, password)
    try:
        return await session.fetch_results()
    finally:
        await session.close()
