import { useEffect, useState } from 'react';
import { handleOidcCallback } from './api';

interface Props {
  onSuccess: (token: string) => void;
}

export default function CallbackPage({ onSuccess }: Props) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    const errorParam = params.get('error');

    if (errorParam) {
      setError(`Keycloak error: ${errorParam}`);
      return;
    }

    if (!code || !state) {
      setError('Missing code or state in callback');
      return;
    }

    handleOidcCallback(code, state)
      .then((token) => {
        window.history.replaceState({}, '', '/');
        onSuccess(token);
      })
      .catch((err: Error) => setError(err.message));
  }, [onSuccess]);

  if (error) return <p>Error: {error}</p>;
  return <p>Completing login...</p>;
}
