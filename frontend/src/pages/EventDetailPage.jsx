import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

function emptyValues(fields) {
  const result = {};
  fields.forEach((field) => {
    result[field.field_name] = '';
  });
  return result;
}

function renderDynamicField(field, value, onChange) {
  if (field.field_type === 'textarea') {
    return <textarea required={field.is_required} value={value} onChange={(e) => onChange(e.target.value)} />;
  }

  if (field.field_type === 'select') {
    return (
      <select required={field.is_required} value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Select an option</option>
        {(field.options || []).map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }

  if (field.field_type === 'radio') {
    return (
      <div>
        {(field.options || []).map((option) => (
          <label key={option} className="radio-label">
            <input
              type="radio"
              name={`radio-${field.field_name}`}
              checked={value === option}
              onChange={() => onChange(option)}
            />
            {option}
          </label>
        ))}
      </div>
    );
  }

  const inputType = field.field_type === 'phone' ? 'tel' : field.field_type;
  return <input type={inputType} required={field.is_required} value={value} onChange={(e) => onChange(e.target.value)} />;
}

function renderRegistrationEditField(field, value, onChange, inputName) {
  if (field.field_type === 'textarea') {
    return <textarea required={field.is_required} value={value} onChange={(e) => onChange(e.target.value)} />;
  }

  if (field.field_type === 'select') {
    return (
      <select required={field.is_required} value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Select an option</option>
        {(field.options || []).map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }

  if (field.field_type === 'radio') {
    return (
      <div>
        {(field.options || []).map((option) => (
          <label key={option} className="radio-label">
            <input type="radio" name={inputName} checked={value === option} onChange={() => onChange(option)} />
            {option}
          </label>
        ))}
      </div>
    );
  }

  const inputType = field.field_type === 'phone' ? 'tel' : field.field_type;
  return <input type={inputType} required={field.is_required} value={value} onChange={(e) => onChange(e.target.value)} />;
}

export default function EventDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const scannerRef = useRef(null);
  const scanLockRef = useRef(false);
  const [eventData, setEventData] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [registerRes, setRegisterRes] = useState(null);
  const [existingRegistration, setExistingRegistration] = useState(null);
  const [results, setResults] = useState(null);
  const [registrationsData, setRegistrationsData] = useState({ fields: [], registrations: [] });
  const [participantsData, setParticipantsData] = useState({ fields: [], participants: [] });
  const [checkinHistory, setCheckinHistory] = useState([]);
  const [manualToken, setManualToken] = useState('');
  const [scanMessage, setScanMessage] = useState('');
  const [scanPopup, setScanPopup] = useState(null);
  const [scannerKey, setScannerKey] = useState(0);
  const [publishNotice, setPublishNotice] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [savingRegistrationId, setSavingRegistrationId] = useState(null);
  const [editingRegistrationId, setEditingRegistrationId] = useState(null);
  const [registrationDrafts, setRegistrationDrafts] = useState({});
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const scannerId = `qr-reader-event-${id}-${scannerKey}`;

  const stopScanner = async () => {
    const scanner = scannerRef.current;
    scannerRef.current = null;

    if (scanner) {
      try {
        await scanner.clear();
      } catch {
        const scannerElement = document.getElementById(scannerId);
        if (scannerElement) {
          scannerElement.innerHTML = '';
        }
      }
    }

    const scannerElement = document.getElementById(scannerId);
    if (scannerElement) {
      scannerElement.innerHTML = '';
    }
  };

  const startScanner = async () => {
    if (scannerRef.current) {
      return;
    }

    scanLockRef.current = false;

    const scannerElement = document.getElementById(scannerId);
    if (!scannerElement) {
      return;
    }

    scannerElement.innerHTML = '';

    const { Html5QrcodeScanner } = await import('html5-qrcode');
    if (!document.getElementById(scannerId)) {
      return;
    }

    const scanner = new Html5QrcodeScanner(scannerId, { fps: 10, qrbox: 220 }, false);

    scanner.render(
      async (decodedText) => {
        if (scanLockRef.current) {
          return;
        }

        scanLockRef.current = true;
        await stopScanner();
        await submitScan(decodedText);
      },
      () => {}
    );

    scannerRef.current = scanner;
  };


  const loadEventDetails = async () => {
    const response = await api.get(`/events/${id}`);
    setEventData(response.data);
    setFormValues(emptyValues(response.data.fields || []));
  };

  useEffect(() => {
    loadEventDetails().catch((err) => setError(err.message));
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

  useEffect(() => {
    if (user?.role !== 'admin') {
      return;
    }

    api
      .get(`/results/event/${id}/registrations`)
      .then((res) => setRegistrationsData(res.data))
      .catch((err) => setError(err.message));
  }, [id, user]);

  useEffect(() => {
    if (user?.role !== 'admin') {
      return;
    }

    api
      .get(`/results/event/${id}/participants`)
      .then((res) => setParticipantsData(res.data))
      .catch((err) => setError(err.message));
  }, [id, user]);

  const refreshCheckinHistory = async () => {
    const response = await api.get(`/checkin/history?event_id=${id}`);
    setCheckinHistory(response.data);
  };

  const submitScan = async (qrToken) => {
    if (!qrToken) {
      return;
    }

    try {
      const response = await api.post('/checkin/scan', {
        qr_token: qrToken,
        event_id: Number(id),
      });
      const result = response.data.result;
      const message =
        result === 'success'
          ? 'Check-in successful.'
          : 'This attendee is already checked in.';

      setScanMessage(message);
      setScanPopup({
        title: result === 'success' ? 'Check-in successful' : 'Already checked in',
        message,
        kind: result === 'success' ? 'success' : 'warning',
      });
      await refreshCheckinHistory();
    } catch (err) {
      setScanMessage(err.message);
      setScanPopup({
        title: 'Check-in failed',
        message: err.message,
        kind: 'error',
      });
    }
  };

  useEffect(() => {
    if (user?.role !== 'admin') {
      return undefined;
    }

    refreshCheckinHistory().catch((err) => setScanMessage(err.message));

    let cancelled = false;

    startScanner().catch((err) => {
      if (!cancelled) {
        setScanMessage(`Scanner failed to initialize: ${err.message}`);
      }
    });

    return () => {
      cancelled = true;
      stopScanner().catch(() => {});
    };
  }, [id, user, scannerId]);

  useEffect(() => {
    if (user?.role !== 'user') {
      setExistingRegistration(null);
      return;
    }

    api
      .get('/registrations')
      .then((res) => {
        const match = (res.data || []).find((item) => Number(item.event_id) === Number(id));
        setExistingRegistration(match || null);
      })
      .catch(() => {});
  }, [id, user]);

  const canRegister = useMemo(() => {
    if (!eventData) return false;
    if (existingRegistration) return false;
    return eventData.status === 'open' || eventData.status === 'ongoing';
  }, [eventData, existingRegistration]);

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

  const updateParticipant = (userId, key, value) => {
    setParticipantsData((prev) => ({
      ...prev,
      participants: prev.participants.map((item) => (item.user_id === userId ? { ...item, [key]: value } : item)),
    }));
  };

  const updateRegistrationField = (registrationId, fieldName, value) => {
    setRegistrationDrafts((prev) => ({
      ...prev,
      [registrationId]: {
        ...(prev[registrationId] || {}),
        [fieldName]: value,
      },
    }));
  };

  const startEditingRegistration = (registrationId) => {
    const row = registrationsData.registrations.find((item) => item.registration_id === registrationId);
    setEditingRegistrationId(registrationId);
    setRegistrationDrafts((prev) => ({
      ...prev,
      [registrationId]: { ...(row?.field_values || {}) },
    }));
  };

  const cancelEditingRegistration = (registrationId) => {
    setEditingRegistrationId(null);
    setRegistrationDrafts((prev) => {
      const next = { ...prev };
      delete next[registrationId];
      return next;
    });
  };

  const saveRegistrationDetails = async (registrationId) => {
    setError('');
    setNotice('');
    setSavingRegistrationId(registrationId);

    try {
      const fieldValues = registrationDrafts[registrationId] || {};
      await api.put(`/registrations/admin/${registrationId}`, {
        field_values: fieldValues,
      });

      const [registrationsResponse, participantsResponse] = await Promise.all([
        api.get(`/results/event/${id}/registrations`),
        api.get(`/results/event/${id}/participants`),
      ]);

      setRegistrationsData(registrationsResponse.data);
      setParticipantsData(participantsResponse.data);
      setEditingRegistrationId(null);
      setRegistrationDrafts((prev) => {
        const next = { ...prev };
        delete next[registrationId];
        return next;
      });
      setNotice('Registration details updated successfully.');
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingRegistrationId(null);
    }
  };

  const publishScores = async () => {
    setError('');
    setPublishNotice('');
    setPublishing(true);
    try {
      const scores = participantsData.participants.map((item) => ({
        user_id: item.user_id,
        score: item.score,
        remarks: item.remarks,
      }));

      await api.post(`/results/event/${id}/publish`, { scores });

      const [participantsResponse, resultsResponse] = await Promise.all([
        api.get(`/results/event/${id}/participants`),
        api.get(`/results/event/${id}`),
      ]);

      setParticipantsData(participantsResponse.data);
      setResults(resultsResponse.data);
      setPublishNotice('Results published successfully. Ranks were calculated automatically.');
    } catch (err) {
      setError(err.message);
    } finally {
      setPublishing(false);
    }
  };

  const updateEventStatus = async (status) => {
    setError('');
    setNotice('');
    try {
      await api.put(`/events/${id}`, { status });
      await loadEventDetails();
      setNotice(`Event status updated to ${status}.`);
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteEvent = async () => {
    if (!window.confirm('Delete this event?')) {
      return;
    }
    setError('');
    setNotice('');
    try {
      await api.del(`/events/${id}`);
      navigate('/admin/events');
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
      {notice && <p className="notice">{notice}</p>}
      {error && <p className="error">{error}</p>}
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
          <div className="stack-horizontal">
            <button className="button-secondary" onClick={() => updateEventStatus('open')}>
              Open
            </button>
            <button className="button-secondary" onClick={() => updateEventStatus('ongoing')}>
              Ongoing
            </button>
            <button className="button-secondary" onClick={() => updateEventStatus('completed')}>
              Completed
            </button>
            <button className="button-danger" onClick={deleteEvent}>
              Delete
            </button>
          </div>
        </section>
      ) : canRegister && (
        <form className="card" onSubmit={onRegister}>
          <h2>Register for this event</h2>
          {eventData.fields?.map((field) => (
            <label key={field.id}>
              {field.label}
              {renderDynamicField(field, formValues[field.field_name] || '', (nextValue) =>
                setFormValues({ ...formValues, [field.field_name]: nextValue })
              )}
            </label>
          ))}
          <button className="button-primary" type="submit">
            Register
          </button>
        </form>
      )}

      {user?.role === 'admin' && (
        <section className="card">
          <h2>Event Check-in Scanner</h2>
          <p>Only QR codes belonging to this event will be accepted.</p>
          <div id={scannerId} className="card" />
          <div className="stack-horizontal">
            <button className="button-secondary" onClick={() => setScannerKey((prev) => prev + 1)}>
              Restart Scanner
            </button>
          </div>

          <h3>Manual Check-in</h3>
          <textarea
            rows="4"
            placeholder="Paste QR token"
            value={manualToken}
            onChange={(e) => setManualToken(e.target.value)}
          />
          <button className="button-primary" onClick={() => submitScan(manualToken)}>
            Submit Token
          </button>

          {scanMessage && <p className="notice">{scanMessage}</p>}

          {scanPopup && (
            <div className="modal-backdrop" role="presentation" onClick={() => setScanPopup(null)}>
              <div className={`modal-card modal-${scanPopup.kind}`} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
                <h2>{scanPopup.title}</h2>
                <p>{scanPopup.message}</p>
                <div className="stack-horizontal">
                  <button
                    className="button-primary"
                    onClick={async () => {
                      setScanPopup(null);
                      await stopScanner();
                      startScanner().catch((err) => setScanMessage(`Scanner failed to restart: ${err.message}`));
                    }}
                  >
                    Scan Next QR
                  </button>
                  <button
                    className="button-secondary"
                    onClick={async () => {
                      setScanPopup(null);
                      await stopScanner();
                    }}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          <h3>Event Scan History</h3>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Registration</th>
                  <th>Result</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {checkinHistory.map((item) => (
                  <tr key={item.id}>
                    <td>{new Date(item.scanned_at).toLocaleString()}</td>
                    <td>{item.registration_id ?? '-'}</td>
                    <td>{item.result}</td>
                    <td>{item.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {user?.role === 'user' && existingRegistration && eventData.status !== 'completed' && (
        <section className="card">
          <h2>Already Registered</h2>
          <p>You are already registered for this event. Use this QR for check-in.</p>
          {existingRegistration.qr_image && <img src={existingRegistration.qr_image} alt="Check-in QR" className="qr" />}
          <details>
            <summary>Show QR token</summary>
            <code className="code">{existingRegistration.qr_token}</code>
          </details>
        </section>
      )}

      {user?.role === 'admin' && (
        <section className="card">
          <h2>All Registrations</h2>
          <p>View all registered users, their check-in status, and submitted event details.</p>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Name</th>
                  <th>Check-in Status</th>
                  {registrationsData.fields.map((field) => (
                    <th key={field.field_name}>{field.label}</th>
                  ))}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {registrationsData.registrations.map((item) => (
                  <tr key={item.registration_id}>
                    <td>{item.user_id}</td>
                    <td>{item.full_name}</td>
                    <td>
                      <span className={item.check_in_status === 'checked_in' ? 'status-checked-in' : 'status-registered'}>
                        {item.check_in_status}
                      </span>
                    </td>
                    {registrationsData.fields.map((field) => (
                      <td key={`${item.user_id}-${field.field_name}`}>
                        {editingRegistrationId === item.registration_id
                          ? renderRegistrationEditField(
                              field,
                              registrationDrafts[item.registration_id]?.[field.field_name] || '',
                              (nextValue) => updateRegistrationField(item.registration_id, field.field_name, nextValue),
                              `registration-${item.registration_id}-${field.field_name}`
                            )
                          : item.field_values?.[field.field_name] || '-'}
                      </td>
                    ))}
                    <td>
                      {editingRegistrationId === item.registration_id ? (
                        <div className="stack-horizontal">
                          <button
                            className="button-primary"
                            onClick={() => saveRegistrationDetails(item.registration_id)}
                            disabled={savingRegistrationId === item.registration_id}
                          >
                            {savingRegistrationId === item.registration_id ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            className="button-secondary"
                            onClick={() => cancelEditingRegistration(item.registration_id)}
                            disabled={savingRegistrationId === item.registration_id}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          className="button-secondary"
                          onClick={() => startEditingRegistration(item.registration_id)}
                          disabled={savingRegistrationId !== null}
                        >
                          Edit
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {user?.role === 'admin' && (
        <section className="card">
          <h2>Publish Event Results</h2>
          <p>Enter marks for participants. Rank is computed automatically from highest score to lowest score.</p>
          {publishNotice && <p className="notice">{publishNotice}</p>}
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Name</th>
                  {participantsData.fields.map((field) => (
                    <th key={field.field_name}>{field.label}</th>
                  ))}
                  <th>Marks</th>
                  <th>Rank</th>
                  <th>Remarks</th>
                </tr>
              </thead>
              <tbody>
                {participantsData.participants.map((item) => (
                  <tr key={item.user_id}>
                    <td>{item.user_id}</td>
                    <td>{item.full_name}</td>
                    {participantsData.fields.map((field) => (
                      <td key={`${item.user_id}-${field.field_name}`}>{item.field_values?.[field.field_name] || '-'}</td>
                    ))}
                    <td>
                      <input
                        type="number"
                        step="0.01"
                        value={item.score ?? ''}
                        onChange={(e) => updateParticipant(item.user_id, 'score', e.target.value)}
                        placeholder="Marks"
                      />
                    </td>
                    <td>{item.rank ?? '-'}</td>
                    <td>
                      <input
                        value={item.remarks ?? ''}
                        onChange={(e) => updateParticipant(item.user_id, 'remarks', e.target.value)}
                        placeholder="Remarks"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="button-primary" onClick={publishScores} disabled={publishing}>
            {publishing ? 'Publishing...' : 'Publish Results'}
          </button>
        </section>
      )}

      {registerRes && eventData.status !== 'completed' && (
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
          {user?.role === 'admin' && results.attendance && (
            <p>
              Attendance: {results.attendance.checked_in}/{results.attendance.total_registered} checked in
            </p>
          )}

          {user?.role !== 'admin' && results.my_result?.remarks && (
            <section className="subtle card">
              <h3>Your Remark</h3>
              <p>{results.my_result.remarks}</p>
            </section>
          )}

          <table className="table">
            <thead>
              <tr>
                <th>User ID</th>
                <th>Name</th>
                <th>Score</th>
                <th>Rank</th>
                {user?.role === 'admin' && <th>Remarks</th>}
              </tr>
            </thead>
            <tbody>
              {results.ranking.map((item) => (
                <tr key={`${item.user_id}-${item.rank}`}>
                  <td>{item.user_id}</td>
                  <td>{item.full_name || '-'}</td>
                  <td>{item.score}</td>
                  <td>{item.rank}</td>
                  {user?.role === 'admin' && <td>{item.remarks || '-'}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
