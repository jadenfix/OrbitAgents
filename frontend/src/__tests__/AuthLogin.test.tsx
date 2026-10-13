import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuthProvider } from '../contexts/AuthContext'
import Login from '../pages/Login'

jest.mock('../services/auth', () => ({
  tokenStorage: { getToken: () => null, isTokenExpired: () => true },
  authAPI: { login: jest.fn(() => Promise.reject(new Error('Rejected'))), logout: jest.fn() }
}))

test('failed sign-in retains the form and visible error with the real provider', async () => {
  render(<AuthProvider><Login /></AuthProvider>)
  const submit = screen.getByRole('button', { name: 'Sign In' })
  await waitFor(() => expect(submit).not.toBeDisabled())
  fireEvent.change(screen.getByLabelText('Email Address'), { target: { value: 'test@example.com' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'safe-password' } })
  fireEvent.click(submit)
  expect(await screen.findByText('Login failed')).toBeInTheDocument()
  expect(screen.getByLabelText('Email Address')).toHaveValue('test@example.com')
  await waitFor(() => expect(submit).not.toBeDisabled())
})
