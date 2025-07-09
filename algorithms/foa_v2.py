"""
Fossa Optimization Algorithm (FOA) - Version 2
Implementación usando la nueva arquitectura base_v2.

Referencias:
- Khodadadi et al. (2022): Fossa Optimization Algorithm
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem


class FossaV2(Individual):
    """Fossa individual para FOA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un fossa.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        # Para problemas VRP, los límites son [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
    
    def initialize(self) -> None:
        """
        Inicializa la posición del fossa aleatoriamente.
        """
        self.position = np.random.uniform(
            self.lower_bounds, 
            self.upper_bounds, 
            self.dimension
        )
        self.invalidate_fitness()
    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al fossa según el algoritmo FOA.
        
        El algoritmo tiene dos fases:
        - Primera mitad de iteraciones: Exploración (basada en lemures)
        - Segunda mitad: Explotación (movimiento reducido)
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        dim = self.dimension
        t = context.iteration + 1  # t empieza en 1
        
        # Obtener candidatos mejores (lemures) - individuos con mejor fitness
        lemurs = [ind for ind in context.population 
                  if ind.fitness() < self.fitness() and ind is not self]
        
        if not lemurs:
            return  # No hay movimiento si no hay mejores individuos
        
        # Seleccionar un lemur aleatorio
        lemur = random.choice(lemurs)
        x_new = self.position.copy()
        
        for j in range(dim):
            if t <= context.max_iterations // 2:
                # Fase de exploración (Eq. 5 del paper)
                I = random.choice([1, 2])
                r_ij = random.random()
                xj_p1 = self.position[j] + r_ij * (
                    lemur.position[j] - I * self.position[j]
                )
                x_new[j] = np.clip(xj_p1, self.lower_bounds[j], self.upper_bounds[j])
            else:
                # Fase de explotación (Eq. 7 del paper)
                r_ij = random.random()
                range_j = self.upper_bounds[j] - self.lower_bounds[j]
                xj_p2 = self.position[j] + (1 - 2 * r_ij) * (range_j / t)
                x_new[j] = np.clip(xj_p2, self.lower_bounds[j], self.upper_bounds[j])
        
        # Evaluar nueva posición y actualizar si mejora
        new_fitness = self.problem.evaluate(x_new)
        if new_fitness <= self.fitness():
            self.position = x_new
            self.invalidate_fitness()


class FOAV2(MetaheuristicAlgorithm[FossaV2]):
    """
    Fossa Optimization Algorithm (FOA) - Versión 2.
    
    Algoritmo inspirado en el comportamiento de caza cooperativa de los fosas.
    Los fosas aprenden de individuos más exitosos (lemures) y ajustan su
    comportamiento entre exploración y explotación según la fase del algoritmo.
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo FOA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población de fosas
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo fossa.
        
        Returns:
            Nueva instancia de FossaV2
        """
        return FossaV2(self.problem)
    
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
            algorithm_params={}
        )
    
    def _should_sort_population(self) -> bool:
        """
        FOA requiere población ordenada para identificar lemures.
        
        Returns:
            True para mantener población ordenada
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
            "algorithm": "Fossa Optimization Algorithm v2",
            "phases": ["Exploration (first half)", "Exploitation (second half)"],
            "inspiration": "Cooperative hunting behavior of fossas",
            "key_mechanism": "Learning from better individuals (lemurs)"
        })
        return base_summary