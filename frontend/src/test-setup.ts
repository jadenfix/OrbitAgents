import '@testing-library/jest-dom'

// Global test utilities and mocks
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: any) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
})

// Mock localStorage
const localStorageMock = {
  length: 0,
  getItem: jest.fn(() => null),
  setItem: jest.fn(() => {}),
  removeItem: jest.fn(() => {}),
  clear: jest.fn(() => {}),
  key: jest.fn(() => null),
}

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  } as Response)
)

// Mock process.env
process.env.VITE_API_URL = 'http://localhost:3001' 