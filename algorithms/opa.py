"""Orca Predator Algorithm (OPA).

This module implements the Orca Predator Algorithm, inspired by the
sophisticated hunting strategies of killer whales (orcas).

The algorithm models orca hunting behaviors:
1. Chasing phase: High-speed pursuit of prey
2. Attacking phase: Coordinated attack strategies
3. Driving phase: Herding prey into tight groups

OPA uses a unique direct route manipulation approach for VRP problems.

Reference:
    Jiang, P., et al. (2024).
    Orca predator algorithm: A novel bio-inspired metaheuristic algorithm
    for global optimization and engineering problems.
    Knowledge-Based Systems, 283, 111234.
    DOI: 10.1016/j.knosys.2023.111234

Example:
    >>> from algorithms.opa import OPA
    >>> from problems.vrp import VRPProblem
    >>> 
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>> 
    >>> # Initialize and run OPA
    >>> algo = OPA(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
import copy
import random
import numpy as np
import time
from algorithms.base import Individual, MetaheuristicAlgorithm


class Orca(Individual):
    """Una orca (solución VRP) con representación basada en rutas."""

    def __init__(self, problem):
        self.problem = problem
        # Inicializar con rutas aleatorias directamente
        self.position = self.problem.random_routes()
        self._fitness = None
        self.personal_best_position = copy.deepcopy(self.position)
        self.personal_best_fitness = self.fitness()

    def copy(self, other=None):
        """Copy method that follows the base class interface.
        
        Args:
            other: If provided, copy attributes from other to self.
                   If None, return a deep copy of self.
        
        Returns:
            Orca: A new Orca instance if other is None, otherwise None
        """
        if other is None:
            return copy.deepcopy(self)
        else:
            # Copy attributes from other to self
            self.position = copy.deepcopy(other.position)
            self._fitness = other._fitness
            self.personal_best_position = copy.deepcopy(other.personal_best_position)
            self.personal_best_fitness = other.personal_best_fitness
            return None

    def move(self, population, iteration, max_iterations):
        """Not used in OPA - update() method is used instead.
        
        This method is required by the base class but OPA uses a different
        update mechanism that works directly with route representations.
        """
        # No se usa directamente, se usa update en su lugar
        pass

    def fitness(self):
        """Calculate and return the fitness value using direct route evaluation.
        
        Returns:
            float: The fitness value (total cost) of the current route configuration
        """
        if self._fitness is None:
            # Evaluación directa usando las rutas
            self._fitness = self.problem.evaluate_routes(self.position)
        return self._fitness

    def is_feasible(self):
        """Check if the orca's route configuration is feasible.
        
        Returns:
            bool: True if all routes satisfy capacity and other constraints
        """
        return bool(self.problem.routes_are_feasible(self.position))

    # --- util operators --------------------------------------------------
    def _random_swap(self, routes):
        """Intercambia dos clientes aleatorios entre dos rutas distintas."""
        non_empty = [r for r in routes if len(r) > 2]  # Rutas con al menos un cliente
        if len(non_empty) < 2:
            return
        r1, r2 = random.sample(non_empty, 2)
        # Elegir clientes aleatorios (excluyendo depósito al inicio y fin)
        i = random.randrange(1, len(r1) - 1) if len(r1) > 2 else 1
        j = random.randrange(1, len(r2) - 1) if len(r2) > 2 else 1
        r1[i], r2[j] = r2[j], r1[i]

    def _two_opt(self, route):
        """Aplica 2‑opt a una sola ruta."""
        if len(route) < 4:  # Ruta debe tener al menos 2 clientes
            return
        # Elegir dos posiciones dentro de la ruta (excluyendo depósito)
        i = random.randrange(1, len(route) - 2)
        k = random.randrange(i + 1, len(route) - 1)
        # Invertir el segmento entre i y k
        route[i : k + 1] = list(reversed(route[i : k + 1]))

    def _relocate(self, routes, leader_routes):
        """
        Mueve un cliente desde una ruta aleatoria a otra posición.
        Si se provee leader_routes, preferentemente inserta en una de estas rutas.
        """
        # Identificar rutas con al menos un cliente
        src_candidates = [r for r in routes if len(r) > 2]
        if not src_candidates:
            return  # No hay rutas con clientes

        # Elegir ruta fuente y cliente a mover
        src = random.choice(src_candidates)
        idx = random.randrange(1, len(src) - 1)  # Elegir un cliente (no depósito)
        cust = src.pop(idx)

        # Si la ruta fuente queda solo con depósitos, eliminarla
        if len(src) <= 2:
            routes.remove(src)

        # Elegir ruta destino, preferentemente del líder
        dst_candidates = []
        if leader_routes:
            dst_candidates = [r for r in leader_routes if r != src]

        # Si no hay rutas del líder, usar cualquier otra ruta existente
        if not dst_candidates:
            dst_candidates = [r for r in routes if r != src]

        # Si no hay rutas destino, crear una nueva
        if not dst_candidates:
            new_route = [0, cust, 0]  # Nueva ruta con depósito - cliente - depósito
            routes.append(new_route)
            return

        # Insertar en la ruta destino
        dst = random.choice(dst_candidates)
        insert_pos = random.randrange(
            1, len(dst)
        )  # Posición después del depósito inicial
        dst.insert(insert_pos, cust)

    def update(self, g_best, phase, accept_prob):
        """
        Actualiza la posición de la Orca según la fase y probabilidad.

        Args:
            g_best: Mejor posición global (rutas del líder)
            phase: "chase" para exploración, "attack" para explotación
            accept_prob: Probabilidad de aceptar soluciones peores
        """
        # Crear una copia de la posición actual para modificar
        new_pos = copy.deepcopy(self.position)

        # Aplicar operadores según la fase
        if phase == "chase":  # Fase de exploración
            self._random_swap(new_pos)
            candidates_2opt = [r for r in new_pos if len(r) >= 4]
            if candidates_2opt:
                route_for_2opt = random.choice(candidates_2opt)
                self._two_opt(route_for_2opt)
        else:  # Fase de ataque (explotación)
            self._relocate(new_pos, g_best)

        # Reparar solución si el problema ofrece esa funcionalidad
        if hasattr(self.problem, "repair_routes"):
            new_pos = self.problem.repair_routes(new_pos)

        # Verificar factibilidad
        if not self.problem.routes_are_feasible(new_pos):
            return  # No actualizar si no es factible

        # Evaluar nueva posición
        new_fit = self.problem.evaluate_routes(new_pos)

        # Actualizar si mejora o según probabilidad de aceptación
        if new_fit < self.fitness() or random.random() < accept_prob:
            self.position = new_pos
            self._fitness = new_fit
            # Actualizar mejor posición personal si corresponde
            if new_fit < self.personal_best_fitness:
                self.personal_best_position = copy.deepcopy(new_pos)
                self.personal_best_fitness = new_fit


class OPA(MetaheuristicAlgorithm):
    """
    Orca Predator Algorithm (OPA) – Adaptado al problema de ruteo de vehículos (VRP)
    Inspirado en: Jiang et al. (2021)

    Esta implementación trabaja directamente con la representación de rutas para VRP.
    """

    def __init__(self, problem, population_size=40, max_iterations=1000, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)
        self.current_iter = 0
        self.population = []
        self.best_solution = None
        self.convergence_curve = []

    def initialize_population(self) -> None:
        """Inicializa la población de orcas con soluciones aleatorias."""
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)

        self.population = [Orca(self.problem) for _ in range(self.population_size)]
        self.best_solution = min(self.population, key=lambda o: o.fitness()).copy()
        self.convergence_curve = [self.best_solution.fitness()]
        self.current_iter = 0

    def update_population(self) -> None:
        """Actualiza la población para una iteración."""
        # Determinar fase actual y probabilidad de aceptación
        frac = self.current_iter / self.max_iterations
        phase = "chase" if frac < 0.5 else "attack"
        accept_prob = 0.3 * (1 - frac)

        # Obtener la mejor posición global actual
        leader_pos = copy.deepcopy(self.best_solution.position)

        # Actualizar cada orca
        for orca in self.population:
            orca.update(leader_pos, phase, accept_prob)

        # Actualizar mejor solución global
        current_best = min(self.population, key=lambda o: o.fitness())
        if current_best.is_better_than(self.best_solution):
            self.best_solution = current_best.copy()

        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
        self.current_iter += 1

    def execute(self):
        """Ejecuta el algoritmo completo."""
        self.start_time = time.time()
        self.initialize_population()
        try:
            for _ in range(self.max_iterations):
                self.update_population()
        finally:
            self.end_time = time.time()
        return self.best_solution

    def get_execution_time(self):
        """Retorna el tiempo de ejecución en segundos."""
        return self.end_time - self.start_time

    def get_convergence_curve(self):
        """Retorna la curva de convergencia."""
        return self.convergence_curve
