import time
import random
import numpy as np
from abc import ABC, abstractmethod

class Individual(ABC):
    """Clase base para representar individuos en algoritmos metaheurísticos."""
    
    @abstractmethod
    def is_better_than(self, other):
        """Compara si este individuo es mejor que otro."""
        pass
    
    @abstractmethod
    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        pass
    
    @abstractmethod
    def move(self, best):
        """Mueve al individuo según las reglas del algoritmo."""
        pass
    
    @abstractmethod
    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        pass

class MetaheuristicAlgorithm(ABC):
    """Clase base para algoritmos metaheurísticos."""
    
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo metaheurístico.
        
        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        self.problem = problem
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.population = []
        self.best_solution = None
        self.start_time = 0
        self.end_time = 0
        self.convergence_curve = []
        
        # Establecer semilla para reproducibilidad
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    @abstractmethod
    def initialize_population(self):
        """Inicializa la población del algoritmo."""
        pass
    
    @abstractmethod
    def update_population(self):
        """Actualiza la población en cada iteración."""
        pass
    
    def execute(self):
        """Ejecuta el algoritmo completo."""
        self.start_time = time.time()
        self.initialize_population()
        
        for iteration in range(self.max_iterations):
            self.update_population()
            self.convergence_curve.append(self.best_solution.fitness())
            
        self.end_time = time.time()
        return self.best_solution
    
    def get_execution_time(self):
        """Retorna el tiempo de ejecución en segundos."""
        return self.end_time - self.start_time
    
    def get_convergence_curve(self):
        """Retorna la curva de convergencia."""
        return self.convergence_curve
