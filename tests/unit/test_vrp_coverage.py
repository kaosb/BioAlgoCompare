"""
Tests adicionales para alcanzar 100% de cobertura en problems/vrp.py
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np
from unittest.mock import Mock, patch, mock_open
from problems.vrp import VRPProblem


class TestVRPValidation:
    """Tests para casos de validación en VRPProblem."""
    
    def test_validate_missing_dimension(self):
        """Test validación cuando falta DIMENSION."""
        # Contenido de archivo sin DIMENSION
        file_content = """NAME : test
CAPACITY : 100
NODE_COORD_SECTION
1 10 20
2 30 40
EOF
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            with pytest.raises(ValueError, match="DIMENSION not found"):
                VRPProblem("test.vrp")
    
    def test_validate_missing_capacity(self):
        """Test validación cuando falta CAPACITY."""
        file_content = """NAME : test
DIMENSION : 2
NODE_COORD_SECTION
1 10 20
2 30 40
DEMAND_SECTION
1 0
2 10
DEPOT_SECTION
1
-1
EOF
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            with pytest.raises(ValueError, match="CAPACITY not found"):
                VRPProblem("test.vrp")
    
    def test_validate_coordinate_count_mismatch(self):
        """Test validación cuando el número de coordenadas no coincide."""
        file_content = """NAME : test
DIMENSION : 3
CAPACITY : 100
NODE_COORD_SECTION
1 10 20
2 30 40
DEMAND_SECTION
1 0
2 10
3 15
DEPOT_SECTION
1
-1
EOF
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            with pytest.raises(ValueError, match="Expected 3 nodes, found 2"):
                VRPProblem("test.vrp")
    
    def test_validate_demand_count_mismatch(self):
        """Test validación cuando el número de demandas no coincide."""
        file_content = """NAME : test
DIMENSION : 2
CAPACITY : 100
NODE_COORD_SECTION
1 10 20
2 30 40
DEMAND_SECTION
1 0
DEPOT_SECTION
1
-1
EOF
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            with pytest.raises(ValueError, match="Expected 2 demands, found 1"):
                VRPProblem("test.vrp")


class TestVRPEdgeCases:
    """Tests para casos edge en VRPProblem."""
    
    def test_edge_weight_type_geo(self):
        """Test cuando EDGE_WEIGHT_TYPE es GEO."""
        file_content = """NAME : test
DIMENSION : 2
CAPACITY : 100
EDGE_WEIGHT_TYPE : GEO
NODE_COORD_SECTION
1 10.0 20.0
2 30.0 40.0
DEMAND_SECTION
1 0
2 10
DEPOT_SECTION
1
-1
EOF
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            problem = VRPProblem("test.vrp")
            assert problem.dimension == 2
            assert problem.capacity == 100
    
    def test_depot_section_processing(self):
        """Test procesamiento de sección DEPOT_SECTION."""
        file_content = """NAME : test
DIMENSION : 3
CAPACITY : 100
NODE_COORD_SECTION
1 10 20
2 30 40
3 50 60
DEMAND_SECTION
1 0
2 10
3 15
DEPOT_SECTION
1
-1
EOF
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            problem = VRPProblem("test.vrp")
            assert problem.depot_index == 0  # Ajustado a índice 0
    
    def test_empty_random_solution(self):
        """Test generación de solución aleatoria con semilla."""
        problem = VRPProblem(seed=42)
        problem.dimension = 5
        problem.lower_bound = 0
        problem.upper_bound = 1
        
        solution = problem.random_solution()
        # get_dimension retorna dimension - 1 (excluye depósito)
        assert len(solution) == problem.get_dimension()
        assert all(0 <= x <= 1 for x in solution)
    
    def test_random_routes_generation(self):
        """Test generación de rutas aleatorias."""
        problem = VRPProblem(seed=42)
        problem.dimension = 5
        problem.depot_index = 0
        problem.capacity = 50
        problem.demands = [0, 10, 15, 20, 25]
        problem.distance_matrix = np.random.rand(5, 5)
        
        routes = problem.random_routes()
        assert isinstance(routes, list)
        assert all(route[0] == 0 and route[-1] == 0 for route in routes)


class TestVRPDecoding:
    """Tests para funciones de decodificación."""
    
    def test_decode_solution_basic(self):
        """Test decodificación básica."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        problem.distance_matrix = np.array([
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 10],
            [30, 25, 10, 0]
        ])
        
        # Solución simple
        solution = np.array([0.1, 0.9, 0.5])
        
        routes, distance, is_feasible = problem.decode_solution(solution)
        assert is_feasible  # Debe ser factible
        assert distance > 0
        assert isinstance(routes, list)
    
    def test_decode_solution_capacity_split(self):
        """Test decodificación cuando se debe dividir por capacidad."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 20  # Capacidad limitada
        problem.demands = [0, 15, 15, 10]  # Clientes 1 y 2 no caben juntos
        problem.distance_matrix = np.array([
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 10],
            [30, 25, 10, 0]
        ])
        
        solution = np.array([0.1, 0.5, 0.9])  # Orden: 1, 2, 3
        
        routes, distance, is_feasible = problem.decode_solution(solution)
        assert is_feasible
        assert len(routes) >= 2  # Debe crear al menos 2 rutas
        assert all(route[0] == 0 and route[-1] == 0 for route in routes)
    
    def test_evaluate_routes_as_solution(self):
        """Test evaluar rutas directamente como solución."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        problem.distance_matrix = np.array([
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 10],
            [30, 25, 10, 0]
        ])
        
        # Evaluar rutas directamente
        routes = [[0, 1, 2, 0], [0, 3, 0]]
        
        fitness = problem.evaluate(routes)
        assert fitness > 0
        assert isinstance(fitness, (float, np.float64))


class TestVRPEvaluation:
    """Tests para funciones de evaluación."""
    
    def test_evaluate_with_penalty_factor(self):
        """Test evaluación con factor de penalización."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 10
        problem.demands = [0, 15, 5]  # Cliente 1 excede capacidad
        problem.distance_matrix = np.array([
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0]
        ])
        problem.penalty_factor = 1000.0
        
        # Rutas con violación de capacidad
        routes = [[0, 1, 0], [0, 2, 0]]  # Primera ruta excede capacidad
        
        fitness = problem.evaluate_routes(routes)
        # Debe ser mayor que solo la distancia
        base_distance = 10 + 10 + 20 + 20  # 0->1->0 + 0->2->0
        assert fitness > base_distance
    
    def test_evaluate_routes_detailed(self):
        """Test evaluación detallada de rutas."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 20
        problem.demands = [0, 15, 10]
        problem.distance_matrix = np.array([
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0]
        ])
        
        # Ruta que excede capacidad
        routes = [[0, 1, 2, 0]]  # Carga total: 25 > 20
        
        distance, penalties, errors = problem.evaluate_routes_detailed(routes)
        assert penalties['capacity'] > 0  # Debe tener penalización por capacidad
        assert len(errors) > 0  # Debe tener mensajes de error
    
    def test_evaluate_routes_missing_nodes(self):
        """Test evaluación con nodos faltantes."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        problem.distance_matrix = np.ones((4, 4)) * 10
        np.fill_diagonal(problem.distance_matrix, 0)
        
        # Rutas que no cubren todos los clientes (falta cliente 3)
        routes = [[0, 1, 0], [0, 2, 0]]
        
        distance, penalties, errors = problem.evaluate_routes_detailed(routes)
        assert penalties['missing'] > 0  # Debe tener penalización por nodo faltante
        assert any('faltantes' in err for err in errors)


class TestVRPDistance:
    """Tests para cálculos de distancia."""
    
    def test_evaluate_routes_duplicate_nodes(self):
        """Test evaluación con nodos duplicados."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        problem.distance_matrix = np.ones((4, 4)) * 10
        np.fill_diagonal(problem.distance_matrix, 0)
        
        # Rutas con cliente 2 duplicado
        routes = [[0, 1, 2, 0], [0, 2, 3, 0]]
        
        distance, penalties, errors = problem.evaluate_routes_detailed(routes)
        assert penalties['duplicate'] > 0  # Debe tener penalización por duplicado
        assert any('duplicados' in err for err in errors)


class TestVRPRouteManagement:
    """Tests para manejo de rutas."""
    
    def test_routes_feasibility_capacity_violation(self):
        """Test factibilidad con violación de capacidad."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 20
        problem.demands = [0, 15, 10]
        
        # Ruta que excede capacidad
        routes = [[0, 1, 2, 0]]  # Carga: 25 > 20
        
        is_feasible, errors = problem.routes_are_feasible(routes)
        assert not is_feasible
        assert any('excede capacidad' in err for err in errors)
    
    def test_routes_feasibility_missing_nodes(self):
        """Test factibilidad con nodos faltantes."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        
        # Rutas que no cubren cliente 3
        routes = [[0, 1, 0], [0, 2, 0]]
        
        is_feasible, errors = problem.routes_are_feasible(routes)
        assert not is_feasible
        assert any('faltantes' in err for err in errors)
    
    def test_routes_feasibility_duplicates(self):
        """Test factibilidad con nodos duplicados."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        
        # Cliente 2 aparece en ambas rutas
        routes = [[0, 1, 2, 0], [0, 2, 3, 0]]
        
        is_feasible, errors = problem.routes_are_feasible(routes)
        assert not is_feasible
        assert any('duplicados' in err for err in errors)


class TestVRPDynamicMethods:
    """Tests para métodos dinámicos de VRP."""
    
    def test_update_demand_with_orders(self):
        """Test actualización de demanda con órdenes específicas."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15]
        problem.nodes = [(0, 0), (10, 10), (20, 20)]
        
        # Agregar nueva orden
        new_orders = [{
            'coord': (30, 30),
            'demand': 5,
            'time': 10.0,
            'order_id': 'TEST_001'
        }]
        
        problem.update_demand(new_orders, current_time=10.0)
        
        assert problem.dimension == 4  # Debe haber aumentado
        assert len(problem.nodes) == 4
        assert len(problem.demands) == 4
        assert problem.demands[-1] == 5
    
    def test_update_demand_dynamic_generation(self):
        """Test actualización dinámica con generación Poisson."""
        problem = VRPProblem(seed=42, dynamic_lambda=5.0)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15]
        problem.nodes = [(0, 0), (10, 10), (20, 20)]
        
        initial_dim = problem.dimension
        
        # Actualizar sin órdenes específicas (generación Poisson)
        problem.update_demand([], current_time=5.0)
        
        # Debe haber generado algunas órdenes nuevas
        assert problem.dimension >= initial_dim
        assert problem.current_time == 5.0


class TestVRPInitialization:
    """Tests para inicialización sin archivo."""
    
    def test_init_without_file(self):
        """Test inicialización sin archivo VRP."""
        problem = VRPProblem(seed=123)
        
        # Valores iniciales
        assert problem.dimension == 0
        assert problem.capacity == 0
        assert problem.depot_index == 0
        assert len(problem.nodes) == 0
        assert len(problem.demands) == 0
        assert problem.seed == 123
    
    def test_init_with_depots(self):
        """Test inicialización con dark stores."""
        depots = [(0, 0), (50, 50), (100, 100)]
        problem = VRPProblem(depots=depots, dynamic_lambda=10.0)
        
        assert problem.depots == depots
        assert problem.dynamic_lambda == 10.0
        assert len(problem.dynamic_orders) == 0
        assert problem.current_time == 0.0


class TestVRPMultiObjective:
    """Tests para funciones multiobjetivo."""
    
    def test_evaluate_multi(self):
        """Test evaluación multiobjetivo."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        problem.distance_matrix = np.array([
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 10],
            [30, 25, 10, 0]
        ])
        
        routes = [[0, 1, 2, 0], [0, 3, 0]]
        
        tiempo, coef_var, distancia = problem.evaluate_multi(routes)
        
        assert tiempo > 0  # Tiempo promedio debe ser positivo
        assert coef_var >= 0  # Coeficiente de variación no negativo
        assert distancia > 0  # Distancia total positiva
    
    def test_evaluate_multi_empty_routes(self):
        """Test evaluación multiobjetivo con rutas vacías."""
        problem = VRPProblem(seed=42)
        problem.dimension = 2
        problem.depot_index = 0
        problem.distance_matrix = np.zeros((2, 2))
        
        # Rutas vacías
        routes = [[0, 0]]
        
        tiempo, coef_var, distancia = problem.evaluate_multi(routes)
        
        assert tiempo == float('inf')  # Sin entregas
        assert coef_var == float('inf')  # Sin cargas
    
    def test_dominates(self):
        """Test dominancia de Pareto."""
        problem = VRPProblem()
        
        # sol1 domina a sol2 (mejor en todos los objetivos)
        sol1 = (10.0, 0.2, 100.0)
        sol2 = (15.0, 0.5, 150.0)
        assert problem.dominates(sol1, sol2)
        assert not problem.dominates(sol2, sol1)
        
        # Soluciones no dominadas
        sol3 = (10.0, 0.5, 150.0)  # Mejor tiempo, peor en otros
        sol4 = (15.0, 0.2, 100.0)  # Peor tiempo, mejor en otros
        assert not problem.dominates(sol3, sol4)
        assert not problem.dominates(sol4, sol3)


class TestVRPEvasion:
    """Tests para estrategia de evasión."""
    
    def test_apply_evasion_strategy(self):
        """Test aplicar estrategia de evasión."""
        problem = VRPProblem(seed=42)
        problem.dimension = 5
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5, 8]
        problem.distance_matrix = np.ones((5, 5)) * 10
        np.fill_diagonal(problem.distance_matrix, 0)
        problem.avg_speed = 40.0
        problem.service_time = 5.0
        
        # Rutas con tiempos largos
        routes = [[0, 1, 2, 3, 0], [0, 4, 0]]
        
        new_routes = problem.apply_evasion_strategy(routes, delay_threshold=30.0)
        
        assert isinstance(new_routes, list)
        assert len(new_routes) == len(routes)
    
    def test_apply_evasion_no_delays(self):
        """Test evasión sin retrasos."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.distance_matrix = np.ones((3, 3)) * 5
        np.fill_diagonal(problem.distance_matrix, 0)
        problem.avg_speed = 60.0
        problem.service_time = 2.0
        
        routes = [[0, 1, 0], [0, 2, 0]]
        
        new_routes = problem.apply_evasion_strategy(routes, delay_threshold=100.0)
        
        # Sin retrasos, rutas no deben cambiar
        assert new_routes == routes


class TestVRPHelpers:
    """Tests para métodos auxiliares."""
    
    def test_is_valid_with_routes(self):
        """Test validación con rutas."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15]
        
        # Rutas válidas
        valid_routes = [[0, 1, 2, 0]]
        assert problem.is_valid(valid_routes)
        
        # Rutas inválidas (falta cliente 2)
        invalid_routes = [[0, 1, 0]]
        assert not problem.is_valid(invalid_routes)
    
    def test_is_valid_with_solution(self):
        """Test validación con solución continua."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        
        # Solución válida
        valid_solution = np.array([0.5, 0.8])
        assert problem.is_valid(valid_solution)
        
        # Solución inválida (dimensión incorrecta)
        invalid_solution = np.array([0.5])
        assert not problem.is_valid(invalid_solution)
        
        # Solución inválida (valores fuera de rango)
        invalid_solution2 = np.array([0.5, 1.5])
        assert not problem.is_valid(invalid_solution2)
    
    def test_repair_routes_with_duplicates(self):
        """Test reparación de rutas con duplicados."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        
        # Rutas con duplicados y faltantes
        routes = [[0, 1, 2, 0], [0, 2, 0]]  # 2 duplicado, falta 3
        
        repaired = problem.repair_routes(routes)
        
        # Verificar que las rutas reparadas son factibles
        is_feasible, errors = problem.routes_are_feasible(repaired)
        assert is_feasible
        assert len(errors) == 0
        
        # Verificar que todos los clientes están cubiertos
        all_customers = set()
        for route in repaired:
            all_customers.update(route[1:-1])
        assert all_customers == {1, 2, 3}


class TestVRPScipyFallback:
    """Tests para fallback cuando scipy no está disponible."""
    
    def test_compute_distance_matrix_without_scipy(self):
        """Test cálculo de matriz de distancias sin scipy."""
        # Simular ausencia de scipy
        import sys
        scipy_backup = sys.modules.get('scipy.spatial')
        if 'scipy.spatial' in sys.modules:
            del sys.modules['scipy.spatial']
        
        try:
            problem = VRPProblem(seed=42)
            problem.nodes = [(0, 0), (3, 4), (6, 8)]
            problem.compute_distance_matrix()
            
            # Verificar distancias calculadas manualmente
            assert problem.distance_matrix[0, 0] == 0
            assert problem.distance_matrix[0, 1] == 5.0  # sqrt(3^2 + 4^2)
            assert problem.distance_matrix[0, 2] == 10.0  # sqrt(6^2 + 8^2)
            assert problem.distance_matrix[1, 2] == 5.0  # sqrt(3^2 + 4^2)
        finally:
            # Restaurar scipy si estaba disponible
            if scipy_backup:
                sys.modules['scipy.spatial'] = scipy_backup


class TestVRPEdgeWeight:
    """Tests para casos edge de tipos de peso."""
    
    def test_load_instance_by_name(self):
        """Test cargar instancia por nombre."""
        # Crear archivo temporal de prueba
        import tempfile
        import os
        
        # Crear estructura de directorios esperada
        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear subdirectorios data/vrp
            data_dir = os.path.join(tmpdir, 'data', 'vrp')
            os.makedirs(data_dir, exist_ok=True)
            
            # Crear archivo VRP de prueba
            vrp_file = os.path.join(data_dir, 'test-instance.vrp')
            with open(vrp_file, 'w') as f:
                f.write("""NAME : test-instance
DIMENSION : 3
CAPACITY : 100
NODE_COORD_SECTION
1 0 0
2 10 10
3 20 20
DEMAND_SECTION
1 0
2 15
3 25
DEPOT_SECTION
1
-1
EOF
""")
            
            # Cambiar temporalmente el directorio base
            import problems.vrp
            old_file = problems.vrp.__file__
            problems.vrp.__file__ = os.path.join(tmpdir, 'problems', 'vrp.py')
            
            try:
                # Probar carga por nombre
                problem = VRPProblem()
                problem.load_instance('test-instance')
                
                assert problem.name == 'test-instance'
                assert problem.dimension == 3
                assert problem.capacity == 100
            finally:
                problems.vrp.__file__ = old_file


class TestVRPEvasionEdgeCases:
    """Tests para casos edge de evasión."""
    
    def test_apply_evasion_empty_route(self):
        """Test evasión con ruta vacía."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15]
        problem.distance_matrix = np.ones((3, 3)) * 10
        np.fill_diagonal(problem.distance_matrix, 0)
        problem.avg_speed = 40.0
        problem.service_time = 5.0
        
        # Rutas con una vacía
        routes = [[0, 0], [0, 1, 2, 0]]  # Primera ruta vacía
        
        new_routes = problem.apply_evasion_strategy(routes, delay_threshold=30.0)
        assert len(new_routes) == len(routes)
    
    def test_apply_evasion_no_alternative(self):
        """Test evasión sin alternativas factibles."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 15  # Capacidad muy limitada
        problem.demands = [0, 10, 15]
        problem.distance_matrix = np.ones((3, 3)) * 100  # Distancias largas
        np.fill_diagonal(problem.distance_matrix, 0)
        problem.avg_speed = 10.0  # Velocidad baja
        problem.service_time = 10.0  # Tiempo de servicio alto
        
        # Rutas con retrasos pero sin posibilidad de mover clientes
        routes = [[0, 1, 0], [0, 2, 0]]
        
        new_routes = problem.apply_evasion_strategy(routes, delay_threshold=10.0)
        
        # Si no hay mejor opción, debe mantener las rutas originales
        assert new_routes == routes


class TestVRPRepairEdgeCases:
    """Tests para casos edge de reparación."""
    
    def test_repair_routes_capacity_split(self):
        """Test reparación cuando se necesita dividir por capacidad."""
        problem = VRPProblem(seed=42)
        problem.dimension = 5
        problem.depot_index = 0
        problem.capacity = 20
        problem.demands = [0, 15, 15, 10, 5]  # Necesita división cuidadosa
        
        # Ruta original que excede capacidad
        routes = [[0, 1, 2, 3, 4, 0]]  # Total: 45 > 20
        
        repaired = problem.repair_routes(routes)
        
        # Verificar que se dividieron las rutas correctamente
        is_feasible, errors = problem.routes_are_feasible(repaired)
        assert is_feasible
        assert len(repaired) >= 3  # Necesita al menos 3 rutas


class TestVRPEvaluationEdgeCases:
    """Tests para casos edge de evaluación."""
    
    def test_evaluate_numpy_array(self):
        """Test evaluar solución como array numpy."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15]
        problem.distance_matrix = np.array([
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0]
        ])
        
        # Evaluar array numpy
        solution = np.array([0.2, 0.8])
        fitness = problem.evaluate(solution)
        
        assert isinstance(fitness, (float, np.float64))
        assert fitness > 0


class TestVRPLoadInstance:
    """Tests para carga de instancias."""
    
    def test_parse_instance_metadata_edge_weight_type(self):
        """Test parseo de metadatos con EDGE_WEIGHT_TYPE."""
        lines = [
            "NAME : test",
            "TYPE : CVRP",
            "DIMENSION : 5",
            "EDGE_WEIGHT_TYPE : EUC_2D",
            "CAPACITY : 100"
        ]
        
        problem = VRPProblem()
        metadata = problem._parse_instance_metadata(lines)
        
        assert metadata['name'] == 'test'
        assert metadata['type'] == 'CVRP'
        assert metadata['dimension'] == 5
        assert metadata['capacity'] == 100


class TestVRPRepairMissingCustomers:
    """Tests para reparación con clientes faltantes que requieren nueva ruta."""
    
    def test_repair_routes_missing_customers_new_route(self):
        """Test reparación cuando clientes faltantes necesitan nueva ruta."""
        problem = VRPProblem(seed=42)
        problem.dimension = 6
        problem.depot_index = 0
        problem.capacity = 20
        problem.demands = [0, 10, 10, 15, 15, 5]  # Clientes 3 y 4 llenan cada uno una ruta
        
        # Rutas iniciales que no incluyen cliente 5
        routes = [[0, 1, 2, 0], [0, 3, 0], [0, 4, 0]]  # Falta cliente 5
        
        repaired = problem.repair_routes(routes)
        
        # Verificar que se agregó el cliente faltante
        all_customers = set()
        for route in repaired:
            all_customers.update(route[1:-1])
        assert 5 in all_customers
        
        # Verificar factibilidad
        is_feasible, errors = problem.routes_are_feasible(repaired)
        assert is_feasible


class TestVRPMultiObjectiveInfinity:
    """Tests para casos que devuelven infinito en evaluación multiobjetivo."""
    
    def test_evaluate_multi_no_route_loads(self):
        """Test evaluación multiobjetivo sin cargas de ruta."""
        problem = VRPProblem(seed=42)
        problem.dimension = 2
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 0]  # Cliente sin demanda
        problem.distance_matrix = np.array([
            [0, 10],
            [10, 0]
        ])
        
        # Rutas con clientes sin demanda
        routes = [[0, 1, 0]]
        
        tiempo, coef_var, distancia = problem.evaluate_multi(routes)
        
        # Con demanda 0, el coeficiente de variación debe ser infinito
        assert coef_var == float('inf')


class TestVRPEvasionContinueRoute:
    """Tests para evasión cuando se continúa con la ruta."""
    
    def test_apply_evasion_continue_when_empty(self):
        """Test evasión continúa cuando encuentra ruta vacía."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 30
        problem.demands = [0, 10, 15, 5]
        problem.distance_matrix = np.ones((4, 4)) * 50  # Distancias largas
        np.fill_diagonal(problem.distance_matrix, 0)
        problem.avg_speed = 20.0
        problem.service_time = 10.0
        
        # Primera ruta vacía, segunda con retraso
        routes = [[0, 0], [0, 1, 2, 3, 0]]
        
        new_routes = problem.apply_evasion_strategy(routes, delay_threshold=30.0)
        
        # Debe procesar correctamente incluso con ruta vacía
        assert len(new_routes) == 2


class TestVRPDistanceMatrixScipyFallback:
    """Tests para el fallback manual cuando scipy no está disponible."""

    def test_distance_matrix_scipy_fallback(self):
        """Patch sys.modules para que scipy.spatial falle al importar,
        luego verifica que compute_distance_matrix use el fallback manual."""
        import importlib
        import problems.vrp as vrp_module

        problem = VRPProblem(seed=42)
        problem.nodes = [(0, 0), (3, 4), (6, 8)]

        # Forzar que la importación de scipy.spatial.distance lance ImportError
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def patched_import(name, *args, **kwargs):
            if name == "scipy.spatial" or name.startswith("scipy.spatial"):
                raise ImportError("mocked scipy unavailable")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=patched_import):
            problem.compute_distance_matrix()

        # Verificar que la matriz se calculó correctamente con el fallback manual
        assert problem.distance_matrix.shape == (3, 3)
        np.testing.assert_almost_equal(problem.distance_matrix[0, 1], 5.0)
        np.testing.assert_almost_equal(problem.distance_matrix[0, 2], 10.0)
        np.testing.assert_almost_equal(problem.distance_matrix[1, 2], 5.0)
        # Diagonal debe ser 0
        for i in range(3):
            assert problem.distance_matrix[i, i] == 0.0


class TestVRPEvaluateRoutesInvalidIndex:
    """Tests para penalización con nodos inválidos en evaluate_multi."""

    def test_evaluate_routes_invalid_index(self):
        """Rutas con un nodo fuera de rango (999) deben recibir penalización de 1000."""
        problem = VRPProblem(seed=42)
        problem.dimension = 4
        problem.depot_index = 0
        problem.capacity = 100
        problem.demands = [0, 10, 15, 5]
        problem.avg_speed = 40.0
        problem.service_time = 5.0
        problem.distance_matrix = np.ones((4, 4)) * 10
        np.fill_diagonal(problem.distance_matrix, 0)

        # Ruta con nodo inválido 999
        routes_invalid = [[0, 1, 999, 0]]
        # Ruta equivalente sin nodo inválido
        routes_valid = [[0, 1, 2, 0]]

        # evaluate_multi calcula distancia; el nodo 999 recibe penalización de 1000.0
        _, _, dist_invalid = problem.evaluate_multi(routes_invalid)
        _, _, dist_valid = problem.evaluate_multi(routes_valid)

        # La distancia con nodo inválido debe ser significativamente mayor
        assert dist_invalid > dist_valid
        # La penalización por nodo inválido aporta al menos 1000.0 extra
        assert dist_invalid - dist_valid >= 1000.0


class TestVRPEvasionStrategyReturns:
    """Tests para la estrategia de evasión cuando hay retrasos sobre el umbral."""

    def test_evasion_strategy_returns(self):
        """Rutas con delay > threshold deben activar la estrategia de evasión
        y retornar rutas modificadas (o las originales si no hay mejor opción)."""
        problem = VRPProblem(seed=42)
        problem.dimension = 5
        problem.depot_index = 0
        problem.capacity = 50
        problem.demands = [0, 5, 5, 5, 5]
        problem.distance_matrix = np.ones((5, 5)) * 100  # Distancias largas -> retraso
        np.fill_diagonal(problem.distance_matrix, 0)
        problem.avg_speed = 10.0  # Velocidad baja para generar retraso
        problem.service_time = 20.0  # Servicio largo para generar retraso

        # Ruta larga con muchos clientes que genera delay
        routes = [[0, 1, 2, 3, 0], [0, 4, 0]]

        # Umbral bajo para asegurar que hay retrasos
        new_routes = problem.apply_evasion_strategy(routes, delay_threshold=5.0)

        assert isinstance(new_routes, list)
        assert len(new_routes) == len(routes)
        # Todos los clientes deben seguir presentes
        all_customers_before = set()
        for r in routes:
            all_customers_before.update(r[1:-1])
        all_customers_after = set()
        for r in new_routes:
            all_customers_after.update(r[1:-1])
        assert all_customers_before == all_customers_after

    def test_evasion_strategy_short_route_skip(self):
        """Cubre vrp.py:666 – ruta corta (len<=2) en delayed_routes hace continue."""
        problem = VRPProblem(seed=42)
        problem.dimension = 3
        problem.depot_index = 0
        problem.capacity = 50
        problem.demands = [0, 5, 5]
        problem.distance_matrix = np.ones((3, 3)) * 100
        np.fill_diagonal(problem.distance_matrix, 0)
        problem.avg_speed = 10.0
        problem.service_time = 20.0

        # Solo rutas cortas: ambas con len<=2, time=0
        # Con threshold negativo (-1), 0 > -1 = True -> ambas en delayed_routes
        # Ambas hacen continue en línea 666
        routes = [[0, 0], [0, 0]]

        new_routes = problem.apply_evasion_strategy(routes, delay_threshold=-1)

        assert isinstance(new_routes, list)
        assert new_routes == [[0, 0], [0, 0]]