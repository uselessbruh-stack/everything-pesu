import React, { useEffect, useState } from 'react'
import { useAttendanceStore } from '../store/attendanceStore'
import api from '../services/api'
import { 
  RefreshCw, 
  ChevronRight, 
  AlertCircle, 
  CheckCircle2, 
  HelpCircle,
  HelpCircle as InfoIcon
} from 'lucide-react'

export default function AttendanceView({ onSelectCourse }) {
  const { courses, setCourses, targetPercentage, setTargetPercentage } = useAttendanceStore()
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState('')

  // Fetch course list
  const fetchCourses = async (forceSync = false) => {
    setLoading(true)
    setError('')
    try {
      if (forceSync) {
        setSyncing(true)
        await api.post('/api/attendance/sync')
      }
      
      const res = await api.get('/api/attendance/courses')
      if (res.data.success) {
        setCourses(res.data.data)
      }
    } catch (err) {
      console.error(err)
      setError('Failed to load courses. Please try again.')
    } finally {
      setLoading(false)
      setSyncing(false)
    }
  }

  useEffect(() => {
    if (!courses) {
      fetchCourses()
    }
  }, [courses])

  // Local helper to calculate attendance math instantly on the grid
  const calculateCourseStats = (attended, total) => {
    if (total === 0) return { pct: 0, canBunk: 0, mustAttend: 0, status: 'On Track' }
    
    const pct = (attended / total) * 100
    
    let mustAttend = 0
    if (pct < targetPercentage) {
      const num = (targetPercentage * total) - (attended * 100)
      const den = 100 - targetPercentage
      mustAttend = den > 0 ? Math.ceil(num / den) : 0
      mustAttend = Math.max(0, mustAttend)
    }
    
    let canBunk = 0
    if (pct >= targetPercentage) {
      if (targetPercentage > 0) {
        const val = (attended * 100) / targetPercentage
        canBunk = Math.floor(val - total)
        canBunk = Math.max(0, canBunk)
      }
    }

    let status = 'On Track'
    if (pct < targetPercentage) {
      status = 'Below Target'
    } else if (pct < targetPercentage + 3) {
      status = 'Close to Margin'
    }
    
    return { pct, canBunk, mustAttend, status }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Target Setting and Sync Header */}
      <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-center justify-between p-6 glass-panel rounded-2xl border border-slate-900">
        
        {/* Target setting controls */}
        <div className="space-y-2.5 w-full lg:max-w-md">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-slate-300">Set Global Target Percentage</h3>
            <span className="text-brand-400 font-extrabold text-lg">{targetPercentage}%</span>
          </div>
          <div className="flex items-center space-x-4">
            <input 
              type="range" 
              min="50" 
              max="100" 
              step="0.5"
              value={targetPercentage} 
              onChange={(e) => setTargetPercentage(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-brand-500"
            />
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => setTargetPercentage(85)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${targetPercentage === 85 ? 'bg-brand-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-slate-200'}`}
            >
              85% Target (PESU Limit)
            </button>
            <button 
              onClick={() => setTargetPercentage(80)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${targetPercentage === 80 ? 'bg-brand-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-slate-200'}`}
            >
              80% Target
            </button>
            <button 
              onClick={() => setTargetPercentage(75)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${targetPercentage === 75 ? 'bg-brand-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-slate-200'}`}
            >
              75% Target (Minimum)
            </button>
          </div>
        </div>

        {/* Sync trigger */}
        <button
          onClick={() => fetchCourses(true)}
          disabled={loading || syncing}
          className="flex items-center space-x-2 px-5 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-800 transition font-semibold disabled:opacity-50 select-none"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'Syncing...' : 'Sync Attendance'}</span>
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center space-x-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Courses List Grid */}
      {loading && !syncing ? (
        <div className="w-full py-20 flex justify-center">
          <RefreshCw className="w-8 h-8 text-brand-500 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {courses?.map((course) => {
            const code = course.course_code
            const name = course.course_name
            const attended = course.attendance.attended
            const total = course.attendance.total
            
            const stats = calculateCourseStats(attended, total)
            const pct = stats.pct
            
            // Determine border color and badge colors based on target
            let tagColor = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            let progressColor = 'bg-emerald-500'
            let borderHover = 'hover:border-emerald-500/30'
            
            if (stats.status === 'Below Target') {
              tagColor = 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              progressColor = 'bg-rose-500'
              borderHover = 'hover:border-rose-500/30'
            } else if (stats.status === 'Close to Margin') {
              tagColor = 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              progressColor = 'bg-amber-500'
              borderHover = 'hover:border-amber-500/30'
            }

            return (
              <div
                key={code}
                onClick={() => onSelectCourse(code)}
                className={`glass-panel p-6 rounded-2xl cursor-pointer transition-all duration-300 flex flex-col justify-between border border-slate-900/60 ${borderHover} group hover:shadow-lg hover:shadow-brand-500/5 hover:-translate-y-0.5`}
              >
                <div>
                  {/* Top Bar */}
                  <div className="flex justify-between items-start gap-4 mb-3">
                    <span className="text-[11px] font-bold font-mono text-brand-400 tracking-wider uppercase px-2 py-0.5 rounded bg-brand-500/5 border border-brand-500/10">
                      {code}
                    </span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${tagColor}`}>
                      {pct.toFixed(1)}%
                    </span>
                  </div>

                  {/* Title */}
                  <h4 className="text-base font-extrabold text-white group-hover:text-brand-300 transition duration-200 line-clamp-1 mb-4">
                    {name}
                  </h4>

                  {/* Progress Stats */}
                  <div className="space-y-2 mb-6">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Attendance Progress</span>
                      <span className="font-semibold text-slate-200">{attended} / {total} lectures</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-900">
                      <div 
                        className={`h-full rounded-full ${progressColor}`}
                        style={{ width: `${Math.min(100, pct)}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Scenario highlights at bottom */}
                <div className="pt-4 border-t border-slate-900/80 flex justify-between items-center text-xs">
                  {pct >= targetPercentage ? (
                    <div className="flex items-center space-x-1.5 text-emerald-400 font-semibold bg-emerald-500/5 px-2.5 py-1.5 rounded-xl border border-emerald-500/10">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Can bunk <strong className="font-bold">{stats.canBunk}</strong> lectures</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-1.5 text-rose-400 font-semibold bg-rose-500/5 px-2.5 py-1.5 rounded-xl border border-rose-500/10 animate-pulse-subtle">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span>Must attend <strong className="font-bold">{stats.mustAttend}</strong> lectures</span>
                    </div>
                  )}
                  
                  <span className="text-slate-500 group-hover:text-slate-300 flex items-center font-medium transition duration-200">
                    <span>Details</span>
                    <ChevronRight className="w-4 h-4 ml-0.5 group-hover:translate-x-0.5 transition-transform" />
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
