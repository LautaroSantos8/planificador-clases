"""
Planificador - Módulo principal del Asistente de Planificación Docente
Escuela Municipal Dr. Jorge Orgaz - Villa Rivera Indarte

Este módulo orquesta:
1. Recepción de consultas del docente
2. Detección del tipo de consulta
3. Búsqueda de contexto en ChromaDB (RAG)
4. Construcción del prompt con el template correcto
5. Llamada a Gemini 1.5 Pro
6. Devolución de la respuesta
"""

from google import genai
from google.genai import types
from django.conf import settings
from typing import Optional
import logging
import re

from .chroma import ChromaManager
from .prompts import (
    SYSTEM_PROMPT,
    TEMPLATE_PLANIFICACION,
    TEMPLATE_ACTIVIDADES,
    TEMPLATE_CONSULTA_CURRICULA,
    TEMPLATE_DIFERENCIAR,
    TEMPLATE_ALINEAR_PROYECTO,
    TEMPLATE_GENERAL,
    detectar_tipo_consulta,
    obtener_template,
    formatear_lista_alumnos,
    formatear_notas_alumnos,
    MSG_SIN_PROYECTO,
    MSG_SIN_CONTEXTO,
    MSG_SIN_ALUMNOS,
    MSG_BIENVENIDA,
)

logger = logging.getLogger(__name__)

import time

def _llamar_gemini_con_reintento(func, max_reintentos=3, espera_base=5):
    """
    Ejecuta una función de Gemini con reintentos automáticos ante error 429.
    Espera exponencial: 5s, 10s, 20s.
    """
    for intento in range(max_reintentos):
        try:
            return func()
        except Exception as e:
            if '429' in str(e) and intento < max_reintentos - 1:
                espera = espera_base * (2 ** intento)
                logger.warning(f"Rate limit Gemini (intento {intento + 1}). Reintentando en {espera}s...")
                time.sleep(espera)
            else:
                raise

class PlanificadorDocente:
    """
    Clase principal del asistente de planificación docente.
    Orquesta el flujo RAG + LLM para responder consultas.
    """
    
    def __init__(self):
        """Inicializa el planificador con Gemini y ChromaDB."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"
        self.generation_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=7500,
            system_instruction=SYSTEM_PROMPT,
        )
        
        # Inicializar RAG (ChromaDB)
        self.chroma = ChromaManager()
        
        logger.info("PlanificadorDocente inicializado correctamente")
    
    def procesar_consulta(
        self,
        consulta: str,
        docente_id: int,
        grado: str,
        division: str,
        materia: str,
        nombre_docente: str = "",
        turno: str = "Mañana",
        institucion: str = "Escuela Municipal Dr. Jorge Orgaz",
        alumnos: list = None,
        actividad_original: str = "",
        actividad_evaluar: str = "",
        historial: list = None,
    ) -> dict:
        """
        Procesa una consulta del docente y devuelve la respuesta del asistente.
        
        Args:
            consulta: Texto de la consulta del docente
            docente_id: ID del docente en la base de datos
            grado: Grado (ej: "4", "5-6")
            division: División (ej: "A", "B")
            materia: Nombre de la materia
            nombre_docente: Nombre completo del docente
            turno: Turno escolar
            institucion: Nombre de la institución
            alumnos: Lista de diccionarios con datos de alumnos
            actividad_original: Actividad a adaptar (para caso 4)
            actividad_evaluar: Actividad a evaluar alineación (para caso 5)
        
        Returns:
            dict: {
                "tipo_consulta": str,
                "respuesta": str,
                "contexto_utilizado": list,
                "error": str or None
            }
        """
        try:
            # 1. Detectar tipo de consulta
            tipo_consulta = detectar_tipo_consulta(consulta)
            logger.info(f"Tipo de consulta detectado: {tipo_consulta}")
            
            # 2. Buscar contexto en ChromaDB (RAG) — omitir para mensajes conversacionales y ambiguos
            if tipo_consulta in ("conversacional", "ambiguo"):
                contexto_rag = ""
                chunks_utilizados = []
                proyecto_aulico = ""
            else:
                contexto_rag, chunks_utilizados = self._buscar_contexto(
                    consulta=consulta,
                    docente_id=docente_id,
                    grado=grado,
                    materia=materia
                )
                # 3. Buscar proyecto del docente
                proyecto_aulico = self._obtener_proyecto_docente(docente_id, grado, materia, consulta)
            
            # 4. Formatear lista de alumnos
            lista_alumnos = formatear_lista_alumnos(alumnos) if alumnos else MSG_SIN_ALUMNOS
            notas_alumnos = formatear_notas_alumnos(alumnos) if alumnos else ""
            
            # 5. Construir el prompt según el tipo
            prompt = self._construir_prompt(
                tipo_consulta=tipo_consulta,
                consulta_docente=consulta,
                nombre_docente=nombre_docente,
                grado=grado,
                division=division,
                turno=turno,
                materia=materia,
                institucion=institucion,
                lista_alumnos=lista_alumnos,
                notas_alumnos=notas_alumnos,
                contexto_rag=contexto_rag,
                proyecto_aulico=proyecto_aulico,
                actividad_original=actividad_original,
                actividad_evaluar=actividad_evaluar,
            )
            
            # 6. Llamar a Gemini (con historial si existe)
            respuesta = self._llamar_gemini(prompt, historial=historial)
            
            return {
                "tipo_consulta": tipo_consulta,
                "respuesta": respuesta,
                "contexto_utilizado": chunks_utilizados,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error procesando consulta: {str(e)}")
            return {
                "tipo_consulta": "error",
                "respuesta": f"Lo siento, ocurrió un error al procesar tu consulta. Por favor, intentá de nuevo.",
                "contexto_utilizado": [],
                "error": str(e)
            }
    
    def _buscar_contexto(
        self,
        consulta: str,
        docente_id: int,
        grado: str,
        materia: str
    ) -> tuple[str, list]:
        """
        Busca contexto relevante en ChromaDB.
        
        Returns:
            tuple: (contexto_formateado, lista_de_chunks)
        """
        try:
            # Buscar en todas las colecciones respetando prioridad
            resultados = self.chroma.search_with_priority(
                query=consulta,
                docente_id=docente_id,
                institucion_id=1,  # TODO: obtener del docente
                provincia="Córdoba",
                municipio="Córdoba",
                materia=materia,
                grado=grado
            )
            
            # Formatear contexto para el LLM
            contexto_formateado = self.chroma.format_context_for_llm(resultados)
            
            if not contexto_formateado:
                return MSG_SIN_CONTEXTO, []
            
            # Extraer info de chunks utilizados
            chunks_info = []
            for prioridad, datos in resultados.items():
                if datos.get("documents") and datos["documents"][0]:
                    for i, doc in enumerate(datos["documents"][0]):
                        meta = {}
                        if datos.get("metadatas") and datos["metadatas"][0]:
                            meta = datos["metadatas"][0][i]
                        chunks_info.append({
                            "fuente": prioridad,
                            "documento": meta.get("documento", meta.get("titulo", "")),
                            "grado": meta.get("grado", ""),
                        })
            
            return contexto_formateado, chunks_info
            
        except Exception as e:
            logger.error(f"Error buscando contexto RAG: {str(e)}")
            return MSG_SIN_CONTEXTO, []
    
    def _obtener_proyecto_docente(
        self,
        docente_id: int,
        grado: str,
        materia: str,
        consulta: str = ""
    ) -> str:
        """
        Obtiene TODOS los proyectos del docente para el grado,
        sin filtrar por materia. El LLM integra el contexto.
        """
        try:
            # Buscar por relevancia semántica + grado, sin filtrar por materia
            MESES_MAP = ['enero','febrero','marzo','abril','mayo','junio',
                        'julio','agosto','septiembre','octubre','noviembre','diciembre']
            consulta_lower = consulta.lower()
            mes_mencionado = next((m for m in MESES_MAP if m in consulta_lower), None)
            query_busqueda = f"contenidos {mes_mencionado} {materia} {grado}" if mes_mencionado else f"proyecto actividades {grado}"

            resultados = self.chroma.search_proyectos(
                query=query_busqueda,
                docente_id=docente_id,
                grado=grado,
                n_results=10
            )

            if not resultados.get("documents") or not resultados["documents"][0]:
                # Fallback: buscar sin filtro de grado
                resultados = self.chroma.search_proyectos(
                    query=f"proyecto actividades {materia}",
                    docente_id=docente_id,
                    n_results=10
                )

            if not resultados.get("documents") or not resultados["documents"][0]:
                return MSG_SIN_PROYECTO

            # Agrupar chunks por proyecto para mostrar contexto organizado
            proyectos = {}
            metadatas = resultados.get("metadatas", [[]])[0]
            documentos = resultados["documents"][0]

            for doc, meta in zip(documentos, metadatas):
                if not doc:
                    continue
                pid = meta.get("proyecto_id", "unknown")
                titulo = meta.get("titulo", "Proyecto")
                tipo = meta.get("tipo", "proyecto_aulico")
                materias = meta.get("materias", "")

                if pid not in proyectos:
                    proyectos[pid] = {
                        "titulo": titulo,
                        "tipo": tipo,
                        "materias": materias,
                        "chunks": []
                    }
                proyectos[pid]["chunks"].append(doc)

            # Formatear contexto agrupado por proyecto
            partes = []
            for pid, datos in proyectos.items():
                tipo_label = "Proyecto áulico" if datos["tipo"] == "proyecto_aulico" else "Planificación anual"
                materias_label = f" ({datos['materias']})" if datos["materias"] else ""
                partes.append(f"=== {tipo_label}: {datos['titulo']}{materias_label} ===")
                partes.extend(datos["chunks"][:3])  # Máximo 3 chunks por proyecto

            return "\n\n".join(partes) if partes else MSG_SIN_PROYECTO

        except Exception as e:
            logger.error(f"Error obteniendo proyecto docente: {str(e)}")
            return MSG_SIN_PROYECTO
    
    def _construir_prompt(
        self,
        tipo_consulta: str,
        consulta_docente: str,
        nombre_docente: str,
        grado: str,
        division: str,
        turno: str,
        materia: str,
        institucion: str,
        lista_alumnos: str,
        notas_alumnos: str,
        contexto_rag: str,
        proyecto_aulico: str,
        actividad_original: str = "",
        actividad_evaluar: str = "",
    ) -> str:
        """
        Construye el prompt final según el tipo de consulta.
        
        Returns:
            str: Prompt listo para enviar a Gemini
        """
        # Obtener template según tipo
        template = obtener_template(tipo_consulta)
        
        # Mapeo de variables para cada template
        variables = {
            "consulta_docente": consulta_docente,
            "nombre_docente": nombre_docente,
            "grado": grado,
            "division": division,
            "turno": turno,
            "materia": materia,
            "institucion": institucion,
            "lista_alumnos": lista_alumnos,
            "notas_alumnos": notas_alumnos,
            "contexto_rag": contexto_rag,
            "proyecto_aulico": proyecto_aulico,
            "actividad_original": actividad_original or "No se proporcionó actividad.",
            "actividad_evaluar": actividad_evaluar or "No se proporcionó actividad.",
        }
        
        # Formatear template con variables
        try:
            prompt = template.format(**variables)
        except KeyError as e:
            logger.warning(f"Variable faltante en template: {e}")
            # Usar template general como fallback
            prompt = TEMPLATE_GENERAL.format(**variables)
        
        return prompt
    
    # ── Parámetros de compresión de historial ────────────────────────────────
    VENTANA_MENSAJES = 10   # Mensajes recientes a conservar siempre
    UMBRAL_COMPRESION = 20  # A partir de cuántos mensajes comprimir

    def _comprimir_historial(self, historial: list) -> list:
        """
        Comprime el historial cuando supera UMBRAL_COMPRESION mensajes.
        Estrategia: resumen de los mensajes viejos + ventana deslizante de los recientes.

        Args:
            historial: Lista de {role, content, es_resumen?}

        Returns:
            Lista comprimida. Si no supera el umbral, devuelve el historial tal cual.
        """
        if not historial or len(historial) <= self.UMBRAL_COMPRESION:
            return historial

        # Separar resumen previo (si existe), mensajes viejos y mensajes recientes
        resumen_previo = None
        mensajes_sin_resumen = []
        for msg in historial:
            if msg.get("es_resumen"):
                resumen_previo = msg
            else:
                mensajes_sin_resumen.append(msg)

        recientes = mensajes_sin_resumen[-self.VENTANA_MENSAJES:]
        a_comprimir = mensajes_sin_resumen[:-self.VENTANA_MENSAJES]

        if not a_comprimir:
            return historial

        # Construir texto para resumir
        contexto_anterior = ""
        if resumen_previo:
            contexto_anterior = f"Resumen anterior:\n{resumen_previo['content']}\n\n"

        texto_a_resumir = "\n".join(
            f"{'Docente' if m['role'] == 'user' else 'Asistente'}: {m['content']}"
            for m in a_comprimir
        )

        prompt_resumen = (
            f"{contexto_anterior}"
            f"Resumí de forma concisa los siguientes intercambios entre un docente y un asistente de planificación. "
            f"Conservá: qué planificaciones o actividades se generaron, para qué alumnos y niveles, "
            f"y cualquier decisión pedagógica importante. Máximo 200 palabras.\n\n"
            f"{texto_a_resumir}"
        )

        try:
            def _enviar_resumen():
                # NUEVA SINTAXIS: Se crea una sesión de chat a través de client.chats
                chat_resumen = self.client.chats.create(
                    model=self.model_name,
                    config=self.generation_config,
                )
                return chat_resumen.send_message(message=prompt_resumen)

            resp = _llamar_gemini_con_reintento(_enviar_resumen)
            texto_resumen = resp.text if resp and resp.text else texto_a_resumir[:500]
        except Exception as e:
            logger.warning(f"No se pudo generar resumen, usando truncado: {e}")
            texto_resumen = texto_a_resumir[:500]

        nuevo_historial = [
            {"role": "user", "content": texto_resumen, "es_resumen": True},
            {"role": "assistant", "content": "Entendido, tengo en cuenta lo trabajado anteriormente.", "es_resumen": True},
        ] + recientes

        logger.info(f"Historial comprimido: {len(historial)} → {len(nuevo_historial)} mensajes")
        return nuevo_historial

    def _llamar_gemini(self, prompt: str, historial: list = None) -> str:
        """
        Envía el prompt a Gemini usando chat con historial comprimido si existe.

        Args:
            prompt: Prompt del mensaje actual
            historial: Lista opcional de historial de mensajes
        """
        try:
            # 1. Procesar y comprimir el historial si supera los límites
            historial_procesado = self._comprimir_historial(historial) if historial else []

            # 2. Si hay historial, usamos el modo Chat del nuevo SDK
            if historial_procesado:
                # El nuevo SDK mapea roles estrictos: 'user' o 'model'
                history_api = []
                for msg in historial_procesado:
                    rol = "user" if msg.get("role") == "user" else "model"
                    history_api.append(
                        types.Content(
                            role=rol,
                            parts=[types.Part.from_text(text=msg.get("content", ""))] # Corrección: Parámetro nombrado estricto
                        )
                    )
                
                # Inicializar chat pasándole el historial previo formateado
                chat = self.client.chats.create(
                    model=self.model_name,
                    history=history_api,
                    config=self.generation_config
                )
                
                def ejecutar_chat():
                    return chat.send_message(message=prompt)
                    
                response = _llamar_gemini_con_reintento(ejecutar_chat)
                return response.text

            # 3. Si no hay historial, hacemos una llamada directa estándar muy simple
            else:
                def ejecutar_directo():
                    return self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt, # El nuevo SDK infiere el Part automáticamente de un String puro
                        config=self.generation_config
                    )
                    
                response = _llamar_gemini_con_reintento(ejecutar_directo)
                return response.text

        except Exception as e:
            logger.error(f"Error llamando a Gemini: {str(e)}")
            raise e

    
    def obtener_mensaje_bienvenida(self) -> str:
        """Devuelve el mensaje de bienvenida del asistente."""
        return MSG_BIENVENIDA
    
    def obtener_estadisticas_rag(self) -> dict:
        """
        Obtiene estadísticas de las colecciones en ChromaDB.
        
        Returns:
            dict: Estadísticas de cada colección
        """
        try:
            return self.chroma.get_collection_stats()
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas RAG: {str(e)}")
            return {}


# =============================================================================
# FUNCIONES AUXILIARES PARA USO EN VIEWS
# =============================================================================

def crear_planificador() -> PlanificadorDocente:
    """
    Factory function para crear una instancia del planificador.
    Útil para inyección de dependencias en views.
    
    Returns:
        PlanificadorDocente: Instancia configurada
    """
    return PlanificadorDocente()


def procesar_consulta_simple(
    consulta: str,
    docente_id: int,
    grado: str,
    materia: str,
    division: str = "A",
) -> str:
    """
    Función simplificada para procesar una consulta.
    Útil para testing rápido.
    
    Args:
        consulta: Texto de la consulta
        docente_id: ID del docente
        grado: Grado escolar
        materia: Materia
        division: División (default: A)
    
    Returns:
        str: Respuesta del asistente
    """
    planificador = PlanificadorDocente()
    resultado = planificador.procesar_consulta(
        consulta=consulta,
        docente_id=docente_id,
        grado=grado,
        division=division,
        materia=materia,
    )
    return resultado["respuesta"]