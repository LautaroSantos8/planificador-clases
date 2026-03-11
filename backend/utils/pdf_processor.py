"""
Procesador de PDFs Curriculares - VERSIÓN 6.0
==============================================

Para usar en Django:
    from utils.pdf_processor import PDFProcessor, detectar_tipo_por_nombre, ...

Cambios en v6:
- NAP: paginas_ruido_inicio=8, reset de grado en separadores de materia
- MCC: es_documento_general=True (no propaga nivel)
- Orientaciones: nivel_forzado detectado por nombre
- Mejor limpieza de índices
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

try:
    from PyPDF2 import PdfReader
except ImportError:
    raise ImportError("Instalar PyPDF2: pip install PyPDF2")


class TipoDocumento(Enum):
    PROGRESIONES = "progresiones"
    MCC = "mcc"
    ORIENTACIONES = "orientaciones"
    ACTUALIZACION_MUNICIPAL = "actualizacion"
    NAP = "nap"
    OTRO = "otro"


class NivelEducativo(Enum):
    INICIAL = "inicial"
    PRIMARIA = "primaria"
    SECUNDARIA = "secundaria"
    TODOS = "todos"


@dataclass
class ChunkMetadata:
    documento_id: str
    documento_titulo: str
    tipo_documento: str
    nivel_educativo: str
    ciclo: Optional[str] = None
    grado: Optional[str] = None
    año: Optional[str] = None
    sala: Optional[str] = None
    materia: Optional[str] = None
    seccion: Optional[str] = None
    provincia: Optional[str] = None
    año_documento: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convierte a diccionario, excluyendo valores None."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Chunk:
    id: str
    texto: str
    metadata: ChunkMetadata


@dataclass
class DocumentoConfig:
    tipo: TipoDocumento
    paginas_ruido_inicio: int = 0
    paginas_ruido_fin: int = 0
    separadores_principales: List[str] = field(default_factory=list)
    separadores_secundarios: List[str] = field(default_factory=list)
    chunk_max_chars: int = 1500
    chunk_min_chars: int = 100
    chunk_overlap: int = 200
    es_documento_general: bool = False
    usar_año_como_grado: bool = False
    nivel_forzado: Optional[str] = None
    reset_grado_en_separador: bool = False


# =============================================================================
# PATRONES DE LIMPIEZA
# =============================================================================

PATRONES_RUIDO = [
    r'Educación\s+(Inicial|Primaria|Secundaria)\s*·[^\n]*\n*PdA\s*·[^\n]*\d+',
    r'PdA\s*·\s*[A-Za-zÁ-ú\s]+\d+',
    r'^\d{1,3}\s*$',
    r'DISEÑO CURRICULAR DE LA PROVINCIA DE CÓRDOBA\s*',
    r'CURRÍCULUM CÓRDOBA\s*•\s*',
    r'VERSIÓN EN CONSULTA \d{4}\s*•?\s*',
    r'www\.curriculumcordoba\.ar\s*',
    r'Núcleos de Aprendizajes Prioritarios[^\n]*\d+',
    r'Ministerio de Educación\d+',
    r'^\d+\s*$',
    r'^\d{2,3}\s+\d{2,3}\s+\d{2,3}.*$',
    r'\d*\s*VOLVER AL ÍNDICE\s*',
]

PATRON_LINEA_INDICE = re.compile(r'^[A-Za-zÁ-ú\s]+\d{2,}$|^\d{2,}(\s*\d{2,})+$', re.MULTILINE)


# =============================================================================
# PATRONES DE DETECCIÓN
# =============================================================================

PATRON_GRADO = re.compile(
    r'(\d)[\.\s]*[º°]?\s*(?:y\s*(\d)[\.\s]*[º°]?\s*)?grado',
    re.IGNORECASE
)

PATRON_CICLO_GRADO = re.compile(
    r'(\d)[\.\s]*[º°]?\s*y\s*(\d)[\.\s]*[º°]?\s*grado',
    re.IGNORECASE
)

PATRON_AÑO = re.compile(
    r'(\d)[\.\s]*[º°]?\s*(?:,\s*(\d)[\.\s]*[º°]?\s*)?(?:y\s*(\d)[\.\s]*[º°]?\s*)?año',
    re.IGNORECASE
)

PATRON_SALA = re.compile(
    r'[Ss]alas?\s+de\s+(\d)(?:\s*,\s*(\d))?(?:\s+y\s+(\d))?',
    re.IGNORECASE
)

ORDINALES = {
    'primer': '1', 'primero': '1', 
    'segundo': '2',
    'tercer': '3', 'tercero': '3', 
    'cuarto': '4',
    'quinto': '5', 
    'sexto': '6',
    'séptimo': '7', 'septimo': '7',
}

PATRON_ORDINAL_AÑO = re.compile(
    r'(primer[oa]?|segundo|tercer[oa]?|cuarto|quinto|sexto|s[eé]ptimo)\s+año',
    re.IGNORECASE
)

PATRON_ORDINAL_GRADO = re.compile(
    r'(primer[oa]?|segundo|tercer[oa]?|cuarto|quinto|sexto)\s+grado',
    re.IGNORECASE
)

PATRON_INICIAL = re.compile(r'Educación\s+Inicial|[Ss]alas?\s+de\s+[345]|jardín', re.IGNORECASE)
PATRON_PRIMARIA = re.compile(r'Educación\s+Primaria|\d[\.\s]*[º°]?\s*(?:y\s*\d[\.\s]*[º°]?\s*)?grado', re.IGNORECASE)
PATRON_SECUNDARIA = re.compile(r'Educación\s+Secundaria|ciclo\s+básico|ciclo\s+orientado', re.IGNORECASE)

PATRON_NAP_PRIMARIA = re.compile(r'EDUCACIÓN\s+PRIMARIA|CICLO\s+EDUCACIÓN\s+PRIMARIA', re.IGNORECASE)

PATRON_SEPARADOR_MATERIA = re.compile(
    r'^(LENGUA|MATEMÁTICA|CIENCIAS\s+SOCIALES|CIENCIAS\s+NATURALES|'
    r'EDUCACIÓN\s+FÍSICA|EDUCACIÓN\s+TECNOLÓGICA|FORMACIÓN\s+ÉTICA|'
    r'EDUCACIÓN\s+ARTÍSTICA|ARTES\s+VISUALES|MÚSICA|TEATRO|DANZAS)',
    re.IGNORECASE | re.MULTILINE
)


# =============================================================================
# CONFIGURACIONES POR TIPO
# =============================================================================

CONFIGS_DOCUMENTO = {
    TipoDocumento.PROGRESIONES: DocumentoConfig(
        tipo=TipoDocumento.PROGRESIONES,
        paginas_ruido_inicio=9,
        paginas_ruido_fin=1,
        separadores_principales=[
            r'Educación\s+Inicial\s*\n',
            r'Educación\s+Primaria\s*\n',
            r'Educación\s+Secundaria\s*\n',
        ],
        separadores_secundarios=[
            r'Metas\s+del\s+ciclo',
            r'Metas\s+por\s+ciclo',
            r'\bMeta\b\s*\n',
        ],
    ),
    TipoDocumento.MCC: DocumentoConfig(
        tipo=TipoDocumento.MCC,
        paginas_ruido_inicio=4,
        paginas_ruido_fin=2,
        separadores_principales=[
            r'Dimensión\s+\w+',
            r'^I+\.\s+',
        ],
        es_documento_general=True,
    ),
    TipoDocumento.ORIENTACIONES: DocumentoConfig(
        tipo=TipoDocumento.ORIENTACIONES,
        paginas_ruido_inicio=6,
        paginas_ruido_fin=2,
        separadores_principales=[
            r'^I+\.\s+',
            r'Finalidades',
        ],
    ),
    TipoDocumento.ACTUALIZACION_MUNICIPAL: DocumentoConfig(
        tipo=TipoDocumento.ACTUALIZACION_MUNICIPAL,
        paginas_ruido_inicio=2,
        paginas_ruido_fin=1,
        separadores_principales=[
            r'Educación\s+Inicial',
            r'Educación\s+Primaria',
            r'Primer\s+Ciclo',
            r'Segundo\s+Ciclo',
        ],
        chunk_max_chars=1200,
        chunk_min_chars=80,
    ),
    TipoDocumento.NAP: DocumentoConfig(
        tipo=TipoDocumento.NAP,
        paginas_ruido_inicio=8,
        paginas_ruido_fin=1,
        separadores_principales=[
            r'\bLENGUA\b',
            r'\bMATEMÁTICA\b',
            r'CIENCIAS\s+SOCIALES',
            r'CIENCIAS\s+NATURALES',
            r'EDUCACIÓN\s+FÍSICA',
            r'EDUCACIÓN\s+TECNOLÓGICA',
            r'FORMACIÓN\s+ÉTICA',
            r'EDUCACIÓN\s+ARTÍSTICA',
            r'ARTES\s+VISUALES',
            r'\bMÚSICA\b',
            r'\bTEATRO\b',
            r'\bDANZAS\b',
        ],
        separadores_secundarios=[
            r'Primer\s+Año',
            r'Segundo\s+Año',
            r'Tercer\s+Año',
            r'Cuarto\s+Año',
            r'Quinto\s+Año',
            r'Sexto\s+Año',
        ],
        chunk_max_chars=1200,
        chunk_min_chars=80,
        usar_año_como_grado=True,
        reset_grado_en_separador=True,
    ),
    TipoDocumento.OTRO: DocumentoConfig(
        tipo=TipoDocumento.OTRO,
        paginas_ruido_inicio=2,
        paginas_ruido_fin=1,
        chunk_max_chars=1000,
        chunk_min_chars=50,
    ),
}


class PDFProcessor:
    """Procesador de PDFs curriculares v6.0"""
    
    def __init__(self):
        self.stats = {
            'paginas_procesadas': 0,
            'chunks_generados': 0,
            'chunks_descartados': 0,
            'caracteres_totales': 0,
        }
        self._config_actual = None
        self._reset_contexto()
    
    def _reset_contexto(self):
        self._ultimo_nivel = 'todos'
        self._ctx = {
            'inicial': {'sala': None, 'ciclo': None},
            'primaria': {'grado': None, 'ciclo': None},
            'secundaria': {'año': None, 'ciclo': None},
        }
    
    def _reset_grado(self):
        self._ctx['primaria']['grado'] = None
    
    def _set_ctx(self, nivel: str, **kwargs):
        if nivel in self._ctx:
            for k, v in kwargs.items():
                if v is not None:
                    self._ctx[nivel][k] = v
    
    def _get_ctx(self, nivel: str, key: str):
        return self._ctx.get(nivel, {}).get(key)
    
    def extract_text_from_pdf(self, file_path, pagina_inicio=0, pagina_fin=None):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"No encontrado: {file_path}")
        
        reader = PdfReader(str(file_path))
        total = len(reader.pages)
        
        pagina_inicio = max(0, pagina_inicio)
        pagina_fin = total if pagina_fin is None else min(pagina_fin, total)
        
        paginas = []
        textos = []
        
        for i in range(pagina_inicio, pagina_fin):
            texto = reader.pages[i].extract_text() or ""
            texto = self._limpiar(texto)
            if texto.strip():
                paginas.append((i + 1, texto))
                textos.append(texto)
        
        self.stats['paginas_procesadas'] = len(paginas)
        return "\n\n".join(textos), paginas
    
    def _limpiar(self, texto: str) -> str:
        texto = texto.replace('\r\n', '\n').replace('\r', '\n')
        
        for p in PATRONES_RUIDO:
            texto = re.sub(p, '', texto, flags=re.IGNORECASE | re.MULTILINE)
        
        texto = PATRON_LINEA_INDICE.sub('', texto)
        texto = re.sub(r' +', ' ', texto)
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        
        lineas = []
        for l in texto.split('\n'):
            l = l.strip()
            if len(l) > 3 and not re.match(r'^\d+$', l):
                lineas.append(l)
        
        return '\n'.join(lineas)
    
    def _es_separador_materia(self, texto: str) -> bool:
        return bool(PATRON_SEPARADOR_MATERIA.match(texto.strip()))
    
    def _detectar_nivel(self, texto: str) -> str:
        if self._config_actual and self._config_actual.nivel_forzado:
            return self._config_actual.nivel_forzado
        
        if self._config_actual and self._config_actual.es_documento_general:
            menciones = []
            if PATRON_INICIAL.search(texto):
                menciones.append('inicial')
            if PATRON_PRIMARIA.search(texto):
                menciones.append('primaria')
            if PATRON_SECUNDARIA.search(texto):
                menciones.append('secundaria')
            
            if len(menciones) != 1:
                return 'todos'
            return menciones[0]
        
        if self._config_actual and self._config_actual.usar_año_como_grado:
            if PATRON_NAP_PRIMARIA.search(texto):
                self._ultimo_nivel = 'primaria'
                return 'primaria'
            if PATRON_ORDINAL_AÑO.search(texto):
                self._ultimo_nivel = 'primaria'
                return 'primaria'
        
        if PATRON_INICIAL.search(texto):
            self._ultimo_nivel = 'inicial'
        elif PATRON_SECUNDARIA.search(texto):
            self._ultimo_nivel = 'secundaria'
        elif PATRON_PRIMARIA.search(texto):
            self._ultimo_nivel = 'primaria'
        
        return self._ultimo_nivel
    
    def _detectar_sala(self, texto: str) -> Optional[str]:
        m = PATRON_SALA.search(texto)
        if m:
            salas = [g for g in m.groups() if g]
            resultado = "-".join(salas) if len(salas) > 1 else salas[0]
            self._set_ctx('inicial', sala=resultado)
            return resultado
        return self._get_ctx('inicial', 'sala')
    
    def _detectar_grado(self, texto: str, nivel: str) -> Optional[str]:
        if nivel != 'primaria':
            return None
        
        if self._config_actual and self._config_actual.usar_año_como_grado:
            m = PATRON_ORDINAL_AÑO.search(texto)
            if m:
                ordinal = m.group(1).lower()
                for key, num in ORDINALES.items():
                    if ordinal.startswith(key[:4]):
                        self._set_ctx('primaria', grado=num)
                        return num
        
        m = PATRON_GRADO.search(texto)
        if m:
            g1, g2 = m.group(1), m.group(2)
            resultado = f"{g1}-{g2}" if g2 else g1
            self._set_ctx('primaria', grado=resultado)
            return resultado
        
        m = PATRON_ORDINAL_GRADO.search(texto)
        if m:
            ordinal = m.group(1).lower()
            for key, num in ORDINALES.items():
                if ordinal.startswith(key[:4]):
                    self._set_ctx('primaria', grado=num)
                    return num
        
        return self._get_ctx('primaria', 'grado')
    
    def _detectar_año(self, texto: str, nivel: str) -> Optional[str]:
        if nivel != 'secundaria':
            return None
        
        if self._config_actual and self._config_actual.usar_año_como_grado:
            return None
        
        m = PATRON_AÑO.search(texto)
        if m:
            años = [g for g in m.groups() if g]
            if años:
                resultado = "-".join(años) if len(años) > 1 else años[0]
                self._set_ctx('secundaria', año=resultado)
                return resultado
        
        for ordinal, num in ORDINALES.items():
            if re.search(rf'{ordinal}\s+año', texto, re.IGNORECASE):
                self._set_ctx('secundaria', año=num)
                return num
        
        return self._get_ctx('secundaria', 'año')
    
    def _detectar_ciclo(self, texto: str, nivel: str) -> Optional[str]:
        if self._config_actual and self._config_actual.es_documento_general:
            return None
        
        if nivel == 'inicial':
            if 'sala de 3' in texto.lower() or 'salas de 3' in texto.lower():
                self._set_ctx('inicial', ciclo='sala_3')
                return 'sala_3'
            elif 'sala de 4' in texto.lower():
                self._set_ctx('inicial', ciclo='sala_4')
                return 'sala_4'
            elif 'sala de 5' in texto.lower():
                self._set_ctx('inicial', ciclo='sala_5')
                return 'sala_5'
            return self._get_ctx('inicial', 'ciclo')
        
        elif nivel == 'primaria':
            if self._config_actual and self._config_actual.tipo == TipoDocumento.NAP:
                return self._get_ctx('primaria', 'ciclo')
            
            m = PATRON_CICLO_GRADO.search(texto)
            if m:
                g1, g2 = m.group(1), m.group(2)
                if g1 == '1' and g2 == '2':
                    ciclo = 'primer_ciclo'
                elif g1 == '3' and g2 == '4':
                    ciclo = 'segundo_ciclo'
                elif g1 == '5' and g2 == '6':
                    ciclo = 'tercer_ciclo'
                else:
                    ciclo = f"ciclo_{g1}_{g2}"
                self._set_ctx('primaria', ciclo=ciclo)
                return ciclo
            
            return self._get_ctx('primaria', 'ciclo')
        
        elif nivel == 'secundaria':
            if re.search(r'1[\.\s]*[º°]?\s*,?\s*2[\.\s]*[º°]?\s*y\s*3[\.\s]*[º°]?\s*año', texto, re.IGNORECASE):
                self._set_ctx('secundaria', ciclo='ciclo_basico')
                return 'ciclo_basico'
            elif re.search(r'4[\.\s]*[º°]?\s*,?\s*5[\.\s]*[º°]?\s*y\s*6[\.\s]*[º°]?\s*año', texto, re.IGNORECASE):
                self._set_ctx('secundaria', ciclo='ciclo_orientado')
                return 'ciclo_orientado'
            elif 'ciclo básico' in texto.lower():
                self._set_ctx('secundaria', ciclo='ciclo_basico')
                return 'ciclo_basico'
            elif 'ciclo orientado' in texto.lower():
                self._set_ctx('secundaria', ciclo='ciclo_orientado')
                return 'ciclo_orientado'
            return self._get_ctx('secundaria', 'ciclo')
        
        return None
    
    def _detectar_seccion(self, texto: str) -> Optional[str]:
        t = texto[:200].lower()
        if t.startswith('meta') or 'meta\n' in t:
            return 'meta'
        elif 'aprendizaje y contenido' in t or 'aprendizajes y contenidos' in t:
            return 'aprendizaje_contenido'
        elif t.startswith('indicador') or 'indicadores de logro' in t:
            return 'indicador'
        elif 'metas del ciclo' in t or 'metas por ciclo' in t:
            return 'metas_ciclo'
        return None
    
    def _detectar_materia_chunk(self, texto: str) -> Optional[str]:
        t = texto[:100].upper()
        
        if 'MATEMÁTICA' in t:
            return 'matematicas'
        elif 'LENGUA' in t:
            return 'lengua'
        elif 'CIENCIAS NATURALES' in t:
            return 'ciencias_naturales'
        elif 'CIENCIAS SOCIALES' in t:
            return 'ciencias_sociales'
        elif 'EDUCACIÓN FÍSICA' in t:
            return 'educacion_fisica'
        elif 'EDUCACIÓN TECNOLÓGICA' in t:
            return 'educacion_tecnologica'
        elif 'FORMACIÓN ÉTICA' in t:
            return 'formacion_etica'
        elif 'EDUCACIÓN ARTÍSTICA' in t or 'ARTES VISUALES' in t or 'MÚSICA' in t or 'TEATRO' in t or 'DANZAS' in t:
            return 'educacion_artistica'
        
        return None
    
    def _split_semantico(self, texto: str, config: DocumentoConfig) -> list:
        seps = config.separadores_principales + config.separadores_secundarios
        if not seps:
            return self._split_size(texto, config.chunk_max_chars, config.chunk_overlap)
        
        patron = '|'.join(f'({s})' for s in seps)
        matches = list(re.finditer(patron, texto, re.IGNORECASE | re.MULTILINE))
        
        if not matches:
            return self._split_size(texto, config.chunk_max_chars, config.chunk_overlap)
        
        chunks = []
        prev = 0
        
        for i, m in enumerate(matches):
            if m.start() > prev:
                c = texto[prev:m.start()].strip()
                if len(c) >= config.chunk_min_chars:
                    chunks.append(c)
            
            end = matches[i+1].start() if i+1 < len(matches) else len(texto)
            c = texto[m.start():end].strip()
            
            if len(c) > config.chunk_max_chars * 1.5:
                for sc in self._split_size(c, config.chunk_max_chars, config.chunk_overlap):
                    if len(sc) >= config.chunk_min_chars:
                        chunks.append(sc)
            elif len(c) >= config.chunk_min_chars:
                chunks.append(c)
            
            prev = end
        
        if prev < len(texto):
            c = texto[prev:].strip()
            if len(c) >= config.chunk_min_chars:
                chunks.append(c)
        
        return chunks
    
    def _split_size(self, texto: str, max_chars: int, overlap: int) -> list:
        chunks = []
        inicio = 0
        
        while inicio < len(texto):
            fin = inicio + max_chars
            if fin >= len(texto):
                c = texto[inicio:].strip()
                if c:
                    chunks.append(c)
                break
            
            corte = fin
            for sep in ['\n\n', '. ', '\n']:
                pos = texto.rfind(sep, inicio + max_chars//2, fin)
                if pos > inicio:
                    corte = pos + len(sep)
                    break
            
            c = texto[inicio:corte].strip()
            if c:
                chunks.append(c)
            
            inicio = max(corte - overlap, inicio + 1)
        
        return chunks
    
    def process_documento(
        self,
        file_path,
        documento_id: str,
        titulo: str,
        tipo: TipoDocumento = TipoDocumento.OTRO,
        materia: str = None,
        provincia: str = None,
        año: int = None,
        ciclo_nap: str = None,
        nivel_forzado: str = None,
    ) -> list:
        """
        Procesa un PDF y retorna lista de Chunks.
        
        Args:
            file_path: Ruta al PDF
            documento_id: ID único del documento
            titulo: Título del documento
            tipo: TipoDocumento (progresiones, nap, mcc, etc.)
            materia: Materia del documento
            provincia: Provincia (para currículum provincial)
            año: Año del documento
            ciclo_nap: Para NAP, indicar "primer_ciclo" o "segundo_ciclo"
            nivel_forzado: Forzar nivel educativo (primaria, secundaria, etc.)
        
        Returns:
            Lista de objetos Chunk
        """
        self._reset_contexto()
        
        config = CONFIGS_DOCUMENTO.get(tipo, CONFIGS_DOCUMENTO[TipoDocumento.OTRO])
        
        # Clonar config
        config = DocumentoConfig(
            tipo=config.tipo,
            paginas_ruido_inicio=config.paginas_ruido_inicio,
            paginas_ruido_fin=config.paginas_ruido_fin,
            separadores_principales=config.separadores_principales.copy(),
            separadores_secundarios=config.separadores_secundarios.copy(),
            chunk_max_chars=config.chunk_max_chars,
            chunk_min_chars=config.chunk_min_chars,
            chunk_overlap=config.chunk_overlap,
            es_documento_general=config.es_documento_general,
            usar_año_como_grado=config.usar_año_como_grado,
            nivel_forzado=nivel_forzado or config.nivel_forzado,
            reset_grado_en_separador=config.reset_grado_en_separador,
        )
        
        self._config_actual = config
        
        if tipo == TipoDocumento.NAP and ciclo_nap:
            self._set_ctx('primaria', ciclo=ciclo_nap)
            self._ultimo_nivel = 'primaria'
        
        texto, _ = self.extract_text_from_pdf(file_path, config.paginas_ruido_inicio)
        if not texto.strip():
            return []
        
        self.stats['caracteres_totales'] = len(texto)
        
        chunks_raw = self._split_semantico(texto, config)
        
        chunks = []
        descartados = 0
        materia_actual = materia
        
        for i, txt in enumerate(chunks_raw):
            if len(txt) < config.chunk_min_chars:
                descartados += 1
                continue
            
            if config.reset_grado_en_separador and self._es_separador_materia(txt):
                self._reset_grado()
                nueva_materia = self._detectar_materia_chunk(txt)
                if nueva_materia:
                    materia_actual = nueva_materia
            
            nivel = self._detectar_nivel(txt)
            sala = self._detectar_sala(txt) if nivel == 'inicial' else None
            grado = self._detectar_grado(txt, nivel)
            año_esc = self._detectar_año(txt, nivel)
            ciclo = self._detectar_ciclo(txt, nivel)
            seccion = self._detectar_seccion(txt)
            
            meta = ChunkMetadata(
                documento_id=documento_id,
                documento_titulo=titulo,
                tipo_documento=tipo.value,
                nivel_educativo=nivel,
                ciclo=ciclo,
                grado=grado,
                año=año_esc,
                sala=sala,
                materia=materia_actual,
                seccion=seccion,
                provincia=provincia,
                año_documento=año,
            )
            
            chunks.append(Chunk(
                id=f"{documento_id}_chunk_{i:04d}",
                texto=txt,
                metadata=meta
            ))
        
        self.stats['chunks_generados'] = len(chunks)
        self.stats['chunks_descartados'] = descartados
        
        return chunks
    
    def get_stats(self) -> dict:
        return self.stats.copy()


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def detectar_tipo_por_nombre(nombre: str) -> TipoDocumento:
    """Detecta el tipo de documento por el nombre del archivo."""
    nombre = nombre.lower()
    
    if 'progresion' in nombre:
        return TipoDocumento.PROGRESIONES
    elif 'nap' in nombre:
        return TipoDocumento.NAP
    elif 'marco' in nombre or 'mcc' in nombre:
        return TipoDocumento.MCC
    elif 'orientacion' in nombre:
        return TipoDocumento.ORIENTACIONES
    elif 'actualiza' in nombre or '_ac' in nombre or '-ac' in nombre:
        return TipoDocumento.ACTUALIZACION_MUNICIPAL
    
    return TipoDocumento.OTRO


def detectar_materia_por_nombre(nombre: str) -> str:
    """Detecta la materia por el nombre del archivo."""
    nombre = nombre.lower()
    
    if 'matem' in nombre:
        return 'matematicas'
    elif 'lengua' in nombre or 'literatura' in nombre:
        return 'lengua'
    elif 'naturales' in nombre:
        return 'ciencias_naturales'
    elif 'sociales' in nombre:
        return 'ciencias_sociales'
    elif 'fisica' in nombre or 'física' in nombre:
        return 'educacion_fisica'
    elif 'artistica' in nombre or 'artística' in nombre:
        return 'educacion_artistica'
    elif 'tecnolog' in nombre:
        return 'educacion_tecnologica'
    elif 'etica' in nombre or 'ética' in nombre or 'ciudadan' in nombre:
        return 'formacion_etica'
    
    return 'todas'


def detectar_ciclo_nap_por_nombre(nombre: str) -> Optional[str]:
    """Para NAP, detecta el ciclo por el nombre del archivo."""
    nombre = nombre.lower()
    
    if 'primer' in nombre or '1er' in nombre or 'ciclo_1' in nombre:
        return 'primer_ciclo'
    elif 'segundo' in nombre or '2do' in nombre or 'ciclo_2' in nombre:
        return 'segundo_ciclo'
    
    return None


def detectar_nivel_forzado_por_nombre(nombre: str) -> Optional[str]:
    """Detecta si el documento tiene nivel forzado por su nombre."""
    nombre = nombre.lower()
    
    if 'orientacion' in nombre:
        if 'primaria' in nombre:
            return 'primaria'
        elif 'inicial' in nombre:
            return 'inicial'
        elif 'secundaria' in nombre:
            return 'secundaria'
    
    return None
