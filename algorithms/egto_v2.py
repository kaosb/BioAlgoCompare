"""
EGTO (Enhanced Gorilla Troops Optimizer) - Version 2
Implementación usando la nueva arquitectura base_v2.

Variante mejorada del GTO que incorpora estrategias del Marine Predators Algorithm (MPA).
Utiliza tres fases de velocidad (alta, media, baja) con diferentes comportamientos
de búsqueda y movimiento browniano/Lévy para mejorar la exploración.

Referencias:
- Seyyedabbasi et al. (2022): I-GWO and Ex-GWO: improved algorithms of the Grey Wolf Optimizer to solve global optimization problems
- Faramarzi et al. (2020): Marine Predators Algorithm: A nature-inspired metaheuristic
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator
from utils.math_operators import levy_flight

# Imports adicionales necesarios
import math


class EnhancedGorillaV2(Individual):
    """EnhancedGorilla individual para EGTO versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un enhancedgorilla.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # EGTO no requiere atributos especiales adicionales
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # EGTO usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # No hay atributos especiales que inicializar

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo EGTO con estrategias MPA.
        
        El movimiento se divide en tres fases basadas en la iteración:
        1. Alta velocidad: exploración con movimiento browniano
        2. Media velocidad: mezcla aleatoria
        3. Baja velocidad: comportamiento de depredador con perturbación
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best = context.best_individual
        iteration = context.iteration
        max_iterations = context.max_iterations
        
        # Parámetros del algoritmo
        P = context.algorithm_params.get('P', 0.5)
        CF = context.algorithm_params.get('CF', 0.5)
        FADs = context.algorithm_params.get('FADs', 0.2)
        
        dim = self.dimension
        
        # Límites del problema (siempre [0,1] para VRP)
        lower_bounds = np.zeros(dim)
        upper_bounds = np.ones(dim)
        
        if iteration < max_iterations / 3:
            # Alta velocidad (fase exploratoria con movimiento browniano)
            RB = np.random.normal(0, 1, dim)
            S = np.random.rand(dim) * self.position
            delta = P * RB * S
            self.position += delta
            
        elif iteration < 2 * max_iterations / 3:
            # Media velocidad (mezcla aleatoria)
            R = np.random.rand(dim)
            S = R * (best.position - R * self.position)
            delta = P * CF * S
            self.position += delta
            
        else:
            # Baja velocidad (comportamiento de depredador, perturbación aleatoria)
            r1 = random.random()
            if r1 < FADs:
                # Vuelo de Lévy para exploración
                LF = levy_flight(dim, beta=1.5, scale=0.01)
                self.position += LF * self.position
            else:
                # Movimiento hacia la mejor solución
                step = best.position - self.position
                self.position += P * step
        
        # Asegurar que los valores estén dentro del rango [0, 1]
        self.position = np.clip(self.position, lower_bounds, upper_bounds)
        
        # Invalidar fitness para recalcular
        self.invalidate_fitness()


class EGTOV2(MetaheuristicAlgorithm[EnhancedGorillaV2]):
    """
    Enhanced Gorilla Troops Optimizer (EGTO) - Versión 2.
    
    Variante mejorada del GTO que incorpora estrategias del Marine Predators Algorithm.
    Divide la búsqueda en tres fases de velocidad con diferentes comportamientos
    para balancear exploración y explotación de manera más efectiva.
    
    Referencias:
    - Seyyedabbasi et al. (2022): Enhanced algorithms for optimization
    - Faramarzi et al. (2020): Marine Predators Algorithm
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        P: float = 0.5,
        CF: float = 0.5,
        FADs: float = 0.2,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo EGTO v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            P: Factor de perturbación (0.3-0.7)
            CF: Factor de combinación (0.3-0.7)
            FADs: Probabilidad de vuelo de Lévy (0.0-1.0)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer parámetros específicos del algoritmo
        # P: factor de perturbación
        self.P = ParameterValidator.validate_positive_float(
            P, "P", min_value=0.3, max_value=0.7, inclusive_min=True
        )
        
        # CF: factor de combinación
        self.CF = ParameterValidator.validate_positive_float(
            CF, "CF", min_value=0.3, max_value=0.7, inclusive_min=True
        )
        
        # FADs: probabilidad de vuelo de Lévy
        self.FADs = ParameterValidator.validate_probability(FADs, "FADs")
        if self.FADs > 0.4:
            import warnings
            warnings.warn(
                f"FADs={self.FADs} es alto. Se recomienda usar valores <= 0.4.",
                UserWarning
            )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de EnhancedGorillaV2
        """
        return EnhancedGorillaV2(self.problem)
    
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
                'P': self.P,
                'CF': self.CF,
                'FADs': self.FADs
            }
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        EGTO ordena la población por fitness en cada iteración para
        identificar las mejores soluciones y aplicar estrategias basadas en ranking.
        
        Returns:
            True - EGTO sí ordena la población
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
            "algorithm": "EGTO v2",
            "P": self.P,
            "CF": self.CF,
            "FADs": self.FADs,
            "uses_brownian_motion": True,
            "uses_levy_flight": True
        })
        return base_summary
