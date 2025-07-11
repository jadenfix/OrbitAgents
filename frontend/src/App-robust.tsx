import { useState, useEffect, Suspense, lazy, Component, ReactNode } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'

// Simple Error Boundary
class AppErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('App Error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return <SimpleFallback />
    }
    return this.props.children
  }
}

// Simple fallback component that doesn't rely on external imports
const SimpleFallback = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-600 rounded-lg mr-3"></div>
            <h1 className="text-xl font-bold text-gray-900">OrbitAgents</h1>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Reload
          </button>
        </div>
      </div>
    </header>

    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl">
          <span className="block">Intelligent Real Estate</span>
          <span className="block text-blue-600">Automation Platform</span>
        </h1>
        <p className="mt-6 max-w-2xl mx-auto text-lg text-gray-500">
          Deploy AI-powered browser agents that automatically search, analyze, and extract real estate data from multiple platforms.
        </p>
        
        <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Browser Automation</h3>
            <p className="text-gray-600">Intelligent browser agents that navigate real estate platforms automatically.</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered Analysis</h3>
            <p className="text-gray-600">Advanced AI models analyze property data and generate insights.</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Real-time Monitoring</h3>
            <p className="text-gray-600">Comprehensive monitoring for automation workflows.</p>
          </div>
        </div>

        <div className="mt-12 bg-white rounded-xl shadow-lg p-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Test Backend Connection</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={async () => {
                try {
                  const response = await fetch('/api/health')
                  const data = await response.json()
                  alert(`Health Check: ${JSON.stringify(data, null, 2)}`)
                } catch (error) {
                  alert('Health endpoint not available. Ensure backend is running on port 8080.')
                }
              }}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors font-medium"
            >
              Health Check
            </button>
            <button
              onClick={async () => {
                try {
                  const response = await fetch('/api/demo')
                  const data = await response.json()
                  alert(`Demo Response: ${JSON.stringify(data, null, 2)}`)
                } catch (error) {
                  alert('Demo endpoint not available. Ensure backend is running on port 8080.')
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors font-medium"
            >
              Demo Endpoint
            </button>
          </div>
          <p className="mt-4 text-sm text-gray-500">
            Backend should be running on <code className="bg-gray-100 px-2 py-1 rounded">http://localhost:8080</code>
          </p>
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Platform Status</h3>
              <p className="mt-1 text-sm text-blue-700">
                OrbitAgents is initializing. All core features are available through the API endpoints.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
)

// Loading component
const SimpleLoading = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
      <p className="mt-4 text-lg text-gray-600">Loading OrbitAgents...</p>
    </div>
  </div>
)

// Lazy load components with fallbacks
const AuthProvider = lazy(() => 
  import('@/contexts/AuthContext')
    .then(module => ({ default: module.AuthProvider }))
    .catch(error => {
      console.warn('AuthContext failed to load:', error)
      return { default: ({ children }: { children: ReactNode }) => <>{children}</> }
    })
)

const Login = lazy(() => 
  import('@/pages/Login')
    .catch(error => {
      console.warn('Login page failed to load:', error)
      return { default: SimpleFallback }
    })
)

const SplitPaneLayout = lazy(() => 
  import('@/components/Layout/SplitPaneLayout')
    .catch(error => {
      console.warn('SplitPaneLayout failed to load:', error)
      return { default: SimpleFallback }
    })
)

const LoadingSpinner = lazy(() =>
  import('@/components/LoadingSpinner')
    .catch(error => {
      console.warn('LoadingSpinner failed to load:', error)
      return { default: SimpleLoading }
    })
)

// Auth hook with fallback
const useAuth = () => {
  try {
    // Try to import and use the real auth context
    const authModule = require('@/contexts/AuthContext')
    return authModule.useAuth()
  } catch (error) {
    console.warn('Auth context not available, using fallback')
    return {
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: async () => {},
      logout: () => {},
      register: async () => {}
    }
  }
}

// Welcome/Landing Page Component
const WelcomePage = () => {
  const heroText = "Intelligent Real Estate Automation Platform"
  const [displayText, setDisplayText] = useState("")
  const [textIndex, setTextIndex] = useState(0)

  useEffect(() => {
    if (textIndex < heroText.length) {
      const timeout = setTimeout(() => {
        setDisplayText(prev => prev + heroText[textIndex])
        setTextIndex(prev => prev + 1)
      }, 50)
      return () => clearTimeout(timeout)
    }
  }, [textIndex, heroText])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-blue-400/20 to-indigo-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-emerald-400/20 to-teal-400/20 rounded-full blur-3xl animate-pulse"></div>
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Navigation */}
        <nav className="flex items-center justify-between p-6">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">O</span>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
              OrbitAgents
            </span>
          </div>
          <button 
            onClick={() => window.location.href = '/login'}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2.5 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
          >
            Get Started
          </button>
        </nav>

        {/* Hero Section */}
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-120px)] text-center px-6">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              <span className="bg-gradient-to-r from-gray-900 via-blue-900 to-gray-900 bg-clip-text text-transparent">
                {displayText}
                <span className="animate-pulse">|</span>
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Deploy AI-powered browser agents that automatically search, analyze, and extract real estate data from multiple platforms. Scale your lead generation with intelligent automation.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
              >
                Launch Platform
              </button>
              <button
                onClick={async () => {
                  try {
                    const response = await fetch('/api/demo')
                    const data = await response.json()
                    alert(`Demo: ${JSON.stringify(data, null, 2)}`)
                  } catch (error) {
                    alert('Demo endpoint not available')
                  }
                }}
                className="bg-white hover:bg-gray-50 text-gray-700 px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl border border-gray-200"
              >
                View Demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Protected Route component
const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const auth = useAuth()

  if (auth.isLoading) {
    return <SimpleLoading />
  }

  return auth.isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

// Main App Routes
const AppRoutes = () => {
  const auth = useAuth()

  if (auth.isLoading) {
    return <SimpleLoading />
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={auth.isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} 
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
const App = () => {
  return (
    <AppErrorBoundary>
      <Suspense fallback={<SimpleLoading />}>
        <AuthProvider>
          <Router>
            <div className="App">
              <AppRoutes />
            </div>
          </Router>
        </AuthProvider>
      </Suspense>
    </AppErrorBoundary>
  )
}

export default App
