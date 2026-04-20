import { useEffect, useState } from 'react';
import { api } from '../api/client';

const INITIAL_EVENT = {
  title: '',
  description: '',
  location: '',
  event_date: '',
  registration_deadline: '',
  max_capacity: '',
  status: 'open',
};

const INITIAL_FIELD = {
  field_name: '',
  label: '',
  field_type: 'text',
  is_required: true,
  options: [],
  regex_pattern: '',
  max_length: '',
};

export default function AdminEventsPage() {
  const [events, setEvents] = useState([]);
  const [eventForm, setEventForm] = useState(INITIAL_EVENT);
  const [fields, setFields] = useState([]);
  const [fieldDraft, setFieldDraft] = useState(INITIAL_FIELD);
  const [error, setError] = useState('');
  const [resultForm, setResultForm] = useState({ event_id: '', user_id: '', score: '', rank: '', remarks: '' });
  const [notice, setNotice] = useState('');

  const loadEvents = () => {
    api
      .get('/events')
      .then((res) => setEvents(res.data))
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadEvents();
  }, []);

  const addField = () => {
    if (!fieldDraft.field_name || !fieldDraft.label) return;
    setFields([...fields, { ...fieldDraft, max_length: fieldDraft.max_length ? Number(fieldDraft.max_length) : null }]);
    setFieldDraft(INITIAL_FIELD);
  };

  const createEvent = async (e) => {
    e.preventDefault();
    try {
      await api.post('/events', {
        ...eventForm,
        max_capacity: eventForm.max_capacity ? Number(eventForm.max_capacity) : null,
        fields,
      });
      setEventForm(INITIAL_EVENT);
      setFields([]);
      loadEvents();
    } catch (err) {
      setError(err.message);
    }
  };

  const updateStatus = async (eventId, status) => {
    try {
      await api.put(`/events/${eventId}`, { status });
      loadEvents();
    } catch (err) {
      setError(err.message);
    }
  };

  const removeEvent = async (eventId) => {
    try {
      await api.del(`/events/${eventId}`);
      loadEvents();
    } catch (err) {
      setError(err.message);
    }
  };

  const publishResult = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/results/event/${Number(resultForm.event_id)}`, {
        user_id: Number(resultForm.user_id),
        score: Number(resultForm.score),
        rank: Number(resultForm.rank),
        remarks: resultForm.remarks,
      });
      setResultForm({ event_id: '', user_id: '', score: '', rank: '', remarks: '' });
      setNotice('Result published. Users can view once event is completed.');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h1>Admin Event Management</h1>
      {error && <p className="error">{error}</p>}
      {notice && <p className="notice">{notice}</p>}

      <form className="card" onSubmit={createEvent}>
        <h2>Create Event</h2>
        <label>
          Title
          <input value={eventForm.title} onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })} required />
        </label>
        <label>
          Description
          <textarea value={eventForm.description} onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })} required />
        </label>
        <label>
          Location
          <input value={eventForm.location} onChange={(e) => setEventForm({ ...eventForm, location: e.target.value })} required />
        </label>
        <label>
          Event Date
          <input type="datetime-local" value={eventForm.event_date} onChange={(e) => setEventForm({ ...eventForm, event_date: e.target.value })} required />
        </label>
        <label>
          Registration Deadline
          <input
            type="datetime-local"
            value={eventForm.registration_deadline}
            onChange={(e) => setEventForm({ ...eventForm, registration_deadline: e.target.value })}
          />
        </label>
        <label>
          Max Capacity
          <input type="number" value={eventForm.max_capacity} onChange={(e) => setEventForm({ ...eventForm, max_capacity: e.target.value })} />
        </label>

        <section className="card subtle">
          <h3>Add Event-Specific Registration Field</h3>
          <label>
            Field Name
            <input value={fieldDraft.field_name} onChange={(e) => setFieldDraft({ ...fieldDraft, field_name: e.target.value })} />
          </label>
          <label>
            Label
            <input value={fieldDraft.label} onChange={(e) => setFieldDraft({ ...fieldDraft, label: e.target.value })} />
          </label>
          <label>
            Type
            <select value={fieldDraft.field_type} onChange={(e) => setFieldDraft({ ...fieldDraft, field_type: e.target.value })}>
              <option value="text">text</option>
              <option value="email">email</option>
              <option value="phone">phone</option>
              <option value="textarea">textarea</option>
            </select>
          </label>
          <label>
            Regex Pattern
            <input value={fieldDraft.regex_pattern} onChange={(e) => setFieldDraft({ ...fieldDraft, regex_pattern: e.target.value })} />
          </label>
          <button className="button-secondary" type="button" onClick={addField}>
            Add Field
          </button>
          <pre className="code">{JSON.stringify(fields, null, 2)}</pre>
        </section>

        <button className="button-primary" type="submit">
          Create Event
        </button>
      </form>

      <form className="card" onSubmit={publishResult}>
        <h2>Publish Event Result</h2>
        <label>
          Event ID
          <input value={resultForm.event_id} onChange={(e) => setResultForm({ ...resultForm, event_id: e.target.value })} required />
        </label>
        <label>
          User ID
          <input value={resultForm.user_id} onChange={(e) => setResultForm({ ...resultForm, user_id: e.target.value })} required />
        </label>
        <label>
          Score
          <input value={resultForm.score} onChange={(e) => setResultForm({ ...resultForm, score: e.target.value })} required />
        </label>
        <label>
          Rank
          <input value={resultForm.rank} onChange={(e) => setResultForm({ ...resultForm, rank: e.target.value })} required />
        </label>
        <label>
          Remarks
          <input value={resultForm.remarks} onChange={(e) => setResultForm({ ...resultForm, remarks: e.target.value })} />
        </label>
        <button className="button-primary" type="submit">
          Publish Result
        </button>
      </form>

      <div className="grid">
        {events.map((event) => (
          <article className="card" key={event.id}>
            <h3>{event.title}</h3>
            <p>{event.description}</p>
            <p>Status: {event.status}</p>
            <div className="stack-horizontal">
              <button className="button-secondary" onClick={() => updateStatus(event.id, 'open')}>
                Open
              </button>
              <button className="button-secondary" onClick={() => updateStatus(event.id, 'ongoing')}>
                Ongoing
              </button>
              <button className="button-secondary" onClick={() => updateStatus(event.id, 'completed')}>
                Completed
              </button>
              <button className="button-danger" onClick={() => removeEvent(event.id)}>
                Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
