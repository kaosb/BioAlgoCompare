import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class Protozoa(Individual):
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

    def move(self, population, iteration, max_iterations, pf_max=0.1, npairs=1):
        dim = self.dimension
        ps = len(population)
        i = population.index(self)

        # Probabilidades dinámicas
        pf = pf_max * random.random()
        pah = 0.5 * (1 + math.cos((iteration / max_iterations) * math.pi))
        pdr = 0.5 * (1 + math.cos(((ps - i) / ps) * math.pi))

        # Dormancia o reproducción
        if random.random() < pf:
            if random.random() < pdr:
                # Dormancia - Eq. 11
                self.position = self.lower_bounds + np.random.rand(dim) * (
                    self.upper_bounds - self.lower_bounds
                )
            else:
                # Reproducción - Eq. 13
                Mr = np.zeros(dim)
                idxs = np.random.permutation(dim)[: math.ceil(dim * random.random())]
                Mr[idxs] = 1
                delta = np.random.rand(dim) * (
                    self.lower_bounds
                    + np.random.rand(dim) * (self.upper_bounds - self.lower_bounds)
                )
                self.position = self.position + random.choice([-1, 1]) * delta * Mr
        else:
            Mf = np.zeros(dim)
            idxs = np.random.permutation(dim)[: math.ceil(dim * i / ps)]
            Mf[idxs] = 1
            if random.random() < pah:
                # Autotrofia - Eq. 1
                j = random.randint(0, ps - 1)
                neighbor_plus = population[min(i + 1, ps - 1)].position
                neighbor_minus = population[max(i - 1, 0)].position
                wa = math.exp(
                    -abs(population[max(i - 1, 0)].fitness())
                    / (population[min(i + 1, ps - 1)].fitness() + 1e-16)
                )
                delta = (
                    population[j].position
                    - self.position
                    + (wa * (neighbor_minus - neighbor_plus))
                ) / npairs
                f = random.random() * (
                    1 + math.cos((iteration / max_iterations) * math.pi)
                )
                self.position = self.position + f * delta * Mf
            else:
                # Heterotrofia - Eq. 7
                neighbor_minus = population[max(i - 1, 0)].position
                neighbor_plus = population[min(i + 1, ps - 1)].position
                wh = math.exp(
                    -abs(population[max(i - 1, 0)].fitness())
                    / (population[min(i + 1, ps - 1)].fitness() + 1e-16)
                )
                Xnear = (
                    1
                    + random.choice([-1, 1])
                    * random.random()
                    * (1 - iteration / max_iterations)
                ) * self.position
                delta = (
                    Xnear - self.position + (wh * (neighbor_minus - neighbor_plus))
                ) / npairs
                f = random.random() * (
                    1 + math.cos((iteration / max_iterations) * math.pi)
                )
                self.position = self.position + f * delta * Mf

        # Clip y reset
        self.position = np.clip(self.position, self.lower_bounds, self.upper_bounds)
        self._fitness = None

    def copy(self, other):
        if isinstance(other, Protozoa):
            self.position = other.position.copy()
            self._fitness = other._fitness


class APO(MetaheuristicAlgorithm):
    """Implementación del Artificial Protozoa Optimizer (APO), 2024."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)

    def initialize_population(self):
        """Inicializa la población de protozoos."""
        self.population = []
        for _ in range(self.population_size):
            protozoa = Protozoa(self.problem)
            self.population.append(protozoa)
        self.population.sort(key=lambda x: x.fitness())
        self.best_solution = Protozoa(self.problem)
        self.best_solution.copy(self.population[0])
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)
        self.population.sort(key=lambda x: x.fitness())
        self.population[0]
        self.population[-1]
        for i in range(self.population_size):
            self.population[i].move(self.population, iteration, self.max_iterations)
        self.population.sort(key=lambda x: x.fitness())
        if self.population[0].fitness() < self.best_solution.fitness():
            self.best_solution.copy(self.population[0])
        self.convergence_curve.append(self.best_solution.fitness())
