import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Fossa(Individual):
    def __init__(self, problem):
        self.problem = problem
        self.dimension = problem.get_dimension()
        # Para problemas VRP, los límites son [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None

    def fitness(self):
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

    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        self.position = np.copy(other.position)
        self._fitness = other._fitness

    def move(self, population, iteration, max_iterations):
        dim = self.dimension
        t = iteration + 1

        # Obtener candidatos mejores (lemures)
        lemurs = [ind for ind in population if ind.fitness() < self.fitness()]
        if not lemurs:
            return  # No movimiento si no hay mejores

        # Seleccionar un lemur aleatorio
        lemur = random.choice(lemurs)
        x_new = self.position.copy()

        for j in range(dim):
            random.random()
            if t <= max_iterations // 2:
                # Exploración (Eq. 5)
                I = random.choice([1, 2])
                r_ij = random.random()
                xj_p1 = self.position[j] + r_ij * (
                    lemur.position[j] - I * self.position[j]
                )
                x_new[j] = np.clip(xj_p1, self.lower_bounds[j], self.upper_bounds[j])
            else:
                # Explotación (Eq. 7)
                r_ij = random.random()
                range_j = self.upper_bounds[j] - self.lower_bounds[j]
                xj_p2 = self.position[j] + (1 - 2 * r_ij) * (range_j / t)
                x_new[j] = np.clip(xj_p2, self.lower_bounds[j], self.upper_bounds[j])

        # Reemplazar si mejora
        new_fit = self.problem.evaluate(x_new)
        if new_fit <= self.fitness():
            self.position = x_new
            self._fitness = new_fit


class FOA(MetaheuristicAlgorithm):
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)

    def initialize_population(self):
        self.population = [Fossa(self.problem) for _ in range(self.population_size)]
        self.population.sort(key=lambda x: x.fitness())
        self.best_solution = Fossa(self.problem)
        self.best_solution.copy(self.population[0])
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        iteration = len(self.convergence_curve)
        for fossa in self.population:
            fossa.move(self.population, iteration, self.max_iterations)
        self.population.sort(key=lambda x: x.fitness())
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])
        self.convergence_curve.append(self.best_solution.fitness())
