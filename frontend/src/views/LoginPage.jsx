import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { LogIn, Lock, User, AlertCircle, Loader2 } from 'lucide-react'
import api from '../services/api'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const loginStore = useAuthStore((state) => state.login)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setError('Please fill in all credentials.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await api.post('/api/auth/login', {
        username: username.trim(),
        password: password.trim()
      })
      
      const { access_token, user } = response.data
      loginStore(access_token, user)
      navigate('/dashboard')
    } catch (err) {
      console.error(err)
      setError(
        err.response?.data?.detail || 
        'Login failed. Please check your credentials or network.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden px-4">
      {/* Dynamic Background Mesh Circles */}
      <div className="bg-mesh-circle w-[500px] h-[500px] bg-brand-600 top-[-10%] left-[-10%]" />
      <div className="bg-mesh-circle w-[600px] h-[600px] bg-indigo-500 bottom-[-15%] right-[-10%] animation-delay-2000" />
      
      {/* Decorative center glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-indigo-500/10 blur-[100px] pointer-events-none rounded-full" />

      {/* Main card panel */}
      <div className="w-full max-w-md glass-panel p-8 rounded-2xl shadow-2xl relative z-10 border border-slate-800 animate-slide-up">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3 bg-brand-500/10 rounded-xl mb-4 border border-brand-500/20">
            <LogIn className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            PESU <span className="gradient-text">Academy</span>
          </h1>
          <p className="text-slate-400 text-sm mt-2">
            Sign in to check attendance and analyze metrics
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start space-x-3 text-rose-300 text-sm animate-fade-in">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* Username Input */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Student Username / SRN
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <User className="w-5 h-5" />
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. pes1pg25ca005"
                className="w-full pl-10 pr-4 py-3 glass-input text-base placeholder-slate-500"
                disabled={loading}
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
                Password
              </label>
            </div>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-5 h-5" />
              </span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-3 glass-input text-base placeholder-slate-500"
                disabled={loading}
              />
            </div>
          </div>

          {/* Remember Me Option */}
          <div className="flex items-center">
            <input
              id="remember-me"
              type="checkbox"
              defaultChecked
              className="h-4 w-4 rounded bg-slate-900 border-slate-700 text-brand-600 focus:ring-brand-500 focus:ring-offset-slate-900"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-slate-400 select-none">
              Remember my session
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-semibold rounded-xl transition duration-200 flex items-center justify-center space-x-2 border border-brand-400/20 active:scale-95 disabled:opacity-50 disabled:pointer-events-none hover:shadow-lg hover:shadow-brand-500/20"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Logging you in...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        {/* Demo instructions */}
        <div className="mt-8 pt-6 border-t border-slate-800 text-center">
          <p className="text-xs text-slate-500">
            Demo account: <span className="text-brand-400 font-mono">pes1pg25ca005</span>
          </p>
          <p className="text-[10px] text-slate-600 mt-1">
            *Offline mode is supported. If Scraping is unavailable, cached data will be loaded automatically.
          </p>
        </div>
      </div>
    </div>
  )
}
