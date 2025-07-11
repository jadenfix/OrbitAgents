import React from 'react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  centered?: boolean
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  text = 'Loading...', 
  centered = true 
}) => {
  const sizeClasses = {
    sm: 'h-5 w-5',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  }

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  }

  const content = (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative">
        <div className={`animate-spin rounded-full border-4 border-blue-100 ${sizeClasses[size]}`}>
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-600 animate-spin"></div>
        </div>
        <div className={`absolute inset-0 rounded-full border-4 border-transparent border-r-indigo-500 animate-spin animate-reverse ${sizeClasses[size]}`}></div>
      </div>
      {text && (
        <p className={`text-gray-600 font-medium ${textSizeClasses[size]} animate-pulse`}>
          {text}
        </p>
      )}
    </div>
  )

  if (centered) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-8">
          {content}
        </div>
      </div>
    )
  }

  return content
}

export default LoadingSpinner 