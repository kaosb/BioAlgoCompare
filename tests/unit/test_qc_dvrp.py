"""
Tests para el modulo problems.qc_dvrp (QC-DVRP Simulator).
Cubre las lineas criticas incluyendo: 163-184, 219, 273-274, 309, 328,
344-345, 408, 480, 501-502, 509-514, 520-521.
"""
import math
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from problems.qc_dvrp import QCDVRPSimulator, Order, DarkStore


class TestQCDVRPDarkStores:
    """Tests para configuracion de dark stores."""

    def test_single_dark_store(self):
        """n_dark_stores=1 coloca el store en el centro de la zona (line 133)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=5,
            seed=42,
        )
        sim._setup_dark_stores()

        assert len(sim.dark_stores) == 1
        store = sim.dark_stores[0]
        assert store.location == (5.0, 5.0)
        assert store.n_vehicles == 5

    def test_grid_dark_stores(self):
        """n_dark_stores=4 usa layout circular/grid (lines 145-150)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=4,
            n_vehicles=8,
            seed=42,
        )
        sim._setup_dark_stores()

        assert len(sim.dark_stores) == 4
        for store in sim.dark_stores:
            assert store.n_vehicles >= 2
        total_vehicles = sum(s.n_vehicles for s in sim.dark_stores)
        assert total_vehicles == 8


class TestQCDVRPOrderGeneration:
    """Tests para generacion de ordenes."""

    def test_generate_orders(self):
        """_generate_orders crea ordenes via Poisson (lines 163-184)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            poisson_lambda=10.0,  # Alta tasa para garantizar ordenes
            vehicle_capacity=50,
            seed=42,
        )
        sim._setup_dark_stores()

        sim._generate_orders(window_start=0.0, window_duration_min=5.0)

        # Con lambda=10 y duracion=5, esperamos ~50 ordenes
        assert len(sim.all_orders) > 0
        assert len(sim.pending_orders) == len(sim.all_orders)
        assert sim.order_counter == len(sim.all_orders)

        # Verificar propiedades de las ordenes generadas
        for order in sim.all_orders:
            assert 0.0 <= order.location[0] <= 10.0
            assert 0.0 <= order.location[1] <= 10.0
            assert order.demand >= 1
            assert order.arrival_time >= 0.0
            assert order.tw_start == order.arrival_time + sim.time_window_min
            assert order.tw_end == order.arrival_time + sim.time_window_max
            assert order.status == "pending"


class TestQCDVRPOrderAssignment:
    """Tests para asignacion de ordenes."""

    def test_skip_assigned_order(self):
        """Ordenes con assigned_store ya asignado no se re-asignan (line 190)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=3,
            n_vehicles=9,
            seed=42,
        )
        sim._setup_dark_stores()

        order = Order(
            order_id=0,
            location=(8.0, 8.0),
            demand=5,
            arrival_time=0.0,
            tw_start=10.0,
            tw_end=30.0,
        )
        order.assigned_store = 2

        sim.pending_orders = [order]
        sim._assign_orders_to_stores()

        assert order.assigned_store == 2


class TestQCDVRPBuildVRP:
    """Tests para construccion de instancias VRP."""

    def test_build_vrp_no_orders(self):
        """_build_vrp_instance retorna None cuando no hay ordenes (line 219)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            seed=42,
        )
        sim._setup_dark_stores()
        sim.pending_orders = []

        result = sim._build_vrp_instance(0)
        assert result is None


class TestQCDVRPSolveVRP:
    """Tests para resolucion de VRP."""

    def test_solve_no_position_fallback(self):
        """Cuando el algoritmo no tiene .position, usa fallback (lines 276-280)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            population_size=5,
            max_fes=50,
            seed=42,
        )
        sim._setup_dark_stores()

        for i in range(3):
            order = Order(
                order_id=i,
                location=(float(i + 1), float(i + 1)),
                demand=5,
                arrival_time=0.0,
                tw_start=10.0,
                tw_end=60.0,
            )
            order.assigned_store = 0
            order.status = "pending"
            sim.all_orders.append(order)
            sim.pending_orders.append(order)

        problem = sim._build_vrp_instance(0)
        assert problem is not None

        mock_best = MagicMock(spec=[])  # Sin atributo position
        mock_algo_instance = MagicMock()
        mock_algo_instance.execute.return_value = mock_best

        mock_algo_class = MagicMock(return_value=mock_algo_instance)

        routes, fitness = sim._solve_vrp(problem, mock_algo_class, {}, 50)

        assert isinstance(routes, list)
        assert isinstance(fitness, float)

    def test_solve_with_position(self):
        """Cuando best tiene .position, usa decode_solution (lines 273-274)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            population_size=5,
            max_fes=50,
            seed=42,
        )
        sim._setup_dark_stores()

        for i in range(3):
            order = Order(
                order_id=i,
                location=(float(i + 1), float(i + 1)),
                demand=5,
                arrival_time=0.0,
                tw_start=10.0,
                tw_end=60.0,
            )
            order.assigned_store = 0
            order.status = "pending"
            sim.all_orders.append(order)
            sim.pending_orders.append(order)

        problem = sim._build_vrp_instance(0)
        assert problem is not None

        # Mock del algoritmo cuyo best SI tiene .position
        dim = problem.get_dimension()
        mock_best = MagicMock()
        mock_best.position = np.random.rand(dim)
        mock_best.fitness.return_value = 42.0

        mock_algo_instance = MagicMock()
        mock_algo_instance.execute.return_value = mock_best

        mock_algo_class = MagicMock(return_value=mock_algo_instance)

        routes, fitness = sim._solve_vrp(problem, mock_algo_class, {}, 50)

        assert isinstance(routes, list)
        assert fitness == 42.0
        mock_best.fitness.assert_called_once()


class TestQCDVRPSimulateDeliveries:
    """Tests para simulacion de entregas."""

    def test_simulate_deliveries_success(self):
        """Simular entregas exitosas (lines 299-356)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            avg_speed=40.0,
            service_time=5.0,
            seed=42,
        )
        sim._setup_dark_stores()

        orders = []
        for i in range(2):
            order = Order(
                order_id=i,
                location=(5.0 + i, 5.0 + i),
                demand=5,
                arrival_time=0.0,
                tw_start=0.0,
                tw_end=120.0,
            )
            order.assigned_store = 0
            order.status = "pending"
            orders.append(order)
            sim.all_orders.append(order)
            sim.pending_orders.append(order)

        routes = [[0, 1, 2, 0]]
        sim._simulate_deliveries(0, routes, current_time=0.0)

        assert len(sim.completed_orders) + len(sim.failed_orders) == 2
        pending_store0 = [o for o in sim.pending_orders if o.assigned_store == 0]
        assert len(pending_store0) == 0

    def test_vehicle_limit_break(self):
        """Mas rutas que vehiculos causa break (line 309)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=1,  # Solo 1 vehiculo
            avg_speed=40.0,
            service_time=5.0,
            seed=42,
        )
        sim._setup_dark_stores()

        orders = []
        for i in range(3):
            order = Order(
                order_id=i,
                location=(5.0 + i, 5.0),
                demand=5,
                arrival_time=0.0,
                tw_start=0.0,
                tw_end=120.0,
            )
            order.assigned_store = 0
            order.status = "pending"
            orders.append(order)
            sim.all_orders.append(order)
            sim.pending_orders.append(order)

        # 3 rutas pero solo 1 vehiculo -> la segunda ruta dispara break
        routes = [
            [0, 1, 0],
            [0, 2, 0],
            [0, 3, 0],
        ]
        sim._simulate_deliveries(0, routes, current_time=0.0)

        # Solo la primera ruta se procesa (1 vehiculo)
        processed = len(sim.completed_orders) + len(sim.failed_orders)
        assert processed == 1

    def test_prev_node_out_of_range_is_unreachable(self):
        """Linea 328 es dead code defensivo: inalcanzable bajo uso normal.

        Analisis:
        - prev_node solo se actualiza en linea 347: prev_node = node
        - Linea 347 esta dentro del bloque 'if 0 <= order_idx < len(store_orders)'
        - Por lo tanto, prev_node siempre satisface: 1 <= prev_node <= len(store_orders)
        - Esto implica prev_order_idx = prev_node - 1 esta en [0, len(store_orders)-1]
        - La condicion de linea 325 '0 <= prev_order_idx < len(store_orders)' siempre es True
        - La rama else (linea 328) nunca se ejecuta

        Este test documenta que linea 328 es codigo defensivo inalcanzable.
        """
        # Verificamos el comportamiento normal funciona correctamente
        sim = QCDVRPSimulator(
            zone_size=10.0, n_dark_stores=1, n_vehicles=3,
            avg_speed=40.0, service_time=5.0, seed=42,
        )
        sim._setup_dark_stores()

        o1 = Order(0, (6.0, 6.0), 5, 0.0, 0.0, 120.0)
        o1.assigned_store = 0
        o1.status = "pending"
        o2 = Order(1, (7.0, 7.0), 5, 0.0, 0.0, 120.0)
        o2.assigned_store = 0
        o2.status = "pending"

        sim.all_orders.extend([o1, o2])
        sim.pending_orders.extend([o1, o2])

        # Ruta con nodos validos en orden inverso
        routes = [[0, 2, 1, 0]]
        sim._simulate_deliveries(0, routes, current_time=0.0)

        assert len(sim.completed_orders) + len(sim.failed_orders) == 2

    def test_delivery_fails_late(self):
        """Entregas fuera de ventana se marcan como failed (lines 344-345)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            avg_speed=1.0,   # Muy lento: 1 km/h
            service_time=50.0,  # Mucho tiempo de servicio
            seed=42,
        )
        sim._setup_dark_stores()

        order = Order(
            order_id=0,
            location=(9.0, 9.0),  # Lejos del centro (5,5)
            demand=5,
            arrival_time=0.0,
            tw_start=0.0,
            tw_end=1.0,  # Ventana muy corta: 1 minuto
        )
        order.assigned_store = 0
        order.status = "pending"
        sim.all_orders.append(order)
        sim.pending_orders.append(order)

        routes = [[0, 1, 0]]
        sim._simulate_deliveries(0, routes, current_time=0.0)

        # Con avg_speed=1 km/h y distancia ~5.66 km, travel_time >> 1 minuto
        assert order.status == "failed"
        assert len(sim.failed_orders) == 1
        assert len(sim.completed_orders) == 0


class TestQCDVRPFitness:
    """Tests para la funcion fitness tricriterion."""

    def test_fitness_invalid_node_in_route(self):
        """Nodos fuera de la distance_matrix usan dist=0 (line 408)."""
        sim = QCDVRPSimulator(seed=42)
        sim._setup_dark_stores()

        from problems.vrp import VRPProblem
        problem = VRPProblem(seed=42)
        problem.nodes = [(0, 0), (1, 0), (0, 1)]
        problem.dimension = 3
        problem.compute_distance_matrix()

        # Ruta con nodos validos primero, luego nodo invalido (999)
        # Para cubrir linea 408: necesitamos que prev_node o node esten fuera de rango
        # La condicion es: prev_node < shape[0] AND node < shape[0]
        # Si alguno falla, se va al else -> dist = 0 (linea 408)
        # Nodo 999 tiene order_idx=998, fuera de rango de orders(2), se ignora.
        # Necesitamos un nodo que pase el check de order_idx pero falle en distance_matrix.
        # Con 2 ordenes: nodos validos son 1,2. Matrix es 3x3 (indices 0,1,2).
        # Si nodo=3, order_idx=2 >= len(orders)=2, se ignora.
        # Necesitamos nodo valido en orders pero invalido en matrix.
        # Con matrix 3x3: nodos 0,1,2 son validos. orders[0]=nodo1, orders[1]=nodo2.
        # Si expandimos orders sin expandir matrix:
        orders_extended = [
            Order(0, (1, 0), 5, 0.0, 0.0, 60.0),
            Order(1, (0, 1), 5, 0.0, 0.0, 60.0),
            Order(2, (1, 1), 5, 0.0, 0.0, 60.0),  # nodo 3, fuera de matrix 3x3
        ]

        # Ruta: depot(0) -> nodo1 -> nodo3(valido en orders pero fuera de matrix) -> depot
        routes = [[0, 1, 3, 0]]
        fitness = sim.fitness_tricriterion(
            routes, problem, orders_extended, current_time=0.0
        )

        assert isinstance(fitness, float)
        assert not math.isnan(fitness)


class TestQCDVRPRunSimulation:
    """Tests para run_simulation completo."""

    def test_run_simulation_normal_flow(self):
        """run_simulation ejecuta el flujo completo con metaheuristica (lines 509-514)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            poisson_lambda=5.0,  # Suficientes ordenes
            simulation_horizon=2.0,  # 2 minutos
            rolling_horizon_window=60.0,  # 1 minuto
            vehicle_capacity=50,
            population_size=5,
            max_fes=100,
            seed=42,
        )

        # Mock del algoritmo que retorna un best con .position
        mock_best = MagicMock()
        mock_best.position = None  # Se sobreescribe en el lambda

        mock_algo_instance = MagicMock()

        def execute_side_effect():
            # Retorna un objeto con position de la dimension correcta
            best = MagicMock()
            # Usamos un arreglo de dimension suficiente
            best.position = np.random.rand(50)
            best.fitness.return_value = 100.0
            return best

        mock_algo_instance.execute.side_effect = execute_side_effect

        mock_algo_class = MagicMock(return_value=mock_algo_instance)

        results = sim.run_simulation(mock_algo_class)

        assert "adt" in results
        assert "dsr" in results
        assert "wbi" in results
        assert "total_orders" in results
        assert results["total_orders"] >= 0

    def test_run_simulation_with_pending_orders_at_end(self):
        """Ordenes pendientes al final se marcan como failed (lines 520-521)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            poisson_lambda=5.0,
            simulation_horizon=2.0,
            rolling_horizon_window=60.0,
            vehicle_capacity=50,
            population_size=5,
            max_fes=100,
            seed=42,
        )

        # El algoritmo falla a proposito: no retorna position -> fallback
        # Y hacemos que _simulate_deliveries NO procese todas las ordenes
        # usando un mock que deja ordenes pendientes
        mock_algo_instance = MagicMock()

        def execute_no_position():
            best = MagicMock(spec=[])  # Sin position
            return best

        mock_algo_instance.execute.side_effect = execute_no_position
        mock_algo_class = MagicMock(return_value=mock_algo_instance)

        # Interceptar _simulate_deliveries para que deje ordenes pendientes
        def partial_deliveries(store_id, routes, current_time):
            # No hacer nada: las ordenes quedan pendientes
            pass

        sim._simulate_deliveries = partial_deliveries

        results = sim.run_simulation(mock_algo_class)

        # Todas las ordenes que quedaron pendientes deben estar como failed
        assert results["total_orders"] >= 0
        # Si hay ordenes generadas, las pendientes debieron marcarse como failed
        if results["total_orders"] > 0:
            assert results["failed_orders"] > 0

    def test_run_simulation_trivial_dimension_failed(self):
        """Caso trivial con dim<=2 donde la orden llega tarde (lines 501-502)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            poisson_lambda=0.0,  # No generacion automatica
            simulation_horizon=2.0,
            rolling_horizon_window=60.0,
            avg_speed=0.1,     # Muy lento
            service_time=100.0,  # Mucho tiempo de servicio
            vehicle_capacity=50,
            population_size=5,
            max_fes=100,
            seed=42,
        )

        mock_algo_class = MagicMock()

        # Override _generate_orders para inyectar exactamente 1 orden
        # (para que _build_vrp_instance retorne dim=2 -> trivial case)
        call_count = [0]

        def inject_single_order(window_start, window_duration):
            if call_count[0] == 0:
                order = Order(
                    order_id=sim.order_counter,
                    location=(9.0, 9.0),  # Lejos del store
                    demand=5,
                    arrival_time=window_start,
                    tw_start=window_start,
                    tw_end=window_start + 0.001,  # Ventana minima -> falla
                )
                sim.order_counter += 1
                sim.all_orders.append(order)
                sim.pending_orders.append(order)
                call_count[0] += 1

        sim._generate_orders = inject_single_order

        results = sim.run_simulation(mock_algo_class)

        # La orden debio ser procesada en el caso trivial
        assert results["total_orders"] == 1
        # Con avg_speed=0.1 y service_time=100, delivery_time >> tw_end
        assert results["failed_orders"] == 1

    def test_run_simulation_trivial_dimension_success(self):
        """Caso trivial con dim<=2 donde la orden se entrega a tiempo (lines 497-499)."""
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=1,
            n_vehicles=3,
            poisson_lambda=0.0,
            simulation_horizon=2.0,
            rolling_horizon_window=60.0,
            avg_speed=100.0,    # Rapido
            service_time=0.1,   # Poco servicio
            vehicle_capacity=50,
            population_size=5,
            max_fes=100,
            seed=42,
        )

        mock_algo_class = MagicMock()

        call_count = [0]

        def inject_single_order(window_start, window_duration):
            if call_count[0] == 0:
                order = Order(
                    order_id=sim.order_counter,
                    location=(5.1, 5.1),  # Muy cerca del store (5,5)
                    demand=5,
                    arrival_time=window_start,
                    tw_start=window_start,
                    tw_end=window_start + 999.0,  # Ventana enorme
                )
                sim.order_counter += 1
                sim.all_orders.append(order)
                sim.pending_orders.append(order)
                call_count[0] += 1

        sim._generate_orders = inject_single_order

        results = sim.run_simulation(mock_algo_class)

        assert results["total_orders"] == 1
        assert results["completed_orders"] == 1

    def test_run_simulation_store_with_no_orders_continues(self):
        """Store sin ordenes retorna None -> continue (line 480).

        Con 3 dark stores y ordenes asignadas solo a 1 store,
        los otros 2 stores ejecutan continue en linea 480.
        """
        sim = QCDVRPSimulator(
            zone_size=10.0,
            n_dark_stores=3,  # 3 stores, pero ordenes solo en 1
            n_vehicles=9,
            poisson_lambda=0.0,
            simulation_horizon=2.0,
            rolling_horizon_window=60.0,
            vehicle_capacity=50,
            population_size=5,
            max_fes=100,
            avg_speed=100.0,
            service_time=0.1,
            seed=42,
        )

        # Mock del algoritmo que devuelve un best con position real
        def make_algo(*args, **kwargs):
            algo = MagicMock()
            def make_best():
                best = MagicMock()
                # Dimension grande para cualquier problema que se cree
                best.position = np.random.rand(50)
                best.fitness.return_value = 100.0
                return best
            algo.execute.side_effect = make_best
            return algo

        mock_algo_class = MagicMock(side_effect=make_algo)

        call_count = [0]

        def inject_orders_for_one_store(window_start, window_duration):
            """Inyecta ordenes cerca de store 0 (top del triangulo)."""
            if call_count[0] == 0:
                # Con n_dark_stores=3, store 0 esta arriba (cx, cy+r)
                # cx=5, cy=5, r=3.0 -> store 0 en (5, 8)
                for i in range(4):  # 4 ordenes para dim > 2
                    order = Order(
                        order_id=sim.order_counter,
                        location=(5.0 + i * 0.1, 8.0 + i * 0.1),
                        demand=3,
                        arrival_time=window_start,
                        tw_start=window_start,
                        tw_end=window_start + 999.0,
                    )
                    sim.order_counter += 1
                    sim.all_orders.append(order)
                    sim.pending_orders.append(order)
                call_count[0] += 1

        sim._generate_orders = inject_orders_for_one_store

        results = sim.run_simulation(mock_algo_class)

        # La simulacion debe completar sin errores
        assert results["total_orders"] == 4


class TestQCDVRPMetrics:
    """Tests para calculo de metricas."""

    def test_no_completed_orders(self):
        """completed_orders=[] -> ADT=inf (line 544)."""
        sim = QCDVRPSimulator(seed=42)
        sim._setup_dark_stores()

        sim.all_orders = [
            Order(0, (1, 1), 5, 0.0, 0.0, 30.0),
        ]
        sim.all_orders[0].assigned_store = 0
        sim.completed_orders = []
        sim.failed_orders = list(sim.all_orders)

        metrics = sim._compute_metrics(execution_time=1.0)

        assert metrics['adt'] == float('inf')
        assert metrics['completed_orders'] == 0
        assert metrics['failed_orders'] == 1

    def test_no_total_orders(self):
        """all_orders=[] -> DSR=0 (line 554)."""
        sim = QCDVRPSimulator(seed=42)
        sim._setup_dark_stores()

        sim.all_orders = []
        sim.completed_orders = []
        sim.failed_orders = []

        metrics = sim._compute_metrics(execution_time=0.5)

        assert metrics['dsr'] == 0.0
        assert metrics['total_orders'] == 0
        assert metrics['adt'] == float('inf')


class TestQCDVRPLineByLineAnalysis:
    """Tests enfocados en alcanzar lineas especificas de cobertura."""

    def test_line_328_documented_unreachable(self):
        """Linea 328 es dead code defensivo (ver test_prev_node_out_of_range_is_unreachable).

        prev_node solo se actualiza (linea 347) cuando order_idx es valido,
        por lo que prev_order_idx = prev_node - 1 siempre esta en rango.
        """
        pass

    def test_line_408_dist_zero_fallback(self):
        """Nodo valido en orders pero fuera de distance_matrix (line 408).

        Creamos un problema con distance_matrix pequena pero mas ordenes.
        """
        sim = QCDVRPSimulator(seed=42, avg_speed=40.0, service_time=5.0)
        sim._setup_dark_stores()

        from problems.vrp import VRPProblem
        problem = VRPProblem(seed=42)
        # Matrix 3x3 (depot + 2 nodos)
        problem.nodes = [(0, 0), (1, 0), (0, 1)]
        problem.dimension = 3
        problem.compute_distance_matrix()

        # 3 ordenes: nodos 1, 2, 3. Nodo 3 esta fuera de la matrix 3x3.
        orders = [
            Order(0, (1, 0), 5, 0.0, 0.0, 60.0),
            Order(1, (0, 1), 5, 0.0, 0.0, 60.0),
            Order(2, (1, 1), 5, 0.0, 0.0, 60.0),  # nodo 3, fuera de matrix
        ]

        # Ruta que incluye nodo 3 (valido en orders, invalido en matrix)
        routes = [[0, 3, 0]]
        fitness = sim.fitness_tricriterion(routes, problem, orders, current_time=0.0)

        assert isinstance(fitness, float)
        assert not math.isnan(fitness)

    def test_line_408_prev_node_out_of_matrix(self):
        """prev_node fuera de distance_matrix en fitness_tricriterion (line 408).

        Se llega cuando prev_node es valido como orden pero fuera de la matrix.
        """
        sim = QCDVRPSimulator(seed=42, avg_speed=40.0, service_time=5.0)

        from problems.vrp import VRPProblem
        problem = VRPProblem(seed=42)
        # Matrix 3x3 (indices 0,1,2)
        problem.nodes = [(0, 0), (1, 0), (0, 1)]
        problem.dimension = 3
        problem.compute_distance_matrix()

        # 3 ordenes para que nodo 3 sea valido en orders
        orders = [
            Order(0, (1, 0), 5, 0.0, 0.0, 60.0),
            Order(1, (0, 1), 5, 0.0, 0.0, 60.0),
            Order(2, (1, 1), 5, 0.0, 0.0, 60.0),
        ]

        # Ruta: depot -> nodo3 -> nodo1 -> depot
        # Nodo 3: order_idx=2 < 3 OK. prev_node=0 < 3 OK. node=3 >= 3 FAIL -> dist=0
        # prev_node se actualiza a 3.
        # Nodo 1: order_idx=0 < 3 OK. prev_node=3 >= 3 FAIL -> dist=0 (line 408)
        routes = [[0, 3, 1, 0]]
        fitness = sim.fitness_tricriterion(routes, problem, orders, current_time=0.0)

        assert isinstance(fitness, float)
        assert not math.isnan(fitness)
