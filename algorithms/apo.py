import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm

class Piranha(Individual):
    """Clase para representar un individuo en el algoritmo APO."""
    
    def __init__(self, problem):
        """
        Inicializa una piraña con una posición aleatoria.
        
        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        self.hunger = random.random()  # Nivel de hambre inicial
    
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
    
    def move(self, best, worst, iteration, max_iterations):
        """
        Mueve la piraña según las reglas del algoritmo APO.
        
        Args:
            best: Mejor piraña (líder)
            worst: Peor piraña
            iteration: Iteración actual
            max_iterations: Número máximo de iteraciones
        """
        # Parámetros de control
        a = 2 * (1 - iteration / max_iterations)  # Decrece linealmente de 2 a 0
        
        for i in range(self.dimension):
            r1 = random.random()
            r2 = random.random()
            r3 = random.random()
            
            # Comportamiento de caza
            if r3 < 0.5:  # Exploración
                if r1 < 0.5:
                    # Movimiento aleatorio
                    self.position[i] = self.position[i] + a * (2 * r2 - 1)
                else:
                    # Movimiento basado en la mejor solución
                    self.position[i] = best.position[i] + a * (2 * r2 - 1) * abs(best.position[i] - self.position[i])
            else:  # Explotación
                # Ataque a la presa (mejor solución)
                self.position[i] = best.position[i] + a * r2 * (best.position[i] - worst.position[i])
            
            # Actualizar nivel de hambre
            self.hunger = self.hunger * 0.95 + 0.05 * random.random()
            
            # Comportamiento de canibalismo (si está muy hambriento)
            if self.hunger > 0.8:
                self.position[i] = self.position[i] + 0.1 * (2 * random.random() - 1)
            
            # Mantener la posición dentro de los límites [0, 1]
            self.position[i] = max(0, min(1, self.position[i]))
        
        # Invalidar el fitness ya que la posición ha cambiado
        self._fitness = None
    
    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        if isinstance(other, Piranha):
            self.position = other.position.copy()
            self._fitness = other._fitness
            self.hunger = other.hunger

class APO(MetaheuristicAlgorithm):
    """Implementación del algoritmo Artificial Piranha Optimization (APO)."""
    
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo APO.
        
        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
    
    def initialize_population(self):
        """Inicializa la población de pirañas."""
        self.population = []
        
        for _ in range(self.population_size):
            piranha = Piranha(self.problem)
            self.population.append(piranha)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        # Guardar la mejor solución
        self.best_solution = Piranha(self.problem)
        self.best_solution.copy(self.population[0])
        
        # Inicializar curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]
    
    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        best_piranha = self.population[0]
        worst_piranha = self.population[-1]
        
        for i in range(self.population_size):
            # Mover cada piraña
            self.population[i].move(best_piranha, worst_piranha, iteration, self.max_iterations)
        
        # Ordenar la población actualizada
        self.population.sort(key=lambda x: x.fitness())
        
        # Actualizar la mejor solución si es necesario
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])
        
        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
