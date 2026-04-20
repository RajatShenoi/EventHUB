import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="nav">
      <div className="brand">EventHub</div>
      {user ? (
        <div className="nav-links">
          <Link to="/">Events</Link>
          {user.role !== 'admin' && <Link to="/my-registrations">My Registrations</Link>}
          {user.role === 'admin' && <Link to="/admin/events">Manage Events</Link>}
          {user.role === 'admin' && <Link to="/admin/checkin">Check-in Scanner</Link>}
          {user.role === 'admin' && <Link to="/admin/role-requests">Role Requests</Link>}
          {user.role === 'admin' && <Link to="/admin/users">Users</Link>}
          <button
            className="button-secondary"
            onClick={() => {
              logout();
              navigate('/login');
            }}
          >
            Logout
          </button>
        </div>
      ) : (
        <div className="nav-links">
          <Link to="/login">Login</Link>
        </div>
      )}
    </nav>
  );
}
