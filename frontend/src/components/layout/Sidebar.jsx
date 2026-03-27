import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar = ({ asignaciones, loading }) => {
  // Agrupar asignaciones por grado-división
  const grupos = {};
  asignaciones.forEach(a => {
    const key = `${a.grado}° ${a.division}`;
    if (!grupos[key]) grupos[key] = [];
    grupos[key].push(a);
  });

  return (
    <aside className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-white border-r border-gray-200 overflow-y-auto">
      <nav className="p-4">
        {/* Links principales */}
        <div className="space-y-1 mb-6">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'
              }`
            }
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Inicio
          </NavLink>

          <NavLink
            to="/configuracion"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'
              }`
            }
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Mis Asignaciones
          </NavLink>
        </div>

        {/* Asignaciones por grado */}
        {loading ? (
          <div className="px-3 py-4 text-sm text-gray-500">Cargando asignaciones...</div>
        ) : Object.keys(grupos).length === 0 ? (
          <div className="px-3 py-4">
            <NavLink
              to="/configuracion"
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Configurá tus asignaciones para comenzar
            </NavLink>
          </div>
        ) : (
          Object.entries(grupos).map(([grupo, materias]) => (
            <div key={grupo} className="mb-5">
              {/* Título del grado */}
              <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                {grupo}
              </h3>

              <div className="space-y-0.5">
                {/* Documentos — UNO por grado/división */}
                <NavLink
                  to={`/documentos/${materias[0].grado}/${materias[0].division}/${materias[0].materia_id}`}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors font-medium ${
                      isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Documentos
                </NavLink>

                {/* Separador */}
                <div className="px-3 pt-1 pb-0.5">
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Materias</p>
                </div>

                {/* Por materia: Alumnos + Asistente */}
                {materias.map((materia) => (
                  <div key={materia.id} className="ml-2 space-y-0.5">
                    <p className="px-3 pt-1 text-xs font-semibold text-gray-600">
                      {materia.materia_nombre}
                    </p>
                    <NavLink
                      to={`/alumnos/${materia.grado}/${materia.division}/${materia.materia_id}`}
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                          isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                        }`
                      }
                    >
                      <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      Alumnos
                    </NavLink>
                    <NavLink
                      to={`/chat/${materia.grado}/${materia.division}/${materia.materia_id}`}
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors ${
                          isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                        }`
                      }
                    >
                      <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      Asistente
                    </NavLink>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </nav>
    </aside>
  );
};

export default Sidebar;