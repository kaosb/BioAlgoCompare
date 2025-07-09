"""
WOA (Whale Optimization Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

El algoritmo de optimización de ballenas está inspirado en el comportamiento
de caza de las ballenas jorobadas. Utiliza dos estrategias principales:
1. Búsqueda por encogimiento (shrinking encircling)
2. Ataque en espiral (spiral bubble-net)

Referencias:
- Mirjalili & Lewis (2016): The Whale Optimization Algorithm
  https://doi.org/10.1016/j.advengse.2016.01.008
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem

# Imports adicionales necesarios
import math


class WhaleV2(Individual):
    """Whale individual para WOA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un whale.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # No hay atributos especiales para WOA

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # No hay atributos especiales que inicializar para WOA

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve la ballena según las reglas del algoritmo WOA.
        
        El algoritmo tiene dos estrategias principales:
        - Encogimiento (shrinking): exploración/explotación basada en |A|
        - Espiral (spiral): movimiento en espiral alrededor de la presa
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best_whale = context.best_individual
        iteration = context.iteration
        max_iterations = context.max_iterations
        
        # Calcular parámetros de control
        # a disminuye linealmente de 2 a 0
        a = 2 - 2 * (iteration / max_iterations)
        a2 = -1  # Parámetro para la espiral (valor típico)
        
        r1 = random.random()  # Número aleatorio en [0, 1]
        r2 = random.random()  # Número aleatorio en [0, 1]
        
        A = 2 * a * r1 - a  # Coeficiente de encogimiento
        C = 2 * r2  # Coeficiente de peso
        
        # Seleccionar estrategia de movimiento
        p = random.random()  # Probabilidad para seleccionar estrategia
        
        if p < 0.5:  # Estrategia de encogimiento
            if abs(A) < 1:  # Explotación: acercarse a la mejor solución
                for i in range(self.dimension):
                    D = abs(C * best_whale.position[i] - self.position[i])
                    self.position[i] = best_whale.position[i] - A * D
            else:  # Exploración: moverse aleatoriamente
                # Seleccionar una ballena aleatoria
                X_rand = np.random.uniform(0, 1, self.dimension)
                for i in range(self.dimension):
                    D = abs(C * X_rand[i] - self.position[i])
                    self.position[i] = X_rand[i] - A * D
        else:  # Estrategia de espiral
            for i in range(self.dimension):
                D = abs(best_whale.position[i] - self.position[i])
                l = random.uniform(-1, 1)  # Parámetro de forma de espiral
                self.position[i] = (
                    D * np.exp(a2 * l) * np.cos(2 * np.pi * l)
                    + best_whale.position[i]
                )
        
        # Asegurar que los valores estén dentro del rango [0, 1]
        self.position = np.clip(self.position, 0, 1)
        
        # Invalidar fitness para recalcular
        self.invalidate_fitness()


class WOAV2(MetaheuristicAlgorithm[WhaleV2]):
    """
    Whale Optimization Algorithm (WOA) - Versión 2.
    
    Algoritmo inspirado en el comportamiento de caza de las ballenas jorobadas.
    Las ballenas usan dos estrategias principales:
    1. Búsqueda por encogimiento (shrinking encircling)
    2. Ataque en espiral (spiral bubble-net)
    
    Referencias:
    - Mirjalili & Lewis (2016): The Whale Optimization Algorithm
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo WOA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # WOA usa parámetros estándar, no requiere adicionales
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de WhaleV2
        """
        return WhaleV2(self.problem)
    
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
            algorithm_params={}  # WOA no requiere parámetros adicionales
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        WOA no requiere ordenar la población ya que cada ballena
        se mueve independientemente basándose en la mejor solución.
        
        Returns:
            False - WOA no ordena la población
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
            "algorithm": "WOA v2",
            "spiral_parameter": -1,  # Parámetro a2 para la espiral
        })
        return base_summary
