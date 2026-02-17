"""
Tests para el módulo problems.vrptw (Vehicle Routing Problem with Time Windows).
"""
import pytest
import numpy as np
from problems.vrptw import VRPTWProblem


class TestVRPTWProblem:
    """Tests para VRPTWProblem."""
    
    @pytest.fixture
    def simple_instance(self):
        """Create a simple VRPTW instance for testing."""
        # Simple instance with 4 customers + depot
        nodes = [(0, 0), (10, 0), (0, 10), (-10, 0), (0, -10)]
        demands = [0, 20, 30, 25, 35]  # depot has 0 demand
        
        # Time windows: [earliest, latest]
        time_windows = [
            (0, 200),    # depot: always open
            (10, 50),    # customer 1: tight window
            (30, 100),   # customer 2: medium window
            (0, 150),    # customer 3: loose window
            (60, 120)    # customer 4: late window
        ]
        
        return {
            'nodes': nodes,
            'demands': demands,
            'time_windows': time_windows,
            'capacity': 100,
            'service_time': 10
        }
    
    def test_initialization(self, simple_instance):
        """Test VRPTW problem initialization."""
        problem = VRPTWProblem()
        
        # Manually set instance data
        problem.nodes = simple_instance['nodes']
        problem.demands = simple_instance['demands']
        problem.time_windows = simple_instance['time_windows']
        problem.capacity = simple_instance['capacity']
        problem.service_time = simple_instance['service_time']
        problem.dimension = len(simple_instance['nodes'])
        problem.depot_index = 0
        
        # Compute distance matrix
        problem.compute_distance_matrix()
        
        assert problem.dimension == 5
        assert problem.capacity == 100
        assert problem.service_time == 10
        assert len(problem.time_windows) == 5
        assert problem.distance_matrix.shape == (5, 5)
    
    def test_time_windows_setup(self, simple_instance):
        """Test time window setup."""
        problem = VRPTWProblem()
        problem.nodes = simple_instance['nodes']
        problem.dimension = len(simple_instance['nodes'])
        
        # Manually set time windows
        problem.ready_times = [tw[0] for tw in simple_instance['time_windows']]
        problem.due_dates = [tw[1] for tw in simple_instance['time_windows']]
        problem.service_times = [simple_instance['service_time']] * problem.dimension
        problem.service_times[0] = 0  # No service time at depot
        
        # Check time windows are set correctly
        assert len(problem.ready_times) == problem.dimension
        assert len(problem.due_dates) == problem.dimension
        assert problem.ready_times[0] == 0  # Depot ready at time 0
        assert problem.service_times[0] == 0  # No service at depot
    
    def test_evaluate_with_time_windows(self, simple_instance):
        """Test evaluation with time window penalties."""
        problem = VRPTWProblem()
        problem.nodes = simple_instance['nodes']
        problem.demands = simple_instance['demands']
        problem.ready_times = [tw[0] for tw in simple_instance['time_windows']]
        problem.due_dates = [tw[1] for tw in simple_instance['time_windows']]
        problem.service_times = [simple_instance['service_time']] * len(simple_instance['nodes'])
        problem.service_times[0] = 0  # No service at depot
        problem.capacity = simple_instance['capacity']
        problem.dimension = len(simple_instance['nodes'])
        problem.depot_index = 0
        problem.compute_distance_matrix()
        
        # Use method that exists
        routes = [[0, 4, 0], [0, 1, 2, 3, 0]]
        
        # Test evaluating with time windows if method exists
        if hasattr(problem, 'evaluate_routes_with_time'):
            total_cost, penalties, violations = problem.evaluate_routes_with_time(routes)
            assert total_cost > 0
            assert isinstance(penalties, dict)
            assert isinstance(violations, list)
        else:
            # Fall back to regular evaluation
            fitness = problem.evaluate_routes(routes)
            assert fitness > 0
    
    def test_decode_solution(self, simple_instance):
        """Test solution decoding with time windows."""
        problem = VRPTWProblem()
        problem.nodes = simple_instance['nodes']
        problem.demands = simple_instance['demands']
        problem.time_windows = simple_instance['time_windows']
        problem.capacity = simple_instance['capacity']
        problem.service_time = simple_instance['service_time']
        problem.dimension = len(simple_instance['nodes'])
        problem.depot_index = 0
        problem.compute_distance_matrix()
        
        # Random solution vector
        solution = np.random.rand(4)  # 4 customers
        
        routes, total_distance, is_feasible = problem.decode_solution(solution)
        
        # Check basic properties
        assert isinstance(routes, list)
        assert all(isinstance(route, list) for route in routes)
        assert all(route[0] == 0 and route[-1] == 0 for route in routes)
        
        # Check all customers are visited
        visited = set()
        for route in routes:
            for node in route[1:-1]:
                visited.add(node)
        assert visited == {1, 2, 3, 4}
    
    def test_default_time_windows(self, simple_instance):
        """Test default time window initialization."""
        problem = VRPTWProblem()
        problem.dimension = len(simple_instance['nodes'])
        
        # Call method to set default time windows
        problem._set_default_time_windows()
        
        assert len(problem.ready_times) == problem.dimension
        assert len(problem.due_dates) == problem.dimension
        assert len(problem.service_times) == problem.dimension
        
        # Check depot has special values
        assert problem.ready_times[0] == 0.0
        assert problem.service_times[0] == 0.0
        
        # Check all customers have default service time
        for i in range(1, problem.dimension):
            assert problem.service_times[i] == 5.0  # Default 5 minutes
    
    def test_time_attributes(self, simple_instance):
        """Test VRPTW-specific attributes."""
        problem = VRPTWProblem()
        
        # Check default attributes
        assert hasattr(problem, 'ready_times')
        assert hasattr(problem, 'due_dates')
        assert hasattr(problem, 'service_times')
        assert hasattr(problem, 'time_limit')
        assert hasattr(problem, 'time_window_penalty')
        
        # Check default values
        assert problem.time_limit == 1236.0  # Solomon default
        assert problem.time_window_penalty == 1000.0


class TestVRPTWLoadTimeWindows:
    """Tests para carga de ventanas de tiempo desde archivos Solomon."""

    def _write_solomon_file(self, tmp_path, content):
        """Helper para crear archivo Solomon temporal."""
        filepath = tmp_path / "test_solomon.vrp"
        filepath.write_text(content)
        return str(filepath)

    def test_load_time_windows_solomon(self, tmp_path):
        """Test carga de ventanas de tiempo desde archivo Solomon con seccion CUSTOMER."""
        # Sin linea en blanco entre header y datos (el parser hace break en lineas vacias)
        solomon_content = (
            "TEST\n"
            "\n"
            "VEHICLE\n"
            "NUMBER     CAPACITY\n"
            "  5         100\n"
            "\n"
            "CUSTOMER\n"
            "CUST NO.   XCOORD.   YCOORD.    DEMAND   READY TIME   DUE DATE   SERVICE TIME\n"
            "    0      40        50        0        0          1236        0\n"
            "    1      45        68        10       10         100         90\n"
            "    2      42        66        20       20         200         80\n"
            "    3      38        70        30       50         300         70\n"
            "\n"
            "NAME : TEST\n"
            "DIMENSION : 4\n"
            "CAPACITY : 100\n"
            "NODE_COORD_SECTION\n"
            "0 40.0 50.0\n"
            "1 45.0 68.0\n"
            "2 42.0 66.0\n"
            "3 38.0 70.0\n"
            "DEMAND_SECTION\n"
            "0 0\n"
            "1 10\n"
            "2 20\n"
            "3 30\n"
            "DEPOT_SECTION\n"
            "0\n"
            "-1\n"
            "EOF\n"
        )
        filepath = self._write_solomon_file(tmp_path, solomon_content)
        problem = VRPTWProblem(instance_path=filepath)

        assert len(problem.ready_times) == problem.dimension
        assert len(problem.due_dates) == problem.dimension
        assert len(problem.service_times) == problem.dimension
        assert problem.ready_times[0] == 0.0
        assert problem.due_dates[0] == 1236.0
        assert problem.ready_times[1] == 10.0
        assert problem.due_dates[1] == 100.0
        assert problem.service_times[1] == 90.0
        assert problem.ready_times[3] == 50.0
        assert problem.due_dates[3] == 300.0

    def test_load_time_windows_no_customer_section(self, tmp_path):
        """Test carga fallback cuando no hay seccion CUSTOMER."""
        # Archivo VRP sin seccion CUSTOMER -> usa ventanas por defecto
        content = (
            "NAME : TEST\n"
            "DIMENSION : 4\n"
            "CAPACITY : 100\n"
            "NODE_COORD_SECTION\n"
            "0 40.0 50.0\n"
            "1 45.0 68.0\n"
            "2 42.0 66.0\n"
            "3 38.0 70.0\n"
            "DEMAND_SECTION\n"
            "0 0\n"
            "1 10\n"
            "2 20\n"
            "3 30\n"
            "DEPOT_SECTION\n"
            "0\n"
            "-1\n"
            "EOF\n"
        )
        filepath = self._write_solomon_file(tmp_path, content)
        problem = VRPTWProblem(instance_path=filepath)

        # Sin seccion CUSTOMER, deberia usar defaults
        assert len(problem.ready_times) == problem.dimension
        assert all(rt == 0.0 for rt in problem.ready_times)
        assert all(dd == problem.time_limit for dd in problem.due_dates)

    def test_load_time_windows_parse_error(self, tmp_path):
        """Test que datos malformados caen al except con valores por defecto."""
        solomon_content = (
            "TEST\n"
            "\n"
            "VEHICLE\n"
            "NUMBER     CAPACITY\n"
            "  5         100\n"
            "\n"
            "CUSTOMER\n"
            "CUST NO.   XCOORD.   YCOORD.    DEMAND   READY TIME   DUE DATE   SERVICE TIME\n"
            "    0      40        50        0        0          1236        0\n"
            "    1      45        68        10       BAD        DATA        ERR\n"
            "    2      42        66        20       20         200         80\n"
            "\n"
            "NAME : TEST\n"
            "DIMENSION : 3\n"
            "CAPACITY : 100\n"
            "NODE_COORD_SECTION\n"
            "0 40.0 50.0\n"
            "1 45.0 68.0\n"
            "2 42.0 66.0\n"
            "DEMAND_SECTION\n"
            "0 0\n"
            "1 10\n"
            "2 20\n"
            "DEPOT_SECTION\n"
            "0\n"
            "-1\n"
            "EOF\n"
        )
        filepath = self._write_solomon_file(tmp_path, solomon_content)
        problem = VRPTWProblem(instance_path=filepath)

        # El cliente 1 tiene datos malformados -> valores por defecto para ese
        assert len(problem.ready_times) == problem.dimension
        # Linea malformada usa defaults del except
        assert problem.ready_times[1] == 0.0
        assert problem.due_dates[1] == problem.time_limit
        assert problem.service_times[1] == 10.0
        # Linea buena se parsea correctamente
        assert problem.ready_times[2] == 20.0
        assert problem.due_dates[2] == 200.0


class TestVRPTWEvaluateTime:
    """Tests para evaluacion de rutas con ventanas de tiempo."""

    @pytest.fixture
    def vrptw_problem(self):
        """Crea un VRPTW con ventanas estrechas para provocar violaciones."""
        problem = VRPTWProblem()
        # 4 nodos: depot(0) + 3 clientes
        problem.nodes = [(0, 0), (10, 0), (20, 0), (30, 0)]
        problem.demands = [0, 10, 10, 10]
        problem.dimension = 4
        problem.capacity = 100
        problem.depot_index = 0
        problem.compute_distance_matrix()

        # Ventanas de tiempo estrechas
        problem.ready_times = [0.0, 0.0, 0.0, 0.0]
        problem.due_dates = [1236.0, 5.0, 5.0, 5.0]  # Clientes con due_date muy bajo
        problem.service_times = [0.0, 1.0, 1.0, 1.0]
        problem.avg_speed = 40.0

        return problem

    def test_evaluate_routes_with_time_violations(self, vrptw_problem):
        """Test que rutas con ventanas violadas generan penalizaciones."""
        # Ruta que visita los 3 clientes secuencialmente -> el cliente lejano llega tarde
        routes = [[0, 1, 2, 3, 0]]

        total_cost, penalties, violations = vrptw_problem.evaluate_routes_with_time(routes)

        assert total_cost > 0
        assert isinstance(penalties, dict)
        assert 'time_windows' in penalties
        # Con due_date=5 y distancias grandes, deberia haber violaciones
        assert penalties['time_windows'] > 0
        assert len(violations) > 0
        assert any("tardía" in v for v in violations)

    def test_evaluate_routes_short_route(self, vrptw_problem):
        """Test que rutas cortas (< 2 nodos) se saltan correctamente."""
        routes = [[0], [0, 1, 0]]  # Primera ruta tiene solo 1 nodo
        total_cost, penalties, violations = vrptw_problem.evaluate_routes_with_time(routes)
        assert isinstance(total_cost, float)

    def test_evaluate_solution(self, vrptw_problem):
        """Test evaluate() con solucion continua."""
        solution = np.array([0.3, 0.6, 0.9])
        cost = vrptw_problem.evaluate(solution)
        assert cost > 0
        assert isinstance(cost, float)


class TestVRPTWInfoMethods:
    """Tests para metodos de informacion y Quick Commerce."""

    def test_get_time_window_info_empty(self):
        """Test get_time_window_info sin ventanas cargadas."""
        problem = VRPTWProblem()
        info = problem.get_time_window_info()
        assert info == {"status": "No time windows loaded"}

    def test_get_time_window_info_loaded(self):
        """Test get_time_window_info con ventanas cargadas."""
        problem = VRPTWProblem()
        problem.dimension = 4
        problem.ready_times = [0.0, 10.0, 20.0, 50.0]
        problem.due_dates = [1236.0, 100.0, 200.0, 300.0]
        problem.service_times = [0.0, 90.0, 80.0, 70.0]
        problem.time_limit = 1236.0

        info = problem.get_time_window_info()
        assert info['num_customers'] == 3
        assert info['depot_window'] == [0.0, 1236.0]
        assert info['avg_window_width'] > 0
        assert info['avg_service_time'] == 80.0
        assert info['time_horizon'] == 1236.0

    def test_is_quick_commerce_compatible_false_no_windows(self):
        """Test is_quick_commerce_compatible sin ventanas -> False."""
        problem = VRPTWProblem()
        assert problem.is_quick_commerce_compatible() is False

    def test_is_quick_commerce_compatible_false_wide_windows(self):
        """Test is_quick_commerce_compatible con ventanas amplias -> False."""
        problem = VRPTWProblem()
        problem.ready_times = [0.0, 0.0, 0.0, 0.0]
        problem.due_dates = [1236.0, 500.0, 600.0, 700.0]  # Ventanas muy amplias
        assert problem.is_quick_commerce_compatible() is False

    def test_is_quick_commerce_compatible_true(self):
        """Test is_quick_commerce_compatible con ventanas estrechas -> True."""
        problem = VRPTWProblem()
        # Mas del 50% con ventanas <= 30 min
        problem.ready_times = [0.0, 0.0, 0.0, 100.0]
        problem.due_dates = [1236.0, 20.0, 25.0, 120.0]  # 2/3 estrechas
        assert problem.is_quick_commerce_compatible() is True

    def test_convert_to_quick_commerce(self):
        """Test convert_to_quick_commerce convierte ventanas."""
        problem = VRPTWProblem()
        problem.dimension = 4
        problem.time_limit = 1236.0
        problem.rng = np.random.RandomState(42)
        # Inicializar con ventanas amplias
        problem.ready_times = [0.0, 0.0, 0.0, 0.0]
        problem.due_dates = [1236.0, 500.0, 600.0, 700.0]
        problem.service_times = [0.0, 90.0, 80.0, 70.0]

        problem.convert_to_quick_commerce(window_minutes=30)

        # Verificar que ventanas se acortaron para clientes
        for i in range(1, len(problem.ready_times)):
            window_width = problem.due_dates[i] - problem.ready_times[i]
            assert window_width == 30.0
            assert problem.service_times[i] == 5.0
            assert problem.ready_times[i] >= 0
            assert problem.due_dates[i] <= problem.time_limit

    def test_convert_to_quick_commerce_no_windows(self):
        """Test convert_to_quick_commerce sin ventanas previas inicializa defaults primero."""
        problem = VRPTWProblem()
        problem.dimension = 3
        problem.time_limit = 1236.0
        problem.rng = np.random.RandomState(42)
        # Sin ventanas cargadas
        problem.ready_times = []
        problem.due_dates = []
        problem.service_times = []

        problem.convert_to_quick_commerce(window_minutes=20)

        assert len(problem.ready_times) >= problem.dimension
        for i in range(1, len(problem.ready_times)):
            window_width = problem.due_dates[i] - problem.ready_times[i]
            assert window_width == 20.0


class TestVRPTWInconsistentTimeWindows:
    """Tests para ventanas de tiempo inconsistentes."""

    def test_inconsistent_time_windows_length(self, tmp_path):
        """Cuando time_windows tiene menos entradas que dimension,
        load_time_windows debe llamar a _set_default_time_windows."""
        # Crear archivo Solomon con solo 2 entradas CUSTOMER pero DIMENSION=4
        solomon_content = (
            "TEST\n"
            "\n"
            "VEHICLE\n"
            "NUMBER     CAPACITY\n"
            "  5         100\n"
            "\n"
            "CUSTOMER\n"
            "CUST NO.   XCOORD.   YCOORD.    DEMAND   READY TIME   DUE DATE   SERVICE TIME\n"
            "    0      40        50        0        0          1236        0\n"
            "    1      45        68        10       10         100         90\n"
            "\n"
            "NAME : TEST\n"
            "DIMENSION : 4\n"
            "CAPACITY : 100\n"
            "NODE_COORD_SECTION\n"
            "0 40.0 50.0\n"
            "1 45.0 68.0\n"
            "2 42.0 66.0\n"
            "3 38.0 70.0\n"
            "DEMAND_SECTION\n"
            "0 0\n"
            "1 10\n"
            "2 20\n"
            "3 30\n"
            "DEPOT_SECTION\n"
            "0\n"
            "-1\n"
            "EOF\n"
        )
        filepath = tmp_path / "test_inconsistent.vrp"
        filepath.write_text(solomon_content)

        problem = VRPTWProblem(instance_path=str(filepath))

        # Dado que solo hay 2 entradas CUSTOMER pero dimension=4,
        # load_time_windows detecta inconsistencia y usa defaults
        assert len(problem.ready_times) == problem.dimension
        assert len(problem.due_dates) == problem.dimension
        assert len(problem.service_times) == problem.dimension
        # Defaults: all ready_times = 0, all due_dates = time_limit
        assert all(rt == 0.0 for rt in problem.ready_times)
        assert all(dd == problem.time_limit for dd in problem.due_dates)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])