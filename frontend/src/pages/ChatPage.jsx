import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { iaAPI, alumnosAPI } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// ─────────────────────────────────────────────────────────────────────────────
// ExportOption — fila del menú dropdown
// ─────────────────────────────────────────────────────────────────────────────
const ExportOption = ({ emoji, label, sublabel, badgeStyle, hoverBg, onClick }) => {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        width: '100%',
        padding: '10px 14px',
        border: 'none',
        background: hovered ? hoverBg : 'white',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'background 0.12s ease',
      }}
    >
      <div style={{
        width: 34, height: 34, borderRadius: 9,
        background: badgeStyle.bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 17, flexShrink: 0,
      }}>
        {emoji}
      </div>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 2 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#1f2937' }}>{label}</span>
          <span style={{
            background: badgeStyle.bg, color: badgeStyle.text,
            fontSize: 9, fontWeight: 700, letterSpacing: '0.08em',
            padding: '2px 5px', borderRadius: 4, fontFamily: 'monospace',
          }}>
            {label.toUpperCase()}
          </span>
        </div>
        <span style={{ fontSize: 11, color: '#9ca3af' }}>{sublabel}</span>
      </div>
    </button>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// ExportDropdown — botón "Descargar" + menú con animación
// ─────────────────────────────────────────────────────────────────────────────
const ExportDropdown = ({ messageId, exportando, onExport }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const isDownloading = exportando?.id === messageId;

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (fmt) => {
    setOpen(false);
    onExport(messageId, fmt);
  };

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <style>{`
        @keyframes exportPopIn {
          from { opacity: 0; transform: scale(0.9) translateY(6px); }
          to   { opacity: 1; transform: scale(1)   translateY(0);   }
        }
        @keyframes exportSpin {
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* Botón principal */}
      <button
        onClick={() => !isDownloading && setOpen((o) => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 12px', borderRadius: 10,
          border: '1.5px solid',
          fontSize: 12, fontWeight: 600,
          cursor: isDownloading ? 'default' : 'pointer',
          transition: 'all 0.15s ease',
          background: open ? 'linear-gradient(135deg, #4338ca, #6366f1)' : 'white',
          borderColor: open ? 'transparent' : '#c7d2fe',
          color: open ? 'white' : '#4f46e5',
          boxShadow: open
            ? '0 4px 14px rgba(79,70,229,0.3)'
            : '0 1px 3px rgba(0,0,0,0.07)',
          letterSpacing: '0.01em',
          userSelect: 'none',
        }}
      >
        {/* Ícono izquierdo */}
        {isDownloading ? (
          <svg style={{ animation: 'exportSpin 0.7s linear infinite', flexShrink: 0 }}
            width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M21 12a9 9 0 11-6.219-8.56" />
          </svg>
        ) : (
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        )}

        <span>
          {isDownloading
            ? `Descargando ${exportando.formato.toUpperCase()}…`
            : 'Descargar'}
        </span>

        {!isDownloading && (
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.8" strokeLinecap="round"
            style={{
              transition: 'transform 0.2s ease',
              transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
              flexShrink: 0,
            }}>
            <polyline points="6 9 12 15 18 9" />
          </svg>
        )}
      </button>

      {/* Menú desplegable */}
      {open && (
        <div style={{
          position: 'absolute', right: 0, bottom: 'calc(100% + 10px)',
          width: 210,
          background: 'white',
          borderRadius: 14,
          border: '1.5px solid #e0e7ff',
          boxShadow: '0 12px 40px rgba(79,70,229,0.14), 0 2px 8px rgba(0,0,0,0.08)',
          overflow: 'hidden',
          zIndex: 50,
          animation: 'exportPopIn 0.18s cubic-bezier(0.34,1.56,0.64,1)',
        }}>
          <div style={{
            padding: '8px 14px 6px',
            fontSize: 10, fontWeight: 700,
            letterSpacing: '0.1em', textTransform: 'uppercase',
            color: '#a5b4fc', borderBottom: '1px solid #f0f0ff',
          }}>
            Elegí el formato
          </div>

          <ExportOption
            emoji="📄"
            label="PDF"
            sublabel="Listo para imprimir"
            badgeStyle={{ bg: '#fee2e2', text: '#dc2626' }}
            hoverBg="#fff8f8"
            onClick={() => handleSelect('pdf')}
          />

          <div style={{ height: 1, background: '#f5f5ff', margin: '0 12px' }} />

          <ExportOption
            emoji="📝"
            label="Word"
            sublabel="Editable en Word"
            badgeStyle={{ bg: '#dbeafe', text: '#2563eb' }}
            hoverBg="#f0f6ff"
            onClick={() => handleSelect('docx')}
          />
        </div>
      )}
    </div>
  );
};

const ChatInput = React.memo(({ onSubmit, isLoading }) => {
  const [value, setValue] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim() || isLoading) return;
    onSubmit(value.trim());
    setValue('');
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white border-t border-gray-200 p-4">
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Escribí tu consulta..."
          disabled={isLoading}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-50"
        />
        <button
          type="submit"
          disabled={isLoading || !value.trim()}
          className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </form>
  );
});
// ─────────────────────────────────────────────────────────────────────────────
// ChatPage principal
// ─────────────────────────────────────────────────────────────────────────────
const ChatPage = ({ asignaciones }) => {
  const { grado, division, materiaId } = useParams();
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingHistorial, setLoadingHistorial] = useState(true);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [exportando, setExportando] = useState(null);
  const [feedbackOpen, setFeedbackOpen] = useState(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [savingFeedback, setSavingFeedback] = useState(false);
  const messagesEndRef = useRef(null);

  const asignacionActual = asignaciones.find(
    (a) =>
      a.grado === grado &&
      a.division === division &&
      a.materia_id === parseInt(materiaId)
  );

  // Definida con useCallback para poder usarla como dependencia del useEffect
  const getAlumnos = React.useCallback(async () => {
    try {
      const response = await alumnosAPI.getByAsignacion(grado, division);
      if (response.success) {
        return response.alumnos.map((a) => ({
          nombre: a.nombre,
          apellido: a.apellido,
          nivel: a.niveles?.[materiaId]?.nivel || 'LE',
          nota_contextual: a.niveles?.[materiaId]?.nota_contextual || '',
        }));
      }
    } catch (err) {
      console.error('Error fetching alumnos:', err);
    }
    return [];
  }, [grado, division, materiaId]);

  // Cargar historial
  useEffect(() => {
    if (!asignacionActual) return;
    const fetchHistorial = async () => {
      setLoadingHistorial(true);
      try {
        const response = await iaAPI.getHistorial(asignacionActual.id);
        if (response.success && response.historial.length > 0) {
          setMessages(response.historial);
        } else {
          const alumnos = await getAlumnos();
          const nee = alumnos.filter((a) => a.nivel === 'NEE').length;
          const lp  = alumnos.filter((a) => a.nivel === 'LP').length;
          const le  = alumnos.filter((a) => a.nivel === 'LE').length;
          setMessages([{
            role: 'assistant',
            content: `¡Hola! Soy tu asistente de planificación para **${grado}° ${division} - ${asignacionActual.materia_nombre}**.

${alumnos.length > 0
  ? `Tenés ${alumnos.length} alumnos cargados: **${nee} NEE**, **${lp} LP** y **${le} LE**.`
  : 'Todavía no cargaste alumnos. Te recomiendo hacerlo para que pueda personalizar mejor las planificaciones.'}

¿En qué puedo ayudarte? Podés pedirme:
- 📋 **Planificaciones** diferenciadas por nivel
- 🎯 **Actividades** adaptadas para cada grupo
- 📚 **Consultas** sobre la currícula
- ✏️ **Adaptaciones** de contenidos existentes`,
          }]);
        }
      } catch (err) {
        console.error('Error cargando historial:', err);
      } finally {
        setLoadingHistorial(false);
      }
    };
    fetchHistorial();
  }, [asignacionActual, getAlumnos, grado, division]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Exportar ────────────────────────────────────────────────────────────────
  const handleExport = async (planificacionId, formato) => {
    setExportando({ id: planificacionId, formato });
    try {
      const { blob, filename } = await iaAPI.exportar(planificacionId, formato);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exportando:', err);
    } finally {
      setExportando(null);
    }
  };

  // ── Copiar ──────────────────────────────────────────────────────────────────
  const handleCopy = async (content, index) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Error copying:', err);
    }
  };

  // ── Feedback ────────────────────────────────────────────────────────────────
  const handleFeedbackPositive = async (planificacionId) => {
    try {
      await iaAPI.guardarFeedback(planificacionId, true, '');
      setMessages((prev) =>
        prev.map((m) => (m.id === planificacionId ? { ...m, fue_util: true } : m))
      );
    } catch (err) {
      console.error('Error guardando feedback:', err);
    }
  };

  const handleFeedbackNegativeOpen = (id) => {
    setFeedbackOpen(id);
    setFeedbackText('');
  };

  const handleFeedbackNegativeSubmit = async (planificacionId) => {
    setSavingFeedback(true);
    try {
      await iaAPI.guardarFeedback(planificacionId, false, feedbackText);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === planificacionId
            ? { ...m, fue_util: false, feedback: feedbackText }
            : m
        )
      );
      setFeedbackOpen(null);
      setFeedbackText('');
    } catch (err) {
      console.error('Error guardando feedback:', err);
    } finally {
      setSavingFeedback(false);
    }
  };

  const handleFeedbackCancel = () => {
    setFeedbackOpen(null);
    setFeedbackText('');
  };

  // ── Enviar consulta ─────────────────────────────────────────────────────────
  const handleSubmit = async (userMessage) => {
    if (!userMessage || isLoading) return;
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);
    try {
      const alumnos = await getAlumnos();

      // Construir historial para Gemini con ventana deslizante
      // El backend se encarga de comprimir si supera el umbral,
      // pero desde el frontend ya mandamos máximo 20 para no enviar payloads enormes.
      const VENTANA_FRONTEND = 20;
      const todosLosMensajes = messages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .filter((m) => !m.isError && m.content)
        .map((m) => ({ role: m.role, content: m.content, es_resumen: m.es_resumen || false }));

      // Separar resumen (siempre va primero si existe) + últimos VENTANA_FRONTEND mensajes normales
      const resumen = todosLosMensajes.find((m) => m.es_resumen);
      const normales = todosLosMensajes.filter((m) => !m.es_resumen).slice(-VENTANA_FRONTEND);
      const historialParaApi = resumen ? [resumen, ...normales] : normales;

      const response = await iaAPI.consultar(
        userMessage, grado, division,
        asignacionActual?.materia_nombre || '',
        alumnos, asignacionActual?.id,
        historialParaApi
      );
      if (response.success) {
        setMessages((prev) => [...prev, {
          id: response.planificacion_id,
          role: 'assistant',
          content: response.respuesta,
          tipo: response.tipo_consulta,
          contexto: response.contexto_utilizado,
          fue_util: null,
        }]);
      } else {
        throw new Error(response.error || 'Error al procesar la consulta');
      }
    } catch (error) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `Lo siento, ocurrió un error: ${error.message}. Por favor, intentá de nuevo.`,
        isError: true,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sugerencias = [
    'Necesito una planificación para trabajar fracciones',
    '¿Qué contenidos debo dar este mes?',
    'Dame actividades diferenciadas para mi clase',
    '¿Cómo adapto esta actividad para alumnos NEE?',
  ];

  // ── Guards ──────────────────────────────────────────────────────────────────
  if (!asignacionActual) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Asignación no encontrada</p>
      </div>
    );
  }

  if (loadingHistorial) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center">
          <svg className="animate-spin h-8 w-8 text-indigo-600 mx-auto mb-4"
            fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10"
              stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">Cargando conversación...</p>
        </div>
      </div>
    );
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Asistente IA — {grado}° {division}
          </h1>
          <p className="text-sm text-gray-500">{asignacionActual.materia_nombre}</p>
        </div>
        <div className="flex items-center text-sm text-gray-500">
          <span className="w-2 h-2 bg-green-500 rounded-full mr-2" />
          Conectado
        </div>
      </div>

      {/* Lista de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-4xl rounded-2xl px-5 py-4 ${
              message.role === 'user'
                ? 'bg-indigo-600 text-white'
                : message.isError
                ? 'bg-red-50 border border-red-200 text-red-800'
                : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
            }`}>

              {message.role === 'assistant' ? (
                <div className="relative">

                  {/* Botón copiar */}
                  <button
                    onClick={() => handleCopy(message.content, index)}
                    className="absolute top-0 right-0 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    title="Copiar"
                  >
                    {copiedIndex === index ? (
                      <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    )}
                  </button>

                  {/* Contenido Markdown */}
                  <div className="prose prose-sm max-w-none pr-8 break-words" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        table: ({ node, ...props }) => (
                          <div className="overflow-x-auto my-4 rounded-lg border border-gray-200">
                            <table className="min-w-full divide-y divide-gray-200" {...props} />
                          </div>
                        ),
                        thead: ({ node, ...props }) => <thead className="bg-gray-50" {...props} />,
                        th: ({ node, ...props }) => (
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-b" {...props} />
                        ),
                        td: ({ node, ...props }) => (
                          <td className="px-4 py-3 text-sm text-gray-700 border-b border-gray-100" {...props} />
                        ),
                        tr: ({ node, ...props }) => <tr className="hover:bg-gray-50" {...props} />,
                        h1: ({ node, children, ...props }) => (
                          <h1 className="text-xl font-bold text-gray-900 mt-6 mb-3 pb-2 border-b border-gray-200" {...props}>{children}</h1>
                        ),
                        h2: ({ node, children, ...props }) => (
                          <h2 className="text-lg font-bold text-gray-900 mt-6 mb-3" {...props}>{children}</h2>
                        ),
                        h3: ({ node, children, ...props }) => (
                          <h3 className="text-base font-semibold text-gray-800 mt-5 mb-2" {...props}>{children}</h3>
                        ),
                        hr: ({ node, ...props }) => <hr className="my-6 border-t-2 border-indigo-200" {...props} />,
                        strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
                        ul: ({ node, ...props }) => <ul className="list-disc list-outside ml-5 space-y-1 my-3" {...props} />,
                        ol: ({ node, ...props }) => <ol className="list-decimal list-outside ml-5 space-y-1 my-3" {...props} />,
                        li: ({ node, ...props }) => <li className="text-gray-700" {...props} />,
                        p:  ({ node, ...props }) => <p className="my-2 text-gray-700 leading-relaxed" {...props} />,
                        code: ({ node, inline, ...props }) =>
                          inline
                            ? <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-indigo-600" {...props} />
                            : <code className="block bg-gray-100 p-3 rounded-lg text-sm font-mono overflow-x-auto" {...props} />,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>

                  {/* ── Barra inferior: feedback + exportar ── */}
                  {message.id && !message.isError && (
                    <div className="mt-4 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between flex-wrap gap-3">

                        {/* Feedback — izquierda */}
                        <div className="flex items-center gap-2">
                          {message.fue_util !== null && message.fue_util !== undefined ? (
                            <div>
                              {message.fue_util ? (
                                <span className="text-green-600 flex items-center gap-1 text-sm">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  </svg>
                                  ¡Gracias por tu feedback!
                                </span>
                              ) : (
                                <div>
                                  <span className="text-orange-600 flex items-center gap-1 text-sm">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Feedback recibido
                                  </span>
                                  {message.feedback && (
                                    <p className="mt-1 text-gray-500 italic text-xs">"{message.feedback}"/</p>
                                  )}
                                </div>
                              )}
                            </div>
                          ) : feedbackOpen === message.id ? (
                            <div className="space-y-3">
                              <p className="text-sm text-gray-600">¿Qué podríamos mejorar?</p>
                              <textarea
                                value={feedbackText}
                                onChange={(e) => setFeedbackText(e.target.value)}
                                placeholder="Ej: Las actividades para NEE son muy complejas..."
                                rows={3}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleFeedbackNegativeSubmit(message.id)}
                                  disabled={savingFeedback}
                                  className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                                >
                                  {savingFeedback ? 'Enviando...' : 'Enviar feedback'}
                                </button>
                                <button
                                  onClick={handleFeedbackCancel}
                                  className="px-4 py-2 text-gray-600 text-sm hover:bg-gray-100 rounded-lg"
                                >
                                  Cancelar
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-400 font-medium">¿Te fue útil?</span>
                              <button
                                onClick={() => handleFeedbackPositive(message.id)}
                                className="p-1.5 rounded-lg text-gray-400 hover:text-green-600 hover:bg-green-50 transition-colors"
                                title="Sí, útil"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                    d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleFeedbackNegativeOpen(message.id)}
                                className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                                title="No, mejorable"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                    d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                                </svg>
                              </button>
                            </div>
                          )}
                        </div>

                        {/* Descarga — derecha, SIEMPRE visible */}
                        <div className="flex items-center gap-2 flex-wrap">
                          {message.contexto && message.contexto.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {message.contexto.slice(0, 3).map((ctx, i) => (
                                <span key={i} className="text-xs bg-indigo-50 text-indigo-500 px-2 py-0.5 rounded-full font-medium">
                                  {ctx.fuente}
                                </span>
                              ))}
                            </div>
                          )}
                          <ExportDropdown
                            messageId={message.id}
                            exportando={exportando}
                            onExport={handleExport}
                          />
                        </div>

                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p>{message.content}</p>
              )}
            </div>
          </div>
        ))}

        {/* Loading dots */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-5 py-4 shadow-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                <span className="ml-2 text-sm text-gray-500">Generando planificación...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Sugerencias */}
      {messages.length <= 1 && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-2">💡 Sugerencias:</p>
          <div className="flex flex-wrap gap-2">
            {sugerencias.map((sug, i) => (
              <button
                key={i}
                onClick={() => handleSubmit(sug)}
                className="text-sm px-3 py-1.5 bg-white border border-gray-200 rounded-full hover:bg-indigo-50 hover:border-indigo-200 text-gray-700 transition-colors"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  );
};

export default ChatPage;
