"""
Comando Django para cargar proyectos docentes a ChromaDB.

Uso:
    # Cargar un proyecto específico
    python manage.py cargar_proyecto archivo.docx --docente 1 --institucion 1 --grado 4
    
    # Cargar con materias específicas
    python manage.py cargar_proyecto archivo.pdf --docente 1 --institucion 1 --grado 4 --materias matematicas,ciencias_naturales
    
    # Reemplazar proyecto existente
    python manage.py cargar_proyecto archivo.docx --docente 1 --institucion 1 --grado 4 --reemplazar

Notas:
    - Soporta archivos .docx y .pdf
    - Detecta automáticamente secciones, materias y si es integrador
    - Los chunks se guardan en la colección 'proyectos_docentes' de ChromaDB
"""

from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

from apps.ai.core.chroma import chroma_manager
from utils.proyecto_processor import ProyectoProcessor


class Command(BaseCommand):
    help = 'Carga un proyecto docente a ChromaDB'

    def add_arguments(self, parser):
        parser.add_argument(
            'archivo',
            type=str,
            help='Ruta al archivo del proyecto (.docx o .pdf)',
        )
        parser.add_argument(
            '--docente',
            type=int,
            required=True,
            help='ID del docente',
        )
        parser.add_argument(
            '--institucion',
            type=int,
            required=True,
            help='ID de la institución',
        )
        parser.add_argument(
            '--grado',
            type=str,
            required=False,
            help='Grado del docente (ej: 4, sala_5)',
        )
        parser.add_argument(
            '--materias',
            type=str,
            required=False,
            help='Materias separadas por coma (ej: matematicas,ciencias_naturales)',
        )
        parser.add_argument(
            '--año',
            type=int,
            required=False,
            help='Año del proyecto',
        )
        parser.add_argument(
            '--proyecto-id',
            type=str,
            required=False,
            help='ID único del proyecto (se genera automáticamente si no se provee)',
        )
        parser.add_argument(
            '--reemplazar',
            action='store_true',
            help='Elimina chunks anteriores del mismo docente antes de cargar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('  CARGADOR DE PROYECTOS DOCENTES'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        
        # Obtener opciones
        archivo = Path(options['archivo'])
        docente_id = options['docente']
        institucion_id = options['institucion']
        grado = options.get('grado')
        materias_str = options.get('materias')
        año = options.get('año')
        proyecto_id = options.get('proyecto_id')
        reemplazar = options['reemplazar']
        
        # Validar archivo
        if not archivo.exists():
            raise CommandError(f"No existe el archivo: {archivo}")
        
        ext = archivo.suffix.lower()
        if ext not in ['.docx', '.pdf']:
            raise CommandError(f"Formato no soportado: {ext}. Use .docx o .pdf")
        
        # Parsear materias
        materias = None
        if materias_str:
            materias = [m.strip() for m in materias_str.split(',')]
        
        self.stdout.write(f"\n📄 Archivo: {archivo.name}")
        self.stdout.write(f"👤 Docente ID: {docente_id}")
        self.stdout.write(f"🏫 Institución ID: {institucion_id}")
        if grado:
            self.stdout.write(f"📚 Grado: {grado}")
        if materias:
            self.stdout.write(f"📖 Materias: {', '.join(materias)}")
        self.stdout.write("-" * 60)
        
        # Reemplazar si se solicita
        if reemplazar:
            self._eliminar_chunks_anteriores(docente_id, proyecto_id)
        
        # Procesar
        try:
            processor = ProyectoProcessor()
            chunks = processor.process_proyecto(
                file_path=str(archivo),
                docente_id=docente_id,
                institucion_id=institucion_id,
                grado=grado,
                materias=materias,
                año_proyecto=año,
                proyecto_id=proyecto_id,
            )
            
            if not chunks:
                raise CommandError("No se generaron chunks del proyecto")
            
            stats = processor.get_stats()
            
            self.stdout.write(f"\n✓ Formato detectado: {stats['formato']}")
            self.stdout.write(f"✓ Caracteres procesados: {stats['caracteres_totales']}")
            self.stdout.write(f"✓ Chunks generados: {len(chunks)}")
            self.stdout.write(f"✓ Es integrador: {'Sí' if chunks[0].metadata.es_integrador else 'No'}")
            
            # Mostrar secciones
            self.stdout.write(f"\n📋 Secciones detectadas:")
            for chunk in chunks:
                materias_chunk = chunk.metadata.materias
                materias_str = ', '.join(materias_chunk) if materias_chunk else 'general'
                self.stdout.write(f"    [{chunk.metadata.seccion}] → {materias_str}")
            
            # Preparar para ChromaDB
            documents = [c.texto for c in chunks]
            metadatas = [c.metadata.to_dict() for c in chunks]
            ids = [c.id for c in chunks]
            
            # Cargar a ChromaDB
            self.stdout.write(f"\n⏳ Cargando a ChromaDB...")
            chroma_manager.add_to_proyectos(documents, metadatas, ids)
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Proyecto cargado exitosamente"))
            self.stdout.write(f"   Título: {chunks[0].metadata.titulo}")
            self.stdout.write(f"   ID: {chunks[0].metadata.proyecto_id}")
            self.stdout.write(f"   Chunks en ChromaDB: {len(chunks)}")
            
            # Stats finales
            stats_chroma = chroma_manager.get_collection_stats()
            self.stdout.write(f"\n📊 Total en proyectos_docentes: {stats_chroma['proyectos_docentes']} chunks")
            
        except Exception as e:
            raise CommandError(f"Error procesando proyecto: {e}")
        
        self.stdout.write("\n" + "=" * 60)
    
    def _eliminar_chunks_anteriores(self, docente_id: int, proyecto_id: str = None):
        """Elimina chunks anteriores del docente."""
        self.stdout.write(f"\n⚠️  Eliminando chunks anteriores del docente {docente_id}...")
        
        try:
            # Obtener IDs existentes
            collection = chroma_manager.proyectos_docentes
            
            # Buscar por docente_id
            results = collection.get(
                where={"docente_id": docente_id}
            )
            
            if results and results['ids']:
                # Si hay proyecto_id específico, filtrar solo esos
                if proyecto_id:
                    ids_a_eliminar = [
                        id for id, meta in zip(results['ids'], results['metadatas'])
                        if meta.get('proyecto_id') == proyecto_id
                    ]
                else:
                    ids_a_eliminar = results['ids']
                
                if ids_a_eliminar:
                    collection.delete(ids=ids_a_eliminar)
                    self.stdout.write(f"    ✓ Eliminados {len(ids_a_eliminar)} chunks anteriores")
                else:
                    self.stdout.write(f"    ℹ No había chunks anteriores")
            else:
                self.stdout.write(f"    ℹ No había chunks anteriores")
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"    ! Error al eliminar: {e}"))
