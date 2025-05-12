"""
Griffon Vultures Optimization Algorithm (GVOA) - Versión simplificada para VRP
Fuente: Hasan et al. (2025), Expert Systems with Applications.
DOI: 10.1016/j.eswa.2025.127206
"""

import numpy as np
import random
import copy
from algorithms.base import Individual, MetaheuristicAlgorithm


class Vulture(Individual):
    def __init__(self, problem):
        """
        Inicializa un buitre con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        # Continuous VRP representation in range [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.personal_best_position = np.copy(self.position)
        # Evaluate initial fitness and set personal best fitness
        self._fitness = None
        self.personal_best_fitness = None

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
        return self.problem.is_valid(self.position)

    def copy(self):
        """Crea una copia del buitre actual."""
        new_vulture = Vulture(self.problem)
        new_vulture.position = copy.deepcopy(self.position)
        new_vulture.personal_best_position = copy.deepcopy(self.personal_best_position)
        new_vulture._fitness = self._fitness
        new_vulture.personal_best_fitness = self.personal_best_fitness
        return new_vulture

    def move(
        self,
        leader_pos,
        informed_positions=None,
        phase="following",
        r=0.5,
        it=0,
        max_it=100,
    ):
        """
        Mueve el buitre según la fase del algoritmo.

        Args:
            leader_pos: Posición del mejor buitre global
            informed_positions: Posiciones de los buitres bien informados (élite)
            phase: Fase de movimiento ('following', 'foraging', 'search', 'scouting')
            r: Factor de paso
            it: Iteración actual
            max_it: Número máximo de iteraciones
        """
        # Adaptación temporal (decrece con las iteraciones)
        decay = 1 - (it / max_it)
        # Vectores aleatorios
        r1 = np.random.random(self.dimension)
        r2 = np.random.random(self.dimension)

        # Posición inicial para calcular el movimiento
        new_position = np.copy(self.position)

        if phase == "following":
            # Fase 1: Seguimiento del líder
            # Movimiento hacia el líder con perturbación aleatoria
            new_position = (
                self.position
                + decay * r1 * (leader_pos - self.position)
                + r * r2 * (np.random.random(self.dimension) - 0.5)
            )

        elif (
            phase == "foraging"
            and informed_positions is not None
            and len(informed_positions) > 0
        ):
            # Fase 2: Forrajeo grupal
            # Seleccionar una posición aleatoria informada
            target_pos = random.choice(informed_positions)
            # Mover hacia esa posición con influencia del líder
            new_position = (
                self.position
                + r1 * (target_pos - self.position)
                + decay * r2 * (leader_pos - self.position)
            )

        elif phase == "search":
            # Fase 3: Búsqueda independiente
            # Perturbación local con probabilidad adaptativa
            a = 2 * decay  # Parámetro que decrece con el tiempo
            if random.random() < 0.5:
                # Leve perturbación en una dimensión aleatoria
                idx = random.randrange(self.dimension)
                new_position[idx] = np.clip(
                    new_position[idx] + a * (random.random() - 0.5), 0, 1
                )
            else:
                # Perturbación aleatoria en todas las dimensiones
                new_position = self.position + a * (
                    np.random.random(self.dimension) - 0.5
                )

        elif phase == "scouting":
            # Fase 4: Exploración cerca del carroñeo (líder)
            # Exploración adaptativa alrededor del líder
            radius = max(0.1, decay) * r  # Radio que decrece con el tiempo
            if random.random() < 0.5:
                # Exploración cercana al líder
                new_position = leader_pos + radius * (
                    np.random.random(self.dimension) - 0.5
                )
            else:
                # Exploración alejada del líder
                new_position = leader_pos + (1 + radius) * (
                    np.random.random(self.dimension) - 0.5
                )

        # Asegurar que la nueva posición está en el rango [0,1]
        new_position = np.clip(new_position, 0, 1)

        # Aceptación condicional basada en mejora o probabilidad adaptativa
        if self.problem.is_valid(new_position):
            new_fit = self.problem.evaluate(new_position)
            curr_fit = self.fitness()
            # dynamic acceptance probability decreases over iterations
            r_eff = r * (1 - it / max_it)
            if new_fit < curr_fit or random.random() < r_eff:
                self.position = new_position
                self._fitness = new_fit  # Ya calculado

                # Update personal best if better
                if (
                    self.personal_best_fitness is None
                    or new_fit < self.personal_best_fitness
                ):
                    self.personal_best_position = np.copy(self.position)
                    self.personal_best_fitness = new_fit


class GVOA(MetaheuristicAlgorithm):
    """Implementación del algoritmo Griffon Vultures Optimization (GVOA)."""

    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo GVOA.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        # Parámetros del algoritmo
        self.elite_size = max(3, self.population_size // 5)  # Tamaño del grupo élite
        self.r = 0.2  # Radio de búsqueda inicial

    def initialize_population(self):
        """Inicializa la población de buitres."""
        # reproducibility
        if hasattr(self, "seed") and self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)
        self.population = []
        for _ in range(self.population_size):
            v = Vulture(self.problem)
            v._fitness = v.fitness()
            v.personal_best_fitness = v._fitness
            self.population.append(v)
        self.best_solution = min(self.population, key=lambda v: v.fitness()).copy()
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población de buitres en cada iteración."""
        # Iteración actual
        current_iter = len(self.convergence_curve)
        frac = current_iter / self.max_iterations

        # Ordenar población por fitness
        self.population.sort(key=lambda v: v.fitness())

        # Obtener grupo élite (mejores individuos)
        elite_vultures = self.population[: self.elite_size]
        elite_positions = [v.position for v in elite_vultures]

        # Posición del líder
        leader_pos = self.best_solution.position

        # Actualizar cada buitre según su posición en la población
        for i, vulture in enumerate(self.population):
            # dynamic phase based on fitness rank and progress
            if frac < 0.3:
                # early: more exploration
                phase = (
                    "scouting" if i >= int(self.population_size * frac) else "search"
                )
            else:
                # later: more exploitation
                phase = (
                    "foraging"
                    if i < int(self.population_size * (1 - frac))
                    else "following"
                )

            # Mover el buitre
            vulture.move(
                leader_pos=leader_pos,
                informed_positions=elite_positions,
                phase=phase,
                r=self.r,
                it=current_iter,
                max_it=self.max_iterations,
            )

            # Actualizar la mejor solución si encontramos una mejor
            if vulture.fitness() < self.best_solution.fitness():
                self.best_solution = vulture.copy()

        self.best_solution = min(self.population, key=lambda v: v.fitness()).copy()
        self.convergence_curve.append(self.best_solution.fitness())
