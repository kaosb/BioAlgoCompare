import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm

class EnhancedGorilla(Individual):
    """Clase para representar un individuo en el algoritmo EGTO."""
    
    def __init__(self, problem):
        """
        Inicializa un gorila con una posición aleatoria.
        
        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        # Para problemas VRP, los límites son [0,1]
        self.lower_bounds = np.zeros(self.dimension)
        self.upper_bounds = np.ones(self.dimension)
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        self.velocity = np.zeros(self.dimension)  # Vector de velocidad para el movimiento mejorado
    
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
    
    def move(self, best, iteration, max_iterations, w=0.7, c1=1.5, c2=1.5):
        """
        Movimiento del gorila según el algoritmo EGTO (versión con MPA).
        Args:
            best: Mejor solución encontrada (silverback)
            iteration: Iteración actual
            max_iterations: Número total de iteraciones
            w, c1, c2: Coeficientes heredados de la versión tipo PSO (opcional)
        """
        dim = self.dimension
        P = 0.5  # constante de balance
        C = (math.cos(2 * random.random()) + 1) * (1 - iteration / max_iterations)
        k = random.uniform(-1, 1)
        D = C * k
        z = 0.03

        r = random.random()

        # Fase de alta velocidad (exploración)
        if iteration < max_iterations / 3:
            # Movimiento Browniano (alta velocidad)
            RB = np.random.normal(0, 1, dim)
            S = D * np.random.rand(dim) * self.position
            delta = P * RB * S
            self.position = self.position + delta

        # Fase de baja velocidad (explotación con Lévy)
        else:
            RL = np.random.uniform(size=dim)
            E = np.tile(best.position, (dim, 1))  # Matriz E construida con el mejor
            S = RL * (RL * best.position - self.position)
            CF = 0.5  # Coeficiente de control
            delta = P * CF * S
            self.position = best.position + delta

        # Clip y reset fitness
        self.position = np.clip(self.position, self.lower_bounds, self.upper_bounds)
        self._fitness = None
    
    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        if isinstance(other, EnhancedGorilla):
            self.position = other.position.copy()
            self.velocity = other.velocity.copy()
            self._fitness = other._fitness

class EGTO(MetaheuristicAlgorithm):
    """Implementación del algoritmo Enhanced Gorilla Troops Optimization (EGTO)."""
    
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo EGTO.
        
        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
    
    def initialize_population(self):
        """Inicializa la población de gorilas."""
        self.population = []
        
        for _ in range(self.population_size):
            gorilla = EnhancedGorilla(self.problem)
            self.population.append(gorilla)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        # Guardar la mejor solución
        self.best_solution = EnhancedGorilla(self.problem)
        self.best_solution.copy(self.population[0])
        
        # Inicializar curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]
    
    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        best_gorilla = self.population[0]
        
        for i in range(self.population_size):
            # Mover cada gorila
            self.population[i].move(best_gorilla, iteration, self.max_iterations)
        
        # Ordenar la población actualizada
        self.population.sort(key=lambda x: x.fitness())
        
        # Actualizar la mejor solución si es necesario
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])
        
        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
