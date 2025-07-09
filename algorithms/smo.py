"""
Starling Murmuration Optimizer (SMO) - Versión adaptada para optimización continua
Fuente: Zamani, Nadimi-Shahraki & Gandomi (2022), Computer Methods in Applied Mechanics and Engineering.
DOI: 10.1016/j.cma.2022.114616
"""

import numpy as np
import random
import copy
from algorithms.base import Individual, MetaheuristicAlgorithm


class Starling(Individual):
    """Individual starling in the SMO algorithm.

    Represents a starling with its position and murmuration behaviors.
    Starlings exhibit collective motion patterns and adaptive flocking.

    Attributes:
        problem: The optimization problem instance
        position: Current position in the search space
        personal_best_position: Best position found by this starling
        _fitness: Cached fitness value
        personal_best_fitness: Best fitness value found
    """

    def __init__(self, problem):
        """
        Inicializa un estornino para el algoritmo SMO.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        # Generar solución aleatoria - representación continua
        self.position = self.problem.random_solution()
        self.personal_best_position = copy.deepcopy(self.position)
        self._fitness = None
        self.personal_best_fitness = None

    def fitness(self):
        """Calcula el fitness del individuo."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return bool(self.problem.is_valid(self.position))

    def copy(self):
        """Crea una copia del estornino actual."""
        new_starling = Starling(self.problem)
        new_starling.position = copy.deepcopy(self.position)
        new_starling.personal_best_position = copy.deepcopy(self.personal_best_position)
        new_starling._fitness = self._fitness
        new_starling.personal_best_fitness = self.personal_best_fitness
        return new_starling

    def move(
        self, best_position, behavior_type, members=None, coef=0.5, it=0, max_it=100
    ):
        """
        Mueve el estornino - adaptado para representación continua (array de numpy).
        - behavior_type: 'separating', 'diving', 'whirling'
        - coef and it/max_it can be used to tune operator intensity
        """
        # Crear copia de seguridad de posición actual
        new_position = copy.deepcopy(self.position)

        # Adaptación temporal (decrece con las iteraciones)
        decay = 1 - (it / max_it) if max_it > 0 else 0.5

        try:
            # Aplicar diferentes comportamientos según la estrategia
            if behavior_type == "separating":
                # Exploración más aleatoria
                r = np.random.random(new_position.shape)
                new_position = new_position + decay * coef * (2 * r - 1)
            elif behavior_type == "diving":
                # Explotación hacia mejor solución (movimiento más pequeño)
                if (
                    hasattr(best_position, "shape")
                    and best_position.shape == new_position.shape
                ):
                    new_position = new_position + decay * coef * (
                        best_position - new_position
                    )
                else:
                    # Perturbación pequeña si no hay información del mejor
                    r = np.random.random(new_position.shape)
                    new_position = new_position + decay * coef * 0.1 * (2 * r - 1)
            elif behavior_type == "whirling":
                # Movimiento intermedio - combinación de exploración y explotación
                if (
                    hasattr(best_position, "shape")
                    and best_position.shape == new_position.shape
                ):
                    r1 = np.random.random(new_position.shape)
                    r2 = np.random.random(new_position.shape)
                    new_position = new_position + decay * coef * (
                        r1 * (best_position - new_position)
                        + r2 * 0.1 * (2 * np.random.random(new_position.shape) - 1)
                    )
                else:
                    # Movimiento aleatorio si no hay información del mejor
                    r = np.random.random(new_position.shape)
                    new_position = new_position + decay * coef * 0.5 * (2 * r - 1)

            # Asegurar que la posición esté dentro de los límites [0,1]
            new_position = np.clip(new_position, 0, 1)
        except Exception:
            # En caso de error, aplicar una pequeña perturbación
            new_position = (
                self.position
                + np.random.uniform(-0.05, 0.05, self.position.shape) * decay
            )
            new_position = np.clip(new_position, 0, 1)

        # Evaluar y actualizar si mejora
        try:
            new_fit = self.problem.evaluate(new_position)
            curr_fit = self.fitness()

            # Aceptar si mejora o con pequeña probabilidad (criterio de Metropolis)
            if new_fit < curr_fit or random.random() < 0.1 * decay:
                self.position = new_position
                self._fitness = new_fit

                # Actualizar mejor personal si corresponde
                if (
                    self.personal_best_fitness is None
                    or new_fit < self.personal_best_fitness
                ):
                    self.personal_best_position = copy.deepcopy(self.position)
                    self.personal_best_fitness = new_fit
        except Exception:
            # Si hay error, mantener posición actual
            pass


class SMO(MetaheuristicAlgorithm):
    """Implementación del algoritmo Starling Murmuration Optimizer (SMO)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo SMO.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.k = min(10, self.population_size // 3)  # Número de grupos (flocks)
        self.mu = 0.3  # Proporción de individuos en separación
        self.seed = seed  # Guardar la semilla como atributo
        self.convergence_curve = []  # Inicializar curva de convergencia

    def initialize_population(self):
        """Inicializa la población de estorninos."""
        # Inicializar semilla si está disponible
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)

        # Reiniciar la convergence_curve
        self.convergence_curve = []

        # Inicializar población de estorninos
        self.population = []
        for _ in range(self.population_size):
            s = Starling(self.problem)
            s._fitness = s.fitness()
            s.personal_best_fitness = s._fitness
            self.population.append(s)

        # Guardar mejor solución encontrada
        self.best_solution = min(self.population, key=lambda s: s.fitness()).copy()
        # Añadir primer punto de convergencia
        self.convergence_curve.append(float(self.best_solution.fitness()))

    def update_population(self):
        """Actualiza la población de estorninos en cada iteración."""
        # Iteración actual
        current_iter = len(self.convergence_curve)

        # Ordenar población por fitness
        self.population.sort(key=lambda s: s.fitness())

        # Tamaño del subconjunto de separación (exploración)
        sep_size = int(self.mu * self.population_size)

        # Dividir en k grupos (bandadas)
        flocks = []
        group_size = max(1, self.population_size // self.k)

        for i in range(self.k):
            start_idx = i * group_size
            end_idx = (i + 1) * group_size if i < self.k - 1 else self.population_size
            flocks.append(self.population[start_idx:end_idx])

        # Calcular calidad promedio de cada grupo
        flock_qualities = []
        for flock in flocks:
            quality = sum(s.fitness() for s in flock) / len(flock)
            flock_qualities.append(quality)

        avg_quality = sum(flock_qualities) / len(flock_qualities)

        # Actualizar cada estornino según su grupo y posición
        for i, s in enumerate(self.population):
            # Determinar comportamiento y grupo
            if i < sep_size:
                # Grupo de exploración (separación)
                behavior = "separating"
                flock_members = None
            else:
                # Grupo regular basado en calidad
                flock_idx = min(i // group_size, self.k - 1)
                flock_members = flocks[flock_idx]
                if flock_qualities[flock_idx] < avg_quality:
                    # Grupo mejor que el promedio: buceo (explotación)
                    behavior = "diving"
                else:
                    # Grupo peor que el promedio: remolino (exploración)
                    behavior = "whirling"

            # Factor de adaptación basado en la posición
            coef = 0.5 * (1 - i / self.population_size)

            # Mover el estornino
            s.move(
                best_position=self.best_solution.position,
                behavior_type=behavior,
                members=flock_members,
                coef=coef,
                it=current_iter,
                max_it=self.max_iterations,
            )

        # Actualizar mejor solución encontrada globalmente
        best_individual = min(self.population, key=lambda s: s.fitness())
        if best_individual.is_better_than(self.best_solution):
            self.best_solution = best_individual.copy()

        # Añadir punto a la curva de convergencia
        self.convergence_curve.append(float(self.best_solution.fitness()))

    def get_convergence_curve(self):
        """Retorna la curva de convergencia."""
        if not isinstance(self.convergence_curve, list):
            return []
        return self.convergence_curve
