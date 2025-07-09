"""
Raven Roosting Optimization (RRO) - Version 2
Fuente: Brabazon, Cui & O'Neill (2016)
DOI: 10.1007/s00500-014-1520-5

Migrado a arquitectura v2 con validación completa de parámetros.
"""

import numpy as np
from typing import Optional
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem
from algorithms.validators import ParameterValidator


class RavenV2(Individual):
    """
    Representa un cuervo en RRO con arquitectura v2.
    """

    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un cuervo.

        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.get_dimension()
        
        # Atributos específicos de RRO
        self.personal_best_position: Optional[np.ndarray] = None
        self.personal_best_fitness: float = float('inf')

    def initialize(self) -> None:
        """
        Inicializa la posición del cuervo aleatoriamente.
        """
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # Inicializar personal best
        self.personal_best_position = np.copy(self.position)
        self.personal_best_fitness = float('inf')

    def move(self, context: MoveContext) -> None:
        """
        Mueve el cuervo según las reglas de RRO.
        
        Args:
            context: Contexto con parámetros del movimiento
        """
        # Extraer parámetros del contexto
        target_position = context.get_param('target_position')
        Rpcpt = context.get_param('Rpcpt')
        Npcpt = context.get_param('Npcpt')
        Nsteps = context.get_param('Nsteps')
        Pstop = context.get_param('Pstop')
        
        curr_pos = np.copy(self.position)
        best_pos = np.copy(self.personal_best_position)
        best_fit = self.personal_best_fitness
        
        for step in range(Nsteps):
            # Dirección hacia el objetivo + perturbación gaussiana
            direction = target_position - curr_pos
            if np.linalg.norm(direction) > 1e-12:
                direction = direction / np.linalg.norm(direction)
            
            # Aleatoriedad en la dirección
            noisy_direction = direction + np.random.normal(0, 0.1, size=self.dimension)
            noisy_direction = noisy_direction / (np.linalg.norm(noisy_direction) + 1e-12)
            
            # Paso proporcional al radio de percepción
            step_size = Rpcpt / Nsteps
            next_pos = curr_pos + step_size * noisy_direction
            
            # Aplicar límites
            next_pos = np.clip(next_pos, 0, 1)
            
            # Percepción: Npcpt intentos dentro de bola de radio Rpcpt
            improved = False
            for _ in range(Npcpt):
                # Percepción aleatoria en una bola de radio Rpcpt
                rand_dir = np.random.normal(0, 1, size=self.dimension)
                rand_dir = rand_dir / (np.linalg.norm(rand_dir) + 1e-12)
                radius = np.random.uniform(0, Rpcpt)
                percept_pos = curr_pos + rand_dir * radius
                percept_pos = np.clip(percept_pos, 0, 1)
                
                fit = self.problem.evaluate(percept_pos)
                if fit < best_fit:
                    best_fit = fit
                    best_pos = np.copy(percept_pos)
                    improved = True
            
            # Si alguna percepción mejoró el personal_best, considerar parar
            if improved and np.random.uniform() < Pstop:
                curr_pos = np.copy(best_pos)
                break
            
            curr_pos = np.copy(next_pos)
        
        # Actualizar posición del cuervo
        self.position = np.copy(curr_pos)
        self.invalidate_fitness()
        
        # Actualizar personal best si mejoró
        current_fit = self.fitness()
        if current_fit < self.personal_best_fitness:
            self.personal_best_fitness = current_fit
            self.personal_best_position = np.copy(self.position)

    def copy_from(self, other: 'RavenV2') -> None:
        """
        Copia el estado de otro cuervo.
        
        Args:
            other: El cuervo a copiar
        """
        super().copy_from(other)
        self.personal_best_position = np.copy(other.personal_best_position)
        self.personal_best_fitness = other.personal_best_fitness


class RROV2(MetaheuristicAlgorithm[RavenV2]):
    """
    Raven Roosting Optimization (RRO) - Version 2
    
    Parámetros específicos:
    - Rpcpt: Radio de percepción (0.01 a 1.0, default: 0.1 * R * sqrt(D))
    - Rleader: Radio alrededor del líder (0.01 a 1.0, default: 0.1 * R * sqrt(D))
    - Npcpt: Número de percepciones (1 a 50, default: 10)
    - Nsteps: Número de pasos de movimiento (1 a 50, default: 10)
    - Percfollow: Probabilidad de seguir al líder (0.0 a 1.0, default: 0.2)
    - Pstop: Probabilidad de parar anticipadamente (0.0 a 1.0, default: 0.1)
    """

    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        Rpcpt: Optional[float] = None,
        Rleader: Optional[float] = None,
        Npcpt: int = 10,
        Nsteps: int = 10,
        Percfollow: float = 0.2,
        Pstop: float = 0.1,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo RRO v2.

        Args:
            problem: Instancia del problema
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            Rpcpt: Radio de percepción
            Rleader: Radio alrededor del líder
            Npcpt: Número de percepciones
            Nsteps: Número de pasos
            Percfollow: Probabilidad de seguir al líder
            Pstop: Probabilidad de parar anticipadamente
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Obtener dimensión del problema
        dimension = problem.dimension
        
        # Calcular radio del espacio de búsqueda (asumiendo [0,1]^D)
        R = 1.0
        
        # Validar y establecer Rpcpt
        if Rpcpt is None:
            self.Rpcpt = 0.1 * R * np.sqrt(dimension)
        else:
            self.Rpcpt = ParameterValidator.validate_positive_float(
                Rpcpt, "Rpcpt", min_value=0.01, max_value=1.0, inclusive_min=True
            )
        
        # Validar y establecer Rleader
        if Rleader is None:
            self.Rleader = 0.1 * R * np.sqrt(dimension)
        else:
            self.Rleader = ParameterValidator.validate_positive_float(
                Rleader, "Rleader", min_value=0.01, max_value=1.0, inclusive_min=True
            )
        
        # Validar otros parámetros
        self.Npcpt = ParameterValidator.validate_positive_integer(
            Npcpt, "Npcpt", min_value=1
        )
        if self.Npcpt > 50:
            raise ValueError(f"Npcpt debe ser <= 50, se recibió: {self.Npcpt}")
        
        self.Nsteps = ParameterValidator.validate_positive_integer(
            Nsteps, "Nsteps", min_value=1
        )
        if self.Nsteps > 50:
            raise ValueError(f"Nsteps debe ser <= 50, se recibió: {self.Nsteps}")
        
        self.Percfollow = ParameterValidator.validate_probability(
            Percfollow, "Percfollow"
        )
        
        self.Pstop = ParameterValidator.validate_probability(
            Pstop, "Pstop"
        )

    def _create_individual(self) -> RavenV2:
        """
        Factory method para crear un nuevo cuervo.
        
        Returns:
            Una nueva instancia de RavenV2
        """
        return RavenV2(self.problem)
    
    def _create_move_context(self) -> MoveContext:
        """
        Crea el contexto base para los movimientos.
        
        Returns:
            MoveContext con parámetros comunes
        """
        return MoveContext(
            population=self.population,
            best_individual=self.best_solution,
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            algorithm_params={
                'Rpcpt': self.Rpcpt,
                'Rleader': self.Rleader,
                'Npcpt': self.Npcpt,
                'Nsteps': self.Nsteps,
                'Percfollow': self.Percfollow,
                'Pstop': self.Pstop
            }
        )

    def update_population(self) -> None:
        """
        Actualiza la población en cada iteración según RRO.
        """
        # Encontrar líder (mejor fitness actual)
        leader = min(self.population, key=lambda x: x.fitness())
        leader_pos = np.copy(leader.position)
        
        # Crear contexto base
        context = self._create_move_context()
        
        for raven in self.population:
            if np.random.uniform() < self.Percfollow:
                # Seguir al líder con perturbación dentro de bola de radio Rleader
                rand_dir = np.random.normal(0, 1, size=raven.dimension)
                rand_dir = rand_dir / (np.linalg.norm(rand_dir) + 1e-12)
                radius = np.random.uniform(0, self.Rleader)
                target_pos = leader_pos + rand_dir * radius
                target_pos = np.clip(target_pos, 0, 1)
            else:
                # Seguir su personal_best
                target_pos = np.copy(raven.personal_best_position)
            
            # Agregar posición objetivo al contexto
            context.set_param('target_position', target_pos)
            
            # Mover el cuervo
            raven.move(context)
        
        # Actualizar mejor solución global y curva de convergencia
        self.update_best_solution()

    def get_name(self) -> str:
        """Retorna el nombre del algoritmo."""
        return "RRO_v2"

    def get_parameters(self) -> dict:
        """Retorna los parámetros del algoritmo."""
        return {
            "population_size": self.population_size,
            "max_iterations": self.max_iterations,
            "Rpcpt": self.Rpcpt,
            "Rleader": self.Rleader,
            "Npcpt": self.Npcpt,
            "Nsteps": self.Nsteps,
            "Percfollow": self.Percfollow,
            "Pstop": self.Pstop
        }