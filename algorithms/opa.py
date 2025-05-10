import copy
import random
import numpy as np
import time
from algorithms.base import Individual, MetaheuristicAlgorithm

class Orca(Individual):
    """Una orca (solución VRP)."""

    def __init__(self, problem):
        self.problem = problem
        self.position = self.problem.random_solution()
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
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_feasible(self):
        return self.problem.is_valid(self.position)

    def update(self, g_best, phase: str, accept_prob: float):
        # Crear una nueva posición copiando la actual
        new_pos = copy.deepcopy(self.position)
        
        # Exploración o explotación dependiendo de la fase
        if phase == "chase":
            # FASE DE EXPLORACIÓN: swap aleatorio y pequeñas perturbaciones aleatorias
            if len(new_pos) >= 2:
                # Swap aleatorio de dos elementos
                i, j = random.sample(range(len(new_pos)), 2)
                new_pos[i], new_pos[j] = new_pos[j], new_pos[i]
                
                # Pequeñas perturbaciones aleatorias para algunos elementos
                num_perturb = random.randint(1, max(1, len(new_pos) // 4))
                for _ in range(num_perturb):
                    idx = random.randrange(len(new_pos))
                    # Pequeña perturbación aleatoria manteniendo el valor entre [0,1]
                    perturb = (random.random() - 0.5) * 0.2  # Perturbación de ±0.1
                    new_pos[idx] = max(0, min(1, new_pos[idx] + perturb))
        else:
            # FASE DE ATAQUE: mezcla ponderada con el líder (g_best)
            # Seleccionar aleatoriamente un porcentaje de genes del líder para copiar
            copy_ratio = random.uniform(0.1, 0.4)  # Copiar entre 10% y 40% de los genes
            num_copy = max(1, int(len(new_pos) * copy_ratio))
            
            indices_to_copy = random.sample(range(len(new_pos)), num_copy)
            for idx in indices_to_copy:
                # Copiar el valor del líder en esta posición
                new_pos[idx] = g_best[idx]
                
            # Además, hacemos una mezcla ponderada en algunos puntos
            if random.random() < 0.5:  # 50% de probabilidad de hacer mezcla
                blend_indices = [i for i in range(len(new_pos)) if i not in indices_to_copy]
                if blend_indices:
                    # Seleccionar un subconjunto para mezcla
                    blend_subset = random.sample(blend_indices, min(len(blend_indices), num_copy))
                    for idx in blend_subset:
                        # Mezcla ponderada entre la posición actual y la del líder
                        alpha = random.uniform(0.2, 0.8)
                        new_pos[idx] = alpha * new_pos[idx] + (1 - alpha) * g_best[idx]

        # Verificar si la nueva posición es válida
        if not self.problem.is_valid(new_pos):
            # Si no es válida, corregir restringiendo valores al rango [0,1]
            new_pos = np.clip(new_pos, 0, 1)

        # Evaluar la nueva posición y actualizar si mejora o con probabilidad de aceptación
        new_fit = self.problem.evaluate(new_pos)
        if new_fit < self.fitness() or random.random() < accept_prob:
            self.position = new_pos
            self._fitness = new_fit
            # Actualizar mejor posición personal si es necesario
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
        accept_prob = 0.3 * (1 - frac)
        leader_pos = self.best_solution.position

        for orca in self.population:
            phase = "chase" if frac < 0.5 else "attack"
            orca.update(leader_pos, phase, accept_prob)

        self.best_solution = min(self.population, key=lambda o: o.fitness()).copy()
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