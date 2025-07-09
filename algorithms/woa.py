"""Whale Optimization Algorithm (WOA).

This module implements the Whale Optimization Algorithm, inspired by the
bubble-net hunting strategy of humpback whales.

The algorithm simulates three main behaviors:
1. Encircling prey: Whales update their position towards the best solution
2. Bubble-net attacking (exploitation): Spiral-shaped path around prey
3. Search for prey (exploration): Random search guided by a random whale

Reference:
    Mirjalili, S., & Lewis, A. (2016).
    The whale optimization algorithm.
    Advances in Engineering Software, 95, 51-67.
    DOI: 10.1016/j.advengsoft.2016.01.008

Example:
    >>> from algorithms.woa import WOA
    >>> from problems.vrp import VRPProblem
    >>> 
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>> 
    >>> # Initialize and run WOA
    >>> algo = WOA(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Whale(Individual):
    """Clase para representar un individuo en el algoritmo WOA (Whale Optimization Algorithm)."""

    def __init__(self, problem):
        """
        Inicializa una ballena con una posición aleatoria.

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

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return (
            True  # En VRP todas las soluciones son factibles con nuestro decodificador
        )

    def move(self, best_whale, a, a2, leader_type=0):
        """
        Mueve la ballena según las reglas del algoritmo WOA.

        Args:
            best_whale: Mejor ballena (líder)
            a: Parámetro de control que disminuye linealmente de 2 a 0
            a2: Parámetro de control para la espiral
            leader_type: Tipo de líder (0: mejor, 1: aleatorio)
        """
        r1 = random.random()  # Número aleatorio en [0, 1]
        r2 = random.random()  # Número aleatorio en [0, 1]

        A = 2 * a * r1 - a  # Parámetro de comportamiento
        C = 2 * r2  # Parámetro de ponderación

        # Seleccionar estrategia de movimiento
        p = (
            random.random()
        )  # Probabilidad para seleccionar entre encogimiento o espiral

        if p < 0.5:  # Encogimiento (estrategia de exploración/explotación)
            if abs(A) < 1:  # Explotación: acercarse a la presa (mejor solución)
                for i in range(self.dimension):
                    D = abs(C * best_whale.position[i] - self.position[i])
                    self.position[i] = best_whale.position[i] - A * D
            else:  # Exploración: moverse aleatoriamente
                X_rand = np.random.uniform(0, 1, self.dimension)
                for i in range(self.dimension):
                    D = abs(C * X_rand[i] - self.position[i])
                    self.position[i] = X_rand[i] - A * D
        else:  # Estrategia de espiral (movimiento en espiral alrededor de la presa)
            for i in range(self.dimension):
                D = abs(best_whale.position[i] - self.position[i])
                l = random.uniform(
                    -1, 1
                )  # Parámetro aleatorio para definir la forma de la espiral
                self.position[i] = (
                    D * math.exp(a2 * l) * math.cos(2 * math.pi * l)
                    + best_whale.position[i]
                )

        # Asegurar que los valores estén dentro del rango [0, 1]
        LB = np.zeros_like(self.position)
        UB = np.ones_like(self.position)
        self.position = np.clip(self.position, LB, UB)

        # Reset fitness para recalcular
        self._fitness = None

    def copy(self, other):
        """
        Copia los valores de otro individuo a este.

        Args:
            other: Otro individuo (Whale)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class WOA(MetaheuristicAlgorithm):
    """Implementación del algoritmo de optimización de ballenas (Whale Optimization Algorithm)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo WOA.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.convergence_curve = []
        self.a2 = 0.5  # Constante para definir la forma de la espiral logarítmica

    def initialize_population(self):
        """Inicializa la población de ballenas."""
        # Set random seed if provided

        if self.seed is not None:

            random.seed(self.seed)

            np.random.seed(self.seed)

        self.population = []
        for _ in range(self.population_size):
            whale = Whale(self.problem)
            self.population.append(whale)

        # Encontrar la mejor ballena inicial
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]
        
        # Initialize convergence curve with initial best fitness
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        # Calcular el valor de 'a' que disminuye linealmente de 2 a 0
        a = 2 - self.convergence_curve.count(self.best_solution.fitness()) * (
            2 / self.max_iterations
        )

        # Actualizar posición de cada ballena
        for i in range(self.population_size):
            # No mover la mejor ballena
            if self.population[i] is not self.best_solution:
                self.population[i].move(self.best_solution, a, self.a2)

                # Actualizar mejor solución si es necesario
                if self.population[i].is_better_than(self.best_solution):
                    whale_copy = Whale(self.problem)
                    whale_copy.copy(self.population[i])
                    self.best_solution = whale_copy

        # Registrar el mejor fitness en la curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
