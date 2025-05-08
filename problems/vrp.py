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
        
        self.load_instance()
        self.compute_distance_matrix()
    
    def load_instance(self):
        """Carga la instancia desde el archivo."""
        with open(self.instance_path, 'r') as f:
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
                    self.distance_matrix[i, j] = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
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
        indices.sort(key=lambda i: solution[i-1])  # Ordenar por valores de la solución
        
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
                    total_distance += self.distance_matrix[current_route[i], current_route[i+1]]
                
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
                total_distance += self.distance_matrix[current_route[i], current_route[i+1]]
        
        return routes, total_distance, True
    
    def evaluate(self, solution):
        """
        Evalúa una solución y retorna su fitness.
        
        Args:
            solution: Vector de valores continuos
            
        Returns:
            fitness: Valor de fitness (menor es mejor)
        """
        routes, total_distance, is_feasible = self.decode_solution(solution)
        return total_distance
    
    def get_dimension(self):
        """Retorna la dimensión del problema (número de nodos)."""
        return self.dimension - 1  # Excluir el depósito
