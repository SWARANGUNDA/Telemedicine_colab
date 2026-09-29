import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

export default function ProtectedRoute({ currentUser, authChecking, allowedRoles, children }) {
  const location = useLocation();

  if (authChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 text-slate-600">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm font-medium">Authenticating session...</p>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    if (location.pathname.startsWith('/admin')) {
      return <Navigate to="/admin" state={{ from: location }} replace />;
    }
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(currentUser.role)) {
    const defaultRedirect =
      currentUser.role === 'ADMIN'
        ? '/admin/dashboard'
        : currentUser.role === 'DOCTOR'
        ? '/doctor/dashboard'
        : '/dashboard';

    // Seamless auto-redirection to appropriate portal workspace
    return <Navigate to={defaultRedirect} replace />;
  }

  return children;
}
