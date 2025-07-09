"""
SMA (Slime Mould Algorithm) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo inspirado en el comportamiento del moho del limo (Physarum polycephalum)
que muestra una capacidad notable para encontrar caminos óptimos en redes.
Utiliza un mecanismo de pesos adaptativos basado en el fitness.

Referencias:
- Li et al. (2020): Slime mould algorithm: A new method for stochastic optimization
  https://doi.org/10.1016/j.future.2020.03.055
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator

# Imports adicionales necesarios
import math


class SlimeMouldV2(Individual):
    """SlimeMould individual para SMA versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un slimemould.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # Atributo especial del algoritmo: peso para el movimiento
        self.weight = 0.0

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # SMA usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar peso
        self.weight = 0.0

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo SMA.
        
        El movimiento del moho del limo se basa en dos estrategias:
        1. Exploración aleatoria con probabilidad z
        2. Movimiento adaptativo basado en pesos y condiciones de fitness
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        best_mould = context.best_individual
        population = context.population
        t = context.iteration + 1  # Las iteraciones en el original empiezan en 1
        max_t = context.max_iterations
        z = context.algorithm_params.get('z', 0.03)
        
        # Calcular parámetros necesarios
        dim = self.dimension
        epsilon = 1e-8
        bF = best_mould.fitness()
        fitness_values = [ind.fitness() for ind in population]
        wF = max(fitness_values)
        DF = bF
        S_i = self.fitness()
        
        # Calcular probabilidad de movimiento
        p = math.tanh(abs((S_i - DF) / (bF - wF + epsilon)))
        
        r = random.random()
        a = math.atanh(-t / max_t + 1)
        vb = np.random.uniform(-a, a, size=dim)
        vc = np.random.uniform(-1, 1, size=dim) * (1 - t / max_t)
        
        # Decidir estrategia de movimiento
        if random.random() < z:
            # Exploración aleatoria
            self.position = np.random.uniform(0, 1, size=dim)
        else:
            if r < p:
                # Movimiento basado en otros individuos
                A, B = random.sample(population, 2)
                X_A = A.position
                X_B = B.position
                self.position = best_mould.position + vb * self.weight * (X_A - X_B)
            else:
                # Movimiento basado en la posición actual
                self.position = vc * self.position
        
        # Asegurar que los valores estén dentro del rango [0, 1]
        self.position = np.clip(self.position, 0, 1)
        
        # Invalidar fitness para recalcular
        self.invalidate_fitness()


class SMAV2(MetaheuristicAlgorithm[SlimeMouldV2]):
    """
    Slime Mould Algorithm (SMA) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento del moho del limo
    (Physarum polycephalum). Utiliza un mecanismo de pesos adaptativos
    y estrategias de búsqueda basadas en la aptitud relativa de los individuos.
    
    Referencias:
    - Li et al. (2020): Slime mould algorithm: A new method for stochastic optimization
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None,
        z: float = 0.03
    ):
        """
        Inicializa el algoritmo SMA v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
            z: Parámetro de probabilidad para comportamiento aleatorio (0.0-1.0)
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar y establecer parámetro z
        self.z = ParameterValidator.validate_positive_float(
            z, "z", min_value=0.0, max_value=1.0, inclusive_min=True
        )
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de SlimeMouldV2
        """
        return SlimeMouldV2(self.problem)
    
    def _initialize_algorithm(self) -> None:
        """
        Inicialización específica del algoritmo después de crear la población.
        """
        super()._initialize_algorithm()
        # Actualizar pesos iniciales
        self._update_weights()
    
    def _before_iteration(self) -> None:
        """
        Operaciones antes de cada iteración.
        """
        super()._before_iteration()
        # Actualizar pesos de los mohos según su aptitud actual
        self._update_weights()
    
    def _update_weights(self) -> None:
        """
        Actualiza los pesos de los mohos según su aptitud.
        """
        # Obtener todos los valores de fitness
        fitness_values = [m.fitness() for m in self.population]
        epsilon = 1e-8
        bF = min(fitness_values)
        wF = max(fitness_values)
        med = np.median(fitness_values)
        
        for i, mould in enumerate(self.population):
            S_i = fitness_values[i]
            rand_coeff = random.random()
            if S_i <= med:
                mould.weight = 1 + rand_coeff * math.log(
                    (bF - S_i) / (bF - wF + epsilon) + 1
                )
            else:
                mould.weight = 1 - rand_coeff * math.log(
                    (bF - S_i) / (bF - wF + epsilon) + 1
                )
    
    def _get_current_z(self) -> float:
        """
        Calcula el valor actual de z que disminuye con las iteraciones.
        
        Returns:
            Valor actual de z
        """
        current_iter = len(self.convergence_curve)
        return self.z - current_iter * (0.03 / self.max_iterations)
    
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
            algorithm_params={'z': self._get_current_z()}  # Parámetro z adaptativo
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        SMA no requiere ordenar la población ya que usa pesos adaptativos
        basados en el fitness relativo.
        
        Returns:
            False - SMA no ordena la población
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
            "algorithm": "SMA v2",
            "z_parameter": self.z,
            "uses_adaptive_weights": True
        })
        return base_summary
