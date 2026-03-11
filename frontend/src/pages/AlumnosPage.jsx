import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import NivelBadge from '../components/alumnos/NivelBadge';
import { alumnosAPI, nivelesAPI } from '../services/api';

const AlumnosPage = ({ asignaciones }) => {
  const { grado, division, materiaId } = useParams();
  const [alumnos, setAlumnos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingNivel, setUpdatingNivel] = useState(null);
  const [editingObservacion, setEditingObservacion] = useState(null);
  const [observacionTemp, setObservacionTemp] = useState('');
  const [savingObservacion, setSavingObservacion] = useState(false);

  // Encontrar la asignación actual
  const asignacionActual = asignaciones.find(
    a => a.grado === grado && a.division === division && a.materia_id === parseInt(materiaId)
  );

  // Cargar alumnos desde la API
  useEffect(() => {
    const fetchAlumnos = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await alumnosAPI.getByAsignacion(grado, division);
        
        if (response.success) {
          setAlumnos(response.alumnos);
        } else {
          setError(response.error || 'Error al cargar alumnos');
        }
      } catch (err) {
        setError('Error de conexión con el servidor');
        console.error('Error fetching alumnos:', err);
      } finally {
        setLoading(false);
      }
    };

    if (grado && division) {
      fetchAlumnos();
    }
  }, [grado, division]);

  // Cambiar nivel de un alumno
  const handleNivelChange = async (alumnoId, nuevoNivel) => {
    setUpdatingNivel(alumnoId);
    
    try {
      const response = await nivelesAPI.updateNivel(alumnoId, materiaId, nuevoNivel);
      
      if (response.success) {
        // Actualizar estado local
        setAlumnos(prev => prev.map(a => 
          a.id === alumnoId 
            ? { ...a, niveles: { ...a.niveles, [materiaId]: nuevoNivel } }
            : a
        ));
      } else {
        alert('Error al actualizar nivel: ' + response.error);
      }
    } catch (err) {
      alert('Error de conexión');
      console.error('Error updating nivel:', err);
    } finally {
      setUpdatingNivel(null);
    }
  };

  // Abrir editor de observaciones
  const handleEditObservacion = (alumno) => {
    setEditingObservacion(alumno.id);
    setObservacionTemp(alumno.observaciones || '');
  };

  // Guardar observación
  const handleSaveObservacion = async (alumnoId) => {
    setSavingObservacion(true);
    
    try {
      const response = await alumnosAPI.updateObservaciones(alumnoId, observacionTemp);
      
      if (response.success) {
        setAlumnos(prev => prev.map(a => 
          a.id === alumnoId 
            ? { ...a, observaciones: observacionTemp }
            : a
        ));
        setEditingObservacion(null);
        setObservacionTemp('');
      } else {
        alert('Error al guardar: ' + response.error);
      }
    } catch (err) {
      alert('Error de conexión');
      console.error('Error saving observacion:', err);
    } finally {
      setSavingObservacion(false);
    }
  };

  // Cancelar edición
  const handleCancelEdit = () => {
    setEditingObservacion(null);
    setObservacionTemp('');
  };

  // Contar alumnos por nivel
  const contarPorNivel = (nivel) => 
    alumnos.filter(a => (a.niveles?.[materiaId] || 'LE') === nivel).length;

  if (!asignacionActual) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Asignación no encontrada</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <svg className="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="ml-2 text-gray-600">Cargando alumnos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Alumnos de {grado}° {division}
          </h1>
          <p className="text-gray-600 mt-1">{asignacionActual.materia_nombre}</p>
        </div>
        <div className="text-sm text-gray-500">
          Los alumnos se administran desde el panel de Django
        </div>
      </div>

      {/* Resumen por niveles */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-red-700">{contarPorNivel('NEE')}</p>
          <p className="text-sm text-red-600">NEE - Rezago Significativo</p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-yellow-700">{contarPorNivel('LP')}</p>
          <p className="text-sm text-yellow-600">LP - Logros en Proceso</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-green-700">{contarPorNivel('LE')}</p>
          <p className="text-sm text-green-600">LE - Logros Esperados</p>
        </div>
      </div>

      {/* Lista de alumnos */}
      {alumnos.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Sin alumnos en {grado}° {division}</h3>
          <p className="text-gray-500 mb-4">
            Los alumnos se cargan desde el panel de administración de Django.
          </p>
          <a
            href="http://localhost:8000/admin/planificacion/alumno/add/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Ir al Panel de Admin
          </a>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Alumno
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nivel en {asignacionActual.materia_nombre}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Observaciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {alumnos.map((alumno) => (
                <tr key={alumno.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">
                      {alumno.apellido}, {alumno.nombre}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <select
                        value={alumno.niveles?.[materiaId] || 'LE'}
                        onChange={(e) => handleNivelChange(alumno.id, e.target.value)}
                        disabled={updatingNivel === alumno.id}
                        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                      >
                        <option value="NEE">NEE - Rezago Significativo</option>
                        <option value="LP">LP - Logros en Proceso</option>
                        <option value="LE">LE - Logros Esperados</option>
                      </select>
                      <NivelBadge nivel={alumno.niveles?.[materiaId] || 'LE'} size="sm" />
                      {updatingNivel === alumno.id && (
                        <svg className="animate-spin h-4 w-4 text-indigo-600" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {editingObservacion === alumno.id ? (
                      <div className="flex items-center gap-2">
                        <textarea
                          value={observacionTemp}
                          onChange={(e) => setObservacionTemp(e.target.value)}
                          rows={2}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                          placeholder="Ej: Dificultad con lectoescritura..."
                        />
                        <div className="flex flex-col gap-1">
                          <button
                            onClick={() => handleSaveObservacion(alumno.id)}
                            disabled={savingObservacion}
                            className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                          >
                            {savingObservacion ? '...' : 'Guardar'}
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400"
                          >
                            Cancelar
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <p className="text-sm text-gray-500 flex-1">
                          {alumno.observaciones || <span className="italic text-gray-400">Sin observaciones</span>}
                        </p>
                        <button
                          onClick={() => handleEditObservacion(alumno)}
                          className="text-indigo-600 hover:text-indigo-800 text-sm"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Info adicional */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="ml-3">
            <p className="text-sm text-blue-800">
              <strong>Nota:</strong> Los niveles y observaciones que asignes aquí se usarán cuando consultes al asistente IA 
              para generar planificaciones diferenciadas.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlumnosPage;
