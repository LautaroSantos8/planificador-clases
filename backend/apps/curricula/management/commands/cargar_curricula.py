"""
Comando Django para cargar documentos curriculares a ChromaDB.

Uso:
    python manage.py cargar_curricula                    # Procesa data/curricula/
    python manage.py cargar_curricula --reset            # Resetea colecciones antes
    python manage.py cargar_curricula --archivo X.pdf    # Procesa un archivo específico

Estructura esperada en data/curricula/:
    PROGRESIONES DE APRENDIZAJE DE MATEMATICA.pdf
    NAP_Primaria_Primer_Ciclo.pdf
    MARCO CURRICULAR COMUN.pdf
    ACTUALIZACION_2023_Lengua.pdf
    ...
"""

import os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.ai.core.chroma import chroma_manager
from apps.curricula.models import DocumentoCurricula
from utils.pdf_processor import (
    PDFProcessor,
    TipoDocumento,
    detectar_tipo_por_nombre,
    detectar_materia_por_nombre,
    detectar_ciclo_nap_por_nombre,
    detectar_nivel_forzado_por_nombre,
)


# Mapeo de TipoDocumento a nivel de colección
TIPO_A_NIVEL = {
    TipoDocumento.NAP: 'nacional',
    TipoDocumento.PROGRESIONES: 'provincial',
    TipoDocumento.MCC: 'provincial',
    TipoDocumento.ORIENTACIONES: 'provincial',
    TipoDocumento.ACTUALIZACION_MUNICIPAL: 'municipal',
    TipoDocumento.OTRO: 'provincial',
}

# Mapeo de TipoDocumento a tipo del modelo
TIPO_A_MODELO = {
    TipoDocumento.NAP: 'nap_ciclo',
    TipoDocumento.PROGRESIONES: 'progresiones',
    TipoDocumento.MCC: 'mcc',
    TipoDocumento.ORIENTACIONES: 'orientaciones',
    TipoDocumento.ACTUALIZACION_MUNICIPAL: 'actualizacion',
    TipoDocumento.OTRO: 'progresiones',
}


class Command(BaseCommand):
    help = 'Carga documentos curriculares a ChromaDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Resetea las colecciones antes de cargar',
        )
        parser.add_argument(
            '--archivo',
            type=str,
            help='Procesa solo un archivo específico',
        )
        parser.add_argument(
            '--carpeta',
            type=str,
            default='data/curricula',
            help='Carpeta con los PDFs (default: data/curricula)',
        )
        parser.add_argument(
            '--provincia',
            type=str,
            default='cordoba',
            help='Provincia para documentos provinciales (default: cordoba)',
        )
        parser.add_argument(
            '--municipio',
            type=str,
            default='cordoba',
            help='Municipio para actualizaciones (default: cordoba)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('  CARGADOR DE CURRÍCULAS A CHROMADB'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        
        # Opciones
        reset = options['reset']
        archivo_especifico = options.get('archivo')
        carpeta = Path(options['carpeta'])
        provincia = options['provincia']
        municipio = options['municipio']
        
        # Verificar carpeta
        if not carpeta.exists():
            raise CommandError(f"No existe la carpeta: {carpeta.absolute()}")
        
        # Reset si se solicita
        if reset:
            self._reset_colecciones()
        
        # Obtener PDFs
        if archivo_especifico:
            pdfs = [Path(archivo_especifico)]
            if not pdfs[0].exists():
                raise CommandError(f"No existe el archivo: {archivo_especifico}")
        else:
            pdfs = list(carpeta.glob("*.pdf")) + list(carpeta.glob("*.PDF"))
        
        if not pdfs:
            raise CommandError(f"No se encontraron PDFs en: {carpeta.absolute()}")
        
        self.stdout.write(f"\n📁 Carpeta: {carpeta.absolute()}")
        self.stdout.write(f"📄 PDFs encontrados: {len(pdfs)}")
        self.stdout.write("-" * 60)
        
        # Procesar
        processor = PDFProcessor()
        totales = {
            'procesados': 0,
            'chunks': 0,
            'errores': 0,
        }
        
        for i, pdf_path in enumerate(sorted(pdfs), 1):
            self.stdout.write(f"\n[{i}/{len(pdfs)}] {pdf_path.name}")
            
            try:
                resultado = self._procesar_pdf(
                    processor=processor,
                    pdf_path=pdf_path,
                    provincia=provincia,
                    municipio=municipio,
                )
                
                totales['procesados'] += 1
                totales['chunks'] += resultado['chunks']
                
                self.stdout.write(self.style.SUCCESS(
                    f"    ✓ {resultado['chunks']} chunks → {resultado['coleccion']}"
                ))
                
            except Exception as e:
                totales['errores'] += 1
                self.stdout.write(self.style.ERROR(f"    ✗ Error: {e}"))
        
        # Resumen
        self._mostrar_resumen(totales)
    
    def _reset_colecciones(self):
        """Resetea las colecciones de ChromaDB."""
        self.stdout.write("\n⚠️  Reseteando colecciones...")
        
        for coleccion in ['curricula_nacional', 'curricula_provincial', 'actualizaciones_municipal']:
            try:
                chroma_manager.reset_collection(coleccion)
                self.stdout.write(f"    ✓ {coleccion} reseteada")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    ! {coleccion}: {e}"))
    
    def _procesar_pdf(self, processor, pdf_path, provincia, municipio):
        """Procesa un PDF y lo carga a ChromaDB."""
        nombre = pdf_path.stem
        
        # Detectar tipo, materia, etc.
        tipo = detectar_tipo_por_nombre(nombre)
        materia = detectar_materia_por_nombre(nombre)
        ciclo_nap = detectar_ciclo_nap_por_nombre(nombre) if tipo == TipoDocumento.NAP else None
        nivel_forzado = detectar_nivel_forzado_por_nombre(nombre)
        
        # Generar ID único
        doc_id = nombre.lower().replace(' ', '_').replace('-', '_')[:50]
        
        # Procesar PDF
        chunks = processor.process_documento(
            file_path=str(pdf_path),
            documento_id=doc_id,
            titulo=nombre,
            tipo=tipo,
            materia=materia,
            provincia=provincia,
            año=2025,
            ciclo_nap=ciclo_nap,
            nivel_forzado=nivel_forzado,
        )
        
        if not chunks:
            raise Exception("No se generaron chunks")
        
        # Preparar datos para ChromaDB
        documents = [c.texto for c in chunks]
        ids = [c.id for c in chunks]
        metadatas = []
        
        for c in chunks:
            meta = c.metadata.to_dict()
            # Agregar campos requeridos por ChromaDB
            meta['provincia'] = provincia
            if tipo == TipoDocumento.ACTUALIZACION_MUNICIPAL:
                meta['municipio'] = municipio
                meta['vigente'] = True
            metadatas.append(meta)
        
        # Determinar colección
        nivel = TIPO_A_NIVEL.get(tipo, 'provincial')
        
        if nivel == 'nacional':
            chroma_manager.add_to_nacional(documents, metadatas, ids)
            coleccion = 'curricula_nacional'
        elif nivel == 'municipal':
            chroma_manager.add_to_actualizaciones(documents, metadatas, ids)
            coleccion = 'actualizaciones_municipal'
        else:
            chroma_manager.add_to_provincial(documents, metadatas, ids)
            coleccion = 'curricula_provincial'
        
        # Crear o actualizar registro en Django
        self._guardar_modelo(
            pdf_path=pdf_path,
            tipo=tipo,
            materia=materia,
            provincia=provincia,
            municipio=municipio if nivel == 'municipal' else '',
            chunks_count=len(chunks),
            ciclo_nap=ciclo_nap,
        )
        
        return {
            'chunks': len(chunks),
            'coleccion': coleccion,
        }
    
    def _guardar_modelo(self, pdf_path, tipo, materia, provincia, municipio, chunks_count, ciclo_nap):
        """Guarda o actualiza el registro en Django."""
        titulo = pdf_path.stem
        nivel = TIPO_A_NIVEL.get(tipo, 'provincial')
        tipo_modelo = TIPO_A_MODELO.get(tipo, 'progresiones')
        
        # Mapear ciclo
        ciclo = 'todos'
        if ciclo_nap == 'primer_ciclo':
            ciclo = 'primero'
        elif ciclo_nap == 'segundo_ciclo':
            ciclo = 'segundo'
        
        # Mapear materia
        materia_modelo = materia if materia in dict(DocumentoCurricula.MATERIA_CHOICES) else 'todas'
        
        doc, created = DocumentoCurricula.objects.update_or_create(
            titulo=titulo,
            defaults={
                'descripcion': f'Procesado automáticamente desde {pdf_path.name}',
                'nivel': nivel,
                'tipo': tipo_modelo,
                'ciclo': ciclo,
                'materia': materia_modelo,
                'provincia': provincia if nivel in ['provincial', 'municipal'] else '',
                'municipio': municipio,
                'año_actualizacion': 2025 if tipo == TipoDocumento.ACTUALIZACION_MUNICIPAL else None,
                'procesado': True,
                'chunks_count': chunks_count,
                'vigente': True,
            }
        )
        
        # Guardar archivo si no existe
        if not doc.archivo:
            from django.core.files import File
            with open(pdf_path, 'rb') as f:
                doc.archivo.save(pdf_path.name, File(f), save=True)
    
    def _mostrar_resumen(self, totales):
        """Muestra el resumen final."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING("  RESUMEN"))
        self.stdout.write("=" * 60)
        
        self.stdout.write(f"\n✓ Procesados: {totales['procesados']}")
        self.stdout.write(f"📦 Chunks totales: {totales['chunks']}")
        
        if totales['errores']:
            self.stdout.write(self.style.ERROR(f"✗ Errores: {totales['errores']}"))
        
        # Estadísticas de ChromaDB
        stats = chroma_manager.get_collection_stats()
        self.stdout.write(f"\n📊 Estado de ChromaDB:")
        for coleccion, count in stats.items():
            self.stdout.write(f"    {coleccion}: {count} chunks")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("  ✅ PROCESO COMPLETADO"))
        self.stdout.write("=" * 60)
