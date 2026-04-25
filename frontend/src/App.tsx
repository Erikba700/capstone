import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { useAuthStore } from './context/store';
import { LoadingSpinner } from './components/LoadingSpinner';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import { useDarkMode } from './hooks/useDarkMode';

function App() {
  const { isAuthenticated, isLoading, loadUser } = useAuthStore();
  const { isDarkMode } = useDarkMode();

  useEffect(() => {
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  console.log('App rendering:', { isAuthenticated, isLoading, isDarkMode });

  if (isLoading) {
    console.log('Showing loading spinner');
    return <LoadingSpinner fullScreen />;
  }

  console.log('Rendering main app');

  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ backgroundColor: isDarkMode ? '#111827' : '#f9fafb' }}>
        {isAuthenticated && <Navbar />}

        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? <Navigate to="/" replace /> : <Login />
            }
          />

          <Route
            path="/register"
            element={
              isAuthenticated ? <Navigate to="/" replace /> : <Register />
            }
          />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme={isDarkMode ? "dark" : "light"}
        />
      </div>
    </BrowserRouter>
  );
}

export default App;
