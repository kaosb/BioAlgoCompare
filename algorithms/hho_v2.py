"""
Harris Hawks Optimization (HHO) - Version 2
Implementación usando la nueva arquitectura base_v2.

Referencias:
- Heidari et al. (2019): Harris hawks optimization: Algorithm and applications
"""

import numpy as np
import random
import math
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from utils.math_operators import levy_flight


class HawkV2(Individual):
    """Harris Hawk individual para HHO versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un halcón.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
    
    def initialize(self) -> None:
        """
        Inicializa la posición del halcón aleatoriamente.
        """
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al halcón según el algoritmo HHO.
        
        La estrategia de movimiento depende de la energía de escape E:
        - |E| >= 1: Fase de exploración
        - |E| < 1: Fase de explotación
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Extraer parámetros del contexto
        best_hawk = context.best_individual
        dim = len(self.position)
        
        # Calcular energía de escape
        E0 = 2 * random.random() - 1
        E = 2 * (1 - context.iteration / context.max_iterations) * E0
        
        # Calcular posición promedio de la población
        Xm = np.mean([ind.position for ind in context.population], axis=0)
        
        # Límites del espacio de búsqueda
        LB = np.zeros(dim)
        UB = np.ones(dim)
        
        q = random.random()
        r1, r2, r3, r4 = random.random(), random.random(), random.random(), random.random()
        
        # ------------------------- FASE DE EXPLORACIÓN -------------------------
        if abs(E) >= 1:
            if q >= 0.5:
                # Estrategia basada en ubicación aleatoria
                X_rand = np.random.uniform(LB, UB, dim)
                self.position = X_rand - r1 * np.abs(X_rand - 2 * r2 * self.position)
            else:
                # Estrategia basada en otros halcones
                self.position = (best_hawk.position - Xm) - r3 * (LB + r4 * (UB - LB))
        
        # ------------------------- FASE DE EXPLOTACIÓN -------------------------
        else:
            r = random.random()
            
            if r >= 0.5 and abs(E) >= 0.5:  
                # Asedio suave (soft besiege)
                self.position = best_hawk.position - E * np.abs(
                    best_hawk.position - self.position
                )
                
            elif r >= 0.5 and abs(E) < 0.5:  
                # Asedio duro (hard besiege)
                self.position = best_hawk.position - E * np.abs(
                    best_hawk.position - self.position
                ) / (np.abs(E) + 1e-8)
                
            elif r < 0.5 and abs(E) >= 0.5:  
                # Asedio suave con saltos rápidos
                J = 2 * (1 - random.random())
                Y = best_hawk.position - E * np.abs(J * best_hawk.position - self.position)
                Z = Y + random.random() * levy_flight(dim)
                
                # Evaluar ambas posiciones y elegir la mejor
                Y_fitness = self.problem.evaluate(Y)
                Z_fitness = self.problem.evaluate(Z)
                self.position = Y if Y_fitness < Z_fitness else Z
                
            else:  
                # Asedio duro con saltos rápidos
                Y = best_hawk.position - E * np.abs(best_hawk.position - self.position)
                Z = Y + random.random() * levy_flight(dim)
                
                # Evaluar ambas posiciones y elegir la mejor
                Y_fitness = self.problem.evaluate(Y)
                Z_fitness = self.problem.evaluate(Z)
                self.position = Y if Y_fitness < Z_fitness else Z
        
        # Asegurar que los valores estén dentro del rango
        self.position = np.clip(self.position, LB, UB)


class HHOV2(MetaheuristicAlgorithm[HawkV2]):
    """
    Harris Hawks Optimization (HHO) - Versión 2.
    
    Implementación del algoritmo inspirado en el comportamiento cooperativo
    de caza de los halcones de Harris.
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo HHO v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población de halcones
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo halcón.
        
        Returns:
            Nueva instancia de HawkV2
        """
        return HawkV2(self.problem)
    
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
    
    def update_population(self) -> None:
        """
        Actualiza la población de halcones en cada iteración.
        
        El mejor halcón actúa como la presa (conejo) y los demás
        halcones intentan cazarlo cooperativamente.
        """
        # Crear contexto para esta iteración
        context = MoveContext(
            iteration=len(self.convergence_curve),
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution,
            algorithm_params={}
        )
        
        # Actualizar cada halcón excepto el mejor
        for hawk in self.population:
            if hawk is not self.best_solution:
                hawk.move(context)
                hawk.invalidate_fitness()  # Asegurar que el fitness se recalcule
                
                # Actualizar mejor solución si es necesario
                if hawk.is_better_than(self.best_solution):
                    self.best_solution = hawk.clone()
        
        # Registrar convergencia
        self.convergence_curve.append(self.best_solution.fitness())
    
    def summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del algoritmo y sus parámetros.
        
        Returns:
            Diccionario con información del algoritmo
        """
        base_summary = super().summary()
        base_summary.update({
            "algorithm": "Harris Hawks Optimization v2",
            "levy_beta": 1.5,
            "exploration_exploitation": "Energy-based transition",
            "strategies": [
                "Random location",
                "Other hawks",
                "Soft besiege",
                "Hard besiege",
                "Soft besiege with rapid dives",
                "Hard besiege with rapid dives"
            ]
        })
        return base_summary