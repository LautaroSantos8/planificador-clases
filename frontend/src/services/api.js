import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ============================================
// AUTH
// ============================================

export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login/', { email, password });
    return response.data;
  },

  logout: async () => {
    localStorage.removeItem('token');
    localStorage.removeItem('docente');
  },

  getProfile: async () => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  cambiarPassword: async (passwordActual, passwordNuevo) => {
    const response = await api.post('/auth/cambiar-password/', {
      password_actual: passwordActual,
      password_nuevo: passwordNuevo,
    });
    return response.data;
  },

  solicitarResetPassword: async (email) => {
    const response = await api.post('/auth/reset-password/', { email });
    return response.data;
  },

  confirmarResetPassword: async (uid, token, passwordNuevo) => {
    const response = await api.post('/auth/reset-password/confirmar/', {
      uid,
      token,
      password_nuevo: passwordNuevo,
    });
    return response.data;
  },
};

// ============================================
// ASIGNACIONES
// ============================================

export const asignacionesAPI = {
  getAll: async () => {
    const response = await api.get('/docentes/asignaciones/');
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/docentes/asignaciones/', data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/docentes/asignaciones/${id}/`);
    return response.data;
  },
};

// ============================================
// MATERIAS
// ============================================

export const materiasAPI = {
  getAll: async () => {
    const response = await api.get('/docentes/materias/');
    return response.data;
  },
};

// ============================================
// ALUMNOS
// ============================================

export const alumnosAPI = {
  getByAsignacion: async (grado, division) => {
    const response = await api.get(`/planificacion/alumnos/?grado=${grado}&division=${division}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/planificacion/alumnos/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/planificacion/alumnos/${id}/`, data);
    return response.data;
  },

  updateObservaciones: async (alumnoId, asignacionId, notaContextual) => {
    const response = await api.post('/planificacion/alumnos/observaciones/', {
      alumno_id: alumnoId,
      asignacion_id: asignacionId,
      nota_contextual: notaContextual,
    });
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/planificacion/alumnos/${id}/`);
    return response.data;
  },
};

// ============================================
// NIVELES DE ALUMNOS
// ============================================

export const nivelesAPI = {
  getByAlumno: async (alumnoId) => {
    const response = await api.get(`/planificacion/niveles/?alumno_id=${alumnoId}`);
    return response.data;
  },

  updateNivel: async (alumnoId, asignacionId, nivel, motivo = '') => {
    const response = await api.post('/planificacion/niveles/actualizar/', {
      alumno_id: alumnoId,
      asignacion_id: asignacionId,
      nivel: nivel,
      motivo: motivo,
    });
    return response.data;
  },
};

// ============================================
// DOCUMENTOS
// ============================================

export const documentosAPI = {
  getAll: async () => {
    const response = await api.get('/planificacion/documentos/');
    return response.data;
  },

  getByAsignacion: async (asignacionId) => {
    const response = await api.get(`/planificacion/documentos/?asignacion_id=${asignacionId}`);
    return response.data;
  },

  upload: async (titulo, tipo, descripcion, asignacionId, archivo, grado, gradosList, materiasConfirmadas) => {
    const formData = new FormData();
    formData.append('titulo', titulo);
    formData.append('tipo', tipo);
    formData.append('descripcion', descripcion);
    if (asignacionId) formData.append('asignacion_id', asignacionId);
    formData.append('archivo', archivo);
    if (grado) formData.append('grado', grado);
    if (gradosList) formData.append('grados_lista', gradosList);
    if (materiasConfirmadas) formData.append('materias_confirmadas', materiasConfirmadas);
  
    const response = await api.post('/planificacion/documentos/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/planificacion/documentos/${id}/`);
    return response.data;
  },
  analizar: async (archivo) => {
    const formData = new FormData();
    formData.append('archivo', archivo);
    const response = await api.post('/planificacion/documentos/analizar/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

// ============================================
// ASISTENTE IA
// ============================================

export const iaAPI = {
  consultar: async (consulta, grado, division, materia, alumnos = [], asignacionId = null, historial = []) => {
    const response = await api.post('/ai/consultar/', {
      consulta,
      grado,
      division,
      materia,
      alumnos,
      asignacion_id: asignacionId,
      historial,
    });
    return response.data;
  },

  getHistorial: async (asignacionId) => {
    const response = await api.get(`/ai/historial/?asignacion_id=${asignacionId}`);
    return response.data;
  },

  guardarFeedback: async (planificacionId, fueUtil, feedback = '') => {
    const response = await api.post('/ai/feedback/', {
      planificacion_id: planificacionId,
      fue_util: fueUtil,
      feedback: feedback,
    });
    return response.data;
  },

  getBienvenida: async () => {
    const response = await api.get('/ai/bienvenida/');
    return response.data;
  },

  buscarCurricula: async (query, grado, materia) => {
    const response = await api.post('/ai/buscar-curricula/', { query, grado, materia });
    return response.data;
  },

  getEstadisticas: async () => {
    const response = await api.get('/ai/estadisticas/');
    return response.data;
  },

  healthCheck: async () => {
    const response = await api.get('/ai/health/');
    return response.data;
  },

  exportar: async (planificacionId, formato) => {
    const token = localStorage.getItem('token');
    const response = await fetch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/ai/exportar/?planificacion_id=${planificacionId}&formato=${formato}`,
      {
        headers: { Authorization: `Token ${token}` },
      }
    );
    if (!response.ok) {
      throw new Error('Error al exportar la planificación');
    }
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `planificacion.${formato}`;
    return { blob, filename };
  },
};

// ============================================
// PLANIFICACIÓN (stats docente)
// ============================================

export const planificacionAPI = {
  getEstadisticasDocente: async () => {
    const response = await api.get('/planificacion/estadisticas/');
    return response.data;
  },
};

export default api;
