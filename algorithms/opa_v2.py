"""
OPA (Orca Predator Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo bio-inspirado basado en las estrategias de caza de las orcas.
Implementa fases de persecución (chase) y ataque (attack) para balancear
exploración y explotación.

Referencias:
- Jiang et al. (2021): Orca predation algorithm: A novel bio-inspired algorithm for global optimization problems
  Expert Systems with Applications, 188, 116026
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem

import copy


class OrcaV2(Individual):
    """Orca individual para OPA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un orca.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # Atributos especiales: mejor posición personal
        self.personal_best_position = None
        self.personal_best_fitness = float('inf')

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # OPA usa límites [0,1] para representación continua
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar mejor personal
        self.personal_best_position = copy.deepcopy(self.position)
        self.personal_best_fitness = float('inf')

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo OPA.
        
        Implementa estrategias de caza de las orcas:
        - Fase de persecución (chase): exploración mediante movimientos grupales
        - Fase de ataque (attack): explotación cerca de la presa
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        iteration = context.iteration
        max_iterations = context.max_iterations
        population = context.population
        best = context.best_individual
        phase = context.algorithm_params.get('phase', 'chase')
        accept_prob = context.algorithm_params.get('accept_prob', 0.3)
        
        # Crear nueva posición
        new_position = copy.deepcopy(self.position)
        
        if phase == "chase":  # Fase de exploración
            # Movimiento de búsqueda grupal
            # Seleccionar dos individuos aleatorios de la población
            if len(population) > 2:
                idx1, idx2 = random.sample(range(len(population)), 2)
                ind1 = population[idx1]
                ind2 = population[idx2]
                
                # Movimiento basado en diferencias con perturbación
                r1 = random.random()
                r2 = random.random()
                r3 = random.random()
                
                # Estrategia de persecución con influencia grupal
                new_position = (
                    self.position 
                    + r1 * (best.position - self.position)
                    + r2 * (ind1.position - ind2.position)
                    + r3 * (np.random.uniform(-1, 1, self.dimension))
                )
            else:
                # Si la población es muy pequeña, solo moverse hacia el mejor
                r1 = random.random()
                new_position = (
                    self.position 
                    + r1 * (best.position - self.position)
                    + 0.1 * np.random.uniform(-1, 1, self.dimension)
                )
                
        else:  # Fase de ataque (explotación)
            # Movimiento dirigido hacia la presa (mejor solución)
            # Simular el ataque coordinado de las orcas
            alpha = 2 * (1 - iteration / max_iterations)  # Factor de contracción
            beta = random.random()
            
            # Estrategia de ataque con movimiento espiral
            if random.random() < 0.5:
                # Ataque directo
                new_position = (
                    best.position 
                    + alpha * beta * (best.position - self.position)
                )
            else:
                # Ataque espiral (inspirado en ballenas)
                b = 1  # Constante de forma logarítmica
                l = random.uniform(-1, 1)
                distance = np.abs(best.position - self.position)
                new_position = (
                    distance * np.exp(b * l) * np.cos(2 * np.pi * l) 
                    + best.position
                )
        
        # Asegurar límites [0, 1]
        new_position = np.clip(new_position, 0, 1)
        
        # Evaluar nueva posición
        new_fitness = self.problem.evaluate(new_position)
        current_fitness = self.fitness() if self._fitness is not None else self.problem.evaluate(self.position)
        
        # Actualizar si mejora o según probabilidad de aceptación
        if new_fitness < current_fitness or random.random() < accept_prob:
            self.position = new_position
            self.invalidate_fitness()
            
            # Actualizar mejor personal si corresponde
            if new_fitness < self.personal_best_fitness:
                self.personal_best_position = copy.deepcopy(new_position)
                self.personal_best_fitness = new_fitness


class OPAV2(MetaheuristicAlgorithm[OrcaV2]):
    
    def update_population(self) -> None:
        """
        Actualiza la población aplicando las estrategias de caza de las orcas.
        """
        # Determinar fase actual y probabilidad de aceptación
        iteration = len(self.convergence_curve)
        frac = iteration / self.max_iterations
        phase = "chase" if frac < 0.5 else "attack"
        accept_prob = 0.3 * (1 - frac)
        
        # Crear contexto base
        base_context = self._create_move_context()
        
        # Actualizar cada orca
        for orca in self.population:
            # Crear contexto con fase y probabilidad
            context = MoveContext(
                iteration=base_context.iteration,
                max_iterations=base_context.max_iterations,
                population=base_context.population,
                best_individual=base_context.best_individual,
                algorithm_params={
                    'phase': phase,
                    'accept_prob': accept_prob
                }
            )
            
            # Mover la orca
            orca.move(context)
    """
    Orca Predator Algorithm (OPA) - Versión 2.
    
    Algoritmo bio-inspirado basado en las estrategias de caza cooperativa
    de las orcas. Alterna entre fases de persecución (exploración) y
    ataque (explotación) para optimizar eficientemente.
    
    Referencias:
    - Jiang et al. (2021): Orca predation algorithm
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo OPA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # No hay parámetros específicos adicionales en OPA
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de OrcaV2
        """
        return OrcaV2(self.problem)
    
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
        Determina si la población debe ordenarse después de actualizar.
        
        OPA no requiere ordenar la población ya que todos los individuos
        interactúan basados en selección aleatoria.
        
        Returns:
            False - OPA no ordena la población
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
            "algorithm": "OPA v2",
            "phases": ["chase", "attack"],
            "uses_personal_best": True
        })
        return base_summary
