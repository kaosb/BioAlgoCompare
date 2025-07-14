"""Harris Hawks Optimization (HHO).

This module implements the Harris Hawks Optimization algorithm, inspired by
the cooperative hunting behavior of Harris hawks in nature.

The algorithm simulates the surprise pounce hunting strategy:
1. Exploration phase: Hawks perch randomly and search for prey
2. Transition from exploration to exploitation based on prey energy
3. Exploitation phase: Different attacking strategies based on prey escape energy
4. Soft and hard besiege with progressive rapid dives

Reference:
    Heidari, A. A., Mirjalili, S., Faris, H., Aljarah, I., Mafarja, M., & Chen, H. (2019).
    Harris hawks optimization: Algorithm and applications.
    Future Generation Computer Systems, 97, 849-872.
    DOI: 10.1016/j.future.2019.02.028

Example:
    >>> from algorithms.hho import HHO
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run HHO
    >>> algo = HHO(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm
from utils.math_functions import levy_flight


class Hawk(Individual):
    """Clase para representar un individuo en el algoritmo HHO (Harris Hawks Optimization)."""

    def __init__(self, problem):
        """
        Inicializa un halcón con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        self.energy = random.uniform(
            -1, 1
        )  # Energía para el mecanismo de escape de la presa

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

    def move(self, best_hawk, E, Xm, LB, UB):
        """
        Mueve al halcón según los lineamientos exactos del algoritmo HHO.
        Args:
            best_hawk: Individuo que actúa como 'conejo'.
            E: Energía de escape calculada externamente para este halcón.
            Xm: Vector promedio de la población en la iteración actual.
            LB, UB: Límites inferior y superior del dominio de búsqueda (arrays numpy).
        """
        dim = self.dimension
        q = random.random()
        r1, r2, r3, r4 = (
            random.random(),
            random.random(),
            random.random(),
            random.random(),
        )

        # ------------------------- FASE DE EXPLORACIÓN -------------------------
        if abs(E) >= 1:
            if q >= 0.5:
                X_rand = np.random.uniform(LB, UB, dim)
                self.position = X_rand - r1 * np.abs(X_rand - 2 * r2 * self.position)
            else:
                self.position = (best_hawk.position - Xm) - r3 * (LB + r4 * (UB - LB))

        # ------------------------- FASE DE EXPLOTACIÓN -------------------------
        else:
            r = random.random()
            if r >= 0.5 and abs(E) >= 0.5:  # soft besiege
                self.position = best_hawk.position - E * np.abs(
                    best_hawk.position - self.position
                )
            elif r >= 0.5 and abs(E) < 0.5:  # hard besiege
                self.position = best_hawk.position - E * np.abs(
                    best_hawk.position - self.position
                ) / (np.abs(E) + 1e-8)
            elif r < 0.5 and abs(E) >= 0.5:  # soft besiege + rapid dives
                J = 2 * (1 - random.random())
                Y = (
                    best_hawk.position
                    - E * np.abs(J) * best_hawk.position
                    - self.position
                )
                Z = Y + random.random() * levy_flight(dim)
                self.position = (
                    Y if self.problem.evaluate(Y) < self.problem.evaluate(Z) else Z
                )
            else:  # hard besiege + rapid dives
                Y = best_hawk.position - E * np.abs(best_hawk.position - self.position)
                Z = Y + random.random() * levy_flight(dim)
                self.position = (
                    Y if self.problem.evaluate(Y) < self.problem.evaluate(Z) else Z
                )

        # Asegurar que los valores estén dentro del rango [LB, UB]
        self.position = np.clip(self.position, LB, UB)

        # Resetear el fitness para recalcular
        self._fitness = None

    def copy(self, other):
        """
        Copia los valores de otro individuo a este.

        Args:
            other: Otro individuo (Hawk)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class HHO(MetaheuristicAlgorithm):
    """Implementación del algoritmo de optimización de halcones de Harris (Harris Hawks Optimization)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo HHO.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        self.levy_factor = 0.01  # Factor para vuelos de Levy
        self.escape_energy_factor = 2.0  # Factor de energía de escape

    def initialize_population(self):
        """Inicializa la población de halcones."""
        # Set random seed if provided

        if self.seed is not None:
            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []
        for _ in range(self.population_size):
            hawk = Hawk(self.problem)
            self.population.append(hawk)

        # Encontrar el mejor halcón inicial
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

        # Initialize convergence curve with initial best fitness
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        # La iteración actual es el tamaño de la curva de convergencia
        current_iter = len(self.convergence_curve)

        Xm = np.mean([h.position for h in self.population], axis=0)

        # Para problemas VRP, los límites son [0,1] para representación continua
        LB = np.zeros_like(Xm)
        UB = np.ones_like(Xm)

        # Actualizar cada halcón
        for i in range(self.population_size):
            # No mover el mejor halcón
            if self.population[i] is not self.best_solution:
                E0 = 2 * random.random() - 1
                E = 2 * (1 - current_iter / self.max_iterations) * E0
                self.population[i].move(self.best_solution, E, Xm, LB, UB)

                # Actualizar mejor solución si es necesario
                if self.population[i].is_better_than(self.best_solution):
                    hawk_copy = Hawk(self.problem)
                    hawk_copy.copy(self.population[i])
                    self.best_solution = hawk_copy

        # Registrar el mejor fitness en la curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
