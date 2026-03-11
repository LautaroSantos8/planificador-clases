import React, { useState, useEffect } from 'react';
import { materiasAPI } from '../services/api';

const ConfiguracionPage = ({ asignaciones, onAddAsignacion, onDeleteAsignacion }) => {
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [materias, setMaterias] = useState([]);
  
  const [formData, setFormData] = useState({
    grado: '',
    division: 'A',
    turno: 'M',
    materia_nombre: '',
  });

  // Cargar materias disponibles
  useEffect(() => {
    const fetchMaterias = async () => {
      try {
        const response = await materiasAPI.getAll();
        if (response.success) {
          setMaterias(response.materias);
        }
      } catch (err) {
        console.error('Error cargando materias:', err);
        // Materias por defecto si falla
        setMaterias([
          'Matemática', 'Lengua', 'Ciencias Naturales', 
          'Ciencias Sociales', 'Educación Física', 'Música', 
          'Plástica', 'Tecnología', 'Inglés'
        ]);
      }
    };
    fetchMaterias();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await onAddAsignacion(formData);
    
    if (result.success) {
      setFormData({ grado: '', division: 'A', turno: 'M', materia_nombre: '' });
      setShowForm(false);
    } else {
      setError(result.error || 'Error al crear asignación');
    }
    
    setLoading(false);
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar esta asignación?')) {
      const result = await onDeleteAsignacion(id);
      if (!result.success) {
        alert(result.error || 'Error al eliminar');
      }
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mis Asignaciones</h1>
          <p className="text-gray-600 mt-1">Configurá los grados, divisiones y materias que enseñás</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nueva Asignación
        </button>
      </div>

      {/* Formulario */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Agregar Asignación</h2>
          
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Grado</label>
              <select
                value={formData.grado}
                onChange={(e) => setFormData({ ...formData, grado: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Seleccionar</option>
                <option value="1">1° Grado</option>
                <option value="2">2° Grado</option>
                <option value="3">3° Grado</option>
                <option value="4">4° Grado</option>
                <option value="5">5° Grado</option>
                <option value="6">6° Grado</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">División</label>
              <select
                value={formData.division}
                onChange={(e) => setFormData({ ...formData, division: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Turno</label>
              <select
                value={formData.turno}
                onChange={(e) => setFormData({ ...formData, turno: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="M">Mañana</option>
                <option value="T">Tarde</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
              <select
                value={formData.materia_nombre}
                onChange={(e) => setFormData({ ...formData, materia_nombre: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Seleccionar</option>
                {materias.map((m, i) => (
                  <option key={i} value={m}>{m}</option>
                ))}
              </select>
            </div>

            <div className="md:col-span-4 flex justify-end gap-3 mt-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Lista de asignaciones */}
      {asignaciones.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Sin asignaciones</h3>
          <p className="text-gray-500 mb-4">Agregá tu primera asignación para comenzar</p>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Agregar Asignación
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {asignaciones.map((a) => (
            <div key={a.id} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                  <span className="text-indigo-700 font-bold">{a.grado}°{a.division}</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{a.materia_nombre}</h3>
                  <p className="text-sm text-gray-500">
                    {a.grado}° Grado - División {a.division} - Turno {a.turno_display || (a.turno === 'M' ? 'Mañana' : 'Tarde')}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleDelete(a.id)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Eliminar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConfiguracionPage;
