import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ email: '', password: '', full_name: '' });
  const [error, setError] = useState('');

  const onSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      if (isRegister) {
        await api.post('/auth/register', form);
      }
      const response = await api.post('/auth/login', { email: form.email, password: form.password });
      localStorage.setItem('token', response.data.token);
      setUser(response.data.user);
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container form-container">
      <h1>{isRegister ? 'Create Account' : 'Login'}</h1>
      <form onSubmit={onSubmit} className="card">
        {isRegister && (
          <label>
            Full Name
            <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          </label>
        )}
        <label>
          Email
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </label>
        <label>
          Password
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="button-primary" type="submit">
          {isRegister ? 'Register & Login' : 'Login'}
        </button>
      </form>
      <button className="button-secondary" onClick={() => setIsRegister(!isRegister)}>
        {isRegister ? 'Already have an account? Login' : 'New user? Create account'}
      </button>
    </div>
  );
}
