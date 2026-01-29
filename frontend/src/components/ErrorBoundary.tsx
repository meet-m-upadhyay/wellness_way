import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console or error reporting service
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-wellness-light-bg dark:bg-wellness-dark-bg py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="text-6xl mb-4">😵</div>
              <h2 className="mt-6 text-3xl font-extrabold text-wellness-light-text dark:text-wellness-dark-text">
                Oops! Something went wrong
              </h2>
              <p className="mt-2 text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                We're sorry, but something unexpected happened. Please try again.
              </p>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary hover:text-wellness-light-text dark:hover:text-wellness-dark-text">
                    Error Details (Development)
                  </summary>
                  <div className="mt-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                    <pre className="text-xs text-red-800 dark:text-red-200 whitespace-pre-wrap">
                      {this.state.error.toString()}
                      {this.state.errorInfo?.componentStack}
                    </pre>
                  </div>
                </details>
              )}
              
              <div className="mt-6 space-y-3">
                <button
                  onClick={this.handleRetry}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                >
                  Try Again
                </button>
                
                <button
                  onClick={() => window.location.href = '/'}
                  className="w-full flex justify-center py-2 px-4 border border-wellness-light-border dark:border-wellness-dark-border rounded-md shadow-sm text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary bg-wellness-light-card dark:bg-wellness-dark-card hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                >
                  Go to Home
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;