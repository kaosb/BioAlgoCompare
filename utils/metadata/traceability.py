"""
Sistema de trazabilidad experimental completa.

Proporciona capacidades avanzadas de tracking, auditoría y análisis
de la cadena de ejecución experimental.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import hashlib
import pickle
from contextlib import contextmanager
from dataclasses import dataclass, field
import threading
import uuid

from utils.metadata.metadata_manager import ExperimentMetadata, MetadataManager


class EventType(Enum):
    """Tipos de eventos en el sistema de trazabilidad."""
    EXPERIMENT_START = "experiment_start"
    EXPERIMENT_END = "experiment_end"
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    POPULATION_INIT = "population_init"
    POPULATION_UPDATE = "population_update"
    SOLUTION_FOUND = "solution_found"
    PARAMETER_CHANGE = "parameter_change"
    ERROR_OCCURRED = "error_occurred"
    WARNING_RAISED = "warning_raised"
    CHECKPOINT_SAVED = "checkpoint_saved"
    RESOURCE_LIMIT = "resource_limit"
    USER_ANNOTATION = "user_annotation"


@dataclass
class TraceEvent:
    """Evento de trazabilidad."""
    event_id: str
    experiment_id: str
    timestamp: str
    event_type: EventType
    component: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'event_id': self.event_id,
            'experiment_id': self.experiment_id,
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'component': self.component,
            'data': self.data,
            'metadata': self.metadata
        }
    
    def calculate_hash(self) -> str:
        """Calcula hash del evento para integridad."""
        data_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


class TraceabilityDB:
    """Base de datos para almacenar eventos de trazabilidad."""
    
    def __init__(self, db_path: Path):
        """
        Inicializa la base de datos.
        
        Args:
            db_path: Ruta del archivo de base de datos
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
        # Thread-local storage para conexiones
        self._local = threading.local()
    
    def _init_db(self):
        """Inicializa esquema de base de datos."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    data TEXT NOT NULL,
                    metadata TEXT,
                    hash TEXT NOT NULL,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_experiment 
                ON events(experiment_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON events(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON events(event_type)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiment_chains (
                    chain_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    parent_experiment_id TEXT,
                    relationship TEXT,
                    metadata TEXT,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)
            
            conn.commit()
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Obtiene conexión thread-safe."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def add_event(self, event: TraceEvent):
        """
        Añade un evento a la base de datos.
        
        Args:
            event: Evento a añadir
        """
        event_hash = event.calculate_hash()
        
        self.connection.execute("""
            INSERT INTO events 
            (event_id, experiment_id, timestamp, event_type, 
             component, data, metadata, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            event.experiment_id,
            event.timestamp,
            event.event_type.value,
            event.component,
            json.dumps(event.data),
            json.dumps(event.metadata),
            event_hash
        ))
        
        self.connection.commit()
    
    def get_events(self,
                   experiment_id: Optional[str] = None,
                   event_type: Optional[EventType] = None,
                   component: Optional[str] = None,
                   start_time: Optional[str] = None,
                   end_time: Optional[str] = None,
                   limit: Optional[int] = None) -> List[TraceEvent]:
        """
        Obtiene eventos según filtros.
        
        Args:
            experiment_id: Filtrar por experimento
            event_type: Filtrar por tipo de evento
            component: Filtrar por componente
            start_time: Tiempo inicial (ISO format)
            end_time: Tiempo final (ISO format)
            limit: Límite de resultados
            
        Returns:
            Lista de eventos
        """
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if experiment_id:
            query += " AND experiment_id = ?"
            params.append(experiment_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if component:
            query += " AND component = ?"
            params.append(component)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.connection.execute(query, params)
        
        events = []
        for row in cursor:
            events.append(TraceEvent(
                event_id=row['event_id'],
                experiment_id=row['experiment_id'],
                timestamp=row['timestamp'],
                event_type=EventType(row['event_type']),
                component=row['component'],
                data=json.loads(row['data']),
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            ))
        
        return events
    
    def verify_integrity(self, experiment_id: str) -> Tuple[bool, List[str]]:
        """
        Verifica integridad de eventos de un experimento.
        
        Args:
            experiment_id: ID del experimento
            
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        cursor = self.connection.execute(
            "SELECT * FROM events WHERE experiment_id = ? ORDER BY timestamp",
            (experiment_id,)
        )
        
        for row in cursor:
            # Reconstruir evento
            event = TraceEvent(
                event_id=row['event_id'],
                experiment_id=row['experiment_id'],
                timestamp=row['timestamp'],
                event_type=EventType(row['event_type']),
                component=row['component'],
                data=json.loads(row['data']),
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            
            # Verificar hash
            expected_hash = event.calculate_hash()
            if expected_hash != row['hash']:
                issues.append(f"Hash mismatch for event {event.event_id}")
        
        return len(issues) == 0, issues
    
    def add_experiment_chain(self,
                            experiment_id: str,
                            parent_experiment_id: str,
                            relationship: str,
                            metadata: Optional[Dict[str, Any]] = None):
        """
        Añade relación entre experimentos.
        
        Args:
            experiment_id: Experimento hijo
            parent_experiment_id: Experimento padre
            relationship: Tipo de relación (continuation, variation, etc.)
            metadata: Metadatos adicionales
        """
        chain_id = f"{parent_experiment_id}->{experiment_id}"
        
        self.connection.execute("""
            INSERT INTO experiment_chains
            (chain_id, experiment_id, parent_experiment_id, relationship, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            chain_id,
            experiment_id,
            parent_experiment_id,
            relationship,
            json.dumps(metadata or {})
        ))
        
        self.connection.commit()
    
    def get_experiment_lineage(self, experiment_id: str) -> Dict[str, Any]:
        """
        Obtiene linaje completo de un experimento.
        
        Args:
            experiment_id: ID del experimento
            
        Returns:
            Árbol de linaje
        """
        lineage = {
            'experiment_id': experiment_id,
            'parents': [],
            'children': []
        }
        
        # Buscar padres
        cursor = self.connection.execute("""
            SELECT * FROM experiment_chains 
            WHERE experiment_id = ?
        """, (experiment_id,))
        
        for row in cursor:
            lineage['parents'].append({
                'experiment_id': row['parent_experiment_id'],
                'relationship': row['relationship'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            })
        
        # Buscar hijos
        cursor = self.connection.execute("""
            SELECT * FROM experiment_chains 
            WHERE parent_experiment_id = ?
        """, (experiment_id,))
        
        for row in cursor:
            lineage['children'].append({
                'experiment_id': row['experiment_id'],
                'relationship': row['relationship'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            })
        
        return lineage


class ExperimentTracer:
    """Trazador de experimentos con capacidades avanzadas."""
    
    def __init__(self,
                 metadata_manager: MetadataManager,
                 db_path: Optional[Path] = None,
                 auto_trace: bool = True,
                 trace_level: str = "standard"):
        """
        Inicializa el trazador.
        
        Args:
            metadata_manager: Gestor de metadatos
            db_path: Ruta de la base de datos
            auto_trace: Si trazar automáticamente eventos
            trace_level: Nivel de detalle (minimal, standard, detailed)
        """
        self.metadata_manager = metadata_manager
        self.db = TraceabilityDB(db_path or Path("traceability.db"))
        self.auto_trace = auto_trace
        self.trace_level = trace_level
        
        # Experimento actual en contexto
        self._current_experiment: Optional[str] = None
        self._trace_stack: List[str] = []
    
    @contextmanager
    def trace_experiment(self, experiment_id: str):
        """
        Context manager para trazar un experimento.
        
        Args:
            experiment_id: ID del experimento
        """
        # Guardar contexto anterior
        previous = self._current_experiment
        self._current_experiment = experiment_id
        self._trace_stack.append(experiment_id)
        
        # Evento de inicio
        if self.auto_trace:
            self.trace_event(
                EventType.EXPERIMENT_START,
                component="experiment_tracer",
                data={'experiment_id': experiment_id}
            )
        
        try:
            yield self
        finally:
            # Evento de fin
            if self.auto_trace:
                self.trace_event(
                    EventType.EXPERIMENT_END,
                    component="experiment_tracer",
                    data={'experiment_id': experiment_id}
                )
            
            # Restaurar contexto
            self._trace_stack.pop()
            self._current_experiment = previous
    
    def trace_event(self,
                   event_type: EventType,
                   component: str,
                   data: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None,
                   experiment_id: Optional[str] = None):
        """
        Registra un evento de trazabilidad.
        
        Args:
            event_type: Tipo de evento
            component: Componente que genera el evento
            data: Datos del evento
            metadata: Metadatos adicionales
            experiment_id: ID del experimento (usa actual si no se proporciona)
        """
        # Determinar experimento
        exp_id = experiment_id or self._current_experiment
        if not exp_id:
            raise ValueError("No experiment context available")
        
        # Filtrar según nivel
        if not self._should_trace(event_type):
            return
        
        # Crear evento
        event = TraceEvent(
            event_id=str(uuid.uuid4()),
            experiment_id=exp_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            component=component,
            data=data,
            metadata=metadata or {}
        )
        
        # Añadir stack trace si hay
        if self._trace_stack:
            event.metadata['trace_stack'] = self._trace_stack.copy()
        
        # Guardar en BD
        self.db.add_event(event)
    
    def trace_iteration(self, iteration: int, metrics: Dict[str, Any]):
        """
        Traza una iteración del algoritmo.
        
        Args:
            iteration: Número de iteración
            metrics: Métricas de la iteración
        """
        self.trace_event(
            EventType.ITERATION_END,
            component="algorithm",
            data={
                'iteration': iteration,
                'metrics': metrics
            }
        )
        
        # También actualizar metadatos
        if self._current_experiment:
            self.metadata_manager.update_execution(
                self._current_experiment,
                iteration,
                metrics
            )
    
    def trace_solution(self,
                      solution: Any,
                      fitness: float,
                      iteration: int,
                      is_improvement: bool = True):
        """
        Traza el descubrimiento de una solución.
        
        Args:
            solution: Solución encontrada
            fitness: Fitness de la solución
            iteration: Iteración donde se encontró
            is_improvement: Si es una mejora
        """
        self.trace_event(
            EventType.SOLUTION_FOUND,
            component="algorithm",
            data={
                'fitness': fitness,
                'iteration': iteration,
                'is_improvement': is_improvement,
                'solution_summary': str(solution)[:100]  # Resumen
            }
        )
    
    def trace_error(self,
                   error: Exception,
                   component: str,
                   context: Optional[Dict[str, Any]] = None):
        """
        Traza un error.
        
        Args:
            error: Excepción ocurrida
            component: Componente donde ocurrió
            context: Contexto adicional
        """
        import traceback
        
        self.trace_event(
            EventType.ERROR_OCCURRED,
            component=component,
            data={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'context': context or {}
            }
        )
    
    def annotate(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Añade anotación manual al experimento.
        
        Args:
            message: Mensaje de anotación
            data: Datos adicionales
        """
        self.trace_event(
            EventType.USER_ANNOTATION,
            component="user",
            data={
                'message': message,
                'annotation_data': data or {}
            }
        )
    
    def create_checkpoint(self,
                         checkpoint_data: Any,
                         checkpoint_name: str,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Crea checkpoint del experimento.
        
        Args:
            checkpoint_data: Datos a guardar
            checkpoint_name: Nombre del checkpoint
            metadata: Metadatos adicionales
            
        Returns:
            ID del checkpoint
        """
        checkpoint_id = f"ckpt_{self._current_experiment}_{checkpoint_name}_{uuid.uuid4().hex[:8]}"
        
        # Guardar checkpoint
        checkpoint_path = Path("checkpoints") / f"{checkpoint_id}.pkl"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(checkpoint_path, 'wb') as f:
            pickle.dump({
                'checkpoint_id': checkpoint_id,
                'experiment_id': self._current_experiment,
                'checkpoint_name': checkpoint_name,
                'timestamp': datetime.now().isoformat(),
                'data': checkpoint_data,
                'metadata': metadata or {}
            }, f)
        
        # Trazar evento
        self.trace_event(
            EventType.CHECKPOINT_SAVED,
            component="checkpoint_system",
            data={
                'checkpoint_id': checkpoint_id,
                'checkpoint_name': checkpoint_name,
                'checkpoint_path': str(checkpoint_path)
            },
            metadata=metadata
        )
        
        return checkpoint_id
    
    def get_experiment_timeline(self, experiment_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene timeline completo de un experimento.
        
        Args:
            experiment_id: ID del experimento
            
        Returns:
            Lista de eventos ordenados cronológicamente
        """
        events = self.db.get_events(experiment_id=experiment_id)
        
        timeline = []
        for event in events:
            timeline.append({
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'component': event.component,
                'summary': self._summarize_event(event),
                'data': event.data
            })
        
        return timeline
    
    def generate_audit_report(self,
                            experiment_id: str,
                            include_integrity_check: bool = True) -> str:
        """
        Genera reporte de auditoría para un experimento.
        
        Args:
            experiment_id: ID del experimento
            include_integrity_check: Si incluir verificación de integridad
            
        Returns:
            Reporte en formato markdown
        """
        report = f"# Audit Report for Experiment {experiment_id}\n\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        # Metadatos del experimento
        try:
            exp_meta = self.metadata_manager.load_experiment(experiment_id)
            report += "## Experiment Metadata\n"
            report += f"- **Algorithm:** {exp_meta['algorithm']['name']}\n"
            report += f"- **Problem:** {exp_meta['problem']['instance']}\n"
            report += f"- **Start:** {exp_meta['execution']['start_time']}\n"
            report += f"- **End:** {exp_meta['execution']['end_time']}\n\n"
        except:
            report += "## Experiment Metadata\n"
            report += "⚠️ Metadata not available\n\n"
        
        # Timeline de eventos
        report += "## Event Timeline\n"
        timeline = self.get_experiment_timeline(experiment_id)
        
        for event in timeline[:50]:  # Primeros 50 eventos
            report += f"- **{event['timestamp']}** [{event['event_type']}] "
            report += f"{event['component']}: {event['summary']}\n"
        
        if len(timeline) > 50:
            report += f"\n... and {len(timeline) - 50} more events\n"
        
        report += "\n"
        
        # Estadísticas de eventos
        report += "## Event Statistics\n"
        event_counts = {}
        for event in timeline:
            event_type = event['event_type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        for event_type, count in sorted(event_counts.items()):
            report += f"- {event_type}: {count}\n"
        
        report += "\n"
        
        # Verificación de integridad
        if include_integrity_check:
            report += "## Integrity Verification\n"
            is_valid, issues = self.db.verify_integrity(experiment_id)
            
            if is_valid:
                report += "✅ All events passed integrity check\n"
            else:
                report += f"❌ Found {len(issues)} integrity issues:\n"
                for issue in issues:
                    report += f"- {issue}\n"
        
        # Linaje del experimento
        report += "\n## Experiment Lineage\n"
        lineage = self.db.get_experiment_lineage(experiment_id)
        
        if lineage['parents']:
            report += "**Parents:**\n"
            for parent in lineage['parents']:
                report += f"- {parent['experiment_id']} ({parent['relationship']})\n"
        
        if lineage['children']:
            report += "**Children:**\n"
            for child in lineage['children']:
                report += f"- {child['experiment_id']} ({child['relationship']})\n"
        
        if not lineage['parents'] and not lineage['children']:
            report += "No lineage relationships found\n"
        
        return report
    
    def _should_trace(self, event_type: EventType) -> bool:
        """Determina si un evento debe ser trazado según el nivel."""
        if self.trace_level == "minimal":
            return event_type in [
                EventType.EXPERIMENT_START,
                EventType.EXPERIMENT_END,
                EventType.ERROR_OCCURRED
            ]
        elif self.trace_level == "standard":
            return event_type not in [
                EventType.ITERATION_START,
                EventType.POPULATION_UPDATE
            ]
        else:  # detailed
            return True
    
    def _summarize_event(self, event: TraceEvent) -> str:
        """Genera resumen de un evento."""
        if event.event_type == EventType.SOLUTION_FOUND:
            return f"Found solution with fitness {event.data.get('fitness', 'N/A')}"
        elif event.event_type == EventType.ERROR_OCCURRED:
            return f"{event.data.get('error_type', 'Error')}: {event.data.get('error_message', 'N/A')}"
        elif event.event_type == EventType.ITERATION_END:
            return f"Iteration {event.data.get('iteration', 'N/A')} completed"
        elif event.event_type == EventType.USER_ANNOTATION:
            return event.data.get('message', 'User annotation')
        else:
            return event.event_type.value.replace('_', ' ').title()


def create_experiment_tracer(metadata_manager: MetadataManager, **kwargs) -> ExperimentTracer:
    """Factory function para crear ExperimentTracer."""
    return ExperimentTracer(metadata_manager, **kwargs)