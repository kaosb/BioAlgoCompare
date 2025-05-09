import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm

class SlimeMould(Individual):
    """Clase para representar un individuo en el algoritmo SMA (Slime Mould Algorithm)."""
    
    def __init__(self, problem):
        """
        Inicializa un moho del limo con una posición aleatoria.
        
        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        self.weight = 0.0  # Peso para el movimiento
    
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
        return True  # En VRP todas las soluciones son factibles con nuestro decodificador
    
    def move(self, best_mould, weights, z=0.03, t=1, max_t=100):
        """
        Movimiento del moho del limo basado en el algoritmo SMA original.

        Args:
            best_mould: El mejor individuo encontrado hasta ahora.
            weights: Lista de pesos de la población.
            z: Probabilidad de exploración aleatoria.
            t: Iteración actual.
            max_t: Número total de iteraciones.
        """
        dim = self.dimension
        r = random.random()
        p = math.tanh(abs(self.fitness() - best_mould.fitness()))
        a = math.atanh(-t / max_t + 1)
        vb = np.random.uniform(-a, a, size=dim)
        vc = np.random.uniform(-1, 1, size=dim) * (1 - t / max_t)

        # Movimiento
        if random.random() < z:
            self.position = np.random.uniform(0, 1, size=dim)
        else:
            for i in range(dim):
                if r < p:
                    A = np.random.uniform(size=dim)
                    B = np.random.uniform(size=dim)
                    X_A = np.random.uniform(0, 1, size=dim)
                    X_B = np.random.uniform(0, 1, size=dim)
                    self.position[i] = best_mould.position[i] + vb[i] * weights[i] * (X_A[i] - X_B[i])
                else:
                    self.position[i] = vc[i] * self.position[i]

        # Clip en dominio [0,1]
        self.position = np.clip(self.position, 0, 1)
        self._fitness = None
    
    def copy(self, other):
        """
        Copia los valores de otro individuo a este.
        
        Args:
            other: Otro individuo (SlimeMould)
        """
        self.position = np.copy(other.position)
        self._fitness = other._fitness
        if hasattr(other, 'weight'):
            self.weight = other.weight


class SMA(MetaheuristicAlgorithm):
    """Implementación del algoritmo de optimización de moho del limo (Slime Mould Algorithm)."""
    
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo SMA.
        
        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        self.z = 0.03  # Parámetro de probabilidad para comportamiento aleatorio
        
    def initialize_population(self):
        """Inicializa la población de mohos."""
        self.population = []
        for _ in range(self.population_size):
            mould = SlimeMould(self.problem)
            self.population.append(mould)
        
        # Encontrar el mejor moho inicial
        self.best_solution = self.population[0]
        for i in range(1, self.population_size):
            if self.population[i].is_better_than(self.best_solution):
                self.best_solution = self.population[i]
                
        # Inicializar pesos
        self._update_weights()
    
    def _update_weights(self):
        """Actualiza los pesos de los mohos según su aptitud."""
        # Obtener todos los valores de fitness
        fitness_values = [m.fitness() for m in self.population]
        
        # Calcular valores normalizados (peor: 0, mejor: 1)
        if max(fitness_values) == min(fitness_values):
            normalized_fitness = [0.5 for _ in fitness_values]
        else:
            # Normalización para problemas de minimización
            normalized_fitness = [(max(fitness_values) - f) / (max(fitness_values) - min(fitness_values) + 1e-10) 
                                  for f in fitness_values]
        
        # Actualizar peso de cada moho
        for i, mould in enumerate(self.population):
            mould.weight = normalized_fitness[i]
    
    def update_population(self):
        """Actualiza la población en cada iteración."""
        # Actualizar pesos de los mohos según su aptitud actual
        self._update_weights()
        
        # La iteración actual es el tamaño de la curva de convergencia
        current_iter = len(self.convergence_curve)
        
        # Factor de volatilidad que disminuye con las iteraciones
        z = self.z - current_iter * (0.03 / self.max_iterations)
        
        # Obtener todos los pesos
        weights = [m.weight for m in self.population]
        
        # Actualizar cada moho
        for i in range(self.population_size):
            # No mover el mejor moho
            if self.population[i] is not self.best_solution:
                # Mover según el algoritmo SMA
                self.population[i].move(self.best_solution, weights, z, current_iter + 1, self.max_iterations)
                
                # Actualizar mejor solución si es necesario
                if self.population[i].is_better_than(self.best_solution):
                    mould_copy = SlimeMould(self.problem)
                    mould_copy.copy(self.population[i])
                    self.best_solution = mould_copy