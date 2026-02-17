<<<<<<< HEAD
"""
Backward compatibility module for VRPProblem.
This module exports the VRPProblemV2 class as VRPProblem for backward compatibility.
"""
=======
import numpy as np
import pandas as pd
import math
import os
from typing import List, Tuple, Dict, Set, Union, Optional, Any, cast
from collections import Counter
>>>>>>> develop

from .vrp_v2 import VRPProblemV2 as VRPProblem

<<<<<<< HEAD
__all__ = ['VRPProblem']
=======

class VRPProblem:
    """Clase para representar y evaluar problemas de VRP (Vehicle Routing Problem).

    Extiende a QC-DVRP (Quick Commerce Dynamic VRP) con:
    - Multi-depósito (dark stores)
    - Demandas dinámicas con llegadas Poisson
    - Optimización multiobjetivo (tiempo, variabilidad carga, distancia)
    - Estrategias de defensa grupal inspiradas en HO (Amiri et al., 2024)
    """

    def __init__(
        self,
        instance_path: str = None,
        depots: List[Tuple[float, float]] = None,
        dynamic_lambda: float = 5.0,
        seed: int = 42,
    ) -> None:
        """
        Inicializa el problema VRP con extensiones QC-DVRP.

        Args:
            instance_path: Ruta al archivo de instancia VRP (opcional)
            depots: Lista de coordenadas de dark stores [(x1,y1), (x2,y2), ...]
            dynamic_lambda: Parámetro λ para llegadas Poisson (órdenes/hora)
            seed: Semilla para reproducibilidad
        """
        # Reproducibilidad con generador local
        self.seed = seed
        self.rng = np.random.RandomState(seed)

        self.instance_path: str = instance_path
        self.name: Optional[str] = None
        self.dimension: int = 0
        self.capacity: int = 0
        self.depot_index: int = 0
        self.nodes: List[
            Tuple[float, float]
        ] = []  # Lista de coordenadas (x, y) de cada nodo
        self.demands: List[int] = []  # Demanda de cada nodo
        self.distance_matrix: Optional[np.ndarray] = None
        self.penalty_factor: float = (
            PENALTY_FACTOR  # Factor de penalización para rutas no factibles
        )

        # QC-DVRP extensions
        self.depots = depots if depots else [(0, 0)]  # Multi dark stores
        self.dynamic_lambda = dynamic_lambda  # Poisson arrival rate
        self.dynamic_orders: List[Dict[str, Any]] = []  # Órdenes dinámicas
        self.current_time = 0.0  # Tiempo simulado
        self.service_time = 5.0  # Minutos por entrega
        self.avg_speed = 40.0  # km/h velocidad promedio

        # Only load instance if path is provided
        if self.instance_path:
            self.load_instance()
            self.compute_distance_matrix()

    def _parse_instance_metadata(self, lines):
        """Parse instance metadata from file lines."""
        metadata = {}
        for line in lines:
            if line.startswith("NAME"):
                metadata["name"] = line.split(":")[1].strip()
            elif line.startswith("TYPE"):
                metadata["type"] = line.split(":")[1].strip()
            elif line.startswith("DIMENSION"):
                metadata["dimension"] = int(line.split(":")[1].strip())
            elif line.startswith("CAPACITY"):
                metadata["capacity"] = int(line.split(":")[1].strip())
        return metadata

    def _parse_node_coordinates(self, lines):
        """Parse node coordinates section."""
        coordinates = []
        in_coord_section = False

        for line in lines:
            if line == "NODE_COORD_SECTION":
                in_coord_section = True
            elif line == "DEMAND_SECTION":
                in_coord_section = False
            elif (
                in_coord_section
                and line
                and not line.startswith(("EDGE_WEIGHT_TYPE", "EOF"))
            ):
                parts = line.split()
                if len(parts) >= 3:
                    coordinates.append(
                        {
                            "id": int(parts[0]),
                            "x": float(parts[1]),
                            "y": float(parts[2]),
                        }
                    )

        return coordinates

    def _parse_demands(self, lines):
        """Parse demand section."""
        demands = {}
        in_demand_section = False

        for line in lines:
            if line == "DEMAND_SECTION":
                in_demand_section = True
            elif line in ["DEPOT_SECTION", "EOF"]:
                in_demand_section = False
            elif in_demand_section and line:
                parts = line.split()
                if len(parts) >= 2:
                    demands[int(parts[0])] = int(parts[1])

        return demands

    def _validate_instance_data(self, metadata, coordinates, demands):
        """Validate parsed instance data."""
        if "dimension" not in metadata:
            raise ValueError("DIMENSION not found in instance file")

        if "capacity" not in metadata:
            raise ValueError("CAPACITY not found in instance file")

        if len(coordinates) != metadata["dimension"]:
            raise ValueError(
                f"Expected {metadata['dimension']} nodes, found {len(coordinates)}"
            )

        if len(demands) != metadata["dimension"]:
            raise ValueError(
                f"Expected {metadata['dimension']} demands, found {len(demands)}"
            )

        return True

    def _build_instance_data(self, metadata, coordinates, demands):
        """Build instance data structures."""
        # Sort coordinates by node ID
        coordinates.sort(key=lambda x: x["id"])

        # Build arrays
        nodes = [(c["x"], c["y"]) for c in coordinates]
        demand_array = [demands.get(i, 0) for i in range(1, metadata["dimension"] + 1)]

        return {
            "nodes": nodes,
            "demands": demand_array,
            "capacity": metadata["capacity"],
            "dimension": metadata["dimension"],
        }

    def load_instance(self, instance_name: str = None) -> None:
        """
        Carga una instancia de VRP desde el archivo.

        Args:
            instance_name: Nombre de la instancia (e.g., 'P-n16-k8'). Si se proporciona,
                          busca el archivo en el directorio data/

        Versión refactorizada que reduce la complejidad de 16 a menos de 10.
        """
        # If instance_name is provided, build the path
        if instance_name:
            self.instance_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "vrp",
                f"{instance_name}.vrp",
            )

        # Read file
        with open(self.instance_path, "r") as f:
            content = f.read()

        # Split into lines and clean
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        # Parse sections
        metadata = self._parse_instance_metadata(lines)
        coordinates = self._parse_node_coordinates(lines)
        demands = self._parse_demands(lines)

        # Validate data
        self._validate_instance_data(metadata, coordinates, demands)

        # Build instance data
        instance_data = self._build_instance_data(metadata, coordinates, demands)

        # Update class attributes
        self.nodes = instance_data["nodes"]
        self.demands = instance_data["demands"]
        self.capacity = instance_data["capacity"]
        self.dimension = instance_data["dimension"]

        # Extract instance name
        self.name = metadata.get(
            "name", os.path.basename(self.instance_path).split(".")[0]
        )

        # Compute distance matrix after loading
        self.compute_distance_matrix()

    def compute_distance_matrix(self) -> None:
        """Calcula la matriz de distancias entre todos los nodos."""
        n = len(self.nodes)
        self.distance_matrix = np.zeros((n, n))

        try:
            # Intenta usar scipy.spatial.distance.cdist si está disponible
            from scipy.spatial import distance

            # Extraer coordenadas x e y para todos los nodos
            coords = np.array(self.nodes)

            # Calcular matriz de distancias euclidiana
            self.distance_matrix = distance.cdist(coords, coords, metric="euclidean")
        except ImportError:
            # Fallback al método de doble bucle
            for i in range(n):
                for j in range(n):
                    if i != j:
                        x1, y1 = self.nodes[i]
                        x2, y2 = self.nodes[j]
                        # Distancia euclidiana
                        self.distance_matrix[i, j] = math.sqrt(
                            (x2 - x1) ** 2 + (y2 - y1) ** 2
                        )

    def decode_solution(
        self, solution: np.ndarray
    ) -> Tuple[List[List[int]], float, bool]:
        """
        Decodifica una solución continua en una solución VRP.

        Args:
            solution: Vector de valores continuos

        Returns:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)
            total_distance: Distancia total recorrida
            is_feasible: Si la solución respeta las restricciones de capacidad
        """
        # Convertir solución continua a permutación (excluyendo el depósito)
        indices = list(range(1, self.dimension))  # Excluir el depósito (índice 0)
        indices.sort(
            key=lambda i: solution[i - 1]
        )  # Ordenar por valores de la solución

        routes: List[List[int]] = []
        current_route: List[int] = [self.depot_index]
        current_load: int = 0
        total_distance: float = 0.0

        for idx in indices:
            # Si agregar el siguiente nodo excede la capacidad, iniciar nueva ruta
            if current_load + self.demands[idx] > self.capacity:
                # Cerrar la ruta actual volviendo al depósito
                current_route.append(self.depot_index)
                routes.append(current_route)

                # Calcular distancia de la ruta actual
                for i in range(len(current_route) - 1):
                    total_distance += self.distance_matrix[
                        current_route[i], current_route[i + 1]
                    ]

                # Iniciar nueva ruta
                current_route = [self.depot_index, idx]
                current_load = self.demands[idx]
            else:
                # Agregar nodo a la ruta actual
                current_route.append(idx)
                current_load += self.demands[idx]

        # Cerrar la última ruta
        if len(current_route) > 1:
            current_route.append(self.depot_index)
            routes.append(current_route)

            # Calcular distancia de la última ruta
            for i in range(len(current_route) - 1):
                total_distance += self.distance_matrix[
                    current_route[i], current_route[i + 1]
                ]

        return routes, total_distance, True

    def evaluate(self, solution: Union[np.ndarray, List[List[int]]]) -> float:
        """
        Evalúa una solución y retorna su fitness.

        Args:
            solution: Vector de valores continuos o lista de rutas

        Returns:
            fitness: Valor de fitness (menor es mejor)
        """
        # Si es una lista de rutas, usar evaluación directa
        if (
            isinstance(solution, list)
            and len(solution) > 0
            and isinstance(solution[0], list)
        ):
            return self.evaluate_routes(solution)

        # Si es un vector continuo, decodificar y evaluar
        routes, total_distance, is_feasible = self.decode_solution(solution)
        return total_distance

    def evaluate_routes(self, routes: List[List[int]]) -> float:
        """
        Evalúa directamente una solución de rutas.

        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)

        Returns:
            fitness: Valor de fitness (menor es mejor)
        """
        total_distance: float = 0.0
        penalty: float = 0.0

        # Obtener detalles de penalización pero ignorar lista de errores
        total_distance, penalties_dict, _ = self.evaluate_routes_detailed(routes)

        # Sumar todas las penalizaciones
        for penalty_value in penalties_dict.values():
            penalty += penalty_value

        return total_distance + penalty

    def evaluate_routes_detailed(
        self, routes: List[List[int]]
    ) -> Tuple[float, Dict[str, float], List[str]]:
        """
        Evalúa directamente una solución de rutas con detalles de penalización.

        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)

        Returns:
            total_distance: Distancia total recorrida
            penalties: Diccionario con los valores de cada tipo de penalización
            error_messages: Lista de mensajes de error explicativos
        """
        total_distance: float = 0.0
        penalties: Dict[str, float] = {
            "capacity": 0.0,
            "missing": 0.0,
            "duplicate": 0.0,
        }
        error_messages: List[str] = []

        for route_idx, route in enumerate(routes):
            # Calcular distancia de la ruta
            route_distance = 0.0
            for i in range(len(route) - 1):
                route_distance += self.distance_matrix[route[i], route[i + 1]]
            total_distance += route_distance

            # Calcular carga y verificar factibilidad
            route_load = 0
            for node in route[1:-1]:  # Excluir depósito al inicio y fin
                route_load += self.demands[node]

            # Aplicar penalización si excede capacidad
            if route_load > self.capacity:
                excess = route_load - self.capacity
                penalty = excess * PENALTY_CAP
                penalties["capacity"] += penalty
                error_messages.append(
                    f"Ruta {route_idx+1} excede capacidad: {route_load} > {self.capacity} (penalización: {penalty})"
                )

        # Verificar que todos los clientes están cubiertos
        covered_nodes = set()
        all_nodes = []
        for route in routes:
            route_nodes = route[1:-1]  # Excluir depósito
            all_nodes.extend(route_nodes)
            for node in route_nodes:
                covered_nodes.add(node)

        required_nodes = set(range(1, self.dimension))  # Todos excepto depósito
        missing_nodes = required_nodes - covered_nodes

        # Aplicar penalización por nodos faltantes
        if missing_nodes:
            penalty = len(missing_nodes) * PENALTY_MISSING
            penalties["missing"] += penalty
            error_messages.append(
                f"Nodos faltantes: {sorted(missing_nodes)} (penalización: {penalty})"
            )

        # Verificar duplicados
        node_counts = Counter(all_nodes)
        duplicates = {node: count for node, count in node_counts.items() if count > 1}

        if duplicates:
            penalty = sum(count - 1 for count in duplicates.values()) * PENALTY_MISSING
            penalties["duplicate"] += penalty
            error_messages.append(
                f"Nodos duplicados: {duplicates} (penalización: {penalty})"
            )

        return total_distance, penalties, error_messages

    def routes_are_feasible(self, routes: List[List[int]]) -> Tuple[bool, List[str]]:
        """
        Verifica si una solución de rutas es factible.

        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)

        Returns:
            tuple: (es_factible, mensajes_error)
                   - es_factible: True si las rutas son factibles, False en caso contrario
                   - mensajes_error: Lista de mensajes describiendo los errores encontrados
        """
        is_feasible = True
        error_messages: List[str] = []

        # Verificar que todas las rutas respetan la capacidad
        for route_idx, route in enumerate(routes):
            route_load = 0
            for node in route[1:-1]:  # Excluir depósito al inicio y fin
                route_load += self.demands[node]

            if route_load > self.capacity:
                is_feasible = False
                error_messages.append(
                    f"Ruta {route_idx+1} excede capacidad: {route_load} > {self.capacity}"
                )

        # Verificar que todos los clientes están cubiertos
        covered_nodes = set()
        all_nodes = []
        for route in routes:
            route_nodes = route[1:-1]  # Excluir depósito
            all_nodes.extend(route_nodes)
            for node in route_nodes:
                covered_nodes.add(node)

        required_nodes = set(range(1, self.dimension))  # Todos excepto depósito
        missing_nodes = required_nodes - covered_nodes

        if missing_nodes:
            is_feasible = False
            error_messages.append(f"Nodos faltantes: {sorted(missing_nodes)}")

        # Verificar duplicados (un nodo no debe aparecer en múltiples rutas)
        node_counts = Counter(all_nodes)
        duplicates = {node: count for node, count in node_counts.items() if count > 1}

        if duplicates:
            is_feasible = False
            error_messages.append(f"Nodos duplicados: {duplicates}")

        return is_feasible, error_messages

    def get_dimension(self) -> int:
        """Retorna la dimensión del problema (número de nodos)."""
        return self.dimension - 1  # Excluir el depósito

    def update_demand(
        self, new_orders: List[Dict[str, Any]], current_time: float = None
    ) -> None:
        """
        Actualiza demandas con nuevas órdenes dinámicas siguiendo distribución Poisson.

        Args:
            new_orders: Lista de órdenes con formato [{'coord': (x,y), 'demand': int, 'time': float}]
            current_time: Tiempo actual de simulación

        Referencias:
            - Amiri et al. (2024): Fase de defensa grupal para balanceo de carga
        """
        if current_time is not None:
            self.current_time = current_time

        # Generar llegadas Poisson si no se especifican órdenes
        if not new_orders:
            # Número de nuevas órdenes ~ Poisson(λ)
            num_orders = self.rng.poisson(self.dynamic_lambda)
            new_orders = []

            for _ in range(num_orders):
                # Generar ubicación aleatoria en área de servicio
                x = self.rng.uniform(-50, 50)
                y = self.rng.uniform(-50, 50)
                # Asegurar que tenemos capacidad válida
                max_demand = min(20, self.capacity // 3) if self.capacity > 3 else 10
                demand = self.rng.randint(1, max(2, max_demand))

                new_orders.append(
                    {
                        "coord": (x, y),
                        "demand": demand,
                        "time": self.current_time,
                        "order_id": f"DYN_{self.current_time}_{len(self.dynamic_orders)}",
                    }
                )

        # Añadir nuevas órdenes
        for order in new_orders:
            # Añadir nodo dinámico
            self.nodes.append(order["coord"])
            self.demands.append(order["demand"])
            self.dynamic_orders.append(order)
            self.dimension += 1

        # Recomputar matriz de distancias si hay nuevos nodos
        if new_orders:
            self.compute_distance_matrix()

    def evaluate_multi(
        self, solution: Union[np.ndarray, List[List[int]]]
    ) -> Tuple[float, float, float]:
        """
        Evaluación multiobjetivo para QC-DVRP.

        Returns:
            Tuple de (tiempo_promedio_entrega, coef_variacion_carga, distancia_total)

        Objetivos:
            1. Minimizar tiempo promedio de entrega (minutos)
            2. Minimizar coeficiente de variación de carga (equilibrio entre vehículos)
            3. Minimizar distancia total (km)
        """
        # Decodificar si es necesario
        if isinstance(solution, np.ndarray):
            routes, _, _ = self.decode_solution(solution)
        else:
            routes = solution

        # Calcular distancia total
        total_distance = 0.0
        route_distances = []
        route_loads = []
        delivery_times = []

        for route in routes:
            if len(route) < 3:  # Ruta vacía o inválida
                continue

            # Distancia de la ruta
            route_dist = 0.0
            for i in range(len(route) - 1):
                node_a, node_b = route[i], route[i + 1]
                # Validar que los índices estén dentro del rango
                if (
                    node_a >= self.distance_matrix.shape[0]
                    or node_b >= self.distance_matrix.shape[0]
                    or node_a < 0
                    or node_b < 0
                ):
                    # Nodos inválidos, aplicar penalización
                    route_dist += 1000.0
                else:
                    route_dist += self.distance_matrix[node_a, node_b]

            route_distances.append(route_dist)
            total_distance += route_dist

            # Carga de la ruta
            route_load = 0
            for node in route[1:-1]:  # Excluir depósitos
                if 0 <= node < len(self.demands):
                    route_load += self.demands[node]
            route_loads.append(route_load)

            # Tiempo de entrega (distancia/velocidad + tiempo servicio)
            travel_time = (route_dist / self.avg_speed) * 60  # minutos
            service_time = len(route[1:-1]) * self.service_time
            total_time = travel_time + service_time

            # Tiempo promedio por cliente en la ruta
            if len(route) > 2:
                avg_time = total_time / len(route[1:-1])
                delivery_times.extend([avg_time] * len(route[1:-1]))

        # Calcular métricas
        tiempo_promedio = np.mean(delivery_times) if delivery_times else float("inf")

        # Coeficiente de variación de carga (inspirado en defensa grupal HO)
        if route_loads and np.mean(route_loads) > 0:
            coef_variacion = np.std(route_loads) / np.mean(route_loads)
        else:
            # No loads or all loads are zero - division by zero case
            coef_variacion = float("inf")

        return tiempo_promedio, coef_variacion, total_distance

    def dominates(
        self, sol1: Tuple[float, float, float], sol2: Tuple[float, float, float]
    ) -> bool:
        """
        Verifica dominancia de Pareto entre dos soluciones.

        Args:
            sol1: Tupla (tiempo, coef_var, distancia) de solución 1
            sol2: Tupla (tiempo, coef_var, distancia) de solución 2

        Returns:
            True si sol1 domina a sol2
        """
        # sol1 domina a sol2 si es mejor o igual en todos los objetivos
        # y estrictamente mejor en al menos uno
        better_or_equal = all(s1 <= s2 for s1, s2 in zip(sol1, sol2))
        strictly_better = any(s1 < s2 for s1, s2 in zip(sol1, sol2))

        return better_or_equal and strictly_better

    def apply_evasion_strategy(
        self, routes: List[List[int]], delay_threshold: float = 30.0
    ) -> List[List[int]]:
        """
        Aplica estrategia de evasión inspirada en HO cuando hay retrasos.
        Usa operador relocate para re-rutear clientes críticos.

        Args:
            routes: Rutas actuales
            delay_threshold: Umbral de retraso en minutos

        Referencias:
            - Amiri et al. (2024): X_i^{t+1} = X_i^t + γ*Levy()*perturbation
        """
        # Calcular tiempos de entrega actuales
        route_times = []
        for route in routes:
            if len(route) > 2:
                route_dist = sum(
                    self.distance_matrix[route[i], route[i + 1]]
                    for i in range(len(route) - 1)
                )
                travel_time = (route_dist / self.avg_speed) * 60
                service_time = len(route[1:-1]) * self.service_time
                route_times.append(travel_time + service_time)
            else:
                route_times.append(0)

        # Identificar rutas con retraso
        delayed_routes = [i for i, t in enumerate(route_times) if t > delay_threshold]

        if not delayed_routes:
            return routes

        # Aplicar perturbación tipo Levy (simplificada como relocate)
        new_routes = [route[:] for route in routes]

        for route_idx in delayed_routes:
            if len(new_routes[route_idx]) <= 2:
                continue

            # Seleccionar cliente aleatorio para reubicar
            route = new_routes[route_idx]
            customer_idx = self.rng.randint(1, len(route) - 1)
            customer = route.pop(customer_idx)

            # Encontrar mejor posición en otra ruta (γ factor de perturbación)
            best_route = None
            best_pos = None
            best_increase = float("inf")

            for r_idx, other_route in enumerate(new_routes):
                if r_idx == route_idx:
                    continue

                # Verificar capacidad
                route_load = sum(self.demands[n] for n in other_route[1:-1])
                if route_load + self.demands[customer] > self.capacity:
                    continue

                # Encontrar mejor posición de inserción
                for pos in range(1, len(other_route)):
                    dist_increase = (
                        self.distance_matrix[other_route[pos - 1], customer]
                        + self.distance_matrix[customer, other_route[pos]]
                        - self.distance_matrix[other_route[pos - 1], other_route[pos]]
                    )

                    if dist_increase < best_increase:
                        best_increase = dist_increase
                        best_route = r_idx
                        best_pos = pos

            # Aplicar mejor movimiento
            if best_route is not None:
                new_routes[best_route].insert(best_pos, customer)
            else:
                # Si no hay mejor opción, devolver cliente a ruta original
                new_routes[route_idx].insert(customer_idx, customer)

        return new_routes

    def random_solution(self, rng=None) -> np.ndarray:
        """
        Genera una solución aleatoria para el problema VRP.

        Args:
            rng: NumPy random generator instance (uses default if None)

        Returns:
            solution: Vector de valores continuos aleatorios en el rango [0,1]
        """
        if rng is None:
            rng = np.random.default_rng()
        dim = self.get_dimension()
        return rng.random(dim)

    def random_routes(self, rng=None) -> List[List[int]]:
        """
        Genera una solución aleatoria en forma de rutas para el problema VRP.
        Usa una estrategia de construcción simplificada tipo Clarke-Wright.

        Args:
            rng: NumPy random generator instance (uses default if None)

        Returns:
            routes: Lista de rutas que respetan restricciones de capacidad
        """
        if rng is None:
            rng = np.random.default_rng()
        depot = self.depot_index
        customers = list(range(1, self.dimension))
        rng.shuffle(customers)

        routes: List[List[int]] = []
        current_route: List[int] = [depot]
        current_load: int = 0

        for customer in customers:
            # Si agregar el cliente excede capacidad, cerrar ruta y comenzar nueva
            if current_load + self.demands[customer] > self.capacity:
                current_route.append(depot)  # Cerrar ruta volviendo al depósito
                routes.append(current_route)

                # Iniciar nueva ruta
                current_route = [depot, customer]
                current_load = self.demands[customer]
            else:
                # Agregar cliente a la ruta actual
                current_route.append(customer)
                current_load += self.demands[customer]

        # Cerrar última ruta
        if len(current_route) > 1:
            current_route.append(depot)
            routes.append(current_route)

        return routes

    def is_valid(self, solution: Union[np.ndarray, List[List[int]]]) -> bool:
        """
        Verifica si una solución es válida.
        Para VRP con representación de permutación, verificamos que sea un vector
        con valores dentro del rango [0,1]

        Args:
            solution: Vector de solución o lista de rutas a verificar

        Returns:
            bool: True si la solución es válida, False en caso contrario
        """
        # Si es una lista de rutas, verificar directamente
        if (
            isinstance(solution, list)
            and len(solution) > 0
            and isinstance(solution[0], list)
        ):
            is_feasible, _ = self.routes_are_feasible(cast(List[List[int]], solution))
            return is_feasible

        # En el contexto de VRP con permutación/prioridad, consideramos válido
        # cualquier vector de la dimensión correcta con valores entre 0 y 1
        if len(solution) != self.get_dimension():
            return False

        return np.all(solution >= 0) and np.all(solution <= 1)

    def repair_routes(self, routes: List[List[int]]) -> List[List[int]]:
        """
        Repara una solución de rutas para hacerla factible.

        Args:
            routes: Lista de rutas a reparar

        Returns:
            Lista de rutas reparadas
        """
        depot = self.depot_index

        # Paso 1: Recolectar todos los clientes de todas las rutas
        all_customers: List[int] = []
        for route in routes:
            for node in route:
                if node != depot:
                    all_customers.append(node)

        # Eliminar duplicados manteniendo el orden de aparición
        seen: Set[int] = set()
        unique_customers = [
            x for x in all_customers if x not in seen and not seen.add(x)
        ]

        # Paso 2: Verificar clientes faltantes
        required_customers = set(range(1, self.dimension))
        missing_customers = list(required_customers - set(unique_customers))

        # Paso 3: Crear nuevas rutas factibles
        new_routes: List[List[int]] = []
        current_route = [depot]
        current_load = 0

        # Agregar primero los clientes de las rutas originales (sin duplicados)
        for customer in unique_customers:
            if current_load + self.demands[customer] > self.capacity:
                # Cerrar ruta actual y comenzar nueva
                current_route.append(depot)
                new_routes.append(current_route)

                current_route = [depot, customer]
                current_load = self.demands[customer]
            else:
                current_route.append(customer)
                current_load += self.demands[customer]

        # Agregar clientes faltantes
        for customer in missing_customers:
            if current_load + self.demands[customer] > self.capacity:
                # Cerrar ruta actual y comenzar nueva
                current_route.append(depot)
                new_routes.append(current_route)

                current_route = [depot, customer]
                current_load = self.demands[customer]
            else:
                current_route.append(customer)
                current_load += self.demands[customer]

        # Cerrar última ruta
        if len(current_route) > 1:
            current_route.append(depot)
            new_routes.append(current_route)

        return new_routes

    def encode_routes(self, routes: List[List[int]]) -> np.ndarray:
        """
        Codifica una solución de rutas en un vector continuo.
        
        Este método implementa la transformación inversa de decode_solution,
        permitiendo convertir rutas modificadas (por operadores como swap,
        2-opt, etc.) de vuelta a la representación continua que usan los
        algoritmos metaheurísticos.
        
        Args:
            routes: Lista de rutas (cada ruta incluye depósito al inicio y fin)
            
        Returns:
            solution: Vector de valores continuos en [0,1] que al decodificar
                     produce las rutas dadas (o rutas equivalentes)
        """
        # Extraer la secuencia de clientes de las rutas
        customer_sequence = []
        for route in routes:
            # Excluir depósito (primer y último elemento)
            for customer in route[1:-1]:
                if customer != self.depot_index:
                    customer_sequence.append(customer)
        
        # Verificar que tenemos todos los clientes
        expected_customers = set(range(1, self.dimension))
        actual_customers = set(customer_sequence)
        
        # Agregar clientes faltantes al final
        missing_customers = list(expected_customers - actual_customers)
        customer_sequence.extend(missing_customers)
        
        # Crear vector de solución basado en el orden
        # Asignar valores de 0 a 1 según la posición en la secuencia
        solution = np.zeros(self.dimension - 1)  # Excluir depósito
        
        # Asignar valores incrementales basados en posición
        for position, customer in enumerate(customer_sequence):
            # customer-1 porque los índices del vector empiezan en 0
            # pero los clientes empiezan en 1
            if 1 <= customer < self.dimension:
                # Valor entre 0 y 1 basado en posición
                solution[customer - 1] = position / len(customer_sequence)
        
        return solution
>>>>>>> develop
