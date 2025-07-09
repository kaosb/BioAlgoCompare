"""
FGO (Flamingo Optimization Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo bio-inspirado basado en el comportamiento de forrajeo y migración de los flamencos.
Combina estrategias de forrajeo local y migración global para equilibrar exploración y explotación.

Referencias:
- Sharma et al. (2021): Flamingo Search Algorithm: A novel bio-inspired optimizer for solving optimization problems
  IEEE Access, 9, 33168-33186. DOI: 10.1109/ACCESS.2021.3060714
"""

import numpy as np
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator


class FlamingoV2(Individual):
    """Flamingo individual para FGO versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un flamenco.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # Atributos especiales del algoritmo
        self.personal_best_position = None
        self._personal_best_fitness = None

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # FGO usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar mejor personal
        self.personal_best_position = np.copy(self.position)
        self._personal_best_fitness = None

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve el flamenco según el modelo oficial FSA.
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        mode = context.algorithm_params.get('mode', 'forage')
        best_position = context.best_individual.position
        
        # Grados de libertad para chi-square
        n = self.dimension
        
        # Nueva posición
        new_position = np.zeros(self.dimension)
        
        for j in range(self.dimension):
            xij = self.position[j]
            xbj = best_position[j]
            
            if mode == "forage":
                # Comportamiento de forrajeo: exploración local
                G1 = np.random.normal(0, 1)
                G2 = np.random.normal(0, 1)
                epsilon1 = np.random.choice([-1, 1])
                epsilon2 = np.random.choice([-1, 1])
                K = np.random.chisquare(n)
                
                # Forrajeo: Eq. (2) del paper
                step = G1 * xbj + epsilon2 * xij
                scan = G2 * abs(step)
                foot = epsilon1 * xbj
                delta = scan + foot + K
                
                new_position[j] = xij + delta
                
            elif mode == "migrate":
                # Comportamiento de migración: movimiento hacia la mejor solución
                omega = np.random.normal(0, n)
                delta = omega * (xbj - xij)
                
                # Migración: Eq. (3) del paper
                new_position[j] = xij + delta
        
        # Aplicar límites
        new_position = np.clip(new_position, 0, 1)
        
        # Evaluar nueva posición
        new_fitness = self.problem.evaluate(new_position)
        current_fitness = self.fitness()
        
        # Reemplazo si mejora
        if new_fitness < current_fitness:
            self.position = new_position
            self.invalidate_fitness()
            
            # Actualizar mejor personal si corresponde
            if self._personal_best_fitness is None or new_fitness < self.personal_best_fitness():
                self.personal_best_position = np.copy(self.position)
                self._personal_best_fitness = new_fitness
    
    def personal_best_fitness(self) -> float:
        """Calcula el fitness de la mejor posición personal."""
        if self._personal_best_fitness is None:
            self._personal_best_fitness = self.problem.evaluate(
                self.personal_best_position
            )
        return self._personal_best_fitness


class FGOV2(MetaheuristicAlgorithm[FlamingoV2]):
    """
    Flamingo Optimization Algorithm (FGO) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento de forrajeo y migración
    de los flamencos. Los flamencos se dividen en tres grupos:
    - MPo: mejores individuos que migran
    - MPr: individuos intermedios que forrajean
    - MPt: peores individuos que migran
    
    Referencias:
    - Sharma et al. (2021): Flamingo Search Algorithm
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        MPb_ratio: float = 0.1,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo FGO v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            MPb_ratio: Proporción de mejores flamencos (0.05-0.2)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer la proporción de mejores flamencos
        self.MPb_ratio = ParameterValidator.validate_probability(
            MPb_ratio, "MPb_ratio"
        )
        
        # Advertencia si el valor está fuera del rango recomendado
        if self.MPb_ratio < 0.05 or self.MPb_ratio > 0.2:
            import warnings
            warnings.warn(
                f"MPb_ratio={self.MPb_ratio} está fuera del rango recomendado [0.05, 0.2]",
                UserWarning
            )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de FlamingoV2
        """
        return FlamingoV2(self.problem)
    
    def update_population(self) -> None:
        """
        Actualiza la población en cada iteración.
        """
        # Calcular tamaños de grupos según el paper
        MPb = int(self.MPb_ratio * self.population_size)
        MPo = MPb  # Mejores individuos
        MPr = int(np.random.random() * self.population_size * (1 - MPb / self.population_size))
        MPt = self.population_size - MPo - MPr  # Resto
        
        # Ordenar población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        # Crear contexto base
        base_context = self._create_move_context()
        
        # Migración inicial: MPo mejores
        for i in range(MPo):
            context = MoveContext(
                iteration=base_context.iteration,
                max_iterations=base_context.max_iterations,
                population=base_context.population,
                best_individual=base_context.best_individual,
                algorithm_params={'mode': 'migrate'}
            )
            self.population[i].move(context)
        
        # Forrajeo: intermedios
        for i in range(MPo, MPo + MPr):
            context = MoveContext(
                iteration=base_context.iteration,
                max_iterations=base_context.max_iterations,
                population=base_context.population,
                best_individual=base_context.best_individual,
                algorithm_params={'mode': 'forage'}
            )
            self.population[i].move(context)
        
        # Migración final: MPt peores
        for i in range(MPo + MPr, MPo + MPr + MPt):
            context = MoveContext(
                iteration=base_context.iteration,
                max_iterations=base_context.max_iterations,
                population=base_context.population,
                best_individual=base_context.best_individual,
                algorithm_params={'mode': 'migrate'}
            )
            self.population[i].move(context)
    
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
        
        FGO requiere ordenar la población para asignar grupos.
        
        Returns:
            True - FGO necesita ordenar la población
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
            "algorithm": "FGO v2",
            "MPb_ratio": self.MPb_ratio,
            "behaviors": ["migrate", "forage"],
            "groups": ["MPo (best)", "MPr (intermediate)", "MPt (worst)"]
        })
        return base_summary