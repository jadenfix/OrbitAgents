import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Login from '../pages/Login'

const mockLogin = jest.fn()
const mockRegister = jest.fn()
jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ login: mockLogin, register: mockRegister, isLoading: false })
}))

beforeEach(() => jest.clearAllMocks())

test('submits credentials to the auth provider', async () => {
  mockLogin.mockResolvedValue(undefined)
  render(<Login />)
  fireEvent.change(screen.getByLabelText('Email Address'), { target: { value: 'test@example.com' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'safe-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Sign In' }))
  await waitFor(() => expect(mockLogin).toHaveBeenCalledWith({ email: 'test@example.com', password: 'safe-password' }))
  expect(mockRegister).not.toHaveBeenCalled()
})

test('surfaces provider rejection instead of claiming success', async () => {
  mockLogin.mockRejectedValue({ detail: 'Invalid credentials' })
  render(<Login />)
  fireEvent.change(screen.getByLabelText('Email Address'), { target: { value: 'test@example.com' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'safe-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Sign In' }))
  expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
})
