"""
EWA (Earthworm Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo bio-inspirado basado en el comportamiento de los gusanos de tierra.
Utiliza mecanismos de reproducción (auto-replicación y crossover) combinados
con mutación de Cauchy para balancear exploración y explotación.

Referencias:
- Wang et al. (2018): Earthworm optimisation algorithm: a bio-inspired metaheuristic algorithm for global optimisation problems
  https://doi.org/10.1504/IJBIC.2018.093328
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

# Imports adicionales no necesarios (ya están arriba)


class EarthwormV2(Individual):
    """Earthworm individual para EWA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un earthworm.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # EWA no requiere atributos especiales adicionales

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # EWA usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # No hay atributos especiales que inicializar

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve el gusano según las estrategias de reproducción de EWA.
        
        Implementa dos tipos de reproducción:
        1. Auto-replicación con modificación (similarity)
        2. Crossover uniforme con el mejor individuo
        
        Seguido de mutación de Cauchy para exploración adicional.
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best_worm = context.best_individual
        generation = context.iteration
        alpha = context.algorithm_params.get('alpha', 0.8)
        beta = context.algorithm_params.get('beta', 0.2)
        gamma = context.algorithm_params.get('gamma', 0.99)
        
        # Límites del problema (siempre [0,1] para VRP)
        LB = np.zeros(self.dimension)
        UB = np.ones(self.dimension)
        
        # Reproducción 1: auto-replicación con modificación
        u1 = UB + LB - alpha * self.position
        
        # Reproducción 2: crossover uniforme con mejor gusano
        u12 = np.copy(self.position)
        u22 = np.copy(best_worm.position)
        
        for k in range(self.dimension):
            if random.random() > 0.5:
                u12[k] = self.position[k]
                u22[k] = best_worm.position[k]
            else:
                u12[k] = best_worm.position[k]
                u22[k] = self.position[k]
        
        # Seleccionar uno de los dos descendientes
        u2 = u12 if random.random() < 0.5 else u22
        
        # Suma ponderada con factor de enfriamiento
        beta_t = beta * (gamma ** generation)
        u_prime = beta_t * u1 + (1 - beta_t) * u2
        
        # Mutación de Cauchy
        W = np.mean(self.position)  # Peso medio de la posición actual
        C_d = np.random.standard_cauchy(size=self.dimension)
        u_final = u_prime + W * C_d
        
        # Asegurar que los valores estén dentro del rango [0, 1]
        self.position = np.clip(u_final, LB, UB)
        
        # Invalidar fitness para recalcular
        self.invalidate_fitness()


class EWAV2(MetaheuristicAlgorithm[EarthwormV2]):
    """
    Earthworm Algorithm (EWA) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento reproductivo de los gusanos
    de tierra. Combina estrategias de auto-replicación y crossover con mutación
    de Cauchy para lograr un balance entre exploración y explotación.
    
    Referencias:
    - Wang et al. (2018): Earthworm optimisation algorithm
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        alpha: float = 0.8,
        beta: float = 0.2,
        gamma: float = 0.99,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo EWA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            alpha: Parámetro de intensificación (0.5-0.9)
            beta: Parámetro de exploración (0.1-0.5)
            gamma: Factor de enfriamiento para beta (0.9-0.999)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer parámetros específicos del algoritmo
        # alpha: intensificación
        self.alpha = ParameterValidator.validate_positive_float(
            alpha, "alpha", min_value=0.5, max_value=0.9, inclusive_min=True
        )
        
        # beta: exploración
        self.beta = ParameterValidator.validate_positive_float(
            beta, "beta", min_value=0.1, max_value=0.5, inclusive_min=True
        )
        
        # gamma: factor de enfriamiento
        self.gamma = ParameterValidator.validate_positive_float(
            gamma, "gamma", min_value=0.9, max_value=0.999, inclusive_min=True
        )
        
        # Validación cruzada
        if self.alpha + self.beta > 1.0:
            import warnings
            warnings.warn(
                f"alpha + beta = {self.alpha + self.beta} > 1.0. "
                "Esto puede causar comportamiento no deseado.",
                UserWarning
            )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de EarthwormV2
        """
        return EarthwormV2(self.problem)
    
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
                'alpha': self.alpha,
                'beta': self.beta,
                'gamma': self.gamma
            }
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        EWA no requiere ordenar la población ya que todos los individuos
        se mueven basándose únicamente en el mejor individuo global.
        
        Returns:
            False - EWA no ordena la población
        """
        return False
    
    def summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del algoritmo y sus parámetros.
        
        Returns:
            Diccionario con información del algoritmo
        """
        base_summary = super().summary()
        base_summary.update({
            "algorithm": "EWA v2",
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "uses_cauchy_mutation": True,
            "uses_crossover": True
        })
        return base_summary
