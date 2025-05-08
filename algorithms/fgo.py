import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm

class Flamingo(Individual):
    """Clase para representar un individuo en el algoritmo FGO."""
    
    def __init__(self, problem):
        """
        Inicializa un flamenco con una posición aleatoria.
        
        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        self.personal_best_position = self.position.copy()
        self.personal_best_fitness = float('inf')
    
    def fitness(self):
        """Calcula el fitness del individuo."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
            
            # Actualizar mejor posición personal si es necesario
            if self._fitness < self.personal_best_fitness:
                self.personal_best_position = self.position.copy()
                self.personal_best_fitness = self._fitness
                
        return self._fitness
    
    def is_better_than(self, other):
        """Compara si este individuo es mejor que otro."""
        return self.fitness() < other.fitness()
    
    def is_feasible(self):
        """Verifica si el individuo representa una solución factible."""
        return True  # En VRP todas las soluciones son factibles con nuestro decodificador
    
    def move(self, best, iteration, max_iterations):
        """
        Mueve el flamenco según las reglas del algoritmo FGO.
        
        Args:
            best: Mejor flamenco (líder)
            iteration: Iteración actual
            max_iterations: Número máximo de iteraciones
        """
        # Parámetros de control
        a = 2 * (1 - iteration / max_iterations)  # Decrece linealmente de 2 a 0
        
        for i in range(self.dimension):
            r1 = random.random()
            r2 = random.random()
            r3 = random.random()
            
            # Comportamiento de filtración (inspirado en los flamencos filtrando comida)
            if r3 < 0.3:  # Exploración - Movimiento aleatorio
                self.position[i] = self.position[i] + a * (2 * r1 - 1)
            elif r3 < 0.6:  # Explotación local - Basado en la mejor posición personal
                self.position[i] = self.personal_best_position[i] + a * r1 * (best.position[i] - self.position[i])
            else:  # Explotación global - Seguir al líder
                # Movimiento en V (formación de vuelo de los flamencos)
                self.position[i] = best.position[i] + a * r2 * (best.position[i] - self.position[i])
                
                # Añadir componente de perturbación basado en la distancia al líder
                if random.random() < 0.2:  # 20% de probabilidad de perturbación
                    distance = abs(best.position[i] - self.position[i])
                    self.position[i] += (2 * random.random() - 1) * distance * 0.1
            
            # Mantener la posición dentro de los límites [0, 1]
            self.position[i] = max(0, min(1, self.position[i]))
        
        # Invalidar el fitness ya que la posición ha cambiado
        self._fitness = None
    
    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        if isinstance(other, Flamingo):
            self.position = other.position.copy()
            self._fitness = other._fitness
            self.personal_best_position = other.personal_best_position.copy()
            self.personal_best_fitness = other.personal_best_fitness

class FGO(MetaheuristicAlgorithm):
    """Implementación del algoritmo Flamingo Optimization Algorithm (FGO)."""
    
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo FGO.
        
        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
    
    def initialize_population(self):
        """Inicializa la población de flamencos."""
        self.population = []
        
        for _ in range(self.population_size):
            flamingo = Flamingo(self.problem)
            self.population.append(flamingo)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        # Guardar la mejor solución
        self.best_solution = Flamingo(self.problem)
        self.best_solution.copy(self.population[0])
        
        # Inicializar curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]
    
    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        best_flamingo = self.population[0]
        
        # Dividir la población en subgrupos (simulando bandadas de flamencos)
        num_groups = 3
        group_size = self.population_size // num_groups
        
        for g in range(num_groups):
            start_idx = g * group_size
            end_idx = (g + 1) * group_size if g < num_groups - 1 else self.population_size
            
            # Identificar el líder del grupo (el mejor del grupo)
            group = self.population[start_idx:end_idx]
            group.sort(key=lambda x: x.fitness())
            group_leader = group[0]
            
            # Mover cada flamenco en el grupo
            for i in range(start_idx, end_idx):
                # Los flamencos siguen a su líder de grupo y también al líder global
                if random.random() < 0.5:
                    self.population[i].move(group_leader, iteration, self.max_iterations)
                else:
                    self.population[i].move(best_flamingo, iteration, self.max_iterations)
        
        # Ordenar la población actualizada
        self.population.sort(key=lambda x: x.fitness())
        
        # Actualizar la mejor solución si es necesario
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])
        
        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
