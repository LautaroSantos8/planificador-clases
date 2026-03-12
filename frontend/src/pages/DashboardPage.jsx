import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { iaAPI, planificacionAPI } from '../services/api';

// ── Stat card simple ──────────────────────────────────────────────────────────
const StatCard = ({ icon, label, value, color, sublabel }) => (
  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex items-center gap-4">
    <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
      {icon}
    </div>
    <div>
      <p className="text-2xl font-bold text-gray-900">{value ?? '—'}</p>
      <p className="text-sm text-gray-500">{label}</p>
      {sublabel && <p className="text-xs text-gray-400 mt-0.5">{sublabel}</p>}
    </div>
  </div>
);

// ── Barra de nivel ────────────────────────────────────────────────────────────
const NivelBar = ({ label, count, total, color, bg }) => {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${bg} ${color}`}>{label}</span>
          <span className="text-sm text-gray-600">{count} alumnos</span>
        </div>
        <span className="text-sm font-semibold text-gray-700">{pct}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color.replace('text-', 'bg-')}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

// ── Indicador de feedback ─────────────────────────────────────────────────────
const FeedbackMeter = ({ positivo, negativo }) => {
  const total = positivo + negativo;
  const pct = total > 0 ? Math.round((positivo / total) * 100) : null;
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden flex">
        {total > 0 ? (
          <>
            <div className="h-full bg-green-400 rounded-l-full transition-all duration-700"
              style={{ width: `${pct}%` }} />
            <div className="h-full bg-red-300 rounded-r-full transition-all duration-700"
              style={{ width: `${100 - pct}%` }} />
          </>
        ) : (
          <div className="h-full w-full bg-gray-200 rounded-full" />
        )}
      </div>
      <span className="text-sm font-semibold text-gray-700 w-10 text-right">
        {pct !== null ? `${pct}%` : '—'}
      </span>
    </div>
  );
};

// ── Componente principal ──────────────────────────────────────────────────────
const DashboardPage = ({ asignaciones = [] }) => {
  const { docente } = useAuth();
  const [statsIA, setStatsIA] = useState(null);
  const [statsDocente, setStatsDocente] = useState(null);
  const [loading, setLoading] = useState(true);
  const [asignacionSeleccionada, setAsignacionSeleccionada] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [resIA, resDocente] = await Promise.all([
          iaAPI.getEstadisticas().catch(() => null),
          planificacionAPI.getEstadisticasDocente().catch(() => null),
        ]);
        if (resIA?.success) setStatsIA(resIA.estadisticas);
        if (resDocente?.success) setStatsDocente(resDocente.estadisticas);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const totalAsignaciones = asignaciones.length;
  const gradosUnicos = [...new Set(asignaciones.map((a) => `${a.grado}${a.division}`))].length;
  const materiasUnicas = [...new Set(asignaciones.map((a) => a.materia_nombre))].length;

  // Seleccionar primera asignación por defecto cuando llegan los datos
  const nivelesData = statsDocente?.niveles_por_asignacion ?? [];
  const asignacionActiva = asignacionSeleccionada
    ? nivelesData.find(a => a.asignacion_id === asignacionSeleccionada) ?? nivelesData[0]
    : nivelesData[0];
  const nivelesActivos = asignacionActiva?.niveles ?? statsDocente?.niveles ?? { NEE: 0, LP: 0, LE: 0 };
  const totalNiveles = (nivelesActivos.NEE ?? 0) + (nivelesActivos.LP ?? 0) + (nivelesActivos.LE ?? 0);

  const hora = new Date().getHours();
  const saludo = hora < 12 ? 'Buenos días' : hora < 19 ? 'Buenas tardes' : 'Buenas noches';

  return (
    <div className="max-w-5xl">

      {/* Saludo */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          {saludo}, {docente?.first_name || 'Docente'} 👋
        </h1>
        <p className="text-gray-500 mt-1">
          Bienvenido/a al Planificador Docente · Escuela Dr. Jorge Orgaz
        </p>
      </div>

      {/* ── Fila 1: resumen de asignaciones ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard
          color="bg-indigo-100"
          label="Asignaciones activas"
          value={totalAsignaciones}
          icon={
            <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          }
        />
        <StatCard
          color="bg-green-100"
          label="Grados / Divisiones"
          value={gradosUnicos}
          icon={
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          }
        />
        <StatCard
          color="bg-purple-100"
          label="Materias"
          value={materiasUnicas}
          icon={
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
        />
      </div>

      {/* ── Fila 2: stats personales ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

        {/* Niveles de alumnos */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Mis alumnos por nivel</h2>
            {statsDocente && (
              <span className="text-sm text-gray-500 font-medium">
                {totalNiveles} registrados
              </span>
            )}
          </div>
          {nivelesData.length > 1 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {nivelesData.map((a) => (
                <button
                  key={a.asignacion_id}
                  onClick={() => setAsignacionSeleccionada(a.asignacion_id)}
                  className={"text-xs px-3 py-1 rounded-full border transition-colors " + (
                    (asignacionActiva?.asignacion_id === a.asignacion_id)
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-600 border-gray-300 hover:border-indigo-400"
                  )}
                >
                  {a.label}
                </button>
              ))}
            </div>
          )}

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-8 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : totalNiveles === 0 ? (
            <div className="text-center py-6">
              <p className="text-gray-400 text-sm">Todavía no hay alumnos cargados</p>
              <p className="text-gray-400 text-xs mt-1">Andá a una asignación para agregar alumnos</p>
            </div>
          ) : (
            <div className="space-y-4">
              <NivelBar
                label="NEE" count={nivelesActivos.NEE ?? 0}
                total={totalNiveles} color="text-red-600" bg="bg-red-100"
              />
              <NivelBar
                label="LP" count={nivelesActivos.LP ?? 0}
                total={totalNiveles} color="text-yellow-600" bg="bg-yellow-100"
              />
              <NivelBar
                label="LE" count={nivelesActivos.LE ?? 0}
                total={totalNiveles} color="text-green-600" bg="bg-green-100"
              />
            </div>
          )}
        </div>

        {/* Actividad del asistente IA */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Mi actividad con el asistente</h2>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-8 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Planificaciones generadas */}
              <div className="flex items-center justify-between py-2 border-b border-gray-50">
                <span className="text-sm text-gray-600 flex items-center gap-2">
                  <span className="text-base">📋</span> Planificaciones generadas
                </span>
                <span className="text-lg font-bold text-indigo-600">
                  {statsDocente?.planificaciones_generadas ?? '—'}
                </span>
              </div>

              {/* Documentos subidos */}
              <div className="flex items-center justify-between py-2 border-b border-gray-50">
                <span className="text-sm text-gray-600 flex items-center gap-2">
                  <span className="text-base">📎</span> Documentos subidos
                </span>
                <span className="text-lg font-bold text-indigo-600">
                  {statsDocente?.documentos_subidos ?? '—'}
                </span>
              </div>

              {/* Feedback */}
              <div className="py-2 border-b border-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <span className="text-base">👍</span> Satisfacción con el asistente
                  </span>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <span className="text-green-500">+{statsDocente?.feedback_positivo ?? 0}</span>
                    <span>/</span>
                    <span className="text-red-400">-{statsDocente?.feedback_negativo ?? 0}</span>
                  </div>
                </div>
                <FeedbackMeter
                  positivo={statsDocente?.feedback_positivo ?? 0}
                  negativo={statsDocente?.feedback_negativo ?? 0}
                />
              </div>

              {/* Última planificación */}
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-gray-600 flex items-center gap-2">
                  <span className="text-base">🕐</span> Última planificación
                </span>
                <span className="text-sm font-medium text-gray-700">
                  {statsDocente?.ultima_planificacion ?? 'Nunca'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Estado del sistema (ChromaDB) ── */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Base de conocimiento del asistente</h2>
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : statsIA ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'NAP Nacional', value: statsIA.curricula_nacional },
              { label: 'Currícula Provincial', value: statsIA.curricula_provincial },
              { label: 'Actualizaciones', value: statsIA.actualizaciones_municipal },
              { label: 'Proyectos docentes', value: statsIA.proyectos_docentes },
            ].map(({ label, value }) => (
              <div key={label} className="text-center p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-indigo-600">{value ?? '—'}</p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-red-500 text-sm">No se pudo conectar con el asistente</p>
        )}
      </div>

      {/* ── Guía rápida ── */}
      {totalAsignaciones === 0 && (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
          <h2 className="text-base font-semibold mb-3">¿Cómo empezar?</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { n: 1, title: 'Configurá tus asignaciones', sub: 'Grado, división y materias que das' },
              { n: 2, title: 'Cargá tus alumnos', sub: 'Y asigná su nivel (NEE, LP, LE)' },
              { n: 3, title: 'Usá el asistente', sub: 'Pedí planificaciones diferenciadas' },
            ].map(({ n, title, sub }) => (
              <div key={n} className="flex items-start gap-3">
                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="font-bold text-sm">{n}</span>
                </div>
                <div>
                  <p className="font-medium text-sm">{title}</p>
                  <p className="text-xs text-white/75 mt-0.5">{sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
