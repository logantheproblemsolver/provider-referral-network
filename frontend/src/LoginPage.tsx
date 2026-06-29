import { useState } from 'react';
import { localLogin, initiateOidcLogin } from './api';

interface Props {
  onSuccess: (token: string) => void;
}

export default function LoginPage({ onSuccess }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLocalLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const token = await localLogin(email, password);
      onSuccess(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', fontFamily: 'sans-serif' }}>
      <h1>Provider Referral Network</h1>

      <form onSubmit={handleLocalLogin} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <h2>Local Login</h2>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>

      <hr style={{ margin: '24px 0' }} />

      <div>
        <h2>Login with Keycloak</h2>
        <button onClick={initiateOidcLogin}>Continue with Keycloak</button>
      </div>
    </div>
  );
}
