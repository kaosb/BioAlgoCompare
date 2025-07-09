"""
FSA (Flamingo Search Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo bio-inspirado basado en el comportamiento de los flamencos.
Utiliza dos estrategias principales: forrajeo (búsqueda local) y
migración (exploración global) con particionamiento dinámico de la población.

Referencias:
- Zheng et al. (2021): Flamingo Search Algorithm: A new swarm intelligence optimization algorithm
  IEEE Access, vol. 9, pp. 88564-88582
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

# Imports adicionales no necesarios (ya están arriba)


class FlamingoV2(Individual):
    """Flamingo individual para FSA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un flamingo.
        
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
        # FSA usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar mejor personal
        self.personal_best_position = self.position.copy()
        self.personal_best_fitness = float('inf')

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve el flamenco según las estrategias de FSA.
        
        Implementa dos modos de movimiento:
        - Forrajeo: búsqueda local con componentes aleatorios
        - Migración: movimiento dirigido hacia el mejor individuo
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best = context.best_individual
        iteration = context.iteration
        max_iterations = context.max_iterations
        mode = context.algorithm_params.get('mode', 'forage')
        
        n = self.dimension  # grados de libertad
        x_new = self.position.copy()
        
        for j in range(self.dimension):
            xij = self.position[j]
            xbj = best.position[j]
            
            if mode == "forage":
                # Componentes del forrajeo
                G1 = np.random.normal(0, 1)
                G2 = np.random.normal(0, 1)
                ε1 = random.choice([-1, 1])
                ε2 = random.choice([-1, 1])
                K = np.random.chisquare(n)
                
                # Ecuación de forrajeo
                step = G1 * xbj + ε2 * xij
                scan = G2 * abs(step)
                foot = ε1 * xbj
                delta = scan + foot + K
                
                x_new[j] = xij + delta
                
            elif mode == "migrate":
                # Componente de migración
                ω = np.random.normal(0, n)
                delta = ω * (xbj - xij)
                
                # Ecuación de migración
                x_new[j] = xij + delta
            
            # Asegurar límites [0, 1]
            x_new[j] = np.clip(x_new[j], 0, 1)
        
        # Evaluación y reemplazo si mejora
        new_fitness = self.problem.evaluate(x_new)
        current_fitness = self.fitness() if self._fitness is not None else self.problem.evaluate(self.position)
        
        if new_fitness < current_fitness:
            self.position = x_new
            self.invalidate_fitness()
            
            # Actualizar mejor personal si mejora
            if new_fitness < self.personal_best_fitness:
                self.personal_best_position = x_new.copy()
                self.personal_best_fitness = new_fitness


class FSAV2(MetaheuristicAlgorithm[FlamingoV2]):
    """
    Flamingo Search Algorithm (FSA) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento de búsqueda de alimento
    de los flamencos. Divide la población en tres grupos con diferentes estrategias:
    migración inicial, forrajeo y migración final.
    
    Referencias:
    - Zheng et al. (2021): Flamingo Search Algorithm
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
        Inicializa el algoritmo FSA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            MPb_ratio: Proporción de mejores flamencos (0.05-0.2)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer parámetros específicos del algoritmo
        self.MPb_ratio = ParameterValidator.validate_positive_float(
            MPb_ratio, "MPb_ratio", min_value=0.05, max_value=0.2, inclusive_min=True
        )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de FlamingoV2
        """
        return FlamingoV2(self.problem)
    
    def _before_iteration(self) -> None:
        """
        Operaciones antes de cada iteración.
        """
        super()._before_iteration()
        # Calcular particiones de la población
        self.MPb = int(self.MPb_ratio * self.population_size)
        self.MPo = self.MPb
        self.MPr = int(
            random.random() * self.population_size * (1 - self.MPb / self.population_size)
        )
        self.MPt = self.population_size - self.MPo - self.MPr
    
    def _get_mode_for_individual(self, index: int) -> str:
        """
        Determina el modo de movimiento para un individuo según su índice.
        
        Args:
            index: Índice del individuo en la población ordenada
            
        Returns:
            'migrate' o 'forage' según la partición
        """
        if hasattr(self, 'MPo') and hasattr(self, 'MPr'):
            if index < self.MPo:
                return 'migrate'  # Migración inicial
            elif index < self.MPo + self.MPr:
                return 'forage'   # Forrajeo
            else:
                return 'migrate'  # Migración final
        else:
            # Por defecto, usar forrajeo
            return 'forage'
    
    def update_population(self) -> None:
        """
        Actualiza la población aplicando diferentes modos según la partición.
        """
        # Crear contexto base
        base_context = self._create_move_context()
        
        # Mover cada individuo según su partición
        for i, individual in enumerate(self.population):
            # Determinar modo según partición
            mode = self._get_mode_for_individual(i)
            
            # Crear contexto con modo específico
            context = MoveContext(
                iteration=base_context.iteration,
                max_iterations=base_context.max_iterations,
                population=base_context.population,
                best_individual=base_context.best_individual,
                algorithm_params={'mode': mode}
            )
            
            # Mover individuo
            individual.move(context)
    
    def _create_move_context(self) -> MoveContext:
        """
        Crea el contexto de movimiento para la iteración actual.
        
        Returns:
            MoveContext con información del estado actual
        """
        # Nota: el modo se determina por individuo en update_population
        return MoveContext(
            iteration=len(self.convergence_curve),
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution,
            algorithm_params={}  # El modo se agrega dinámicamente
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        FSA ordena la población por fitness para determinar las particiones
        de migración y forrajeo según el rendimiento.
        
        Returns:
            True - FSA sí ordena la población
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
            "algorithm": "FSA v2",
            "MPb_ratio": self.MPb_ratio,
            "uses_foraging": True,
            "uses_migration": True
        })
        return base_summary
