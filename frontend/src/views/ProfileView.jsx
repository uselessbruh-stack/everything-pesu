import React, { useEffect, useState } from 'react'
import { useAttendanceStore } from '../store/attendanceStore'
import api from '../services/api'
import { 
  User, 
  Settings, 
  Bell, 
  ShieldAlert, 
  HelpCircle,
  CheckCircle2,
  Moon,
  Sun
} from 'lucide-react'

export default function ProfileView() {
  const { targetPercentage, setTargetPercentage } = useAttendanceStore()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [settingsLoading, setSettingsLoading] = useState(false)

  // Local settings states
  const [enableNotifications, setEnableNotifications] = useState(true)
  const [themeMode, setThemeMode] = useState('dark')
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    const fetchProfileData = async () => {
      setLoading(true)
      try {
        const profRes = await api.get('/api/user/profile')
        if (profRes.data.success) {
          setProfile(profRes.data.data)
        }
        
        const setRes = await api.get('/api/user/settings')
        if (setRes.data.success) {
          setEnableNotifications(setRes.data.data.enable_notifications)
          setThemeMode(setRes.data.data.theme || 'dark')
        }
      } catch (err) {
        console.error('Failed to load profile details:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchProfileData()
  }, [])

  const handleSaveSettings = async () => {
    setSettingsLoading(true)
    setSaveSuccess(false)
    try {
      const res = await api.put('/api/user/settings', {
        target_percentage: targetPercentage,
        theme: themeMode,
        enable_notifications: enableNotifications
      })
      if (res.data.success) {
        setSaveSuccess(true)
        setTimeout(() => setSaveSuccess(false), 3000) // clear success state
      }
    } catch (err) {
      console.error('Failed to update settings:', err)
    } finally {
      setSettingsLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="w-full py-20 flex justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      
      {/* Upper Grid: Profile Card + Settings Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Student Profile Details Card */}
        <div className="lg:col-span-1 glass-panel p-6 md:p-8 rounded-2xl border border-slate-900 flex flex-col items-center text-center">
          
          {profile && (
            <>
              <div className="relative mb-5">
                <img 
                  src={profile.avatar_url} 
                  alt="Student Avatar" 
                  className="w-24 h-24 rounded-full border-2 border-brand-500/35 p-1 bg-slate-900"
                />
                <span className="absolute bottom-1.5 right-1.5 w-4 h-4 bg-emerald-500 border-2 border-slate-950 rounded-full" />
              </div>

              <h2 className="text-xl font-extrabold text-white tracking-tight">{profile.name}</h2>
              <p className="text-xs font-bold text-brand-400 font-mono tracking-wider mt-1 uppercase">{profile.srn}</p>
              
              <div className="w-full space-y-4 pt-6 border-t border-slate-900/80 mt-6 text-left text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Department</span>
                  <span className="text-slate-200 font-bold text-right max-w-[150px] truncate">{profile.department}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Program</span>
                  <span className="text-slate-200 font-bold text-right">{profile.program}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Academic Period</span>
                  <span className="text-slate-200 font-bold text-right">{profile.semester}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Division / Section</span>
                  <span className="text-slate-200 font-bold text-right">{profile.section}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">E-Mail Address</span>
                  <span className="text-brand-400 font-bold text-right truncate max-w-[170px]">{profile.email}</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Right Columns: Settings Configurations Panel */}
        <div className="lg:col-span-2 glass-panel p-6 md:p-8 rounded-2xl border border-slate-900 space-y-6 flex flex-col justify-between">
          <div className="space-y-6">
            <h3 className="text-base font-bold text-white flex items-center space-x-2 border-b border-slate-900 pb-3">
              <Settings className="w-5 h-5 text-indigo-400" />
              <span>Application Preferences</span>
            </h3>

            {/* Config Item 1: Attendance Threshold Slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-sm font-bold text-slate-200">Global Attendance Threshold</h4>
                  <p className="text-xs text-slate-500">Target limit to flag course shortages.</p>
                </div>
                <span className="text-brand-400 font-extrabold text-base">{targetPercentage}%</span>
              </div>
              <input 
                type="range" 
                min="50" 
                max="100" 
                step="0.5"
                value={targetPercentage} 
                onChange={(e) => setTargetPercentage(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-brand-500"
              />
              <div className="flex gap-2.5 pt-1">
                {[75, 80, 85, 90].map(val => (
                  <button 
                    key={val}
                    onClick={() => setTargetPercentage(val)}
                    className={`px-3 py-1 text-[11px] font-bold rounded-lg transition ${
                      targetPercentage === val ? 'bg-brand-600 text-white' : 'bg-slate-900 text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {val}%
                  </button>
                ))}
              </div>
            </div>

            {/* Config Item 2: Alerts / Notifications Toggle */}
            <div className="flex items-center justify-between p-4 bg-slate-900/30 rounded-xl border border-slate-900">
              <div className="flex items-start space-x-3.5">
                <div className="p-2 bg-brand-500/10 text-brand-400 rounded-lg border border-brand-500/10">
                  <Bell className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200">Low Attendance Push Alerts</h4>
                  <p className="text-[11px] text-slate-500">Notify me if active rates sink below threshold limits.</p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer select-none">
                <input 
                  type="checkbox" 
                  checked={enableNotifications}
                  onChange={(e) => setEnableNotifications(e.target.checked)}
                  className="sr-only peer" 
                />
                <div className="w-10 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-300 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-600 peer-checked:after:bg-white" />
              </label>
            </div>

            {/* Config Item 3: Dark Mode toggle */}
            <div className="flex items-center justify-between p-4 bg-slate-900/30 rounded-xl border border-slate-900">
              <div className="flex items-start space-x-3.5">
                <div className="p-2 bg-brand-500/10 text-brand-400 rounded-lg border border-brand-500/10">
                  {themeMode === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200">Interface Theme</h4>
                  <p className="text-[11px] text-slate-500">Toggle dark mode visual styles.</p>
                </div>
              </div>
              
              <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-900">
                <button
                  onClick={() => setThemeMode('dark')}
                  className={`px-3 py-1 text-[10px] font-bold rounded transition ${
                    themeMode === 'dark' ? 'bg-brand-600 text-white' : 'text-slate-500'
                  }`}
                >
                  Dark
                </button>
                <button
                  onClick={() => setThemeMode('light')}
                  className={`px-3 py-1 text-[10px] font-bold rounded transition ${
                    themeMode === 'light' ? 'bg-brand-600 text-white' : 'text-slate-500'
                  }`}
                >
                  Light
                </button>
              </div>
            </div>
          </div>

          {/* Action trigger footer */}
          <div className="flex items-center space-x-3 pt-6 border-t border-slate-900/80 mt-4">
            <button
              onClick={handleSaveSettings}
              disabled={settingsLoading}
              className="px-5 py-2.5 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold rounded-xl text-xs transition disabled:opacity-50 select-none active:scale-95 shadow-lg shadow-brand-500/10 hover:shadow-brand-500/20"
            >
              {settingsLoading ? 'Saving...' : 'Apply Preferences'}
            </button>
            
            {saveSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1 animate-fade-in font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Preferences synchronized successfully!</span>
              </span>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
