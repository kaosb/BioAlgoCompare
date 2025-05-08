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
        Mueve el gorila según las reglas del algoritmo EGTO.
        
        Args:
            best: Mejor gorila (líder)
            iteration: Iteración actual
            max_iterations: Número máximo de iteraciones
            w: Factor de inercia
            c1, c2: Coeficientes de aceleración
        """
        # Parámetros de control
        a = 2 * (1 - iteration / max_iterations)  # Decrece linealmente de 2 a 0
        
        for i in range(self.dimension):
            r1 = random.random()
            r2 = random.random()
            r3 = random.random()
            
            if r3 < 0.5:  # Exploración - Movimiento inspirado en PSO
                # Actualizar velocidad
                self.velocity[i] = w * self.velocity[i] + \
                                  c1 * r1 * (best.position[i] - self.position[i]) + \
                                  c2 * r2 * (best.position[i] - self.position[i])
                
                # Actualizar posición
                self.position[i] = self.position[i] + self.velocity[i]
            else:  # Explotación - Movimiento inspirado en GTO original
                if r1 < 0.5:
                    # Movimiento de exploración local
                    self.position[i] = best.position[i] + a * (2 * r2 - 1) * abs(best.position[i] - self.position[i])
                else:
                    # Movimiento de explotación
                    self.position[i] = self.position[i] + a * r2 * (best.position[i] - self.position[i])
            
            # Mantener la posición dentro de los límites [0, 1]
            self.position[i] = max(0, min(1, self.position[i]))
        
        # Invalidar el fitness ya que la posición ha cambiado
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
        self.w = 0.7  # Factor de inercia
        self.c1 = 1.5  # Coeficiente cognitivo
        self.c2 = 1.5  # Coeficiente social
    
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
        
        # Actualizar factor de inercia
        self.w = 0.9 - 0.5 * (iteration / self.max_iterations)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        best_gorilla = self.population[0]
        
        for i in range(self.population_size):
            # Mover cada gorila
            self.population[i].move(best_gorilla, iteration, self.max_iterations, self.w, self.c1, self.c2)
        
        # Ordenar la población actualizada
        self.population.sort(key=lambda x: x.fitness())
        
        # Actualizar la mejor solución si es necesario
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])
        
        # Implementar operador de cruce entre los mejores individuos
        if iteration % 10 == 0:  # Cada 10 iteraciones
            self._perform_crossover()
        
        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
    
    def _perform_crossover(self):
        """Realiza operaciones de cruce entre los mejores individuos."""
        elite_size = max(2, self.population_size // 5)  # 20% de la población
        
        for i in range(elite_size, self.population_size):
            # Seleccionar dos padres de la élite
            parent1_idx = random.randint(0, elite_size - 1)
            parent2_idx = random.randint(0, elite_size - 1)
            
            # Asegurar que son diferentes
            while parent2_idx == parent1_idx:
                parent2_idx = random.randint(0, elite_size - 1)
            
            parent1 = self.population[parent1_idx]
            parent2 = self.population[parent2_idx]
            
            # Cruce aritmético
            alpha = random.random()
            for j in range(self.problem.get_dimension()):
                self.population[i].position[j] = alpha * parent1.position[j] + (1 - alpha) * parent2.position[j]
            
            # Invalidar el fitness
            self.population[i]._fitness = None
