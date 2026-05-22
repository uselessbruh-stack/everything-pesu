import os
import sys
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import asyncio
from api.config import cache

# Add parent directory to sys.path to allow importing scraper.py
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Try importing PESUScraper from scraper.py
try:
    from scraper import PESUScraper
except ImportError:
    PESUScraper = None

DATA_FILE_PATH = os.path.join(parent_dir, "attendance_data.json")

def load_raw_data() -> Optional[Dict[str, Any]]:
    """Loads attendance data from the JSON file"""
    if os.path.exists(DATA_FILE_PATH):
        try:
            with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON data file: {str(e)}")
            return None
    return None

def generate_class_history(course_code: str, attended_count: int, total_count: int) -> List[Dict[str, Any]]:
    """
    Generates a realistic class-by-class breakdown matching the counts.
    Distributes Present/Absent values realistically over past weeks.
    """
    classes = []
    current_date = datetime.now() - timedelta(days=1)
    
    # Generate list of statuses
    statuses = ["Present"] * attended_count + ["Absent"] * (total_count - attended_count)
    # Seed based on course_code to keep details consistent per request
    random.seed(hash(course_code))
    random.shuffle(statuses)
    
    topics = [
        "Introduction and Course Overview",
        "Fundamental Concepts & Architecture",
        "Key Methodologies & Processes",
        "Core Module Discussion",
        "Lab Practice Session 1",
        "Case Study Review",
        "Intermediate Evaluation & Review",
        "Advanced System Paradigms",
        "Implementation and Deployment",
        "Performance Analysis & Testing",
        "Optimization Techniques",
        "Lab Demonstration & Evaluation",
        "Industry Best Practices",
        "Guest Lecture Topic",
        "Project Presentations",
        "Semester End Syllabus Revision"
    ]
    
    day_offset = 0
    for idx, status in enumerate(statuses):
        # Stagger classes: roughly 2-3 per week
        day_offset += random.choice([2, 3, 2])
        class_date = current_date - timedelta(days=day_offset)
        
        # Pick topic
        topic_idx = idx % len(topics)
        topic = f"{topics[topic_idx]} (Part {idx // len(topics) + 1})" if idx >= len(topics) else topics[topic_idx]
        
        # Slot time
        time_slot = random.choice(["08:45 AM-09:45 AM", "11:15 AM-12:15 PM", "12:15 PM-01:15 PM", "02:00 PM-03:00 PM"])
        
        classes.append({
            "id": f"{course_code}_{idx}",
            "date": class_date.strftime("%Y-%m-%d"),
            "time_slot": time_slot,
            "topic": topic,
            "status": status
        })
        
    return classes

async def scrape_data_async(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Wrapper to run Selenium scraper inside an async thread pool.
    Falls back to existing JSON file if scraping fails or selenium environment is missing.
    """
    if PESUScraper is None:
        print("Warning: PESUScraper could not be imported. Falling back to mocked file.")
        return load_raw_data()
        
    def run_scraper():
        scraper = PESUScraper(username, password)
        try:
            scraper.setup_driver()
            if not scraper.login():
                scraper.close()
                return None
                
            # Fetch all items
            scraper.fetch_attendance_data()
            
            timetable = scraper.fetch_timetable_data()
            scraper.timetable_data = timetable
            
            raw_results = scraper.fetch_results_data()
            if raw_results:
                scraper.results_data = scraper.parse_results_data(raw_results)
            
            calendar = scraper.fetch_calendar_data()
            scraper.calendar_data = calendar
            
            # Save and return updated data
            result = scraper.save_full_data_to_json(
                scraper.attendance_structured,
                scraper.credentials_data,
                scraper.timetable_data,
                scraper.results_data,
                scraper.calendar_data
            )
            scraper.close()
            return result
        except Exception as ex:
            print(f"Error executing selenium scraper: {str(ex)}")
            try:
                scraper.close()
            except:
                pass
            return None

    try:
        # Run synchronous Selenium task in a separate executor thread
        loop = asyncio.get_event_loop()
        scraped_result = await loop.run_in_executor(None, run_scraper)
        if scraped_result:
            return scraped_result
    except Exception as e:
        print(f"Async scrape thread error: {str(e)}")
        
    # Return file-based fallback if scraping doesn't succeed
    return load_raw_data()
