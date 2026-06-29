import { useEffect, useState } from 'react';
import { listProviders, createProvider, updateProvider, deleteProvider } from './api';

interface Provider {
  id: string;
  npi: string;
  name: string;
  specialty: string;
  taxonomy: string;
  status: string;
  accepting_new_patients: boolean;
  region?: string;
  state?: string;
}

interface Props {
  token: string;
  isAdmin: boolean;
}

const EMPTY_FORM = {
  npi: '', name: '', taxonomy: '', specialty: '',
  accepting_new_patients: true, region: '', state: '', status: 'active',
};

export default function ProvidersPage({ token, isAdmin }: Props) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  function fetchProviders() {
    listProviders(token, page)
      .then((data) => {
        setProviders(data.data);
        setHasMore(data.pagination.hasMore);
      })
      .catch((err: Error) => setError(err.message));
  }

  useEffect(() => { fetchProviders(); }, [page]);

  function startEdit(p: Provider) {
    setEditingId(p.id);
    setForm({ 
      npi: p.npi, name: p.name, taxonomy: p.taxonomy, specialty: p.specialty, 
      accepting_new_patients: p.accepting_new_patients, 
      region: p.region ?? '', state: p.state ?? '',
      status: p.status,
    });
    setShowForm(true);
  }

  function resetForm() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setShowForm(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId) {
        await updateProvider(token, editingId, {
          ...form,
          region: form.region || undefined,
          state: form.state || undefined,
        });
      } else {
        await createProvider(token, {
          ...form,
          region: form.region || undefined,
          state: form.state || undefined,
        });
      }
      resetForm();
      fetchProviders();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save provider');
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this provider?')) return;
    try {
      await deleteProvider(token, id);
      fetchProviders();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete provider');
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Providers</h2>
        {isAdmin && (
          <button onClick={() => { resetForm(); setShowForm((v) => !v); }}>
            {showForm && !editingId ? 'Cancel' : '+ New Provider'}
          </button>
        )}
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {isAdmin && showForm && (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24, maxWidth: 400 }}>
          <h3>{editingId ? 'Edit Provider' : 'New Provider'}</h3>
          <input placeholder="NPI (10 digits)" value={form.npi} onChange={(e) => setForm({ ...form, npi: e.target.value })} required disabled={!!editingId} />
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input placeholder="Taxonomy" value={form.taxonomy} onChange={(e) => setForm({ ...form, taxonomy: e.target.value })} required />
          <input placeholder="Specialty" value={form.specialty} onChange={(e) => setForm({ ...form, specialty: e.target.value })} required />
          <input placeholder="Region (optional)" value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} />
          <input placeholder="State (optional)" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} />
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <label>
            <input type="checkbox" checked={form.accepting_new_patients} onChange={(e) => setForm({ ...form, accepting_new_patients: e.target.checked })} />
            {' '}Accepting new patients
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="submit">{editingId ? 'Save Changes' : 'Create Provider'}</button>
            <button type="button" onClick={resetForm}>Cancel</button>
          </div>
        </form>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {['Name', 'NPI', 'Specialty', 'Status', 'Accepting', ...(isAdmin ? ['Actions'] : [])].map((h) => (
              <th key={h} style={{ textAlign: 'left', borderBottom: '1px solid #ccc', padding: '8px' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {providers.map((p) => (
            <tr key={p.id}>
              <td style={{ padding: '8px' }}>{p.name}</td>
              <td style={{ padding: '8px' }}>{p.npi}</td>
              <td style={{ padding: '8px' }}>{p.specialty}</td>
              <td style={{ padding: '8px' }}>{p.status}</td>
              <td style={{ padding: '8px' }}>{p.accepting_new_patients ? 'Yes' : 'No'}</td>
              {isAdmin && (
                <td style={{ padding: '8px', display: 'flex', gap: 8 }}>
                  <button onClick={() => startEdit(p)}>Edit</button>
                  <button onClick={() => handleDelete(p.id)} style={{ color: 'red' }}>Delete</button>
                </td>
              )}
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
