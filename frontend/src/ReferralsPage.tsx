import { useEffect, useState } from 'react';
import { listReferrals, createReferral, updateReferralStatus } from './api';

interface Referral {
  id: string;
  referring_provider_id: string;
  referred_provider_id: string;
  patient_ref: string;
  icd10_code: string;
  status: string;
  notes?: string;
}

interface Props {
  token: string;
  providers: { id: string; name: string }[];
}

const STATUSES = ['pending', 'accepted', 'rejected'];

export default function ReferralsPage({ token, providers }: Props) {
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    referring_provider_id: '',
    referred_provider_id: '',
    patient_ref: '',
    icd10_code: '',
    notes: '',
  });

  function providerName(id: string) {
    return providers.find((p) => p.id === id)?.name ?? id;
  }

  function fetchReferrals() {
    listReferrals(token, page)
      .then((data) => {
        setReferrals(data.data);
        setHasMore(data.pagination.hasMore);
      })
      .catch((err: Error) => setError(err.message));
  }

  useEffect(() => { fetchReferrals(); }, [page]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createReferral(token, {
        ...form,
        notes: form.notes || undefined,
      });
      setForm({ referring_provider_id: '', referred_provider_id: '', patient_ref: '', icd10_code: '', notes: '' });
      setShowForm(false);
      fetchReferrals();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create referral');
    }
  }

  async function handleStatusChange(id: string, status: string) {
    try {
      await updateReferralStatus(token, id, status);
      fetchReferrals();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Referrals</h2>
        <button onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : '+ New Referral'}
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {showForm && (
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24, maxWidth: 400 }}>
          <select value={form.referring_provider_id} onChange={(e) => setForm({ ...form, referring_provider_id: e.target.value })} required>
            <option value="">Referring Provider</option>
            {providers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select value={form.referred_provider_id} onChange={(e) => setForm({ ...form, referred_provider_id: e.target.value })} required>
            <option value="">Referred Provider</option>
            {providers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <input placeholder="Patient Ref (e.g. PAT-001)" value={form.patient_ref} onChange={(e) => setForm({ ...form, patient_ref: e.target.value })} required />
          <input placeholder="ICD-10 Code (e.g. Z00.00)" value={form.icd10_code} onChange={(e) => setForm({ ...form, icd10_code: e.target.value })} required />
          <input placeholder="Notes (optional)" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <button type="submit">Create Referral</button>
        </form>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {['Referring Provider', 'Referred Provider', 'Patient Ref', 'ICD-10', 'Status', 'Update Status'].map((h) => (
              <th key={h} style={{ textAlign: 'left', borderBottom: '1px solid #ccc', padding: '8px' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {referrals.map((r) => (
            <tr key={r.id}>
              <td style={{ padding: '8px' }}>{providerName(r.referring_provider_id)}</td>
              <td style={{ padding: '8px' }}>{providerName(r.referred_provider_id)}</td>
              <td style={{ padding: '8px' }}>{r.patient_ref}</td>
              <td style={{ padding: '8px' }}>{r.icd10_code}</td>
              <td style={{ padding: '8px' }}>{r.status}</td>
              <td style={{ padding: '8px' }}>
                <select value={r.status} onChange={(e) => handleStatusChange(r.id, e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        <button onClick={() => setPage((p) => p - 1)} disabled={page === 1}>Previous</button>
        <span>Page {page}</span>
        <button onClick={() => setPage((p) => p + 1)} disabled={!hasMore}>Next</button>
      </div>
    </div>
  );
}
