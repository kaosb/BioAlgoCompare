"""
Raven Roosting Optimization (RRO)
Fuente: Brabazon, Cui & O'Neill (2016)
DOI: 10.1007/s00500-014-1520-5
"""

import numpy as np
import random
from .base import Individual, MetaheuristicAlgorithm


class Raven(Individual):
    """
    Representa un cuervo en RRO.
    """

    def __init__(self, problem, rng=None):
        """
        Inicializa un cuervo con una posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
            rng: NumPy random generator instance
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.rng = rng if rng is not None else np.random.default_rng()
        self.position = self.rng.uniform(0, 1, self.dimension)
        self.personal_best_position = np.copy(self.position)
        self._fitness = None
        self._personal_best_fitness = None

        # Límites para el espacio de búsqueda en VRP (siempre entre 0 y 1)
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)

    def fitness(self):
        """Calcula el fitness del individuo."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def personal_best_fitness(self):
        """Calcula el fitness de la mejor posición personal."""
        if self._personal_best_fitness is None:
            self._personal_best_fitness = self.problem.evaluate(
                self.personal_best_position
            )
        return self._personal_best_fitness

    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return (
            True  # En VRP todas las soluciones son factibles con nuestro decodificador
        )

    def copy(self):
        """Crea una copia del individuo (sin consumir estado del RNG)."""
        new = object.__new__(Raven)
        new.problem = self.problem
        new.dimension = self.dimension
        new.rng = self.rng
        new.lower_bounds = self.lower_bounds
        new.upper_bounds = self.upper_bounds
        new.position = np.copy(self.position)
        new.personal_best_position = np.copy(self.personal_best_position)
        new._fitness = self._fitness
        new._personal_best_fitness = self._personal_best_fitness
        return new

    def move(self, target_position, Rpcpt, Npcpt, Nsteps, Pstop):
        """
        Mueve el cuervo hacia target_position, con percepciones y posible parada anticipada.
        """
        dim = len(self.position)
        curr_pos = np.copy(self.position)
        best_pos = np.copy(self.personal_best_position)
        best_fit = self.personal_best_fitness()
        for step in range(Nsteps):
            # Dirección hacia el objetivo + pequeña perturbación gaussiana
            direction = target_position - curr_pos
            if np.linalg.norm(direction) > 1e-12:
                direction = direction / np.linalg.norm(direction)
            # Aleatoriedad en la dirección
            noisy_direction = direction + self.rng.normal(0, 0.1, size=dim)
            noisy_direction = noisy_direction / (
                np.linalg.norm(noisy_direction) + 1e-12
            )
            # Paso proporcional al radio de percepción
            step_size = Rpcpt / Nsteps
            next_pos = curr_pos + step_size * noisy_direction
            # Clipping
            next_pos = np.clip(next_pos, self.lower_bounds, self.upper_bounds)
            # Percepción: Npcpt intentos dentro de bola de radio Rpcpt
            improved = False
            for _ in range(Npcpt):
                # Percepción aleatoria en una bola de radio Rpcpt
                rand_dir = self.rng.normal(0, 1, size=dim)
                rand_dir = rand_dir / (np.linalg.norm(rand_dir) + 1e-12)
                radius = self.rng.uniform(0, Rpcpt)
                percept_pos = curr_pos + rand_dir * radius
                percept_pos = np.clip(percept_pos, self.lower_bounds, self.upper_bounds)
                fit = self.problem.evaluate(percept_pos)
                if fit < best_fit:
                    best_fit = fit
                    best_pos = np.copy(percept_pos)
                    improved = True
            # Si alguna percepción mejoró el personal_best, considerar parar
            if improved and self.rng.uniform() < Pstop:
                curr_pos = np.copy(best_pos)
                break
            curr_pos = np.copy(next_pos)
        # Actualiza posición y personal_best si corresponde
        self.position = np.copy(curr_pos)
        self._fitness = None  # recalcular fitness
        curr_fit = self.fitness()
        if curr_fit < self.personal_best_fitness():
            self.personal_best_position = np.copy(self.position)
            self._personal_best_fitness = curr_fit


class RRO(MetaheuristicAlgorithm):
    """
    Raven Roosting Optimization (RRO)
    """

    def __init__(
        self,
        problem,
        population_size=30,
        max_iterations=100,
        Rpcpt=None,
        Rleader=None,
        Npcpt=10,
        Nsteps=10,
        Percfollow=0.2,
        Pstop=0.1,
        seed=None,
    ):
        """
        Inicializa el algoritmo RRO.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            Rpcpt: Radio de percepción
            Rleader: Radio alrededor del líder
            Npcpt: Número de percepciones
            Nsteps: Número de pasos
            Percfollow: Probabilidad de seguir al líder
            Pstop: Probabilidad de parar anticipadamente
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)

        # Establecer dimensión del problema
        self.D = problem.get_dimension()

        # Configurar parámetros específicos del algoritmo
        # Para VRP, el espacio de búsqueda está entre 0 y 1
        R = 1.0  # Radio del espacio de búsqueda

        if Rpcpt is None:
            self.Rpcpt = (
                0.1 * R * np.sqrt(self.D)
            )  # Valor ajustado para el espacio [0,1]
        else:
            self.Rpcpt = Rpcpt

        if Rleader is None:
            self.Rleader = (
                0.1 * R * np.sqrt(self.D)
            )  # Valor ajustado para el espacio [0,1]
        else:
            self.Rleader = Rleader

        self.Npcpt = Npcpt
        self.Nsteps = Nsteps
        self.Percfollow = Percfollow
        self.Pstop = Pstop
        self.population = []

    def initialize_population(self):
        """Inicializa la población de cuervos."""
        self.population = []
        for _ in range(self.population_size):
            raven = Raven(self.problem, rng=self.rng)
            self.population.append(raven)

        # Inicializar mejor solución y curva de convergencia
        leader = min(self.population, key=lambda r: r.fitness())
        self.best_solution = leader.copy()
        self.convergence_curve = [self.best_solution.fitness()]

    def update_population(self):
        """Actualiza la población en cada iteración."""
        # Asigna LEADER (mejor fitness actual)
        leader = min(self.population, key=lambda r: r.fitness())
        leader_pos = np.copy(leader.position)

        for idx, raven in enumerate(self.population):
            if self.rng.uniform() < self.Percfollow:
                # Seguir al líder con perturbación dentro de bola de radio Rleader
                rand_dir = self.rng.normal(0, 1, size=self.D)
                rand_dir = rand_dir / (np.linalg.norm(rand_dir) + 1e-12)
                radius = self.rng.uniform(0, self.Rleader)
                target_pos = leader_pos + rand_dir * radius
                target_pos = np.clip(target_pos, 0, 1)  # Límites para VRP [0,1]
            else:
                # Seguir su personal_best
                target_pos = np.copy(raven.personal_best_position)

            raven.move(target_pos, self.Rpcpt, self.Npcpt, self.Nsteps, self.Pstop)

        # Actualizar mejor solución global y registrar convergencia
        leader = min(self.population, key=lambda r: r.fitness())
        if leader.fitness() < self.best_solution.fitness():
            self.best_solution = leader.copy()
        self.convergence_curve.append(self.best_solution.fitness())
