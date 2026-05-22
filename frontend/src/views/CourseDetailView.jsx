import React, { useEffect, useState } from 'react'
import { useAttendanceStore } from '../store/attendanceStore'
import { useAttendanceCalculator } from '../hooks/useAttendanceCalculator'
import api from '../services/api'
import { 
  ArrowLeft, 
  Search, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  BarChart4,
  PlusCircle,
  MinusCircle,
  HelpCircle
} from 'lucide-react'

export default function CourseDetailView({ courseCode, onBack }) {
  const { targetPercentage } = useAttendanceStore()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  // Table filters
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('All') // All, Present, Absent

  // Interactive inputs for calculator
  const [classesToAttend, setClassesToAttend] = useState(0)
  const [classesToBunk, setClassesToBunk] = useState(0)

  useEffect(() => {
    const fetchCourseDetail = async () => {
      setLoading(true)
      setError('')
      try {
        const res = await api.get(`/api/attendance/course/${courseCode}`)
        if (res.data.success) {
          setCourse(res.data.data)
        }
      } catch (err) {
        console.error(err)
        setError('Failed to fetch course details.')
      } finally {
        setLoading(false)
      }
    }

    fetchCourseDetail()
  }, [courseCode])

  if (loading) {
    return (
      <div className="w-full py-20 flex justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
      </div>
    )
  }

  if (error || !course) {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-rose-500/20 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-400 mx-auto" />
        <p className="text-slate-300 font-bold">{error || 'Course not found'}</p>
        <button 
          onClick={onBack}
          className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-200 hover:text-white"
        >
          Back to Attendance
        </button>
      </div>
    )
  }

  const { attended, total } = course.attendance
  const currentPct = total > 0 ? (attended / total) * 100 : 0

  // Bind the attendance calculator hook
  const calc = useAttendanceCalculator(attended, total, targetPercentage)
  const attendResult = calc.calculateAttendMore(classesToAttend)
  const bunkResult = calc.calculateBunkClasses(classesToBunk)
  const requiredStats = calc.calculateRequired

  // Filter classes history
  const filteredClasses = (course.classes || []).filter(item => {
    const matchesSearch = item.topic.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          item.date.includes(searchQuery)
    const matchesStatus = statusFilter === 'All' || item.status === statusFilter
    return matchesSearch && matchesStatus
  })

  // SVG Circular progress computations
  const radius = 50
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (Math.min(100, currentPct) / 100) * circumference

  // SVG Trendline computation (last 10 classes)
  const renderTrendLine = () => {
    const lastClasses = [...(course.classes || [])].reverse().slice(-10) // chronological
    if (lastClasses.length < 2) return null

    let accumulatedAttended = 0
    let accumulatedTotal = 0
    const points = lastClasses.map((item, idx) => {
      accumulatedTotal += 1
      if (item.status === 'Present') accumulatedAttended += 1
      const pct = (accumulatedAttended / accumulatedTotal) * 100
      
      // X maps to index, Y maps to percentage (bottom is 0%, top is 100%)
      const x = (idx / (lastClasses.length - 1)) * 100 // percent spacing
      const y = 80 - (pct / 100) * 60 // scale to fit 80px height SVG with padding
      return { x, y }
    })

    const pathData = points.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
    
    return (
      <svg className="w-full h-24 mt-2 overflow-visible" viewBox="0 0 100 80" preserveAspectRatio="none">
        {/* Horizontal gridlines */}
        <line x1="0" y1="20" x2="100" y2="20" stroke="#1e293b" strokeWidth="0.5" strokeDasharray="2,2" />
        <line x1="0" y1="50" x2="100" y2="50" stroke="#1e293b" strokeWidth="0.5" strokeDasharray="2,2" />
        <line x1="0" y1="80" x2="100" y2="80" stroke="#1e293b" strokeWidth="0.5" strokeDasharray="2,2" />
        
        {/* Glow path */}
        <path d={pathData} fill="none" stroke="rgba(99, 102, 241, 0.25)" strokeWidth="4" />
        {/* Main path */}
        <path d={pathData} fill="none" stroke="#6366f1" strokeWidth="1.5" />
        
        {/* Points */}
        {points.map((p, idx) => (
          <circle 
            key={idx} 
            cx={p.x} 
            cy={p.y} 
            r="1.5" 
            fill="#818cf8" 
            stroke="#020617" 
            strokeWidth="0.5" 
          />
        ))}
      </svg>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      
      {/* Header and Go Back */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 text-slate-400 hover:text-slate-100 transition self-start"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Courses</span>
        </button>
        <span className="text-xs text-slate-500">
          Viewing course details & interactive dashboard
        </span>
      </div>

      {/* Main Course Info card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Overview Stats (left card) */}
        <div className="lg:col-span-2 glass-panel p-6 md:p-8 rounded-2xl border border-slate-900 flex flex-col sm:flex-row items-center gap-8">
          {/* Radial progress ring */}
          <div className="relative w-36 h-36 shrink-0 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90">
              <circle
                cx="72"
                cy="72"
                r={radius}
                className="stroke-slate-900 fill-transparent"
                strokeWidth="10"
              />
              <circle
                cx="72"
                cy="72"
                r={radius}
                className={`fill-transparent transition-all duration-1000 ${
                  currentPct >= targetPercentage ? 'stroke-emerald-500' : 'stroke-rose-500'
                }`}
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-2xl font-extrabold text-white">{currentPct.toFixed(1)}%</span>
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider mt-0.5">Attendance</span>
            </div>
          </div>

          <div className="flex-1 space-y-4 w-full text-center sm:text-left">
            <div className="space-y-1">
              <span className="text-xs font-bold font-mono text-brand-400 uppercase bg-brand-500/5 px-2 py-0.5 rounded border border-brand-500/10">
                {course.course_code}
              </span>
              <h2 className="text-xl md:text-2xl font-extrabold text-white tracking-tight mt-2">
                {course.course_name}
              </h2>
            </div>
            
            <div className="grid grid-cols-3 gap-4 bg-slate-900/40 p-4 rounded-xl border border-slate-900 text-center">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Attended</p>
                <p className="text-xl font-bold text-white mt-1">{attended}</p>
              </div>
              <div className="border-x border-slate-800">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Bunked</p>
                <p className="text-xl font-bold text-slate-300 mt-1">{total - attended}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Total</p>
                <p className="text-xl font-bold text-slate-300 mt-1">{total}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Shortage Summary and Trend Card (right card) */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-900 flex flex-col justify-between">
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <BarChart4 className="w-4 h-4 text-brand-400" />
              <span>Attendance Trend</span>
            </h3>
            <p className="text-[11px] text-slate-500">Accumulated percentage over past 10 classes</p>
          </div>
          
          {renderTrendLine()}

          <div className="pt-4 border-t border-slate-900 flex justify-between items-center text-xs">
            <span className="text-slate-400">Current Target:</span>
            <span className="font-extrabold text-brand-400 bg-brand-500/5 px-2 py-0.5 rounded border border-brand-500/10">
              {targetPercentage}%
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Attendance Calculator Section */}
      <div className="glass-panel p-6 md:p-8 rounded-2xl border border-slate-900 space-y-6">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <BarChart4 className="w-5 h-5 text-indigo-400" />
            <span>Interactive Bunk Calculator</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Simulate "what-if" bunk allowance and required attendance scenarios in real-time.
          </p>
        </div>

        {/* Target Status Bar */}
        <div className="p-4 bg-slate-950 rounded-xl border border-slate-900 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-500">Need to Reach {targetPercentage}%:</span>
            <span className={`text-sm font-bold ${requiredStats.classesNeededToAttend > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
              {requiredStats.classesNeededToAttend > 0 
                ? `Attend ${requiredStats.classesNeededToAttend} more classes` 
                : '✓ Already met'}
            </span>
          </div>
          <div className="flex items-center space-x-3 sm:border-l sm:border-slate-900 sm:pl-4">
            <span className="text-xs text-slate-500">Can Safely Bunk:</span>
            <span className={`text-sm font-bold ${requiredStats.classesCanBunk > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
              {requiredStats.classesCanBunk > 0 
                ? `${requiredStats.classesCanBunk} classes` 
                : 'Cannot bunk any classes'}
            </span>
          </div>
        </div>

        {/* Inputs and Scenarios */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Scenario 1: Attend More Classes */}
          <div className="p-5 rounded-xl bg-emerald-500/5 border border-emerald-500/10 flex flex-col justify-between space-y-4">
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
                <PlusCircle className="w-4 h-4" />
                <span>Attend More Classes</span>
              </h4>
              <p className="text-xs text-slate-500">If I attend more classes consecutively...</p>
            </div>
            
            <div className="flex items-center space-x-3">
              <input
                type="number"
                min="0"
                max="100"
                value={classesToAttend}
                onChange={(e) => setClassesToAttend(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-20 px-3 py-2 glass-input font-bold text-center no-spinner text-sm"
              />
              <span className="text-xs text-slate-400">additional classes</span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-900 text-xs flex justify-between items-center">
              <span className="text-slate-400">Predicted Attendance:</span>
              <div className="text-right">
                <p className="font-extrabold text-white">{attendResult.newAttended} / {attendResult.newTotal}</p>
                <p className={`font-bold mt-0.5 ${attendResult.meetsTarget ? 'text-emerald-400' : 'text-slate-400'}`}>
                  {attendResult.newPercentage}% {attendResult.meetsTarget ? '✓' : ''}
                </p>
              </div>
            </div>
          </div>

          {/* Scenario 2: Bunk Classes */}
          <div className="p-5 rounded-xl bg-rose-500/5 border border-rose-500/10 flex flex-col justify-between space-y-4">
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-rose-400 flex items-center gap-1.5">
                <MinusCircle className="w-4 h-4" />
                <span>Bunk Classes</span>
              </h4>
              <p className="text-xs text-slate-500">If I decide to bunk upcoming classes...</p>
            </div>
            
            <div className="flex items-center space-x-3">
              <input
                type="number"
                min="0"
                max="100"
                value={classesToBunk}
                onChange={(e) => setClassesToBunk(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-20 px-3 py-2 glass-input font-bold text-center no-spinner text-sm"
              />
              <span className="text-xs text-slate-400">future lectures</span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-900 text-xs flex flex-col space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Predicted Attendance:</span>
                <div className="text-right">
                  <p className="font-extrabold text-white">{bunkResult.newAttended} / {bunkResult.newTotal}</p>
                  <p className={`font-bold mt-0.5 ${bunkResult.meetsTarget ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {bunkResult.newPercentage}%
                  </p>
                </div>
              </div>
              {bunkResult.warning && (
                <div className="text-[10px] text-rose-300 bg-rose-500/10 p-1.5 rounded border border-rose-500/10 mt-1 animate-pulse-subtle">
                  ⚠️ Goes below the {targetPercentage}% threshold limit!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Class-by-Class Breakdown Table */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-900 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
          <h3 className="text-base font-bold text-white">Class-by-Class History</h3>
          
          <div className="flex flex-wrap items-center gap-3">
            {/* Search Box */}
            <div className="relative w-full sm:w-56">
              <Search className="absolute inset-y-0 left-0 pl-2.5 w-4 h-4 text-slate-500 self-center pointer-events-none" />
              <input
                type="text"
                placeholder="Search topic or date..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 glass-input text-xs"
              />
            </div>

            {/* Filter Toggle */}
            <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-900">
              {['All', 'Present', 'Absent'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setStatusFilter(tab)}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                    statusFilter === tab 
                      ? 'bg-brand-600 text-white shadow-sm' 
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Classes Table */}
        <div className="overflow-x-auto border border-slate-900 rounded-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/60 border-b border-slate-900 text-xs text-slate-400 font-bold uppercase tracking-wider">
                <th className="py-3.5 px-4">Date</th>
                <th className="py-3.5 px-4">Slot</th>
                <th className="py-3.5 px-4">Lecture Description</th>
                <th className="py-3.5 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900/55 text-sm">
              {filteredClasses.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-12 text-center text-slate-500 text-xs font-medium">
                    No matching class logs found.
                  </td>
                </tr>
              ) : (
                filteredClasses.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/20 transition">
                    <td className="py-3 px-4 font-semibold text-slate-300 whitespace-nowrap">{item.date}</td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-xs whitespace-nowrap">{item.time_slot}</td>
                    <td className="py-3 px-4 text-slate-200 font-medium max-w-xs truncate" title={item.topic}>{item.topic}</td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        item.status === 'Present' 
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/10' 
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/10'
                      }`}>
                        {item.status === 'Present' ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 mr-0.5" />
                            <span>Present</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="w-3 h-3 mr-0.5" />
                            <span>Absent</span>
                          </>
                        )}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
