"""Deep dive: timetable JSON and provisional results."""
import asyncio
import json
import re
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.pesuacademy.com/Academy"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

async def test():
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        r1 = await client.get(f"{BASE_URL}/s/studentProfilePESU")
        soup1 = BeautifulSoup(r1.text, "html.parser")
        csrf = soup1.find("input", {"name": "_csrf"})
        csrf_val = csrf.get("value") if csrf else ""
        r2 = await client.post(f"{BASE_URL}/j_spring_security_check", data={
            "j_username": "pes1pg25ca005", "j_password": "Mymosi@132513", "_csrf": csrf_val,
        }, headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded", "Referer": str(r1.url)})
        soup2 = BeautifulSoup(r2.text, "html.parser")
        csrf2 = soup2.find("input", {"name": "_csrf"})
        csrf_val2 = csrf2.get("value") if csrf2 else csrf_val
        ajax = {**HEADERS, "X-Requested-With": "XMLHttpRequest", "X-CSRF-TOKEN": csrf_val2, 
                "Referer": f"{BASE_URL}/s/studentProfilePESU"}

        # ===== TIMETABLE JSON =====
        print("=== TIMETABLE JSON ===")
        r_tt = await client.get(f"{BASE_URL}/s/studentProfilePESUAdmin", params={
            "controllerMode": "6415", "actionType": "5"
        }, headers=ajax)
        soup_tt = BeautifulSoup(r_tt.text, "html.parser")
        for script in soup_tt.find_all("script"):
            text = script.string or ""
            if "timeTableTemplateDetailsJson" in text or "timeTableSubjectListJson" in text:
                # Extract all JSON arrays
                json_matches = re.findall(r'var\s+(\w+)\s*=\s*(\[.*?\]);', text, re.DOTALL)
                for var_name, json_str in json_matches:
                    try:
                        data = json.loads(json_str)
                        print(f"\n{var_name}: {len(data)} items")
                        for item in data[:3]:
                            print(f"  {json.dumps(item, indent=2)[:400]}")
                        if len(data) > 3:
                            print(f"  ... and {len(data)-3} more")
                    except json.JSONDecodeError:
                        print(f"\n{var_name}: (parse error) {json_str[:200]}")

        # ===== PROVISIONAL RESULTS =====
        print("\n\n=== provisionalResults (controllerMode=6402, actionType=53) ===")
        r = await client.post(f"{BASE_URL}/s/studentProfilePESUAdmin", data={
            "controllerMode": "6402", "actionType": "53", "_csrf": csrf_val2,
        }, headers={**ajax, "Content-Type": "application/x-www-form-urlencoded"})
        print(f"Status: {r.status_code}, Length: {len(r.text)}")
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        print(f"Tables: {len(tables)}")
        for ti, table in enumerate(tables):
            rows = table.find_all("tr")
            print(f"\nTable {ti}: {len(rows)} rows")
            for ri, row in enumerate(rows[:20]):
                cells = [c.get_text(strip=True)[:50] for c in row.find_all(["td", "th"])]
                if cells:
                    print(f"  Row {ri}: {cells}")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        print(f"\nText ({len(lines)} lines):")
        for l in lines[:15]:
            print(f"  {l[:100]}")
        
        # Try getSemesterDetails with semIds
        print("\n\n=== getSemesterDetails ===")
        for sem_id, sem_name in [("3309", "Sem-2"), ("3064", "Sem-1")]:
            r = await client.post(f"{BASE_URL}/s/studentProfilePESUAdmin", data={
                "controllerMode": "6402", "actionType": "9", "semid": sem_id, "_csrf": csrf_val2,
            }, headers={**ajax, "Content-Type": "application/x-www-form-urlencoded"})
            soup = BeautifulSoup(r.text, "html.parser")
            tables = soup.find_all("table")
            text = soup.get_text(strip=True)
            print(f"\n{sem_name} (id={sem_id}): len={len(r.text)}, tables={len(tables)}, text={text[:200]}")
            for ti, table in enumerate(tables):
                rows = table.find_all("tr")
                for row in rows[:10]:
                    cells = [c.get_text(strip=True)[:40] for c in row.find_all(["td", "th"])]
                    if cells:
                        print(f"  {cells}")

asyncio.run(test())
