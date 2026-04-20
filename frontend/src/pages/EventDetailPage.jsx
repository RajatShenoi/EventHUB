import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

function emptyValues(fields) {
  const result = {};
  fields.forEach((field) => {
    result[field.field_name] = '';
  });
  return result;
}

export default function EventDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [eventData, setEventData] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [registerRes, setRegisterRes] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get(`/events/${id}`)
      .then((res) => {
        setEventData(res.data);
        setFormValues(emptyValues(res.data.fields || []));
      })
      .catch((err) => setError(err.message));
  }, [id]);

  useEffect(() => {
    if (!eventData || eventData.status !== 'completed') {
      return;
    }

    api
      .get(`/results/event/${id}`)
      .then((res) => setResults(res.data))
      .catch(() => {});
  }, [id, eventData]);

  const canRegister = useMemo(() => {
    if (!eventData) return false;
    return eventData.status === 'open' || eventData.status === 'ongoing';
  }, [eventData]);

  const onRegister = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await api.post('/registrations', {
        event_id: Number(id),
        field_values: formValues,
      });
      setRegisterRes(res.data);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!eventData) {
    return <div className="container">Loading event details...</div>;
  }

  return (
    <div className="container">
      <h1>{eventData.title}</h1>
      <p>{eventData.description}</p>
      <p>
        <strong>Location:</strong> {eventData.location}
      </p>
      <p>
        <strong>Status:</strong> {eventData.status}
      </p>

      {user?.role === 'admin' ? (
        <section className="card">
          <h2>Management Mode</h2>
          <p>Admins manage events and check-ins, but cannot register for events.</p>
        </section>
      ) : canRegister && (
        <form className="card" onSubmit={onRegister}>
          <h2>Register for this event</h2>
          {eventData.fields?.map((field) => (
            <label key={field.id}>
              {field.label}
              <input
                required={field.is_required}
                value={formValues[field.field_name] || ''}
                onChange={(e) => setFormValues({ ...formValues, [field.field_name]: e.target.value })}
              />
            </label>
          ))}
          {error && <p className="error">{error}</p>}
          <button className="button-primary" type="submit">
            Register
          </button>
        </form>
      )}

      {registerRes && (
        <section className="card">
          <h2>Registration Successful</h2>
          <p>Use this QR for event check-in:</p>
          <img src={registerRes.qr_image} alt="Check-in QR" className="qr" />
          <details>
            <summary>Show QR token</summary>
            <code className="code">{registerRes.qr_token}</code>
          </details>
        </section>
      )}

      {eventData.status === 'completed' && results && (
        <section className="card">
          <h2>Event Results</h2>
          <p>
            Attendance: {results.attendance.checked_in}/{results.attendance.total_registered} checked in
          </p>
          <table className="table">
            <thead>
              <tr>
                <th>User</th>
                <th>Score</th>
                <th>Rank</th>
                <th>Remarks</th>
              </tr>
            </thead>
            <tbody>
              {results.ranking.map((item) => (
                <tr key={`${item.user_id}-${item.rank}`}>
                  <td>{item.user_id}</td>
                  <td>{item.score}</td>
                  <td>{item.rank}</td>
                  <td>{item.remarks || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
