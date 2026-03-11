"""
Prompts para el Asistente de Planificación Docente
Escuela Municipal Dr. Jorge Orgaz - Villa Rivera Indarte

Este módulo contiene los prompts del sistema y templates para:
1. Generar planificaciones diarias diferenciadas por nivel
2. Generar actividades concretas
3. Consultar currícula y progresiones
4. Diferenciar/adaptar actividades por nivel
5. Analizar alineación con proyecto áulico
"""

# =============================================================================
# SYSTEM PROMPT PRINCIPAL
# =============================================================================

SYSTEM_PROMPT = """Eres un asistente pedagógico especializado para docentes de educación primaria de la Escuela Municipal Dr. Jorge Orgaz, ubicada en Villa Rivera Indarte, Córdoba, Argentina.

## TU ROL
Ayudas a los docentes a:
- Crear planificaciones diarias diferenciadas según el nivel de los alumnos
- Diseñar actividades alineadas con el currículo oficial y proyectos áulicos
- Consultar contenidos de las progresiones de aprendizaje
- Adaptar actividades para diferentes niveles de desempeño
- Verificar la alineación de actividades con proyectos institucionales

## NIVELES DE DESEMPEÑO DE ALUMNOS
Los alumnos se clasifican en tres niveles:
- **NEE (Rezago Significativo)**: Alumnos que están 2 o más grados por debajo del nivel esperado. Requieren actividades con material concreto, apoyo visual intensivo, consignas simples y acompañamiento cercano del docente.
- **LP (Logros en Proceso)**: Alumnos que están 1 grado por debajo. Requieren actividades con apoyo visual, trabajo guiado y gradual autonomía.
- **LE (Logros Esperados)**: Alumnos que están en el nivel acorde a su grado. Pueden trabajar con mayor autonomía, resolver problemas complejos y ayudar a compañeros.

## CONTEXTO CURRICULAR
Trabajas con documentos oficiales de Argentina y Córdoba:
- NAP (Núcleos de Aprendizajes Prioritarios) - Nacional
- Progresiones de Aprendizaje - Provincial (Córdoba)
- Marco Curricular Común - Provincial
- Orientaciones Pedagógicas y Didácticas - Provincial
- Actualizaciones curriculares municipales

## PRINCIPIOS PEDAGÓGICOS
1. Las actividades deben ser inclusivas y respetar la diversidad
2. Priorizar el aprendizaje significativo y contextualizado
3. Fomentar el trabajo colaborativo entre pares de diferentes niveles
4. Las evaluaciones deben ser formativas y orientar la mejora
5. Usar lenguaje inclusivo (niños y niñas, todos y todas)

## FORMATO DE RESPUESTAS
- Sé claro, específico y práctico
- Incluye tiempos estimados realistas
- Sugiere recursos accesibles y disponibles en escuelas públicas
- Adapta el vocabulario al contexto argentino
- Cuando generes planificaciones, sigue EXACTAMENTE el formato de tabla solicitado
- IMPORTANTE: Usa saltos de línea entre cada campo para mejor legibilidad
- IMPORTANTE: Genera 3 planificaciones separadas, una para CADA nivel (NEE, LP, LE)
"""

# =============================================================================
# TEMPLATE: GENERAR PLANIFICACIÓN DIARIA (Caso 1)
# =============================================================================

TEMPLATE_PLANIFICACION = """## SOLICITUD DEL DOCENTE
{consulta_docente}

## INFORMACIÓN DEL DOCENTE
- Docente: {nombre_docente}
- Grado: {grado}° - División: {division}
- Turno: {turno}
- Materia: {materia}
- Institución: {institucion}

## ALUMNOS Y SUS NIVELES
{lista_alumnos}

## CONTEXTO CURRICULAR RELEVANTE (RAG)
{contexto_rag}

## PROYECTO ÁULICO DEL DOCENTE
{proyecto_aulico}

## INSTRUCCIONES CRÍTICAS - LEER CON ATENCIÓN

Debes generar **3 PLANIFICACIONES DIARIAS COMPLETAS Y SEPARADAS**, una para cada nivel de desempeño:
1. Una planificación para NEE (Rezago Significativo)
2. Una planificación para LP (Logros en Proceso)  
3. Una planificación para LE (Logros Esperados)

**IMPORTANTE**: Si hay un proyecto áulico cargado, DEBES alinear las actividades con ese proyecto. Usa los temas, contextos y metodologías del proyecto en las actividades.

**FORMATO OBLIGATORIO** - Cada planificación debe seguir EXACTAMENTE esta estructura:

---

### PLANIFICACIÓN DIARIA - NIVEL NEE (Rezago Significativo)

**Alumnos:** [Nombres de los alumnos de este nivel]

**Fecha:** A definir por el docente

**Curso:** {grado}° {division}

**Docente:** {nombre_docente}

**Área curricular:** {materia}

**Aprendizajes y contenidos:** [Contenido adaptado al nivel, 1-2 grados por debajo]

**Intención pedagógica del día:** Que los niños y niñas logren [objetivo específico y alcanzable para este nivel]

**Indicadores de logro:**
- [Indicador 1 - concreto y observable]
- [Indicador 2 - concreto y observable]

| Momento de clase | Competencias específicas | Actividad/duración | Organización estudiante | Recursos |
|------------------|--------------------------|-------------------|------------------------|----------|
| **Inicio** | [Competencia] | [Nombre]: [Descripción detallada de la actividad con material concreto] (X min) | [Individual/parejas con apoyo docente] | [Recursos accesibles] |
| **Desarrollo** | [Competencia] | [Nombre]: [Descripción detallada con pasos claros y simples] (X min) | [Organización con apoyo cercano] | [Recursos visuales/manipulables] |
| **Cierre** | [Competencia] | [Nombre]: [Actividad de cierre sencilla] (X min) | [Grupal con guía] | [Recursos] |

**Vocabulario del día:** [3-4 palabras clave simples]

**Recomendación:** [Sugerencia práctica para reforzar]

---

### PLANIFICACIÓN DIARIA - NIVEL LP (Logros en Proceso)

**Alumnos:** [Nombres de los alumnos de este nivel]

**Fecha:** A definir por el docente

**Curso:** {grado}° {division}

**Docente:** {nombre_docente}

**Área curricular:** {materia}

**Aprendizajes y contenidos:** [Contenido de 1 grado por debajo con andamiaje]

**Intención pedagógica del día:** Que los niños y niñas logren [objetivo intermedio con apoyo gradual]

**Indicadores de logro:**
- [Indicador 1]
- [Indicador 2]

| Momento de clase | Competencias específicas | Actividad/duración | Organización estudiante | Recursos |
|------------------|--------------------------|-------------------|------------------------|----------|
| **Inicio** | [Competencia] | [Nombre]: [Descripción con apoyo visual] (X min) | [Parejas/pequeños grupos] | [Recursos] |
| **Desarrollo** | [Competencia] | [Nombre]: [Descripción con complejidad intermedia] (X min) | [Trabajo guiado] | [Recursos con apoyo visual] |
| **Cierre** | [Competencia] | [Nombre]: [Actividad de síntesis] (X min) | [Grupal] | [Recursos] |

**Vocabulario del día:** [4-5 palabras clave]

**Recomendación:** [Sugerencia para consolidar]

---

### PLANIFICACIÓN DIARIA - NIVEL LE (Logros Esperados)

**Alumnos:** [Nombres de los alumnos de este nivel]

**Fecha:** A definir por el docente

**Curso:** {grado}° {division}

**Docente:** {nombre_docente}

**Área curricular:** {materia}

**Aprendizajes y contenidos:** [Contenido del grado o superior como desafío]

**Intención pedagógica del día:** Que los niños y niñas logren [objetivo desafiante con autonomía]

**Indicadores de logro:**
- [Indicador 1 - nivel del grado]
- [Indicador 2 - extensión/profundización]

| Momento de clase | Competencias específicas | Actividad/duración | Organización estudiante | Recursos |
|------------------|--------------------------|-------------------|------------------------|----------|
| **Inicio** | [Competencia] | [Nombre]: [Descripción con desafío cognitivo] (X min) | [Individual/autónomo] | [Recursos] |
| **Desarrollo** | [Competencia] | [Nombre]: [Descripción con resolución de problemas y pensamiento crítico] (X min) | [Autónomo o como tutor de otros] | [Recursos variados] |
| **Cierre** | [Competencia] | [Nombre]: [Actividad de metacognición/reflexión] (X min) | [Individual o explicando a otros] | [Recursos] |

**Vocabulario del día:** [5-6 palabras clave incluyendo técnicas]

**Recomendación:** [Desafío adicional para casa]

---

## CONSIDERACIONES FINALES

Al final, incluye una breve sección de "Consideraciones por nivel" explicando las decisiones pedagógicas tomadas para cada grupo.

**RECUERDA**: 
- Genera las 3 planificaciones COMPLETAS con todas las tablas
- Alinea con el proyecto áulico si está disponible
- Las tablas deben estar bien formateadas en Markdown
- Cada celda de la tabla debe tener contenido sustancial

Genera las 3 planificaciones ahora."""

# =============================================================================
# TEMPLATE: GENERAR ACTIVIDADES (Caso 2)
# =============================================================================

TEMPLATE_ACTIVIDADES = """## SOLICITUD DEL DOCENTE
{consulta_docente}

## INFORMACIÓN DEL DOCENTE
- Docente: {nombre_docente}
- Grado: {grado}° - División: {division}
- Materia: {materia}

## ALUMNOS Y SUS NIVELES
{lista_alumnos}

## CONTEXTO CURRICULAR RELEVANTE (RAG)
{contexto_rag}

## PROYECTO ÁULICO DEL DOCENTE
{proyecto_aulico}

## INSTRUCCIONES
Genera entre 3 y 5 ACTIVIDADES CONCRETAS relacionadas con la solicitud del docente.

Para cada actividad, usa este formato (cada campo en su propia línea):

---

### ACTIVIDAD [N]: [Nombre de la actividad]

**Objetivo:** [Qué se busca lograr]

**Contenido curricular:** [De las progresiones]

**Duración estimada:** [X minutos]

**Materiales:** [Lista de recursos necesarios]

**Descripción:**
[Explicación detallada de la actividad]

**Adaptaciones por nivel:**

*NEE:* [Cómo adaptar para rezago significativo]

*LP:* [Cómo adaptar para logros en proceso]

*LE:* [Cómo adaptar/extender para logros esperados]

**Evaluación:** [Cómo saber si se logró el objetivo]

---

Las actividades deben:
1. Estar alineadas con el proyecto áulico si existe
2. Ser progresivas en complejidad
3. Usar recursos accesibles en escuelas públicas
4. Incluir trabajo individual y colaborativo
5. Permitir evaluación formativa

Genera las actividades ahora."""

# =============================================================================
# TEMPLATE: CONSULTAR CURRÍCULA (Caso 3)
# =============================================================================

TEMPLATE_CONSULTA_CURRICULA = """## CONSULTA DEL DOCENTE
{consulta_docente}

## INFORMACIÓN DEL DOCENTE
- Grado: {grado}°
- Materia: {materia}

## CONTENIDO CURRICULAR ENCONTRADO (RAG)
{contexto_rag}

## INSTRUCCIONES
El docente quiere información sobre los contenidos curriculares. Responde de forma clara y organizada.

Tu respuesta debe incluir (cada sección en su propio párrafo):

### 1. Resumen de contenidos
Lista los aprendizajes y contenidos relevantes para el grado y materia consultados.

### 2. Indicadores de logro
Menciona los indicadores asociados a esos contenidos.

### 3. Secuencia sugerida
Si aplica, sugiere un orden lógico para abordar los contenidos.

### 4. Conexiones intercurriculares
Menciona posibles conexiones con otras áreas curriculares.

Basa tu respuesta ÚNICAMENTE en el contexto curricular proporcionado. Si no hay información suficiente, indícalo claramente.

Responde ahora de forma clara y práctica."""

# =============================================================================
# TEMPLATE: DIFERENCIAR ACTIVIDADES (Caso 4)
# =============================================================================

TEMPLATE_DIFERENCIAR = """## SOLICITUD DEL DOCENTE
{consulta_docente}

## INFORMACIÓN DEL DOCENTE
- Grado: {grado}° - División: {division}
- Materia: {materia}

## ALUMNOS Y SUS NIVELES
{lista_alumnos}

## NOTAS CONTEXTUALES DE ALUMNOS
{notas_alumnos}

## ACTIVIDAD ORIGINAL (si se proporciona)
{actividad_original}

## CONTEXTO CURRICULAR RELEVANTE (RAG)
{contexto_rag}

## INSTRUCCIONES
El docente necesita diferenciar o adaptar una actividad según los niveles de sus alumnos.

Proporciona una respuesta con este formato (cada campo en su propia línea):

---

## ANÁLISIS DE LA SITUACIÓN
[Breve análisis de las necesidades identificadas]

---

## ACTIVIDAD ADAPTADA POR NIVEL

### NIVEL NEE (Rezago Significativo)

**Adaptaciones:**
- [Modificación 1]
- [Modificación 2]

**Consigna adaptada:**
[Consigna simplificada y clara]

**Recursos adicionales:**
[Materiales de apoyo específicos]

**Rol del docente:**
[Cómo debe acompañar el docente]

---

### NIVEL LP (Logros en Proceso)

**Adaptaciones:**
- [Modificación 1]
- [Modificación 2]

**Consigna adaptada:**
[Consigna con nivel intermedio de complejidad]

**Recursos adicionales:**
[Materiales de apoyo]

**Organización sugerida:**
[Trabajo en parejas, grupos, etc.]

---

### NIVEL LE (Logros Esperados)

**Extensiones:**
- [Cómo enriquecer la actividad]
- [Desafíos adicionales]

**Consigna enriquecida:**
[Consigna con mayor complejidad]

**Rol como tutor:**
[Cómo pueden ayudar a compañeros NEE/LP]

---

## SUGERENCIAS ADICIONALES
[Consejos para implementar la diferenciación en el aula]

Considera las notas contextuales de los alumnos para personalizar las adaptaciones.

Responde ahora."""

# =============================================================================
# TEMPLATE: ALINEAR CON PROYECTO (Caso 5)
# =============================================================================

TEMPLATE_ALINEAR_PROYECTO = """## CONSULTA DEL DOCENTE
{consulta_docente}

## INFORMACIÓN DEL DOCENTE
- Grado: {grado}° - División: {division}
- Materia: {materia}

## ACTIVIDAD A EVALUAR
{actividad_evaluar}

## PROYECTO ÁULICO DEL DOCENTE
{proyecto_aulico}

## CONTEXTO CURRICULAR RELEVANTE (RAG)
{contexto_rag}

## INSTRUCCIONES
El docente quiere saber si una actividad está alineada con su proyecto áulico.

Proporciona un análisis con este formato:

---

## ANÁLISIS DE ALINEACIÓN

### ¿Está alineada con el proyecto?
[SÍ / PARCIALMENTE / NO] - [Explicación breve]

### Puntos de conexión encontrados:
1. [Conexión con objetivo del proyecto]
2. [Conexión con contenido del proyecto]
3. [Conexión con metodología del proyecto]

### Puntos que no se alinean (si los hay):
1. [Aspecto que no conecta]

### Nivel de alineación: [Alto / Medio / Bajo]

---

## SUGERENCIAS DE MEJORA

### Para mayor alineación con el proyecto:
- [Sugerencia 1]
- [Sugerencia 2]

### Modificaciones recomendadas:
[Cómo ajustar la actividad para mejor alineación]

### Actividad alternativa (si la alineación es baja):
[Propuesta de actividad que sí se alinee bien]

---

## CONEXIÓN CURRICULAR
[Cómo esta actividad conecta con las progresiones y contenidos oficiales]

Sé honesto en tu análisis. Si la actividad no se alinea bien, sugiere alternativas constructivas.

Responde ahora."""

# =============================================================================
# TEMPLATE: RESPUESTA GENERAL (para consultas que no encajan en los otros casos)
# =============================================================================

TEMPLATE_GENERAL = """## CONSULTA DEL DOCENTE
{consulta_docente}

## INFORMACIÓN DEL DOCENTE
- Docente: {nombre_docente}
- Grado: {grado}° - División: {division}
- Materia: {materia}
- Institución: {institucion}

## CONTEXTO CURRICULAR RELEVANTE (RAG)
{contexto_rag}

## PROYECTO ÁULICO DEL DOCENTE
{proyecto_aulico}

## INSTRUCCIONES
Responde la consulta del docente de forma clara, práctica y fundamentada en el contexto curricular proporcionado.

- Sé específico y concreto
- Basa tus respuestas en el currículo oficial cuando sea posible
- Si no tienes información suficiente, indícalo
- Ofrece ejemplos prácticos cuando sea útil
- Usa saltos de línea para separar secciones claramente

Responde ahora."""

# =============================================================================
# FUNCIÓN PARA DETECTAR TIPO DE CONSULTA
# =============================================================================

TIPOS_CONSULTA = {
    "planificacion": [
        "planificación", "planificacion", "planificar", 
        "clase de", "secuencia didáctica", "secuencia de",
        "unidad didáctica", "planifica", "planificá",
        "necesito una planificación", "genera una planificación",
        "haceme una planificación", "dame una planificación"
    ],
    "actividades": [
        "actividad", "actividades", "ejercicio", "ejercicios",
        "tarea", "tareas", "dame actividades", "necesito actividades",
        "proponé", "propone", "sugiere", "sugerí"
    ],
    "curricula": [
        "contenido", "contenidos", "currícula", "curricula",
        "qué debo dar", "que debo dar", "qué temas", "que temas",
        "progresiones", "nap", "qué enseñar", "que enseñar"
    ],
    "diferenciar": [
        "adaptar", "adaptación", "diferenciar", "diferenciación",
        "rezago", "dificultad", "adecuar", "adecuación",
        "alumnos con", "estudiantes con", "cómo adapto", "como adapto"
    ],
    "alinear": [
        "está alineada", "esta alineada", "evalúa si",
        "evalua si", "revisa si", "analiza si",
        "encaja con mi proyecto", "corresponde con mi proyecto",
        "se ajusta a mi proyecto"
    ]
}

# Palabras que indican que se quiere GENERAR algo (no solo evaluar)
PALABRAS_GENERACION = [
    "necesito", "genera", "generá", "haceme", "hacé", 
    "dame", "creá", "crea", "quiero", "preparar"
]


def detectar_tipo_consulta(texto: str) -> str:
    """
    Detecta el tipo de consulta basándose en palabras clave.
    
    Prioridad:
    1. Si pide "planificación" + palabras de generación → planificacion
    2. Si solo dice "está alineada" sin pedir generar → alinear
    3. En otro caso, contar coincidencias
    
    Args:
        texto: La consulta del docente
        
    Returns:
        str: Tipo de consulta (planificacion, actividades, curricula, diferenciar, alinear, general)
    """
    texto_lower = texto.lower()
    
    # Verificar si quiere GENERAR planificación (aunque mencione "alineada")
    quiere_generar = any(palabra in texto_lower for palabra in PALABRAS_GENERACION)
    menciona_planificacion = any(palabra in texto_lower for palabra in TIPOS_CONSULTA["planificacion"])
    
    # Si quiere generar Y menciona planificación → es planificacion
    if quiere_generar and menciona_planificacion:
        return "planificacion"
    
    # Si menciona "actividad/es" Y quiere generar → es actividades
    menciona_actividades = any(palabra in texto_lower for palabra in ["actividad", "actividades"])
    if quiere_generar and menciona_actividades and not menciona_planificacion:
        return "actividades"
    
    # Contar coincidencias por tipo
    coincidencias = {}
    for tipo, palabras in TIPOS_CONSULTA.items():
        coincidencias[tipo] = sum(1 for palabra in palabras if palabra in texto_lower)
    
    # Obtener el tipo con más coincidencias
    if max(coincidencias.values()) > 0:
        return max(coincidencias, key=coincidencias.get)
    
    return "general"


def obtener_template(tipo_consulta: str) -> str:
    """
    Obtiene el template correspondiente al tipo de consulta.
    
    Args:
        tipo_consulta: Tipo detectado de consulta
        
    Returns:
        str: Template correspondiente
    """
    templates = {
        "planificacion": TEMPLATE_PLANIFICACION,
        "actividades": TEMPLATE_ACTIVIDADES,
        "curricula": TEMPLATE_CONSULTA_CURRICULA,
        "diferenciar": TEMPLATE_DIFERENCIAR,
        "alinear": TEMPLATE_ALINEAR_PROYECTO,
        "general": TEMPLATE_GENERAL
    }
    return templates.get(tipo_consulta, TEMPLATE_GENERAL)


# =============================================================================
# FUNCIONES AUXILIARES PARA FORMATEAR DATOS
# =============================================================================

def formatear_lista_alumnos(alumnos: list) -> str:
    """
    Formatea la lista de alumnos con sus niveles para incluir en el prompt.
    
    Args:
        alumnos: Lista de diccionarios con datos de alumnos
                 [{"nombre": "Juan", "apellido": "Pérez", "nivel": "NEE", "notas": "..."}]
    
    Returns:
        str: Lista formateada
    """
    if not alumnos:
        return "No hay información de alumnos disponible."
    
    # Agrupar por nivel
    por_nivel = {"NEE": [], "LP": [], "LE": []}
    
    for alumno in alumnos:
        nivel = alumno.get("nivel", "LE")
        nombre_completo = f"{alumno.get('nombre', '')} {alumno.get('apellido', '')}".strip()
        if nivel in por_nivel:
            por_nivel[nivel].append(nombre_completo)
    
    # Formatear
    lineas = []
    
    nombres_niveles = {
        "NEE": "NEE (Rezago Significativo)",
        "LP": "LP (Logros en Proceso)", 
        "LE": "LE (Logros Esperados)"
    }
    
    for nivel, nombre_nivel in nombres_niveles.items():
        cantidad = len(por_nivel[nivel])
        if cantidad > 0:
            lineas.append(f"- {nombre_nivel}: {cantidad} alumnos")
            # Listar nombres (máximo 10 para no saturar el prompt)
            for nombre in por_nivel[nivel][:10]:
                lineas.append(f"  • {nombre}")
            if cantidad > 10:
                lineas.append(f"  • ... y {cantidad - 10} más")
    
    return "\n".join(lineas) if lineas else "No hay información de alumnos disponible."


def formatear_notas_alumnos(alumnos: list) -> str:
    """
    Formatea las notas contextuales de los alumnos.
    
    Args:
        alumnos: Lista de diccionarios con datos de alumnos
    
    Returns:
        str: Notas formateadas
    """
    notas = []
    for alumno in alumnos:
        nota = alumno.get("observaciones")
        if nota:
            nombre = f"{alumno.get('nombre', '')} {alumno.get('apellido', '')}".strip()
            notas.append(f"- {nombre}: {nota}")
    
    return "\n".join(notas) if notas else "No hay notas contextuales registradas."


# =============================================================================
# MENSAJES DE ERROR Y AYUDA
# =============================================================================

MSG_SIN_PROYECTO = """
No encontré un proyecto áulico cargado para tu perfil. Para obtener planificaciones más 
personalizadas, te recomiendo subir tu proyecto desde la sección "Documentos".

Mientras tanto, puedo ayudarte basándome en:
- Las Progresiones de Aprendizaje de Córdoba
- El Marco Curricular Común
- Los NAP nacionales
"""

MSG_SIN_CONTEXTO = """
No encontré información específica sobre ese tema en la currícula cargada.
Puedo ayudarte con mi conocimiento general sobre pedagogía y didáctica.
"""

MSG_SIN_ALUMNOS = """
No hay alumnos con niveles asignados para este curso. Para generar planificaciones 
diferenciadas, asigná los niveles (NEE, LP, LE) desde la sección "Alumnos".

Generaré una planificación general mientras tanto.
"""

MSG_BIENVENIDA = """
¡Hola! Soy tu asistente de planificación docente. Puedo ayudarte a:

📋 **Crear planificaciones** diferenciadas por nivel (NEE, LP, LE)
💡 **Sugerir actividades** alineadas con tu proyecto y currícula
📚 **Consultar contenidos** de las progresiones de Córdoba
🔄 **Adaptar actividades** según las necesidades de tus alumnos
✅ **Evaluar alineación** con tu proyecto áulico

¿En qué puedo ayudarte hoy?
"""


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Test de detección de tipo
    consultas_test = [
        "Necesito una planificación para trabajar fracciones",
        "Necesito una planificación alineada con mi proyecto",
        "Dame actividades sobre biodiversidad",
        "¿Qué contenidos de matemática debo dar en 4° grado?",
        "Tengo alumnos con rezago, ¿cómo adapto esta actividad?",
        "¿Esta actividad está alineada con mi proyecto?",
        "Hola, tengo una duda general"
    ]
    
    print("=== Test de detección de tipo de consulta ===\n")
    for consulta in consultas_test:
        tipo = detectar_tipo_consulta(consulta)
        print(f"Consulta: {consulta}")
        print(f"Tipo detectado: {tipo}\n")
