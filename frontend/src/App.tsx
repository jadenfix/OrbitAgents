import {
  useState,
  useEffect,
  Suspense,
  lazy,
  Component,
  ReactNode,
  ErrorInfo,
} from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthProvider';
import { useAuth } from '@/contexts/AuthContext';

// Reusable Section component for consistent spacing
const Section = ({
  children,
  className = '',
  id = '',
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) => (
  <section
    id={id}
    className={`container mx-auto max-w-7xl space-y-8 px-4 py-16 ${className}`}
  >
    {children}
  </section>
);

// Space-themed Error Boundary
class AppErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('App Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <SpaceFallback />;
    }
    return this.props.children;
  }
}

// Beautiful space-themed fallback
const SpaceFallback = () => (
  <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-indigo-900 via-purple-900 to-black">
    {/* Animated stars */}
    <div className="absolute inset-0">
      {[...Array(100)].map((_, i) => (
        <div
          key={i}
          className="absolute animate-pulse rounded-full bg-white"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            width: `${Math.random() * 3 + 1}px`,
            height: `${Math.random() * 3 + 1}px`,
            animationDelay: `${Math.random() * 3}s`,
            animationDuration: `${Math.random() * 3 + 2}s`,
          }}
        />
      ))}
    </div>

    <div className="relative z-10 flex min-h-screen items-center justify-center p-8">
      <div className="text-center">
        <div className="mx-auto mb-8 h-24 w-24 animate-spin rounded-full bg-gradient-to-r from-cyan-400 to-purple-400"></div>
        <h1 className="mb-4 text-4xl font-bold text-white">OrbitAgents</h1>
        <p className="mb-8 text-cyan-200">
          Navigating you to your perfect home...
        </p>
        <button
          onClick={() => window.location.reload()}
          className="transform rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 px-8 py-3 text-white transition-all duration-300 hover:scale-105 hover:from-cyan-600 hover:to-purple-600"
        >
          Re-enter Orbit
        </button>
      </div>
    </div>
  </div>
);

// Loading component with space theme
const SpaceLoading = () => (
  <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-900 via-purple-900 to-black">
    {/* Floating particles */}
    <div className="absolute inset-0">
      {[...Array(50)].map((_, i) => (
        <div
          key={i}
          className="absolute animate-bounce rounded-full bg-cyan-400 opacity-30"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            width: `${Math.random() * 4 + 2}px`,
            height: `${Math.random() * 4 + 2}px`,
            animationDelay: `${Math.random() * 2}s`,
          }}
        />
      ))}
    </div>

    <div className="relative z-10 text-center">
      <div className="mx-auto mb-8 h-32 w-32 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent"></div>
      <h2 className="text-2xl font-light tracking-wide text-white">
        Preparing your journey through space...
      </h2>
      <p className="mt-4 text-cyan-300">Finding homes across the universe</p>
    </div>
  </div>
);

// Lazy load components with space-themed fallbacks
const Login = lazy(() =>
  import('@/pages/Login').catch((error) => {
    console.warn('Login page failed to load:', error);
    return { default: SpaceFallback };
  })
);

const SplitPaneLayout = lazy(() =>
  import('@/components/Layout/SplitPaneLayout').catch((error) => {
    console.warn('SplitPaneLayout failed to load:', error);
    return { default: SpaceFallback };
  })
);

// Main space-themed landing page
const SpaceLandingPage = () => {
  const [mounted, setMounted] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setMounted(true);

    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  if (!mounted) return <SpaceLoading />;

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-indigo-900 via-purple-900 to-black">
      {/* Animated cosmic background */}
      <div className="absolute inset-0">
        {/* Stars */}
        {[...Array(200)].map((_, i) => (
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
        {[...Array(20)].map((_, i) => (
          <div
            key={`orb-${i}`}
            className="absolute animate-pulse rounded-full opacity-20"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: `${Math.random() * 100 + 50}px`,
              height: `${Math.random() * 100 + 50}px`,
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

      {/* Header Navigation */}
      <header className="relative z-20">
        <nav className="flex items-center justify-between p-6">
          <div className="flex items-center space-x-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-purple-400">
              <span className="text-lg font-bold text-white">O</span>
            </div>
            <div>
              <h1 className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-2xl font-bold text-transparent">
                OrbitAgents
              </h1>
              <p className="text-xs text-cyan-300">Housing Navigator</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={() => (window.location.href = '/login')}
              className="px-4 py-2 text-cyan-300 transition-colors duration-300 hover:text-white"
            >
              Sign In
            </button>
            <button
              onClick={() => (window.location.href = '/dashboard')}
              className="transform rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 px-6 py-2 text-white shadow-lg transition-all duration-300 hover:scale-105 hover:from-cyan-600 hover:to-purple-600"
            >
              Get Started
            </button>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="relative z-10">
        {/* Hero Section */}
        <Section className="flex min-h-[calc(100vh-200px)] flex-col items-center justify-center text-center">
          {/* Main orbit animation */}
          <div className="relative mx-auto mb-16 h-80 w-80">
            <div
              className="absolute inset-0 animate-spin rounded-full border border-cyan-400/30"
              style={{ animationDuration: '20s' }}
            >
              <div className="absolute left-1/2 top-0 h-3 w-3 -translate-x-1/2 -translate-y-2 transform rounded-full bg-cyan-400"></div>
            </div>
            <div
              className="absolute inset-4 animate-spin rounded-full border border-purple-400/30"
              style={{
                animationDuration: '15s',
                animationDirection: 'reverse',
              }}
            >
              <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 -translate-y-1 transform rounded-full bg-purple-400"></div>
            </div>
            <div
              className="absolute inset-8 animate-spin rounded-full border border-pink-400/30"
              style={{ animationDuration: '10s' }}
            >
              <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 transform rounded-full bg-pink-400"></div>
            </div>

            {/* Center icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-purple-400">
                <div className="h-8 w-8 rounded-sm bg-white"></div>
              </div>
            </div>
          </div>

          {/* Hero Typography */}
          <div className="mb-12 space-y-6">
            <div className="space-y-4">
              <h1 className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-5xl font-bold leading-tight tracking-tight text-transparent md:text-7xl">
                Finding Housing
              </h1>
              <h2 className="text-4xl font-semibold leading-snug text-white md:text-6xl">
                Doesn't Have to Feel Like
              </h2>
              <h3 className="bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-3xl font-bold leading-snug text-transparent md:text-5xl">
                Another Planet
              </h3>
            </div>

            <div className="mx-auto max-w-4xl">
              <article className="prose prose-invert mx-auto lg:prose-xl">
                <p className="text-xl font-light leading-relaxed text-cyan-200 md:text-2xl">
                  Navigate the universe of real estate with AI-powered agents
                  that search, analyze, and discover your perfect home across
                  infinite possibilities.
                </p>
              </article>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="mb-24 flex flex-col items-center justify-center gap-8 sm:flex-row">
            <button
              onClick={() => (window.location.href = '/dashboard')}
              className="min-w-[200px] transform rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 px-10 py-4 text-lg font-semibold text-white shadow-xl transition-all duration-300 hover:scale-105 hover:from-cyan-600 hover:to-purple-600 hover:shadow-cyan-500/30"
            >
              Begin Your Journey
            </button>

            <button
              onClick={async () => {
                try {
                  const response = await fetch('/api/demo');
                  const data = await response.json();
                  alert(`Demo Results: ${JSON.stringify(data, null, 2)}`);
                } catch (error) {
                  alert(
                    'Backend offline. Please ensure API is running on port 8080.'
                  );
                }
              }}
              className="min-w-[200px] transform rounded-full border-2 border-cyan-400 bg-transparent px-10 py-4 text-lg font-semibold text-cyan-300 transition-all duration-300 hover:scale-105 hover:bg-cyan-400/10 hover:text-white"
            >
              View Demo
            </button>
          </div>
        </Section>

        {/* Features Section */}
        <Section className="bg-black/20 py-24">
          <div className="mb-16 text-center">
            <h2 className="mb-6 text-3xl font-bold text-white md:text-4xl">
              Platform Features
            </h2>
            <div className="mx-auto max-w-3xl">
              <article className="prose prose-invert mx-auto lg:prose-xl">
                <p className="text-lg text-cyan-200">
                  Discover how our AI-powered platform revolutionizes property
                  search with advanced algorithms and intelligent automation.
                </p>
              </article>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-12 px-4 md:grid-cols-3">
            {[
              {
                title: 'AI Agents',
                description:
                  'Intelligent agents explore the real estate universe, discovering properties across multiple data sources with advanced algorithms and machine learning capabilities.',
              },
              {
                title: 'Smart Search',
                description:
                  'Search across all available properties with advanced filters, location intelligence, personalized recommendations, and real-time market insights.',
              },
              {
                title: 'Market Analysis',
                description:
                  'Predict market trends and property values using sophisticated machine learning algorithms and comprehensive historical market data analysis.',
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-indigo-800/30 to-purple-800/30 p-8 backdrop-blur-sm transition-all duration-300 hover:border-cyan-400/40 hover:shadow-xl hover:shadow-cyan-500/10"
              >
                <h3 className="mb-6 text-xl font-bold text-white">
                  {feature.title}
                </h3>
                <article className="prose prose-sm prose-invert">
                  <p className="leading-relaxed text-cyan-200">
                    {feature.description}
                  </p>
                </article>
              </div>
            ))}
          </div>
        </Section>

        {/* System Status Section */}
        <Section className="py-24">
          <div className="mx-auto max-w-4xl rounded-2xl border border-cyan-400/20 bg-gradient-to-r from-indigo-900/30 to-purple-900/30 p-12 backdrop-blur-sm">
            <div className="mb-12 text-center">
              <h3 className="mb-6 text-2xl font-bold text-white">
                System Status
              </h3>
              <article className="prose prose-invert mx-auto">
                <p className="text-cyan-200">
                  Test platform connectivity and verify that all agent systems
                  are operational and ready for deployment.
                </p>
              </article>
            </div>

            <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2">
              <button
                onClick={async () => {
                  try {
                    const response = await fetch('/api/health');
                    const data = await response.json();
                    alert(`System Status: ${JSON.stringify(data, null, 2)}`);
                  } catch (error) {
                    alert('Backend offline. Check API at port 8080.');
                  }
                }}
                className="transform rounded-xl bg-gradient-to-r from-green-500/80 to-cyan-500/80 px-8 py-4 font-medium text-white transition-all duration-300 hover:scale-105 hover:from-green-600/90 hover:to-cyan-600/90"
              >
                Health Check
              </button>

              <button
                onClick={async () => {
                  try {
                    const response = await fetch('/api/demo');
                    const data = await response.json();
                    alert(`Demo Results: ${JSON.stringify(data, null, 2)}`);
                  } catch (error) {
                    alert('Demo unavailable. Ensure backend is running.');
                  }
                }}
                className="transform rounded-xl bg-gradient-to-r from-purple-500/80 to-pink-500/80 px-8 py-4 font-medium text-white transition-all duration-300 hover:scale-105 hover:from-purple-600/90 hover:to-pink-600/90"
              >
                Test Demo
              </button>
            </div>

            <div className="text-center">
              <p className="text-sm text-cyan-300">
                Backend API:{' '}
                <code className="rounded bg-indigo-800 px-2 py-1 text-xs">
                  http://localhost:8080
                </code>
              </p>
            </div>
          </div>
        </Section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-8">
        <div className="container mx-auto max-w-7xl px-4">
          <div className="flex items-center justify-center space-x-4 text-cyan-300">
            <div className="h-3 w-3 animate-pulse rounded-full bg-green-400"></div>
            <span className="text-sm">
              Platform online and ready for exploration
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Protected Route component
const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const auth = useAuth();

  if (auth.isLoading) {
    return <SpaceLoading />;
  }

  return auth.isAuthenticated ? (
    <>{children}</>
  ) : (
    <Navigate to="/login" replace />
  );
};

// Main App Routes
const AppRoutes = () => {
  const auth = useAuth();

  if (auth.isLoading) {
    return <SpaceLoading />;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          auth.isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Login />
          )
        }
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
  );
};

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
  );
};

export default App;
