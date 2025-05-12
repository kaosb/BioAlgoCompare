import numpy as np
import pandas as pd
import math


class VRPProblem:
    """Clase para representar y evaluar problemas de VRP (Vehicle Routing Problem)."""

    def __init__(self, instance_path):
        """
        Inicializa el problema VRP desde un archivo de instancia.

        Args:
            instance_path: Ruta al archivo de instancia VRP
        """
        self.instance_path = instance_path
        self.name = None
        self.dimension = 0
        self.capacity = 0
        self.depot_index = 0
        self.nodes = []  # Lista de coordenadas (x, y) de cada nodo
        self.demands = []  # Demanda de cada nodo
        self.distance_matrix = None
        self.penalty_factor = 1000.0  # Factor de penalización para rutas no factibles

        self.load_instance()
        self.compute_distance_matrix()

    def load_instance(self):
        """Carga la instancia desde el archivo."""
        with open(self.instance_path, "r") as f:
            lines = f.readlines()

        # Parsear encabezado
        for line in lines:
            line = line.strip()
            if line.startswith("NAME"):
                self.name = line.split(":")[1].strip()
            elif line.startswith("DIMENSION"):
                self.dimension = int(line.split(":")[1].strip())
            elif line.startswith("CAPACITY"):
                self.capacity = int(line.split(":")[1].strip())
            elif line.startswith("NODE_COORD_SECTION"):
                break

        # Parsear coordenadas de nodos
        node_section = False
        demand_section = False

        for line in lines:
            line = line.strip()

            if line == "NODE_COORD_SECTION":
                node_section = True
                continue
            elif line == "DEMAND_SECTION":
                node_section = False
                demand_section = True
                continue
            elif line == "DEPOT_SECTION":
                demand_section = False
                continue
            elif line == "EOF":
                break

            if node_section:
                parts = line.split()
                if len(parts) >= 3:
                    node_id = int(parts[0]) - 1  # Convertir a índice base 0
                    x = float(parts[1])
                    y = float(parts[2])
                    self.nodes.append((x, y))

            if demand_section:
                parts = line.split()
                if len(parts) >= 2:
                    node_id = int(parts[0]) - 1  # Convertir a índice base 0
                    demand = int(parts[1])
                    self.demands.append(demand)
                    if demand == 0:
                        self.depot_index = node_id

    def compute_distance_matrix(self):
        """Calcula la matriz de distancias entre todos los nodos."""
        n = len(self.nodes)
        self.distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    x1, y1 = self.nodes[i]
                    x2, y2 = self.nodes[j]
                    # Distancia euclidiana
                    self.distance_matrix[i, j] = math.sqrt(
                        (x2 - x1) ** 2 + (y2 - y1) ** 2
                    )

    def decode_solution(self, solution):
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

        routes = []
        current_route = [self.depot_index]
        current_load = 0
        total_distance = 0

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

    def evaluate(self, solution):
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

    def evaluate_routes(self, routes):
        """
        Evalúa directamente una solución de rutas.

        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)

        Returns:
            fitness: Valor de fitness (menor es mejor)
        """
        total_distance = 0
        penalty = 0

        for route in routes:
            # Calcular distancia de la ruta
            route_distance = 0
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
                penalty += excess * self.penalty_factor

        # Verificar que todos los clientes están cubiertos
        covered_nodes = set()
        for route in routes:
            for node in route[1:-1]:  # Excluir depósito
                covered_nodes.add(node)

        required_nodes = set(range(1, self.dimension))  # Todos excepto depósito
        missing_nodes = required_nodes - covered_nodes

        # Aplicar penalización por nodos faltantes
        if missing_nodes:
            penalty += (
                len(missing_nodes) * self.penalty_factor * 10
            )  # Mayor penalización por nodos faltantes

        return total_distance + penalty

    def routes_are_feasible(self, routes):
        """
        Verifica si una solución de rutas es factible.

        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)

        Returns:
            bool: True si las rutas son factibles, False en caso contrario
        """
        # Verificar que todas las rutas respetan la capacidad
        for route in routes:
            route_load = 0
            for node in route[1:-1]:  # Excluir depósito al inicio y fin
                route_load += self.demands[node]

            if route_load > self.capacity:
                return False

        # Verificar que todos los clientes están cubiertos
        covered_nodes = set()
        for route in routes:
            for node in route[1:-1]:  # Excluir depósito
                covered_nodes.add(node)

        required_nodes = set(range(1, self.dimension))  # Todos excepto depósito
        missing_nodes = required_nodes - covered_nodes

        # Verificar duplicados (un nodo no debe aparecer en múltiples rutas)
        all_nodes = []
        for route in routes:
            all_nodes.extend(route[1:-1])  # Excluir depósito

        if len(all_nodes) != len(set(all_nodes)):
            return False

        return len(missing_nodes) == 0

    def get_dimension(self):
        """Retorna la dimensión del problema (número de nodos)."""
        return self.dimension - 1  # Excluir el depósito

    def random_solution(self):
        """
        Genera una solución aleatoria para el problema VRP.

        Returns:
            solution: Vector de valores continuos aleatorios en el rango [0,1]
        """
        dim = self.get_dimension()
        return np.random.rand(dim)

    def random_routes(self):
        """
        Genera una solución aleatoria en forma de rutas para el problema VRP.
        Usa una estrategia de construcción simplificada tipo Clarke-Wright.

        Returns:
            routes: Lista de rutas que respetan restricciones de capacidad
        """
        depot = self.depot_index
        customers = list(range(1, self.dimension))
        np.random.shuffle(customers)

        routes = []
        current_route = [depot]
        current_load = 0

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

    def is_valid(self, solution):
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
            return self.routes_are_feasible(solution)

        # En el contexto de VRP con permutación/prioridad, consideramos válido
        # cualquier vector de la dimensión correcta con valores entre 0 y 1
        if len(solution) != self.get_dimension():
            return False

        return np.all(solution >= 0) and np.all(solution <= 1)

    def repair_routes(self, routes):
        """
        Repara una solución de rutas para hacerla factible.

        Args:
            routes: Lista de rutas a reparar

        Returns:
            Lista de rutas reparadas
        """
        depot = self.depot_index

        # Paso 1: Recolectar todos los clientes de todas las rutas
        all_customers = []
        for route in routes:
            for node in route:
                if node != depot:
                    all_customers.append(node)

        # Eliminar duplicados manteniendo el orden de aparición
        seen = set()
        unique_customers = [
            x for x in all_customers if x not in seen and not seen.add(x)
        ]

        # Paso 2: Verificar clientes faltantes
        required_customers = set(range(1, self.dimension))
        missing_customers = list(required_customers - set(unique_customers))

        # Paso 3: Crear nuevas rutas factibles
        new_routes = []
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
