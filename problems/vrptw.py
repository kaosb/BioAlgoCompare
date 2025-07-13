"""
Vehicle Routing Problem with Time Windows (VRPTW)
================================================

Extensión del VRP básico que incluye ventanas de tiempo para cada cliente.
Cada cliente debe ser visitado dentro de su ventana de tiempo [ready_time, due_date].

Esta implementación es específica para instancias Solomon y Quick Commerce.
"""

import numpy as np
import os
from typing import List, Tuple, Dict, Any, Optional
from problems.vrp import VRPProblem


class VRPTWProblem(VRPProblem):
    """
    Vehicle Routing Problem with Time Windows.
    
    Extiende VRPProblem para incluir:
    - Ventanas de tiempo [ready_time, due_date] para cada cliente
    - Tiempo de servicio en cada cliente
    - Restricciones temporales en la evaluación
    - Soporte para instancias Solomon
    """
    
    def __init__(self, instance_path: str = None, 
                 depots: List[Tuple[float, float]] = None,
                 dynamic_lambda: float = 5.0, 
                 seed: int = 42,
                 time_limit: float = 1236.0):  # Horizonte temporal Solomon
        """
        Inicializa problema VRPTW.
        
        Args:
            instance_path: Ruta a instancia Solomon
            depots: Lista de depósitos (Quick Commerce)
            dynamic_lambda: Tasa de llegada Poisson
            seed: Semilla aleatoria
            time_limit: Horizonte temporal máximo
        """
        super().__init__(instance_path, depots, dynamic_lambda, seed)
        
        # Atributos VRPTW
        self.ready_times: List[float] = []  # Tiempo más temprano de llegada
        self.due_dates: List[float] = []    # Tiempo más tarde de llegada
        self.service_times: List[float] = []  # Tiempo de servicio
        self.time_limit = time_limit
        
        # Parámetros de penalización
        self.time_window_penalty = 1000.0  # Penalización por violar ventanas
        
        # Si hay instancia, cargar datos de tiempo
        if instance_path and os.path.exists(instance_path):
            self.load_time_windows()
    
    def load_time_windows(self) -> None:
        """
        Carga ventanas de tiempo desde archivo Solomon.
        """
        with open(self.instance_path, 'r') as f:
            lines = f.readlines()
        
        # Buscar sección CUSTOMER
        customer_start = None
        for i, line in enumerate(lines):
            if "CUSTOMER" in line:
                customer_start = i + 2  # Saltar encabezados
                break
        
        if customer_start is None:
            # Si no hay sección CUSTOMER, asumir ventanas amplias
            self._set_default_time_windows()
            return
        
        # Limpiar listas
        self.ready_times = []
        self.due_dates = []
        self.service_times = []
        
        # Parsear datos de clientes
        for line in lines[customer_start:]:
            line = line.strip()
            if not line or line.startswith("NAME"):
                break
                
            parts = line.split()
            if len(parts) >= 7:
                try:
                    # Formato Solomon: ID X Y DEMAND READY DUE SERVICE
                    ready_time = float(parts[4])
                    due_date = float(parts[5])
                    service_time = float(parts[6])
                    
                    self.ready_times.append(ready_time)
                    self.due_dates.append(due_date)
                    self.service_times.append(service_time)
                except (ValueError, IndexError):
                    # Si falla, usar valores por defecto
                    self.ready_times.append(0.0)
                    self.due_dates.append(self.time_limit)
                    self.service_times.append(10.0)
        
        # Verificar consistencia
        if len(self.ready_times) != self.dimension:
            self._set_default_time_windows()
    
    def _set_default_time_windows(self) -> None:
        """
        Establece ventanas de tiempo por defecto para Quick Commerce.
        """
        self.ready_times = [0.0] * self.dimension
        self.due_dates = [self.time_limit] * self.dimension
        self.service_times = [5.0] * self.dimension  # 5 minutos por entrega
        
        # Depósito siempre disponible
        if self.dimension > 0:
            self.ready_times[0] = 0.0
            self.due_dates[0] = self.time_limit
            self.service_times[0] = 0.0
    
    def evaluate_routes_with_time(self, routes: List[List[int]]) -> Tuple[float, Dict[str, float], List[str]]:
        """
        Evalúa rutas considerando restricciones de tiempo.
        
        Returns:
            total_cost: Costo total (distancia + penalizaciones)
            penalties: Diccionario de penalizaciones
            violations: Lista de violaciones
        """
        # Primero evaluar restricciones básicas VRP
        total_distance, penalties, violations = self.evaluate_routes_detailed(routes)
        
        # Agregar evaluación de ventanas de tiempo
        time_penalties = 0.0
        time_violations = []
        
        for route_idx, route in enumerate(routes):
            if len(route) < 2:
                continue
                
            current_time = 0.0
            
            for i in range(len(route) - 1):
                current_node = route[i]
                next_node = route[i + 1]
                
                # Tiempo de viaje
                travel_time = self.distance_matrix[current_node, next_node] / self.avg_speed * 60
                current_time += travel_time
                
                # Verificar ventana de tiempo del siguiente nodo
                if i < len(route) - 2:  # No verificar retorno al depósito
                    # Esperar si llegamos muy temprano
                    if current_time < self.ready_times[next_node]:
                        current_time = self.ready_times[next_node]
                    
                    # Verificar llegada tardía
                    if current_time > self.due_dates[next_node]:
                        lateness = current_time - self.due_dates[next_node]
                        time_penalties += lateness * self.time_window_penalty
                        time_violations.append(
                            f"Ruta {route_idx+1}: Cliente {next_node} llegada tardía por {lateness:.1f} min"
                        )
                    
                    # Agregar tiempo de servicio
                    current_time += self.service_times[next_node]
        
        # Actualizar penalizaciones y violaciones
        penalties['time_windows'] = time_penalties
        violations.extend(time_violations)
        
        return total_distance + time_penalties, penalties, violations
    
    def evaluate(self, solution: np.ndarray) -> float:
        """
        Evalúa solución considerando ventanas de tiempo.
        """
        routes, _, _ = self.decode_solution(solution)
        total_cost, _, _ = self.evaluate_routes_with_time(routes)
        return total_cost
    
    def get_time_window_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre las ventanas de tiempo.
        """
        if not self.ready_times:
            return {"status": "No time windows loaded"}
        
        return {
            "num_customers": len(self.ready_times) - 1,
            "depot_window": [self.ready_times[0], self.due_dates[0]],
            "avg_window_width": np.mean([
                self.due_dates[i] - self.ready_times[i] 
                for i in range(1, len(self.ready_times))
            ]),
            "avg_service_time": np.mean(self.service_times[1:]),
            "time_horizon": self.time_limit,
            "tight_windows": sum(1 for i in range(1, len(self.ready_times))
                               if self.due_dates[i] - self.ready_times[i] < 60)
        }
    
    def is_quick_commerce_compatible(self) -> bool:
        """
        Verifica si la instancia es compatible con Quick Commerce (ventanas < 30 min).
        """
        if not self.ready_times:
            return False
            
        # Verificar si hay ventanas estrechas (< 30 minutos)
        tight_windows = 0
        for i in range(1, len(self.ready_times)):
            window_width = self.due_dates[i] - self.ready_times[i]
            if window_width <= 30:  # 30 minutos
                tight_windows += 1
        
        # Considerar compatible si >50% tienen ventanas estrechas
        return tight_windows > (len(self.ready_times) - 1) * 0.5
    
    def convert_to_quick_commerce(self, window_minutes: int = 30) -> None:
        """
        Convierte ventanas de tiempo a formato Quick Commerce.
        
        Args:
            window_minutes: Duración de ventanas en minutos (default: 30)
        """
        if not self.ready_times:
            self._set_default_time_windows()
        
        # Convertir ventanas amplias a ventanas estrechas Quick Commerce
        for i in range(1, len(self.ready_times)):
            # Generar ventana aleatoria dentro del horizonte
            start_time = self.rng.uniform(0, self.time_limit - window_minutes)
            self.ready_times[i] = start_time
            self.due_dates[i] = start_time + window_minutes
            self.service_times[i] = 5.0  # 5 minutos estándar
        
        print(f"✅ Convertido a Quick Commerce: ventanas de {window_minutes} minutos")