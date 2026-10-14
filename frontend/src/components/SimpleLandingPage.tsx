import { useState, useEffect } from 'react';

const SimpleLandingPage = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogin = () => {
    // Simple login simulation
    alert(
      'Login functionality will be available once all components load properly!'
    );
  };

  const handleDemo = async () => {
    try {
      const response = await fetch('/api/demo');
      const data = await response.json();
      alert(`Demo Response: ${JSON.stringify(data, null, 2)}`);
    } catch (error) {
      alert(
        'Demo endpoint not available. Please ensure the backend is running on port 8080.'
      );
    }
  };

  const handleHealth = async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();
      alert(`Health Check: ${JSON.stringify(data, null, 2)}`);
    } catch (error) {
      alert(
        'Health endpoint not available. Please ensure the backend is running on port 8080.'
      );
    }
  };

  if (!mounted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center">
              <div className="mr-3 h-8 w-8 rounded-lg bg-blue-600"></div>
              <h1 className="text-xl font-bold text-gray-900">OrbitAgents</h1>
            </div>
            <button
              onClick={handleLogin}
              className="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
            >
              Login
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
            <span className="block">Intelligent Real Estate</span>
            <span className="block text-blue-600">Automation Platform</span>
          </h1>
          <p className="mx-auto mt-3 max-w-md text-base text-gray-500 sm:text-lg md:mt-5 md:max-w-3xl md:text-xl">
            Deploy AI-powered browser agents that automatically search, analyze,
            and extract real estate data from multiple platforms. Scale your
            lead generation with intelligent automation.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-xl bg-white p-6 shadow-lg">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
              <svg
                className="h-6 w-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              Browser Automation
            </h3>
            <p className="text-gray-600">
              Intelligent browser agents that can navigate and interact with any
              real estate platform automatically.
            </p>
          </div>

          <div className="rounded-xl bg-white p-6 shadow-lg">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-green-100">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              AI-Powered Analysis
            </h3>
            <p className="text-gray-600">
              Advanced AI models analyze property data, market trends, and
              generate actionable insights.
            </p>
          </div>

          <div className="rounded-xl bg-white p-6 shadow-lg">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100">
              <svg
                className="h-6 w-6 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              Real-time Monitoring
            </h3>
            <p className="text-gray-600">
              Comprehensive monitoring and observability for all your automation
              workflows.
            </p>
          </div>
        </div>

        {/* API Test Buttons */}
        <div className="mt-16 rounded-xl bg-white p-8 shadow-lg">
          <h3 className="mb-6 text-lg font-semibold text-gray-900">
            Test Backend Connection
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <button
              onClick={handleHealth}
              className="rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700"
            >
              Health Check
            </button>
            <button
              onClick={handleDemo}
              className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700"
            >
              Demo Endpoint
            </button>
          </div>
          <p className="mt-4 text-sm text-gray-500">
            Backend should be running on{' '}
            <code className="rounded bg-gray-100 px-2 py-1">
              http://localhost:8080
            </code>
          </p>
        </div>

        {/* Status Info */}
        <div className="mt-8 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-yellow-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Fallback Mode Active
              </h3>
              <p className="mt-1 text-sm text-yellow-700">
                This is a simplified version of the OrbitAgents platform. The
                full application with all features will load once all components
                are properly configured.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default SimpleLandingPage;
