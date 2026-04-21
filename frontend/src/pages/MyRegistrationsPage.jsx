import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function MyRegistrationsPage() {
  const [rows, setRows] = useState([]);
  const [eventNames, setEventNames] = useState({});
  const [error, setError] = useState('');

  const fetchRows = async () => {
    try {
      const res = await api.get('/registrations');
      setRows(res.data);

      // Fetch event names for all registrations
      const eventIds = [...new Set(res.data.map((r) => r.event_id))];
      const names = {};
      for (const eventId of eventIds) {
        try {
          const eventRes = await api.get(`/events/${eventId}`);
          names[eventId] = eventRes.data.title;
        } catch (err) {
          names[eventId] = `Event ${eventId}`;
        }
      }
      setEventNames(names);
    } catch (err) {
      setError(err.message);
    }
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

  const renderFieldValue = (value) => {
    if (typeof value === 'string') {
      return value;
    }
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="container">
      <h1>My Registrations</h1>
      {error && <p className="error">{error}</p>}
      <div className="grid">
        {rows.map((row) => (
          <article className="card" key={row.id}>
            <h3>{eventNames[row.event_id] || `Event ${row.event_id}`}</h3>
            <p>
              <strong>Registration ID:</strong> {row.id}
            </p>
            <p>
              <strong>Status:</strong> <span className={`status-${row.status}`}>{row.status}</span>
            </p>
            {row.status === 'checked_in' ? (
              <p className="notice">Checked-in registrations cannot be cancelled.</p>
            ) : (
              <button className="button-secondary" onClick={() => cancelRegistration(row.id)}>
                Cancel
              </button>
            )}
            {row.field_values && Object.keys(row.field_values).length > 0 && (
              <details>
                <summary>Submitted Details</summary>
                <dl className="field-list">
                  {Object.entries(row.field_values).map(([fieldName, fieldValue]) => (
                    <div key={fieldName} className="field-item">
                      <dt>{fieldName}</dt>
                      <dd>{renderFieldValue(fieldValue)}</dd>
                    </div>
                  ))}
                </dl>
              </details>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
