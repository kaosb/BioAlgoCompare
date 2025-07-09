"""
MRFO (Manta Ray Foraging Optimization) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo inspirado en el comportamiento de forrajeo de las mantarrayas.
Utiliza tres estrategias principales:
1. Forrajeo en cadena (chain foraging)
2. Forrajeo en ciclón (cyclone foraging)
3. Forrajeo en salto mortal (somersault foraging)

Referencias:
- Zhao et al. (2020): Manta ray foraging optimization: An effective bio-inspired optimizer for engineering applications
  https://doi.org/10.1016/j.engappai.2019.103300
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

# Imports adicionales necesarios
import math


class MantaRayV2(Individual):
    """MantaRay individual para MRFO versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un mantaray.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # MRFO no requiere atributos especiales adicionales
        self.upper_bounds = np.ones(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # MRFO usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # No hay atributos especiales que inicializar

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve la mantarraya según las reglas del algoritmo MRFO.
        
        El movimiento se basa en tres estrategias:
        - Primera mitad: forrajeo en cadena
        - Segunda mitad: forrajeo en ciclón
        - Ocasionalmente: forrajeo en salto mortal
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best_ray = context.best_individual
        t = context.iteration + 1  # Las iteraciones en el original empiezan en 1
        T = context.max_iterations
        alpha = context.algorithm_params.get('alpha', 2.0)
        
        # Límites del problema (siempre [0,1] para VRP)
        lower_bounds = np.zeros(self.dimension)
        upper_bounds = np.ones(self.dimension)
        
        r = random.random()  # Factor aleatorio para seleccionar comportamiento
        # Controla la espiral
        beta = 2 * math.exp(1 - (t / T)) * math.sin(2 * math.pi * r)
        
        if t / T < 0.5:  # Primera mitad: forrajeo en cadena
            for i in range(self.dimension):
                r1 = random.random()
                # Seguir a la mejor mantarraya con factor de espiral
                self.position[i] = (
                    best_ray.position[i]
                    + beta * (best_ray.position[i] - self.position[i])
                    + alpha * r1
                )
        else:  # Segunda mitad: forrajeo en ciclón
            for i in range(self.dimension):
                r2 = random.random()
                if random.random() < 0.5:  # Espiral externa (alejándose)
                    # Comportamiento de ciclón
                    self.position[i] = best_ray.position[i] + alpha * math.exp(
                        beta * r2
                    ) * math.cos(2 * math.pi * r2) * abs(
                        best_ray.position[i] - self.position[i]
                    )
                else:  # Espiral interna (acercándose)
                    # Exploración de profundidad
                    self.position[i] = (
                        best_ray.position[i]
                        + random.random() * (best_ray.position[i] - self.position[i])
                        + beta * r2
                    )
        
        # Asegurar que los valores estén dentro del rango [0, 1]
        self.position = np.clip(self.position, lower_bounds, upper_bounds)
        
        # Fase opcional: somersault foraging (al final de cada iteración o periódicamente)
        if random.random() < context.algorithm_params.get('somersault_prob', 0.3):
            for i in range(self.dimension):
                self.position[i] += random.uniform(-1, 1) * abs(
                    best_ray.position[i] - self.position[i]
                )
            # Volver a aplicar límites después del salto mortal
            self.position = np.clip(self.position, lower_bounds, upper_bounds)
        
        # Invalidar fitness para recalcular
        self.invalidate_fitness()


class MRFOV2(MetaheuristicAlgorithm[MantaRayV2]):
    """
    Manta Ray Foraging Optimization (MRFO) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento de forrajeo de las mantarrayas.
    Combina tres estrategias de búsqueda: forrajeo en cadena (chain), forrajeo en
    ciclón (cyclone) y forrajeo en salto mortal (somersault).
    
    Referencias:
    - Zhao et al. (2020): Manta ray foraging optimization
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        spiral_factor: float = 2.0,
        somersault_prob: float = 0.3,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo MRFO v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            spiral_factor: Factor para el comportamiento en espiral (1.0-3.0)
            somersault_prob: Probabilidad de aplicar forrajeo en salto mortal (0.0-1.0)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer el factor de espiral
        self.spiral_factor = ParameterValidator.validate_positive_float(
            spiral_factor, "spiral_factor", min_value=1.0, max_value=3.0, inclusive_min=True
        )
        
        # Validar y establecer la probabilidad de salto mortal
        self.somersault_prob = ParameterValidator.validate_probability(
            somersault_prob, "somersault_prob"
        )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de MantaRayV2
        """
        return MantaRayV2(self.problem)
    
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
                'alpha': self.spiral_factor,  # Factor de espiral
                'somersault_prob': self.somersault_prob  # Probabilidad de salto mortal
            }
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        MRFO no requiere ordenar la población ya que las mantarrayas
        siguen a la mejor solución independientemente del orden.
        
        Returns:
            False - MRFO no ordena la población
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
            "algorithm": "MRFO v2",
            "spiral_factor": self.spiral_factor,
            "somersault_prob": self.somersault_prob,
            "uses_chain_foraging": True,
            "uses_cyclone_foraging": True,
            "uses_somersault_foraging": True
        })
        return base_summary
