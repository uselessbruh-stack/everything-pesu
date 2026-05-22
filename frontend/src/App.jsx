import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LoginPage from './views/LoginPage'
import Dashboard from './views/Dashboard'

export default function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <BrowserRouter>
      <Routes>
        {/* Login Page Route */}
        <Route 
          path="/login" 
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
          } 
        />
        
        {/* Main Student Dashboard Panel */}
        <Route 
          path="/dashboard" 
          element={
            isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />
          } 
        />

        {/* Fallbacks */}
        <Route 
          path="/" 
          element={
            <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
          } 
        />
        
        <Route 
          path="*" 
          element={
            <Navigate to="/" replace />
          } 
        />
      </Routes>
    </BrowserRouter>
  )
}
