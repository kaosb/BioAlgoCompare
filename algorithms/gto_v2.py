"""
GTO (Gorilla Troops Optimizer) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo inspirado en el comportamiento de las tropas de gorilas.
Utiliza estrategias de exploración (migración) y explotación
(seguir al silverback y competencia) con transición adaptativa.

Referencias:
- Abdollahzadeh et al. (2021): Artificial gorilla troops optimizer: A new nature-inspired metaheuristic algorithm for global optimization problems
  https://doi.org/10.1002/int.22535
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

# Imports adicionales necesarios
import math


class GorillaV2(Individual):
    """Gorilla individual para GTO versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un gorilla.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # GTO no requiere atributos especiales adicionales
        self.upper_bounds = np.ones(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # GTO usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # No hay atributos especiales que inicializar

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo GTO.
        
        El movimiento incluye:
        - Exploración: migración a lugares conocidos o desconocidos
        - Explotación: seguir al silverback o competencia por hembras
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best_gorilla = context.best_individual
        population = context.population
        iteration = context.iteration
        max_iterations = context.max_iterations
        
        # Obtener parámetros del algoritmo
        C = context.algorithm_params.get('C', 1.0)
        L = context.algorithm_params.get('L', 0.0)
        W = context.algorithm_params.get('W', 0.8)
        beta = context.algorithm_params.get('beta', 3)
        p = context.algorithm_params.get('p', 0.03)
        
        dim = self.dimension
        
        # Límites del problema (siempre [0,1] para VRP)
        lower_bounds = np.zeros(dim)
        upper_bounds = np.ones(dim)
        
        # --- Operadores de exploración (Ecuación 1) ---
        if random.random() < p:
            # Exploración: migración a lugar desconocido
            r1 = np.random.rand(dim)
            self.position = lower_bounds + (upper_bounds - lower_bounds) * r1
        elif random.random() >= 0.5:
            # Exploración: moverse hacia otro gorila
            Xr = random.choice(population).position
            self.position = self.position + C * (Xr - self.position)
        else:
            # Exploración: migración hacia un lugar conocido
            H = (np.random.uniform(-C, C, dim)) * self.position
            self.position = (upper_bounds - lower_bounds) * np.random.rand(dim) + lower_bounds
            self.position = self.position + L * H
        
        # --- Transición a explotación si corresponde ---
        if C < W:
            if random.random() < 0.5:
                # Seguir al silverback (Eq. 7)
                M = np.mean([g.position for g in population], axis=0)
                self.position = L * (M - self.position) + best_gorilla.position
            else:
                # Competencia por hembras (Eq. 10)
                Q = 2 * random.random() - 1
                E = np.random.rand(dim) if random.random() >= 0.5 else np.random.randn(dim)
                A = beta * E
                self.position = (
                    best_gorilla.position
                    - Q * (best_gorilla.position - self.position) * A
                )
        
        # Asegurar que los valores estén dentro del rango [0, 1]
        self.position = np.clip(self.position, lower_bounds, upper_bounds)
        
        # Invalidar fitness para recalcular
        self.invalidate_fitness()


class GTOV2(MetaheuristicAlgorithm[GorillaV2]):
    """
    Gorilla Troops Optimizer (GTO) - Versión 2.
    
    Algoritmo inspirado en el comportamiento social de las tropas de gorilas.
    Combina estrategias de exploración (migración) y explotación (seguir
    al silverback y competencia) con transiciones adaptativas basadas en
    parámetros que varían durante la optimización.
    
    Referencias:
    - Abdollahzadeh et al. (2021): Artificial gorilla troops optimizer
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None,
        p: float = 0.03,
        beta: float = 3.0
    ):
        """
        Inicializa el algoritmo GTO v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
            p: Probabilidad de migración (0.0-1.0)
            beta: Parámetro para competencia (>0)
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer parámetros específicos
        self.p = ParameterValidator.validate_probability(p, "p")
        self.beta = ParameterValidator.validate_positive_float(
            beta, "beta", min_value=0.0
        )
        
        # Parámetros fijos del algoritmo
        self.exploitation_factor = 0.5  # Factor para balancear exploración y explotación
        self.social_factor = 0.2  # Factor para aprendizaje social
        self.W = 0.8  # Umbral de transición
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de GorillaV2
        """
        return GorillaV2(self.problem)
    
    def _get_dynamic_params(self) -> Dict[str, Any]:
        """
        Calcula los parámetros dinámicos del algoritmo.
        
        Returns:
            Diccionario con parámetros C, L, W, beta, p
        """
        t = len(self.convergence_curve)
        
        # Calcular C y L según las ecuaciones del paper
        F = math.cos(2 * math.pi * random.random()) + 1
        C = F * (1 - t / self.max_iterations)
        l = random.uniform(-1, 1)
        L = C * l
        
        # Ajustar el factor de explotación basado en la iteración actual
        self.exploitation_factor = 0.5 - 0.3 * (t / self.max_iterations)
        
        return {
            'C': C,
            'L': L,
            'W': self.W,
            'beta': self.beta,
            'p': self.p
        }
    
    def _after_iteration(self) -> None:
        """
        Operaciones después de cada iteración.
        """
        super()._after_iteration()
        
        # Comportamiento social: interacción entre gorilas
        for i in range(self.population_size):
            if self.population[i] is not self.best_solution:
                if random.random() < self.social_factor:
                    # Seleccionar otro gorila aleatoriamente
                    other_idx = random.randint(0, self.population_size - 1)
                    while other_idx == i:
                        other_idx = random.randint(0, self.population_size - 1)
                    
                    # Aprendizaje social
                    for j in range(self.population[i].dimension):
                        if random.random() < 0.3:  # Probabilidad de aprendizaje
                            self.population[i].position[j] = self.population[i].position[j] + random.random() * (
                                self.population[other_idx].position[j] - self.population[i].position[j]
                            )
                    
                    # Asegurar valores en rango [0, 1]
                    self.population[i].position = np.clip(self.population[i].position, 0, 1)
                    self.population[i].invalidate_fitness()
    
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
            algorithm_params=self._get_dynamic_params()  # Parámetros dinámicos
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        GTO no requiere ordenar la población ya que cada gorila
        se mueve independientemente siguiendo estrategias específicas.
        
        Returns:
            False - GTO no ordena la población
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
            "algorithm": "GTO v2",
            "exploitation_factor": self.exploitation_factor,
            "social_factor": self.social_factor,
            "beta": self.beta,
            "p": self.p,
            "W": self.W
        })
        return base_summary
