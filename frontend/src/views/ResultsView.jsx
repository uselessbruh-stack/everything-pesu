import React, { useEffect, useState } from 'react'
import api from '../services/api'
import { 
  Award, 
  ChevronDown, 
  ChevronUp, 
  BookOpen, 
  FileText,
  TrendingUp,
  ExternalLink
} from 'lucide-react'

export default function ResultsView({ onSelectCourse }) {
  const [resultsData, setResultsData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expandedSems, setExpandedSems] = useState({}) // track open/closed sem accordions

  useEffect(() => {
    const fetchResults = async () => {
      setLoading(true)
      try {
        const res = await api.get('/api/results')
        if (res.data.success) {
          setResultsData(res.data.data)
          
          // Auto-expand all semesters by default
          const initialExpanded = {}
          Object.keys(res.data.data).forEach(sem => {
            initialExpanded[sem] = true
          })
          setExpandedSems(initialExpanded)
        }
      } catch (err) {
        console.error('Failed to load results:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [])

  const toggleSem = (semName) => {
    setExpandedSems(prev => ({
      ...prev,
      [semName]: !prev[semName]
    }))
  }

  // Parses fractional string marks "29 /40.0" and returns percentage and clean string
  const parseMarks = (marksStr) => {
    if (!marksStr || marksStr.trim() === '') return { score: 0, pct: 0, display: '-' }
    
    // Clean string formatting
    const cleaned = marksStr.replace(/\s+/g, '') // remove spaces
    const parts = cleaned.split('/')
    
    if (parts.length === 2) {
      const score = parseFloat(parts[0]) || 0
      const total = parseFloat(parts[1]) || 1
      const pct = (score / total) * 100
      return { 
        score, 
        total, 
        pct, 
        display: `${score} / ${total}` 
      }
    }
    
    return { score: 0, pct: 0, display: marksStr }
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      
      {/* Overview stats header */}
      <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between p-6 bg-gradient-to-r from-brand-900/40 via-indigo-950/20 to-slate-900/20 border border-brand-500/10 rounded-2xl">
        <div className="space-y-1">
          <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
            Academic Grades & <span className="gradient-text">Assessments</span>
          </h1>
          <p className="text-xs text-slate-400">
            Track your performance in internal exams (ISAs), assignments, and practicals.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-slate-900/60 py-2 px-4 rounded-xl border border-slate-800 self-start md:self-auto">
          <Award className="w-4 h-4 text-brand-400" />
          <span className="text-xs font-semibold text-slate-300">
            Target Grade: <span className="text-brand-400 font-bold">9.0+ SGPA</span>
          </span>
        </div>
      </div>

      {loading ? (
        <div className="w-full py-20 flex justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
        </div>
      ) : resultsData && Object.keys(resultsData).length === 0 ? (
        <div className="glass-panel p-8 text-center text-slate-500 text-sm">
          No grade sheet reports available at this moment.
        </div>
      ) : (
        <div className="space-y-6">
          {resultsData && Object.entries(resultsData).map(([semName, semInfo]) => {
            const isExpanded = expandedSems[semName]
            const coursesList = semInfo.courses || []
            
            return (
              <div key={semName} className="glass-panel rounded-2xl border border-slate-900 overflow-hidden">
                {/* Accordion Trigger Header */}
                <button
                  onClick={() => toggleSem(semName)}
                  className="w-full py-4.5 px-6 bg-slate-900/30 border-b border-slate-900/60 hover:bg-slate-900/40 transition flex items-center justify-between text-left"
                >
                  <div className="flex items-center space-x-3.5">
                    <div className="p-2 bg-brand-500/10 text-brand-400 rounded-lg border border-brand-500/10">
                      <BookOpen className="w-4.5 h-4.5" />
                    </div>
                    <div>
                      <h3 className="font-extrabold text-white text-base tracking-tight">{semName}</h3>
                      <p className="text-[10px] text-slate-500 font-semibold">{semInfo.course_count} active registered courses</p>
                    </div>
                  </div>
                  {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500" />}
                </button>

                {/* Accordion Content Panel */}
                {isExpanded && (
                  <div className="p-6 space-y-6 divide-y divide-slate-900/70">
                    {coursesList.map((course, idx) => (
                      <div 
                        key={course.course_code} 
                        className={`pt-5 first:pt-0 flex flex-col lg:flex-row gap-6 justify-between items-start`}
                      >
                        {/* Course Info */}
                        <div className="space-y-2 lg:max-w-xs w-full">
                          <div className="flex items-center gap-2">
                            <span className="text-[9px] font-bold font-mono text-brand-400 uppercase bg-brand-500/5 px-2 py-0.5 rounded border border-brand-500/10">
                              {course.course_code}
                            </span>
                            
                            <button
                              onClick={() => onSelectCourse(course.course_code)}
                              className="text-[10px] text-slate-500 hover:text-brand-400 flex items-center gap-0.5 transition font-semibold"
                              title="Go to attendance details"
                            >
                              <span>View Attendance</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </button>
                          </div>
                          
                          <h4 className="text-sm font-extrabold text-white tracking-tight line-clamp-2">
                            {course.course_name}
                          </h4>
                        </div>

                        {/* Assessments Listing */}
                        <div className="flex-1 w-full grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4.5">
                          {Object.entries(course.assessments || {}).map(([examName, rawScore]) => {
                            const parsed = parseMarks(rawScore)
                            
                            // Color progress bar depending on percentage
                            let colorClass = 'bg-brand-500'
                            if (parsed.pct < 60) colorClass = 'bg-rose-500'
                            else if (parsed.pct < 75) colorClass = 'bg-amber-500'
                            else if (parsed.pct >= 85) colorClass = 'bg-emerald-500'

                            return (
                              <div 
                                key={examName}
                                className="p-3 bg-slate-900/30 rounded-xl border border-slate-900 flex flex-col justify-between space-y-2 hover:border-slate-800/80 transition"
                              >
                                <div className="flex justify-between items-center text-xs">
                                  <span className="font-bold text-slate-400 flex items-center gap-1">
                                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                                    {examName}
                                  </span>
                                  <span className="font-extrabold text-white font-mono text-[11px]">{parsed.display}</span>
                                </div>
                                
                                {parsed.total && (
                                  <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-900">
                                    <div 
                                      className={`h-full rounded-full ${colorClass}`}
                                      style={{ width: `${Math.min(100, parsed.pct)}%` }}
                                    />
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
