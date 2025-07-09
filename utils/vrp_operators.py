import numpy as np
import random
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.animation as animation
from matplotlib.patches import FancyArrowPatch
from matplotlib.collections import LineCollection
import copy
from typing import List, Tuple, Any

from problems.vrp import VRPProblem # Keep for now for plot_routes_comparison compatibility
from problems.vrp_v2 import VRPProblemV2
from problems.base import AbstractProblem


class VRPOperators:
    """Clase de operadores avanzados para problemas de ruteo de vehículos (VRP)."""

    @staticmethod
    def calculate_route_distance(route: List[int], distance_matrix: np.ndarray) -> float:
        """
        Calcula la distancia total de una ruta.

        Args:
            route: Lista de índices de nodos (incluye depósito al inicio y final)
            distance_matrix: Matriz de distancias entre nodos

        Returns:
            Distancia total de la ruta
        """
        total_distance = 0
        for i in range(len(route) - 1):
            total_distance += distance_matrix[route[i], route[i + 1]]
        return total_distance

    @staticmethod
    def calculate_route_load(route: List[int], demands: List[int]) -> int:
        """
        Calcula la carga total de una ruta.

        Args:
            route: Lista de índices de nodos (incluye depósito al inicio y final)
            demands: Lista de demandas de cada nodo

        Returns:
            Carga total de la ruta
        """
        total_load = 0
        for node in route[1:-1]:  # Excluir depósito al inicio y final
            total_load += demands[node]
        return total_load

    @staticmethod
    def check_route_capacity(route: List[int], demands: List[int], capacity: int) -> bool:
        """
        Verifica si una ruta respeta la restricción de capacidad.

        Args:
            route: Lista de índices de nodos (incluye depósito al inicio y final)
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo

        Returns:
            True si la ruta es factible, False en caso contrario
        """
        return VRPOperators.calculate_route_load(route, demands) <= capacity

    @staticmethod
    def evaluate_solution(routes: List[List[int]], problem: Any) -> Tuple[float, bool]:
        """
        Evalúa una solución de rutas utilizando el objeto problema.

        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)
            problem: Instancia del problema VRP (VRPProblem o VRPProblemV2)

        Returns:
            fitness: Valor de fitness (menor es mejor)
            is_feasible: Si la solución es factible
        """
        fitness = problem.evaluate(routes)
        is_feasible = problem.is_feasible(routes)
        return fitness, is_feasible

    @staticmethod
    def split_vrp(permutation: List[int], problem: Any) -> Tuple[List[List[int]], float]:
        """
        Algoritmo Split para VRP.
        Transforma una permutación de clientes en un conjunto de rutas óptimas.

        Args:
            permutation: Lista de índices de clientes (sin depósito)
            problem: Objeto con los atributos del problema VRP (VRPProblem o VRPProblemV2)

        Returns:
            routes: Lista de rutas optimizadas
            total_cost: Costo total de las rutas
        """
        n = len(permutation)
        depot = problem.depot_index

        # Inicializar array para costos potenciales
        potential = [float('inf')] * (n + 1)
        potential[0] = 0

        # Inicializar array para predecesores
        predecessor = [-1] * (n + 1)

        # Para cada cliente
        for i in range(n):
            load = 0
            cost = 0
            j = i

            # Intentar agregar más clientes a la ruta actual
            while j < n:
                # Agregar el cliente j a la ruta
                client = permutation[j]
                load += problem.demands[client]

                # Si excede la capacidad, no podemos agregar más clientes
                if load > problem.capacity:
                    break

                # Calcular el costo de esta ruta
                if j == i:  # Primera iteración
                    cost = (problem.distance_matrix[depot, client] +
                            problem.distance_matrix[client, depot])
                else:
                    prev_client = permutation[j-1]
                    cost = (cost - problem.distance_matrix[prev_client, depot] +
                            problem.distance_matrix[prev_client, client] +
                            problem.distance_matrix[client, depot])

                # Actualizar potencial
                if potential[i] + cost < potential[j + 1]:
                    potential[j + 1] = potential[i] + cost
                    predecessor[j + 1] = i

                j += 1

        # Construir las rutas a partir de los predecesores
        routes = []
        total_cost = potential[n]

        # Reconstruir las rutas desde el final
        j = n
        while j > 0:
            i = predecessor[j]
            route = [depot]  # Comenzar con el depósito
            for k in range(i, j):
                route.append(permutation[k])
            route.append(depot)  # Terminar con el depósito
            routes.insert(0, route)  # Insertar al inicio para mantener el orden
            j = i

        return routes, total_cost

    @staticmethod
    def optimize_all_routes(routes: List[List[int]], problem: Any) -> List[List[int]]:
        """
        Aplica optimización local (2-opt) a cada ruta individualmente.

        Args:
            routes: Lista de rutas
            problem: Instancia del problema VRP (VRPProblem o VRPProblemV2)

        Returns:
            Rutas optimizadas
        """
        optimized_routes = []
        for route in routes:
            if len(route) > 3:  # Rutas con al menos 2 clientes (depot-c1-c2-depot)
                current_route = route[1:-1]  # Excluir depósitos
                best_route = current_route
                best_distance = VRPOperators.calculate_route_distance([problem.depot_index] + best_route + [problem.depot_index], problem.distance_matrix)
                
                improved = True
                while improved:
                    improved = False
                    for i in range(len(best_route) - 1):
                        for j in range(i + 1, len(best_route)):
                            new_route = best_route[:i+1] + best_route[i+1:j+1][::-1] + best_route[j+1:]
                            new_distance = VRPOperators.calculate_route_distance([problem.depot_index] + new_route + [problem.depot_index], problem.distance_matrix)
                            
                            if new_distance < best_distance:
                                best_route = new_route
                                best_distance = new_distance
                                improved = True
                                break
                        if improved:
                            break
                optimized_routes.append([problem.depot_index] + best_route + [problem.depot_index])
            else:
                optimized_routes.append(route)
        return optimized_routes

    @staticmethod
    def optimize_between_routes(routes: List[List[int]], problem: Any) -> List[List[int]]:
        """
        Aplica optimización entre rutas (intercambio de clientes) para mejorar la solución global.

        Args:
            routes: Lista de rutas
            problem: Instancia del problema VRP (VRPProblem o VRPProblemV2)

        Returns:
            Rutas optimizadas
        """
        # Implementación de un simple intercambio de clientes entre rutas
        # Esto es un placeholder, una implementación real sería más compleja (ej. Or-opt, exchange)
        optimized_routes = copy.deepcopy(routes)
        num_routes = len(optimized_routes)

        for _ in range(100): # Número fijo de intentos de mejora
            route_idx1, route_idx2 = random.sample(range(num_routes), 2)
            route1 = optimized_routes[route_idx1]
            route2 = optimized_routes[route_idx2]

            if len(route1) <= 2 or len(route2) <= 2: # Rutas vacías o solo con depósito
                continue

            # Seleccionar un cliente de cada ruta (excluyendo depósitos)
            cust_idx1 = random.randrange(1, len(route1) - 1)
            cust_idx2 = random.randrange(1, len(route2) - 1)

            customer1 = route1[cust_idx1]
            customer2 = route2[cust_idx2]

            # Intentar intercambiar clientes
            new_route1 = route1[:cust_idx1] + [customer2] + route1[cust_idx1+1:]
            new_route2 = route2[:cust_idx2] + [customer1] + route2[cust_idx2+1:]

            # Verificar factibilidad y mejora
            if (VRPOperators.check_route_capacity(new_route1, problem.demands, problem.capacity) and
                VRPOperators.check_route_capacity(new_route2, problem.demands, problem.capacity)):

                old_total_distance = (VRPOperators.calculate_route_distance(route1, problem.distance_matrix) +
                                      VRPOperators.calculate_route_distance(route2, problem.distance_matrix))
                new_total_distance = (VRPOperators.calculate_route_distance(new_route1, problem.distance_matrix) +
                                      VRPOperators.calculate_route_distance(new_route2, problem.distance_matrix))

                if new_total_distance < old_total_distance:
                    optimized_routes[route_idx1] = new_route1
                    optimized_routes[route_idx2] = new_route2
        return optimized_routes

    @staticmethod
    def plot_routes_comparison(original_routes: List[List[int]], optimized_routes: List[List[int]], problem: Any, title: str = "Route Comparison") -> Any:
        """
        Compara visualmente las rutas originales y optimizadas.

        Args:
            original_routes: Rutas antes de la optimización
            optimized_routes: Rutas después de la optimización
            problem: Instancia del problema VRP (VRPProblem o VRPProblemV2)
            title: Título del gráfico
        """
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        fig.suptitle(title, fontsize=16)

        # Obtener coordenadas de los nodos
        if isinstance(problem, VRPProblemV2):
            nodes = problem.nodes
            depot_index = problem.depot_index
        elif isinstance(problem, VRPProblem):
            nodes = problem.nodes
            depot_index = problem.depot_index
        else:
            raise TypeError("Unsupported problem type for plotting")

        # Plot original routes
        ax = axes[0]
        ax.set_title("Original Routes")
        VRPOperators._plot_single_set_of_routes(ax, original_routes, problem)

        # Plot optimized routes
        ax = axes[1]
        ax.set_title("Optimized Routes")
        VRPOperators._plot_single_set_of_routes(ax, optimized_routes, problem)

        return fig

    @staticmethod
    def _plot_single_set_of_routes(ax: Any, routes: List[List[int]], problem: Any) -> None:
        """
        Helper function to plot a single set of VRP routes.
        """
        # Plot nodes
        x_coords = [node[0] for node in problem.nodes]
        y_coords = [node[1] for node in problem.nodes]
        ax.scatter(x_coords, y_coords, c='blue', s=50, zorder=2)

        # Highlight depot
        ax.scatter(problem.nodes[problem.depot_index][0], problem.nodes[problem.depot_index][1], c='red', marker='s', s=100, label='Depot', zorder=3)

        # Plot routes
        colors = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.XKCD_COLORS.values()) # More colors
        for i, route in enumerate(routes):
            route_coords_x = [problem.nodes[node_idx][0] for node_idx in route]
            route_coords_y = [problem.nodes[node_idx][1] for node_idx in route]
            ax.plot(route_coords_x, route_coords_y, color=colors[i % len(colors)], linewidth=1.5, marker='o', markersize=5, label=f'Route {i+1}')

            # Add arrows for direction
            for j in range(len(route) - 1):
                start_node = problem.nodes[route[j]]
                end_node = problem.nodes[route[j+1]]
                ax.annotate(
                    '',
                    xy=(end_node[0], end_node[1]),
                    xytext=(start_node[0], start_node[1]),
                    arrowprops=dict(facecolor=colors[i % len(colors)], shrink=0.05, width=1, headwidth=5),
                    s=0
                )

        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_aspect('equal', adjustable='box')
        ax.legend()





