import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function MyRegistrationsPage() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');

  const fetchRows = () => {
    api
      .get('/registrations')
      .then((res) => setRows(res.data))
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    fetchRows();
  }, []);

  const cancelRegistration = async (id) => {
    try {
      await api.del(`/registrations/${id}`);
      fetchRows();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h1>My Registrations</h1>
      {error && <p className="error">{error}</p>}
      <div className="grid">
        {rows.map((row) => (
          <article className="card" key={row.id}>
            <p>
              <strong>Registration ID:</strong> {row.id}
            </p>
            <p>
              <strong>Event ID:</strong> {row.event_id}
            </p>
            <p>
              <strong>Status:</strong> {row.status}
            </p>
            {row.status === 'checked_in' ? (
              <p className="notice">Checked-in registrations cannot be cancelled.</p>
            ) : (
              <button className="button-secondary" onClick={() => cancelRegistration(row.id)}>
                Cancel
              </button>
            )}
            <details>
              <summary>Show Submitted Details</summary>
              <pre className="code">{JSON.stringify(row.field_values, null, 2)}</pre>
            </details>
          </article>
        ))}
      </div>
    </div>
  );
}
