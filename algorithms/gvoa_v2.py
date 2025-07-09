"""
GVOA (Golden Vulture Optimization Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo bio-inspirado basado en el comportamiento de los buitres dorados.
Implementa estrategias de forrajeo, seguimiento del líder, búsqueda y exploración.

Referencias:
- Hasan et al. (2025): Griffon Vultures Optimization Algorithm (GVOA)
  Expert Systems with Applications. DOI: 10.1016/j.eswa.2025.127206
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

# Imports ya incluidos arriba


class VultureV2(Individual):
    """Vulture individual para GVOA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un vulture.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # Atributos especiales: mejor posición personal
        self.personal_best_position = None
        self.personal_best_fitness = None

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # GVOA usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar mejor personal
        self.personal_best_position = np.copy(self.position)
        self.personal_best_fitness = None

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo GVOA.
        
        Implementa cuatro fases de movimiento:
        - Following: seguimiento del líder
        - Foraging: forrajeo grupal con individuos informados
        - Search: búsqueda independiente
        - Scouting: exploración cerca del carroñeo
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        it = context.iteration
        max_it = context.max_iterations
        leader_pos = context.best_individual.position
        informed_positions = context.algorithm_params.get('informed_positions', [])
        phase = context.algorithm_params.get('phase', 'following')
        r = context.algorithm_params.get('r', 0.5)
        
        # Adaptación temporal (decrece con las iteraciones)
        decay = 1 - (it / max_it)
        # Vectores aleatorios
        r1 = np.random.random(self.dimension)
        r2 = np.random.random(self.dimension)
        
        # Posición inicial para calcular el movimiento
        new_position = np.copy(self.position)
        
        if phase == "following":
            # Fase 1: Seguimiento del líder
            # Movimiento hacia el líder con perturbación aleatoria
            new_position = (
                self.position
                + decay * r1 * (leader_pos - self.position)
                + r * r2 * (np.random.random(self.dimension) - 0.5)
            )
            
        elif (
            phase == "foraging"
            and informed_positions is not None
            and len(informed_positions) > 0
        ):
            # Fase 2: Forrajeo grupal
            # Seleccionar una posición aleatoria informada
            target_pos = random.choice(informed_positions)
            # Mover hacia esa posición con influencia del líder
            new_position = (
                self.position
                + r1 * (target_pos - self.position)
                + decay * r2 * (leader_pos - self.position)
            )
            
        elif phase == "search":
            # Fase 3: Búsqueda independiente
            # Perturbación local con probabilidad adaptativa
            a = 2 * decay  # Parámetro que decrece con el tiempo
            if random.random() < 0.5:
                # Leve perturbación en una dimensión aleatoria
                idx = random.randrange(self.dimension)
                new_position[idx] = np.clip(
                    new_position[idx] + a * (random.random() - 0.5), 0, 1
                )
            else:
                # Perturbación aleatoria en todas las dimensiones
                new_position = self.position + a * (
                    np.random.random(self.dimension) - 0.5
                )
                
        elif phase == "scouting":
            # Fase 4: Exploración cerca del carroñeo (líder)
            # Exploración adaptativa alrededor del líder
            radius = max(0.1, decay) * r  # Radio que decrece con el tiempo
            if random.random() < 0.5:
                # Exploración cercana al líder
                new_position = leader_pos + radius * (
                    np.random.random(self.dimension) - 0.5
                )
            else:
                # Exploración alejada del líder
                new_position = leader_pos + (1 + radius) * (
                    np.random.random(self.dimension) - 0.5
                )
        
        # Asegurar que la nueva posición está en el rango [0,1]
        new_position = np.clip(new_position, 0, 1)
        
        # Aceptación condicional basada en mejora o probabilidad adaptativa
        new_fit = self.problem.evaluate(new_position)
        curr_fit = self.fitness() if self._fitness is not None else self.problem.evaluate(self.position)
        
        # probabilidad de aceptación dinámica decrece con iteraciones
        r_eff = r * (1 - it / max_it)
        if new_fit < curr_fit or random.random() < r_eff:
            self.position = new_position
            self.invalidate_fitness()
            
            # Actualizar mejor personal si es mejor
            if (
                self.personal_best_fitness is None
                or new_fit < self.personal_best_fitness
            ):
                self.personal_best_position = np.copy(self.position)
                self.personal_best_fitness = new_fit


class GVOAV2(MetaheuristicAlgorithm[VultureV2]):
    
    def update_population(self) -> None:
        """
        Actualiza la población aplicando diferentes fases según el ranking.
        """
        # Iteración actual
        current_iter = len(self.convergence_curve)
        frac = current_iter / self.max_iterations
        
        # Obtener grupo élite (mejores individuos)
        elite_vultures = self.population[: self.elite_size]
        elite_positions = [v.position for v in elite_vultures]
        
        # Crear contexto base
        base_context = self._create_move_context()
        
        # Actualizar cada buitre según su posición en la población
        for i, vulture in enumerate(self.population):
            # fase dinámica basada en ranking de fitness y progreso
            if frac < 0.3:
                # early: más exploración
                phase = (
                    "scouting" if i >= int(self.population_size * frac) else "search"
                )
            else:
                # later: más explotación
                phase = (
                    "foraging"
                    if i < int(self.population_size * (1 - frac))
                    else "following"
                )
            
            # Crear contexto con fase y posiciones informadas
            context = MoveContext(
                iteration=base_context.iteration,
                max_iterations=base_context.max_iterations,
                population=base_context.population,
                best_individual=base_context.best_individual,
                algorithm_params={
                    'r': self.r,
                    'elite_size': self.elite_size,
                    'informed_positions': elite_positions,
                    'phase': phase
                }
            )
            
            # Mover el buitre
            vulture.move(context)
    """
    Golden Vulture Optimization Algorithm (GVOA) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento de forrajeo de los
    buitres dorados. Implementa múltiples estrategias de movimiento según
    la fase y el ranking de fitness.
    
    Referencias:
    - Hasan et al. (2025): Griffon Vultures Optimization Algorithm
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        elite_ratio: float = 0.2,
        r: float = 0.2,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo GVOA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            elite_ratio: Proporción de individuos élite (0.1-0.33)
            r: Radio de búsqueda inicial (0.1-0.5)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer parámetros específicos del algoritmo
        # elite_ratio para calcular elite_size
        self.elite_ratio = ParameterValidator.validate_positive_float(
            elite_ratio, "elite_ratio", min_value=0.1, max_value=0.33, inclusive_min=True
        )
        self.elite_size = max(3, int(self.population_size * self.elite_ratio))
        
        # r: radio de búsqueda inicial
        self.r = ParameterValidator.validate_positive_float(
            r, "r", min_value=0.1, max_value=0.5, inclusive_min=True
        )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de VultureV2
        """
        return VultureV2(self.problem)
    
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
                'r': self.r,
                'elite_size': self.elite_size
            }
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        GVOA ordena la población para identificar el grupo élite y
        asignar fases según el ranking de fitness.
        
        Returns:
            True - GVOA sí ordena la población
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
            "algorithm": "GVOA v2",
            "elite_ratio": self.elite_ratio,
            "elite_size": self.elite_size,
            "r": self.r,
            "phases": ["following", "foraging", "search", "scouting"]
        })
        return base_summary
