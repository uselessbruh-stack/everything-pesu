"""
PESU Academy HTTP Scraper — direct AJAX calls to pesuacademy.com.
Discovered endpoints by reverse-engineering the JS on the student portal.
No browser needed — pure httpx + BeautifulSoup. Works on Vercel serverless.
"""

import json
import logging
import re
from datetime import datetime

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

ENDPOINTS = {
    "semesters": "/a/studentProfilePESU/getStudentSemestersPESU",
    "result_semesters": "/a/studentProfilePESU/getEsaAndIsaResultSemBySRN",
    "admin": "/s/studentProfilePESUAdmin",
}

CONTROLLER = {
    "attendance": 6407,
    "timetable": 6415,
    "results": 6402,
    "profile": 6414,
    "courses": 6403,
}

DAYS_LIST = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


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
            r1 = await self.client.get(f"{BASE_URL}/s/studentProfilePESU")
            soup = BeautifulSoup(r1.text, "html.parser")
            csrf_input = soup.find("input", {"name": "_csrf"})
            self._csrf = csrf_input.get("value", "") if csrf_input else ""

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

            soup2 = BeautifulSoup(r2.text, "html.parser")
            csrf2 = soup2.find("input", {"name": "_csrf"})
            if csrf2:
                self._csrf = csrf2.get("value", self._csrf)

            if "j_username" in r2.text:
                return False

            self.logged_in = True
            return True

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def _ajax_headers(self) -> dict:
        return {
            **HEADERS,
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-TOKEN": self._csrf,
            "Referer": f"{BASE_URL}/s/studentProfilePESU",
        }

    async def _get_semesters(self) -> list[tuple[str, str]]:
        r = await self.client.get(
            f"{BASE_URL}{ENDPOINTS['semesters']}",
            headers=self._ajax_headers(),
        )
        text = r.text.strip('"').replace('\\"', '"').replace("'", '"')
        soup = BeautifulSoup(text, "html.parser")
        return [
            (o.get("value"), o.get_text(strip=True))
            for o in soup.find_all("option")
            if o.get("value")
        ]

    async def _post_admin(self, controller_mode: int, action_type: int, **extra) -> BeautifulSoup:
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
        r = await self.client.get(
            f"{BASE_URL}{ENDPOINTS['admin']}",
            params={
                "controllerMode": str(controller_mode),
                "actionType": str(action_type),
            },
            headers=self._ajax_headers(),
        )
        return BeautifulSoup(r.text, "html.parser")

    async def _get_admin_raw(self, controller_mode: int, action_type: int) -> str:
        """GET admin endpoint, return raw text (for extracting inline JSON)."""
        r = await self.client.get(
            f"{BASE_URL}{ENDPOINTS['admin']}",
            params={
                "controllerMode": str(controller_mode),
                "actionType": str(action_type),
            },
            headers=self._ajax_headers(),
        )
        return r.text

    # ── Attendance ──────────────────────────────────────────────

    async def fetch_attendance(self, semester_id: str = None) -> dict:
        """Fetch attendance. If semester_id is None, fetches latest semester only."""
        semesters = await self._get_semesters()
        if not semesters:
            return {"summary": {}, "courses": [], "semesters": []}

        # If specific semester requested, use that; otherwise use latest (first)
        if semester_id:
            target_sems = [(sid, sname) for sid, sname in semesters if sid == semester_id]
        else:
            target_sems = [semesters[0]]  # Latest semester only

        all_courses = []
        for sem_id, sem_name in target_sems:
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
            "semesters": [{"id": sid, "name": sname} for sid, sname in semesters],
        }

    # ── Profile ─────────────────────────────────────────────────

    async def fetch_profile(self) -> dict:
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
        """Fetch timetable by parsing inline JSON from the timetable page."""
        raw_html = await self._get_admin_raw(CONTROLLER["timetable"], 5)
        soup = BeautifulSoup(raw_html, "html.parser")

        # Extract metadata
        text = soup.get_text(separator="\n", strip=True)
        batch_match = re.search(r"Batch:\s*(.+)", text)
        room_match = re.search(r"Room:\s*(.+)", text)
        section_match = re.search(r"Section:\s*(.+)", text)

        timetable = {
            "batch": batch_match.group(1).strip() if batch_match else "",
            "room": room_match.group(1).strip() if room_match else "",
            "section": section_match.group(1).strip() if section_match else "",
        }

        # Parse inline script for JSON data
        time_slots = []
        schedule_data = {}

        for script in soup.find_all("script"):
            js = script.string or ""
            if "timeTableTemplateDetailsJson" not in js:
                continue

            # Extract timeTableTemplateDetailsJson (time slot definitions)
            match = re.search(
                r'var\s+timeTableTemplateDetailsJson\s*=\s*(\[.*?\])\s*;', js, re.DOTALL
            )
            if match:
                try:
                    raw_slots = json.loads(match.group(1))
                    # Each slot has startTime, endTime, orderedBy, type
                    # type=2 is a regular class slot, type=1 seems to be break
                    for slot in raw_slots:
                        start = slot.get("startTime", "")
                        end = slot.get("endTime", "")
                        order = slot.get("orderedBy", 0)
                        slot_type = slot.get("type", 2)
                        desc = slot.get("timeTableTemplateDetailsDescription", "")
                        time_slots.append({
                            "start": start,
                            "end": end,
                            "order": order,
                            "type": slot_type,
                            "description": desc,
                        })
                except (json.JSONDecodeError, KeyError):
                    pass

            # Extract timeTableJson (subject assignments)
            # Keys: ttDivText_{day}_{slot}_{section}
            # Values: ["ttSubject_&&CODE-NAME", "ttFaculty_1_&&FACULTY NAME"]
            match2 = re.search(
                r'var\s+timeTableJson\s*=\s*(\{.*?\})\s*;', js, re.DOTALL
            )
            if match2:
                try:
                    schedule_data = json.loads(match2.group(1))
                except json.JSONDecodeError:
                    pass

        # Build structured schedule from the JSON data
        # Sort time slots by order
        time_slots.sort(key=lambda s: s["order"])

        # Filter to class slots only (type=2), skip breaks
        class_slots = [s for s in time_slots if s.get("type") == 2]

        schedule = {}
        for day_idx, day_name in enumerate(DAYS_LIST):
            day_num = day_idx + 1  # 1-indexed
            day_classes = []

            for slot_idx, slot in enumerate(class_slots):
                slot_num = slot_idx + 1
                # Try keys: ttDivText_{day}_{slot}_1
                key = f"ttDivText_{day_num}_{slot_num}_1"
                if key not in schedule_data:
                    # Also try with the raw orderedBy as slot index
                    key = f"ttDivText_{day_num}_{slot['order']}_1"
                if key not in schedule_data:
                    continue

                entries = schedule_data[key]
                subject = ""
                faculty = ""
                course_code = ""
                course_name = ""

                for entry in entries:
                    if "ttSubject_" in entry:
                        # Format: "ttSubject_&&UQ25CA652B-DATA COMMUNICATION..."
                        subj_raw = entry.split("&&", 1)[-1] if "&&" in entry else entry
                        parts = subj_raw.split("-", 1)
                        course_code = parts[0].strip()
                        course_name = parts[1].strip().title() if len(parts) > 1 else subj_raw
                    elif "ttFaculty_" in entry:
                        faculty = entry.split("&&", 1)[-1].strip().title() if "&&" in entry else ""

                if course_code:
                    # Clean time: "08:45:13 AM" → "08:45 AM"
                    start_time = re.sub(r':(\d{2}) (AM|PM)', r' \2', slot["start"]).strip()
                    end_time = re.sub(r':(\d{2}) (AM|PM)', r' \2', slot["end"]).strip()
                    day_classes.append({
                        "time": f"{start_time} - {end_time}",
                        "course_code": course_code,
                        "course_name": course_name,
                        "instructor": faculty,
                    })

            if day_classes:
                schedule[day_name] = day_classes

        timetable["schedule"] = schedule
        return timetable

    # ── Results ─────────────────────────────────────────────────

    async def fetch_results(self, semester_id: str = None) -> dict:
        """Fetch results. If semester_id=None, use provisionalResults for latest."""
        # Get semester list for results
        r = await self.client.get(
            f"{BASE_URL}{ENDPOINTS['result_semesters']}",
            headers=self._ajax_headers(),
        )
        text = r.text.strip('"').replace('\\"', '"').replace("'", '"')
        soup = BeautifulSoup(text, "html.parser")
        semesters = [
            (o.get("value"), o.get_text(strip=True))
            for o in soup.find_all("option")
            if o.get("value")
        ]

        all_results = {}

        if semester_id:
            # Fetch specific semester
            target_sems = [(sid, sname) for sid, sname in semesters if sid == semester_id]
        else:
            # Fetch only latest (first) semester
            target_sems = [semesters[0]] if semesters else []

        for sem_id, sem_name in target_sems:
            result = await self._fetch_semester_results(sem_id, sem_name)
            all_results[sem_name] = result

        # Also try provisionalResults for overall data
        if not semester_id:
            prov = await self._fetch_provisional_results()
            if prov:
                # Merge provisional data with semester data
                for sem_name, prov_data in prov.items():
                    if sem_name not in all_results:
                        all_results[sem_name] = prov_data
                    else:
                        # Merge grades into existing data
                        existing = all_results[sem_name]
                        if not existing.get("sgpa") and prov_data.get("sgpa"):
                            existing["sgpa"] = prov_data["sgpa"]
                        if not existing.get("cgpa") and prov_data.get("cgpa"):
                            existing["cgpa"] = prov_data["cgpa"]
                        # Add grades to courses
                        grade_map = {c["course_code"]: c.get("grade", "") for c in prov_data.get("courses", [])}
                        for course in existing.get("courses", []):
                            if course["course_code"] in grade_map and not course.get("grade"):
                                course["grade"] = grade_map[course["course_code"]]

        return {
            "results": all_results,
            "semesters": [{"id": sid, "name": sname} for sid, sname in semesters],
        }

    async def _fetch_provisional_results(self) -> dict:
        """Fetch provisional results (actionType=53)."""
        soup = await self._post_admin(CONTROLLER["results"], 53)
        text = soup.get_text(separator="\n", strip=True)

        # Parse SGPA, CGPA, semester info
        sgpa_match = re.search(r"SGPA\s*[:\n]*\s*([\d.]+)", text, re.IGNORECASE)
        cgpa_match = re.search(r"CGPA\s*[:\n]*\s*([\d.]+)", text, re.IGNORECASE)
        sem_match = re.search(r"(\d+)\s*Sem", text)
        earned_match = re.search(r"EARNED\s*[:\n]*\s*([\d.]+)", text, re.IGNORECASE)

        # Parse course grades from table
        courses = []
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = [c.get_text(strip=True) for c in row.find_all("td")]
                if len(cells) >= 4:
                    code = cells[1] if cells[1] else ""
                    name = cells[2] if len(cells) > 2 else ""
                    grade = cells[3] if len(cells) > 3 else ""
                    if code and re.match(r"[A-Z]{2}\d{2}", code):
                        courses.append({
                            "course_code": code,
                            "course_name": name,
                            "grade": grade,
                        })

        if not courses:
            return {}

        sem_name = f"Sem-{sem_match.group(1)}" if sem_match else "Unknown"
        return {
            sem_name: {
                "sgpa": float(sgpa_match.group(1)) if sgpa_match else None,
                "cgpa": float(cgpa_match.group(1)) if cgpa_match else None,
                "earned_credits": earned_match.group(1) if earned_match else None,
                "courses": courses,
                "course_count": len(courses),
                "type": "provisional",
            }
        }

    async def _fetch_semester_results(self, sem_id: str, sem_name: str) -> dict:
        """Fetch results for a specific semester (actionType=9, semid=...)."""
        soup = await self._post_admin(CONTROLLER["results"], 9, semid=sem_id)
        text = soup.get_text(separator="\n", strip=True)

        # Parse SGPA/CGPA
        sgpa_match = re.search(r"SGPA\s*[:\n]*\s*([\d.]+)", text, re.IGNORECASE)
        cgpa_match = re.search(r"CGPA\s*[:\n]*\s*([\d.]+)", text, re.IGNORECASE)

        # Parse courses - the text pattern is:
        # COURSE_CODE \n-\nCourse Name\n ISA 1\n score\n /max\n FINAL ISA\n score\n ESA\n score_or_NA
        courses = []
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        i = 0
        while i < len(lines):
            # Look for course code pattern
            if re.match(r"^[A-Z]{2}\d{2}[A-Z]{2}\d{3}", lines[i]):
                code = lines[i]
                name = ""
                assessments = {}

                # Next line should be "-" then course name
                if i + 1 < len(lines) and lines[i + 1] == "-":
                    name = lines[i + 2] if i + 2 < len(lines) else ""
                    j = i + 3
                elif i + 1 < len(lines):
                    name = lines[i + 1].lstrip("- ").strip()
                    j = i + 2
                else:
                    j = i + 1

                # Parse assessment pairs
                while j < len(lines):
                    line = lines[j]
                    if re.match(r"^[A-Z]{2}\d{2}[A-Z]{2}\d{3}", line):
                        break  # Next course
                    if line in ("ISA 1", "ISA 2", "FINAL ISA", "ESA", "ISA"):
                        label = line
                        if j + 1 < len(lines):
                            score_str = lines[j + 1]
                            max_str = ""
                            if j + 2 < len(lines) and lines[j + 2].startswith("/"):
                                max_str = lines[j + 2].lstrip("/")
                                j += 1
                            assessments[label] = {
                                "score": score_str,
                                "max": max_str,
                            }
                            j += 1
                    j += 1

                courses.append({
                    "course_code": code,
                    "course_name": name,
                    "assessments": assessments,
                    "grade": "",
                })
                i = j
                continue
            i += 1

        return {
            "sgpa": float(sgpa_match.group(1)) if sgpa_match else None,
            "cgpa": float(cgpa_match.group(1)) if cgpa_match else None,
            "courses": courses,
            "course_count": len(courses),
            "type": "detailed",
        }

    # ── Courses ─────────────────────────────────────────────────

    async def fetch_courses(self, semester_id: str = None) -> dict:
        """Fetch course list for a semester."""
        semesters = await self._get_semesters()
        if not semesters:
            return {"courses": [], "semesters": []}

        if semester_id:
            target_sems = [(sid, sname) for sid, sname in semesters if sid == semester_id]
        else:
            target_sems = [semesters[0]]

        courses = []
        for sem_id, sem_name in target_sems:
            # Use attendance data which has course codes and names
            soup = await self._post_admin(
                CONTROLLER["attendance"], 8, batchClassId=sem_id
            )
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all("td")]
                    if len(cells) >= 2:
                        courses.append({
                            "course_code": cells[0],
                            "course_name": cells[1],
                            "semester": sem_name,
                        })

        return {
            "courses": courses,
            "semesters": [{"id": sid, "name": sname} for sid, sname in semesters],
        }

    async def close(self):
        await self.client.aclose()


# ── Public API functions ──────────────────────────────────────


async def create_session(username: str, password: str) -> PESUSession:
    session = PESUSession()
    success = await session.login(username, password)
    if not success:
        await session.close()
        raise Exception("Invalid PESU Academy credentials")
    return session


async def fetch_attendance(username: str, password: str, semester_id: str = None) -> dict:
    session = await create_session(username, password)
    try:
        return await session.fetch_attendance(semester_id)
    finally:
        await session.close()


async def fetch_profile(username: str, password: str) -> dict:
    session = await create_session(username, password)
    try:
        return await session.fetch_profile()
    finally:
        await session.close()


async def fetch_timetable(username: str, password: str) -> dict:
    session = await create_session(username, password)
    try:
        return await session.fetch_timetable()
    finally:
        await session.close()


async def fetch_results(username: str, password: str, semester_id: str = None) -> dict:
    session = await create_session(username, password)
    try:
        return await session.fetch_results(semester_id)
    finally:
        await session.close()


async def fetch_courses(username: str, password: str, semester_id: str = None) -> dict:
    session = await create_session(username, password)
    try:
        return await session.fetch_courses(semester_id)
    finally:
        await session.close()
