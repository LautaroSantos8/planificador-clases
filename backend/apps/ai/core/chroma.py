"""
ChromaDB Manager - Gestión de colecciones vectoriales
======================================================

Maneja las 4 colecciones de documentos curriculares:
1. proyectos_docentes (prioridad máxima)
2. actualizaciones_municipal
3. curricula_provincial  
4. curricula_nacional (prioridad mínima)
"""

import chromadb
from chromadb.utils import embedding_functions
from django.conf import settings
from typing import Optional, Union, List
import os


class ChromaManager:
    """
    Singleton que gestiona la conexión a ChromaDB.
    
    Colecciones (en orden de prioridad de búsqueda):
    1. proyectos_docentes: Proyectos de aula (máxima prioridad)
    2. actualizaciones_municipal: Lineamientos recientes del municipio
    3. curricula_provincial: Currícula específica de cada provincia
    4. curricula_nacional: Contenidos base del Ministerio
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Crear directorio si no existe
        chroma_path = getattr(settings, 'CHROMA_DIR', str(settings.BASE_DIR / 'data' / 'chroma'))
        os.makedirs(chroma_path, exist_ok=True)
        
        # Inicializar cliente persistente
        self.client = chromadb.PersistentClient(path=str(chroma_path))
        
        # Embeddings de Google (no requiere torch ni modelos locales)
        self.embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.GEMINI_API_KEY,
            model_name="models/gemini-embedding-001"
        )
        
        # Inicializar las 4 colecciones
        self.curricula_nacional = self._get_or_create_collection("curricula_nacional")
        self.curricula_provincial = self._get_or_create_collection("curricula_provincial")
        self.actualizaciones_municipal = self._get_or_create_collection("actualizaciones_municipal")
        self.proyectos_docentes = self._get_or_create_collection("proyectos_docentes")
        
        self._initialized = True

    def _get_or_create_collection(self, name: str):
        """Obtiene o crea una colección con la función de embeddings."""
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def _build_where_filter(self, **conditions) -> Optional[dict]:
        """
        Construye el filtro where para ChromaDB.
        
        ChromaDB requiere $and cuando hay múltiples condiciones.
        
        Args:
            **conditions: pares clave=valor para filtrar
        
        Returns:
            dict con formato correcto para ChromaDB o None si no hay condiciones
        """
        # Filtrar condiciones None
        valid_conditions = {k: v for k, v in conditions.items() if v is not None}
        
        if not valid_conditions:
            return None
        
        # Si hay una sola condición, no necesita $and
        if len(valid_conditions) == 1:
            key, value = list(valid_conditions.items())[0]
            return {key: value}
        
        # Múltiples condiciones requieren $and
        return {
            "$and": [{k: v} for k, v in valid_conditions.items()]
        }

    def _normalize_grado(self, grado: Optional[Union[str, int]]) -> Optional[str]:
        """
        Normaliza el grado a string para búsquedas consistentes.
        
        Acepta:
            - int: 4 → "4"
            - str: "4", "sala_5", "1-2" → sin cambios
            - None → None
        """
        if grado is None:
            return None
        return str(grado)

    # === CURRÍCULA NACIONAL ===
    def add_to_nacional(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        """
        Agrega documentos a currícula nacional.
        
        Metadata esperada: {materia, grado, nivel_educativo, tipo_documento}
        """
        self.curricula_nacional.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search_nacional(
        self, 
        query: str, 
        n_results: int = 3, 
        materia: str = None, 
        grado: Union[str, int] = None,
        nivel_educativo: str = None,
    ) -> dict:
        """Busca en currícula nacional con filtros opcionales."""
        where = self._build_where_filter(
            materia=materia,
            grado=self._normalize_grado(grado),
            nivel_educativo=nivel_educativo,
        )
        
        return self.curricula_nacional.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

    # === CURRÍCULA PROVINCIAL ===
    def add_to_provincial(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        """
        Agrega documentos a currícula provincial.
        
        Metadata esperada: {provincia, materia, grado, nivel_educativo, tipo_documento}
        """
        self.curricula_provincial.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search_provincial(
        self, 
        query: str, 
        provincia: str, 
        n_results: int = 3, 
        materia: str = None, 
        grado: Union[str, int] = None,
        nivel_educativo: str = None,
    ) -> dict:
        """Busca en currícula de una provincia específica."""
        where = self._build_where_filter(
            provincia=provincia,
            materia=materia,
            grado=self._normalize_grado(grado),
            nivel_educativo=nivel_educativo,
        )
        
        return self.curricula_provincial.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

    # === ACTUALIZACIONES MUNICIPALES ===
    def add_to_actualizaciones(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        """
        Agrega documentos de actualizaciones municipales.
        
        Metadata esperada: {municipio, materia, grado, nivel_educativo, vigente}
        """
        self.actualizaciones_municipal.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search_actualizaciones(
        self, 
        query: str, 
        municipio: str, 
        n_results: int = 3,
        materia: str = None, 
        grado: Union[str, int] = None,
        nivel_educativo: str = None,
        solo_vigentes: bool = True,
    ) -> dict:
        """Busca actualizaciones municipales, priorizando las vigentes."""
        where = self._build_where_filter(
            municipio=municipio,
            vigente=True if solo_vigentes else None,
            materia=materia,
            grado=self._normalize_grado(grado),
            nivel_educativo=nivel_educativo,
        )
        
        return self.actualizaciones_municipal.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

    # === PROYECTOS DOCENTES ===
    def add_to_proyectos(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        """
        Agrega proyectos de aula.
        
        Metadata esperada: {docente_id, institucion_id, proyecto_id, grado, materias, titulo}
        """
        self.proyectos_docentes.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search_proyectos(
        self, 
        query: str, 
        docente_id: int = None, 
        institucion_id: int = None,
        materia: str = None, 
        grado: Union[str, int] = None, 
        n_results: int = 3,
    ) -> dict:
        """Busca en proyectos docentes con filtros. Materia es opcional."""
        where = self._build_where_filter(
            docente_id=docente_id,
            institucion_id=institucion_id,
            grado=self._normalize_grado(grado),
        )
        # Nota: materia se ignora intencionalmente para traer todos los proyectos del grado
        # El LLM integra el contexto de todos los proyectos

        return self.proyectos_docentes.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

    def delete_proyecto_docente(
        self, 
        docente_id: int, 
        proyecto_id: str = None,
    ) -> dict:
        """
        Elimina chunks de proyecto de un docente.
        
        Args:
            docente_id: ID del docente (obligatorio)
            proyecto_id: ID del proyecto específico (opcional, si no se da elimina todos)
        
        Returns:
            dict con información de la eliminación
        """
        try:
            # Obtener chunks existentes del docente
            results = self.proyectos_docentes.get(
                where={"docente_id": docente_id}
            )
            
            if not results or not results['ids']:
                return {
                    'success': True,
                    'deleted_count': 0,
                    'message': 'No había chunks para eliminar'
                }
            
            # Filtrar por proyecto_id si se especifica
            if proyecto_id:
                ids_to_delete = [
                    id for id, meta in zip(results['ids'], results['metadatas'])
                    if meta.get('proyecto_id') == proyecto_id
                ]
            else:
                ids_to_delete = results['ids']
            
            if not ids_to_delete:
                return {
                    'success': True,
                    'deleted_count': 0,
                    'message': 'No había chunks del proyecto especificado'
                }
            
            # Eliminar
            self.proyectos_docentes.delete(ids=ids_to_delete)
            
            return {
                'success': True,
                'deleted_count': len(ids_to_delete),
                'message': f'Eliminados {len(ids_to_delete)} chunks'
            }
            
        except Exception as e:
            return {
                'success': False,
                'deleted_count': 0,
                'message': f'Error al eliminar: {str(e)}'
            }

    def get_proyectos_docente(self, docente_id: int) -> dict:
        """
        Obtiene todos los proyectos de un docente.
        
        Returns:
            dict con lista de proyectos únicos del docente
        """
        try:
            results = self.proyectos_docentes.get(
                where={"docente_id": docente_id}
            )
            
            if not results or not results['metadatas']:
                return {
                    'success': True,
                    'proyectos': [],
                    'total_chunks': 0
                }
            
            # Extraer proyectos únicos
            proyectos = {}
            for meta in results['metadatas']:
                pid = meta.get('proyecto_id', 'unknown')
                if pid not in proyectos:
                    proyectos[pid] = {
                        'proyecto_id': pid,
                        'titulo': meta.get('titulo', 'Sin título'),
                        'grado': meta.get('grado'),
                        'materias': meta.get('materias', '').split(',') if meta.get('materias') else [],
                        'chunks_count': 0
                    }
                proyectos[pid]['chunks_count'] += 1
            
            return {
                'success': True,
                'proyectos': list(proyectos.values()),
                'total_chunks': len(results['ids'])
            }
            
        except Exception as e:
            return {
                'success': False,
                'proyectos': [],
                'total_chunks': 0,
                'error': str(e)
            }

    # === BÚSQUEDA PRIORIZADA ===
    def search_with_priority(
        self, 
        query: str, 
        docente_id: int, 
        institucion_id: int,
        provincia: str, 
        municipio: str, 
        materia: str = None, 
        grado: Union[str, int] = None,
        nivel_educativo: str = None,
    ) -> dict:
        """
        Búsqueda en todas las colecciones respetando orden de prioridad.
        
        Prioridad:
        1. Proyectos del docente (n=3)
        2. Currícula provincial (n=3)
        3. Actualizaciones municipales vigentes (n=2)
        4. Currícula nacional (n=2)
        
        Returns:
            dict con resultados organizados por fuente y prioridad
        """
        grado_normalized = self._normalize_grado(grado)
        
        results = {
            "prioridad_1_proyectos": self.search_proyectos(
                query=query,
                docente_id=docente_id,
                materia=materia,
                grado=grado_normalized,
                n_results=3
            ),
            "prioridad_2_provincial": self.search_provincial(
                query=query,
                provincia=provincia,
                materia=materia,
                grado=grado_normalized,
                nivel_educativo=nivel_educativo,
                n_results=3
            ),
            "prioridad_3_actualizaciones": self.search_actualizaciones(
                query=query,
                municipio=municipio,
                materia=materia,
                grado=grado_normalized,
                nivel_educativo=nivel_educativo,
                solo_vigentes=True,
                n_results=2
            ),
            "prioridad_4_nacional": self.search_nacional(
                query=query,
                materia=materia,
                grado=grado_normalized,
                nivel_educativo=nivel_educativo,
                n_results=2
            )
        }
        
        return results

    def format_context_for_llm(self, search_results: dict) -> str:
        """
        Formatea los resultados de búsqueda para incluir en el prompt del LLM.
        Respeta el orden de prioridad en la presentación.
        """
        context_parts = []
        
        # 1. Proyectos del docente (máxima prioridad)
        proyectos = search_results.get("prioridad_1_proyectos", {})
        if proyectos.get("documents") and proyectos["documents"][0]:
            context_parts.append("=== PROYECTO DE AULA (PRIORIDAD MÁXIMA) ===")
            context_parts.append("Las actividades deben alinearse con este proyecto:")
            for i, doc in enumerate(proyectos["documents"][0]):
                # Incluir metadata si está disponible
                meta = ""
                if proyectos.get("metadatas") and proyectos["metadatas"][0]:
                    m = proyectos["metadatas"][0][i]
                    seccion = m.get('seccion', '')
                    if seccion:
                        meta = f" [{seccion}]"
                context_parts.append(f"  •{meta} {doc[:600]}...")
        
        # 2. Currícula provincial
        provincial = search_results.get("prioridad_2_provincial", {})
        if provincial.get("documents") and provincial["documents"][0]:
            context_parts.append("\n=== CURRÍCULA PROVINCIAL ===")
            for i, doc in enumerate(provincial["documents"][0]):
                meta = ""
                if provincial.get("metadatas") and provincial["metadatas"][0]:
                    m = provincial["metadatas"][0][i]
                    tipo = m.get('tipo_documento', '')
                    nivel = m.get('nivel_educativo', '')
                    if tipo or nivel:
                        meta = f" [{tipo} - {nivel}]"
                context_parts.append(f"  •{meta} {doc[:400]}...")
        
        # 3. Actualizaciones municipales
        actualizaciones = search_results.get("prioridad_3_actualizaciones", {})
        if actualizaciones.get("documents") and actualizaciones["documents"][0]:
            context_parts.append("\n=== ACTUALIZACIONES MUNICIPALES ===")
            for doc in actualizaciones["documents"][0]:
                context_parts.append(f"  • {doc[:300]}...")
        
        # 4. Currícula nacional (complemento)
        nacional = search_results.get("prioridad_4_nacional", {})
        if nacional.get("documents") and nacional["documents"][0]:
            context_parts.append("\n=== CURRÍCULA NACIONAL (NAP) ===")
            for doc in nacional["documents"][0]:
                context_parts.append(f"  • {doc[:300]}...")
        
        if not context_parts:
            return ""
        
        return "\n".join(context_parts)

    # === UTILIDADES ===
    def reset_collection(self, name: str):
        """Elimina y recrea una colección."""
        self.client.delete_collection(name)
        if name == "curricula_nacional":
            self.curricula_nacional = self._get_or_create_collection("curricula_nacional")
        elif name == "curricula_provincial":
            self.curricula_provincial = self._get_or_create_collection("curricula_provincial")
        elif name == "actualizaciones_municipal":
            self.actualizaciones_municipal = self._get_or_create_collection("actualizaciones_municipal")
        elif name == "proyectos_docentes":
            self.proyectos_docentes = self._get_or_create_collection("proyectos_docentes")

    def get_collection_stats(self) -> dict:
        """Devuelve estadísticas de las colecciones."""
        return {
            "curricula_nacional": self.curricula_nacional.count(),
            "curricula_provincial": self.curricula_provincial.count(),
            "actualizaciones_municipal": self.actualizaciones_municipal.count(),
            "proyectos_docentes": self.proyectos_docentes.count()
        }


# Instancia global (singleton)
chroma_manager = ChromaManager()