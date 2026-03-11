import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [docente, setDocente] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cargar docente desde localStorage al iniciar
  useEffect(() => {
    const storedDocente = localStorage.getItem('docente');
    if (storedDocente) {
      try {
        setDocente(JSON.parse(storedDocente));
      } catch (e) {
        localStorage.removeItem('docente');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await authAPI.login(email, password);
      
      if (response.token) {
        localStorage.setItem('token', response.token);
      }
      
      const docenteData = response.docente || response;
      localStorage.setItem('docente', JSON.stringify(docenteData));
      setDocente(docenteData);
      
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.error || 'Error al iniciar sesión';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authAPI.logout();
    setDocente(null);
    setError(null);
  };

  const value = {
    docente,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!docente,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
