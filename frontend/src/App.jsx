import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { asignacionesAPI } from './services/api';

// Components
import Login from './components/auth/Login';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';

// Pages
import DashboardPage from './pages/DashboardPage';
import ConfiguracionPage from './pages/ConfiguracionPage';
import AlumnosPage from './pages/AlumnosPage';
import DocumentosPage from './pages/DocumentosPage';
import ChatPage from './pages/ChatPage';

// Layout para páginas protegidas
const AppLayout = ({ children, asignaciones, loading }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
      <Sidebar 
        asignaciones={asignaciones} 
        loading={loading} 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <main className="lg:ml-64 pt-20 px-4 pb-4 md:px-6 md:pb-6">
        {children}
      </main>
    </div>
  );
};

// Componente principal con estado de asignaciones
const AppContent = () => {
  const { isAuthenticated } = useAuth();
  const [asignaciones, setAsignaciones] = useState([]);
  const [loading, setLoading] = useState(true);

  // Cargar asignaciones desde la API
  useEffect(() => {
    const fetchAsignaciones = async () => {
      if (isAuthenticated) {
        setLoading(true);
        try {
          const response = await asignacionesAPI.getAll();
          if (response.success) {
            setAsignaciones(response.asignaciones);
          }
        } catch (error) {
          console.error('Error cargando asignaciones:', error);
        } finally {
          setLoading(false);
        }
      } else {
        setAsignaciones([]);
        setLoading(false);
      }
    };

    fetchAsignaciones();
  }, [isAuthenticated]);

  // Agregar asignación
  const handleAddAsignacion = async (nueva) => {
    try {
      const response = await asignacionesAPI.create(nueva);
      if (response.success) {
        setAsignaciones(prev => [...prev, response.asignacion]);
        return { success: true };
      } else {
        return { success: false, error: response.error };
      }
    } catch (error) {
      console.error('Error creando asignación:', error);
      const msg = error?.response?.data?.error || 'Error de conexión';
      return { success: false, error: msg };
    }
  };

  // Eliminar asignación
  const handleDeleteAsignacion = async (id) => {
    try {
      const response = await asignacionesAPI.delete(id);
      if (response.success) {
        setAsignaciones(prev => prev.filter(a => a.id !== id));
        return { success: true };
      } else {
        return { success: false, error: response.error };
      }
    } catch (error) {
      console.error('Error eliminando asignación:', error);
      return { success: false, error: 'Error de conexión' };
    }
  };

  return (
    <Routes>
      {/* Ruta pública */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
      />

      {/* Rutas protegidas */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout asignaciones={asignaciones} loading={loading}>
              <DashboardPage asignaciones={asignaciones} />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/configuracion"
        element={
          <ProtectedRoute>
            <AppLayout asignaciones={asignaciones} loading={loading}>
              <ConfiguracionPage
                asignaciones={asignaciones}
                onAddAsignacion={handleAddAsignacion}
                onDeleteAsignacion={handleDeleteAsignacion}
              />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/alumnos/:grado/:division/:materiaId"
        element={
          <ProtectedRoute>
            <AppLayout asignaciones={asignaciones} loading={loading}>
              <AlumnosPage asignaciones={asignaciones} />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/documentos/:grado/:division/:materiaId"
        element={
          <ProtectedRoute>
            <AppLayout asignaciones={asignaciones} loading={loading}>
              <DocumentosPage asignaciones={asignaciones} />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/chat/:grado/:division/:materiaId"
        element={
          <ProtectedRoute>
            <AppLayout asignaciones={asignaciones} loading={loading}>
              <ChatPage asignaciones={asignaciones} />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Redirect por defecto */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
