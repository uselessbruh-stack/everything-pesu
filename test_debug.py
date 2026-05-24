"""Get full timetable JSON and all variables from the script."""
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

        # Get full timetable HTML to find all JSON vars
        r_tt = await client.get(f"{BASE_URL}/s/studentProfilePESUAdmin", params={
            "controllerMode": "6415", "actionType": "5"
        }, headers=ajax)
        soup_tt = BeautifulSoup(r_tt.text, "html.parser")
        
        for script in soup_tt.find_all("script"):
            text = script.string or ""
            if "timeTable" in text or "days" in text:
                # Find ALL var assignments
                all_vars = re.findall(r'var\s+(\w+)\s*=\s*', text)
                print(f"Variables found: {all_vars}")
                
                # Extract JSON for each
                for var_name in all_vars:
                    # Try to extract value (could be JSON or simple)
                    match = re.search(rf'var\s+{var_name}\s*=\s*([\[\{{].*?[\]\}}])\s*;', text, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            if isinstance(data, list) and len(data) > 0:
                                print(f"\n{var_name}: {len(data)} items, type={type(data[0]).__name__}")
                                for item in data[:2]:
                                    s = json.dumps(item, indent=2)
                                    print(f"  {s[:500]}")
                            elif isinstance(data, dict):
                                print(f"\n{var_name}: dict, keys={list(data.keys())[:10]}")
                                print(f"  {json.dumps(data, indent=2)[:500]}")
                        except json.JSONDecodeError:
                            val = match.group(1)[:200]
                            print(f"\n{var_name}: (not JSON) {val}")
                    else:
                        # Simple var
                        match2 = re.search(rf'var\s+{var_name}\s*=\s*([^;]+);', text)
                        if match2:
                            val = match2.group(1).strip()
                            if len(val) < 100:
                                print(f"\n{var_name} = {val}")

        # Also try getSemesterDetails for Sem-2 to get ISA marks
        print("\n\n=== getSemesterDetails Sem-2 full response ===")
        r = await client.post(f"{BASE_URL}/s/studentProfilePESUAdmin", data={
            "controllerMode": "6402", "actionType": "9", "semid": "3309", "_csrf": csrf_val2,
        }, headers={**ajax, "Content-Type": "application/x-www-form-urlencoded"})
        soup = BeautifulSoup(r.text, "html.parser")
        # Find all course blocks
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        print(f"Lines: {len(lines)}")
        for l in lines[:50]:
            print(f"  {l[:100]}")

asyncio.run(test())
