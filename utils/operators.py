"""
Operadores para algoritmos metaheurísticos y VRP.
Incluye operadores genéricos (cruce, mutación) y específicos de VRP (Split, 2-opt, etc.).
"""
import numpy as np
import random
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.animation as animation
from matplotlib.patches import FancyArrowPatch
from matplotlib.collections import LineCollection
import copy


def sbx_crossover(parent1, parent2, probability=0.9, distribution_index=15):
    """
    Cruce binario simulado (SBX).

    Args:
        parent1: Vector de genes del primer padre
        parent2: Vector de genes del segundo padre
        probability: Probabilidad de aplicar el cruce
        distribution_index: Índice de distribución (mayor = más parecido a padres)

    Returns:
        Nuevo vector de genes resultante del cruce
    """
    child = np.copy(parent1)

    if np.random.random() <= probability:
        for i in range(len(parent1)):
            if np.random.random() <= 0.5:
                y1, y2 = parent1[i], parent2[i]

                if abs(y1 - y2) > 1e-10:
                    if y1 > y2:
                        y1, y2 = y2, y1

                    # Calcular beta
                    rand = np.random.random()
                    beta = 1.0 + (2.0 * (y1 - 0.0) / (y2 - y1))
                    alpha = 2.0 - beta ** (-(distribution_index + 1.0))

                    if rand <= (1.0 / alpha):
                        beta_q = (rand * alpha) ** (1.0 / (distribution_index + 1.0))
                    else:
                        beta_q = (1.0 / (2.0 - rand * alpha)) ** (
                            1.0 / (distribution_index + 1.0)
                        )

                    # Calcular hijo
                    c = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))

                    # Limitar al rango [0, 1]
                    c = max(0.0, min(1.0, c))

                    child[i] = c

    return child


def polynomial_mutation(solution, probability=0.1, distribution_index=20):
    """
    Mutación polinomial.

    Args:
        solution: Vector de genes a mutar
        probability: Probabilidad de mutar cada gen
        distribution_index: Índice de distribución (mayor = cambios más pequeños)

    Returns:
        Vector mutado
    """
    mutated = np.copy(solution)

    for i in range(len(solution)):
        if np.random.random() <= probability:
            y = solution[i]
            lb, ub = 0.0, 1.0  # Límites inferior y superior

            # Calcular delta
            delta1 = (y - lb) / (ub - lb)
            delta2 = (ub - y) / (ub - lb)

            rand = np.random.random()
            mut_pow = 1.0 / (distribution_index + 1.0)

            if rand < 0.5:
                xy = 1.0 - delta1
                val = 2.0 * rand + (1.0 - 2.0 * rand) * (
                    xy ** (distribution_index + 1.0)
                )
                deltaq = val**mut_pow - 1.0
            else:
                xy = 1.0 - delta2
                val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * (
                    xy ** (distribution_index + 1.0)
                )
                deltaq = 1.0 - val**mut_pow

            y = y + deltaq * (ub - lb)
            y = max(lb, min(ub, y))  # Mantener en rango

            mutated[i] = y

    return mutated


def repair_bounds(solution, lb=0.0, ub=1.0):
    """
    Repara una solución para mantenerla dentro de los límites.

    Args:
        solution: Vector de genes a reparar
        lb: Límite inferior
        ub: Límite superior

    Returns:
        Vector reparado
    """
    return np.clip(solution, lb, ub)


# ============================================================================
# Operadores específicos para VRP
# ============================================================================

class VRPOperators:
    """Clase de operadores avanzados para problemas de ruteo de vehículos (VRP)."""

    @staticmethod
    def calculate_route_distance(route, distance_matrix):
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
    def calculate_route_load(route, demands):
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
    def check_route_capacity(route, demands, capacity):
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


# Funciones globales para compatibilidad con tests existentes
def check_route_capacity(route, demands, capacity):
    """Función global para compatibilidad."""
    return VRPOperators.check_route_capacity(route, demands, capacity)


def calculate_route_distance(route, distance_matrix):
    """Función global para compatibilidad."""
    return VRPOperators.calculate_route_distance(route, distance_matrix)


def split_vrp(permutation, problem):
    """
    Algoritmo Split para VRP.
    Transforma una permutación de clientes en un conjunto de rutas óptimas.

    Args:
        permutation: Lista de índices de clientes (sin depósito)
        problem: Objeto con los atributos del problema VRP

    Returns:
        routes: Lista de rutas optimizadas
        total_cost: Costo total de las rutas
    """
    n = len(permutation)
    depot = problem.depot_index

    # Inicializar array para costos potenciales
    potential = [float("inf")] * (n + 1)
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
                cost = (
                    problem.distance_matrix[depot, client]
                    + problem.distance_matrix[client, depot]
                )
            else:
                prev_client = permutation[j - 1]
                cost = (
                    cost
                    - problem.distance_matrix[prev_client, depot]
                    + problem.distance_matrix[prev_client, client]
                    + problem.distance_matrix[client, depot]
                )

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
