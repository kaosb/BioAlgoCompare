"""
AHA (Artificial Hummingbird Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo inspirado en el comportamiento de forrajeo de los colibríes.
Combina tres tipos de vuelo (axial, diagonal, omnidireccional) con
tres modos de forrajeo (guiado, territorial, migratorio) y usa una
tabla de memoria para evitar revisitar posiciones.

Referencias:
- Zhao, Wang & Mirjalili (2022): Artificial hummingbird algorithm: A new bio-inspired optimizer with its engineering applications
  https://doi.org/10.1016/j.cma.2021.114194
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

# Imports adicionales no necesarios (ya están arriba)


class HummingbirdV2(Individual):
    """Hummingbird individual para AHA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un hummingbird.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # Atributo especial: posición del mejor personal
        self.personal_best_position = None

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # AHA usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar mejor personal
        self.personal_best_position = self.position.copy()

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve el colibrí según las estrategias de vuelo y forrajeo de AHA.
        
        Combina tres tipos de vuelo:
        - Axial: movimiento en una sola dimensión
        - Diagonal: movimiento en subconjunto de dimensiones
        - Omnidireccional: movimiento en todas las direcciones
        
        Con tres modos de forrajeo:
        - Guiado: hacia el mejor individuo
        - Territorial: exploración local
        - Migratorio: hacia otro individuo aleatorio
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best_individual = context.best_individual
        population = context.population
        memory_table = context.algorithm_params.get('memory_table', set())
        step_size = context.algorithm_params.get('step_size', 0.1)
        
        # Selección aleatoria del tipo de vuelo
        flight_type = np.random.choice(["axial", "diagonal", "omnidirectional"])
        
        # Selección aleatoria del modo de forrajeo
        forage_mode = np.random.choice(["guided", "territorial", "migratory"])
        
        new_position = self.position.copy()
        dim = self.dimension
        
        # Generar dirección según el tipo de vuelo
        if flight_type == "axial":
            # Movimiento en una sola dimensión
            axis = np.random.randint(0, dim)
            step = np.random.uniform(-1, 1)
            direction = np.zeros(dim)
            direction[axis] = step
        elif flight_type == "diagonal":
            # Movimiento en diagonal (subconjunto de dimensiones)
            direction = np.random.uniform(-1, 1, size=dim)
            # Para simular diagonal, poner algunos ceros aleatorios
            zero_mask = np.random.rand(dim) < 0.5
            direction[zero_mask] = 0
        else:  # omnidireccional
            # Movimiento en cualquier dirección
            direction = np.random.uniform(-1, 1, size=dim)
        
        # Normalizar dirección
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm
        
        # Aplicar modo de forrajeo
        if forage_mode == "guided":
            # Movimiento hacia el mejor individuo con memoria
            diff = best_individual.position - self.position
            # Usar personal_best_position si está disponible
            if hasattr(self, 'personal_best_position') and self.personal_best_position is not None:
                diff = self.personal_best_position - self.position
            new_position = self.position + step_size * diff + step_size * direction
        elif forage_mode == "territorial":
            # Perturbación aleatoria local
            new_position = self.position + step_size * direction * np.random.uniform(-1, 1)
        else:  # migratory
            # Hacia un individuo aleatorio
            other = random.choice([ind for ind in population if ind is not self])
            diff = other.position - self.position
            new_position = self.position + step_size * diff + step_size * direction
        
        # Asegurar que los valores estén dentro del rango [0, 1]
        new_position = np.clip(new_position, 0, 1)
        
        # Discretizar posición para la tabla de memoria
        discretized_pos = tuple(np.round(new_position, decimals=6))
        
        # Verificar si la posición ya está en la memoria
        if discretized_pos in memory_table:
            # Si ya visitado, hacer un pequeño movimiento aleatorio
            new_position += step_size * np.random.uniform(-1, 1, size=dim)
            new_position = np.clip(new_position, 0, 1)
            discretized_pos = tuple(np.round(new_position, decimals=6))
        
        # Actualizar posición
        self.position = new_position
        
        # Actualizar tabla de memoria
        memory_table.add(discretized_pos)
        
        # Invalidar fitness para recalcular
        self.invalidate_fitness()


class AHAV2(MetaheuristicAlgorithm[HummingbirdV2]):
    """
    Artificial Hummingbird Algorithm (AHA) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento de forrajeo de los colibríes.
    Utiliza múltiples estrategias de vuelo y forrajeo, junto con una tabla de memoria
    para evitar la revisión de posiciones ya exploradas.
    
    Referencias:
    - Zhao, Wang & Mirjalili (2022): Artificial hummingbird algorithm
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        step_size: float = 0.1,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo AHA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            step_size: Tamaño del paso para el movimiento (0.01-0.5)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Parámetros específicos del algoritmo
        self.memory_table = set()  # Tabla de memoria compartida
        
        # Validar y establecer el tamaño del paso
        self.step_size = ParameterValidator.validate_positive_float(
            step_size, "step_size", min_value=0.01, max_value=0.5, inclusive_min=True
        )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de HummingbirdV2
        """
        return HummingbirdV2(self.problem)
    
    def _initialize_algorithm(self) -> None:
        """
        Inicialización específica del algoritmo después de crear la población.
        """
        super()._initialize_algorithm()
        # Agregar posiciones iniciales a la tabla de memoria
        for ind in self.population:
            discretized_pos = tuple(np.round(ind.position, decimals=6))
            self.memory_table.add(discretized_pos)
    
    def _after_iteration(self) -> None:
        """
        Operaciones después de cada iteración.
        """
        super()._after_iteration()
        # Actualizar personal best de cada individuo
        for ind in self.population:
            if ind._fitness is not None:
                # Calcular fitness del personal best actual
                pb_fitness = self.problem.evaluate(ind.personal_best_position)
                if ind.fitness() < pb_fitness:
                    ind.personal_best_position = ind.position.copy()
    
    def _create_move_context(self) -> MoveContext:
        """
        Crea el contexto de movimiento para la iteración actual.
        
        Returns:
            MoveContext con información del estado actual
        """
        return MoveContext(
            iteration=len(self.convergence_curve),
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution,
            algorithm_params={
                'memory_table': self.memory_table,
                'step_size': self.step_size
            }
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        AHA ordena la población por fitness para identificar los mejores
        individuos y aplicar estrategias basadas en el rendimiento.
        
        Returns:
            True - AHA sí ordena la población
        """
        return True
    
    def summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del algoritmo y sus parámetros.
        
        Returns:
            Diccionario con información del algoritmo
        """
        base_summary = super().summary()
        base_summary.update({
            "algorithm": "AHA v2",
            "step_size": self.step_size,
            "memory_table_size": len(self.memory_table),
            "uses_memory": True,
            "flight_types": ["axial", "diagonal", "omnidirectional"],
            "forage_modes": ["guided", "territorial", "migratory"]
        })
        return base_summary
