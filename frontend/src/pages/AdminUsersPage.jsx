import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({ email: '', full_name: '', role: 'user' });

  const loadUsers = () => {
    api
      .get('/admin/users')
      .then((res) => setUsers(res.data))
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const startEdit = (user) => {
    setEditingUser(user.id);
    setEditForm({ email: user.email, full_name: user.full_name, role: user.role });
    setNotice('');
    setError('');
  };

  const cancelEdit = () => {
    setEditingUser(null);
    setEditForm({ email: '', full_name: '', role: 'user' });
  };

  const saveEdit = async () => {
    try {
      await api.put(`/admin/users/${editingUser}`, editForm);
      setNotice('User updated successfully.');
      cancelEdit();
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('Delete this user?')) {
      return;
    }
    try {
      await api.del(`/admin/users/${userId}`);
      setNotice('User deleted successfully.');
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h1>Registered Users</h1>
      <p className="notice">Visible to admins only.</p>
      {error && <p className="error">{error}</p>}
      {notice && <p className="notice">{notice}</p>}

      {editingUser && (
        <section className="card">
          <h2>Edit User</h2>
          <div className="grid two-up">
            <label>
              Full Name
              <input value={editForm.full_name} onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })} />
            </label>
            <label>
              Email
              <input value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} />
            </label>
            <label>
              Role
              <select value={editForm.role} onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}>
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </label>
          </div>
          <div className="stack-horizontal">
            <button className="button-primary" onClick={saveEdit}>
              Save Changes
            </button>
            <button className="button-secondary" onClick={cancelEdit}>
              Cancel
            </button>
          </div>
        </section>
      )}

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Joined</th>
              <th>Registrations</th>
              <th>Checked In</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.full_name}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>{new Date(user.created_at).toLocaleString()}</td>
                <td>{user.registration_count}</td>
                <td>{user.checked_in_count}</td>
                <td>
                  <div className="stack-horizontal">
                    <button className="button-secondary" onClick={() => startEdit(user)}>
                      Edit
                    </button>
                    <button className="button-danger" onClick={() => deleteUser(user.id)}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
