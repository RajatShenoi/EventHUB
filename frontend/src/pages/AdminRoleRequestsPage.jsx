import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function AdminRoleRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');

  const loadRequests = () => {
    api
      .get('/admin/role-requests')
      .then((res) => setRequests(res.data))
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const review = async (id, approve) => {
    try {
      await api.post(`/admin/role-requests/${id}/review`, { approve });
      loadRequests();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h1>Admin Role Requests</h1>
      {error && <p className="error">{error}</p>}
      <p className="notice">This page shows pending and previously reviewed requests.</p>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>User</th>
              <th>Name</th>
              <th>Message</th>
              <th>Status</th>
              <th>Submitted</th>
              <th>Reviewed</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.user_email}</td>
                <td>{item.user_full_name}</td>
                <td>{item.reason}</td>
                <td>{item.status}</td>
                <td>{new Date(item.created_at).toLocaleString()}</td>
                <td>{item.reviewed_at ? `${new Date(item.reviewed_at).toLocaleString()} by ${item.reviewed_by || 'unknown'}` : '-'}</td>
                <td>
                  {item.status === 'pending' ? (
                    <div className="stack-horizontal">
                      <button className="button-primary" onClick={() => review(item.id, true)}>
                        Approve
                      </button>
                      <button className="button-danger" onClick={() => review(item.id, false)}>
                        Reject
                      </button>
                    </div>
                  ) : (
                    <span className="muted">Reviewed</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
