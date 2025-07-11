import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import Login from '@/pages/Login'
import SplitPaneLayout from '@/components/Layout/SplitPaneLayout'
import LoadingSpinner from '@/components/LoadingSpinner'

// Typing animation hook
const useTypingEffect = (text: string, speed: number = 50) => {
  const [displayText, setDisplayText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayText(prev => prev + text[currentIndex])
        setCurrentIndex(prev => prev + 1)
      }, speed)
      return () => clearTimeout(timeout)
    } else {
      setIsComplete(true)
    }
  }, [currentIndex, text, speed])

  return { displayText, isComplete }
}

// Welcome/Landing Page Component
const WelcomePage: React.FC = () => {
  const [isLoaded, setIsLoaded] = useState(false)
  const heroText = "Intelligent Real Estate Automation Platform"
  const subText = "Deploy AI-powered browser agents that automatically search, analyze, and extract real estate data from multiple platforms. Scale your lead generation with intelligent automation."
  
  const { displayText: heroDisplay, isComplete: heroComplete } = useTypingEffect(heroText, 30)
  const { displayText: subDisplay, isComplete: subComplete } = useTypingEffect(
    heroComplete ? subText : "", 15
  )

  useEffect(() => {
    setIsLoaded(true)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-blue-400/20 to-indigo-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-pulse delay-700"></div>
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-emerald-400/20 to-teal-400/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>
      
      {/* Floating particles */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(50)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-blue-400/30 rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${2 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>
      
      <div className="relative z-10">
        {/* Navigation */}
        <nav className={`flex justify-between items-center px-8 py-6 max-w-7xl mx-auto transition-all duration-1000 ${
          isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-10'
        }`}>
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-xl">O</span>
              </div>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-25 animate-pulse"></div>
            </div>
            <div className="relative">
              <span className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                OrbitAgents
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent opacity-50 blur-sm">
                OrbitAgents
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-6">
            <a 
              href="/api/health" 
              target="_blank"
              rel="noopener noreferrer"
              className="group relative text-sm text-gray-600 hover:text-blue-600 transition-all duration-300"
            >
              <span className="relative z-10">System Status</span>
              <div className="absolute -inset-2 bg-gradient-to-r from-blue-600/10 to-indigo-600/10 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </a>
            <a 
              href="/login" 
              className="group relative bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium py-3 px-8 rounded-full transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <span className="relative z-10">Sign In</span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
            </a>
          </div>
        </nav>

        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-8 py-20 text-center">
          <div className={`inline-flex items-center bg-blue-50/80 backdrop-blur-sm border border-blue-200/50 rounded-full px-6 py-3 mb-12 transition-all duration-1000 delay-300 ${
            isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          }`}>
            <div className="w-2 h-2 bg-green-500 rounded-full mr-3 animate-pulse"></div>
            <span className="text-blue-600 text-sm font-medium">✨ AI-Powered Browser Automation • Live</span>
          </div>
          
          <h1 className="text-6xl md:text-8xl font-bold mb-8 leading-tight">
            <span className="bg-gradient-to-r from-slate-900 via-blue-800 to-indigo-800 bg-clip-text text-transparent">
              {heroDisplay}
              {!heroComplete && <span className="animate-pulse">|</span>}
            </span>
          </h1>
          
          <div className="text-xl md:text-2xl text-gray-600 mb-16 max-w-4xl mx-auto leading-relaxed min-h-[120px]">
            {subDisplay}
            {heroComplete && !subComplete && <span className="animate-pulse">|</span>}
          </div>

          {/* CTA Buttons */}
          <div className={`flex flex-col sm:flex-row justify-center gap-6 mb-20 transition-all duration-1000 delay-1000 ${
            subComplete ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          }`}>
            <a 
              href="/login" 
              className="group relative bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-5 px-10 rounded-full transition-all duration-300 shadow-xl hover:shadow-2xl transform hover:scale-105"
            >
              <span className="relative z-10 flex items-center justify-center">
                Start Free Trial
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
            </a>
            <a 
              href="#features" 
              className="group relative border-2 border-gray-200 hover:border-blue-300 bg-white/80 backdrop-blur-sm text-gray-700 hover:text-blue-600 font-semibold py-5 px-10 rounded-full transition-all duration-300 hover:shadow-lg"
            >
              <span className="relative z-10 flex items-center justify-center">
                Explore Features
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </span>
            </a>
          </div>

          {/* Trust indicators */}
          <div className={`flex justify-center items-center space-x-8 text-sm text-gray-500 transition-all duration-1000 delay-1200 ${
            subComplete ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          }`}>
            <div className="flex items-center bg-white/50 backdrop-blur-sm px-4 py-2 rounded-full">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
              Production Ready
            </div>
            <div className="flex items-center bg-white/50 backdrop-blur-sm px-4 py-2 rounded-full">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2 animate-pulse"></div>
              Open Source
            </div>
            <div className="flex items-center bg-white/50 backdrop-blur-sm px-4 py-2 rounded-full">
              <div className="w-3 h-3 bg-purple-500 rounded-full mr-2 animate-pulse"></div>
              Enterprise Grade
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="max-w-7xl mx-auto px-8 py-24">
          <div className="text-center mb-20">
            <h2 className="text-5xl font-bold text-gray-900 mb-6">
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Powerful Features
              </span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to automate your real estate operations with AI-powered precision
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: "🔍",
                title: "Intelligent Search",
                description: "AI-powered search across multiple MLS platforms with natural language processing and advanced filters",
                gradient: "from-blue-500 to-indigo-500"
              },
              {
                icon: "🤖",
                title: "Browser Automation",
                description: "Automated workflows for lead generation, data collection, and form filling across multiple websites",
                gradient: "from-indigo-500 to-purple-500"
              },
              {
                icon: "📊",
                title: "Real-time Analytics",
                description: "Advanced analytics dashboard with real-time insights, performance tracking, and predictive modeling",
                gradient: "from-purple-500 to-pink-500"
              }
            ].map((feature, index) => (
              <div key={index} className="group relative bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl hover:shadow-2xl transition-all duration-500 p-8 border border-white/20 hover:border-blue-200/50 transform hover:-translate-y-2">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 to-indigo-600/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative">
                  <div className={`w-16 h-16 bg-gradient-to-r ${feature.gradient} rounded-2xl flex items-center justify-center mb-6 shadow-lg`}>
                    <span className="text-2xl">{feature.icon}</span>
                  </div>
                  <h3 className="text-2xl font-bold mb-4 text-gray-900">{feature.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-white/80 backdrop-blur-xl border-t border-gray-200/50 py-16">
          <div className="max-w-7xl mx-auto px-8 text-center">
            <div className="flex justify-center items-center space-x-4 mb-8">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">O</span>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                OrbitAgents
              </span>
            </div>
            <div className="flex flex-col sm:flex-row justify-center items-center space-y-2 sm:space-y-0 sm:space-x-8 text-sm text-gray-500">
              <span>© 2024 OrbitAgents. All rights reserved.</span>
              <span className="hidden sm:block">•</span>
              <span>Made with ❤️ for real estate professionals</span>
            </div>
          </div>
        </footer>
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