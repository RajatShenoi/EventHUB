import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
  options_text: '',
  regex_pattern: '',
  max_length: '',
};

export default function AdminEventsPage() {
  const [events, setEvents] = useState([]);
  const [eventForm, setEventForm] = useState(INITIAL_EVENT);
  const [fields, setFields] = useState([]);
  const [fieldDraft, setFieldDraft] = useState(INITIAL_FIELD);
  const [error, setError] = useState('');
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

    const options = ['select', 'radio'].includes(fieldDraft.field_type)
      ? fieldDraft.options_text
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean)
      : [];

    if (['select', 'radio'].includes(fieldDraft.field_type) && options.length === 0) {
      setError('Please provide at least one option for option-based question fields.');
      return;
    }

    setFields([
      ...fields,
      {
        field_name: fieldDraft.field_name,
        label: fieldDraft.label,
        field_type: fieldDraft.field_type,
        is_required: fieldDraft.is_required,
        options,
        regex_pattern: fieldDraft.regex_pattern,
        max_length: fieldDraft.max_length ? Number(fieldDraft.max_length) : null,
      },
    ]);
    setError('');
    setFieldDraft(INITIAL_FIELD);
  };

  const removeField = (indexToRemove) => {
    setFields((prev) => prev.filter((_, index) => index !== indexToRemove));
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
            Question / Label
            <input value={fieldDraft.label} onChange={(e) => setFieldDraft({ ...fieldDraft, label: e.target.value })} />
          </label>
          <label>
            Type
            <select value={fieldDraft.field_type} onChange={(e) => setFieldDraft({ ...fieldDraft, field_type: e.target.value })}>
              <option value="text">text</option>
              <option value="email">email</option>
              <option value="phone">phone</option>
              <option value="textarea">textarea</option>
              <option value="select">select (question + options)</option>
              <option value="radio">radio (question + options)</option>
            </select>
          </label>
          {['select', 'radio'].includes(fieldDraft.field_type) && (
            <label>
              Options (comma-separated)
              <input
                value={fieldDraft.options_text}
                onChange={(e) => setFieldDraft({ ...fieldDraft, options_text: e.target.value })}
                placeholder="Option 1, Option 2, Option 3"
              />
            </label>
          )}
          <label>
            Regex Pattern
            <input value={fieldDraft.regex_pattern} onChange={(e) => setFieldDraft({ ...fieldDraft, regex_pattern: e.target.value })} />
          </label>
          <button className="button-secondary" type="button" onClick={addField}>
            Add Field
          </button>

          {fields.length > 0 && (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Field Name</th>
                    <th>Question</th>
                    <th>Type</th>
                    <th>Options</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {fields.map((field, index) => (
                    <tr key={`${field.field_name}-${index}`}>
                      <td>{index + 1}</td>
                      <td>{field.field_name}</td>
                      <td>{field.label}</td>
                      <td>{field.field_type}</td>
                      <td>{field.options?.length ? field.options.join(', ') : '-'}</td>
                      <td>
                        <button className="button-danger" type="button" onClick={() => removeField(index)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <button className="button-primary" type="submit">
          Create Event
        </button>
      </form>

      <div className="grid">
        {events.map((event) => (
          <article className="card" key={event.id}>
            <h3>{event.title}</h3>
            <p>{event.description}</p>
            <p>Status: {event.status}</p>
            <div className="stack-horizontal">
              <Link className="button-secondary inline-block" to={`/events/${event.id}`}>
                Open Event Page
              </Link>
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
