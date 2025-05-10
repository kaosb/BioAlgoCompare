#!/usr/bin/env python3
import unittest
import numpy as np
from problems.vrp import VRPProblem
from algorithms.opa import OPA, Orca

class TestOPAImplementation(unittest.TestCase):
    """Tests para verificar la correcta implementación de OPA para VRP."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        # Cargar una instancia pequeña
        self.instance_path = "data/vrp/E-n22-k4.vrp"
        self.problem = VRPProblem(self.instance_path)
        
        # Configurar semilla para reproducibilidad
        np.random.seed(42)
        self.seed = 42
    
    def test_random_routes_validity(self):
        """Verificar que random_routes() genera rutas factibles."""
        routes = self.problem.random_routes()
        
        # 1. Verificar que cada ruta comienza y termina en el depósito
        for route in routes:
            self.assertEqual(route[0], self.problem.depot_index)
            self.assertEqual(route[-1], self.problem.depot_index)
        
        # 2. Verificar que todas las rutas respetan la capacidad
        for route in routes:
            route_load = 0
            for node in route[1:-1]:  # Excluir depósito
                route_load += self.problem.demands[node]
            self.assertLessEqual(route_load, self.problem.capacity)
        
        # 3. Verificar que todos los clientes están cubiertos exactamente una vez
        covered_nodes = []
        for route in routes:
            covered_nodes.extend(route[1:-1])  # Excluir depósito
        
        # Ordenar para verificar
        covered_nodes.sort()
        expected_nodes = list(range(1, self.problem.dimension))
        expected_nodes.sort()
        
        self.assertEqual(covered_nodes, expected_nodes)
    
    def test_evaluate_routes(self):
        """Verificar que evaluate_routes() es determinista y coherente."""
        routes = self.problem.random_routes()
        
        # Calcular fitness manual
        total_distance = 0
        for route in routes:
            for i in range(len(route) - 1):
                total_distance += self.problem.distance_matrix[route[i], route[i+1]]
        
        # Calcular con evaluate_routes
        fitness = self.problem.evaluate_routes(routes)
        
        # Verificar que son iguales (evaluación sin penalización para rutas factibles)
        # Usar assertAlmostEqual para manejar errores de redondeo en punto flotante
        self.assertAlmostEqual(fitness, total_distance, places=6)
        
        # Verificar que múltiples llamadas dan el mismo resultado
        fitness2 = self.problem.evaluate_routes(routes)
        self.assertEqual(fitness, fitness2)
    
    def test_repair_routes(self):
        """Verificar que repair_routes() corrige rutas no factibles."""
        # Crear rutas intencionalmente no factibles
        routes = [
            [0, 1, 2, 3, 0],  # Ruta normal
            [0, 4, 5, 6, 0],  # Ruta normal
            [0, 7, 8, 9, 7, 0]  # Duplicado intencional
        ]
        
        # Verificar que no son factibles
        is_feasible = self.problem.routes_are_feasible(routes)
        self.assertFalse(is_feasible)
        
        # Reparar rutas
        repaired = self.problem.repair_routes(routes)
        
        # Verificar que ahora son factibles
        is_repaired_feasible = self.problem.routes_are_feasible(repaired)
        self.assertTrue(is_repaired_feasible)
        
        # Verificar que no hay duplicados
        all_nodes = []
        for route in repaired:
            all_nodes.extend(route[1:-1])  # Excluir depósito
        self.assertEqual(len(all_nodes), len(set(all_nodes)))
    
    def test_orca_initialization(self):
        """Verificar que la inicialización de Orca es correcta."""
        orca = Orca(self.problem)
        
        # Verificar que tiene posición factible
        self.assertTrue(self.problem.routes_are_feasible(orca.position))
        
        # Verificar que fitness es un número válido
        self.assertIsNotNone(orca.fitness())
        self.assertIsInstance(orca.fitness(), (int, float))
        
        # Verificar personal_best inicializado correctamente
        self.assertEqual(orca.personal_best_fitness, orca.fitness())
    
    def test_opa_convergence(self):
        """Verificar que OPA no empeora con las iteraciones."""
        # Inicializar OPA con pocas iteraciones
        opa = OPA(self.problem, population_size=10, max_iterations=10, seed=self.seed)
        
        # Ejecutar algoritmo
        best = opa.execute()
        
        # Verificar factibilidad de la solución final
        self.assertTrue(self.problem.routes_are_feasible(best.position))
        
        # Verificar que la curva de convergencia no empeora
        for i in range(1, len(opa.convergence_curve)):
            self.assertLessEqual(opa.convergence_curve[i], opa.convergence_curve[i-1])
    
    def test_opa_consistency(self):
        """Verificar que OPA es consistente con misma semilla."""
        # Crear dos instancias con la misma semilla
        opa1 = OPA(self.problem, population_size=5, max_iterations=5, seed=self.seed)
        opa2 = OPA(self.problem, population_size=5, max_iterations=5, seed=self.seed)
        
        # Ejecutar ambos
        best1 = opa1.execute()
        best2 = opa2.execute()
        
        # Verificar que convergencia es idéntica
        for i in range(len(opa1.convergence_curve)):
            self.assertEqual(opa1.convergence_curve[i], opa2.convergence_curve[i])
        
        # Verificar que fitness final es idéntico
        self.assertEqual(best1.fitness(), best2.fitness())

if __name__ == "__main__":
    unittest.main()