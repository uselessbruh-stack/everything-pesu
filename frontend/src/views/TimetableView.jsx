import React, { useEffect, useState } from 'react'
import api from '../services/api'
import { 
  Calendar, 
  Clock, 
  MapPin, 
  User, 
  Grid, 
  Layers, 
  Milestone,
  RefreshCw
} from 'lucide-react'

export default function TimetableView() {
  const [activeTab, setActiveTab] = useState('day') // day, week, semester
  const [selectedDay, setSelectedDay] = useState('') // active day in Day view
  const [timetableData, setTimetableData] = useState(null)
  const [semesterCalendar, setSemesterCalendar] = useState([])
  const [loading, setLoading] = useState(false)

  const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

  // Set default day to today's weekday, or Monday if weekend
  useEffect(() => {
    const today = new Date().strftime ? new Date().strftime("%A") : new Date().toLocaleDateString('en-US', { weekday: 'long' })
    if (weekdays.includes(today)) {
      setSelectedDay(today)
    } else {
      setSelectedDay('Monday')
    }
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      // Fetch weekly timetable (contains all weekdays data)
      const tRes = await api.get('/api/timetable/week')
      if (tRes.data.success) {
        setTimetableData(tRes.data.data)
      }
      
      // Fetch semester calendar milestones
      const cRes = await api.get('/api/timetable/semester')
      if (cRes.data.success) {
        setSemesterCalendar(cRes.data.data)
      }
    } catch (err) {
      console.error('Failed to fetch schedules:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const renderDaySchedule = (dayName) => {
    const classes = timetableData?.[dayName] || []
    
    if (classes.length === 0) {
      return (
        <div className="py-12 text-center text-slate-500 text-xs font-semibold border border-dashed border-slate-900 rounded-2xl bg-slate-900/10">
          No classes scheduled for {dayName}.
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {classes.map((cls, index) => (
          <div 
            key={index}
            className="p-5 rounded-2xl glass-panel border border-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-800 transition duration-200"
          >
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-brand-500/10 text-brand-400 rounded-xl border border-brand-500/10 shrink-0">
                <Clock className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold font-mono text-brand-400">{cls.course_code}</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-600" />
                    <span>{cls.room}</span>
                  </span>
                </div>
                <h4 className="text-base font-extrabold text-white">{cls.subject}</h4>
                <p className="text-xs text-slate-400 flex items-center gap-1">
                  <User className="w-3 h-3 text-slate-500" />
                  <span>{cls.instructor}</span>
                </p>
              </div>
            </div>
            
            <div className="flex items-center justify-center bg-slate-900 py-2 px-4 rounded-xl border border-slate-800 self-start md:self-auto min-w-[150px]">
              <span className="text-xs font-bold text-slate-300 font-mono">{cls.time_slot}</span>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      
      {/* Header and navigation tabs */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 p-4 glass-panel rounded-2xl border border-slate-900">
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-900 self-start">
          <button
            onClick={() => setActiveTab('day')}
            className={`flex items-center space-x-2 px-4 py-2 text-xs font-bold rounded-lg transition ${
              activeTab === 'day' ? 'bg-brand-600 text-white' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Day View</span>
          </button>
          <button
            onClick={() => setActiveTab('week')}
            className={`flex items-center space-x-2 px-4 py-2 text-xs font-bold rounded-lg transition ${
              activeTab === 'week' ? 'bg-brand-600 text-white' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <Grid className="w-4 h-4" />
            <span>Week View</span>
          </button>
          <button
            onClick={() => setActiveTab('semester')}
            className={`flex items-center space-x-2 px-4 py-2 text-xs font-bold rounded-lg transition ${
              activeTab === 'semester' ? 'bg-brand-600 text-white' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <Milestone className="w-4 h-4" />
            <span>Semester Milestones</span>
          </button>
        </div>

        <button 
          onClick={fetchData}
          disabled={loading}
          className="p-2 rounded-xl bg-slate-950 border border-slate-900 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition"
          title="Refresh Schedule"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="w-full py-20 flex justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
        </div>
      ) : (
        <>
          {/* Tab 1: Day View */}
          {activeTab === 'day' && (
            <div className="space-y-6">
              {/* Day selection tabs */}
              <div className="flex overflow-x-auto gap-2 pb-2">
                {weekdays.map(day => (
                  <button
                    key={day}
                    onClick={() => setSelectedDay(day)}
                    className={`px-4 py-2.5 text-xs font-extrabold rounded-xl shrink-0 transition border ${
                      selectedDay === day 
                        ? 'bg-brand-600/10 text-brand-400 border-brand-500/20' 
                        : 'bg-slate-900/40 text-slate-500 border-slate-900 hover:text-slate-300'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
              
              {renderDaySchedule(selectedDay)}
            </div>
          )}

          {/* Tab 2: Week View */}
          {activeTab === 'week' && (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              {weekdays.map(day => {
                const classes = timetableData?.[day] || []
                return (
                  <div key={day} className="glass-panel p-5 rounded-2xl border border-slate-900 flex flex-col space-y-4">
                    <h3 className="text-sm font-extrabold text-white border-b border-slate-900 pb-2.5 tracking-tight">
                      {day}
                    </h3>
                    
                    <div className="flex-1 space-y-3.5">
                      {classes.length === 0 ? (
                        <p className="text-[10px] text-slate-600 font-semibold italic text-center py-6">No classes</p>
                      ) : (
                        classes.map((cls, idx) => (
                          <div 
                            key={idx}
                            className="p-3.5 bg-slate-900/40 rounded-xl border border-slate-900/60 flex flex-col space-y-1 hover:border-slate-800 transition"
                          >
                            <span className="text-[9px] font-bold font-mono text-brand-400 uppercase">{cls.course_code}</span>
                            <h4 className="text-xs font-extrabold text-white line-clamp-1">{cls.subject}</h4>
                            <p className="text-[10px] text-slate-500 font-mono pt-1.5 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              <span>{cls.time_slot.split('-')[0]}</span>
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Tab 3: Semester Milestones */}
          {activeTab === 'semester' && (
            <div className="glass-panel p-6 md:p-8 rounded-2xl border border-slate-900 space-y-6">
              <div>
                <h3 className="text-base font-bold text-white">Semester Events & Dates</h3>
                <p className="text-xs text-slate-500 mt-1">Milestones, evaluations, holidays and deadlines from PESU Calendar.</p>
              </div>

              {semesterCalendar.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-12">No milestone dates available.</p>
              ) : (
                <div className="relative border-l border-slate-900 pl-6 ml-2 space-y-6">
                  {semesterCalendar.map((evt, idx) => {
                    // Decide bullet color
                    let dotColor = 'bg-brand-500 border-slate-950'
                    let bgStyle = 'bg-slate-900/30'
                    
                    const titleLower = evt.title.toLowerCase()
                    if (titleLower.includes('isa') || titleLower.includes('esa')) {
                      dotColor = 'bg-amber-500 border-slate-950'
                      bgStyle = 'bg-amber-500/5 border-amber-500/10'
                    } else if (titleLower.includes('holiday') || titleLower.includes('day') || titleLower.includes('festival')) {
                      dotColor = 'bg-emerald-500 border-slate-950'
                      bgStyle = 'bg-emerald-500/5 border-emerald-500/10'
                    }

                    return (
                      <div key={idx} className="relative group">
                        {/* Bullet dot */}
                        <div className={`absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full border-2 ${dotColor}`} />
                        
                        {/* Event Card */}
                        <div className={`p-4 rounded-xl border border-slate-900 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 hover:border-slate-800 transition ${bgStyle}`}>
                          <div>
                            <span className="text-[10px] font-bold text-brand-400 font-mono uppercase tracking-wider bg-brand-500/5 px-2 py-0.5 rounded border border-brand-500/10">
                              {evt.type}
                            </span>
                            <h4 className="text-sm font-extrabold text-white mt-2 group-hover:text-brand-300 transition duration-150">
                              {evt.title}
                            </h4>
                          </div>
                          
                          <span className="text-xs font-bold text-slate-400 font-mono shrink-0 whitespace-nowrap self-start sm:self-auto bg-slate-950/80 px-3 py-1 rounded-lg border border-slate-900">
                            {evt.date}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
