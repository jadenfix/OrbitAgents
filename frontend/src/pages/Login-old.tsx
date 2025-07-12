import { useState, useEffect } from 'react'

const SpaceLogin = () => {
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
      setError('🚨 Mission parameters incomplete - please fill all fields')
      return
    }

    if (password.length < 8) {
      setError('🔒 Security clearance requires at least 8 characters')
      return
    }

    try {
      // Simulate authentication
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      if (isRegisterMode) {
        setError('✨ Welcome to the fleet! Redirecting to mission control...')
        setTimeout(() => window.location.href = '/dashboard', 2000)
      } else {
        setError('🚀 Authentication successful! Preparing for launch...')
        setTimeout(() => window.location.href = '/dashboard', 2000)
      }
    } catch (err: any) {
      setError('🛸 Communication error with mission control')
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
        {[...Array(150)].map((_, i) => (
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
        
        {/* Mouse-following cosmic effect */}
        <div
          className="absolute w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full blur-3xl transition-all duration-1000 ease-out"
          style={{
            left: `${mousePosition.x - 12}%`,
            top: `${mousePosition.y - 12}%`
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between p-6">
        <button
          onClick={() => window.location.href = '/'}
          className="flex items-center space-x-3 group"
        >
          <div className="w-10 h-10 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full flex items-center justify-center animate-pulse">
            <span className="text-white font-bold">🌌</span>
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent group-hover:scale-105 transition-transform">
              OrbitAgents
            </h1>
            <p className="text-xs text-cyan-300">Return to Base</p>
          </div>
        </button>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-100px)] px-6">
        <div className="w-full max-w-md">
          {/* Orbital Animation */}
          <div className="relative w-40 h-40 mx-auto mb-8">
            <div className="absolute inset-0 rounded-full border border-cyan-400/30 animate-spin" style={{ animationDuration: '15s' }}>
              <div className="absolute w-3 h-3 bg-cyan-400 rounded-full top-0 left-1/2 transform -translate-x-1/2 -translate-y-1"></div>
            </div>
            <div className="absolute inset-4 rounded-full border border-purple-400/30 animate-spin" style={{ animationDuration: '10s', animationDirection: 'reverse' }}>
              <div className="absolute w-2 h-2 bg-purple-400 rounded-full top-0 left-1/2 transform -translate-x-1/2"></div>
            </div>
            
            {/* Center icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full flex items-center justify-center text-xl animate-pulse">
                🚀
              </div>
            </div>
          </div>

          {/* Login Form */}
          <div className="bg-gradient-to-br from-indigo-800/50 to-purple-800/50 backdrop-blur-sm border border-cyan-400/20 rounded-2xl p-8 shadow-2xl">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-2">
                {isRegisterMode ? 'Join the Fleet' : 'Mission Control Access'}
              </h2>
              <p className="text-cyan-200">
                {isRegisterMode 
                  ? 'Register for your space exploration license'
                  : 'Enter your credentials to begin the mission'
                }
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field */}
              <div>
                <label className="block text-cyan-300 text-sm font-medium mb-2">
                  🛰️ Communication ID (Email)
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-indigo-900/50 border border-cyan-400/30 rounded-lg px-4 py-3 text-white placeholder-cyan-300/50 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all duration-300"
                  placeholder="astronaut@orbitagents.space"
                  required
                />
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-cyan-300 text-sm font-medium mb-2">
                  🔐 Security Clearance Code
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-indigo-900/50 border border-cyan-400/30 rounded-lg px-4 py-3 pr-12 text-white placeholder-cyan-300/50 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all duration-300"
                    placeholder="Enter your secret code"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              {/* Error/Success Message */}
              {error && (
                <div className={`p-4 rounded-lg text-center font-medium ${
                  error.includes('✨') || error.includes('🚀') 
                    ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                    : 'bg-red-500/20 text-red-300 border border-red-500/30'
                }`}>
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-cyan-500/25"
              >
                <span className="flex items-center justify-center space-x-2">
                  <span>{isRegisterMode ? 'Launch Registration' : 'Begin Mission'}</span>
                  <span>🚀</span>
                </span>
              </button>
            </form>

            {/* Toggle Mode */}
            <div className="mt-8 text-center">
              <p className="text-cyan-300 mb-4">
                {isRegisterMode 
                  ? 'Already have clearance?' 
                  : 'Need to register for the space program?'
                }
              </p>
              <button
                onClick={toggleMode}
                className="text-purple-400 hover:text-purple-300 font-medium transition-colors duration-300 underline"
              >
                {isRegisterMode ? 'Access Mission Control' : 'Join the Fleet'}
              </button>
            </div>

            {/* Features Preview */}
            <div className="mt-8 pt-6 border-t border-cyan-400/20">
              <h3 className="text-cyan-300 font-medium mb-4 text-center">🌟 Mission Capabilities</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-2xl mb-2">🤖</div>
                  <p className="text-cyan-200">AI Agents</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl mb-2">🌍</div>
                  <p className="text-cyan-200">Global Search</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl mb-2">🔮</div>
                  <p className="text-cyan-200">Future Vision</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl mb-2">🏠</div>
                  <p className="text-cyan-200">Dream Homes</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Demo Access */}
          <div className="mt-6 text-center">
            <button
              onClick={() => window.location.href = '/'}
              className="text-cyan-400 hover:text-cyan-300 transition-colors duration-300 text-sm"
            >
              ← Return to Home Base
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SpaceLogin
