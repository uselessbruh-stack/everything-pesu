import React, { useEffect, useState } from 'react'
import { useAttendanceStore } from '../store/attendanceStore'
import api from '../services/api'
import { 
  CheckSquare, 
  AlertTriangle, 
  Clock, 
  Calendar, 
  TrendingUp, 
  ArrowRight,
  BookOpen,
  Award
} from 'lucide-react'

export default function HomeView({ navigateToSection, loadingSummary }) {
  const { summary, targetPercentage } = useAttendanceStore()
  const [todayClasses, setTodayClasses] = useState([])
  const [loadingSchedule, setLoadingSchedule] = useState(false)

  // Fetch today's schedule for preview on dashboard
  useEffect(() => {
    const fetchTodayClasses = async () => {
      setLoadingSchedule(true)
      try {
        const res = await api.get('/api/timetable')
        if (res.data.success) {
          setTodayClasses(res.data.classes || [])
        }
      } catch (err) {
        console.error('Failed to load today schedule:', err)
      } finally {
        setLoadingSchedule(false)
      }
    }

    fetchTodayClasses()
  }, [])

  // Calculate overall shortage relative to the target percentage
  const overallPercentage = summary?.overall_percentage || 0
  const isBelowTarget = overallPercentage < targetPercentage
  
  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6 md:p-8 rounded-2xl bg-gradient-to-r from-brand-900/40 via-indigo-950/20 to-slate-900/20 border border-brand-500/10">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Welcome back, <span className="gradient-text">Alex Mercer</span> 👋
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Here is your academic overview for today.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-slate-900/60 py-2 px-4 rounded-xl border border-slate-800 self-start md:self-auto">
          <TrendingUp className="w-4 h-4 text-brand-400" />
          <span className="text-xs font-semibold text-slate-300">
            Attendance Target: <span className="text-brand-400 font-bold">{targetPercentage}%</span>
          </span>
        </div>
      </div>

      {/* Main Attendance Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        
        {/* Overall Percentage */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-900 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/10 rounded-full blur-2xl group-hover:bg-brand-500/20 transition-all duration-500" />
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall Attendance</p>
          <div className="flex items-baseline space-x-2 mt-4">
            <span className={`text-4xl font-extrabold tracking-tight ${isBelowTarget ? 'text-rose-400' : 'text-emerald-400'}`}>
              {overallPercentage.toFixed(1)}%
            </span>
          </div>
          <div className="mt-3 flex items-center space-x-1.5 text-xs">
            <span className={`px-2 py-0.5 rounded-full font-semibold ${isBelowTarget ? 'bg-rose-500/10 text-rose-300' : 'bg-emerald-500/10 text-emerald-300'}`}>
              {isBelowTarget ? 'Below Target' : 'On Track'}
            </span>
            <span className="text-slate-500">vs {targetPercentage}% goal</span>
          </div>
        </div>

        {/* Classes Attended */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-900 relative overflow-hidden">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Classes Attended</p>
          <div className="flex items-baseline space-x-1 mt-4">
            <span className="text-3xl font-extrabold text-white">
              {summary?.total_attended || 0}
            </span>
            <span className="text-slate-500 text-lg font-medium">
              /{summary?.total_classes || 0}
            </span>
          </div>
          <div className="mt-4 w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
            <div 
              className={`h-full rounded-full ${isBelowTarget ? 'bg-rose-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, overallPercentage)}%` }}
            />
          </div>
        </div>

        {/* Courses Below Goal */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-900 relative overflow-hidden">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Below Threshold</p>
          <div className="flex items-baseline space-x-2 mt-4">
            <span className={`text-3xl font-extrabold ${(summary?.courses_below_requirement || 0) > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
              {summary?.courses_below_requirement || 0}
            </span>
            <span className="text-slate-500 text-sm font-medium">courses</span>
          </div>
          <p className="text-slate-500 text-xs mt-3 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            Needs attendance attention
          </p>
        </div>

        {/* Total Class Shortage */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-900 relative overflow-hidden">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Class Shortage</p>
          <div className="flex items-baseline space-x-2 mt-4">
            <span className={`text-3xl font-extrabold ${(summary?.total_shortage || 0) > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {summary?.total_shortage || 0}
            </span>
            <span className="text-slate-500 text-sm font-medium">lectures</span>
          </div>
          <p className="text-slate-500 text-xs mt-3">
            {(summary?.total_shortage || 0) > 0 
              ? 'Required to attend to meet minimums' 
              : '✓ Shortage free overall!'}
          </p>
        </div>
      </div>

      {/* Main Sections Grid: Timetable Preview + Shortcuts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Today's Schedule Panel */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-900 flex flex-col min-h-[300px]">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-brand-400" />
              <span>Today's Classes</span>
            </h3>
            <button 
              onClick={() => navigateToSection('timetable')}
              className="text-xs font-semibold text-brand-400 hover:text-brand-300 flex items-center space-x-1"
            >
              <span>Full Schedule</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {loadingSchedule ? (
            <div className="flex-1 flex items-center justify-center">
              <Clock className="w-6 h-6 text-slate-600 animate-spin" />
            </div>
          ) : todayClasses.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-slate-900/20 rounded-xl border border-dashed border-slate-900">
              <Calendar className="w-8 h-8 text-slate-700 mb-2" />
              <p className="text-slate-500 text-sm">No classes scheduled for today.</p>
              <p className="text-xs text-slate-600 mt-1">Enjoy your day off!</p>
            </div>
          ) : (
            <div className="space-y-3.5 flex-1">
              {todayClasses.map((cls, idx) => (
                <div 
                  key={idx}
                  className="p-4 rounded-xl bg-slate-900/40 border border-slate-900 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 hover:border-slate-800 transition"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold font-mono text-brand-400">{cls.course_code}</span>
                      <span className="w-1 h-1 rounded-full bg-slate-800" />
                      <span className="text-xs text-slate-500">{cls.room}</span>
                    </div>
                    <p className="text-sm font-bold text-white line-clamp-1">{cls.subject}</p>
                    <p className="text-xs text-slate-400">{cls.instructor}</p>
                  </div>
                  
                  <div className="flex items-center space-x-2 bg-slate-950 py-1.5 px-3 rounded-lg border border-slate-900 self-start sm:self-auto">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-xs font-semibold text-slate-300 font-mono whitespace-nowrap">{cls.time_slot}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Navigation Panels */}
        <div className="space-y-5">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider px-1">Navigation Shortcuts</h3>
          
          <div className="grid grid-cols-1 gap-4">
            
            {/* Attendance View */}
            <button
              onClick={() => navigateToSection('attendance')}
              className="glass-panel p-5 rounded-2xl border border-slate-900 text-left flex items-start space-x-4 glass-panel-hover"
            >
              <div className="p-3 bg-brand-500/10 rounded-xl text-brand-400 border border-brand-500/10">
                <CheckSquare className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-white text-sm">Attendance List</h4>
                <p className="text-xs text-slate-400 mt-1">Check individual course ratios & bunk limits.</p>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-600 shrink-0 self-center" />
            </button>

            {/* Results View */}
            <button
              onClick={() => navigateToSection('results')}
              className="glass-panel p-5 rounded-2xl border border-slate-900 text-left flex items-start space-x-4 glass-panel-hover"
            >
              <div className="p-3 bg-amber-500/10 rounded-xl text-amber-400 border border-amber-500/10">
                <Award className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-white text-sm">Exam Results</h4>
                <p className="text-xs text-slate-400 mt-1">Review marks, assignments, and grades.</p>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-600 shrink-0 self-center" />
            </button>

            {/* Profile Settings */}
            <button
              onClick={() => navigateToSection('profile')}
              className="glass-panel p-5 rounded-2xl border border-slate-900 text-left flex items-start space-x-4 glass-panel-hover"
            >
              <div className="p-3 bg-violet-500/10 rounded-xl text-violet-400 border border-violet-500/10">
                <BookOpen className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-white text-sm">Settings & Profile</h4>
                <p className="text-xs text-slate-400 mt-1">Customize global targets & review profile details.</p>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-600 shrink-0 self-center" />
            </button>
            
          </div>
        </div>

      </div>
    </div>
  )
}
