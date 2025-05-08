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
            total_distance += distance_matrix[route[i], route[i+1]]
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
    def check_route_feasibility(route, demands, capacity):
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
    def evaluate_solution(routes, distance_matrix, demands, capacity, penalize_infeasible=True):
        """
        Evalúa una solución VRP completa.
        
        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            penalize_infeasible: Si es True, penaliza las soluciones no factibles
            
        Returns:
            Distancia total y factibilidad de la solución
        """
        total_distance = 0
        is_feasible = True
        
        for route in routes:
            total_distance += VRPOperators.calculate_route_distance(route, distance_matrix)
            
            if not VRPOperators.check_route_feasibility(route, demands, capacity):
                is_feasible = False
                if penalize_infeasible:
                    # Aplicar penalización por violación de capacidad
                    route_load = VRPOperators.calculate_route_load(route, demands)
                    excess = route_load - capacity
                    penalty = excess * 10  # Factor de penalización
                    total_distance += penalty
        
        return total_distance, is_feasible
    
    @staticmethod
    def calculate_penalty(routes, demands, capacity):
        """
        Calcula la penalización por violación de restricciones de capacidad.
        
        Args:
            routes: Lista de rutas (cada ruta es una lista de índices de nodos)
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            
        Returns:
            Valor de penalización
        """
        penalty = 0
        for route in routes:
            route_load = VRPOperators.calculate_route_load(route, demands)
            if route_load > capacity:
                excess = route_load - capacity
                penalty += excess * 10  # Factor de penalización
        return penalty
    
    @staticmethod
    def two_opt_move(route, i, j, distance_matrix):
        """
        Realiza un movimiento 2-opt en una ruta (invierte el segmento entre i y j).
        
        Args:
            route: Lista de índices de nodos
            i, j: Índices para el movimiento 2-opt
            distance_matrix: Matriz de distancias entre nodos
            
        Returns:
            Nueva ruta después del movimiento y el cambio en la distancia
        """
        if i >= j:
            return route, 0
        
        # Calcular distancia antes del cambio
        old_distance = distance_matrix[route[i-1], route[i]] + distance_matrix[route[j], route[j+1]]
        
        # Calcular distancia después del cambio
        new_distance = distance_matrix[route[i-1], route[j]] + distance_matrix[route[i], route[j+1]]
        
        # Realizar el movimiento 2-opt (invertir el segmento)
        new_route = route[:i] + route[i:j+1][::-1] + route[j+1:]
        
        # Calcular el cambio en la distancia
        delta = new_distance - old_distance
        
        return new_route, delta
    
    @staticmethod
    def two_opt_local_search(route, distance_matrix, max_iterations=100):
        """
        Aplica búsqueda local 2-opt a una ruta.
        
        Args:
            route: Lista de índices de nodos (incluye depósito al inicio y final)
            distance_matrix: Matriz de distancias entre nodos
            max_iterations: Número máximo de iteraciones
            
        Returns:
            Ruta mejorada
        """
        improved = True
        iteration = 0
        current_route = route.copy()
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            # Probar todos los posibles movimientos 2-opt
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route) - 1):
                    new_route, delta = VRPOperators.two_opt_move(current_route, i, j, distance_matrix)
                    
                    # Si mejora la solución, actualizar la ruta
                    if delta < 0:
                        current_route = new_route
                        improved = True
                        break
                
                if improved:
                    break
        
        return current_route
    
    @staticmethod
    def swap_nodes(route, i, j, distance_matrix):
        """
        Intercambia dos nodos en una ruta.
        
        Args:
            route: Lista de índices de nodos
            i, j: Índices de los nodos a intercambiar
            distance_matrix: Matriz de distancias entre nodos
            
        Returns:
            Nueva ruta después del intercambio y el cambio en la distancia
        """
        if i == j or i <= 0 or j <= 0 or i >= len(route)-1 or j >= len(route)-1:
            return route, 0
        
        # Calcular distancia antes del cambio
        old_distance = (distance_matrix[route[i-1], route[i]] + 
                       distance_matrix[route[i], route[i+1]] +
                       distance_matrix[route[j-1], route[j]] +
                       distance_matrix[route[j], route[j+1]])
        
        # Intercambiar nodos
        new_route = route.copy()
        new_route[i], new_route[j] = new_route[j], new_route[i]
        
        # Calcular distancia después del cambio
        new_distance = (distance_matrix[new_route[i-1], new_route[i]] + 
                       distance_matrix[new_route[i], new_route[i+1]] +
                       distance_matrix[new_route[j-1], new_route[j]] +
                       distance_matrix[new_route[j], new_route[j+1]])
        
        # Calcular el cambio en la distancia
        delta = new_distance - old_distance
        
        return new_route, delta
    
    @staticmethod
    def relocate_node(route, i, j, distance_matrix):
        """
        Reubica un nodo en otra posición dentro de la ruta.
        
        Args:
            route: Lista de índices de nodos
            i: Índice del nodo a reubicar
            j: Índice de la nueva posición
            distance_matrix: Matriz de distancias entre nodos
            
        Returns:
            Nueva ruta después de la reubicación y el cambio en la distancia
        """
        if i == j or i <= 0 or i >= len(route)-1 or j <= 0 or j >= len(route):
            return route, 0
        
        # Calcular distancia antes del cambio
        old_distance = (distance_matrix[route[i-1], route[i]] + 
                       distance_matrix[route[i], route[i+1]])
        
        # Crear nueva ruta reubicando el nodo
        node = route[i]
        new_route = route[:i] + route[i+1:]  # Eliminar nodo
        new_route = new_route[:j] + [node] + new_route[j:]  # Insertar nodo
        
        # Calcular distancia después del cambio para la nueva inserción
        if j > 0 and j < len(new_route) - 1:
            new_distance = (distance_matrix[new_route[j-1], new_route[j]] + 
                           distance_matrix[new_route[j], new_route[j+1]])
        else:
            new_distance = old_distance  # Sin cambio neto
        
        # Calcular el cambio en la distancia
        delta = new_distance - old_distance
        
        return new_route, delta
    
    @staticmethod
    def or_opt_move(route, i, l, j, distance_matrix):
        """
        Realiza un movimiento Or-opt: mueve un segmento de longitud l desde la posición i a la posición j.
        
        Args:
            route: Lista de índices de nodos
            i: Posición inicial del segmento
            l: Longitud del segmento
            j: Posición donde insertar el segmento
            distance_matrix: Matriz de distancias entre nodos
            
        Returns:
            Nueva ruta después del movimiento y el cambio en la distancia
        """
        if i == j or i + l > len(route) or i <= 0 or j <= 0:
            return route, 0
        
        # Extraer el segmento a mover
        segment = route[i:i+l]
        
        # Calcular distancia antes del cambio
        old_distance = (distance_matrix[route[i-1], route[i]] + 
                       distance_matrix[route[i+l-1], route[i+l]])
        
        # Crear nueva ruta quitando el segmento e insertándolo en la posición j
        if j < i:
            new_route = route[:j] + segment + route[j:i] + route[i+l:]
        else:
            new_route = route[:i] + route[i+l:j] + segment + route[j:]
        
        # Calcular distancia después del cambio
        idx_j = j if j < i else j - l
        new_distance = (distance_matrix[new_route[idx_j-1], new_route[idx_j]] + 
                       distance_matrix[new_route[idx_j+l-1], new_route[idx_j+l]])
        
        # Calcular el cambio en la distancia
        delta = new_distance - old_distance
        
        return new_route, delta
    
    @staticmethod
    def optimize_all_routes(routes, distance_matrix, demands, capacity, max_iterations=50):
        """
        Optimiza todas las rutas de una solución aplicando varios operadores.
        
        Args:
            routes: Lista de rutas
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            max_iterations: Número máximo de iteraciones
            
        Returns:
            Rutas optimizadas
        """
        optimized_routes = []
        
        for route in routes:
            # Si la ruta solo tiene depósito-cliente-depósito, no hay optimización posible
            if len(route) <= 3:
                optimized_routes.append(route)
                continue
            
            # Aplicar 2-opt
            improved_route = VRPOperators.two_opt_local_search(route, distance_matrix, max_iterations)
            
            # Aplicar swap y relocate de manera iterativa
            current_route = improved_route
            improved = True
            iteration = 0
            
            while improved and iteration < max_iterations:
                improved = False
                iteration += 1
                
                # Intentar swap entre nodos
                for i in range(1, len(current_route) - 1):
                    for j in range(i + 1, len(current_route) - 1):
                        new_route, delta = VRPOperators.swap_nodes(current_route, i, j, distance_matrix)
                        
                        # Si mejora la solución, actualizar la ruta
                        if delta < 0:
                            current_route = new_route
                            improved = True
                            break
                    
                    if improved:
                        break
                
                # Si no hubo mejora con swap, intentar relocate
                if not improved:
                    for i in range(1, len(current_route) - 1):
                        for j in range(1, len(current_route)):
                            if i == j or i == j - 1:
                                continue
                            
                            new_route, delta = VRPOperators.relocate_node(current_route, i, j, distance_matrix)
                            
                            # Si mejora la solución, actualizar la ruta
                            if delta < 0:
                                current_route = new_route
                                improved = True
                                break
                        
                        if improved:
                            break
                
                # Si no hubo mejora con los operadores anteriores, intentar Or-opt
                if not improved:
                    for l in range(2, min(4, len(current_route) - 2)):  # Longitudes de segmento 2 y 3
                        for i in range(1, len(current_route) - l):
                            for j in range(1, len(current_route) - l + 1):
                                if j >= i and j <= i + l:
                                    continue
                                
                                new_route, delta = VRPOperators.or_opt_move(current_route, i, l, j, distance_matrix)
                                
                                # Si mejora la solución, actualizar la ruta
                                if delta < 0:
                                    current_route = new_route
                                    improved = True
                                    break
                            
                            if improved:
                                break
                        
                        if improved:
                            break
            
            # Verificar que la ruta optimizada siga respetando la capacidad
            if VRPOperators.check_route_feasibility(current_route, demands, capacity):
                optimized_routes.append(current_route)
            else:
                optimized_routes.append(route)  # Mantener la ruta original si la optimizada no es factible
        
        return optimized_routes
    
    @staticmethod
    def swap_nodes_between_routes(route1, route2, i, j, distance_matrix, demands, capacity):
        """
        Intercambia nodos entre dos rutas diferentes.
        
        Args:
            route1, route2: Las dos rutas
            i: Índice del nodo en route1
            j: Índice del nodo en route2
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            
        Returns:
            Nuevas rutas después del intercambio y el cambio en la distancia total
        """
        if i <= 0 or i >= len(route1)-1 or j <= 0 or j >= len(route2)-1:
            return route1, route2, 0
        
        # Calcular distancia antes del cambio
        old_distance1 = (distance_matrix[route1[i-1], route1[i]] + 
                        distance_matrix[route1[i], route1[i+1]])
        old_distance2 = (distance_matrix[route2[j-1], route2[j]] + 
                        distance_matrix[route2[j], route2[j+1]])
        
        # Intercambiar nodos
        new_route1 = route1.copy()
        new_route2 = route2.copy()
        new_route1[i], new_route2[j] = new_route2[j], new_route1[i]
        
        # Calcular distancia después del cambio
        new_distance1 = (distance_matrix[new_route1[i-1], new_route1[i]] + 
                        distance_matrix[new_route1[i], new_route1[i+1]])
        new_distance2 = (distance_matrix[new_route2[j-1], new_route2[j]] + 
                        distance_matrix[new_route2[j], new_route2[j+1]])
        
        # Calcular el cambio en la distancia total
        delta = (new_distance1 + new_distance2) - (old_distance1 + old_distance2)
        
        # Verificar factibilidad
        if (not VRPOperators.check_route_feasibility(new_route1, demands, capacity) or
            not VRPOperators.check_route_feasibility(new_route2, demands, capacity)):
            return route1, route2, float('inf')  # Retornar un delta infinito si no es factible
        
        return new_route1, new_route2, delta
    
    @staticmethod
    def relocate_between_routes(route1, route2, i, j, distance_matrix, demands, capacity):
        """
        Mueve un nodo de una ruta a otra.
        
        Args:
            route1: Ruta de origen
            route2: Ruta de destino
            i: Índice del nodo en route1
            j: Índice de la posición en route2
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            
        Returns:
            Nuevas rutas después de la reubicación y el cambio en la distancia total
        """
        if i <= 0 or i >= len(route1)-1 or j <= 0 or j >= len(route2):
            return route1, route2, 0
        
        # Calcular distancia antes del cambio
        old_distance1 = (distance_matrix[route1[i-1], route1[i]] + 
                        distance_matrix[route1[i], route1[i+1]])
        
        # Mover el nodo de route1 a route2
        node = route1[i]
        new_route1 = route1[:i] + route1[i+1:]
        new_route2 = route2[:j] + [node] + route2[j:]
        
        # Calcular distancia después del cambio
        new_distance1 = distance_matrix[new_route1[i-1], new_route1[i]]
        new_distance2 = (distance_matrix[new_route2[j-1], new_route2[j]] + 
                        distance_matrix[new_route2[j], new_route2[j+1]])
        
        # Calcular el cambio en la distancia total
        old_distance2 = distance_matrix[route2[j-1], route2[j]]
        delta = (new_distance1 + new_distance2) - (old_distance1 + old_distance2)
        
        # Verificar factibilidad
        if (len(new_route1) < 3 or  # Asegurar que route1 no quede vacía
            not VRPOperators.check_route_feasibility(new_route2, demands, capacity)):
            return route1, route2, float('inf')  # Retornar un delta infinito si no es factible
        
        return new_route1, new_route2, delta
    
    @staticmethod
    def cross_exchange(route1, route2, i1, j1, i2, j2, distance_matrix, demands, capacity):
        """
        Intercambia segmentos entre dos rutas.
        
        Args:
            route1, route2: Las dos rutas
            i1, j1: Inicio y fin del segmento en route1
            i2, j2: Inicio y fin del segmento en route2
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            
        Returns:
            Nuevas rutas después del intercambio y el cambio en la distancia total
        """
        if (i1 >= j1 or i2 >= j2 or 
            i1 <= 0 or j1 >= len(route1)-1 or 
            i2 <= 0 or j2 >= len(route2)-1):
            return route1, route2, 0
        
        # Calcular distancia antes del cambio
        old_distance1 = (distance_matrix[route1[i1-1], route1[i1]] + 
                        distance_matrix[route1[j1], route1[j1+1]])
        old_distance2 = (distance_matrix[route2[i2-1], route2[i2]] + 
                        distance_matrix[route2[j2], route2[j2+1]])
        
        # Extraer segmentos
        segment1 = route1[i1:j1+1]
        segment2 = route2[i2:j2+1]
        
        # Crear nuevas rutas intercambiando segmentos
        new_route1 = route1[:i1] + segment2 + route1[j1+1:]
        new_route2 = route2[:i2] + segment1 + route2[j2+1:]
        
        # Calcular distancia después del cambio
        new_distance1 = (distance_matrix[new_route1[i1-1], new_route1[i1]] + 
                        distance_matrix[new_route1[i1+len(segment2)-1], new_route1[i1+len(segment2)]])
        new_distance2 = (distance_matrix[new_route2[i2-1], new_route2[i2]] + 
                        distance_matrix[new_route2[i2+len(segment1)-1], new_route2[i2+len(segment1)]])
        
        # Calcular el cambio en la distancia total
        delta = (new_distance1 + new_distance2) - (old_distance1 + old_distance2)
        
        # Verificar factibilidad
        if (not VRPOperators.check_route_feasibility(new_route1, demands, capacity) or
            not VRPOperators.check_route_feasibility(new_route2, demands, capacity)):
            return route1, route2, float('inf')  # Retornar un delta infinito si no es factible
        
        return new_route1, new_route2, delta
    
    @staticmethod
    def optimize_between_routes(routes, distance_matrix, demands, capacity, max_iterations=50):
        """
        Optimiza una solución aplicando operadores inter-ruta.
        
        Args:
            routes: Lista de rutas
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            max_iterations: Número máximo de iteraciones
            
        Returns:
            Rutas optimizadas
        """
        current_routes = copy.deepcopy(routes)
        improved = True
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            # Para cada par de rutas, intentar operadores inter-ruta
            for r1 in range(len(current_routes)):
                for r2 in range(r1 + 1, len(current_routes)):
                    route1 = current_routes[r1]
                    route2 = current_routes[r2]
                    
                    # 1. Intercambio de nodos entre rutas
                    for i in range(1, len(route1) - 1):
                        for j in range(1, len(route2) - 1):
                            new_route1, new_route2, delta = VRPOperators.swap_nodes_between_routes(
                                route1, route2, i, j, distance_matrix, demands, capacity)
                            
                            if delta < -0.001:  # Tolerancia para errores de redondeo
                                current_routes[r1] = new_route1
                                current_routes[r2] = new_route2
                                improved = True
                                break
                        
                        if improved:
                            break
                    
                    if improved:
                        continue
                    
                    # 2. Reubicación entre rutas
                    for i in range(1, len(route1) - 1):
                        for j in range(1, len(route2)):
                            new_route1, new_route2, delta = VRPOperators.relocate_between_routes(
                                route1, route2, i, j, distance_matrix, demands, capacity)
                            
                            if delta < -0.001:
                                current_routes[r1] = new_route1
                                current_routes[r2] = new_route2
                                improved = True
                                break
                        
                        if improved:
                            break
                    
                    if improved:
                        continue
                    
                    # Hacer lo mismo pero en dirección opuesta (route2 -> route1)
                    for i in range(1, len(route2) - 1):
                        for j in range(1, len(route1)):
                            new_route2, new_route1, delta = VRPOperators.relocate_between_routes(
                                route2, route1, i, j, distance_matrix, demands, capacity)
                            
                            if delta < -0.001:
                                current_routes[r1] = new_route1
                                current_routes[r2] = new_route2
                                improved = True
                                break
                        
                        if improved:
                            break
                    
                    if improved:
                        continue
                    
                    # 3. Intercambio de segmentos (cross-exchange)
                    for l1 in range(1, min(4, len(route1) - 2)):  # Longitudes de segmento limitadas
                        for l2 in range(1, min(4, len(route2) - 2)):
                            for i1 in range(1, len(route1) - l1):
                                for i2 in range(1, len(route2) - l2):
                                    new_route1, new_route2, delta = VRPOperators.cross_exchange(
                                        route1, route2, i1, i1 + l1 - 1, i2, i2 + l2 - 1, 
                                        distance_matrix, demands, capacity)
                                    
                                    if delta < -0.001:
                                        current_routes[r1] = new_route1
                                        current_routes[r2] = new_route2
                                        improved = True
                                        break
                                
                                if improved:
                                    break
                            
                            if improved:
                                break
                        
                        if improved:
                            break
        
        # Eliminar rutas vacías (solo con depósito)
        optimized_routes = [route for route in current_routes if len(route) > 2]
        
        return optimized_routes
    
    @staticmethod
    def route_based_crossover(parent1_routes, parent2_routes, distance_matrix, demands, capacity):
        """
        Operador de cruce basado en rutas completas.
        
        Args:
            parent1_routes, parent2_routes: Rutas de los padres
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            
        Returns:
            Rutas del hijo
        """
        # Crear lista de todos los clientes
        depot = parent1_routes[0][0]  # Índice del depósito
        all_customers = set()
        
        for route in parent1_routes:
            for node in route[1:-1]:  # Excluir depósito al inicio y final
                all_customers.add(node)
        
        # Seleccionar rutas aleatoriamente de ambos padres
        child_routes = []
        assigned_customers = set()
        
        # Combinar rutas de ambos padres
        all_routes = parent1_routes + parent2_routes
        random.shuffle(all_routes)
        
        for route in all_routes:
            route_customers = set(route[1:-1])  # Clientes en la ruta (sin depósito)
            
            # Si la ruta no tiene clientes ya asignados, añadirla al hijo
            if not route_customers.intersection(assigned_customers):
                child_routes.append(route.copy())
                assigned_customers.update(route_customers)
        
        # Asignar clientes faltantes
        unassigned = all_customers - assigned_customers
        
        if unassigned:
            # Crear nuevas rutas para clientes no asignados
            current_route = [depot]
            current_load = 0
            
            for customer in unassigned:
                if current_load + demands[customer] <= capacity:
                    current_route.append(customer)
                    current_load += demands[customer]
                else:
                    # Cerrar ruta actual y comenzar una nueva
                    current_route.append(depot)
                    child_routes.append(current_route)
                    
                    current_route = [depot, customer]
                    current_load = demands[customer]
            
            # Cerrar última ruta si no está vacía
            if len(current_route) > 1:
                current_route.append(depot)
                child_routes.append(current_route)
        
        return child_routes
    
    @staticmethod
    def best_cost_route_crossover(parent1_routes, parent2_routes, distance_matrix, demands, capacity):
        """
        Operador de cruce basado en selección de mejores rutas por costo.
        
        Args:
            parent1_routes, parent2_routes: Rutas de los padres
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            
        Returns:
            Rutas del hijo
        """
        # Crear lista de todos los clientes
        depot = parent1_routes[0][0]  # Índice del depósito
        all_customers = set()
        
        for route in parent1_routes:
            for node in route[1:-1]:
                all_customers.add(node)
        
        # Calcular la eficiencia de cada ruta (distancia / número de clientes)
        all_routes = []
        
        for route in parent1_routes + parent2_routes:
            distance = VRPOperators.calculate_route_distance(route, distance_matrix)
            customers = len(route) - 2  # Excluir depósito al inicio y final
            if customers > 0:
                efficiency = distance / customers
                all_routes.append((route, efficiency))
        
        # Ordenar rutas por eficiencia (menor es mejor)
        all_routes.sort(key=lambda x: x[1])
        
        # Construir hijo seleccionando las rutas más eficientes
        child_routes = []
        assigned_customers = set()
        
        for route, _ in all_routes:
            route_customers = set(route[1:-1])
            
            # Si la ruta no tiene clientes ya asignados, añadirla al hijo
            if not route_customers.intersection(assigned_customers):
                child_routes.append(route.copy())
                assigned_customers.update(route_customers)
                
                # Si todos los clientes están asignados, terminar
                if assigned_customers == all_customers:
                    break
        
        # Asignar clientes faltantes (similar al método anterior)
        unassigned = all_customers - assigned_customers
        
        if unassigned:
            # Crear nuevas rutas para clientes no asignados
            current_route = [depot]
            current_load = 0
            
            # Ordenar los clientes no asignados por demanda (mayor primero)
            unassigned_list = list(unassigned)
            unassigned_list.sort(key=lambda x: demands[x], reverse=True)
            
            for customer in unassigned_list:
                if current_load + demands[customer] <= capacity:
                    current_route.append(customer)
                    current_load += demands[customer]
                else:
                    # Cerrar ruta actual y comenzar una nueva
                    current_route.append(depot)
                    child_routes.append(current_route)
                    
                    current_route = [depot, customer]
                    current_load = demands[customer]
            
            # Cerrar última ruta si no está vacía
            if len(current_route) > 1:
                current_route.append(depot)
                child_routes.append(current_route)
        
        return child_routes
    
    @staticmethod
    def sequence_based_crossover(parent1_routes, parent2_routes, distance_matrix, demands, capacity):
        """
        Operador de cruce basado en secuencias de nodos.
        
        Args:
            parent1_routes, parent2_routes: Rutas de los padres
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            
        Returns:
            Rutas del hijo
        """
        depot = parent1_routes[0][0]  # Índice del depósito
        
        # Convertir rutas a una única secuencia (ignorando depósitos intermedios)
        def routes_to_sequence(routes):
            sequence = []
            for route in routes:
                sequence.extend(route[1:-1])  # Añadir solo los clientes (sin depósitos)
            return sequence
        
        parent1_sequence = routes_to_sequence(parent1_routes)
        parent2_sequence = routes_to_sequence(parent2_routes)
        
        # Aplicar cruce OX (Order Crossover)
        sequence_length = len(parent1_sequence)
        child_sequence = [-1] * sequence_length
        
        # Seleccionar puntos de cruce
        start = random.randint(0, sequence_length - 1)
        end = random.randint(start, sequence_length - 1)
        
        # Copiar segmento de parent1
        for i in range(start, end + 1):
            child_sequence[i] = parent1_sequence[i]
        
        # Rellenar con elementos de parent2 que no están en el segmento
        segment_elements = set(child_sequence[start:end+1])
        parent2_filtered = [x for x in parent2_sequence if x not in segment_elements]
        
        # Insertar elementos restantes
        j = 0
        for i in range(sequence_length):
            if child_sequence[i] == -1:
                child_sequence[i] = parent2_filtered[j]
                j += 1
        
        # Convertir la secuencia de vuelta a rutas respetando restricciones de capacidad
        child_routes = []
        current_route = [depot]
        current_load = 0
        
        for customer in child_sequence:
            if current_load + demands[customer] <= capacity:
                current_route.append(customer)
                current_load += demands[customer]
            else:
                # Cerrar ruta actual y comenzar una nueva
                current_route.append(depot)
                child_routes.append(current_route)
                
                current_route = [depot, customer]
                current_load = demands[customer]
        
        # Cerrar última ruta
        if len(current_route) > 1:
            current_route.append(depot)
            child_routes.append(current_route)
        
        return child_routes
    
    @staticmethod
    def swap_mutation(routes, distance_matrix, demands, capacity, mutation_rate=0.3):
        """
        Mutación por intercambio de nodos dentro de las rutas.
        
        Args:
            routes: Lista de rutas
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            mutation_rate: Probabilidad de aplicar la mutación
            
        Returns:
            Rutas mutadas
        """
        if random.random() > mutation_rate:
            return routes
        
        mutated_routes = copy.deepcopy(routes)
        
        # Seleccionar una ruta aleatoria para mutar
        if len(mutated_routes) == 0:
            return mutated_routes
            
        route_idx = random.randint(0, len(mutated_routes) - 1)
        route = mutated_routes[route_idx]
        
        # Si la ruta es demasiado corta, no hay nada que intercambiar
        if len(route) <= 3:
            return mutated_routes
        
        # Seleccionar dos posiciones aleatorias para intercambio (excluyendo depósito)
        i = random.randint(1, len(route) - 2)
        j = random.randint(1, len(route) - 2)
        
        # Asegurar que i y j sean diferentes
        while i == j:
            j = random.randint(1, len(route) - 2)
        
        # Intercambiar nodos
        route[i], route[j] = route[j], route[i]
        
        # Verificar factibilidad (siempre factible para VRP de capacidad)
        return mutated_routes
    
    @staticmethod
    def inversion_mutation(routes, distance_matrix, demands, capacity, mutation_rate=0.3):
        """
        Mutación por inversión de segmento en una ruta.
        
        Args:
            routes: Lista de rutas
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            mutation_rate: Probabilidad de aplicar la mutación
            
        Returns:
            Rutas mutadas
        """
        if random.random() > mutation_rate:
            return routes
        
        mutated_routes = copy.deepcopy(routes)
        
        # Seleccionar una ruta aleatoria para mutar
        if len(mutated_routes) == 0:
            return mutated_routes
            
        route_idx = random.randint(0, len(mutated_routes) - 1)
        route = mutated_routes[route_idx]
        
        # Si la ruta es demasiado corta, no hay segmento para invertir
        if len(route) <= 3:
            return mutated_routes
        
        # Seleccionar puntos de inicio y fin aleatorios para la inversión (excluyendo depósito)
        start = random.randint(1, len(route) - 3)
        end = random.randint(start + 1, len(route) - 2)
        
        # Invertir el segmento
        route[start:end+1] = route[start:end+1][::-1]
        
        # Verificar factibilidad (siempre factible para VRP de capacidad)
        return mutated_routes
    
    @staticmethod
    def scramble_mutation(routes, distance_matrix, demands, capacity, mutation_rate=0.3):
        """
        Mutación por reordenamiento aleatorio de un segmento en una ruta.
        
        Args:
            routes: Lista de rutas
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            mutation_rate: Probabilidad de aplicar la mutación
            
        Returns:
            Rutas mutadas
        """
        if random.random() > mutation_rate:
            return routes
        
        mutated_routes = copy.deepcopy(routes)
        
        # Seleccionar una ruta aleatoria para mutar
        if len(mutated_routes) == 0:
            return mutated_routes
            
        route_idx = random.randint(0, len(mutated_routes) - 1)
        route = mutated_routes[route_idx]
        
        # Si la ruta es demasiado corta, no hay segmento para reordenar
        if len(route) <= 3:
            return mutated_routes
        
        # Seleccionar puntos de inicio y fin aleatorios para el segmento (excluyendo depósito)
        start = random.randint(1, len(route) - 3)
        end = random.randint(start + 1, len(route) - 2)
        
        # Extraer el segmento
        segment = route[start:end+1]
        
        # Mezclar el segmento aleatoriamente
        random.shuffle(segment)
        
        # Reemplazar el segmento original con el mezclado
        route[start:end+1] = segment
        
        # Verificar factibilidad (siempre factible para VRP de capacidad)
        return mutated_routes
    
    @staticmethod
    def insertion_mutation(routes, distance_matrix, demands, capacity, mutation_rate=0.3):
        """
        Mutación por inserción de un nodo en una posición diferente de la ruta.
        
        Args:
            routes: Lista de rutas
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            mutation_rate: Probabilidad de aplicar la mutación
            
        Returns:
            Rutas mutadas
        """
        if random.random() > mutation_rate:
            return routes
        
        mutated_routes = copy.deepcopy(routes)
        
        # Seleccionar una ruta aleatoria para mutar
        if len(mutated_routes) == 0:
            return mutated_routes
            
        route_idx = random.randint(0, len(mutated_routes) - 1)
        route = mutated_routes[route_idx]
        
        # Si la ruta es demasiado corta, no se puede aplicar la mutación
        if len(route) <= 3:
            return mutated_routes
        
        # Seleccionar un nodo aleatorio para reubicar (excluyendo depósito)
        i = random.randint(1, len(route) - 2)
        
        # Seleccionar una posición aleatoria para inserción (excluyendo depósito al final)
        j = random.randint(1, len(route) - 2)
        
        # Si i y j son iguales, no hay cambio
        if i == j:
            return mutated_routes
        
        # Extraer el nodo
        node = route[i]
        
        # Eliminar el nodo de su posición original
        route.pop(i)
        
        # Ajustar el índice de inserción si es necesario
        if j > i:
            j -= 1
        
        # Insertar el nodo en la nueva posición
        route.insert(j, node)
        
        # Verificar factibilidad (siempre factible para VRP de capacidad)
        return mutated_routes
    
    @staticmethod
    def inter_route_mutation(routes, distance_matrix, demands, capacity, mutation_rate=0.3):
        """
        Mutación que mueve un nodo de una ruta a otra.
        
        Args:
            routes: Lista de rutas
            distance_matrix: Matriz de distancias entre nodos
            demands: Lista de demandas de cada nodo
            capacity: Capacidad máxima del vehículo
            mutation_rate: Probabilidad de aplicar la mutación
            
        Returns:
            Rutas mutadas
        """
        if random.random() > mutation_rate or len(routes) < 2:
            return routes
        
        mutated_routes = copy.deepcopy(routes)
        
        # Seleccionar dos rutas diferentes para la mutación
        route1_idx = random.randint(0, len(mutated_routes) - 1)
        route2_idx = random.randint(0, len(mutated_routes) - 1)
        
        # Asegurar que sean rutas diferentes
        while route1_idx == route2_idx:
            route2_idx = random.randint(0, len(mutated_routes) - 1)
        
        route1 = mutated_routes[route1_idx]
        route2 = mutated_routes[route2_idx]
        
        # Si alguna ruta es demasiado corta, no se puede aplicar la mutación
        if len(route1) <= 3 or len(route2) <= 3:
            return mutated_routes
        
        # Seleccionar un nodo aleatorio de route1 para mover a route2
        node_idx = random.randint(1, len(route1) - 2)
        node = route1[node_idx]
        
        # Seleccionar una posición aleatoria en route2 para inserción
        insert_idx = random.randint(1, len(route2) - 2)
        
        # Verificar si la inserción en route2 respeta la capacidad
        new_load = VRPOperators.calculate_route_load(route2, demands) + demands[node]
        if new_load > capacity:
            return mutated_routes  # No realizar la mutación si viola la restricción de capacidad
        
        # Eliminar el nodo de route1
        route1.pop(node_idx)
        
        # Insertar el nodo en route2
        route2.insert(insert_idx, node)
        
        # Si route1 quedó solo con depósito, eliminarla
        if len(route1) <= 2:
            mutated_routes.pop(route1_idx)
        
        return mutated_routes
    
    @staticmethod
    def routes_to_continuous(routes, dimension):
        """
        Convierte una solución de rutas a un vector continuo.
        
        Args:
            routes: Lista de rutas
            dimension: Dimensión del problema (número de clientes)
            
        Returns:
            Vector continuo representando la solución
        """
        # Inicializar vector con valores aleatorios [0, 1]
        continuous = np.random.uniform(0, 1, dimension)
        
        # Procesar cada ruta para asignar valores crecientes a sus nodos
        current_val = 0.1
        step = 0.8 / len(routes)  # Asegurar que los valores estén bien separados
        
        for route in routes:
            clients = route[1:-1]  # Excluir depósito
            route_step = step / (len(clients) + 1)  # Sub-paso dentro de cada ruta
            
            for i, client in enumerate(clients):
                if client > 0 and client <= dimension:  # Ajustar índice si es necesario
                    idx = client - 1  # Convertir de índice 1-based a 0-based si es necesario
                    continuous[idx] = current_val + route_step * (i + 1)
            
            current_val += step
        
        return continuous
    
    @staticmethod
    def continuous_to_routes(continuous, problem):
        """
        Convierte un vector continuo a una solución de rutas.
        
        Args:
            continuous: Vector continuo
            problem: Instancia del problema VRP
            
        Returns:
            Lista de rutas
        """
        # Usar el decodificador del problema para obtener rutas
        routes, _, _ = problem.decode_solution(continuous)
        return routes
    
    @staticmethod
    def plot_routes_comparison(original_routes, improved_routes, problem, title="Comparación de Rutas"):
        """
        Visualiza la comparación entre dos conjuntos de rutas.
        
        Args:
            original_routes: Lista de rutas originales
            improved_routes: Lista de rutas mejoradas
            problem: Instancia del problema VRP
            title: Título para el gráfico
            
        Returns:
            Objeto matplotlib.figure.Figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Extraer coordenadas
        x = [node[0] for node in problem.nodes]
        y = [node[1] for node in problem.nodes]
        
        # Calcular distancias
        original_distance, _ = VRPOperators.evaluate_solution(
            original_routes, problem.distance_matrix, problem.demands, problem.capacity)
        improved_distance, _ = VRPOperators.evaluate_solution(
            improved_routes, problem.distance_matrix, problem.demands, problem.capacity)
        
        # Dibujar rutas originales
        ax1.scatter(x, y, c='lightgray', s=50)
        depot_x, depot_y = problem.nodes[problem.depot_index]
        ax1.scatter([depot_x], [depot_y], c='red', s=100, marker='*')
        
        colors = list(mcolors.TABLEAU_COLORS.values())
        
        for i, route in enumerate(original_routes):
            route_x = [problem.nodes[idx][0] for idx in route]
            route_y = [problem.nodes[idx][1] for idx in route]
            
            color = colors[i % len(colors)]
            ax1.plot(route_x, route_y, c=color, linewidth=2, alpha=0.7)
        
        ax1.set_title(f"Rutas Originales\nDistancia: {original_distance:.2f}")
        ax1.set_xlabel("Coordenada X")
        ax1.set_ylabel("Coordenada Y")
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Dibujar rutas mejoradas
        ax2.scatter(x, y, c='lightgray', s=50)
        ax2.scatter([depot_x], [depot_y], c='red', s=100, marker='*')
        
        for i, route in enumerate(improved_routes):
            route_x = [problem.nodes[idx][0] for idx in route]
            route_y = [problem.nodes[idx][1] for idx in route]
            
            color = colors[i % len(colors)]
            ax2.plot(route_x, route_y, c=color, linewidth=2, alpha=0.7)
        
        ax2.set_title(f"Rutas Mejoradas\nDistancia: {improved_distance:.2f}")
        ax2.set_xlabel("Coordenada X")
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Añadir etiquetas a los nodos
        for i, (xi, yi) in enumerate(zip(x, y)):
            ax1.annotate(f"{i}", (xi, yi), xytext=(5, 5), textcoords='offset points')
            ax2.annotate(f"{i}", (xi, yi), xytext=(5, 5), textcoords='offset points')
        
        plt.suptitle(f"{title}\nMejora: {(original_distance - improved_distance) / original_distance * 100:.2f}%", fontsize=14)
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def visualize_route_improvement(route, improved_route, problem, title="Mejora de Ruta"):
        """
        Visualiza la mejora de una ruta específica.
        
        Args:
            route: Ruta original
            improved_route: Ruta mejorada
            problem: Instancia del problema VRP
            title: Título para el gráfico
            
        Returns:
            Objeto matplotlib.figure.Figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Extraer coordenadas
        nodes = problem.nodes
        
        # Calcular distancias
        original_distance = VRPOperators.calculate_route_distance(route, problem.distance_matrix)
        improved_distance = VRPOperators.calculate_route_distance(improved_route, problem.distance_matrix)
        
        # Dibujar ruta original
        for ax, r, dist, subtitle in zip([ax1, ax2], [route, improved_route], 
                                         [original_distance, improved_distance],
                                         ["Ruta Original", "Ruta Mejorada"]):
            # Dibujar nodos
            x = [nodes[idx][0] for idx in r]
            y = [nodes[idx][1] for idx in r]
            
            # Dibujar líneas entre nodos
            for i in range(len(r) - 1):
                ax.plot([x[i], x[i+1]], [y[i], y[i+1]], 'b-', linewidth=2)
                
                # Añadir flechas para indicar dirección
                dx = x[i+1] - x[i]
                dy = y[i+1] - y[i]
                ax.arrow(x[i] + 0.9*dx, y[i] + 0.9*dy, 0.1*dx, 0.1*dy,
                         head_width=0.05, head_length=0.1, fc='black', ec='black')
            
            # Dibujar nodos
            ax.scatter(x, y, c='lightgray', s=50, zorder=5)
            
            # Resaltar depósito
            depot_idx = problem.depot_index
            depot_mask = [idx == depot_idx for idx in r]
            depot_x = [x[i] for i in range(len(r)) if depot_mask[i]]
            depot_y = [y[i] for i in range(len(r)) if depot_mask[i]]
            ax.scatter(depot_x, depot_y, c='red', s=100, marker='*', zorder=6)
            
            # Añadir etiquetas de orden
            for i, (xi, yi) in enumerate(zip(x, y)):
                ax.annotate(f"{i}", (xi, yi), xytext=(5, 5), textcoords='offset points')
                
            # Añadir etiquetas de nodos
            for i, (xi, yi, idx) in enumerate(zip(x, y, r)):
                ax.annotate(f"N{idx}", (xi, yi), xytext=(5, -10), textcoords='offset points', fontsize=8)
            
            ax.set_title(f"{subtitle}\nDistancia: {dist:.2f}")
            ax.set_xlabel("Coordenada X")
            ax.set_ylabel("Coordenada Y")
            ax.grid(True, linestyle='--', alpha=0.7)
        
        plt.suptitle(f"{title}\nMejora: {(original_distance - improved_distance) / original_distance * 100:.2f}%", fontsize=14)
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def animate_route_optimization(routes, improvement_steps, problem, title="Optimización de Rutas", interval=500):
        """
        Crea una animación que muestra la optimización progresiva de rutas.
        
        Args:
            routes: Rutas iniciales
            improvement_steps: Lista de rutas mejoradas en cada paso
            problem: Instancia del problema VRP
            title: Título para la animación
            interval: Intervalo entre frames (ms)
            
        Returns:
            Objeto matplotlib.animation.Animation
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Extraer coordenadas de todos los nodos
        x = [node[0] for node in problem.nodes]
        y = [node[1] for node in problem.nodes]
        
        # Función para actualizar la visualización en cada frame
        def update(frame):
            ax.clear()
            
            current_routes = improvement_steps[frame] if frame < len(improvement_steps) else improvement_steps[-1]
            
            # Dibujar todos los nodos
            ax.scatter(x, y, c='lightgray', s=50)
            
            # Resaltar el depósito
            depot_x, depot_y = problem.nodes[problem.depot_index]
            ax.scatter([depot_x], [depot_y], c='red', s=100, marker='*')
            
            # Dibujar cada ruta
            colors = list(mcolors.TABLEAU_COLORS.values())
            
            for i, route in enumerate(current_routes):
                route_x = [problem.nodes[idx][0] for idx in route]
                route_y = [problem.nodes[idx][1] for idx in route]
                
                color = colors[i % len(colors)]
                ax.plot(route_x, route_y, c=color, linewidth=2, alpha=0.7)
            
            # Añadir etiquetas a los nodos
            for i, (xi, yi) in enumerate(zip(x, y)):
                ax.annotate(f"{i}", (xi, yi), xytext=(5, 5), textcoords='offset points')
            
            # Mostrar distancia total
            distance, _ = VRPOperators.evaluate_solution(
                current_routes, problem.distance_matrix, problem.demands, problem.capacity)
            
            ax.set_title(f"Paso {frame+1}/{len(improvement_steps)}\nDistancia Total: {distance:.2f}")
            ax.set_xlabel("Coordenada X")
            ax.set_ylabel("Coordenada Y")
            ax.grid(True, linestyle='--', alpha=0.7)
            
            return ax,
        
        # Crear animación
        ani = animation.FuncAnimation(
            fig, update, frames=len(improvement_steps),
            interval=interval, blit=False, repeat=True)
        
        plt.suptitle(title, fontsize=14)
        plt.tight_layout()
        
        return ani