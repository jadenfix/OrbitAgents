import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

const Login = () => {
  const { login, register, isLoading } = useAuth()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      })
    }
    
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Please fill in all required fields')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setIsSubmitting(true)
    try {
      if (isRegisterMode) {
        await register({ email, password })
      } else {
        await login({ email, password })
      }
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'detail' in err ? String(err.detail) : 'Authentication failed. Please try again.'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const toggleMode = () => {
    setIsRegisterMode(!isRegisterMode)
    setError('')
    setEmail('')
    setPassword('')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-black relative overflow-hidden">
      {/* Animated cosmic background */}
      <div className="absolute inset-0">
        {/* Stars */}
        {[...Array(100)].map((_, i) => (
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
        {[...Array(10)].map((_, i) => (
          <div
            key={`orb-${i}`}
            className="absolute rounded-full animate-pulse opacity-20"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: `${Math.random() * 60 + 30}px`,
              height: `${Math.random() * 60 + 30}px`,
              background: `radial-gradient(circle, ${['cyan', 'purple', 'pink', 'blue'][Math.floor(Math.random() * 4)]}, transparent)`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${Math.random() * 5 + 3}s`
            }}
          />
        ))}
        
        {/* Mouse-following cosmic dust */}
        <div
          className="absolute w-80 h-80 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full blur-3xl transition-all duration-1000 ease-out"
          style={{
            left: `${mousePosition.x - 10}%`,
            top: `${mousePosition.y - 10}%`
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-20 flex items-center justify-between p-6">
        <button 
          onClick={() => window.location.href = '/'}
          className="flex items-center space-x-3 group"
        >
          <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
            <span className="text-white font-bold text-lg">O</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              OrbitAgents
            </h1>
            <p className="text-xs text-cyan-300">Housing Platform</p>
          </div>
        </button>
      </nav>

      {/* Main content */}
      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-100px)] px-6">
        <div className="w-full max-w-md">
          {/* Central orbital animation */}
          <div className="relative w-24 h-24 mx-auto mb-12">
            <div className="absolute inset-0 rounded-full border border-cyan-400/40 animate-spin" style={{ animationDuration: '15s' }}>
              <div className="absolute w-2 h-2 bg-cyan-400 rounded-full top-0 left-1/2 transform -translate-x-1/2 -translate-y-1"></div>
            </div>
            <div className="absolute inset-2 rounded-full border border-purple-400/40 animate-spin" style={{ animationDuration: '12s', animationDirection: 'reverse' }}>
              <div className="absolute w-1 h-1 bg-purple-400 rounded-full top-0 left-1/2 transform -translate-x-1/2 -translate-y-1"></div>
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-10 h-10 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full flex items-center justify-center">
                <div className="w-4 h-4 bg-white rounded-sm"></div>
              </div>
            </div>
          </div>

          {/* Login Panel */}
          <div className="bg-gradient-to-br from-indigo-800/30 to-purple-800/30 backdrop-blur-sm border border-cyan-400/20 rounded-2xl p-8 shadow-2xl">
            {/* Header */}
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-4">
                {isRegisterMode ? 'Create Account' : 'Welcome Back'}
              </h2>
              <p className="text-cyan-200">
                {isRegisterMode 
                  ? 'Join the OrbitAgents platform' 
                  : 'Sign in to access your dashboard'
                }
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className={`border rounded-xl p-4 backdrop-blur-sm ${
                  error.includes('successful') || error.includes('created')
                    ? 'bg-gradient-to-r from-green-500/20 to-cyan-500/20 border-green-400/30'
                    : 'bg-gradient-to-r from-red-500/20 to-pink-500/20 border-red-400/30'
                }`}>
                  <p className={`text-sm font-medium ${
                    error.includes('successful') || error.includes('created')
                      ? 'text-green-200'
                      : 'text-red-200'
                  }`}>
                    {error}
                  </p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-cyan-200 mb-2">
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-indigo-900/50 border border-cyan-400/30 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all text-white placeholder-cyan-300/50 backdrop-blur-sm"
                    placeholder="Enter your email"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-cyan-200 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full px-4 py-3 rounded-xl bg-indigo-900/50 border border-cyan-400/30 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all text-white placeholder-cyan-300/50 backdrop-blur-sm pr-12"
                      placeholder="Enter your password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-cyan-300 hover:text-white transition-colors"
                    >
                      {showPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading || isSubmitting}
                className="w-full bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white py-4 rounded-xl font-semibold transition-all duration-300 transform hover:scale-105 shadow-lg"
              >
                {isRegisterMode ? 'Create Account' : 'Sign In'}
              </button>
            </form>

            {/* Toggle Mode */}
            <div className="mt-8 text-center">
              <button
                onClick={toggleMode}
                className="text-cyan-300 hover:text-white transition-colors"
              >
                {isRegisterMode ? (
                  <>
                    <span>Already have an account? </span>
                    <span className="font-semibold">Sign In</span>
                  </>
                ) : (
                  <>
                    <span>Need an account? </span>
                    <span className="font-semibold">Create One</span>
                  </>
                )}
              </button>
            </div>

            {/* Additional Info */}
            <div className="mt-8 pt-6 border-t border-cyan-400/20">
              <div className="text-center">
                <p className="text-cyan-300 text-sm mb-4">
                  Secure access to OrbitAgents platform
                </p>
                <div className="flex justify-center space-x-4 text-xs text-cyan-400">
                  <span>Encrypted</span>
                  <span>Secure</span>
                  <span>Fast</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
