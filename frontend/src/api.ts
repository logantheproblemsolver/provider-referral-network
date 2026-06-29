const API_URL = 'http://localhost:8000';
const KEYCLOAK_BASE = 'http://localhost:8080/realms/referral-network/protocol/openid-connect';
const CLIENT_ID = 'resource-api';
const REDIRECT_URI = 'http://localhost:5173/callback';

function base64urlEncode(array: Uint8Array): string {
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64urlEncode(array);
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const data = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64urlEncode(new Uint8Array(digest));
}

export async function initiateOidcLogin(): Promise<void> {
  const verifier = generateCodeVerifier();
  const challenge = await generateCodeChallenge(verifier);
  const state = base64urlEncode(crypto.getRandomValues(new Uint8Array(16)));

  sessionStorage.setItem('pkce_verifier', verifier);
  sessionStorage.setItem('pkce_state', state);

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    scope: 'openid email profile',
    state,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });

  window.location.href = `${KEYCLOAK_BASE}/auth?${params}`;
}

export async function handleOidcCallback(code: string, state: string): Promise<string> {
  const savedState = sessionStorage.getItem('pkce_state');
  const verifier = sessionStorage.getItem('pkce_verifier');

  if (state !== savedState) throw new Error('State mismatch');
  if (!verifier) throw new Error('Missing PKCE verifier');

  sessionStorage.removeItem('pkce_verifier');
  sessionStorage.removeItem('pkce_state');

  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: REDIRECT_URI,
    client_id: CLIENT_ID,
    code_verifier: verifier,
  });

  const tokenResp = await fetch(`${KEYCLOAK_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params,
  });
  if (!tokenResp.ok) throw new Error('Token exchange failed');
  const { id_token } = await tokenResp.json();

  const oidcResp = await fetch(`${API_URL}/auth/oidc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token }),
  });
  if (!oidcResp.ok) throw new Error('OIDC exchange failed');
  const data = await oidcResp.json();
  return data.access_token;
}

export async function localLogin(email: string, password: string): Promise<string> {
  const resp = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!resp.ok) throw new Error('Login failed');
  const data = await resp.json();
  return data.access_token;
}

export async function listProviders(token: string, page = 1) {
  const resp = await fetch(`${API_URL}/providers?page=${page}&limit=20`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch providers');
  return resp.json();
}

export async function listAllProviders(token: string): Promise<{ id: string; name: string }[]> {
  const resp = await fetch(`${API_URL}/providers?page=1&limit=100`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch providers');
  const data = await resp.json();
  return data.data.map((p: { id: string; name: string }) => ({ id: p.id, name: p.name }));
}

export async function listReferrals(token: string, page = 1) {
  const resp = await fetch(`${API_URL}/referrals?page=${page}&limit=20`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch referrals');
  return resp.json();
}

export async function createReferral(token: string, body: {
  referring_provider_id: string;
  referred_provider_id: string;
  patient_ref: string;
  icd10_code: string;
  notes?: string;
}) {
  const resp = await fetch(`${API_URL}/referrals`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error('Failed to create referral');
  return resp.json();
}

export async function updateReferralStatus(token: string, id: string, status: string) {
  const resp = await fetch(`${API_URL}/referrals/${id}`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!resp.ok) throw new Error('Failed to update referral');
  return resp.json();
}


export async function createProvider(token: string, body: {
  npi: string;
  name: string;
  taxonomy: string;
  specialty: string;
  accepting_new_patients: boolean;
  region?: string;
  state?: string;
}) {
  const resp = await fetch(`${API_URL}/providers`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error('Failed to create provider');
  return resp.json();
}

export async function updateProvider(token: string, id: string, body: {
  name?: string;
  specialty?: string;
  taxonomy?: string;
  accepting_new_patients?: boolean;
  status?: string;
  region?: string;
  state?: string;
}) {
  const resp = await fetch(`${API_URL}/providers/${id}`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error('Failed to update provider');
  return resp.json();
}

export async function deleteProvider(token: string, id: string) {
  const resp = await fetch(`${API_URL}/providers/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to delete provider');
}

export async function getMe(token: string): Promise<{ id: string; email: string; role: string }> {
  const resp = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to fetch user');
  return resp.json();
}