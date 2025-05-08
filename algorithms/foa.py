import numpy as np
import random
import math
from .base import Individual, MetaheuristicAlgorithm

class Fox(Individual):
    """Clase para representar un individuo en el algoritmo FOA."""
    
    def __init__(self, problem):
        """
        Inicializa un zorro con una posición aleatoria.
        
        Args:
            problem: Instancia del problema a resolver
        """
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None
        self.energy = 1.0  # Nivel de energía inicial
    
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
    
    def move(self, best, iteration, max_iterations):
        """
        Mueve el zorro según las reglas del algoritmo FOA.
        
        Args:
            best: Mejor zorro (líder)
            iteration: Iteración actual
            max_iterations: Número máximo de iteraciones
        """
        # Parámetros de control
        a = 2 * (1 - iteration / max_iterations)  # Decrece linealmente de 2 a 0
        
        # Actualizar nivel de energía
        self.energy = max(0.1, self.energy - 0.01)  # Decrece lentamente
        
        for i in range(self.dimension):
            r1 = random.random()
            r2 = random.random()
            r3 = random.random()
            
            # Comportamiento de caza
            if self.energy > 0.5:  # Alta energía: exploración activa
                if r3 < 0.33:  # Exploración aleatoria
                    self.position[i] = self.position[i] + a * (2 * r1 - 1)
                elif r3 < 0.66:  # Exploración dirigida
                    self.position[i] = best.position[i] + a * (2 * r2 - 1) * abs(best.position[i] - self.position[i])
                else:  # Salto aleatorio (simulando el salto del zorro para cazar)
                    self.position[i] = random.random()
            else:  # Baja energía: explotación y movimientos más conservadores
                if r1 < 0.5:  # Acercamiento cauteloso
                    self.position[i] = self.position[i] + 0.1 * a * r2 * (best.position[i] - self.position[i])
                else:  # Movimiento hacia la mejor posición conocida
                    self.position[i] = best.position[i] + 0.1 * a * (2 * r2 - 1)
            
            # Mantener la posición dentro de los límites [0, 1]
            self.position[i] = max(0, min(1, self.position[i]))
        
        # Invalidar el fitness ya que la posición ha cambiado
        self._fitness = None
        
        # Recuperar energía si encuentra una buena solución
        if self._fitness is not None and self.is_better_than(best):
            self.energy = min(1.0, self.energy + 0.2)
    
    def copy(self, other):
        """Copia los valores de otro individuo a este."""
        if isinstance(other, Fox):
            self.position = other.position.copy()
            self._fitness = other._fitness
            self.energy = other.energy

class FOA(MetaheuristicAlgorithm):
    """Implementación del algoritmo Fox Optimization Algorithm (FOA)."""
    
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        """
        Inicializa el algoritmo FOA.
        
        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
    
    def initialize_population(self):
        """Inicializa la población de zorros."""
        self.population = []
        
        for _ in range(self.population_size):
            fox = Fox(self.problem)
            self.population.append(fox)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        # Guardar la mejor solución
        self.best_solution = Fox(self.problem)
        self.best_solution.copy(self.population[0])
        
        # Inicializar curva de convergencia
        self.convergence_curve = [self.best_solution.fitness()]
    
    def update_population(self):
        """Actualiza la población en cada iteración."""
        iteration = len(self.convergence_curve)
        
        # Ordenar la población por fitness
        self.population.sort(key=lambda x: x.fitness())
        
        best_fox = self.population[0]
        
        # Implementar comportamiento territorial
        territory_radius = 0.1 * (1 - iteration / self.max_iterations)  # Radio territorial disminuye con el tiempo
        
        for i in range(self.population_size):
            # Mover cada zorro
            self.population[i].move(best_fox, iteration, self.max_iterations)
            
            # Comportamiento territorial: evitar estar demasiado cerca de otros zorros
            for j in range(self.population_size):
                if i != j:
                    # Calcular distancia entre zorros
                    distance = np.linalg.norm(self.population[i].position - self.population[j].position)
                    
                    # Si están demasiado cerca, el zorro más débil se aleja
                    if distance < territory_radius and self.population[i].fitness() > self.population[j].fitness():
                        for k in range(self.population[i].dimension):
                            # Alejarse en una dirección aleatoria
                            self.population[i].position[k] += territory_radius * (2 * random.random() - 1)
                            # Mantener dentro de límites
                            self.population[i].position[k] = max(0, min(1, self.population[i].position[k]))
                        
                        # Invalidar fitness
                        self.population[i]._fitness = None
                        break
        
        # Ordenar la población actualizada
        self.population.sort(key=lambda x: x.fitness())
        
        # Actualizar la mejor solución si es necesario
        if self.population[0].is_better_than(self.best_solution):
            self.best_solution.copy(self.population[0])
        
        # Actualizar curva de convergencia
        self.convergence_curve.append(self.best_solution.fitness())
