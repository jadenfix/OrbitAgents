import React from 'react'
import { render, screen } from '@testing-library/react'
import App from '../App'

const mockAuthState = { isAuthenticated: false }

// Mock AuthContext
jest.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => ({
    user: null,
    token: null,
    isAuthenticated: mockAuthState.isAuthenticated,
    isLoading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    refreshAuth: jest.fn(),
  }),
}))

// Mock components
jest.mock('../pages/Login', () => ({
  __esModule: true,
  default: () => <div data-testid="login-page">Login Page</div>,
}))

jest.mock('../components/Layout/SplitPaneLayout', () => ({
  __esModule: true,
  default: () => <div data-testid="split-pane-layout">Split Pane Layout</div>,
}))

jest.mock('../components/LoadingSpinner', () => {
  return function MockLoadingSpinner() {
    return <div data-testid="loading-spinner">Loading...</div>
  }
})

describe('App', () => {
  beforeEach(() => { mockAuthState.isAuthenticated = false })
  it('renders without crashing', () => {
    window.history.replaceState({}, '', '/')
    render(<App />)
    expect(screen.getByText('OrbitAgents')).toBeInTheDocument()
  })

  it('shows login page when not authenticated', async () => {
    window.history.replaceState({}, '', '/login')
    render(<App />)
    expect(await screen.findByTestId('login-page')).toBeInTheDocument()
  })
  it('redirects an unauthenticated dashboard visit to login', async () => {
    window.history.replaceState({}, '', '/dashboard')
    render(<App />)
    expect(await screen.findByTestId('login-page')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })

  it('opens dashboard for an authenticated session', async () => {
    mockAuthState.isAuthenticated = true
    window.history.replaceState({}, '', '/dashboard')
    render(<App />)
    expect(await screen.findByTestId('split-pane-layout')).toBeInTheDocument()
  })
})
