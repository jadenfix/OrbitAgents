import { useState, useEffect, Suspense, lazy, Component, ReactNode } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'

// Space-themed Error Boundary
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
      return <SpaceFallback />
    }
    return this.props.children
  }
}

// Beautiful space-themed fallback
const SpaceFallback = () => (
  <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-black relative overflow-hidden">
    {/* Animated stars */}
    <div className="absolute inset-0">
      {[...Array(100)].map((_, i) => (
        <div
          key={i}
          className="absolute bg-white rounded-full animate-pulse"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            width: `${Math.random() * 3 + 1}px`,
            height: `${Math.random() * 3 + 1}px`,
            animationDelay: `${Math.random() * 3}s`,
            animationDuration: `${Math.random() * 3 + 2}s`
          }}
        />
      ))}
    </div>
    
    <div className="relative z-10 flex items-center justify-center min-h-screen p-8">
      <div className="text-center">
        <div className="w-24 h-24 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full mx-auto mb-8 animate-spin"></div>
        <h1 className="text-4xl font-bold text-white mb-4">OrbitAgents</h1>
        <p className="text-cyan-200 mb-8">Navigating you to your perfect home...</p>
        <button
          onClick={() => window.location.reload()}
          className="bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white px-8 py-3 rounded-full transition-all duration-300 transform hover:scale-105"
        >
          Re-enter Orbit
        </button>
      </div>
    </div>
  </div>
)

// Loading component with space theme
const SpaceLoading = () => (
  <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-black flex items-center justify-center relative overflow-hidden">
    {/* Floating particles */}
    <div className="absolute inset-0">
      {[...Array(50)].map((_, i) => (
        <div
          key={i}
          className="absolute bg-cyan-400 rounded-full opacity-30 animate-bounce"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            width: `${Math.random() * 4 + 2}px`,
            height: `${Math.random() * 4 + 2}px`,
            animationDelay: `${Math.random() * 2}s`
          }}
        />
      ))}
    </div>
    
    <div className="text-center relative z-10">
      <div className="w-32 h-32 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-8"></div>
      <h2 className="text-2xl text-white font-light tracking-wide">
        Preparing your journey through space...
      </h2>
      <p className="text-cyan-300 mt-4">Finding homes across the universe</p>
    </div>
  </div>
)

// Lazy load components with space-themed fallbacks
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
      return { default: SpaceFallback }
    })
)

const SplitPaneLayout = lazy(() => 
  import('@/components/Layout/SplitPaneLayout')
    .catch(error => {
      console.warn('SplitPaneLayout failed to load:', error)
      return { default: SpaceFallback }
    })
)

// Auth hook with fallback
const useAuth = () => {
  try {
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

// Main space-themed landing page
const SpaceLandingPage = () => {
  const [mounted, setMounted] = useState(false)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  
  useEffect(() => {
    setMounted(true)
    
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      })
    }
    
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  if (!mounted) return <SpaceLoading />

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-black relative overflow-hidden">
      {/* Animated cosmic background */}
      <div className="absolute inset-0">
        {/* Stars */}
        {[...Array(200)].map((_, i) => (
          <div
            key={`star-${i}`}
            className="absolute bg-white rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: `${Math.random() * 2 + 1}px`,
              height: `${Math.random() * 2 + 1}px`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${Math.random() * 3 + 2}s`
            }}
          />
        ))}
        
        {/* Floating orbs */}
        {[...Array(20)].map((_, i) => (
          <div
            key={`orb-${i}`}
            className="absolute rounded-full animate-pulse opacity-20"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: `${Math.random() * 100 + 50}px`,
              height: `${Math.random() * 100 + 50}px`,
              background: `radial-gradient(circle, ${['cyan', 'purple', 'pink', 'blue'][Math.floor(Math.random() * 4)]}, transparent)`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${Math.random() * 5 + 3}s`
            }}
          />
        ))}
        
        {/* Mouse-following cosmic dust */}
        <div
          className="absolute w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full blur-3xl transition-all duration-1000 ease-out"
          style={{
            left: `${mousePosition.x - 12}%`,
            top: `${mousePosition.y - 12}%`
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-20 flex items-center justify-between p-6">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full flex items-center justify-center animate-pulse">
            <span className="text-white font-bold text-lg">🌌</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              OrbitAgents
            </h1>
            <p className="text-xs text-cyan-300">Housing Navigator</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => window.location.href = '/login'}
            className="text-cyan-300 hover:text-white transition-colors duration-300"
          >
            Sign In
          </button>
          <button 
            onClick={() => window.location.href = '/dashboard'}
            className="bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white px-6 py-2 rounded-full transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-cyan-500/25"
          >
            Launch Mission
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-100px)] text-center px-6">
        <div className="max-w-6xl mx-auto">
          {/* Main orbit animation */}
          <div className="relative w-96 h-96 mx-auto mb-12">
            <div className="absolute inset-0 rounded-full border border-cyan-400/30 animate-spin" style={{ animationDuration: '20s' }}>
              <div className="absolute w-4 h-4 bg-cyan-400 rounded-full top-0 left-1/2 transform -translate-x-1/2 -translate-y-2"></div>
            </div>
            <div className="absolute inset-4 rounded-full border border-purple-400/30 animate-spin" style={{ animationDuration: '15s', animationDirection: 'reverse' }}>
              <div className="absolute w-3 h-3 bg-purple-400 rounded-full top-0 left-1/2 transform -translate-x-1/2 -translate-y-1"></div>
            </div>
            <div className="absolute inset-8 rounded-full border border-pink-400/30 animate-spin" style={{ animationDuration: '10s' }}>
              <div className="absolute w-2 h-2 bg-pink-400 rounded-full top-0 left-1/2 transform -translate-x-1/2"></div>
            </div>
            
            {/* Center home icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-20 h-20 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full flex items-center justify-center text-3xl animate-pulse">
                🏠
              </div>
            </div>
          </div>

          <h1 className="text-6xl md:text-8xl font-bold mb-8 leading-tight">
            <span className="block bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent animate-pulse">
              Finding Housing
            </span>
            <span className="block text-white mt-4">
              Doesn't Have to Feel Like
            </span>
            <span className="block bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
              Another Planet
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-cyan-200 mb-12 max-w-4xl mx-auto leading-relaxed">
            Navigate the universe of real estate with AI-powered agents that search, 
            analyze, and discover your perfect home across infinite possibilities.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-16">
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="group bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white px-12 py-4 rounded-full text-xl font-semibold transition-all duration-300 transform hover:scale-105 shadow-2xl hover:shadow-cyan-500/50"
            >
              <span className="flex items-center justify-center space-x-2">
                <span>Begin Your Journey</span>
                <span className="group-hover:translate-x-1 transition-transform">🚀</span>
              </span>
            </button>
            
            <button
              onClick={async () => {
                try {
                  const response = await fetch('/api/demo')
                  const data = await response.json()
                  alert(`Demo Mission Report: ${JSON.stringify(data, null, 2)}`)
                } catch (error) {
                  alert('Mission Control offline. Please ensure orbital systems are active.')
                }
              }}
              className="group bg-transparent border-2 border-cyan-400 hover:bg-cyan-400/10 text-cyan-300 hover:text-white px-12 py-4 rounded-full text-xl font-semibold transition-all duration-300 transform hover:scale-105"
            >
              <span className="flex items-center justify-center space-x-2">
                <span>Demo Mission</span>
                <span className="group-hover:rotate-12 transition-transform">🛸</span>
              </span>
            </button>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20">
            {[
              {
                icon: "🤖",
                title: "AI Space Agents",
                description: "Intelligent agents explore the vast real estate universe, discovering properties across multiple dimensions of data."
              },
              {
                icon: "🌍",
                title: "Planetary Search",
                description: "Search across all inhabited real estate planets with advanced filters and cosmic intelligence."
              },
              {
                icon: "🔮",
                title: "Future Vision",
                description: "Predict market trends and property values using quantum algorithms and temporal analysis."
              }
            ].map((feature, index) => (
              <div
                key={index}
                className="group bg-gradient-to-br from-indigo-800/50 to-purple-800/50 backdrop-blur-sm border border-cyan-400/20 rounded-2xl p-8 hover:border-cyan-400/50 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/20"
              >
                <div className="text-6xl mb-6 group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-2xl font-bold text-white mb-4 group-hover:text-cyan-300 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-cyan-200 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>

          {/* API Testing Section */}
          <div className="mt-20 bg-gradient-to-r from-indigo-900/50 to-purple-900/50 backdrop-blur-sm rounded-2xl p-8 border border-cyan-400/20">
            <h3 className="text-3xl font-bold text-white mb-6 flex items-center justify-center space-x-3">
              <span>🛰️</span>
              <span>Mission Control Systems</span>
            </h3>
            <p className="text-cyan-200 text-center mb-8">
              Test orbital communication systems and agent connectivity
            </p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button
                onClick={async () => {
                  try {
                    const response = await fetch('/api/health')
                    const data = await response.json()
                    alert(`🛰️ System Status: ${JSON.stringify(data, null, 2)}`)
                  } catch (error) {
                    alert('🚨 Orbital systems offline. Check mission control at port 8080.')
                  }
                }}
                className="bg-gradient-to-r from-green-500 to-cyan-500 hover:from-green-600 hover:to-cyan-600 text-white px-8 py-4 rounded-full font-semibold transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/25"
              >
                🟢 System Health Check
              </button>
              
              <button
                onClick={async () => {
                  try {
                    const response = await fetch('/api/demo')
                    const data = await response.json()
                    alert(`🚀 Demo Mission: ${JSON.stringify(data, null, 2)}`)
                  } catch (error) {
                    alert('🛸 Demo mission failed. Ensure agents are deployed on port 8080.')
                  }
                }}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-4 rounded-full font-semibold transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-purple-500/25"
              >
                🔮 Demo Agent Mission
              </button>
            </div>
            
            <p className="text-center text-cyan-300 text-sm mt-6">
              Mission Control: <code className="bg-indigo-800 px-2 py-1 rounded">http://localhost:8080</code>
            </p>
          </div>

          {/* Status indicator */}
          <div className="mt-12 flex items-center justify-center space-x-4 text-cyan-300">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            <span>Orbital systems online • Ready for space exploration</span>
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
    return <SpaceLoading />
  }

  return auth.isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

// Main App Routes
const AppRoutes = () => {
  const auth = useAuth()

  if (auth.isLoading) {
    return <SpaceLoading />
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
      <Route path="/" element={<SpaceLandingPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

// Main App Component
const App = () => {
  return (
    <AppErrorBoundary>
      <Suspense fallback={<SpaceLoading />}>
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
