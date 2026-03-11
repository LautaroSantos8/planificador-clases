import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { documentosAPI } from '../services/api';

const DocumentosPage = ({ asignaciones }) => {
  const { grado, division, materiaId } = useParams();
  const [documentos, setDocumentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [formData, setFormData] = useState({
    titulo: '',
    tipo: 'proyecto',
    descripcion: '',
    archivo: null,
  });

  // Encontrar la asignación actual
  const asignacionActual = asignaciones.find(
    a => a.grado === grado && a.division === division && a.materia_id === parseInt(materiaId)
  );

  // Cargar documentos
  useEffect(() => {
    const fetchDocumentos = async () => {
      if (asignacionActual) {
        setLoading(true);
        try {
          const response = await documentosAPI.getByAsignacion(asignacionActual.id);
          if (response.success) {
            setDocumentos(response.documentos);
          }
        } catch (err) {
          console.error('Error cargando documentos:', err);
        } finally {
          setLoading(false);
        }
      }
    };
    fetchDocumentos();
  }, [asignacionActual?.id]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const extension = file.name.split('.').pop().toLowerCase();
      if (!['docx', 'pdf', 'xlsx'].includes(extension)) {
        setError('Formato no soportado. Use .docx, .pdf o .xlsx');
        return;
      }
      setFormData({ ...formData, archivo: file });
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    
    if (!formData.archivo) {
      setError('Seleccioná un archivo');
      return;
    }

    setUploading(true);

    try {
      const response = await documentosAPI.upload(
        formData.titulo,
        formData.tipo,
        formData.descripcion,
        asignacionActual.id,
        formData.archivo
      );

      if (response.success) {
        setSuccessMsg(`Documento "${response.documento.titulo}" subido correctamente. Se generaron ${response.documento.chunks_generados} fragmentos para el asistente.`);
        setFormData({ titulo: '', tipo: 'proyecto', descripcion: '', archivo: null });
        setShowForm(false);
        // Recargar documentos
        const docsResponse = await documentosAPI.getByAsignacion(asignacionActual.id);
        if (docsResponse.success) {
          setDocumentos(docsResponse.documentos);
        }
      } else {
        setError(response.error || 'Error al subir documento');
      }
    } catch (err) {
      setError('Error de conexión');
      console.error('Error uploading:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId, titulo) => {
    if (!window.confirm(`¿Eliminar "${titulo}"? Esto también eliminará los datos del asistente.`)) {
      return;
    }

    try {
      const response = await documentosAPI.delete(docId);
      if (response.success) {
        setDocumentos(prev => prev.filter(d => d.id !== docId));
        setSuccessMsg('Documento eliminado');
      } else {
        setError(response.error || 'Error al eliminar');
      }
    } catch (err) {
      setError('Error de conexión');
    }
  };

  if (!asignacionActual) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Asignación no encontrada</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Mis Documentos - {grado}° {division}
          </h1>
          <p className="text-gray-600 mt-1">{asignacionActual.materia_nombre}</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Subir Documento
        </button>
      </div>

      {/* Mensajes */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          {successMsg}
        </div>
      )}

      {/* Formulario de subida */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Subir Documento</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
                <input
                  type="text"
                  value={formData.titulo}
                  onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                  required
                  placeholder="Ej: Proyecto Bosque Nativo 2025"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                <select
                  value={formData.tipo}
                  onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="proyecto">Proyecto Áulico</option>
                  <option value="planificacion_anual">Planificación Anual</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descripción (opcional)</label>
              <textarea
                value={formData.descripcion}
                onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                rows={2}
                placeholder="Breve descripción del documento..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Archivo</label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-indigo-400 transition-colors">
                <div className="space-y-1 text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div className="flex text-sm text-gray-600">
                    <label className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500">
                      <span>Seleccionar archivo</span>
                      <input
                        type="file"
                        accept=".docx,.pdf,.xlsx"
                        onChange={handleFileChange}
                        className="sr-only"
                      />
                    </label>
                  </div>
                  <p className="text-xs text-gray-500">.docx, .pdf o .xlsx</p>
                  {formData.archivo && (
                    <p className="text-sm text-indigo-600 font-medium mt-2">
                      📎 {formData.archivo.name}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={uploading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
              >
                {uploading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Procesando...
                  </>
                ) : (
                  'Subir y Procesar'
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="ml-3">
            <p className="text-sm text-blue-800">
              <strong>¿Para qué sirve?</strong> Los documentos que subas serán analizados por el asistente IA 
              para generar planificaciones alineadas con tu proyecto áulico y planificación anual.
            </p>
          </div>
        </div>
      </div>

      {/* Lista de documentos */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <svg className="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      ) : documentos.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Sin documentos</h3>
          <p className="text-gray-500 mb-4">
            Subí tu proyecto áulico o planificación anual para que el asistente pueda ayudarte mejor.
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Subir Primer Documento
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {documentos.map((doc) => (
            <div key={doc.id} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  doc.tipo === 'proyecto' ? 'bg-purple-100' : 'bg-green-100'
                }`}>
                  {doc.tipo === 'proyecto' ? (
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{doc.titulo}</h3>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      doc.tipo === 'proyecto' 
                        ? 'bg-purple-100 text-purple-700' 
                        : 'bg-green-100 text-green-700'
                    }`}>
                      {doc.tipo_display}
                    </span>
                    <span>📎 {doc.archivo_nombre}</span>
                    {doc.procesado && (
                      <span className="text-green-600">✓ {doc.chunks_generados} fragmentos</span>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={() => handleDelete(doc.id, doc.titulo)}
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

export default DocumentosPage;
