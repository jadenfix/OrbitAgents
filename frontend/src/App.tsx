import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import Login from '@/pages/Login'
import SplitPaneLayout from '@/components/Layout/SplitPaneLayout'
import LoadingSpinner from '@/components/LoadingSpinner'

// Welcome/Landing Page Component
const WelcomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-4xl mx-auto px-4 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          🚀 OrbitAgents
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Intelligent Real Estate Automation Platform with AI-Powered Browser Agents
        </p>
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-3xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold mb-2">Smart Search</h3>
            <p className="text-gray-600">AI-powered property search across multiple platforms</p>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-3xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold mb-2">Browser Automation</h3>
            <p className="text-gray-600">Automated workflows for lead generation and data collection</p>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">Analytics</h3>
            <p className="text-gray-600">Real-time insights and performance tracking</p>
          </div>
        </div>
        <div className="flex justify-center space-x-4">
          <a 
            href="/login" 
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-8 rounded-lg transition-colors duration-200"
          >
            Get Started
          </a>
          <a 
            href="/api/health" 
            target="_blank"
            rel="noopener noreferrer"
            className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-8 rounded-lg transition-colors duration-200"
          >
            API Status
          </a>
        </div>
        <div className="mt-12 text-sm text-gray-500">
          <p>Ready for production • Deployed on Vercel • API endpoints available</p>
        </div>
      </div>
    </div>
  )
}

// Protected Route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner />
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

// Main App Routes
const AppRoutes: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} 
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <SplitPaneLayout />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<WelcomePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

// Main App Component
const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppRoutes />
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App 