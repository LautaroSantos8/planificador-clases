import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../../services/api';

const OlvideContrasena = () => {
  const [email, setEmail] = useState('');
  const [enviado, setEnviado] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await authAPI.solicitarResetPassword(email.trim());
      setEnviado(true);
    } catch (err) {
      setError('No pudimos procesar la solicitud. Intentá de nuevo en unos minutos.');
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
          {enviado ? (
            <>
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Revisá tu correo</h2>
              <p className="text-gray-600 mb-2">
                Si <span className="font-medium text-gray-900">{email}</span> está
                registrado en ARIA, vas a recibir un enlace para crear una contraseña nueva.
              </p>
              <p className="text-sm text-gray-500 mb-6">
                El enlace vence en una hora. Si no lo ves, revisá la carpeta de spam.
              </p>
              <Link
                to="/login"
                className="block w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors text-center"
              >
                Volver al inicio de sesión
              </Link>
            </>
          ) : (
            <>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Recuperar contraseña</h2>
              <p className="text-gray-600 text-sm mb-6">
                Ingresá el correo con el que accedés a ARIA y te enviamos un enlace para
                crear una contraseña nueva.
              </p>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    Correo electrónico
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoFocus
                    autoComplete="email"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                    placeholder="docente@ejemplo.com"
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
                      Enviando...
                    </>
                  ) : (
                    'Enviar enlace'
                  )}
                </button>
              </form>

              <Link
                to="/login"
                className="block text-center text-sm text-indigo-600 hover:text-indigo-700 mt-5"
              >
                Volver al inicio de sesión
              </Link>
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

export default OlvideContrasena;
