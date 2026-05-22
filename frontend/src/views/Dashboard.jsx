import { useState, Suspense, lazy } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  BarChart3,
  Calendar,
  FileText,
  User,
  LogOut,
  Home,
  Menu,
  X,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBoundary from '../components/ErrorBoundary';
import HomePage from './HomePage';

// Lazy-loaded views
const AttendanceView = lazy(() => import('./AttendanceView'));
const CourseDetailView = lazy(() => import('./CourseDetailView'));
const TimetableView = lazy(() => import('./TimetableView'));
const ResultsView = lazy(() => import('./ResultsView'));
const ProfileView = lazy(() => import('./ProfileView'));

const NAV_ITEMS = [
  { id: 'home', label: 'Overview', icon: Home },
  { id: 'attendance', label: 'Attendance', icon: BarChart3 },
  { id: 'timetable', label: 'Timetable', icon: Calendar },
  { id: 'results', label: 'Results', icon: FileText },
  { id: 'profile', label: 'Profile', icon: User },
];

export default function Dashboard() {
  const [active, setActive] = useState('home');
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [mobileNav, setMobileNav] = useState(false);

  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const handleNav = (id) => {
    setActive(id);
    setSelectedCourse(null);
    setMobileNav(false);
  };

  const handleCourseSelect = (course) => {
    setSelectedCourse(course);
    setActive('course-detail');
  };

  const handleBackFromCourse = () => {
    setActive('attendance');
    setSelectedCourse(null);
  };

  return (
    <div className="min-h-screen bg-surface-0 flex">
      {/* —— Sidebar (desktop) —— */}
      <aside className="hidden lg:flex flex-col w-56 border-r border-line bg-white fixed h-screen">
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-5 h-14 border-b border-line">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
            <GraduationCap className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-sm text-ink tracking-tight">PESU Academy</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => handleNav(id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150 ${
                active === id || (id === 'attendance' && active === 'course-detail')
                  ? 'bg-accent-light text-accent-text'
                  : 'text-ink-muted hover:text-ink hover:bg-surface-1'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>

        {/* Bottom */}
        <div className="px-3 pb-4 border-t border-line pt-3">
          <div className="text-xs text-ink-faint px-3 mb-2 truncate">
            {user?.username || 'Student'}
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-ink-muted hover:text-bad hover:bg-bad-light transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* —— Mobile header —— */}
      <header className="lg:hidden fixed top-0 inset-x-0 z-40 h-14 bg-white/80 backdrop-blur-md border-b border-line flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
            <GraduationCap className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-sm text-ink">PESU Academy</span>
        </div>
        <button
          onClick={() => setMobileNav(!mobileNav)}
          className="btn-ghost p-2"
        >
          {mobileNav ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </header>

      {/* —— Mobile nav overlay —— */}
      {mobileNav && (
        <div className="lg:hidden fixed inset-0 z-30">
          <div className="absolute inset-0 bg-black/20" onClick={() => setMobileNav(false)} />
          <div className="absolute top-14 left-0 right-0 bg-white border-b border-line p-3 animate-slide-up shadow-modal">
            {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => handleNav(id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  active === id
                    ? 'bg-accent-light text-accent-text'
                    : 'text-ink-muted hover:bg-surface-1'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
            <div className="border-t border-line mt-2 pt-2">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm text-ink-muted hover:text-bad"
              >
                <LogOut className="w-4 h-4" />
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* —— Main content —— */}
      <main className="flex-1 lg:ml-56 pt-14 lg:pt-0 min-h-screen">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
          <ErrorBoundary>
            {active === 'home' && <HomePage onNavigate={handleNav} />}

            {active === 'attendance' && (
              <Suspense fallback={<LoadingSpinner text="Loading attendance…" />}>
                <AttendanceView onCourseSelect={handleCourseSelect} />
              </Suspense>
            )}

            {active === 'course-detail' && selectedCourse && (
              <Suspense fallback={<LoadingSpinner text="Loading course details…" />}>
                <CourseDetailView course={selectedCourse} onBack={handleBackFromCourse} />
              </Suspense>
            )}

            {active === 'timetable' && (
              <Suspense fallback={<LoadingSpinner text="Loading timetable…" />}>
                <TimetableView />
              </Suspense>
            )}

            {active === 'results' && (
              <Suspense fallback={<LoadingSpinner text="Loading results…" />}>
                <ResultsView />
              </Suspense>
            )}

            {active === 'profile' && (
              <Suspense fallback={<LoadingSpinner text="Loading profile…" />}>
                <ProfileView />
              </Suspense>
            )}
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
