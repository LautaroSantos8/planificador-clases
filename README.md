# 🎓 Planificador de Clases con IA

> Asistente inteligente para docentes que genera planificaciones diferenciadas según el nivel de desempeño de cada alumno (NEE, LP, LE), fundamentadas en el currículo oficial argentino.

**🟢 Live demo:** [Frontend](https://comfortable-wisdom-production-685d.up.railway.app) · [API](https://planificador-clases-production.up.railway.app/api) · [Admin](https://planificador-clases-production.up.railway.app/admin)

---

## 📌 El problema

Los docentes de educación primaria deben planificar clases para grupos con niveles de desempeño muy distintos dentro del mismo aula. Hacerlo manualmente para cada alumno, materia y grado — respetando el currículo oficial — consume horas de trabajo semanal.

Este proyecto automatiza ese proceso: el docente sube su proyecto áulico y la planificación anual, indica el nivel de cada alumno, y el sistema genera planificaciones completas y diferenciadas en segundos.

**Cliente real:** Escuela Municipal Dr. Jorge Orgaz, Villa Rivera Indarte, Córdoba — piloto activo con 16 docentes.

---

## 🏗️ Arquitectura

```
┌─────────────┐   HTTP/JSON   ┌──────────────┐   ORM   ┌──────────────┐
│  Frontend   │◄─────────────►│   Backend    │────────►│   SQLite     │
│  (React)    │               │   (Django)   │         │  (Railway)   │
└─────────────┘               └──────┬───────┘         └──────────────┘
                                     │
                              ┌──────▼───────┐
                              │  Servicios IA │
                              │  Gemini API   │
                              │  ChromaDB     │
                              └──────────────┘
```

**Stack completo:**

| Capa | Tecnología |
|------|-----------|
| Frontend | React, Context API, React.memo |
| Backend | Django 5.2, Django REST Framework |
| IA / LLM | Gemini 2.5 Flash (generación + embeddings) |
| Base vectorial | ChromaDB (2,787 chunks del currículo oficial) |
| Base de datos | SQLite (persistente en volumen Railway) |
| Procesamiento docs | PyPDF2, python-docx, ReportLab |
| Deploy | Railway (backend + frontend + volumen) |

---

## ✨ Funcionalidades

- **Generación diferenciada:** el sistema detecta automáticamente si el alumno es NEE (Necesidades Educativas Especiales), LP (Logros en Proceso) o LE (Logros Esperados) y adapta el contenido
- **RAG sobre currículo oficial:** 12 documentos curriculares embebidos con Gemini Embedding → ChromaDB, la IA fundamenta cada planificación en el currículo real
- **Dos tipos de output:** planificaciones completas (inicio/desarrollo/cierre, competencias, indicadores de logro) o ejercicios listos para el alumno — el sistema detecta cuál pide el docente
- **Proyecto áulico como contexto silencioso:** el docente sube su proyecto y la IA lo usa como contexto temático sin mencionarlo explícitamente al alumno
- **Compresión de historial:** resumen automático + ventana deslizante para mantener contexto pedagógico en conversaciones largas
- **Exportación:** descarga de planificaciones en PDF y DOCX
- **Autenticación:** login por institución, gestión de materias y asignaciones por docente

---

## 🧠 Pipeline de IA

```
Docente hace consulta
        │
        ▼
Clasificación de intent (planificación vs. ejercicios)
        │
        ▼
RAG: búsqueda semántica en ChromaDB (currículo oficial)
        │
        ▼
Selección de prompt template (8 templates según nivel + tipo)
        │
        ▼
Gemini 2.5 Flash genera la respuesta
        │
        ▼
Compresión de historial si supera ventana
        │
        ▼
Respuesta entregada + disponible para exportar
```

**Decisión técnica clave — embeddings en la nube:**
Se migró de SentenceTransformer (local) a Gemini Embedding API para eliminar ~3 GB de dependencias (torch, transformers, scipy) que hacían inviable el deploy en Railway. Trade-off aceptado: +1-2 seg de latencia por consulta, imperceptible para el caso de uso educativo.

---

## 📁 Estructura del proyecto

```
planificador-clases/
├── backend/
│   ├── apps/
│   │   ├── ai/                     # RAG + LLM + prompts
│   │   │   └── core/
│   │   │       ├── chroma.py       # Gestor ChromaDB (Singleton)
│   │   │       ├── planificador.py # Orquestador RAG + Gemini
│   │   │       └── prompts.py      # 8 templates de prompts
│   │   ├── docentes/               # Auth, instituciones, materias
│   │   ├── planificacion/          # Alumnos, niveles NEE/LP/LE
│   │   └── curricula/              # Documentos curriculares
│   ├── utils/
│   │   ├── pdf_processor.py
│   │   ├── proyecto_processor.py
│   │   └── exportador.py           # Genera PDF y DOCX
│   └── curricula/                  # 12 PDFs del currículo oficial
├── frontend/
│   └── src/
│       ├── pages/                  # Dashboard, Alumnos, Chat, Docs
│       ├── components/
│       └── context/AuthContext.jsx
└── railway.toml
```

---

## 🔮 Escalabilidad planificada

La arquitectura actual soporta el piloto (~16 docentes). Para escalar:

| Escala | Base de datos | Vectorial | Procesamiento |
|--------|--------------|-----------|---------------|
| Piloto (16 docentes) | SQLite | ChromaDB local | Síncrono, 4 workers |
| Municipal (500+) | PostgreSQL | ChromaDB Cloud | Celery + Redis |
| Provincial (5000+) | PostgreSQL + réplicas | Pinecone | Celery cluster |

---

## 👤 Autor

**Lautaro Santos Da Silveira**
Tesis de graduación — Tecnicatura Superior en Inteligencia Artificial y Ciencia de Datos, IES21
[LinkedIn](https://www.linkedin.com/in/lautaro-santos-da-silveira-2a0852201/) · [GitHub](https://github.com/LautaroSantos8)
