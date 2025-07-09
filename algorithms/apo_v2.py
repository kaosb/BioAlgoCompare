"""
APO (Artificial Protozoa Optimizer) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo bio-inspirado basado en el comportamiento de los protozoos.
Imita estrategias de forrajeo (autotrofía/heterotrofía), reproducción y dormancia.

Referencias:
- Wang et al. (2024): Artificial protozoa optimizer (APO): A novel bio-inspired metaheuristic algorithm for engineering optimization
  Knowledge-Based Systems, Volume 295, 111737
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

import math


class ProtozoaV2(Individual):
    """Protozoa individual para APO versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un protozoa.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # Límites del problema (siempre [0,1] para VRP)
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # APO usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo APO.
        
        Implementa las estrategias de:
        - Autotrofía: absorción de nutrientes del ambiente
        - Heterotrofía: alimentación de otros organismos
        - Reproducción: división y generación de nuevos individuos
        - Dormancia: estado de reposo en condiciones adversas
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        iteration = context.iteration
        max_iterations = context.max_iterations
        population = context.population
        pf_max = context.algorithm_params.get('pf_max', 0.1)
        npairs = context.algorithm_params.get('npairs', 1)
        
        # Encontrar índice del individuo actual en la población
        i = 0
        for idx, ind in enumerate(population):
            if ind is self:
                i = idx
                break
        
        dim = self.dimension
        ps = len(population)
        
        # Probabilidades dinámicas
        pf = pf_max * random.random()
        pah = 0.5 * (1 + math.cos((iteration / max_iterations) * math.pi))
        pdr = 0.5 * (1 + math.cos(((ps - i) / ps) * math.pi))
        
        # Dormancia o reproducción
        if random.random() < pf:
            if random.random() < pdr:
                # Dormancia - Eq. 11
                self.position = self.lower_bounds + np.random.rand(dim) * (
                    self.upper_bounds - self.lower_bounds
                )
            else:
                # Reproducción - Eq. 13
                Mr = np.zeros(dim)
                idxs = np.random.permutation(dim)[: math.ceil(dim * random.random())]
                Mr[idxs] = 1
                delta = np.random.rand(dim) * (
                    self.lower_bounds
                    + np.random.rand(dim) * (self.upper_bounds - self.lower_bounds)
                )
                self.position = self.position + random.choice([-1, 1]) * delta * Mr
        else:
            Mf = np.zeros(dim)
            idxs = np.random.permutation(dim)[: math.ceil(dim * i / ps)]
            Mf[idxs] = 1
            if random.random() < pah:
                # Autotrofia - Eq. 1
                j = random.randint(0, ps - 1)
                neighbor_plus = population[min(i + 1, ps - 1)].position
                neighbor_minus = population[max(i - 1, 0)].position
                wa = math.exp(
                    -abs(population[max(i - 1, 0)].fitness())
                    / (population[min(i + 1, ps - 1)].fitness() + 1e-16)
                )
                delta = (
                    population[j].position
                    - self.position
                    + (wa * (neighbor_minus - neighbor_plus))
                ) / npairs
                f = random.random() * (
                    1 + math.cos((iteration / max_iterations) * math.pi)
                )
                self.position = self.position + f * delta * Mf
            else:
                # Heterotrofia - Eq. 7
                neighbor_minus = population[max(i - 1, 0)].position
                neighbor_plus = population[min(i + 1, ps - 1)].position
                wh = math.exp(
                    -abs(population[max(i - 1, 0)].fitness())
                    / (population[min(i + 1, ps - 1)].fitness() + 1e-16)
                )
                Xnear = (
                    1
                    + random.choice([-1, 1])
                    * random.random()
                    * (1 - iteration / max_iterations)
                ) * self.position
                delta = (
                    Xnear - self.position + (wh * (neighbor_minus - neighbor_plus))
                ) / npairs
                f = random.random() * (
                    1 + math.cos((iteration / max_iterations) * math.pi)
                )
                self.position = self.position + f * delta * Mf
        
        # Clip y invalidar fitness
        self.position = np.clip(self.position, self.lower_bounds, self.upper_bounds)
        self.invalidate_fitness()


class APOV2(MetaheuristicAlgorithm[ProtozoaV2]):
    """
    Artificial Protozoa Optimizer (APO) - Versión 2.
    
    Algoritmo metaheurístico bio-inspirado que simula el comportamiento de los protozoos,
    incluyendo estrategias de forrajeo (autotrofía y heterotrofía), reproducción y dormancia.
    
    Referencias:
    - Wang et al. (2024): Artificial protozoa optimizer (APO)
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        pf_max: float = 0.1,
        npairs: int = 1,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo APO v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            pf_max: Probabilidad máxima de forrajeo (0.05-0.3)
            npairs: Número de pares para interacciones (>=1)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer parámetros específicos del algoritmo
        self.pf_max = ParameterValidator.validate_positive_float(
            pf_max, "pf_max", min_value=0.05, max_value=0.3, inclusive_min=True
        )
        
        self.npairs = ParameterValidator.validate_positive_integer(
            npairs, "npairs", min_value=1
        )
        
        # Advertencia si npairs es muy alto
        if self.npairs > 3:
            import warnings
            warnings.warn(
                f"npairs={self.npairs} es alto. Se recomienda usar 1-3 pares.",
                UserWarning
            )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de ProtozoaV2
        """
        return ProtozoaV2(self.problem)
    
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
                'pf_max': self.pf_max,
                'npairs': self.npairs
            }
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        APO ordena la población por fitness para determinar las interacciones
        entre vecinos y calcular probabilidades basadas en el ranking.
        
        Returns:
            True - APO sí ordena la población
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
            "algorithm": "APO v2",
            "pf_max": self.pf_max,
            "npairs": self.npairs,
            "strategies": ["autotrophy", "heterotrophy", "reproduction", "dormancy"]
        })
        return base_summary
