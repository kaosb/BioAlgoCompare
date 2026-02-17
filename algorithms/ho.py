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
import os
from typing import List, Tuple, Optional
from algorithms.base import Individual, MetaheuristicAlgorithm
from scipy.spatial.distance import cdist
from scipy.cluster.hierarchy import linkage, fcluster
from utils.math_functions import levy_flight


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

    def __init__(self, problem, rng=None):
        """Inicializa un hipopótamo con posición aleatoria.

        Args:
            problem: Instancia del problema a resolver
            rng: NumPy random generator instance
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.rng = rng if rng is not None else np.random.default_rng()
        self.position = self.rng.uniform(0, 1, self.dimension)
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
            return bool(self.problem.is_valid(self.position))
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
        use_il: bool = False,
        il_model_path: str = None,
        alpha_fixed: float = None,
        beta_fixed: float = None,
        gamma_fixed: float = None,
    ):
        """
        Inicializa el algoritmo HO.

        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
            use_il: Si usar Imitation Learning para parámetros dinámicos
            il_model_path: Ruta al modelo IL entrenado
            alpha_fixed: Valor fijo de alpha (None = adaptativo)
            beta_fixed: Valor fijo de beta (None = adaptativo)
            gamma_fixed: Valor fijo de gamma (None = adaptativo)
        """
        super().__init__(problem, population_size, max_iterations, seed)

        # Fixed parameters (for paper experiments)
        self.alpha_fixed = alpha_fixed
        self.beta_fixed = beta_fixed
        self.gamma_fixed = gamma_fixed

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

        # Imitation Learning
        self.use_il = use_il
        self.il_model = None
        if use_il:
            # Try sklearn-based IL first (to avoid PyTorch issues)
            try:
                from utils.train_il_simple import SimpleILModel
                from pathlib import Path
                
                # Check for sklearn model first
                sklearn_model_path = "models/ho_il_model.pkl"
                if Path(sklearn_model_path).exists():
                    self.il_model = SimpleILModel()
                    self.il_model.load(sklearn_model_path)
                    print(f"✅ Modelo IL (sklearn) cargado desde {sklearn_model_path}")
                elif il_model_path and os.path.exists(il_model_path):
                    # Fallback to PyTorch model if specified
                    from utils.imitation_learning import HOImitationLearning
                    self.il_model = HOImitationLearning()
                    self.il_model.load(il_model_path)
                    print(f"Modelo IL (PyTorch) cargado desde {il_model_path}")
                else:
                    print("⚠️ IL habilitado pero sin modelo entrenado")
                    self.use_il = False
            except ImportError as e:
                print(f"⚠️ No se pudo importar módulo IL: {e}")
                self.use_il = False

    def initialize_population(self) -> None:
        """Inicializa la población de hipopótamos."""
        self.population = []

        for _ in range(self.population_size):
            hippo = Hippopotamus(self.problem, rng=self.rng)
            self.population.append(hippo)

            # Actualizar mejor global
            if self.global_best is None or hippo.fitness() < self.global_best.fitness():
                self.global_best = object.__new__(Hippopotamus)
                self.global_best.problem = self.problem
                self.global_best.dimension = hippo.dimension
                self.global_best.rng = self.rng
                self.global_best.copy(hippo)

        self.best_solution = self.global_best
        self.convergence_curve = [self.global_best.fitness()]

    def update_population(self) -> None:
        """
        Actualiza la población usando las tres fases del algoritmo HO.

        Fases según Amiri et al. (2024):
        1. Fase de posición (Position phase)
        2. Fase de defensa (Defense phase)
        3. Fase de evasión (Predation phase)

        Si IL está habilitado, usa el modelo para predecir parámetros óptimos.
        """
        iteration = len(self.convergence_curve)
        progress = iteration / self.max_iterations

        # Si IL está habilitado, usar modelo para predecir parámetros
        if self.use_il and self.il_model is not None:
            try:
                # Create state for IL model
                if hasattr(self.il_model, 'predict'):  # sklearn model
                    # Use simplified state creation
                    from utils.test_il_integration import create_state_dict
                    state = create_state_dict(
                        self.problem, iteration, self.max_iterations, 
                        self.convergence_curve
                    )
                    alpha, beta, gamma = self.il_model.predict(state)
                else:  # PyTorch model
                    from utils.imitation_learning import create_state_from_problem
                    state = create_state_from_problem(
                        self.problem, self, iteration, self.max_iterations
                    )
                    alpha, beta, gamma = self.il_model.predict(state)
            except Exception as e:
                # Fallback a parámetros adaptativos estándar
                if iteration == 0:  # Only print once
                    print(f"⚠️ IL fallback to standard params: {e}")
                alpha = self.alpha_max - (self.alpha_max - self.alpha_min) * progress
                beta = self.beta_max - (self.beta_max - self.beta_min) * progress
                gamma = self.gamma_min + (self.gamma_max - self.gamma_min) * progress
        else:
            # Use fixed parameters if provided, otherwise adaptive
            if self.alpha_fixed is not None:
                alpha = self.alpha_fixed
            else:
                alpha = self.alpha_max - (self.alpha_max - self.alpha_min) * progress

            if self.beta_fixed is not None:
                beta = self.beta_fixed
            else:
                beta = self.beta_max - (self.beta_max - self.beta_min) * progress

            if self.gamma_fixed is not None:
                gamma = self.gamma_fixed
            else:
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
            leader = self.py_rng.choice(self.leaders)

            # Actualizar posición continua
            new_position = hippo.position.copy()

            # Movimiento hacia el líder
            leader_direction = leader.position - hippo.position
            new_position += alpha * leader_direction

            # Movimiento hacia el mejor global
            global_direction = self.global_best.position - hippo.position
            new_position += beta * self.rng.random() * global_direction

            # Asegurar límites [0, 1]
            new_position = np.clip(new_position, 0, 1)

            # Para VRP: Aplicar operador 2-opt discreto
            if hasattr(self.problem, "decode_solution"):
                routes, _, _ = self.problem.decode_solution(new_position)
                # Aplicar 2-opt a una ruta aleatoria
                if routes and len(routes) > 0:
                    route_idx = self.rng.integers(len(routes))
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
            # linkage espera una matriz de distancias condensada
            from scipy.spatial.distance import pdist
            distances_condensed = pdist(positions)
            linkage_matrix = linkage(distances_condensed, method="ward")
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

                # Si coef_variación alto, aplicar balanceo de rutas
                if coef_var > 0.3:  # Threshold para desbalance
                    routes, _, _ = self.problem.decode_solution(hippo.position)
                    balanced_routes = self._apply_swap_balancing(routes)
                    # Recodificar rutas balanceadas a posición continua
                    if hasattr(self.problem, 'encode_routes'):
                        hippo.position = self.problem.encode_routes(balanced_routes)
                    hippo.fitness_value = self.problem.evaluate_routes(balanced_routes)
                else:
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
            levy_step = levy_flight(hippo.dimension, rng=self.rng)
            perturbation = gamma * levy_step

            new_position = hippo.position + perturbation
            new_position = np.clip(new_position, 0, 1)

            # Para QC-DVRP: La estrategia de evasión se aplica durante la evaluación
            # No se modifica la posición aquí para mantener la integridad del espacio de búsqueda

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


    def _route_distance(self, route: List[int]) -> float:
        """Calcula distancia de una ruta (simplificado)."""
        if not hasattr(self.problem, "distance_matrix"):
            return 0.0

        distance = 0.0
        for i in range(len(route) - 1):
            distance += self.problem.distance_matrix[route[i], route[i + 1]]
        return distance

    def _apply_swap_balancing(self, routes: List[List[int]]) -> List[List[int]]:
        """
        Aplica operador swap para balancear cargas entre rutas.
        
        Implementa la estrategia de defensa grupal del HO mediante
        intercambio de clientes entre rutas desbalanceadas.
        
        Args:
            routes: Lista de rutas actuales
            
        Returns:
            Rutas balanceadas
        """
        if len(routes) < 2:
            return routes
            
        # Calcular cargas actuales
        route_loads = []
        for route in routes:
            load = sum(self.problem.demands[n] for n in route[1:-1])
            route_loads.append(load)
        
        # Identificar rutas más y menos cargadas
        max_load_idx = np.argmax(route_loads)
        min_load_idx = np.argmin(route_loads)
        
        if max_load_idx == min_load_idx:
            return routes
            
        # Copiar rutas para no modificar las originales
        balanced_routes = [route[:] for route in routes]
        
        # Intentar intercambiar clientes
        max_route = balanced_routes[max_load_idx]
        min_route = balanced_routes[min_load_idx]
        
        best_swap = None
        best_improvement = 0
        
        # Buscar mejor intercambio
        for i, customer1 in enumerate(max_route[1:-1], 1):
            for j, customer2 in enumerate(min_route[1:-1], 1):
                # Verificar factibilidad del intercambio
                new_max_load = route_loads[max_load_idx] - self.problem.demands[customer1] + self.problem.demands[customer2]
                new_min_load = route_loads[min_load_idx] - self.problem.demands[customer2] + self.problem.demands[customer1]
                
                if new_max_load <= self.problem.capacity and new_min_load <= self.problem.capacity:
                    # Calcular mejora en balance (reducción en diferencia de cargas)
                    old_diff = abs(route_loads[max_load_idx] - route_loads[min_load_idx])
                    new_diff = abs(new_max_load - new_min_load)
                    improvement = old_diff - new_diff
                    
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_swap = (i, j, customer1, customer2)
        
        # Aplicar mejor intercambio si existe
        if best_swap:
            i, j, customer1, customer2 = best_swap
            balanced_routes[max_load_idx][i] = customer2
            balanced_routes[min_load_idx][j] = customer1
        
        return balanced_routes
