import React, { useState, useEffect, Suspense, lazy } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useAttendanceStore } from '../store/attendanceStore'
import api from '../services/api'
import { 
  Home, 
  Calendar, 
  Award, 
  User, 
  LogOut, 
  Menu, 
  X, 
  CheckSquare, 
  ChevronRight,
  TrendingUp,
  Settings
} from 'lucide-react'

// Lazy loaded views
import HomeView from './HomeView'
const AttendanceView = lazy(() => import('./AttendanceView'))
const CourseDetailView = lazy(() => import('./CourseDetailView'))
const TimetableView = lazy(() => import('./TimetableView'))
const ResultsView = lazy(() => import('./ResultsView'))
const ProfileView = lazy(() => import('./ProfileView'))

// Loading Spinner Component
function ViewLoader() {
  return (
    <div className="w-full min-h-[400px] flex flex-col items-center justify-center space-y-4">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 border-4 border-slate-800 rounded-full" />
        <div className="absolute inset-0 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
      <p className="text-slate-400 text-sm animate-pulse">Loading section data...</p>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { user, logout, isAuthenticated } = useAuthStore()
  const { setSummary, clearCache } = useAttendanceStore()
  
  const [activeSection, setActiveSection] = useState('home') // home, attendance, timetable, results, profile
  const [selectedCourse, setSelectedCourse] = useState(null) // course code
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [profileData, setProfileData] = useState(null)
  const [loadingSummary, setLoadingSummary] = useState(false)

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  // Fetch initial profile & prefetch summary
  useEffect(() => {
    if (!isAuthenticated) return

    const fetchSummary = async () => {
      setLoadingSummary(true)
      try {
        const sumRes = await api.get('/api/attendance/summary')
        if (sumRes.data.success) {
          setSummary(sumRes.data.data)
        }
        
        const profRes = await api.get('/api/user/profile')
        if (profRes.data.success) {
          setProfileData(profRes.data.data)
        }
      } catch (err) {
        console.error('Error loading initial data:', err)
      } finally {
        setLoadingSummary(false)
      }
    }

    fetchSummary()
  }, [isAuthenticated, setSummary])

  if (!isAuthenticated) return null

  const handleLogout = () => {
    clearCache()
    logout()
    navigate('/login')
  }

  const navigateToSection = (section, courseCode = null) => {
    setActiveSection(section)
    setSelectedCourse(courseCode)
    setMobileMenuOpen(false)
  }

  const menuItems = [
    { id: 'home', label: 'Dashboard Home', icon: Home },
    { id: 'attendance', label: 'Attendance', icon: CheckSquare },
    { id: 'timetable', label: 'Timetable', icon: Calendar },
    { id: 'results', label: 'Results & Marks', icon: Award },
    { id: 'profile', label: 'Student Profile', icon: User }
  ]

  // Dynamic component resolver
  const renderContent = () => {
    if (selectedCourse && activeSection === 'attendance') {
      return (
        <Suspense fallback={<ViewLoader />}>
          <CourseDetailView 
            courseCode={selectedCourse} 
            onBack={() => setSelectedCourse(null)} 
          />
        </Suspense>
      )
    }

    switch (activeSection) {
      case 'attendance':
        return (
          <Suspense fallback={<ViewLoader />}>
            <AttendanceView onSelectCourse={(code) => setSelectedCourse(code)} />
          </Suspense>
        )
      case 'timetable':
        return (
          <Suspense fallback={<ViewLoader />}>
            <TimetableView />
          </Suspense>
        )
      case 'results':
        return (
          <Suspense fallback={<ViewLoader />}>
            <ResultsView onSelectCourse={(code) => navigateToSection('attendance', code)} />
          </Suspense>
        )
      case 'profile':
        return (
          <Suspense fallback={<ViewLoader />}>
            <ProfileView />
          </Suspense>
        )
      default:
        // Default Home preloaded view
        return <HomeView navigateToSection={navigateToSection} loadingSummary={loadingSummary} />
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Background glowing circles */}
      <div className="bg-mesh-circle w-[400px] h-[400px] bg-brand-900/20 top-[10%] left-[5%]" />
      <div className="bg-mesh-circle w-[500px] h-[500px] bg-violet-950/20 bottom-[10%] right-[5%] animation-delay-2000" />

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 glass-panel border-r border-slate-900 shrink-0 sticky top-0 h-screen p-6">
        <div className="flex items-center space-x-3 mb-8 px-2">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold font-sans">P</div>
          <span className="text-xl font-bold tracking-tight text-white">PESU <span className="gradient-text">Academy</span></span>
        </div>

        {/* Sidebar Nav */}
        <nav className="flex-1 space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = activeSection === item.id
            return (
              <button
                key={item.id}
                onClick={() => navigateToSection(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive 
                    ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/20 border border-brand-500/20' 
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/50'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Profile Card & Logout */}
        <div className="pt-6 border-t border-slate-900 space-y-4">
          {profileData && (
            <div className="flex items-center space-x-3 px-2">
              <img 
                src={profileData.avatar_url} 
                alt="Avatar" 
                className="w-10 h-10 rounded-full border border-slate-800"
              />
              <div className="min-w-0">
                <p className="text-sm font-bold text-white truncate">{profileData.name}</p>
                <p className="text-xs text-slate-500 truncate">{profileData.srn}</p>
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all border border-transparent hover:border-rose-500/10"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Layout Area */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Header */}
        <header className="h-16 glass-panel border-b border-slate-900 px-6 flex items-center justify-between sticky top-0 z-20 backdrop-blur-md">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-900/60 transition"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h2 className="text-lg font-bold text-white capitalize md:block hidden">
              {activeSection === 'home' ? 'Welcome Back' : activeSection}
            </h2>
          </div>
          
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => navigateToSection('profile')}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-900/60 transition"
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
            
            {profileData && (
              <div className="flex items-center space-x-2 md:bg-slate-900/40 py-1.5 px-3 rounded-full border border-slate-900/80">
                <span className="text-xs font-semibold text-brand-400 md:inline hidden">{profileData.section}</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse md:inline hidden" />
                <img 
                  src={profileData.avatar_url} 
                  alt="Student Avatar" 
                  className="w-7 h-7 rounded-full border border-brand-500/20"
                />
              </div>
            )}
          </div>
        </header>

        {/* Content Wrapper */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
          {renderContent()}
        </main>
      </div>

      {/* Mobile Drawer Navigation Menu */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          {/* Drawer Panel */}
          <div className="relative flex flex-col w-4/5 max-w-xs bg-slate-950 border-r border-slate-900 p-6 z-10 animate-fade-in">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold">P</div>
                <span className="text-lg font-bold text-white">PESU Dashboard</span>
              </div>
              <button 
                onClick={() => setMobileMenuOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <nav className="flex-1 space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon
                const isActive = activeSection === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => navigateToSection(item.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      isActive 
                        ? 'bg-brand-600 text-white shadow-lg border border-brand-500/20' 
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </button>
                )
              })}
            </nav>

            <div className="pt-6 border-t border-slate-900 space-y-4">
              {profileData && (
                <div className="flex items-center space-x-3">
                  <img 
                    src={profileData.avatar_url} 
                    alt="Avatar" 
                    className="w-10 h-10 rounded-full"
                  />
                  <div>
                    <p className="text-sm font-bold text-white">{profileData.name}</p>
                    <p className="text-xs text-slate-500">{profileData.srn}</p>
                  </div>
                </div>
              )}
              <button
                onClick={handleLogout}
                className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
              >
                <LogOut className="w-5 h-5" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
