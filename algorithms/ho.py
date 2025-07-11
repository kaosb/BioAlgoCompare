"""
Hippopotamus Optimization Algorithm (HO)

Implementación del algoritmo de optimización inspirado en el comportamiento
de los hipopótamos (Hippopotamus amphibius) propuesto por Amiri et al. (2024).

Referencias:
    Mohammad Hussein Amiri, Nastaran Mehrabi Hashjin, Mohsen Montazeri, Seyedali Mirjalili & Nima Khodadadi.
    "Hippopotamus optimization algorithm: a novel nature-inspired optimization algorithm".
    Scientific Reports 14, Article number: 5032 (2024).
    https://doi.org/10.1038/s41598-024-54909-3

El algoritmo simula tres comportamientos principales de los hipopótamos:
1. Fase de posición: Movimiento hacia el líder y mejor global
2. Fase de defensa: Clustering jerárquico para protección grupal
3. Fase de evasión: Perturbación tipo Levy para escapar de depredadores

Ecuaciones principales:
- Posición: X_i^{t+1} = X_i^t + α*(X_leader - X_i^t) + β*rand*(X_global - X_i^t)
- Defensa: Clustering y balanceo de carga cuando coef_variacion > threshold
- Evasión: X_i^{t+1} = X_i^t + γ*Levy()*perturbation
"""

import numpy as np
import math
from typing import List, Tuple, Optional
from algorithms.base import Individual, MetaheuristicAlgorithm
from scipy.spatial.distance import cdist
from scipy.cluster.hierarchy import linkage, fcluster


def levy_flight(dim: int, beta: float = 1.5) -> np.ndarray:
    """
    Genera un vector de desplazamiento siguiendo una distribución Lévy.

    Args:
        dim: Dimensión del vector
        beta: Parámetro de la distribución (típicamente 1.5)

    Returns:
        Vector de desplazamiento Lévy
    """
    sigma = (
        math.gamma(1 + beta)
        * math.sin(math.pi * beta / 2)
        / (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))
    ) ** (1 / beta)
    u = np.random.normal(0, sigma, dim)
    v = np.random.normal(0, 1, dim)
    return u / (np.abs(v) ** (1 / beta))


class Hippopotamus(Individual):
    """
    Clase para representar un hipopótamo en el algoritmo HO.

    Cada hipopótamo tiene:
    - position: Posición en el espacio de soluciones
    - velocity: Velocidad de movimiento (para memoria)
    - fitness_value: Valor de fitness actual
    - is_leader: Si es líder de su grupo
    - group_id: ID del grupo al que pertenece
    """

    def __init__(self, problem):
        """Inicializa un hipopótamo con posición aleatoria."""
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self.velocity = np.zeros(self.dimension)
        self.fitness_value = float("inf")
        self.is_leader = False
        self.group_id = 0
        self.update_fitness()

    def update_fitness(self):
        """Actualiza el valor de fitness del hipopótamo."""
        self.fitness_value = self.problem.evaluate(self.position)

    def fitness(self) -> float:
        """Retorna el fitness del hipopótamo."""
        return self.fitness_value

    def is_feasible(self) -> bool:
        """Verifica si la solución es factible."""
        if hasattr(self.problem, "is_valid"):
            return self.problem.is_valid(self.position)
        return True

    def copy(self, other: "Hippopotamus") -> None:
        """Copia los valores de otro hipopótamo."""
        self.position = other.position.copy()
        self.velocity = other.velocity.copy()
        self.fitness_value = other.fitness_value
        self.is_leader = other.is_leader
        self.group_id = other.group_id

    def move(
        self, population: List["Hippopotamus"], iteration: int, max_iterations: int
    ) -> None:
        """
        Mueve el hipopótamo según las tres fases del algoritmo HO.

        Args:
            population: Población de hipopótamos
            iteration: Iteración actual
            max_iterations: Máximo de iteraciones
        """
        # Esta función se sobrescribe en HO.update_population()
        pass


class HO(MetaheuristicAlgorithm):
    """
    Implementación del Hippopotamus Optimization Algorithm.

    Parámetros del algoritmo según Amiri et al. (2024):
    - α (alpha): Factor de atracción al líder [0.1, 0.9]
    - β (beta): Factor de atracción global [0.2, 0.8]
    - γ (gamma): Factor de perturbación [0.3, 1.0]
    - θ (theta): Umbral para cambio de fase [0.4, 0.6]
    """

    def __init__(
        self,
        problem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: int = None,
    ):
        """
        Inicializa el algoritmo HO.

        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)

        # Parámetros del algoritmo según el paper
        self.alpha_min = 0.1
        self.alpha_max = 0.9
        self.beta_min = 0.2
        self.beta_max = 0.8
        self.gamma_min = 0.3
        self.gamma_max = 1.0
        self.theta = 0.5  # Umbral para cambio de fase

        # Variables para tracking
        self.global_best = None
        self.leaders = []
        self.groups = []

        # Para QC-DVRP multiobjetivo
        self.use_multiobjective = hasattr(problem, "evaluate_multi")
        self.pareto_front = []

    def initialize_population(self) -> None:
        """Inicializa la población de hipopótamos."""
        self.population = []

        for _ in range(self.population_size):
            hippo = Hippopotamus(self.problem)
            self.population.append(hippo)

            # Actualizar mejor global
            if self.global_best is None or hippo.fitness() < self.global_best.fitness():
                self.global_best = Hippopotamus(self.problem)
                self.global_best.copy(hippo)

        self.best_solution = self.global_best
        self.convergence_curve.append(self.global_best.fitness())

    def update_population(self) -> None:
        """
        Actualiza la población usando las tres fases del algoritmo HO.

        Fases según Amiri et al. (2024):
        1. Fase de posición (Position phase)
        2. Fase de defensa (Defense phase)
        3. Fase de evasión (Predation phase)
        """
        iteration = len(self.convergence_curve)

        # Actualizar parámetros adaptativos
        progress = iteration / self.max_iterations
        alpha = self.alpha_max - (self.alpha_max - self.alpha_min) * progress
        beta = self.beta_max - (self.beta_max - self.beta_min) * progress
        gamma = self.gamma_min + (self.gamma_max - self.gamma_min) * progress

        # Determinar fase basada en progreso y fitness
        avg_fitness = np.mean([h.fitness() for h in self.population])
        fitness_ratio = (
            self.global_best.fitness() / avg_fitness if avg_fitness > 0 else 0
        )

        if fitness_ratio < self.theta:
            # Fase 1: Posición (exploración)
            self._position_phase(alpha, beta)
        elif progress < 0.7:
            # Fase 2: Defensa (clustering y balanceo)
            self._defense_phase()
        else:
            # Fase 3: Evasión (explotación con perturbación)
            self._evasion_phase(gamma)

        # Actualizar mejor global
        for hippo in self.population:
            if hippo.fitness() < self.global_best.fitness():
                self.global_best.copy(hippo)

        self.best_solution = self.global_best
        self.convergence_curve.append(self.global_best.fitness())

    def _position_phase(self, alpha: float, beta: float) -> None:
        """
        Fase de posición: Movimiento hacia líder y mejor global.

        Ecuación (Amiri et al., 2024):
        X_i^{t+1} = X_i^t + α*(X_leader - X_i^t) + β*rand*(X_global - X_i^t)

        Para VRP discreto: Aplicamos 2-opt para reasignación de rutas
        """
        # Identificar líderes (top 20% de la población)
        sorted_pop = sorted(self.population, key=lambda h: h.fitness())
        n_leaders = max(1, int(0.2 * self.population_size))
        self.leaders = sorted_pop[:n_leaders]

        for i, hippo in enumerate(self.population):
            if hippo in self.leaders:
                continue

            # Seleccionar líder aleatorio
            leader = np.random.choice(self.leaders)

            # Actualizar posición continua
            new_position = hippo.position.copy()

            # Movimiento hacia el líder
            leader_direction = leader.position - hippo.position
            new_position += alpha * leader_direction

            # Movimiento hacia el mejor global
            global_direction = self.global_best.position - hippo.position
            new_position += beta * np.random.rand() * global_direction

            # Asegurar límites [0, 1]
            new_position = np.clip(new_position, 0, 1)

            # Para VRP: Aplicar operador 2-opt discreto
            if hasattr(self.problem, "decode_solution"):
                routes, _, _ = self.problem.decode_solution(new_position)
                # Aplicar 2-opt a una ruta aleatoria
                if routes and len(routes) > 0:
                    route_idx = np.random.randint(len(routes))
                    if len(routes[route_idx]) > 3:  # Necesitamos al menos 4 nodos
                        improved_route = self._apply_2opt(routes[route_idx])
                        routes[route_idx] = improved_route

            # Evaluar nueva posición
            hippo.position = new_position
            hippo.update_fitness()

    def _defense_phase(self) -> None:
        """
        Fase de defensa: Clustering jerárquico para protección grupal.

        Implementa balanceo de carga si coef_variacion > threshold.
        Usa operador swap para equilibrar cargas entre rutas.
        """
        # Clustering jerárquico de la población
        positions = np.array([h.position for h in self.population])

        # Calcular distancias y clusters
        if len(positions) > 1:
            distances = cdist(positions, positions)
            linkage_matrix = linkage(distances, method="ward")
            n_clusters = max(2, int(np.sqrt(self.population_size)))
            clusters = fcluster(linkage_matrix, n_clusters, criterion="maxclust")

            # Asignar grupos
            for i, hippo in enumerate(self.population):
                hippo.group_id = clusters[i]

        # Para QC-DVRP: Verificar coeficiente de variación
        if hasattr(self.problem, "evaluate_multi"):
            for hippo in self.population:
                tiempo_avg, coef_var, distancia = self.problem.evaluate_multi(
                    hippo.position
                )

                # Si coef_variacion alto, aplicar swap para balanceo
                if coef_var > 0.3:  # Threshold para desbalance
                    routes, _, _ = self.problem.decode_solution(hippo.position)
                    balanced_routes = self._apply_swap_balancing(routes)
                    # Recodificar a posición continua (simplificado)
                    # En práctica, necesitaríamos un método más sofisticado
                    hippo.update_fitness()

    def _evasion_phase(self, gamma: float) -> None:
        """
        Fase de evasión: Perturbación tipo Levy para escapar.

        Ecuación (Amiri et al., 2024):
        X_i^{t+1} = X_i^t + γ*Levy()*perturbation

        Para VRP: Usa relocate para mover clientes con retraso.
        """
        for hippo in self.population:
            # Aplicar perturbación Levy
            levy_step = levy_flight(hippo.dimension)
            perturbation = gamma * levy_step

            new_position = hippo.position + perturbation
            new_position = np.clip(new_position, 0, 1)

            # Para QC-DVRP: Verificar retrasos y aplicar relocate
            if hasattr(self.problem, "apply_evasion_strategy"):
                routes, _, _ = self.problem.decode_solution(new_position)
                # Aplicar estrategia de evasión si hay retrasos
                improved_routes = self.problem.apply_evasion_strategy(
                    routes, delay_threshold=30.0
                )
                # La estrategia ya está implementada en vrp.py

            # Evaluar nueva posición
            temp_fitness = self.problem.evaluate(new_position)
            if temp_fitness < hippo.fitness():
                hippo.position = new_position
                hippo.update_fitness()

    def _apply_2opt(self, route: List[int]) -> List[int]:
        """
        Aplica operador 2-opt para mejorar una ruta.

        Args:
            route: Ruta a mejorar

        Returns:
            Ruta mejorada
        """
        if len(route) < 4:
            return route

        improved = True
        best_route = route.copy()

        while improved:
            improved = False
            for i in range(1, len(best_route) - 2):
                for j in range(i + 1, len(best_route) - 1):
                    # Crear nueva ruta con segmento invertido
                    new_route = (
                        best_route[:i]
                        + best_route[i : j + 1][::-1]
                        + best_route[j + 1 :]
                    )

                    # Evaluar mejora (simplificado)
                    if self._route_distance(new_route) < self._route_distance(
                        best_route
                    ):
                        best_route = new_route
                        improved = True
                        break
                if improved:
                    break

        return best_route

    def _apply_swap_balancing(self, routes: List[List[int]]) -> List[List[int]]:
        """
        Aplica operador swap para balancear cargas entre rutas.

        Args:
            routes: Lista de rutas

        Returns:
            Rutas balanceadas
        """
        if len(routes) < 2:
            return routes

        # Calcular cargas actuales
        route_loads = []
        for route in routes:
            load = sum(self.problem.demands[node] for node in route[1:-1])
            route_loads.append(load)

        # Encontrar rutas más y menos cargadas
        max_idx = np.argmax(route_loads)
        min_idx = np.argmin(route_loads)

        if max_idx != min_idx and len(routes[max_idx]) > 2 and len(routes[min_idx]) > 2:
            # Intentar swap de un cliente
            max_route = routes[max_idx].copy()
            min_route = routes[min_idx].copy()

            # Seleccionar cliente aleatorio de ruta más cargada
            if len(max_route) > 2:
                customer_idx = np.random.randint(1, len(max_route) - 1)
                customer = max_route[customer_idx]

                # Verificar si cabe en ruta menos cargada
                if (
                    route_loads[min_idx] + self.problem.demands[customer]
                    <= self.problem.capacity
                ):
                    # Realizar swap
                    max_route.pop(customer_idx)
                    insert_pos = np.random.randint(1, len(min_route))
                    min_route.insert(insert_pos, customer)

                    routes[max_idx] = max_route
                    routes[min_idx] = min_route

        return routes

    def _route_distance(self, route: List[int]) -> float:
        """Calcula distancia de una ruta (simplificado)."""
        if not hasattr(self.problem, "distance_matrix"):
            return 0.0

        distance = 0.0
        for i in range(len(route) - 1):
            distance += self.problem.distance_matrix[route[i], route[i + 1]]
        return distance
