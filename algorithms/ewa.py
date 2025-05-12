import numpy as np
import random
import time
from .base import Individual, MetaheuristicAlgorithm


class Earthworm(Individual):
    """Clase para representar un individuo en el algoritmo EWA (Earthworm Algorithm)."""

    def __init__(self, problem):
        """
        Inicializa un gusano de tierra con una posición aleatoria.

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

    def move(self, best_worm, alpha=0.8, beta=0.2, generation=0, gamma=0.99):
        """
        Movimiento y reproducción según el algoritmo EWA original.

        Args:
            best_worm: Mejor gusano (líder)
            alpha: Similarity factor
            beta: Proportional factor para la suma ponderada
            generation: número de iteración actual
            gamma: factor de enfriamiento para β
        """
        LB = np.zeros_like(self.position)
        UB = np.ones_like(self.position)

        # Reproducción 1 (auto-replicación con modificación)
        u1 = UB + LB - alpha * self.position

        # Reproducción 2 (crossover uniforme con mejor gusano)
        u12 = np.copy(self.position)
        u22 = np.copy(best_worm.position)
        for k in range(self.dimension):
            if random.random() > 0.5:
                u12[k] = self.position[k]
                u22[k] = best_worm.position[k]
            else:
                u12[k] = best_worm.position[k]
                u22[k] = self.position[k]
        u2 = u12 if random.random() < 0.5 else u22

        # Suma ponderada
        beta_t = beta * (gamma**generation)
        u_prime = beta_t * u1 + (1 - beta_t) * u2

        # Mutación Cauchy
        W = np.mean([self.position[k] for k in range(self.dimension)])
        C_d = np.random.standard_cauchy(size=self.dimension)
        u_final = u_prime + W * C_d

        # Clip
        self.position = np.clip(u_final, LB, UB)
        self._fitness = None

    def copy(self, other):
        """
        Copia los valores de otro individuo a este.

        Args:
            other: Otro individuo (Earthworm)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class EWA(MetaheuristicAlgorithm):
    """Implementación del algoritmo de optimización de gusanos de tierra (Earthworm Algorithm)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo EWA.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.alpha = 0.8  # Parámetro de intensificación
        self.beta = 0.2  # Parámetro de exploración
        self.convergence_curve = []

    def initialize_population(self):
        """Inicializa la población de gusanos de tierra."""
        self.population = []
        for _ in range(self.population_size):
            worm = Earthworm(self.problem)
            self.population.append(worm)

        # Encontrar el mejor gusano inicial
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

    def update_population(self):
        """Actualiza la población en cada iteración (fase de movimiento y registro de convergencia)."""
        current_iter = len(self.convergence_curve)
        # 1. Fase de movimiento: mover todos los gusanos
        for i in range(self.population_size):
            # No mover el mejor gusano
            if self.population[i] is not self.best_solution:
                self.population[i].move(
                    self.best_solution, self.alpha, self.beta, current_iter
                )

                # Actualizar mejor solución si es necesario
                if self.population[i].is_better_than(self.best_solution):
                    worm_copy = Earthworm(self.problem)
                    worm_copy.copy(self.population[i])
                    self.best_solution = worm_copy

        # 2. Registrar convergencia
        self.convergence_curve.append(self.best_solution.fitness())
