import time
import random
from typing import List, Dict, Optional

import numpy as np
from abc import ABC, abstractmethod


class Individual(ABC):
    """Clase base para representar individuos en algoritmos metaheurísticos."""

    def is_better_than(self, other: "Individual") -> bool:
        """
        Compara si este individuo es mejor que otro.

        Esta implementación base asume minimización. Las subclases pueden
        sobrescribir si necesitan comportamiento diferente.

        Returns:
            bool: True si este individuo es mejor que el otro
        """
        # Asegurar que retornamos bool nativo, no np.bool_
        return bool(self.fitness() < other.fitness())

    @abstractmethod
    def is_feasible(self) -> bool:
        """Verifica si el individuo representa una solución factible."""
        pass

    @abstractmethod
    def move(self, population: list, iteration: int, max_iterations: int) -> None:
        """Mueve al individuo según las reglas del algoritmo.

        Args:
            population: La población actual de individuos.
            iteration: La iteración actual del algoritmo.
            max_iterations: El número máximo de iteraciones.
        """
        pass

    @abstractmethod
    def copy(self, other: "Individual") -> None:
        """Copia los valores de otro individuo a este."""
        pass


class MetaheuristicAlgorithm(ABC):
    """Clase base para algoritmos metaheurísticos."""

    def __init__(
        self,
        problem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None,
    ):
        """
        Inicializa el algoritmo metaheurístico.

        Args:
            problem: Instancia del problema a resolver
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        # Validación de parámetros
        if population_size < 1:
            raise ValueError(
                f"population_size debe ser >= 1, recibido: {population_size}"
            )
        if max_iterations < 1:
            raise ValueError(
                f"max_iterations debe ser >= 1, recibido: {max_iterations}"
            )
        if not hasattr(problem, "evaluate"):
            raise ValueError("problem debe tener método evaluate()")

        self.problem = problem
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.seed = seed
        self.population = []
        self.best_solution = None
        self.start_time = 0
        self.end_time = 0
        self.convergence_curve = []

        # Generadores de números aleatorios por instancia (no globales)
        self.rng = np.random.default_rng(seed)
        self.py_rng = random.Random(seed)

    @abstractmethod
    def initialize_population(self) -> None:
        """Inicializa la población del algoritmo."""
        pass

    @abstractmethod
    def update_population(self) -> None:
        """Actualiza la población en cada iteración."""
        pass

    def execute(self) -> "Individual":
        """Ejecuta el algoritmo completo."""
        self.start_time = time.time()
        self.initialize_population()
        try:
            for iteration in range(self.max_iterations):
                self.update_population()
        finally:
            self.end_time = time.time()
        return self.best_solution

    def get_execution_time(self) -> float:
        """Retorna el tiempo de ejecución en segundos."""
        return self.end_time - self.start_time

    def get_convergence_curve(self) -> list:
        """Retorna la curva de convergencia."""
        return self.convergence_curve

    def summary(self) -> Dict:
        """
        Devuelve un resumen del resultado del algoritmo.
        """
        return {
            "best_solution": getattr(self.best_solution, "position", None),
            "best_fitness": self.best_solution.fitness(),
            "execution_time": self.get_execution_time(),
            "convergence_curve": self.get_convergence_curve(),
        }

    def run(self, iterations: int = None) -> "Individual":
        """
        Run the algorithm for a specified number of iterations.

        This is an alias for execute() that allows specifying iterations
        and matches the interface expected by tests and documentation.

        Args:
            iterations: Number of iterations to run. If None, uses max_iterations.

        Returns:
            The best solution found
        """
        if iterations is not None:
            self.max_iterations = iterations
        return self.execute()

    def get_best_solution(self) -> "Individual":
        """
        Retorna la mejor solución encontrada por el algoritmo.

        Returns:
            La mejor solución (Individual) encontrada, o None si no se ha ejecutado
        """
        return self.best_solution
