import { useEffect, useState } from 'react';
import { api } from '../api/client';

function formatFieldValue(value) {
  if (value === null || value === undefined || value === '') {
    return '-';
  }

  return String(value);
}

function humanizeFieldName(fieldName) {
  return fieldName
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getSubmittedFields(row) {
  if (Array.isArray(row.submitted_fields) && row.submitted_fields.length > 0) {
    return row.submitted_fields;
  }

  if (row.field_values && typeof row.field_values === 'object') {
    return Object.entries(row.field_values).map(([field_name, value]) => ({
      field_name,
      label: humanizeFieldName(field_name),
      value,
    }));
  }

  return [];
}

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
            <p className="muted">Registration ID: {row.id}</p>
            <p>
              <strong>Event:</strong> {row.event_title || `Event #${row.event_id}`}
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

            <section>
              <h3>Submitted Details</h3>
              {getSubmittedFields(row).length ? (
                <div className="registration-details">
                  {getSubmittedFields(row).map((field) => (
                    <div className="registration-detail" key={field.field_name}>
                      <span className="registration-detail-label">{field.label}</span>
                      <span className="registration-detail-value">{formatFieldValue(field.value)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No submitted details available.</p>
              )}
            </section>
          </article>
        ))}
      </div>
    </div>
  );
}
