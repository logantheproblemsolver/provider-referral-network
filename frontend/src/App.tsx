import { useState, useEffect } from 'react';
import LoginPage from './LoginPage';
import CallbackPage from './CallbackPage';
import ProvidersPage from './ProvidersPage';
import ReferralsPage from './ReferralsPage';
import { listAllProviders, getMe } from './api';

type Page = 'login' | 'callback' | 'providers' | 'referrals';

function getInitialPage(): Page {
  if (window.location.pathname === '/callback') return 'callback';
  if (localStorage.getItem('token')) return 'providers';
  return 'login';
}

export default function App() {
  const [page, setPage] = useState<Page>(getInitialPage);
  const [token, setToken] = useState<string>(localStorage.getItem('token') ?? '');
  const [providers, setProviders] = useState<{ id: string; name: string }[]>([]);
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    listAllProviders(token).then(setProviders);
    getMe(token).then((user) => setRole(user.role));
  }, [token]);

  function handleSuccess(newToken: string) {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setPage('providers');
  }

  function handleLogout() {
    localStorage.removeItem('token');
    setToken('');
    setRole(null);
    setPage('login');
  }

  if (page === 'callback') return <CallbackPage onSuccess={handleSuccess} />;
  if (page === 'login') return <LoginPage onSuccess={handleSuccess} />;

  return (
    <div style={{ maxWidth: 1000, margin: '40px auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Provider Referral Network</h1>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          {role && <span style={{ color: '#666' }}>Role: {role}</span>}
          <button onClick={handleLogout}>Logout</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <button onClick={() => setPage('providers')} style={{ fontWeight: page === 'providers' ? 'bold' : 'normal' }}>
          Providers
        </button>
        <button onClick={() => setPage('referrals')} style={{ fontWeight: page === 'referrals' ? 'bold' : 'normal' }}>
          Referrals
        </button>
      </div>

      {page === 'providers' && <ProvidersPage token={token} isAdmin={role === 'admin'} />}
      {page === 'referrals' && <ReferralsPage token={token} providers={providers} />}
    </div>
  );
}
