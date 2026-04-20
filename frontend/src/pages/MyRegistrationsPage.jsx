import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function MyRegistrationsPage() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [requestMessage, setRequestMessage] = useState('I can help organize and moderate events.');
  const [requestStatus, setRequestStatus] = useState('');
  const { user, refreshUser } = useAuth();

  const fetchRows = () => {
    api
      .get('/registrations')
      .then((res) => setRows(res.data))
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    fetchRows();
  }, []);

  useEffect(() => {
    if (refreshUser) {
      refreshUser().catch(() => {});
    }
  }, [refreshUser]);

  const requestAdminRole = async () => {
    try {
      const response = await api.post('/auth/request-admin', { reason: requestMessage });
      setNotice('Admin role request submitted successfully.');
      setRequestStatus(response.data.status);
    } catch (err) {
      setError(err.message);
    }
  };

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
      {notice && <p className="notice">{notice}</p>}
      {user?.role !== 'admin' && (
        <section className="card">
          <h2>Request Admin Role</h2>
          <label>
            Message
            <textarea
              rows="4"
              value={requestMessage}
              onChange={(e) => setRequestMessage(e.target.value)}
              placeholder="Why do you want admin access?"
            />
          </label>
          {requestStatus && <p className="notice">Current request status: {requestStatus}</p>}
          <button className="button-secondary" onClick={requestAdminRole}>
            Submit Request
          </button>
        </section>
      )}
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
            <button className="button-secondary" onClick={() => cancelRegistration(row.id)}>
              Cancel
            </button>
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
