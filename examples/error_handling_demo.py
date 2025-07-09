#!/usr/bin/env python3
"""
Demostración del sistema de manejo robusto de errores.

Este ejemplo muestra cómo integrar el sistema de manejo de errores
en algoritmos existentes para hacerlos más robustos y confiables.
"""

import numpy as np
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from algorithms.genetic_algorithm_v2 import GeneticAlgorithmV2, GAIndividual
from algorithms.mixins import ErrorHandlingMixin, with_error_handling
from utils.error_handling import (
    create_safe_algorithm, validate_parameters,
    handle_errors, ParameterError
)
from problems.vrp_problem import VRPProblem


class RobustGAIndividual(GAIndividual):
    """Individuo GA con validación adicional."""
    
    def __init__(self, problem, position=None):
        """Inicializa con validación."""
        super().__init__(problem, position)
        
        # Validar posición
        if self.position is not None:
            if np.any(np.isnan(self.position)):
                raise ValueError("Position contains NaN values")
            if np.any(np.isinf(self.position)):
                raise ValueError("Position contains Inf values")


class RobustGeneticAlgorithm(ErrorHandlingMixin, GeneticAlgorithmV2):
    """
    Algoritmo Genético con manejo robusto de errores.
    
    Esta implementación añade:
    - Validación de parámetros
    - Recuperación automática de errores
    - Logging detallado de problemas
    - Fallbacks para operaciones críticas
    """
    
    @validate_parameters(
        population_size=lambda x: x > 0,
        max_iterations=lambda x: x > 0,
        crossover_rate=lambda x: 0 <= x <= 1,
        mutation_rate=lambda x: 0 <= x <= 1,
        elitism_size=lambda x: x >= 0
    )
    def __init__(self, problem, population_size=50, max_iterations=1000,
                 crossover_rate=0.8, mutation_rate=0.2, elitism_size=2,
                 seed=None, **kwargs):
        """
        Inicializa GA robusto con validación de parámetros.
        
        Args:
            problem: Instancia del problema VRP
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            crossover_rate: Probabilidad de cruce
            mutation_rate: Probabilidad de mutación
            elitism_size: Número de individuos elite
            seed: Semilla para reproducibilidad
            **kwargs: Argumentos adicionales para error handling
        """
        # Inicializar con manejo de errores
        super().__init__(problem, population_size, max_iterations,
                        crossover_rate, mutation_rate, elitism_size, seed)
        
        # Validar estado inicial
        self.validate_algorithm_state()
        
        print(f"RobustGA initialized with error handling enabled")
        print(f"  - Error tolerance: {self.error_tolerance}")
        print(f"  - Max consecutive errors: {self.max_consecutive_errors}")
        print(f"  - Recovery enabled: {self.enable_recovery}")
    
    def _create_individual(self):
        """Crea individuo con manejo de errores."""
        return self.safe_operation(
            lambda: RobustGAIndividual(self.problem),
            error_type='population'
        )
    
    @with_error_handling
    def initialize_population(self):
        """Inicializa población con validación."""
        self.population = []
        
        for i in range(self.population_size):
            individual = self._create_individual()
            
            if individual is None:
                # Fallback: crear individuo básico
                individual = GAIndividual(self.problem)
            
            self.population.append(individual)
        
        # Validar población completa
        self.validate_population()
        
        print(f"Population initialized successfully with {len(self.population)} individuals")
    
    @handle_errors(log_errors=True, reraise=False)
    def crossover(self, parent1, parent2):
        """Cruce con manejo de errores."""
        try:
            # Validar padres
            if parent1 is None or parent2 is None:
                raise ValueError("Invalid parents for crossover")
            
            # Ejecutar cruce
            return super().crossover(parent1, parent2)
            
        except Exception as e:
            # Fallback: retornar copias de los padres
            print(f"Crossover failed: {e}. Returning parent copies.")
            child1 = RobustGAIndividual(self.problem, parent1.position.copy())
            child2 = RobustGAIndividual(self.problem, parent2.position.copy())
            return child1, child2
    
    def mutate(self, individual):
        """Mutación con manejo de errores."""
        def mutation_operation():
            # Guardar posición original
            original_position = individual.position.copy()
            
            try:
                # Aplicar mutación
                super().mutate(individual)
                
                # Validar resultado
                if np.any(np.isnan(individual.position)):
                    raise ValueError("Mutation produced NaN values")
                
            except Exception as e:
                # Restaurar posición original
                individual.position = original_position
                print(f"Mutation failed: {e}. Position restored.")
        
        self.safe_operation(mutation_operation, error_type='general')
    
    def run(self):
        """Ejecuta el algoritmo con manejo robusto de errores."""
        print(f"\n{'='*60}")
        print(f"Robust Genetic Algorithm para {self.problem.name}")
        print(f"Población: {self.population_size}, Iteraciones: {self.max_iterations}")
        print(f"{'='*60}\n")
        
        # Inicializar población
        self.initialize_population()
        
        best_solution = None
        best_fitness = float('inf')
        iterations_without_improvement = 0
        
        for iteration in range(self.max_iterations):
            try:
                # Guardar iteración actual para logging
                self.current_iteration = iteration
                
                # Evaluar población con manejo de errores
                fitness_values = []
                for ind in self.population:
                    fitness = self.safe_fitness_evaluation(ind)
                    fitness_values.append(fitness)
                
                # Encontrar mejor solución
                min_idx = np.argmin(fitness_values)
                current_best_fitness = fitness_values[min_idx]
                
                # Actualizar mejor global
                if current_best_fitness < best_fitness:
                    best_fitness = current_best_fitness
                    best_solution = self.population[min_idx]
                    iterations_without_improvement = 0
                else:
                    iterations_without_improvement += 1
                
                # Verificar estancamiento
                if iterations_without_improvement > 50:
                    print(f"\nStagnation detected at iteration {iteration}")
                    if self.enable_recovery:
                        self._recover_convergence(None)
                        iterations_without_improvement = 0
                
                # Mostrar progreso
                if iteration % 50 == 0:
                    mean_fitness = np.mean([f for f in fitness_values if f != float('inf')])
                    print(f"Iter {iteration:4d}: Best = {best_fitness:.2f}, "
                          f"Mean = {mean_fitness:.2f}, "
                          f"Errors = {self.total_errors}")
                
                # Generar nueva población
                new_population = []
                
                # Preservar elite
                sorted_indices = np.argsort(fitness_values)
                for i in range(self.elitism_size):
                    if i < len(sorted_indices):
                        new_population.append(self.population[sorted_indices[i]])
                
                # Generar resto de la población
                while len(new_population) < self.population_size:
                    # Selección con manejo de errores
                    parent1 = self.safe_operation(
                        lambda: self.tournament_selection(self.population),
                        error_type='general'
                    )
                    parent2 = self.safe_operation(
                        lambda: self.tournament_selection(self.population),
                        error_type='general'
                    )
                    
                    # Validar selección
                    if parent1 is None or parent2 is None:
                        # Fallback: selección aleatoria
                        parent1 = np.random.choice(self.population)
                        parent2 = np.random.choice(self.population)
                    
                    # Cruce
                    if np.random.rand() < self.crossover_rate:
                        offspring = self.crossover(parent1, parent2)
                        if offspring:
                            child1, child2 = offspring
                        else:
                            child1, child2 = parent1, parent2
                    else:
                        child1, child2 = parent1, parent2
                    
                    # Mutación
                    for child in [child1, child2]:
                        if np.random.rand() < self.mutation_rate:
                            self.mutate(child)
                    
                    new_population.extend([child1, child2])
                
                # Actualizar población
                self.population = new_population[:self.population_size]
                
                # Validar nueva población periódicamente
                if iteration % 100 == 0:
                    try:
                        self.validate_population()
                    except Exception as e:
                        print(f"Population validation warning: {e}")
                
            except Exception as e:
                print(f"\nError in iteration {iteration}: {e}")
                
                # Verificar límite de errores consecutivos
                if self.consecutive_errors >= self.max_consecutive_errors:
                    print(f"\nToo many consecutive errors. Stopping algorithm.")
                    break
                
                # Intentar continuar con población actual
                continue
        
        # Resultados finales
        print(f"\n{'='*60}")
        print("Resultados finales:")
        
        if best_solution:
            print(f"Mejor fitness: {best_fitness:.2f}")
            
            # Mostrar rutas
            routes = best_solution.decode_routes()
            total_distance = 0
            
            print("\nRutas encontradas:")
            for i, route in enumerate(routes):
                route_distance = sum(
                    self.problem.distance_matrix[route[j]][route[j+1]]
                    for j in range(len(route) - 1)
                )
                total_distance += route_distance
                
                load = sum(self.problem.demands[c] for c in route[1:-1])
                print(f"  Ruta {i+1}: {' -> '.join(map(str, route))}")
                print(f"    Distancia: {route_distance:.2f}, Carga: {load}/{self.problem.capacity}")
        else:
            print("No se encontró solución válida")
        
        # Mostrar resumen de errores
        error_summary = self.get_error_summary()
        print(f"\nResumen de errores:")
        print(f"  - Total de errores: {error_summary['total_errors']}")
        print(f"  - Tipos de errores: {error_summary['error_types']}")
        print(f"  - Intentos de recuperación: {error_summary['recovery_attempts']}")
        
        return best_solution


def demonstrate_error_scenarios():
    """Demuestra diferentes escenarios de error y recuperación."""
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DE ESCENARIOS DE ERROR")
    print("="*60)
    
    # Cargar problema
    instance_path = "data/vrp/E-n22-k4.vrp"
    problem = VRPProblem(instance_path)
    
    # Escenario 1: Parámetros inválidos
    print("\n1. Intento con parámetros inválidos:")
    try:
        algo = RobustGeneticAlgorithm(
            problem,
            population_size=-10,  # Inválido
            max_iterations=100
        )
    except ParameterError as e:
        print(f"   ✓ Error capturado correctamente: {e}")
    
    # Escenario 2: Algoritmo con recuperación automática
    print("\n2. Algoritmo con recuperación automática:")
    algo = RobustGeneticAlgorithm(
        problem,
        population_size=20,
        max_iterations=100,
        max_consecutive_errors=10,
        enable_recovery=True,
        seed=42
    )
    
    # Simular algunos errores
    print("\n   Simulando errores numéricos...")
    
    # Corromper algunos individuos
    algo.initialize_population()
    if len(algo.population) > 2:
        algo.population[0].position[0] = np.nan
        algo.population[1].position[1] = np.inf
    
    # El algoritmo debería recuperarse automáticamente
    algo._recover_numeric(None)
    print("   ✓ Recuperación numérica exitosa")
    
    # Escenario 3: Usar wrapper seguro
    print("\n3. Usando SafeAlgorithmWrapper:")
    safe_algo = create_safe_algorithm(
        GeneticAlgorithmV2,
        problem=problem,
        population_size=10,
        max_iterations=50
    )
    
    result = safe_algo.run()
    if result:
        print("   ✓ Algoritmo ejecutado exitosamente con wrapper")
    else:
        print("   ✗ Algoritmo falló pero fue manejado de forma segura")


def main():
    """Función principal de demostración."""
    # Cargar problema
    instance_path = "data/vrp/E-n22-k4.vrp"
    
    try:
        problem = VRPProblem(instance_path)
    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo {instance_path}")
        print("Asegúrate de ejecutar desde el directorio raíz del proyecto")
        return
    
    print(f"\nProblem: {problem.name}")
    print(f"Customers: {problem.dimension - 1}")
    print(f"Vehicles: {problem.num_vehicles}")
    print(f"Capacity: {problem.capacity}")
    
    # Ejecutar algoritmo robusto
    algorithm = RobustGeneticAlgorithm(
        problem,
        population_size=30,
        max_iterations=200,
        crossover_rate=0.8,
        mutation_rate=0.2,
        elitism_size=3,
        max_consecutive_errors=10,
        enable_recovery=True,
        seed=42
    )
    
    best_solution = algorithm.run()
    
    # Demostrar escenarios de error
    demonstrate_error_scenarios()
    
    return algorithm, best_solution


if __name__ == "__main__":
    algorithm, solution = main()