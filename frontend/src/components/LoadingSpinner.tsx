import type { ReactNode } from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
}

export function LoadingSpinner({ size = 'md', fullScreen = false }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4',
  };

  const spinner = (
    <div
      className={`${sizeClasses[size]} border-primary-600 border-t-transparent rounded-full animate-spin`}
    />
  );

  if (fullScreen) {
    const isDark = document.documentElement.classList.contains('dark');
    return (
      <div
        className="fixed inset-0 flex items-center justify-center"
        style={{ backgroundColor: isDark ? '#111827' : '#ffffff' }}
      >
        {spinner}
      </div>
    );
  }

  return spinner;
}

interface LoadingOverlayProps {
  children: ReactNode;
  isLoading: boolean;
}

export function LoadingOverlay({ children, isLoading }: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-white/50 dark:bg-gray-900/50 flex items-center justify-center rounded-lg">
          <LoadingSpinner />
        </div>
      )}
    </div>
  );
}

