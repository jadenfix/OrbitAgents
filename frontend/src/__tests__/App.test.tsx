import React from 'react'
import { render, screen } from '@testing-library/react'
import App from '../App'

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Mock AuthContext
jest.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => ({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    refreshAuth: jest.fn(),
  }),
}))

// Mock components
jest.mock('../pages/Login', () => {
  return function MockLogin() {
    return <div data-testid="login-page">Login Page</div>
  }
})

jest.mock('../components/Layout/SplitPaneLayout', () => {
  return function MockSplitPaneLayout() {
    return <div data-testid="split-pane-layout">Split Pane Layout</div>
  }
})

jest.mock('../components/LoadingSpinner', () => {
  return function MockLoadingSpinner() {
    return <div data-testid="loading-spinner">Loading...</div>
  }
})

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
  })

  it('shows login page when not authenticated', () => {
    render(<App />)
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
  })
}) 