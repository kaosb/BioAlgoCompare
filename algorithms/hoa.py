"""Hyena Optimization Algorithm (HOA).

This module implements the Hyena Optimization Algorithm, also known as
Spotted Hyena Optimizer (SHO), inspired by the social behavior and hunting
strategies of spotted hyenas.

The algorithm models:
1. Searching for prey (exploration)
2. Encircling prey
3. Hunting behavior with cooperative strategies
4. Attacking prey (exploitation)

Reference:
    Dhiman, G., & Kumar, V. (2017).
    Spotted hyena optimizer: A novel bio-inspired based metaheuristic
    technique for engineering applications.
    Advances in Engineering Software, 114, 48-70.
    DOI: 10.1016/j.advengsoft.2017.05.014

Example:
    >>> from algorithms.hoa import HOA
    >>> from problems.vrp import VRPProblem
    >>> 
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>> 
    >>> # Initialize and run HOA
    >>> algo = HOA(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Hyena(Individual):
    """Clase para representar un individuo en el algoritmo HOA."""

    def __init__(self, problem):
        """
        Inicializa un hiena con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None

    def fitness(self):
        """Calcula el fitness del individuo."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_better_than(self, other):
        """Compara si este individuo es mejor que otro."""
        return self.fitness() < other.fitness()

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return (
            True  # En VRP todas las soluciones son factibles con nuestro decodificador
        )

    def move(self, alpha, beta, delta, iteration, max_iterations):
        """
        Mueve la hiena según las reglas del algoritmo HOA.

        Args:
            alpha: Mejor hiena (líder)
            beta: Segunda mejor hiena
            delta: Tercera mejor hiena
            iteration: Iteración actual
            max_iterations: Número máximo de iteraciones
        """
        a = 2 - iteration * (2 / max_iterations)  # Decrece linealmente de 2 a 0

        for i in range(self.dimension):
            r1 = random.random()
            r2 = random.random()

            A = 2 * a * r1 - a  # Vector de coeficiente
            C = 2 * r2  # Vector de énfasis

            # Fase de exploración/explotación
            if abs(A) >= 1:  # Exploración
                rand_index = random.randint(0, 2)
                if rand_index == 0:
                    D = abs(C * alpha.position[i] - self.position[i])
                    self.position[i] = alpha.position[i] - A * D
                elif rand_index == 1:
                    D = abs(C * beta.position[i] - self.position[i])
                    self.position[i] = beta.position[i] - A * D
                else:
                    D = abs(C * delta.position[i] - self.position[i])
                    self.position[i] = delta.position[i] - A * D
            else:  # Explotación - Ataque en círculo
                D_alpha = abs(C * alpha.position[i] - self.position[i])
                D_beta = abs(C * beta.position[i] - self.position[i])
                D_delta = abs(C * delta.position[i] - self.position[i])

                X1 = alpha.position[i] - A * D_alpha
                X2 = beta.position[i] - A * D_beta
                X3 = delta.position[i] - A * D_delta

                self.position[i] = (X1 + X2 + X3) / 3

            # Mantener la posición dentro de los límites [0, 1]
            self.position[i] = max(0, min(1, self.position[i]))

        # Invalidar el fitness ya que la posición ha cambiado
        self._fitness = None

    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        if isinstance(other, Hyena):
            self.position = other.position.copy()
            self._fitness = other._fitness


class HOA(MetaheuristicAlgorithm):
    """Implementación del algoritmo Hyena Optimization Algorithm (HOA)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo HOA.

        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.alpha = None  # Mejor hiena
        self.beta = None  # Segunda mejor hiena
        self.delta = None  # Tercera mejor hiena

    def initialize_population(self):
        """Inicializa la población de hienas."""
        self.population = []

        for _ in range(self.population_size):
            hyena = Hyena(self.problem)
            self.population.append(hyena)

        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())

        # Asignar líderes
        self.alpha = self.population[0]
        self.beta = self.population[1]
        self.delta = self.population[2]

        # Guardar la mejor solución
        self.best_solution = Hyena(self.problem)
        self.best_solution.copy(self.alpha)

        # Inicializar curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)

        for i in range(self.population_size):
            # Mover cada hiena
            self.population[i].move(
                self.alpha, self.beta, self.delta, iteration, self.max_iterations
            )

        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())

        # Actualizar líderes
        self.alpha = self.population[0]
        self.beta = self.population[1]
        self.delta = self.population[2]

        # Actualizar la mejor solución si es necesario
        if self.alpha.is_better_than(self.best_solution):
            self.best_solution.copy(self.alpha)

        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
