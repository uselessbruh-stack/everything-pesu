"""
PESU Academy Attendance Scraper
Fetches and displays attendance data from PESU Academy
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
from datetime import datetime
import json
import re

class PESUScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.attendance_data = []
        self.min_attendance_percentage = 85  # Minimum required attendance
        self.attendance_structured = None
        self.credentials_data = None
        self.timetable_data = None
        self.results_data = None
        self.calendar_data = None
        
    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Chrome driver initialized")
        
    def login(self):
        """Login to PESU Academy"""
        try:
            print("\n📍 Navigating to PESU Academy...")
            self.driver.get("https://www.pesuacademy.com/Academy/s/studentProfilePESU")
            time.sleep(4)
            
            # Get page title
            print(f"Page title: {self.driver.title}")
            
            # Use the correct selectors discovered from page inspection
            print("\n🔐 Attempting to login...")
            
            try:
                # Fill username using name='j_username'
                username_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "j_username"))
                )
                username_field.clear()
                username_field.send_keys(self.username)
                print("✓ Username entered")
            except Exception as e:
                print(f"❌ Could not fill username: {str(e)}")
                return False
            
            time.sleep(1)
            
            try:
                # Fill password using name='j_password'
                password_field = self.driver.find_element(By.NAME, "j_password")
                password_field.clear()
                password_field.send_keys(self.password)
                print("✓ Password entered")
            except Exception as e:
                print(f"❌ Could not fill password: {str(e)}")
                return False
            
            time.sleep(1)
            
            try:
                # Click sign in button with id='postloginform#/Academy/j_spring_security_check'
                login_button = self.driver.find_element(By.ID, "postloginform#/Academy/j_spring_security_check")
                login_button.click()
                print("✓ Login button clicked")
            except Exception as e:
                print(f"❌ Could not click login button: {str(e)}")
                return False
            
            # Wait for dashboard to load
            print("⏳ Waiting for dashboard to load...")
            time.sleep(6)
            

            print("✓ Login successful!")
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def fetch_credentials(self):
        """Extract credentials from home page"""
        try:
            print("\n🔐 Fetching credentials...")
            
            # Wait for page to load
            time.sleep(2)
            
            # Get page text
            body = self.driver.find_element(By.TAG_NAME, "body")
            page_text = body.text
            page_html = self.driver.page_source
            
            credentials = {}
            
            # Parse Teams credentials - extract from text
            if "MS Teams" in page_html:
                # Try to extract from text
                teams_match = re.search(r'Username\s*:\s*([^\n]+)', page_text)
                if teams_match:
                    credentials["teams"] = {
                        "username": teams_match.group(1).strip(),
                        "note": "For MS Teams"
                    }
            
            # Parse Internet Portal credentials
            if "Internet Captive Portal" in page_html or "Captive Portal" in page_text:
                credentials["portal"] = {
                    "username": self.username.upper(),
                    "note": "For Internet Captive Portal Login"
                }
            
            # Parse WiFi credentials
            if "WIFI" in page_html or "SSID" in page_text:
                ssid_match = re.search(r'SSID[:\s]+([^\n]+)', page_text)
                wifi_pass = re.search(r'Password[:\s]+([^\n]+)', page_text)
                
                credentials["wifi"] = {
                    "ssid": ssid_match.group(1).strip() if ssid_match else "GJBC-MCA",
                    "password": wifi_pass.group(1).strip() if wifi_pass else self.username.upper(),
                    "note": "WiFi Network"
                }
            
            print(f"✓ Found {len(credentials)} credential types")
            return credentials
            
        except Exception as e:
            print(f"⚠️  Error fetching credentials: {str(e)}")
            return {}
    
    def fetch_attendance_data(self):
        """Scrape attendance data from the dashboard"""
        try:
            print("\n📊 Fetching attendance data...")
            
            # First fetch credentials from home page
            credentials = self.fetch_credentials()
            
            # Click on "My Attendance" menu item
            print("🔍 Looking for 'My Attendance' menu...")
            try:
                # Look for "My Attendance" link
                attendance_link = None
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    if "attendance" in link.text.lower():
                        attendance_link = link
                        print(f"Found link: {link.text}")
                        break
                
                if attendance_link:
                    # Use JavaScript click if regular click is intercepted
                    try:
                        attendance_link.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", attendance_link)
                    print("✓ Clicked 'My Attendance'")
                    time.sleep(3)
                else:
                    print("❌ Could not find 'My Attendance' link")
                    return False
                    
            except Exception as e:
                print(f"Error clicking attendance link: {str(e)}")
                return False
            

            
            # Try to find tables with attendance data
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"\n📋 Found {len(tables)} tables on attendance page")
            
            attendance_data = []
            
            if tables:
                for table_idx, table in enumerate(tables):
                    print(f"\n--- Table {table_idx + 1} ---")
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"Rows: {len(rows)}")
                    
                    # Extract all rows
                    table_data = []
                    for row_idx, row in enumerate(rows):
                        cells = row.find_elements(By.TAG_NAME, "td")
                        headers = row.find_elements(By.TAG_NAME, "th")
                        
                        cell_list = cells if cells else headers
                        if cell_list:
                            row_data = [cell.text.strip() for cell in cell_list]
                            table_data.append(row_data)
                            print(f"Row {row_idx + 1}: {row_data}")
                    
                    attendance_data.append(table_data)
            
            # Look for divs or other elements with attendance info
            print("\n🔎 Looking for attendance elements...")
            divs_with_text = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'attendance')]")
            print(f"Found {len(divs_with_text)} elements mentioning 'attendance'")
            
            # Get body text for additional info
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                all_text = body.text
                if all_text:
                    print(f"\n📝 Full page text preview:\n{all_text[:2000]}")
            except:
                pass
            
            # Parse and save as structured JSON with credentials
            structured_data = self.parse_attendance_data(attendance_data)
            if structured_data:
                # Save with timetable (we'll get it after)
                self.attendance_structured = structured_data
                self.credentials_data = credentials
            
            return True
            
        except Exception as e:
            print(f"❌ Error fetching attendance data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_attendance_to_csv(self, data):
        """Save attendance data to CSV file (deprecated - JSON only)"""
        pass
    
    def parse_attendance_data(self, raw_table_data):
        """Parse raw table data into structured format"""
        structured_data = []
        
        if not raw_table_data or len(raw_table_data) == 0:
            return structured_data
        
        # First table contains attendance data
        table = raw_table_data[0]
        
        # Skip header row (row 0)
        for row in table[1:]:
            if len(row) >= 4:
                course_code = row[0].strip()
                course_name = row[1].strip()
                classes_str = row[2].strip()  # e.g., "14/19"
                percentage_str = row[3].strip()  # e.g., "73"
                
                try:
                    # Parse "attended/total" format
                    attended, total = map(int, classes_str.split('/'))
                    percentage = int(percentage_str)
                    
                    # Calculate shortage
                    required_classes = (self.min_attendance_percentage * total) // 100
                    shortage = max(0, required_classes - attended)
                    
                    # Determine status
                    status = "✓ Pass" if percentage >= self.min_attendance_percentage else "✗ Below Required"
                    
                    course_data = {
                        "course_code": course_code,
                        "course_name": course_name,
                        "attendance": {
                            "attended": attended,
                            "total": total,
                            "percentage": percentage
                        },
                        "requirement": {
                            "minimum_percentage": self.min_attendance_percentage,
                            "required_classes": required_classes,
                            "shortage": shortage
                        },
                        "status": status
                    }
                    
                    structured_data.append(course_data)
                except ValueError:
                    print(f"⚠️  Could not parse row: {row}")
                    continue
        
        return structured_data
    
    def calculate_summary(self, structured_data):
        """Calculate overall attendance summary"""
        if not structured_data:
            return {}
        
        total_attended = sum(course["attendance"]["attended"] for course in structured_data)
        total_classes = sum(course["attendance"]["total"] for course in structured_data)
        overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
        
        courses_below_requirement = sum(1 for course in structured_data 
                                       if course["attendance"]["percentage"] < self.min_attendance_percentage)
        total_shortage = sum(course["requirement"]["shortage"] for course in structured_data)
        
        return {
            "total_attended": total_attended,
            "total_classes": total_classes,
            "overall_percentage": round(overall_percentage, 2),
            "courses_count": len(structured_data),
            "courses_below_requirement": courses_below_requirement,
            "total_shortage": total_shortage
        }
    
    def save_attendance_to_json(self, structured_data, credentials=None):
        """Save attendance data as JSON"""
        try:
            print("\n💾 Saving attendance data to JSON...")
            
            # Calculate summary
            summary = self.calculate_summary(structured_data)
            
            # Create final output structure
            output = {
                "user": {
                    "username": self.username,
                    "timestamp": datetime.now().isoformat()
                },
                "credentials": credentials or {},
                "summary": summary,
                "courses": structured_data
            }
            
            # Save to JSON file
            filename = "attendance_data.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved: {filename}")
            
            # Pretty print to console
            print("\n" + "="*80)
            print("📊 ATTENDANCE SUMMARY")
            print("="*80)
            print(f"Overall Attendance: {summary['overall_percentage']}%")
            print(f"Total Classes: {summary['total_attended']}/{summary['total_classes']}")
            print(f"Courses: {summary['courses_count']}")
            print(f"Courses Below {self.min_attendance_percentage}%: {summary['courses_below_requirement']}")
            print(f"Total Classes Need to Attend: {summary['total_shortage']}")
            print("="*80 + "\n")
            
            # Print credentials
            if credentials:
                print("🔐 CREDENTIALS")
                print("-"*80)
                if "teams" in credentials:
                    print(f"\n📱 Teams ({credentials['teams'].get('note', '')})")
                    print(f"   Username: {credentials['teams'].get('username', 'N/A')}")
                
                if "portal" in credentials:
                    print(f"\n🌐 Portal ({credentials['portal'].get('note', '')})")
                    print(f"   Username: {credentials['portal'].get('username', 'N/A')}")
                
                if "wifi" in credentials:
                    print(f"\n📡 WiFi ({credentials['wifi'].get('note', '')})")
                    print(f"   SSID: {credentials['wifi'].get('ssid', 'N/A')}")
                    print(f"   Password: {credentials['wifi'].get('password', 'N/A')}")
                print("-"*80 + "\n")
            
            # Print individual courses
            print("📋 COURSE-WISE BREAKDOWN:")
            print("-"*100)
            for i, course in enumerate(structured_data, 1):
                print(f"\n{i}. {course['course_name']} ({course['course_code']})")
                print(f"   Attendance: {course['attendance']['attended']}/{course['attendance']['total']} ({course['attendance']['percentage']}%)")
                print(f"   Status: {course['status']}")
                if course['requirement']['shortage'] > 0:
                    print(f"   ⚠️  Need {course['requirement']['shortage']} more class(es) to reach {self.min_attendance_percentage}%")
            print("-"*100)
            
            return output
            
        except Exception as e:
            print(f"Error saving JSON: {str(e)}")
    
    def fetch_timetable_data(self):
        """Scrape timetable data from the dashboard"""
        try:
            print("\n📅 Fetching timetable data...")
            
            # Click on "Time Table" menu item
            print("🔍 Looking for 'Time Table' menu...")
            try:
                # Look for "Time Table" link
                timetable_link = None
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    if "time table" in link.text.lower() or "timetable" in link.text.lower():
                        timetable_link = link
                        print(f"Found link: {link.text}")
                        break
                
                if timetable_link:
                    timetable_link.click()
                    print("✓ Clicked 'Time Table'")
                    time.sleep(3)
                else:
                    print("⚠️  Could not find 'Time Table' link")
                    return {}
                    
            except Exception as e:
                print(f"Error clicking timetable link: {str(e)}")
                return {}
            

            
            # Try to find tables with timetable data
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"\n📋 Found {len(tables)} tables on timetable page")
            
            timetable_data = []
            
            if tables:
                for table_idx, table in enumerate(tables):
                    print(f"\n--- Table {table_idx + 1} ---")
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"Rows: {len(rows)}")
                    
                    # Extract all rows
                    table_data = []
                    for row_idx, row in enumerate(rows):
                        cells = row.find_elements(By.TAG_NAME, "td")
                        headers = row.find_elements(By.TAG_NAME, "th")
                        
                        cell_list = cells if cells else headers
                        if cell_list:
                            row_data = [cell.text.strip() for cell in cell_list]
                            table_data.append(row_data)
                            print(f"Row {row_idx + 1}: {row_data}")
                    
                    timetable_data.append(table_data)
            
            # Get body text for additional info
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                all_text = body.text
                if all_text:
                    print(f"\n📝 Full page text preview:\n{all_text[:2000]}")
            except:
                pass
            
            # Parse timetable data into structured format
            structured_timetable = self.parse_timetable_data(timetable_data)
            return structured_timetable
            
        except Exception as e:
            print(f"❌ Error fetching timetable data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def parse_timetable_data(self, raw_table_data):
        """Parse raw timetable data into structured format"""
        structured_data = {}
        
        if not raw_table_data or len(raw_table_data) == 0:
            return structured_data
        
        try:
            table = raw_table_data[0]
            if len(table) < 2:
                return structured_data
            
            # First row contains time slots
            time_slots = table[0][1:]  # Skip first empty cell
            
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            
            # Parse schedule for each day
            for row_idx in range(1, len(table)):
                row = table[row_idx]
                if row and row[0] in days:
                    day = row[0]
                    day_schedule = {}
                    
                    # Map time slots to classes
                    for time_idx, time_slot in enumerate(time_slots):
                        if time_idx + 1 < len(row):
                            class_info = row[time_idx + 1].strip()
                            if class_info and class_info not in ["Break", "No Schedule"]:
                                day_schedule[time_slot] = class_info
                    
                    if day_schedule:
                        structured_data[day] = day_schedule
            
        except Exception as e:
            print(f"Error parsing timetable: {str(e)}")
        
        return structured_data
    
    def save_full_data_to_json(self, attendance_data, credentials, timetable_data, results_data=None, calendar_data=None):
        """Save all data (attendance, credentials, timetable, results, calendar) as JSON"""
        try:
            print("\n💾 Saving complete data to JSON...")
            
            # Calculate summary
            summary = self.calculate_summary(attendance_data)
            
            # Create final output structure
            output = {
                "user": {
                    "username": self.username,
                    "timestamp": datetime.now().isoformat()
                },
                "credentials": credentials or {},
                "summary": summary,
                "courses": attendance_data,
                "timetable": timetable_data or {},
                "results": results_data or {},
                "calendar": calendar_data or {"events": [], "event_count": 0}
            }
            
            # Save to JSON file
            filename = "attendance_data.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved: {filename}")
            
            # Print timetable if available
            if timetable_data:
                print("\n📅 TIMETABLE")
                print("-"*80)
                for day, schedule in timetable_data.items():
                    print(f"\n{day}:")
                    for time_slot, class_info in schedule.items():
                        # Extract course code
                        course_code = class_info.split("-")[0] if "-" in class_info else class_info
                        print(f"  {time_slot}: {course_code}")
                print("-"*80)
            
            # Print results if available
            if results_data:
                print("\n🎓 RESULTS BY SEMESTER")
                print("-"*80)
                for semester, sem_data in results_data.items():
                    print(f"\n{semester} ({sem_data.get('type', 'unknown')} semester):")
                    print(f"  Total Courses: {sem_data.get('course_count', 0)}")
                    
                    for course_idx, course in enumerate(sem_data.get('courses', []), 1):
                        print(f"\n    {course_idx}. {course['course_code']} - {course['course_name']}")
                        
                        # Display assessments with marks if available
                        assessments = course.get('assessments', {})
                        marks = course.get('marks', {})
                        
                        if assessments:
                            print(f"       Assessments:")
                            for assessment_name, assessment_value in assessments.items():
                                # Display formatted marks
                                if assessment_name in marks:
                                    mark_info = marks[assessment_name]
                                    if 'obtained' in mark_info and 'total' in mark_info:
                                        print(f"         • {assessment_name}: {mark_info['obtained']} / {mark_info['total']}")
                                    else:
                                        print(f"         • {assessment_name}: {mark_info.get('raw', assessment_value)}")
                                else:
                                    print(f"         • {assessment_name}: {assessment_value}")
                        else:
                            print(f"       (No assessment data available yet)")
                
                print("-"*80)
            
            # Print calendar events if available
            if calendar_data and calendar_data.get('event_count', 0) > 0:
                print("\n📆 CALENDAR EVENTS")
                print("-"*80)
                print(f"Total Events: {calendar_data.get('event_count', 0)}\n")
                
                for event_idx, event in enumerate(calendar_data.get('events', [])[:20], 1):  # Show first 20
                    event_date = event.get('date', 'Unknown date')
                    event_desc = event.get('description', event.get('raw_text', 'No description'))
                    
                    # Truncate long descriptions
                    if len(event_desc) > 70:
                        event_desc = event_desc[:70] + "..."
                    
                    print(f"{event_idx}. [{event_date}] {event_desc}")
                
                if calendar_data.get('event_count', 0) > 20:
                    print(f"\n... and {calendar_data.get('event_count', 0) - 20} more events")
                
                print("-"*80)
            
            return output
            
        except Exception as e:
            print(f"Error saving JSON: {str(e)}")
    
    def fetch_results_data(self):
        """Scrape results data for all semesters"""
        try:
            print("\n🎓 Fetching results data...")
            
            # Click on "Results" menu item
            print("🔍 Looking for 'Results' menu...")
            try:
                results_link = None
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    link_text = link.text.lower()
                    if "result" in link_text or "grade" in link_text:
                        results_link = link
                        print(f"Found link: {link.text}")
                        break
                
                if results_link:
                    try:
                        results_link.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", results_link)
                    print("✓ Clicked 'Results'")
                    time.sleep(4)
                else:
                    print("⚠️  Could not find 'Results' link")
                    return {}
                    
            except Exception as e:
                print(f"Error clicking results link: {str(e)}")
                return {}
            

            
            # Look for semester selector (dropdown or tabs)
            all_results = {}
            
            # Try to find select/dropdown for semesters
            try:
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                print(f"Found {len(selects)} select elements")
                
                semester_select = None
                for select in selects:
                    try:
                        options = select.find_elements(By.TAG_NAME, "option")
                        if len(options) > 1:
                            semester_select = select
                            print(f"Found semester selector with {len(options)} options")
                            break
                    except:
                        continue
                
                if semester_select:
                    # Get all options
                    options = semester_select.find_elements(By.TAG_NAME, "option")
                    semesters = [(opt.get_attribute("value"), opt.text) for opt in options if opt.get_attribute("value")]
                    
                    print(f"🔍 Found {len(semesters)} semesters: {[s[1] for s in semesters]}")
                    
                    # Fetch results for each semester
                    for semester_value, semester_label in semesters:
                        try:
                            # Re-find the select in case DOM changed
                            selects = self.driver.find_elements(By.TAG_NAME, "select")
                            semester_select = selects[0]
                            
                            # Select semester
                            from selenium.webdriver.support.ui import Select
                            Select(semester_select).select_by_value(semester_value)
                            print(f"\n📋 Fetching results for: {semester_label}")
                            
                            # Wait for results to load
                            time.sleep(3)
                            
                            # Extract results table
                            results_table = self._extract_results_table()
                            if results_table:
                                all_results[semester_label] = results_table
                                print(f"✓ Extracted {len(results_table.get('data', []))} courses for {semester_label}")
                            else:
                                print(f"⚠️  No results table found for {semester_label}")
                        except Exception as e:
                            print(f"⚠️  Error fetching semester {semester_label}: {str(e)}")
                            continue
                else:
                    # No semester selector, try to extract results directly
                    print("⚠️  No semester selector found, extracting results from current view...")
                    results_table = self._extract_results_table()
                    if results_table:
                        all_results["Current"] = results_table
                        
            except Exception as e:
                print(f"Error finding semester selector: {str(e)}")
                # Try direct extraction
                results_table = self._extract_results_table()
                if results_table:
                    all_results["Current"] = results_table
            
            return all_results
            
        except Exception as e:
            print(f"❌ Error fetching results data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _extract_results_table(self):
        """Extract results from current page view - handles both complete and incomplete semesters"""
        try:
            print("  🔎 Searching for result elements...")
            
            # Try multiple strategies to find results
            # Strategy 1: Look for elem-info-wrapper class
            result_elements = self.driver.find_elements(By.CLASS_NAME, "elem-info-wrapper")
            print(f"  Found {len(result_elements)} elem-info-wrapper elements")
            
            # Strategy 2: Look for divs containing course information
            if not result_elements or len(result_elements) < 1:
                # Try finding divs with course codes
                all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                result_elements = [d for d in all_divs if "UQ25CA" in d.text or "CS25" in d.text]
                print(f"  Found {len(result_elements)} divs with course codes")
            
            if not result_elements:
                print("  ❌ No result elements found")
                return None
            
            # Get all text from all result elements (they may contain multiple courses)
            all_text = ""
            for elem in result_elements:
                elem_text = elem.text.strip()
                if elem_text:
                    all_text += "\n" + elem_text
            
            if not all_text or len(all_text) < 10:
                print("  ❌ No meaningful content in result elements")
                return None
            
            # Parse all courses from the combined text
            results_data = self._parse_results_text(all_text)
            
            if results_data:
                print(f"  ✅ Successfully extracted {len(results_data)} courses")
                return {
                    "headers": ["Course Code", "Course Name", "Assessments"],
                    "data": results_data
                }
            
            return None
            
        except Exception as e:
            print(f"Error extracting results table: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_results_text(self, text):
        """Parse results text to extract all courses with their assessment data"""
        results_data = []
        
        try:
            import re
            # Find all course code patterns
            course_pattern = r'([A-Z]{2}\d{2}[A-Z]{2}\d{3}[A-Z]?\d?)\s*-\s*([^\n]+)'
            courses = re.finditer(course_pattern, text)
            
            course_list = list(courses)
            print(f"  Found {len(course_list)} course patterns in text")
            
            for idx, match in enumerate(course_list):
                try:
                    course_code = match.group(1).strip()
                    course_name = match.group(2).strip()
                    
                    # Get position of this course
                    start_pos = match.end()
                    
                    # Get position of next course (or end of text)
                    if idx + 1 < len(course_list):
                        end_pos = course_list[idx + 1].start()
                    else:
                        end_pos = len(text)
                    
                    # Extract content for this course
                    course_content = text[start_pos:end_pos]
                    
                    # Parse assessments - handle both formats:
                    # Format 1: "Assessment: Marks" (colon separated)
                    # Format 2: "Assessment\nMarks" (newline separated)
                    assessments = {}
                    lines = course_content.split('\n')
                    
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        
                        if not line or len(line) < 2:
                            i += 1
                            continue
                        
                        # Skip metadata
                        if any(skip in line.lower() for skip in ['disclaimer', 'tal -', 'incase of', '* tal']):
                            i += 1
                            continue
                        
                        # Format 1: "Assessment: Marks"
                        if ':' in line:
                            try:
                                key, value = line.split(':', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                if len(value) > 0 and key.lower() not in ['disclaimer', 'note']:
                                    assessments[key] = value
                            except:
                                pass
                            i += 1
                            continue
                        
                        # Format 2: "Assessment\nMarks" (look ahead for marks)
                        # Check if this line is an assessment name (not a mark value)
                        is_assessment_name = not re.match(r'^\d+|^[A-Z]$|^NA$', line) and len(line) > 1
                        
                        if is_assessment_name and i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            # Check if next line looks like marks (numbers, slashes, or NA)
                            if next_line and (re.match(r'^\d+\s*/\s*\d+', next_line) or 
                                            re.match(r'^\d+$', next_line) or
                                            next_line.upper() == 'NA' or
                                            next_line == '0'):
                                assessments[line] = next_line
                                i += 2
                                continue
                        
                        i += 1
                    
                    # Create course entry
                    course_entry = {
                        "course_code": course_code,
                        "course_name": course_name,
                        "assessments": assessments,
                        "raw_content": course_content[:200]  # Store first 200 chars for debugging
                    }
                    
                    results_data.append(course_entry)
                    print(f"    ✓ Parsed: {course_code} - {course_name}")
                    if assessments:
                        for key, val in assessments.items():
                            print(f"      • {key}: {val}")
                    else:
                        print(f"      (No assessments yet)")
                    
                except Exception as e:
                    print(f"    ⚠️  Error parsing course {idx + 1}: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"Error parsing results text: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return results_data
    
    def parse_results_data(self, raw_results):
        """Parse raw results data into structured format
        Handles both complete semesters (with all assessments) and current semester (partial)"""
        structured_results = {}
        
        try:
            for semester, semester_data in raw_results.items():
                courses = []
                
                if not semester_data:
                    continue
                
                data = semester_data.get("data", [])
                
                print(f"\n  Processing {semester}: {len(data)} courses found")
                
                for course_idx, course in enumerate(data):
                    try:
                        # Handle both old format (list) and new format (dict)
                        if isinstance(course, dict):
                            # New format with assessments dictionary
                            course_info = {
                                "course_code": course.get("course_code", "N/A"),
                                "course_name": course.get("course_name", "N/A"),
                                "assessments": course.get("assessments", {}),
                                "marks": {}  # Extracted marks by assessment
                            }
                            
                            # Extract marks from assessment strings like "29 /40.0"
                            for assessment_name, assessment_value in course_info["assessments"].items():
                                # Try to parse marks from strings like "29 /40.0", "5 / 5", "A", "NA"
                                marks_str = assessment_value.strip()
                                
                                # Handle "XX /YY" format
                                if '/' in marks_str:
                                    try:
                                        parts = marks_str.split('/')
                                        obtained = parts[0].strip()
                                        total = parts[1].strip()
                                        course_info["marks"][assessment_name] = {
                                            "obtained": obtained,
                                            "total": total,
                                            "raw": marks_str
                                        }
                                    except:
                                        course_info["marks"][assessment_name] = {"raw": marks_str}
                                else:
                                    # Handle single values like grades (A, B, NA)
                                    course_info["marks"][assessment_name] = {"raw": marks_str}
                        else:
                            # Old format (list)
                            course_info = {
                                "course_code": course[0] if len(course) > 0 else "N/A",
                                "course_name": course[1] if len(course) > 1 else "N/A",
                                "assessments": {},
                                "marks": {}
                            }
                        
                        # Skip invalid entries
                        if course_info["course_code"] in ["N/A", "", None]:
                            continue
                        
                        # Skip summary rows
                        if "total" in course_info["course_name"].lower() or \
                           "gpa" in course_info["course_name"].lower():
                            continue
                        
                        courses.append(course_info)
                        print(f"    ✓ Course {course_idx + 1}: {course_info['course_code']} - {course_info['course_name']}")
                        if course_info["assessments"]:
                            for assessment_name, assessment_value in course_info["assessments"].items():
                                print(f"      • {assessment_name}: {assessment_value}")
                    
                    except Exception as e:
                        print(f"    ⚠️  Error parsing course {course_idx}: {str(e)}")
                        continue
                
                if courses:
                    structured_results[semester] = {
                        "course_count": len(courses),
                        "courses": courses,
                        "type": "complete" if len(courses) > 3 else "partial"
                    }
                    print(f"  ✓ Parsed {len(courses)} courses for {semester}")
                else:
                    print(f"  ⚠️  No valid courses found for {semester}")
        
        except Exception as e:
            print(f"Error parsing results: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return structured_results
    
    def fetch_calendar_data(self):
        """Scrape calendar/events data from the dashboard"""
        try:
            print("\n📆 Fetching calendar data...")
            
            # Click on "Calendar" menu item (note: PESU spells it "Calender")
            print("🔍 Looking for 'Calendar/Calender' menu...")
            try:
                calendar_link = None
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    link_text = link.text.lower()
                    # Check for both spellings and variations
                    if "calendar" in link_text or "calender" in link_text or "event" in link_text:
                        calendar_link = link
                        print(f"Found link: {link.text}")
                        break
                
                if calendar_link:
                    try:
                        calendar_link.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", calendar_link)
                    print("✓ Clicked 'Calendar'")
                    time.sleep(4)
                else:
                    print("⚠️  Could not find 'Calendar' link, trying to extract from announcements...")
                    # Try to extract announcements which may contain calendar events
                    return self._extract_announcements()
                    
            except Exception as e:
                print(f"Error clicking calendar link: {str(e)}")
                return {}
            
            # Extract calendar events and data
            calendar_events = self._extract_calendar_events()
            
            return calendar_events
            
        except Exception as e:
            print(f"❌ Error fetching calendar data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _extract_announcements(self):
        """Extract announcements as calendar events (fallback if calendar page not found)"""
        try:
            print("  📢 Extracting announcements...")
            
            announcements = []
            
            # Look for announcement elements
            announcement_selectors = [
                "div[class*='announce']",
                "div[class*='news']",
                "div[class*='event']",
                "div[class*='notification']",
                ".announcement",
                ".news",
                ".event"
            ]
            
            for selector in announcement_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements[:10]:
                        try:
                            text = elem.text.strip()
                            if text and len(text) > 5:
                                announcements.append({
                                    "type": "announcement",
                                    "content": text,
                                    "source": selector
                                })
                        except:
                            pass
                except:
                    continue
            
            # Look for any divs with "announcement" or "news" text
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                all_divs = body.find_elements(By.TAG_NAME, "div")
                
                for div in all_divs[:50]:
                    try:
                        div_text = div.text.strip()
                        if ("announcement" in div_text.lower() or "news" in div_text.lower() or 
                            "event" in div_text.lower()) and len(div_text) > 20:
                            announcements.append({
                                "type": "announcement",
                                "content": div_text[:200],
                                "source": "body_search"
                            })
                    except:
                        pass
            except:
                pass
            
            # Remove duplicates
            unique_announcements = []
            seen = set()
            for ann in announcements:
                content = ann.get('content', '')
                if content not in seen:
                    seen.add(content)
                    unique_announcements.append(ann)
            
            print(f"  Found {len(unique_announcements)} announcements")
            
            return {
                "events": unique_announcements,
                "event_count": len(unique_announcements),
                "source": "announcements",
                "extraction_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error extracting announcements: {str(e)}")
            return {"events": [], "event_count": 0}
    
    def _extract_calendar_events(self):
        """Extract all events from the calendar view"""
        try:
            print("  🔎 Searching for calendar events...")
            
            events = []
            
            # Strategy 1: Look for event elements with common calendar classes
            event_selectors = [
                "div.event",
                "div.calendar-event",
                "div[class*='event']",
                "li.event",
                "tr[class*='event']",
                ".calendar-cell",
                "[data-event]"
            ]
            
            event_elements = []
            for selector in event_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        event_elements.extend(elements)
                        print(f"  Found {len(elements)} events with selector: {selector}")
                except:
                    continue
            
            # Remove duplicates based on text content
            seen_texts = set()
            unique_events = []
            for elem in event_elements:
                try:
                    text = elem.text.strip()
                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        unique_events.append(elem)
                except:
                    continue
            
            # Extract event details
            for idx, elem in enumerate(unique_events):
                try:
                    event_text = elem.text.strip()
                    if not event_text or len(event_text) < 2:
                        continue
                    
                    # Try to extract date attributes
                    date_attr = elem.get_attribute("data-date") or elem.get_attribute("date")
                    
                    # Extract from text if no date attribute
                    event_date = None
                    event_desc = event_text
                    
                    # Try to parse date from various formats
                    date_patterns = [
                        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
                        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)',  # 15 Jan
                        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                    ]
                    
                    for pattern in date_patterns:
                        match = re.search(pattern, event_text, re.IGNORECASE)
                        if match:
                            event_date = match.group(1)
                            event_desc = event_text.replace(event_date, "").strip()
                            break
                    
                    event_data = {
                        "date": event_date or date_attr or "Unknown",
                        "description": event_desc,
                        "raw_text": event_text,
                        "element_class": elem.get_attribute("class") or ""
                    }
                    
                    events.append(event_data)
                    print(f"  Event {idx + 1}: {event_date or 'Unknown'} - {event_desc[:50]}")
                    
                except Exception as e:
                    print(f"  ⚠️  Error extracting event {idx}: {str(e)}")
                    continue
            
            # Strategy 2: Look for tables with event data (common in college portals)
            try:
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                for table_idx, table in enumerate(tables):
                    try:
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        headers = []
                        
                        # Try to identify header row
                        if rows:
                            header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                            if not header_cells:
                                header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                            headers = [cell.text.strip() for cell in header_cells]
                        
                        # Extract data rows
                        for row_idx in range(1 if headers else 0, len(rows)):
                            try:
                                row = rows[row_idx]
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if not cells:
                                    cells = row.find_elements(By.TAG_NAME, "th")
                                
                                if cells:
                                    row_data = [cell.text.strip() for cell in cells]
                                    
                                    # Try to identify date and event columns
                                    event_entry = {
                                        "source": "table",
                                        "table_index": table_idx,
                                        "row_index": row_idx,
                                        "data": row_data,
                                        "raw_text": " | ".join(row_data)
                                    }
                                    
                                    # Try to extract date from row
                                    for cell_text in row_data:
                                        if any(c.isdigit() for c in cell_text):
                                            date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', cell_text)
                                            if date_match:
                                                event_entry["date"] = date_match.group(0)
                                                break
                                    
                                    # Check if this event is not already in our list
                                    if not any(e.get("raw_text") == event_entry["raw_text"] for e in events):
                                        events.append(event_entry)
                                        print(f"  Table Event: {' | '.join(row_data[:2])}...")
                            except:
                                continue
                    except:
                        continue
            except:
                pass
            
            # Strategy 3: Look for announcements/events in divs or paragraphs
            try:
                # Look for common event/announcement containers
                announcement_divs = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'event') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'announce')]")
                
                for ann_div in announcement_divs[:20]:  # Limit to first 20
                    try:
                        ann_text = ann_div.text.strip()
                        if ann_text and len(ann_text) > 5 and not any(e.get("raw_text") == ann_text for e in events):
                            event_entry = {
                                "source": "announcement",
                                "description": ann_text[:100],
                                "raw_text": ann_text
                            }
                            events.append(event_entry)
                            print(f"  Announcement: {ann_text[:60]}...")
                    except:
                        continue
            except:
                pass
            
            # Get full page text as backup
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                all_text = body.text
                
                if all_text:
                    print(f"\n📝 Calendar page text preview (first 1000 chars):\n{all_text[:1000]}")
            except:
                pass
            
            if events:
                print(f"  ✅ Successfully extracted {len(events)} calendar events/items")
            else:
                print(f"  ⚠️  No calendar events found on the page")
            
            return {
                "events": events,
                "event_count": len(events),
                "extraction_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error extracting calendar events: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"events": [], "event_count": 0}
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("\n✓ Browser closed")


def main():
    # Credentials
    USERNAME = "pes1pg25ca005"
    PASSWORD = "Mymosi@132513"
    
    scraper = PESUScraper(USERNAME, PASSWORD)
    
    try:
        scraper.setup_driver()
        if scraper.login():
            # Fetch attendance data
            scraper.fetch_attendance_data()
            
            # Fetch timetable data
            timetable = scraper.fetch_timetable_data()
            scraper.timetable_data = timetable
            
            # Fetch results data
            raw_results = scraper.fetch_results_data()
            if raw_results:
                parsed_results = scraper.parse_results_data(raw_results)
                scraper.results_data = parsed_results
            else:
                scraper.results_data = {}
            
            # Fetch calendar data
            calendar = scraper.fetch_calendar_data()
            scraper.calendar_data = calendar
            
            # Save all data to JSON
            if scraper.attendance_structured:
                scraper.save_full_data_to_json(
                    scraper.attendance_structured,
                    scraper.credentials_data,
                    scraper.timetable_data,
                    scraper.results_data,
                    scraper.calendar_data
                )
            
            print("\n✅ All data fetched and saved successfully!")
        else:
            print("❌ Failed to login")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
