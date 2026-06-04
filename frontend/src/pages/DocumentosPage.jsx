import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { documentosAPI } from '../services/api';

const MATERIAS_DISPONIBLES = [
  { id: 'matematicas', label: 'Matemática' },
  { id: 'lengua', label: 'Lengua' },
  { id: 'ciencias_naturales', label: 'Ciencias Naturales' },
  { id: 'ciencias_sociales', label: 'Ciencias Sociales' },
  { id: 'educacion_fisica', label: 'Educación Física' },
  { id: 'educacion_artistica', label: 'Educación Artística' },
  { id: 'tecnologia', label: 'Tecnología' },
  { id: 'ciudadania', label: 'Ciudadanía / ESI' },
];

const GRADOS_DISPONIBLES = ['1', '2', '3', '4', '5', '6'];

const DocumentosPage = ({ asignaciones }) => {
  const gradoDisplay = (grado) => {
    const map = { '-2': 'Sala de 4', '-1': 'Sala de 5', '1': '1°', '2': '2°', '3': '3°', '4': '4°', '5': '5°', '6': '6°' };
    return map[String(grado)] || `${grado}°`;
  }
  const { grado, division, materiaId } = useParams();
  const [documentos, setDocumentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Estados del formulario por pasos
  const [paso, setPaso] = useState(1); // 1: seleccionar archivo, 2: confirmar detección, 3: subiendo
  const [archivo, setArchivo] = useState(null);
  const [titulo, setTitulo] = useState('');
  const [tipo, setTipo] = useState('proyecto');
  const [analizando, setAnalizando] = useState(false);
  const [subiendo, setSubiendo] = useState(false);

  // Resultado del análisis
  // eslint-disable-next-line no-unused-vars
  const [tituloDetectado, setTituloDetectado] = useState('');
  const [materiasDetectadas, setMateriasDetectadas] = useState([]);
  const [materiasSeleccionadas, setMateriasSeleccionadas] = useState([]);
  const [gradosDetectados, setGradosDetectados] = useState([]);
  const [gradosSeleccionados, setGradosSeleccionados] = useState([]);
  const [todosLosGrados, setTodosLosGrados] = useState(false);

  const asignacionActual = asignaciones.find(
    a => a.grado === grado && a.division === division && a.materia_id === parseInt(materiaId)
  );

  useEffect(() => {
    const fetchDocumentos = async () => {
      if (asignacionActual) {
        setLoading(true);
        try {
          const response = await documentosAPI.getByAsignacion(asignacionActual.id);
          if (response.success) setDocumentos(response.documentos);
        } catch (err) {
          console.error('Error cargando documentos:', err);
        } finally {
          setLoading(false);
        }
      }
    };
    fetchDocumentos();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asignacionActual?.id]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['docx', 'pdf', 'xlsx'].includes(ext)) {
      setError('Formato no soportado. Use .docx, .pdf o .xlsx');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('El archivo es muy grande (máximo 5MB). Si tiene imágenes, intentá guardar el documento sin imágenes o comprimirlas.');
      return;
    }
    setArchivo(file);
    setTitulo(file.name.replace(/\.[^/.]+$/, ''));
    setError('');
  };

  const handleAnalizar = async () => {
    if (!archivo) { setError('Seleccioná un archivo'); return; }
    setAnalizando(true);
    setError('');
    try {
      const res = await documentosAPI.analizar(archivo);
      if (res.success) {
        setTituloDetectado(res.titulo_detectado || titulo);
        setTitulo(res.titulo_detectado || titulo);
        setMateriasDetectadas(res.materias_detectadas || []);
        setMateriasSeleccionadas(res.materias_detectadas || []);
        const gd = res.grados_detectados || [];
        setGradosDetectados(gd);
        if (gd.length === 6) {
          setTodosLosGrados(true);
          setGradosSeleccionados(GRADOS_DISPONIBLES);
        } else {
          setTodosLosGrados(false);
          setGradosSeleccionados(gd.length > 0 ? gd : [grado]);
        }
        setPaso(2);
      } else {
        setError(res.error || 'Error al analizar el archivo');
      }
    } catch (err) {
      setError('Error al analizar el archivo');
    } finally {
      setAnalizando(false);
    }
  };

  const toggleMateria = (id) => {
    setMateriasSeleccionadas(prev =>
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  };

  const toggleGrado = (g) => {
    if (todosLosGrados) return;
    setGradosSeleccionados(prev =>
      prev.includes(g) ? prev.filter(x => x !== g) : [...prev, g]
    );
  };

  const handleTodosLosGrados = (checked) => {
    setTodosLosGrados(checked);
    setGradosSeleccionados(checked ? GRADOS_DISPONIBLES : [grado]);
  };

  const handleSubir = async () => {
    if (!titulo.trim()) { setError('Ingresá un título'); return; }
    if (gradosSeleccionados.length === 0) { setError('Seleccioná al menos un grado'); return; }

    setSubiendo(true);
    setPaso(3);
    setError('');

    try {
      const gradoFinal = todosLosGrados ? 'todos' : gradosSeleccionados[0];
      const gradosLista = gradosSeleccionados.join(',');
      const materiasFinales = materiasSeleccionadas.join(',');

      const res = await documentosAPI.upload(
        titulo,
        tipo,
        '',
        asignacionActual?.id || null,
        archivo,
        gradoFinal,
        gradosLista,
        materiasFinales,
      );

      if (res.success) {
        if (res.documento.chunks_generados > 0) {
            setSuccessMsg(`✓ "${res.documento.titulo}" guardado correctamente. El asistente ya puede usarlo.`);
          } else {
            setError('El documento se guardó pero no se pudo procesar. Intentá subirlo de nuevo o contactá al administrador.');
          }
        resetForm();
        const docsRes = await documentosAPI.getByAsignacion(asignacionActual.id);
        if (docsRes.success) setDocumentos(docsRes.documentos);
      } else {
        setError(res.error || 'Error al subir');
        setPaso(2);
      }
    } catch (err) {
      setError('Error de conexión');
      setPaso(2);
    } finally {
      setSubiendo(false);
    }
  };

  const resetForm = () => {
    setPaso(1);
    setArchivo(null);
    setTitulo('');
    setTipo('proyecto');
    setTituloDetectado('');
    setMateriasDetectadas([]);
    setMateriasSeleccionadas([]);
    setGradosDetectados([]);
    setGradosSeleccionados([]);
    setTodosLosGrados(false);
    setShowForm(false);
    setError('');
  };

  const handleDelete = async (docId, docTitulo) => {
    if (!window.confirm(`¿Eliminar "${docTitulo}"? Esto también eliminará los datos del asistente.`)) return;
    try {
      const res = await documentosAPI.delete(docId);
      if (res.success) {
        setDocumentos(prev => prev.filter(d => d.id !== docId));
        setSuccessMsg('Documento eliminado');
      } else {
        setError(res.error || 'Error al eliminar');
      }
    } catch (err) {
      setError('Error de conexión');
    }
  };

  if (!asignacionActual) {
    return <div className="text-center py-12"><p className="text-gray-500">Asignación no encontrada</p></div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Mis Documentos - {gradoDisplay(grado)} {division}</h1>
          <p className="text-gray-600 mt-1">{asignacionActual.materia_nombre}</p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Subir Documento
          </button>
        )}
      </div>

      {/* Mensajes */}
      {error && <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}
      {successMsg && <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">{successMsg}</div>}

      {/* Formulario multi-paso */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">

          {/* Paso 1: Seleccionar archivo */}
          {paso === 1 && (
            <>
              <h2 className="text-lg font-semibold mb-4">Subir Documento — Paso 1 de 2</h2>
              <p className="text-sm text-gray-500 mb-4">
                Podés subir proyectos áulicos, proyectos institucionales o planificaciones anuales.
                El sistema detectará automáticamente a qué grados y materias aplica.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de documento</label>
                  <select
                    value={tipo}
                    onChange={e => setTipo(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="proyecto">Proyecto Áulico / Institucional</option>
                    <option value="planificacion_anual">Planificación Anual</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Archivo</label>
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-indigo-400 transition-colors">
                    <div className="space-y-1 text-center">
                      <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <label className="cursor-pointer text-indigo-600 hover:text-indigo-500 text-sm font-medium">
                        <span>Seleccionar archivo</span>
                        <input type="file" accept=".docx,.pdf,.xlsx" onChange={handleFileChange} className="sr-only" />
                      </label>
                      <p className="text-xs text-gray-500">.docx, .pdf o .xlsx</p>
                      {archivo && <p className="text-sm text-indigo-600 font-medium mt-2">📎 {archivo.name}</p>}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button onClick={resetForm} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">Cancelar</button>
                <button
                  onClick={handleAnalizar}
                  disabled={!archivo || analizando}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {analizando ? (
                    <>
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Analizando...
                    </>
                  ) : 'Analizar documento →'}
                </button>
              </div>
            </>
          )}

          {/* Paso 2: Confirmar detección */}
          {paso === 2 && (
            <>
              <h2 className="text-lg font-semibold mb-1">Confirmá los datos detectados — Paso 2 de 2</h2>
              <p className="text-sm text-gray-500 mb-5">
                El sistema analizó el documento. Revisá y corregí si es necesario antes de guardar.
              </p>

              <div className="space-y-5">
                {/* Título */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Título del documento</label>
                  <input
                    type="text"
                    value={titulo}
                    onChange={e => setTitulo(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                {/* Grados */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ¿A qué grados aplica este documento?
                    {gradosDetectados.length > 0 && (
                      <span className="ml-2 text-xs text-indigo-500 font-normal">
                        (Detectados: {gradosDetectados.join(', ')}°)
                      </span>
                    )}
                  </label>
                  <div className="flex items-center gap-2 mb-3">
                    <input
                      type="checkbox"
                      id="todosGrados"
                      checked={todosLosGrados}
                      onChange={e => handleTodosLosGrados(e.target.checked)}
                      className="w-4 h-4 text-indigo-600"
                    />
                    <label htmlFor="todosGrados" className="text-sm text-gray-700">Todos los grados (1° a 6°)</label>
                  </div>
                  {!todosLosGrados && (
                    <div className="flex flex-wrap gap-2">
                      {GRADOS_DISPONIBLES.map(g => (
                        <button
                          key={g}
                          type="button"
                          onClick={() => toggleGrado(g)}
                          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                            gradosSeleccionados.includes(g)
                              ? 'bg-indigo-600 text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {g}°
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Materias */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ¿Qué materias cubre este documento?
                    {materiasDetectadas.length > 0 && (
                      <span className="ml-2 text-xs text-indigo-500 font-normal">
                        (Detectadas automáticamente)
                      </span>
                    )}
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {MATERIAS_DISPONIBLES.map(m => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => toggleMateria(m.id)}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                          materiasSeleccionadas.includes(m.id)
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Podés seleccionar varias materias — el asistente usará este documento como contexto para todas ellas.
                  </p>
                </div>
              </div>

              <div className="flex justify-between mt-6">
                <button onClick={() => setPaso(1)} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
                  ← Volver
                </button>
                <div className="flex gap-3">
                  <button onClick={resetForm} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">Cancelar</button>
                  <button
                    onClick={handleSubir}
                    disabled={subiendo || gradosSeleccionados.length === 0}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Guardar y procesar
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Paso 3: Subiendo */}
          {paso === 3 && (
            <div className="py-8 text-center">
              <svg className="animate-spin h-10 w-10 text-indigo-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-gray-600 font-medium">Procesando documento...</p>
              <p className="text-sm text-gray-400 mt-1">Esto puede tardar unos segundos</p>
            </div>
          )}
        </div>
      )}

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="ml-3 text-sm text-blue-800">
            <strong>¿Para qué sirve?</strong> Los documentos que subas serán analizados por el asistente IA
            para generar planificaciones y actividades alineadas con tus proyectos e interrelacionadas entre materias.
          </p>
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
          <p className="text-gray-500 mb-4">Subí tus proyectos y planificaciones para que el asistente pueda ayudarte mejor.</p>
          <button onClick={() => setShowForm(true)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
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
                  <div className="flex items-center gap-3 text-sm text-gray-500 flex-wrap">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      doc.tipo === 'proyecto' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'
                    }`}>
                      {doc.tipo_display}
                    </span>
                    <span>📎 {doc.archivo_nombre}</span>
                    {doc.procesado && <span className="text-green-600">✓ {doc.chunks_generados} fragmentos</span>}
                    {doc.materias_detectadas && (
                      <span className="text-indigo-500 text-xs">{doc.materias_detectadas.split(',').join(', ')}</span>
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
