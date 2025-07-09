#!/usr/bin/env python3
"""
Demostración de integración de mixins con algoritmos V2.

Este ejemplo muestra cómo usar los mixins para simplificar
y mejorar la implementación de algoritmos metaheurísticos.
"""

import numpy as np
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from algorithms.genetic_algorithm_v2 import GeneticAlgorithmV2, GAIndividual
from algorithms.mixins import (
    VRPCrossoverMixin,
    VRPMutationMixin,
    VRPLocalSearchMixin,
    TournamentSelectionMixin,
    ElitismMixin,
    ConvergenceTrackingMixin,
    AdaptiveParameterMixin,
    StagnationDetectionMixin,
    RestartMixin,
    NearestNeighborInitializationMixin
)
from problems.vrp_problem import VRPProblem


class EnhancedGAIndividual(GAIndividual):
    """Individuo GA mejorado con operadores de búsqueda local."""
    
    def __init__(self, problem, position=None):
        super().__init__(problem, position)
        self._local_search_applied = False
    
    def apply_local_search(self, local_search_fn):
        """Aplica búsqueda local a las rutas."""
        if self._local_search_applied:
            return
        
        routes = self.decode_routes()
        improved_routes = []
        
        for route in routes:
            if len(route) > 3:  # Solo aplicar si hay al menos 2 clientes
                improved_route = local_search_fn(route)
                improved_routes.append(improved_route)
            else:
                improved_routes.append(route)
        
        # Reconstruir posición desde rutas mejoradas
        self._reconstruct_position_from_routes(improved_routes)
        self._local_search_applied = True
    
    def _reconstruct_position_from_routes(self, routes):
        """Reconstruye la posición desde rutas."""
        # Extraer secuencia de clientes
        sequence = []
        for route in routes:
            sequence.extend(route[1:-1])  # Excluir depots
        
        # Crear nueva posición manteniendo el orden
        new_position = np.zeros_like(self.position)
        for i, customer in enumerate(sequence):
            new_position[customer - 1] = i / len(sequence)
        
        self.position = new_position


class EnhancedGeneticAlgorithm(
    VRPCrossoverMixin,
    VRPMutationMixin,
    VRPLocalSearchMixin,
    TournamentSelectionMixin,
    ElitismMixin,
    ConvergenceTrackingMixin,
    AdaptiveParameterMixin,
    StagnationDetectionMixin,
    RestartMixin,
    NearestNeighborInitializationMixin,
    GeneticAlgorithmV2
):
    """
    Algoritmo Genético mejorado usando mixins.
    
    Esta implementación combina:
    - Operadores VRP especializados
    - Selección por torneo y elitismo
    - Tracking de convergencia
    - Parámetros adaptativos
    - Detección de estancamiento y reinicio
    - Inicialización inteligente
    """
    
    def __init__(self, problem, population_size=50, max_iterations=1000,
                 crossover_rate=0.8, mutation_rate=0.2, elitism_size=2,
                 tournament_size=3, local_search_rate=0.1, seed=None):
        """
        Inicializa el algoritmo genético mejorado.
        
        Args:
            problem: Instancia del problema VRP
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            crossover_rate: Probabilidad de cruce
            mutation_rate: Probabilidad de mutación inicial
            elitism_size: Número de individuos elite
            tournament_size: Tamaño del torneo
            local_search_rate: Probabilidad de aplicar búsqueda local
            seed: Semilla para reproducibilidad
        """
        # Inicializar clase base
        super().__init__(problem, population_size, max_iterations, 
                        crossover_rate, mutation_rate, elitism_size, seed)
        
        self.tournament_size = tournament_size
        self.local_search_rate = local_search_rate
        
        # Configurar parámetros adaptativos
        self.register_adaptive_parameter(
            'mutation_rate', mutation_rate, 0.01, 0.5,
            self.performance_based_rule(1.05, 0.95, 'improvement')
        )
        
        # Configurar detección de estancamiento
        self.configure_stagnation_detection(window=20, threshold=0.001)
        
        # Configurar reinicio
        self.configure_restart(enabled=True, threshold=50, 
                             strategy='adaptive', preserve_elite=2)
    
    def _create_individual(self):
        """Crea un individuo usando inicialización inteligente."""
        if np.random.rand() < 0.3 and hasattr(self, 'best_solution'):
            # 30% de probabilidad de usar vecino más cercano
            routes = self.nearest_neighbor_solution(
                self.problem.distance_matrix,
                self.problem.capacity,
                self.problem.demands,
                start_customer=np.random.randint(1, len(self.problem.demands))
            )
            
            # Convertir rutas a posición
            position = self._routes_to_position(routes)
            return EnhancedGAIndividual(self.problem, position)
        else:
            # Inicialización aleatoria
            return EnhancedGAIndividual(self.problem)
    
    def _routes_to_position(self, routes):
        """Convierte rutas a representación de posición."""
        n_customers = len(self.problem.demands) - 1
        position = np.zeros(n_customers)
        
        # Asignar valores basados en el orden de visita
        order = 0
        for route in routes:
            for customer in route[1:-1]:  # Excluir depots
                position[customer - 1] = order / n_customers
                order += 1
        
        return position
    
    def run(self):
        """Ejecuta el algoritmo con mejoras."""
        print(f"\n{'='*60}")
        print(f"Enhanced Genetic Algorithm para {self.problem.name}")
        print(f"Población: {self.population_size}, Iteraciones: {self.max_iterations}")
        print(f"{'='*60}\n")
        
        # Inicializar población
        self.initialize_population()
        best_fitness = float('inf')
        
        for iteration in range(self.max_iterations):
            # Evaluar población
            fitness_values = [ind.fitness() for ind in self.population]
            current_best = min(fitness_values)
            
            # Tracking de convergencia
            self.track_iteration(self.population, iteration, iteration * 0.01)
            
            # Verificar mejora
            improved = current_best < best_fitness
            if improved:
                best_fitness = current_best
                self.best_solution = self.population[fitness_values.index(current_best)]
            
            # Actualizar parámetros adaptativos
            metrics = {'improvement': 1.0 if improved else 0.0}
            self.update_adaptive_parameters(iteration, self.max_iterations, metrics)
            
            # Verificar estancamiento
            diversity = self.population_diversity(self.population)
            stagnation = self.check_stagnation(current_best, diversity)
            
            # Aplicar reinicio si es necesario
            stagnation_count = self.get_stagnation_counter()
            if self.check_restart_condition(stagnation_count, stagnation):
                print(f"\nReinicio en iteración {iteration} (estancamiento: {stagnation_count} iter)")
                self.population = self.perform_restart(self.population, iteration)
                continue
            
            # Mostrar progreso
            if iteration % 50 == 0:
                mutation_rate = self.get_adaptive_parameter('mutation_rate')
                print(f"Iter {iteration:4d}: Best = {best_fitness:.2f}, "
                      f"Mean = {np.mean(fitness_values):.2f}, "
                      f"Diversity = {diversity:.3f}, "
                      f"Mutation = {mutation_rate:.3f}")
            
            # Selección y reproducción
            new_population = []
            
            # Preservar elite
            elite = self.select_elite(self.population, self.elitism_size)
            new_population.extend(elite)
            
            # Generar nueva población
            while len(new_population) < self.population_size:
                # Selección por torneo
                parent1 = self.tournament_selection(
                    self.population, self.tournament_size, 1)[0]
                parent2 = self.tournament_selection(
                    self.population, self.tournament_size, 1)[0]
                
                # Cruce
                if np.random.rand() < self.crossover_rate:
                    # Usar order crossover para VRP
                    perm1 = parent1.decode_routes_to_permutation()
                    perm2 = parent2.decode_routes_to_permutation()
                    
                    child_perm1, child_perm2 = self.order_crossover(perm1, perm2)
                    
                    # Crear nuevos individuos
                    child1 = EnhancedGAIndividual(self.problem)
                    child1.position = child1.permutation_to_position(child_perm1)
                    
                    child2 = EnhancedGAIndividual(self.problem)
                    child2.position = child2.permutation_to_position(child_perm2)
                    
                    offspring = [child1, child2]
                else:
                    offspring = [parent1, parent2]
                
                # Mutación
                mutation_rate = self.get_adaptive_parameter('mutation_rate')
                for child in offspring:
                    if np.random.rand() < mutation_rate:
                        # Aplicar mutación scramble
                        perm = child.decode_routes_to_permutation()
                        mutated_perm = self.scramble_mutation(perm, 0.3)
                        child.position = child.permutation_to_position(mutated_perm)
                
                # Búsqueda local ocasional
                for child in offspring:
                    if np.random.rand() < self.local_search_rate:
                        child.apply_local_search(self.two_opt)
                
                new_population.extend(offspring)
            
            # Actualizar población
            self.population = new_population[:self.population_size]
        
        # Resultados finales
        print(f"\n{'='*60}")
        print("Resultados finales:")
        print(f"Mejor fitness: {best_fitness:.2f}")
        print(f"Reinicios realizados: {self.restart_count}")
        
        metrics = self.get_convergence_metrics()
        print(f"\nMétricas de convergencia:")
        print(f"  - Mejora total: {metrics['total_improvement']:.2f}")
        print(f"  - Tasa de convergencia: {metrics['convergence_rate']:.3f}")
        print(f"  - Iteraciones sin mejora: {metrics['stagnation_count']}")
        print(f"  - Diversidad final: {metrics['final_diversity']:.3f}")
        
        return self.best_solution


def main():
    """Función principal de demostración."""
    # Cargar problema
    instance_path = "data/vrp/E-n22-k4.vrp"
    problem = VRPProblem(instance_path)
    
    print(f"\nProblem: {problem.name}")
    print(f"Customers: {problem.dimension - 1}")
    print(f"Vehicles: {problem.num_vehicles}")
    print(f"Capacity: {problem.capacity}")
    
    # Ejecutar algoritmo mejorado
    algorithm = EnhancedGeneticAlgorithm(
        problem,
        population_size=50,
        max_iterations=500,
        crossover_rate=0.8,
        mutation_rate=0.2,
        elitism_size=3,
        tournament_size=3,
        local_search_rate=0.1,
        seed=42
    )
    
    best_solution = algorithm.run()
    
    # Mostrar mejor solución
    print(f"\n{'='*60}")
    print("Mejor solución encontrada:")
    routes = best_solution.decode_routes()
    total_distance = 0
    
    for i, route in enumerate(routes):
        route_distance = sum(
            problem.distance_matrix[route[j]][route[j+1]]
            for j in range(len(route) - 1)
        )
        total_distance += route_distance
        
        load = sum(problem.demands[c] for c in route[1:-1])
        print(f"  Ruta {i+1}: {' -> '.join(map(str, route))}")
        print(f"    Distancia: {route_distance:.2f}, Carga: {load}/{problem.capacity}")
    
    print(f"\nDistancia total: {total_distance:.2f}")
    
    # Guardar gráfico de convergencia si está disponible matplotlib
    try:
        algorithm.plot_convergence(save_path="enhanced_ga_convergence.png")
        print("\nGráfico de convergencia guardado en 'enhanced_ga_convergence.png'")
    except:
        pass
    
    return algorithm, best_solution


if __name__ == "__main__":
    algorithm, solution = main()