# PESU Academy Dashboard - Full Stack Architecture

## Project Overview
- **Backend**: Python (FastAPI) with async support
- **Frontend**: React with dynamic loading
- **Deployment**: Vercel (Python backend via serverless functions + React frontend)
- **Data**: PESU scraper + Async data fetching

---

## Backend Architecture (Python)

### Tech Stack
- **Framework**: FastAPI (async-native)
- **Authentication**: JWT tokens
- **Database**: SQLite (for local) or PostgreSQL (production)
- **Scraper**: Selenium (async wrapper) or headless browser
- **Async Tasks**: Celery + Redis OR APScheduler
- **Deployment**: Vercel Functions (serverless) + Vercel Database

### Project Structure
```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py (FastAPI app + Vercel function handler)
│   ├── routes/
│   │   ├── auth.py (login, register, jwt)
│   │   ├── attendance.py (attendance endpoints)
│   │   ├── courses.py (course details)
│   │   ├── timetable.py (timetable/schedule)
│   │   ├── results.py (exam results)
│   │   └── user.py (profile, settings)
│   ├── models/
│   │   ├── user.py
│   │   ├── attendance.py
│   │   ├── course.py
│   │   └── session.py
│   ├── services/
│   │   ├── scraper_service.py (async PESU scraper)
│   │   ├── auth_service.py (JWT handling)
│   │   ├── cache_service.py (Redis/in-memory caching)
│   │   └── scheduler_service.py (background jobs)
│   ├── middleware/
│   │   ├── auth_middleware.py (JWT verification)
│   │   └── cors_middleware.py
│   ├── utils/
│   │   ├── logger.py
│   │   └── decorators.py
│   └── vercel.json (Vercel configuration)
├── requirements.txt
└── .env.example
```

### Key API Endpoints (Async)

```
POST   /api/auth/login              → Authenticate user
POST   /api/auth/register           → Create new user
GET    /api/auth/me                 → Get current user (protected)
POST   /api/auth/logout             → Logout

GET    /api/attendance/summary      → Overall summary (cached, 5min)
GET    /api/attendance/courses      → Course-wise attendance (cached)
GET    /api/attendance/course/:id   → Single course details (lazy load)
POST   /api/attendance/sync         → Manual sync with PESU (background job)

GET    /api/timetable               → Today's schedule (lazy load)
GET    /api/timetable/week          → Weekly schedule
GET    /api/timetable/semester      → Full semester

GET    /api/results                 → Exam results (lazy load)
GET    /api/results/course/:id      → Single course results

GET    /api/user/profile            → User profile
PUT    /api/user/settings           → Update settings
GET    /api/user/preferences        → User preferences

GET    /api/health                  → Health check
```

### Async Data Fetching Strategy

```python
# Background sync service
- Scrape PESU every 30 minutes (configurable)
- Cache results in database
- Real-time updates via WebSocket (optional)
- User can manually trigger sync

# On-demand fetching
- First visit: Return cached data immediately
- Background: Update cache asynchronously
- Stale-while-revalidate pattern

# Lazy loading
- Only fetch when section is viewed
- Cache results with TTL
- Return minimal data for list views, full data on detail views
```

---

## Frontend Architecture (React)

### Tech Stack
- **Framework**: React 18+ (Vite for fast builds)
- **State Management**: Zustand or TanStack Query (React Query)
- **UI Library**: Tailwind CSS + Shadcn/ui
- **Code Splitting**: React.lazy() + Suspense
- **HTTP Client**: Axios + interceptors for JWT

### Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── AuthProvider.jsx
│   │   ├── layout/
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Navigation.jsx
│   │   │   └── Layout.jsx
│   │   ├── dashboard/
│   │   │   └── AttendanceSummary.jsx (LAZY LOAD)
│   │   ├── attendance/
│   │   │   ├── AttendanceView.jsx (LAZY LOAD)
│   │   │   ├── CourseCard.jsx
│   │   │   ├── CourseDetail.jsx (LAZY LOAD on click)
│   │   │   └── AttendanceChart.jsx
│   │   ├── timetable/
│   │   │   ├── TimetableView.jsx (LAZY LOAD)
│   │   │   ├── DaySchedule.jsx
│   │   │   └── WeekView.jsx
│   │   ├── results/
│   │   │   ├── ResultsView.jsx (LAZY LOAD)
│   │   │   └── ResultCard.jsx
│   │   ├── user/
│   │   │   ├── ProfileView.jsx (LAZY LOAD)
│   │   │   └── SettingsView.jsx (LAZY LOAD)
│   │   └── common/
│   │       ├── Loading.jsx
│   │       ├── Error.jsx
│   │       └── EmptyState.jsx
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx (Home - main hub)
│   │   ├── NotFound.jsx
│   │   └── Error.jsx
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useAttendance.js
│   │   ├── useTimetable.js
│   │   ├── useResults.js
│   │   └── useAsync.js (custom hook for async data)
│   ├── services/
│   │   ├── api.js (axios instance + interceptors)
│   │   ├── authService.js
│   │   ├── attendanceService.js
│   │   ├── timetableService.js
│   │   └── resultsService.js
│   ├── store/
│   │   ├── authStore.js (Zustand)
│   │   ├── attendanceStore.js
│   │   └── uiStore.js
│   ├── App.jsx
│   └── index.jsx
├── vercel.json
├── vite.config.js
└── package.json
```

### Frontend Flow

```
1. USER VISITS APP
   ↓
2. [LOGIN PAGE]
   - Email + Password
   - JWT token stored (localStorage/httpOnly cookie)
   ↓
3. [DASHBOARD HOME]
   - Show: Attendance Summary Card (PRELOADED - critical)
   - Show: Navigation Menu (Attendance, Timetable, Results, Profile)
   - DON'T LOAD: Other sections yet
   ↓
4. USER CLICKS "ATTENDANCE"
   - Lazy load AttendanceView component
   - Show loading spinner
   - Fetch course list from /api/attendance/courses
   - Display courses list
   ↓
5. USER CLICKS COURSE DETAIL
   - Lazy load CourseDetail component
   - Fetch /api/attendance/course/:id
   - Show detailed view with class-by-class breakdown
   ↓
6. USER CLICKS "TIMETABLE"
   - Lazy load TimetableView component
   - Fetch /api/timetable
   - Display schedule
   ↓
7. SIMILAR FOR OTHER SECTIONS
```

### Lazy Loading Implementation

```jsx
// Dashboard.jsx
import { Suspense, lazy } from 'react';

const AttendanceView = lazy(() => import('./components/attendance/AttendanceView'));
const TimetableView = lazy(() => import('./components/timetable/TimetableView'));
const ResultsView = lazy(() => import('./components/results/ResultsView'));
const ProfileView = lazy(() => import('./components/user/ProfileView'));

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState('home');

  return (
    <Layout>
      <Navigation onNavigate={setActiveSection} />
      
      {activeSection === 'home' && <AttendanceSummary />}
      
      {activeSection === 'attendance' && (
        <Suspense fallback={<Loading />}>
          <AttendanceView />
        </Suspense>
      )}
      
      {activeSection === 'timetable' && (
        <Suspense fallback={<Loading />}>
          <TimetableView />
        </Suspense>
      )}
      
      {/* ... similar for other sections */}
    </Layout>
  );
}
```

### Data Fetching Hook

```javascript
// hooks/useAsync.js - Reusable async hook
export function useAsync(asyncFunction, immediate = true) {
  const [status, setStatus] = useState('idle');
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const execute = useCallback(async () => {
    setStatus('pending');
    try {
      const response = await asyncFunction();
      setData(response);
      setStatus('success');
    } catch (err) {
      setError(err);
      setStatus('error');
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) execute();
  }, [execute, immediate]);

  return { status, data, error, execute };
}

// Usage in component
const { status, data: courses, error } = useAsync(
  () => attendanceService.getCourses(),
  true // Load immediately
);
```

---

## Deployment: Vercel Full-Stack

### Both Backend + Frontend on Vercel

#### Backend (Vercel Functions)
```
vercel.json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python@3.11"
    }
  }
}
```

File structure:
```
api/
├── attendance.py (becomes /api/attendance)
├── auth.py (becomes /api/auth)
├── courses.py (becomes /api/courses)
└── ...
```

Each Python file becomes a serverless function automatically.

#### Frontend (Vercel Static + Edge)
- Automatic deployment on push to `main`
- All React components served statically
- Environment variables: `VITE_API_URL=https://your-domain/api`

#### Environment Variables
```
PESU_USERNAME=pes1pg25ca005
PESU_PASSWORD=your_password
JWT_SECRET=your_jwt_secret
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PESU Academy Website                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Backend (Vercel Functions/FastAPI)                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Scraper Service (Async)                             │   │
│  │  - Scheduled: Every 30 min                           │   │
│  │  - Manual: User triggered                            │   │
│  │  - Results: Stored in DB + Redis cache              │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Database (Vercel Postgres)                          │   │
│  │  - Users, attendance, courses, timetable, results    │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cache Layer (Redis/in-memory)                       │   │
│  │  - Attendance summary: 5 min TTL                     │   │
│  │  - Course data: 30 min TTL                           │   │
│  │  - Timetable: 1 hour TTL                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  REST API Endpoints (Async)                          │   │
│  │  - /api/auth/*                                       │   │
│  │  - /api/attendance/*                                 │   │
│  │  - /api/timetable/*                                  │   │
│  │  - /api/results/*                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Frontend (React on Vercel)                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Login Page                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Dashboard (Home)                                    │   │
│  │  ├─ Attendance Summary (Preloaded)                   │   │
│  │  ├─ Navigation Menu                                  │   │
│  │  └─ User Settings Button                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│         ┌───────────────┼───────────────┬──────────────┐    │
│         │               │               │              │    │
│         ▼               ▼               ▼              ▼    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────┐ │
│  │Attendance  │  │Timetable   │  │Results     │  │Profile │ │
│  │(Lazy Load) │  │(Lazy Load) │  │(Lazy Load) │  │(Lazy)  │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Development Setup

### Backend
```bash
# Create virtual env
python -m venv venv
source venv/Scripts/activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn api.main:app --reload --port 8000

# Environment
cp .env.example .env
# Edit .env with PESU credentials
```

### Frontend
```bash
# Install dependencies
npm install

# Development
npm run dev

# Build
npm run build

# Vercel deployment
vercel deploy
```

---

## Key Features Summary

✅ **Async Operations**: All data fetching is non-blocking
✅ **Lazy Loading**: Sections load on-demand, not on app start
✅ **Smart Caching**: Reduce API calls with intelligent TTL
✅ **Real-time Sync**: Background jobs update data periodically
✅ **Security**: JWT auth, password hashing, CORS
✅ **Scalable**: Vercel serverless functions + Postgres
✅ **Mobile-friendly**: Responsive React UI
✅ **Error Handling**: Graceful degradation, user feedback
✅ **Logging**: Full debug info for troubleshooting

---

## Migration Checklist

- [ ] Convert Flask to FastAPI with async routes
- [ ] Implement JWT authentication
- [ ] Create database schema (users, sessions, etc.)
- [ ] Wrap scraper in async task service
- [ ] Implement caching layer
- [ ] Create React frontend from scratch
- [ ] Implement lazy loading components
- [ ] Set up Vercel configuration
- [ ] Configure environment variables
- [ ] Set up CI/CD pipeline
- [ ] Test all endpoints
- [ ] Deploy to Vercel
