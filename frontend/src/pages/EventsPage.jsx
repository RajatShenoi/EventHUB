import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/events')
      .then((res) => setEvents(res.data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="container">
      <h1>Available Events</h1>
      {error && <p className="error">{error}</p>}
      <div className="grid">
        {events.map((event) => (
          <article className="card" key={event.id}>
            <h3>{event.title}</h3>
            <p>{event.description.slice(0, 120)}...</p>
            <p>
              <strong>Status:</strong> {event.status}
            </p>
            <p>
              <strong>Date:</strong> {new Date(event.event_date).toLocaleString()}
            </p>
            <Link className="button-primary inline-block" to={`/events/${event.id}`}>
              View Event
            </Link>
          </article>
        ))}
      </div>
    </div>
  );
}
