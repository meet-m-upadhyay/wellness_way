import React, { useEffect, useState } from 'react';

interface GoogleLoginProps {
  onSuccess: (credential: string) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

declare global {
  interface Window {
    google: any;
  }
}

const GoogleLogin: React.FC<GoogleLoginProps> = ({ onSuccess, onError, disabled = false }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isScriptLoaded, setIsScriptLoaded] = useState(false);

  useEffect(() => {
    // Load Google Identity Services script
    const loadGoogleScript = () => {
      if (window.google) {
        setIsScriptLoaded(true);
        setIsLoading(false);
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        setIsScriptLoaded(true);
        setIsLoading(false);
      };
      script.onerror = () => {
        onError('Failed to load Google Sign-In script');
        setIsLoading(false);
      };
      document.head.appendChild(script);
    };

    loadGoogleScript();
  }, [onError]);

  useEffect(() => {
    if (isScriptLoaded && window.google) {
      const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;

      if (!clientId) {
        onError('Google Client ID not configured');
        return;
      }

      // Initialize Google Identity Services
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response: any) => {
          if (response.credential) {
            onSuccess(response.credential);
          } else {
            onError('No credential received from Google');
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      // Render the sign-in button
      const buttonElement = document.getElementById('google-signin-button');
      if (buttonElement) {
        // Clear any existing content
        buttonElement.innerHTML = '';

        window.google.accounts.id.renderButton(
          buttonElement,
          {
            theme: 'outline',
            size: 'large',
            text: 'signin_with',
            shape: 'rectangular',
            logo_alignment: 'left',
            width: '100%',
          }
        );
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isScriptLoaded]); // Intentionally excluding onSuccess and onError to prevent infinite loop

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-wellness-light-border dark:border-wellness-dark-border border-t-primary-500 dark:border-t-primary-400"></div>
        <span className="ml-2 text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">Loading Google Sign-In...</span>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div
        id="google-signin-button"
        className={`w-full ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      ></div>
      {!process.env.REACT_APP_GOOGLE_CLIENT_ID && (
        <div className="mt-2 p-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-200/60 dark:border-amber-800/30 rounded-xl text-sm text-amber-700 dark:text-amber-300">
          Google Client ID not configured. Please set REACT_APP_GOOGLE_CLIENT_ID in your environment.
        </div>
      )}
    </div>
  );
};

export default GoogleLogin;