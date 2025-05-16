import numpy as np
import random
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.animation as animation
from matplotlib.patches import FancyArrowPatch
from matplotlib.collections import LineCollection
import copy


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


# Funciones globales para los tests de VRP
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
    total_load = 0
    for node in route[1:-1]:  # Excluir depósito al inicio y final
        total_load += demands[node]
    
    return total_load <= capacity


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
