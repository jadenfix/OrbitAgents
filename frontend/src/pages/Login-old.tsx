import { useState, useEffect } from 'react';

const SpaceLogin = () => {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('🚨 Mission parameters incomplete - please fill all fields');
      return;
    }

    if (password.length < 8) {
      setError('🔒 Security clearance requires at least 8 characters');
      return;
    }

    try {
      // Simulate authentication
      await new Promise((resolve) => setTimeout(resolve, 1000));

      if (isRegisterMode) {
        setError('✨ Welcome to the fleet! Redirecting to mission control...');
        setTimeout(() => (window.location.href = '/dashboard'), 2000);
      } else {
        setError('🚀 Authentication successful! Preparing for launch...');
        setTimeout(() => (window.location.href = '/dashboard'), 2000);
      }
    } catch {
      setError('🛸 Communication error with mission control');
    }
  };

  const toggleMode = () => {
    setIsRegisterMode(!isRegisterMode);
    setError('');
    setEmail('');
    setPassword('');
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-indigo-900 via-purple-900 to-black">
      {/* Animated cosmic background */}
      <div className="absolute inset-0">
        {/* Stars */}
        {[...Array(150)].map((_, i) => (
          <div
            key={`star-${i}`}
            className="absolute animate-pulse rounded-full bg-white"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: `${Math.random() * 2 + 1}px`,
              height: `${Math.random() * 2 + 1}px`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${Math.random() * 3 + 2}s`,
            }}
          />
        ))}

        {/* Mouse-following cosmic effect */}
        <div
          className="absolute h-96 w-96 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-500/20 blur-3xl transition-all duration-1000 ease-out"
          style={{
            left: `${mousePosition.x - 12}%`,
            top: `${mousePosition.y - 12}%`,
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between p-6">
        <button
          onClick={() => (window.location.href = '/')}
          className="group flex items-center space-x-3"
        >
          <div className="flex h-10 w-10 animate-pulse items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-purple-400">
            <span className="font-bold text-white">🌌</span>
          </div>
          <div>
            <h1 className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-xl font-bold text-transparent transition-transform group-hover:scale-105">
              OrbitAgents
            </h1>
            <p className="text-xs text-cyan-300">Return to Base</p>
          </div>
        </button>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 flex min-h-[calc(100vh-100px)] items-center justify-center px-6">
        <div className="w-full max-w-md">
          {/* Orbital Animation */}
          <div className="relative mx-auto mb-8 h-40 w-40">
            <div
              className="absolute inset-0 animate-spin rounded-full border border-cyan-400/30"
              style={{ animationDuration: '15s' }}
            >
              <div className="absolute left-1/2 top-0 h-3 w-3 -translate-x-1/2 -translate-y-1 transform rounded-full bg-cyan-400"></div>
            </div>
            <div
              className="absolute inset-4 animate-spin rounded-full border border-purple-400/30"
              style={{
                animationDuration: '10s',
                animationDirection: 'reverse',
              }}
            >
              <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 transform rounded-full bg-purple-400"></div>
            </div>

            {/* Center icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex h-12 w-12 animate-pulse items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-purple-400 text-xl">
                🚀
              </div>
            </div>
          </div>

          {/* Login Form */}
          <div className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-indigo-800/50 to-purple-800/50 p-8 shadow-2xl backdrop-blur-sm">
            <div className="mb-8 text-center">
              <h2 className="mb-2 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-3xl font-bold text-transparent">
                {isRegisterMode ? 'Join the Fleet' : 'Mission Control Access'}
              </h2>
              <p className="text-cyan-200">
                {isRegisterMode
                  ? 'Register for your space exploration license'
                  : 'Enter your credentials to begin the mission'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field */}
              <div>
                <label className="mb-2 block text-sm font-medium text-cyan-300">
                  🛰️ Communication ID (Email)
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-cyan-400/30 bg-indigo-900/50 px-4 py-3 text-white placeholder-cyan-300/50 transition-all duration-300 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                  placeholder="astronaut@orbitagents.space"
                  required
                />
              </div>

              {/* Password Field */}
              <div>
                <label className="mb-2 block text-sm font-medium text-cyan-300">
                  🔐 Security Clearance Code
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-lg border border-cyan-400/30 bg-indigo-900/50 px-4 py-3 pr-12 text-white placeholder-cyan-300/50 transition-all duration-300 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                    placeholder="Enter your secret code"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 transform text-cyan-400 transition-colors hover:text-cyan-300"
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              {/* Error/Success Message */}
              {error && (
                <div
                  className={`rounded-lg p-4 text-center font-medium ${
                    error.includes('✨') || error.includes('🚀')
                      ? 'border border-green-500/30 bg-green-500/20 text-green-300'
                      : 'border border-red-500/30 bg-red-500/20 text-red-300'
                  }`}
                >
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                className="w-full transform rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 px-6 py-3 font-semibold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:from-cyan-600 hover:to-purple-600 hover:shadow-cyan-500/25"
              >
                <span className="flex items-center justify-center space-x-2">
                  <span>
                    {isRegisterMode ? 'Launch Registration' : 'Begin Mission'}
                  </span>
                  <span>🚀</span>
                </span>
              </button>
            </form>

            {/* Toggle Mode */}
            <div className="mt-8 text-center">
              <p className="mb-4 text-cyan-300">
                {isRegisterMode
                  ? 'Already have clearance?'
                  : 'Need to register for the space program?'}
              </p>
              <button
                onClick={toggleMode}
                className="font-medium text-purple-400 underline transition-colors duration-300 hover:text-purple-300"
              >
                {isRegisterMode ? 'Access Mission Control' : 'Join the Fleet'}
              </button>
            </div>

            {/* Features Preview */}
            <div className="mt-8 border-t border-cyan-400/20 pt-6">
              <h3 className="mb-4 text-center font-medium text-cyan-300">
                🌟 Mission Capabilities
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-center">
                  <div className="mb-2 text-2xl">🤖</div>
                  <p className="text-cyan-200">AI Agents</p>
                </div>
                <div className="text-center">
                  <div className="mb-2 text-2xl">🌍</div>
                  <p className="text-cyan-200">Global Search</p>
                </div>
                <div className="text-center">
                  <div className="mb-2 text-2xl">🔮</div>
                  <p className="text-cyan-200">Future Vision</p>
                </div>
                <div className="text-center">
                  <div className="mb-2 text-2xl">🏠</div>
                  <p className="text-cyan-200">Dream Homes</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Demo Access */}
          <div className="mt-6 text-center">
            <button
              onClick={() => (window.location.href = '/')}
              className="text-sm text-cyan-400 transition-colors duration-300 hover:text-cyan-300"
            >
              ← Return to Home Base
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpaceLogin;
