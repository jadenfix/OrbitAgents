import { useState, useEffect } from 'react';

const Login = () => {
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

        {/* Floating orbs */}
        {[...Array(15)].map((_, i) => (
          <div
            key={`orb-${i}`}
            className="absolute animate-pulse rounded-full opacity-20"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: `${Math.random() * 80 + 40}px`,
              height: `${Math.random() * 80 + 40}px`,
              background: `radial-gradient(circle, ${['cyan', 'purple', 'pink', 'blue'][Math.floor(Math.random() * 4)]}, transparent)`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${Math.random() * 5 + 3}s`,
            }}
          />
        ))}

        {/* Mouse-following cosmic dust */}
        <div
          className="absolute h-96 w-96 rounded-full bg-gradient-to-r from-cyan-500/20 to-purple-500/20 blur-3xl transition-all duration-1000 ease-out"
          style={{
            left: `${mousePosition.x - 12}%`,
            top: `${mousePosition.y - 12}%`,
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-20 flex items-center justify-between p-6">
        <button
          onClick={() => (window.location.href = '/')}
          className="group flex items-center space-x-3"
        >
          <div className="flex h-12 w-12 animate-pulse items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-purple-400 transition-transform group-hover:scale-110">
            <span className="text-lg font-bold text-white">🌌</span>
          </div>
          <div>
            <h1 className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-2xl font-bold text-transparent">
              OrbitAgents
            </h1>
            <p className="text-xs text-cyan-300">Mission Control</p>
          </div>
        </button>
      </nav>

      {/* Main content */}
      <div className="relative z-10 flex min-h-[calc(100vh-100px)] items-center justify-center px-6">
        <div className="w-full max-w-md">
          {/* Central orbital animation */}
          <div className="relative mx-auto mb-12 h-32 w-32">
            <div
              className="absolute inset-0 animate-spin rounded-full border border-cyan-400/40"
              style={{ animationDuration: '15s' }}
            >
              <div className="absolute left-1/2 top-0 h-3 w-3 -translate-x-1/2 -translate-y-1 transform rounded-full bg-cyan-400"></div>
            </div>
            <div
              className="absolute inset-2 animate-spin rounded-full border border-purple-400/40"
              style={{
                animationDuration: '12s',
                animationDirection: 'reverse',
              }}
            >
              <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 -translate-y-1 transform rounded-full bg-purple-400"></div>
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex h-16 w-16 animate-pulse items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-purple-400">
                <span className="text-2xl text-white">🔐</span>
              </div>
            </div>
          </div>

          {/* Login Panel */}
          <div className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-indigo-800/50 to-purple-800/50 p-8 shadow-2xl shadow-cyan-500/10 backdrop-blur-sm">
            {/* Header */}
            <div className="mb-8 text-center">
              <h2 className="mb-4 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-4xl font-bold text-transparent">
                {isRegisterMode ? 'Join the Fleet' : 'Mission Control'}
              </h2>
              <p className="text-cyan-200">
                {isRegisterMode
                  ? 'Begin your journey through the cosmos of real estate'
                  : 'Access your orbital command center'}
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="rounded-xl border border-red-400/30 bg-gradient-to-r from-red-500/20 to-pink-500/20 p-4 backdrop-blur-sm">
                  <p className="text-sm font-medium text-red-200">{error}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="email"
                    className="mb-2 block text-sm font-medium text-cyan-200"
                  >
                    Communication Channel
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full rounded-xl border border-cyan-400/30 bg-indigo-900/50 px-4 py-3 text-white placeholder-cyan-300/50 backdrop-blur-sm transition-all focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                    placeholder="Enter your email coordinates"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="mb-2 block text-sm font-medium text-cyan-200"
                  >
                    Security Clearance
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full rounded-xl border border-cyan-400/30 bg-indigo-900/50 px-4 py-3 pr-12 text-white placeholder-cyan-300/50 backdrop-blur-sm transition-all focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                      placeholder="Enter your access code"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 transform text-cyan-300 transition-colors hover:text-white"
                    >
                      {showPassword ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="w-full transform rounded-xl bg-gradient-to-r from-cyan-500 to-purple-500 py-4 font-semibold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:from-cyan-600 hover:to-purple-600 hover:shadow-cyan-500/25"
              >
                <span className="flex items-center justify-center space-x-2">
                  <span>
                    {isRegisterMode ? 'Launch Mission' : 'Engage Thrusters'}
                  </span>
                  <span>🚀</span>
                </span>
              </button>
            </form>

            {/* Toggle Mode */}
            <div className="mt-8 text-center">
              <button
                onClick={toggleMode}
                className="text-cyan-300 transition-colors hover:text-white"
              >
                {isRegisterMode ? (
                  <>
                    <span>Already part of the fleet? </span>
                    <span className="font-semibold">Return to Command</span>
                  </>
                ) : (
                  <>
                    <span>New to the cosmos? </span>
                    <span className="font-semibold">Join the Fleet</span>
                  </>
                )}
              </button>
            </div>

            {/* Additional Info */}
            <div className="mt-8 border-t border-cyan-400/20 pt-6">
              <div className="text-center">
                <p className="mb-4 text-sm text-cyan-300">
                  🛰️ Secure orbital communication established
                </p>
                <div className="flex justify-center space-x-4 text-xs text-cyan-400">
                  <span>🔒 Encrypted</span>
                  <span>🌍 Global Access</span>
                  <span>⚡ Instant</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
