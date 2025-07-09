"""
SMO (Starling Murmuration Optimizer) - Version 2
Implementación usando la nueva arquitectura base_v2.

Algoritmo bio-inspirado basado en el comportamiento de bandadas de estorninos.
Utiliza tres comportamientos: separación (exploración), buceo (explotación) y remolino (exploración/explotación).

Referencias:
- Zamani, Nadimi-Shahraki & Gandomi (2022): Starling murmuration optimizer: A novel bio-inspired algorithm for global optimization
  Computer Methods in Applied Mechanics and Engineering, 392, 114616. DOI: 10.1016/j.cma.2022.114616
"""

import numpy as np
from typing import Optional, Dict, Any, List
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator, ValidationError


class StarlingV2(Individual):
    """Starling individual para SMO versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un starling.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.dimension
        
        # Atributos especiales del algoritmo
        self.personal_best_position = None
        self._personal_best_fitness = None

    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # SMO usa límites [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar mejor personal
        self.personal_best_position = np.copy(self.position)
        self._personal_best_fitness = None

    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo SMO.
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # Obtener parámetros del contexto
        behavior_type = context.algorithm_params.get('behavior_type', 'separating')
        coef = context.algorithm_params.get('coef', 0.5)
        best_position = context.best_individual.position
        
        # Factor de decaimiento basado en la iteración
        decay = 1 - (context.iteration / context.max_iterations)
        
        # Aplicar diferentes comportamientos según la estrategia
        if behavior_type == "separating":
            # Exploración más aleatoria
            r = np.random.random(self.dimension)
            new_position = self.position + decay * coef * (2 * r - 1)
            
        elif behavior_type == "diving":
            # Explotación hacia mejor solución
            new_position = self.position + decay * coef * (best_position - self.position)
            
        elif behavior_type == "whirling":
            # Movimiento intermedio - combinación de exploración y explotación
            r1 = np.random.random(self.dimension)
            r2 = np.random.random(self.dimension)
            new_position = self.position + decay * coef * (
                r1 * (best_position - self.position) + 
                r2 * 0.1 * (2 * np.random.random(self.dimension) - 1)
            )
        else:
            # Comportamiento por defecto
            new_position = self.position
        
        # Asegurar que la posición esté dentro de los límites [0,1]
        new_position = np.clip(new_position, 0, 1)
        
        # Evaluar nueva posición
        new_fitness = self.problem.evaluate(new_position)
        current_fitness = self.fitness()
        
        # Aceptar si mejora o con pequeña probabilidad (criterio de Metropolis)
        if new_fitness < current_fitness or np.random.random() < 0.1 * decay:
            self.position = new_position
            self.invalidate_fitness()
            
            # Actualizar mejor personal si corresponde
            if self._personal_best_fitness is None or new_fitness < self.personal_best_fitness():
                self.personal_best_position = np.copy(self.position)
                self._personal_best_fitness = new_fitness
    
    def personal_best_fitness(self) -> float:
        """Calcula el fitness de la mejor posición personal."""
        if self._personal_best_fitness is None:
            self._personal_best_fitness = self.problem.evaluate(
                self.personal_best_position
            )
        return self._personal_best_fitness


class SMOV2(MetaheuristicAlgorithm[StarlingV2]):
    """
    Starling Murmuration Optimizer (SMO) - Versión 2.
    
    Algoritmo bio-inspirado basado en el comportamiento de bandadas de estorninos.
    Los estorninos se dividen en grupos y siguen diferentes comportamientos:
    - Separación: exploración aleatoria
    - Buceo: explotación hacia la mejor solución
    - Remolino: balance entre exploración y explotación
    
    Referencias:
    - Zamani, Nadimi-Shahraki & Gandomi (2022): Starling murmuration optimizer
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        k: Optional[int] = None,
        mu: float = 0.3,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo SMO v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            k: Número de bandadas (None para auto-calcular)
            mu: Proporción de individuos en comportamiento de separación (0.0-1.0)
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Parámetros específicos del algoritmo
        # k: número de bandadas
        if k is None:
            self.k = min(10, self.population_size // 3)
        else:
            self.k = ParameterValidator.validate_positive_integer(
                k, "k", min_value=3
            )
            if self.k > self.population_size // 2:
                raise ValidationError(
                    f"k debe ser <= population_size//2 ({self.population_size//2})"
                )
        
        # mu: proporción en comportamiento de separación
        self.mu = ParameterValidator.validate_probability(mu, "mu")
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de StarlingV2
        """
        return StarlingV2(self.problem)
    
    def update_population(self) -> None:
        """
        Actualiza la población en cada iteración.
        """
        # Ordenar población por fitness (necesario para SMO)
        self.population.sort(key=lambda s: s.fitness())
        
        # Tamaño del subconjunto de separación (exploración)
        sep_size = int(self.mu * self.population_size)
        
        # Dividir en k grupos (bandadas)
        flocks = []
        group_size = max(1, self.population_size // self.k)
        
        for i in range(self.k):
            start_idx = i * group_size
            end_idx = (i + 1) * group_size if i < self.k - 1 else self.population_size
            flocks.append(self.population[start_idx:end_idx])
        
        # Calcular calidad promedio de cada grupo
        flock_qualities = []
        for flock in flocks:
            quality = sum(s.fitness() for s in flock) / len(flock)
            flock_qualities.append(quality)
        
        avg_quality = sum(flock_qualities) / len(flock_qualities)
        
        # Crear contexto base
        base_context = self._create_move_context()
        
        # Actualizar cada estornino según su grupo y posición
        for i, starling in enumerate(self.population):
            # Determinar comportamiento
            if i < sep_size:
                # Grupo de exploración (separación)
                behavior = "separating"
            else:
                # Grupo regular basado en calidad
                flock_idx = min(i // group_size, self.k - 1)
                if flock_qualities[flock_idx] < avg_quality:
                    # Grupo mejor que el promedio: buceo (explotación)
                    behavior = "diving"
                else:
                    # Grupo peor que el promedio: remolino (exploración)
                    behavior = "whirling"
            
            # Factor de adaptación basado en la posición
            coef = 0.5 * (1 - i / self.population_size)
            
            # Crear contexto con parámetros específicos
            context = MoveContext(
                iteration=base_context.iteration,
                max_iterations=base_context.max_iterations,
                population=base_context.population,
                best_individual=base_context.best_individual,
                algorithm_params={
                    'behavior_type': behavior,
                    'coef': coef
                }
            )
            
            # Mover el estornino
            starling.move(context)
    
    def _create_move_context(self) -> MoveContext:
        """
        Crea el contexto de movimiento para la iteración actual.
        
        Returns:
            MoveContext con información del estado actual
        """
        return MoveContext(
            iteration=len(self.convergence_curve),
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution,
            algorithm_params={}
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        SMO requiere ordenar la población para asignar comportamientos.
        
        Returns:
            True - SMO necesita ordenar la población
        """
        return True
    
    def summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del algoritmo y sus parámetros.
        
        Returns:
            Diccionario con información del algoritmo
        """
        base_summary = super().summary()
        base_summary.update({
            "algorithm": "SMO v2",
            "k": self.k,
            "mu": self.mu,
            "behaviors": ["separating", "diving", "whirling"]
        })
        return base_summary