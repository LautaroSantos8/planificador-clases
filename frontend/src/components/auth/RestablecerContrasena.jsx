import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../../services/api';

const RestablecerContrasena = () => {
  const { uid, token } = useParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmacion, setConfirmacion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [listo, setListo] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirmacion) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await authAPI.confirmarResetPassword(uid, token, password);
      setListo(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      const detalle = err?.response?.data?.error;
      setError(
        detalle ||
          'El enlace venció o ya se usó. Pedí uno nuevo desde "Olvidé mi contraseña".'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full mx-4">
        {/* Logo y título */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-full mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">ARIA</h1>
          <p className="text-gray-600 mt-2">Escuela Municipal Dr. Jorge Orgaz</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {listo ? (
            <>
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Contraseña actualizada</h2>
              <p className="text-gray-600 mb-6">
                Ya podés entrar a ARIA con tu contraseña nueva. Te llevamos al inicio de sesión.
              </p>
              <Link
                to="/login"
                className="block w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors text-center"
              >
                Ir al inicio de sesión
              </Link>
            </>
          ) : (
            <>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Crear contraseña nueva</h2>
              <p className="text-gray-600 text-sm mb-6">
                Elegí una contraseña de al menos 8 caracteres, que no se parezca a tu
                nombre ni a tu correo.
              </p>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    Contraseña nueva
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    autoFocus
                    autoComplete="new-password"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                    placeholder="••••••••"
                  />
                </div>

                <div>
                  <label htmlFor="confirmacion" className="block text-sm font-medium text-gray-700 mb-1">
                    Repetir contraseña
                  </label>
                  <input
                    id="confirmacion"
                    type="password"
                    value={confirmacion}
                    onChange={(e) => setConfirmacion(e.target.value)}
                    required
                    autoComplete="new-password"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                    placeholder="••••••••"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Guardando...
                    </>
                  ) : (
                    'Guardar contraseña'
                  )}
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          Villa Rivera Indarte, Córdoba
        </p>
      </div>
    </div>
  );
};

export default RestablecerContrasena;
