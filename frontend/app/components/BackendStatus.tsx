import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

export default function BackendStatus() {
  const [status, setStatus] = useState('checking');
  const [message, setMessage] = useState('Checking server...');
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    checkBackend();
  }, []);

  const checkBackend = async () => {
    const startTime = Date.now();
    let attempts = 0;
    const maxAttempts = 3;

    const tryConnect = async () => {
      attempts++;
      setMessage(`Connecting to server... (Attempt ${attempts}/${maxAttempts})`);

      try {
        const response = await fetch(`${API_BASE_URL}/health`, {
          signal: AbortSignal.timeout(60000)
        });

        const elapsed = Math.round((Date.now() - startTime) / 1000);
        setDuration(elapsed);

        if (response.ok) {
          setStatus('online');
          if (elapsed > 15) {
            setMessage(`Server was sleeping, now awake! (${elapsed}s)`);
            setTimeout(() => setStatus('hidden'), 3000);
          } else {
            setMessage('Server is ready!');
            setTimeout(() => setStatus('hidden'), 2000);
          }
        } else {
          throw new Error('Server responded with error');
        }
      } catch (error) {
        if (attempts < maxAttempts) {
          setMessage(`Server starting up... This can take 30-60 seconds on first use. Retrying...`);
          setTimeout(tryConnect, 10000); // Retry after 10 seconds
        } else {
          setStatus('error');
          setMessage('Cannot connect to server. Please try again later or check if the backend is deployed.');
        }
      }
    };

    tryConnect();
  };

  if (status === 'hidden') return null;

  return (
    <div className={`fixed top-4 right-4 max-w-md p-4 rounded-lg shadow-lg z-50 border-2 ${
      status === 'checking' ? 'bg-yellow-50 border-yellow-400' : 
      status === 'online' ? 'bg-green-50 border-green-400' :
      'bg-red-50 border-red-400'
    }`}>
      <div className="flex items-start gap-3">
        {status === 'checking' && (
          <div className="flex-shrink-0 mt-1">
            <div className="animate-spin h-5 w-5 border-2 border-yellow-600 border-t-transparent rounded-full" />
          </div>
        )}
        {status === 'online' && (
          <div className="flex-shrink-0 mt-1">
            <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
        {status === 'error' && (
          <div className="flex-shrink-0 mt-1">
            <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        )}
        <div className="flex-1">
          <p className="font-semibold text-sm text-gray-900">
            {status === 'checking' ? '🔄 Starting Server' : 
             status === 'online' ? '✅ Server Ready' : 
             '❌ Connection Issue'}
          </p>
          <p className="text-xs text-gray-700 mt-1">{message}</p>
          {status === 'checking' && (
            <p className="text-xs text-gray-500 mt-2">
              ℹ️ Free tier servers sleep after 15 minutes of inactivity. 
              First connection may take 30-60 seconds.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
