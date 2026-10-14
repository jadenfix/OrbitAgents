import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  centered?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  text = 'Loading...',
  centered = true,
}) => {
  const sizeClasses = {
    sm: 'h-5 w-5',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const content = (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative">
        <div
          className={`animate-spin rounded-full border-4 border-blue-100 ${sizeClasses[size]}`}
        >
          <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-blue-600"></div>
        </div>
        <div
          className={`animate-reverse absolute inset-0 animate-spin rounded-full border-4 border-transparent border-r-indigo-500 ${sizeClasses[size]}`}
        ></div>
      </div>
      {text && (
        <p
          className={`font-medium text-gray-600 ${textSizeClasses[size]} animate-pulse`}
        >
          {text}
        </p>
      )}
    </div>
  );

  if (centered) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <div className="rounded-2xl border border-white/20 bg-white/80 p-8 shadow-xl backdrop-blur-xl">
          {content}
        </div>
      </div>
    );
  }

  return content;
};

export default LoadingSpinner;
