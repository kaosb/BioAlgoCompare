import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm


class MantaRay(Individual):
    """Clase para representar un individuo en el algoritmo MRFO (Manta Ray Foraging Optimization)."""

    def __init__(self, problem):
        """
        Inicializa una mantarraya con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        # Para problemas VRP, los límites son [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
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

    def move(self, best_ray, t, T, alpha=2.0):
        """
        Mueve la mantarraya según las reglas del algoritmo MRFO.

        Args:
            best_ray: Mejor mantarraya (líder)
            t: Iteración actual
            T: Número máximo de iteraciones
            alpha: Factor de espiral
        """
        r = random.random()  # Factor aleatorio para seleccionar comportamiento
        beta = (
            2 * math.exp(1 - (t / T)) * math.sin(2 * math.pi * r)
        )  # Controla la espiral

        if t / T < 0.5:  # Primera mitad: forrajeo en cadena
            for i in range(self.dimension):
                r1 = random.random()
                # Seguir a la mejor mantarraya con factor de espiral
                self.position[i] = (
                    best_ray.position[i]
                    + beta * (best_ray.position[i] - self.position[i])
                    + alpha * r1
                )
        else:  # Segunda mitad: forrajeo en ciclón
            for i in range(self.dimension):
                r2 = random.random()
                if random.random() < 0.5:  # Espiral externa (alejándose)
                    # Comportamiento de ciclón
                    self.position[i] = best_ray.position[i] + alpha * math.exp(
                        beta * r2
                    ) * math.cos(2 * math.pi * r2) * abs(
                        best_ray.position[i] - self.position[i]
                    )
                else:  # Espiral interna (acercándose)
                    # Exploración de profundidad
                    self.position[i] = (
                        best_ray.position[i]
                        + random.random() * (best_ray.position[i] - self.position[i])
                        + beta * r2
                    )

        LB = self.lower_bounds
        UB = self.upper_bounds
        self.position = np.clip(self.position, LB, UB)

        # Fase opcional: somersault foraging (al final de cada iteración o periódicamente)
        somersault_prob = 0.3  # probabilidad de aplicar este paso
        if random.random() < somersault_prob:
            for i in range(self.dimension):
                self.position[i] += random.uniform(-1, 1) * abs(
                    best_ray.position[i] - self.position[i]
                )

        # Resetear fitness para recalcular
        self._fitness = None

    def copy(self, other):
        """
        Copia los valores de otro individuo a este.

        Args:
            other: Otro individuo (MantaRay)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness


class MRFO(MetaheuristicAlgorithm):
    """Implementación del algoritmo de optimización de forrajeo de mantarrayas (Manta Ray Foraging Optimization)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo MRFO.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.spiral_factor = 2.0  # Factor para el comportamiento en espiral

    def initialize_population(self):
        """Inicializa la población de mantarrayas."""
        self.population = []
        for _ in range(self.population_size):
            ray = MantaRay(self.problem)
            self.population.append(ray)

        # Encontrar la mejor mantarraya inicial
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        # La iteración actual es el tamaño de la curva de convergencia
        current_iter = len(self.convergence_curve)

        # Actualizar cada mantarraya
        for i in range(self.population_size):
            # No mover la mejor mantarraya
            if self.population[i] is not self.best_solution:
                # Mover según el algoritmo MRFO
                self.population[i].move(
                    self.best_solution,
                    current_iter,
                    self.max_iterations,
                    self.spiral_factor,
                )

                # Actualizar mejor solución si es necesario
                if self.population[i].is_better_than(self.best_solution):
                    ray_copy = MantaRay(self.problem)
                    ray_copy.copy(self.population[i])
                    self.best_solution = ray_copy

        # Registrar el mejor fitness en la curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
