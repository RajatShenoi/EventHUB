import { Navigate, Route, Routes } from 'react-router-dom';
import NavBar from './components/NavBar';
import ProtectedRoute from './components/ProtectedRoute';
import AdminCheckinPage from './pages/AdminCheckinPage';
import AdminEventsPage from './pages/AdminEventsPage';
import AdminRoleRequestsPage from './pages/AdminRoleRequestsPage';
import AdminUsersPage from './pages/AdminUsersPage';
import EventDetailPage from './pages/EventDetailPage';
import EventsPage from './pages/EventsPage';
import LoginPage from './pages/LoginPage';
import MyRegistrationsPage from './pages/MyRegistrationsPage';

export default function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute roles={['user', 'admin']}>
              <EventsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/:id"
          element={
            <ProtectedRoute roles={['user', 'admin']}>
              <EventDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/my-registrations"
          element={
            <ProtectedRoute roles={['user']}>
              <MyRegistrationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/events"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminEventsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/checkin"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminCheckinPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/role-requests"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminRoleRequestsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
