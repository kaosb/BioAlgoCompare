import copy
import random
import numpy as np
import time
from algorithms.base import Individual, MetaheuristicAlgorithm

# ---------------------------------------------------------------------------
# util para convertir cualquier representación 1‑D (np.ndarray o lista plana)
# a la codificación de rutas [[clientes...]]
def _ensure_routes(solution):
    """
    Convierte una solución devuelta por `problem.random_solution()` a formato
    List[List[int]] requerido por los operadores discretos.  Maneja:
      • np.ndarray -> [[1, 2, ...]] (convertimos valores float a índices)
      • lista plana -> [[1, 2, ...]] (convertimos valores float a índices)
      • lista de rutas (ya correcto) -> se devuelve igual
    """
    if isinstance(solution, np.ndarray):
        # Para representación VRP: convertir a índices de 1..n en lugar de valores
        indices = list(range(1, len(solution) + 1))
        indices.sort(key=lambda i: solution[i-1])
        return [indices]
    elif solution and isinstance(solution[0], (float, int, np.integer, np.floating)):
        indices = list(range(1, len(solution) + 1))
        indices.sort(key=lambda i: solution[i-1] if i-1 < len(solution) else 0)
        return [indices]
    return solution

class Orca(Individual):
    """Una orca (solución VRP)."""

    def __init__(self, problem):
        self.problem = problem
        self.position = _ensure_routes(self.problem.random_solution())
        self._fitness = None
        self.velocity = None  # Se omite para implementación continua
        self.personal_best_position = copy.deepcopy(self.position)
        self.personal_best_fitness = self.fitness()

    def copy(self):
        return copy.deepcopy(self)
        
    def is_better_than(self, other):
        return self.fitness() < other.fitness()
        
    def move(self, population, iteration, max_iterations):
        # No se usa directamente, se usa update en su lugar
        pass

    def fitness(self):
        if self._fitness is None:
            # Si la posición es una lista de rutas, convertirla a un vector para evaluate
            if isinstance(self.position, list) and len(self.position) > 0 and isinstance(self.position[0], list):
                # Forma inversa de _ensure_routes: convertir rutas a un array para evaluate
                # Crear un array aleatorio
                dim = self.problem.get_dimension()
                vector = np.random.rand(dim)

                # Las rutas contienen índices de nodos ordenados por prioridad
                # Asignar valores crecientes a los nodos según su posición en las rutas
                all_nodes = []
                for route in self.position:
                    for node in route:
                        if node != 0 and node not in all_nodes:  # Excluir depósito
                            all_nodes.append(node)

                # Asignar valores crecientes para mantener el orden deseado
                for i, node in enumerate(all_nodes):
                    if 1 <= node <= dim:  # Verificar que el índice esté en rango
                        vector[node-1] = i / (len(all_nodes) + 1)  # Valores entre 0 y 1

                self._fitness = self.problem.evaluate(vector)
            else:
                self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        # Si la posición es una lista de rutas, convertirla a un vector para is_valid
        if isinstance(self.position, list) and len(self.position) > 0 and isinstance(self.position[0], list):
            # Convertir de manera similar a fitness()
            dim = self.problem.get_dimension()
            vector = np.random.rand(dim)

            all_nodes = []
            for route in self.position:
                for node in route:
                    if node != 0 and node not in all_nodes:  # Excluir depósito
                        all_nodes.append(node)

            for i, node in enumerate(all_nodes):
                if 1 <= node <= dim:  # Verificar que el índice esté en rango
                    vector[node-1] = i / (len(all_nodes) + 1)

            return self.problem.is_valid(vector)
        else:
            return self.problem.is_valid(self.position)

    # --- util operators --------------------------------------------------
    def _random_swap(self, routes):
        """Intercambia dos clientes aleatorios entre dos rutas distintas."""
        non_empty = [r for r in routes if len(r) > 0]
        if len(non_empty) < 2:
            return
        r1, r2 = random.sample(non_empty, 2)
        i = random.randrange(len(r1))
        j = random.randrange(len(r2))
        r1[i], r2[j] = r2[j], r1[i]

    def _two_opt(self, route):
        """Aplica 2‑opt a una sola ruta."""
        if len(route) < 4:
            return
        i, k = sorted(random.sample(range(len(route)), 2))
        route[i:k+1] = list(reversed(route[i:k+1]))

    def _relocate(self, routes, leader_routes):
        """
        Mueve un cliente desde una ruta aleatoria a una posición de la mejor ruta
        (o, si esta no tiene rutas no vacías, a cualquier otra ruta no vacía).
        Si todas las rutas quedan vacías tras la operación se crea una nueva ruta.
        """
        # elegir ruta fuente con al menos 1 cliente
        src_candidates = [r for r in routes if len(r) > 0]
        if not src_candidates:
            return  # nada que mover
        src = random.choice(src_candidates)
        idx = random.randrange(len(src))
        cust = src.pop(idx)

        # si la ruta fuente quedó vacía, elimínala para no tener rutas vacías
        if len(src) == 0:
            routes.remove(src)

        # destino: preferir rutas no vacías del líder
        dst_candidates = [r for r in leader_routes if len(r) > 0]
        if not dst_candidates:
            dst_candidates = [r for r in routes if len(r) > 0]

        # si aún no hay candidatas, crea una nueva ruta con el cliente movido
        if not dst_candidates:
            routes.append([cust])
            return

        dst = random.choice(dst_candidates)
        insert_pos = random.randrange(len(dst) + 1)
        dst.insert(insert_pos, cust)

    def update(self, g_best, phase: str, accept_prob: float):
        # Crear una nueva posición copiando la actual
        new_pos = _ensure_routes(copy.deepcopy(self.position))

        # Exploración o explotación dependiendo de la fase
        if phase == "chase":
            self._random_swap(new_pos)
            candidates_2opt = [r for r in new_pos if len(r) >= 4]
            if candidates_2opt:
                route_for_2opt = random.choice(candidates_2opt)
                self._two_opt(route_for_2opt)
        else:
            self._relocate(new_pos, g_best)

        # Para verificar validez y evaluar, necesitamos convertir a formato array para el problema
        if hasattr(self.problem, "repair"):
            new_pos = self.problem.repair(new_pos)

        # Verificar si la solución es factible
        is_valid = True

        # Evaluación especial para OPA que trabaja con rutas
        # Convertir rutas a array para evaluate()
        dim = self.problem.get_dimension()
        vector = np.random.rand(dim)

        all_nodes = []
        for route in new_pos:
            for node in route:
                if node != 0 and node not in all_nodes:  # Excluir depósito
                    all_nodes.append(node)

        for i, node in enumerate(all_nodes):
            if 1 <= node <= dim:
                vector[node-1] = i / (len(all_nodes) + 1)

        # Evaluar con el vector convertido
        is_valid = self.problem.is_valid(vector)
        if not is_valid:
            return

        new_fit = self.problem.evaluate(vector)

        if new_fit < self.fitness() or random.random() < accept_prob:
            self.position = _ensure_routes(new_pos)
            self._fitness = new_fit
            if new_fit < self.personal_best_fitness:
                self.personal_best_position = copy.deepcopy(new_pos)
                self.personal_best_fitness = new_fit


class OPA(MetaheuristicAlgorithm):
    """
    Orca Predator Algorithm (OPA) – Adaptado al problema de ruteo de vehículos (VRP)
    Inspirado en: Jiang et al. (2021)
    """

    def __init__(self, problem, population_size=40, max_iterations=1000, seed=None):
        self.problem = problem
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.seed = seed
        self.current_iter = 0
        self.population = []
        self.best_solution = None
        self.start_time = 0
        self.end_time = 0
        self.convergence_curve = []

    def initialize_population(self) -> None:
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)
        self.population = [Orca(self.problem) for _ in range(self.population_size)]
        self.best_solution = min(self.population, key=lambda o: o.fitness()).copy()
        self.convergence_curve = [self.best_solution.fitness()]
        self.current_iter = 0

    def update_population(self) -> None:
        frac = self.current_iter / self.max_iterations
        leader_pos = copy.deepcopy(self.best_solution.position)

        accept_prob = 0.3 * (1 - frac)

        for orca in self.population:
            phase = "chase" if frac < 0.5 else "attack"
            orca.update(leader_pos, phase, accept_prob)

        self.best_solution = min(self.population, key=lambda o: o.fitness()).copy()
        previous_best = self.convergence_curve[-1]
        current_best = self.best_solution.fitness()
        self.convergence_curve.append(min(previous_best, current_best))
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