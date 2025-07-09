"""Slime Mould Algorithm (SMA).

This module implements the Slime Mould Algorithm, inspired by the
oscillation behavior and morphological changes of slime mould in nature.

The algorithm simulates:
1. Approach food: Slime mould approaches food sources using bio-oscillator
2. Wrap food: Slime mould wraps around food with venous structure
3. Oscillation frequency changes based on food quality
4. Adaptive weights for exploring different regions

Reference:
    Li, S., Chen, H., Wang, M., Heidari, A. A., & Mirjalili, S. (2020).
    Slime mould algorithm: A new method for stochastic optimization.
    Future Generation Computer Systems, 111, 300-323.
    DOI: 10.1016/j.future.2020.03.055

Example:
    >>> from algorithms.sma import SMA
    >>> from problems.vrp import VRPProblem
    >>> 
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>> 
    >>> # Initialize and run SMA
    >>> algo = SMA(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class SlimeMould(Individual):
    """Clase para representar un individuo en el algoritmo SMA (Slime Mould Algorithm)."""

    def __init__(self, problem):
        """
        Inicializa un moho del limo con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        self.weight = 0.0  # Peso para el movimiento

    def fitness(self):
        """Calcula el fitness del individuo."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return (
            True  # En VRP todas las soluciones son factibles con nuestro decodificador
        )

    def move(self, best_mould, population, z=0.03, t=1, max_t=100):
        """
        Movimiento del moho del limo basado en el algoritmo SMA original.

        Args:
            best_mould: El mejor individuo encontrado hasta ahora.
            population: Lista de todos los individuos en la población.
            z: Probabilidad de exploración aleatoria.
            t: Iteración actual.
            max_t: Número total de iteraciones.
        """
        dim = self.dimension
        epsilon = 1e-8
        bF = best_mould.fitness()
        fitness_values = [ind.fitness() for ind in population]
        wF = max(fitness_values)
        DF = bF
        S_i = self.fitness()
        p = math.tanh(abs((S_i - DF) / (bF - wF + epsilon)))

        r = random.random()
        a = math.atanh(-t / max_t + 1)
        vb = np.random.uniform(-a, a, size=dim)
        vc = np.random.uniform(-1, 1, size=dim) * (1 - t / max_t)

        if random.random() < z:
            self.position = np.random.uniform(0, 1, size=dim)
        else:
            if r < p:
                A, B = random.sample(population, 2)
                X_A = A.position
                X_B = B.position
                self.position = best_mould.position + vb * self.weight * (X_A - X_B)
            else:
                self.position = vc * self.position

        # Clip en dominio [0,1]
        self.position = np.clip(self.position, 0, 1)
        self._fitness = None

    def copy(self, other):
        """
        Copia los valores de otro individuo a este.

        Args:
            other: Otro individuo (SlimeMould)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness
        if hasattr(other, "weight"):
            self.weight = other.weight


class SMA(MetaheuristicAlgorithm):
    """Implementación del algoritmo de optimización de moho del limo (Slime Mould Algorithm)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo SMA.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        self.z = 0.03  # Parámetro de probabilidad para comportamiento aleatorio

    def initialize_population(self):
        """Inicializa la población de mohos."""
        # Set random seed if provided

        if self.seed is not None:

            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []
        for _ in range(self.population_size):
            mould = SlimeMould(self.problem)
            self.population.append(mould)

        # Encontrar el mejor moho inicial
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

        # Initialize convergence curve with initial best fitness
        self.convergence_curve = [self.best_solution.fitness()]

        # Inicializar pesos
        self._update_weights()

    def _update_weights(self):
        """Actualiza los pesos de los mohos según su aptitud."""
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

    def update_population(self):
        """Actualiza la población en cada iteración."""
        # Actualizar pesos de los mohos según su aptitud actual
        self._update_weights()

        # La iteración actual es el tamaño de la curva de convergencia
        current_iter = len(self.convergence_curve)

        # Factor de volatilidad que disminuye con las iteraciones
        z = self.z - current_iter * (0.03 / self.max_iterations)

        # Actualizar cada moho
        for i in range(self.population_size):
            # No mover el mejor moho
            if self.population[i] is not self.best_solution:
                # Mover según el algoritmo SMA
                self.population[i].move(
                    self.best_solution,
                    self.population,
                    z,
                    current_iter + 1,
                    self.max_iterations,
                )

                # Actualizar mejor solución si es necesario
                if self.population[i].is_better_than(self.best_solution):
                    mould_copy = SlimeMould(self.problem)
                    mould_copy.copy(self.population[i])
                    self.best_solution = mould_copy

        # Registrar el mejor fitness en la curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
