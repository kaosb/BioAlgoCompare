#!/usr/bin/env python3
"""
Script de migración semi-automático para algoritmos v1 a v2.
Genera el esqueleto básico y marca las secciones que requieren revisión manual.
"""

import os
import sys
import re
import ast
import click
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class AlgorithmMigrator:
    """Migrador automático de algoritmos v1 a v2."""
    
    def __init__(self, algorithm_name: str):
        self.algorithm_name = algorithm_name
        self.source_file = Path(f"algorithms/{algorithm_name}.py")
        self.target_file = Path(f"algorithms/{algorithm_name}_v2.py")
        self.test_file = Path(f"tests/test_{algorithm_name}_v2_migration.py")
        
        # Información extraída del algoritmo
        self.individual_class_name = None
        self.algorithm_class_name = None
        self.move_params = []
        self.special_attributes = []
        self.imports = []
    
    def parse_source(self) -> bool:
        """Parsea el archivo fuente para extraer información."""
        if not self.source_file.exists():
            click.echo(f"❌ Archivo no encontrado: {self.source_file}")
            return False
        
        with open(self.source_file, 'r') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            click.echo(f"❌ Error de sintaxis en {self.source_file}: {e}")
            return False
        
        # Buscar clases y métodos
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Buscar clase Individual
                if any(base.id == 'Individual' for base in node.bases if hasattr(base, 'id')):
                    self.individual_class_name = node.name
                    self._extract_individual_info(node)
                
                # Buscar clase Algorithm
                elif any(base.id == 'MetaheuristicAlgorithm' for base in node.bases if hasattr(base, 'id')):
                    self.algorithm_class_name = node.name
        
        # Extraer imports
        self._extract_imports(content)
        
        return True
    
    def _extract_individual_info(self, class_node: ast.ClassDef):
        """Extrae información de la clase Individual."""
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                if node.name == 'move':
                    # Extraer parámetros del método move
                    self.move_params = [arg.arg for arg in node.args.args[1:]]  # Excluir self
                elif node.name == '__init__':
                    # Buscar atributos especiales
                    for stmt in node.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and target.value.id == 'self':
                                    attr_name = target.attr
                                    if attr_name not in ['problem', 'dimension', 'position', '_fitness']:
                                        self.special_attributes.append(attr_name)
    
    def _extract_imports(self, content: str):
        """Extrae las declaraciones de import."""
        import_lines = []
        for line in content.split('\n'):
            if line.strip().startswith(('import ', 'from ')) and 'base' not in line:
                import_lines.append(line)
        self.imports = import_lines
    
    def generate_v2_code(self) -> str:
        """Genera el código v2 basado en la información extraída."""
        # Template base
        template = f'''"""
{self.algorithm_class_name} - Version 2
Implementación usando la nueva arquitectura base_v2.

TODO: Revisar y ajustar la implementación
TODO: Verificar que todos los parámetros se pasen correctamente via MoveContext
TODO: Agregar docstrings específicos del algoritmo
"""

import numpy as np
import random
from typing import Optional, Dict, Any
from algorithms.base_v2 import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem

# TODO: Revisar imports adicionales necesarios
{chr(10).join(self.imports)}


class {self.individual_class_name}V2(Individual):
    """{self.individual_class_name} individual para {self.algorithm_class_name} versión 2."""
    
    def __init__(self, problem: AbstractProblem):
        """
        Inicializa un {self.individual_class_name.lower()}.
        
        Args:
            problem: Problema a optimizar
        """
        super().__init__(problem)
        self.dimension = problem.get_dimension()
        
        # TODO: Revisar atributos especiales del algoritmo
'''
        
        # Agregar atributos especiales
        for attr in self.special_attributes:
            template += f"        self.{attr} = None  # TODO: Inicializar correctamente\n"
        
        template += f'''
    
    def initialize(self) -> None:
        """
        Inicializa la posición del individuo aleatoriamente.
        """
        # TODO: Revisar si el algoritmo usa límites diferentes a [0,1]
        self.position = np.random.uniform(0, 1, self.dimension)
        self.invalidate_fitness()
        
        # TODO: Inicializar atributos especiales si es necesario
'''
        
        for attr in self.special_attributes:
            template += f"        # self.{attr} = ...\n"
        
        template += f'''
    
    def move(self, context: MoveContext) -> None:
        """
        Mueve al individuo según el algoritmo {self.algorithm_class_name}.
        
        TODO: Migrar la lógica del método move original
        Los parámetros originales eran: {', '.join(self.move_params)}
        Ahora deben obtenerse del context:
        - context.iteration: iteración actual
        - context.max_iterations: iteraciones máximas
        - context.population: población completa
        - context.best_individual: mejor individuo
        - context.algorithm_params: parámetros específicos del algoritmo
        
        Args:
            context: Contexto con información del estado del algoritmo
        """
        # TODO: Implementar la lógica de movimiento
        # NOTA: Los parámetros originales {self.move_params} ahora vienen en context
        
        # Ejemplo de cómo obtener parámetros del contexto:
        iteration = context.iteration
        max_iterations = context.max_iterations
        population = context.population
        best = context.best_individual
        
        # TODO: Migrar el código del método move original aquí
        # Recordar invalidar fitness si se modifica la posición:
        # self.invalidate_fitness()
        
        pass  # Eliminar cuando se implemente


class {self.algorithm_class_name}V2(MetaheuristicAlgorithm):
    """
    {self.algorithm_class_name} - Versión 2.
    
    TODO: Agregar descripción del algoritmo
    TODO: Agregar referencias bibliográficas
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None
    ):
        """
        Inicializa el algoritmo {self.algorithm_class_name} v2.
        
        Args:
            problem: Problema a optimizar
            population_size: Tamaño de la población
            max_iterations: Número máximo de iteraciones
            seed: Semilla para reproducibilidad
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # TODO: Agregar parámetros específicos del algoritmo si los hay
    
    def _create_individual(self) -> Individual:
        """
        Crea un nuevo individuo.
        
        Returns:
            Nueva instancia de {self.individual_class_name}V2
        """
        return {self.individual_class_name}V2(self.problem)
    
    def _create_move_context(self) -> MoveContext:
        """
        Crea el contexto de movimiento para la iteración actual.
        
        TODO: Agregar parámetros específicos del algoritmo al contexto
        
        Returns:
            MoveContext con información del estado actual
        """
        return MoveContext(
            iteration=len(self.convergence_curve),
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution,
            algorithm_params={{}}  # TODO: Agregar parámetros específicos
        )
    
    def _should_sort_population(self) -> bool:
        """
        Determina si la población debe ordenarse después de actualizar.
        
        TODO: Verificar si el algoritmo original ordena la población
        
        Returns:
            True si la población debe ordenarse
        """
        return False  # TODO: Cambiar según el algoritmo
    
    def summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del algoritmo y sus parámetros.
        
        Returns:
            Diccionario con información del algoritmo
        """
        base_summary = super().summary()
        base_summary.update({{
            "algorithm": "{self.algorithm_class_name} v2",
            # TODO: Agregar información específica del algoritmo
        }})
        return base_summary
'''
        
        return template
    
    def generate_test_code(self) -> str:
        """Genera el código de pruebas para la migración."""
        template = f'''"""
Tests para verificar la migración de {self.algorithm_class_name} a la nueva arquitectura v2.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar ambas versiones
from algorithms.{self.algorithm_name} import {self.algorithm_class_name}, {self.individual_class_name}
from algorithms.{self.algorithm_name}_v2 import {self.algorithm_class_name}V2, {self.individual_class_name}V2
from problems.vrp import VRPProblem


class Test{self.algorithm_class_name}V2Migration:
    """Tests para la migración de {self.algorithm_class_name} a v2."""
    
    @pytest.fixture
    def test_problem(self):
        """Crea un problema de prueba pequeño."""
        data_dir = Path("data/vrp/test")
        instance_path = data_dir / "test-n5-k2.vrp"
        
        if not instance_path.exists():
            # Usar otra instancia pequeña si no existe la de prueba
            data_dir = Path("data/vrp")
            instance_path = data_dir / "P-n16-k8.vrp"
            
            if not instance_path.exists():
                pytest.skip(f"Instancia de prueba no encontrada")
                
        return VRPProblem(str(instance_path))
    
    def test_initialization_compatibility(self, test_problem):
        """Verifica que ambas versiones se inicialicen de forma similar."""
        seed = 42
        pop_size = 10
        max_iter = 5
        
        # Crear instancias de ambas versiones
        v1 = {self.algorithm_class_name}(test_problem, population_size=pop_size, 
                                         max_iterations=max_iter, seed=seed)
        v2 = {self.algorithm_class_name}V2(test_problem, population_size=pop_size, 
                                           max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert v1.population_size == v2.population_size
        assert v1.max_iterations == v2.max_iterations
        assert v2.seed == seed
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos se creen correctamente."""
        # Crear individuos de ambas versiones
        ind_v1 = {self.individual_class_name}(test_problem)
        ind_v2 = {self.individual_class_name}V2(test_problem)
        ind_v2.initialize()
        
        # Verificar propiedades básicas
        assert ind_v1.dimension == ind_v2.dimension
        assert len(ind_v1.position) == len(ind_v2.position)
        assert ind_v1.position.shape == ind_v2.position.shape
        
        # Verificar que las posiciones estén en límites válidos
        assert np.all(ind_v1.position >= 0) and np.all(ind_v1.position <= 1)
        assert np.all(ind_v2.position >= 0) and np.all(ind_v2.position <= 1)
    
    def test_reproducibility(self, test_problem):
        """Verifica que ambas versiones sean reproducibles con la misma semilla."""
        seed = 12345
        pop_size = 15
        max_iter = 10
        
        # Ejecutar v2 dos veces
        v2_1 = {self.algorithm_class_name}V2(test_problem, population_size=pop_size, 
                                             max_iterations=max_iter, seed=seed)
        best_v2_1 = v2_1.execute()
        
        v2_2 = {self.algorithm_class_name}V2(test_problem, population_size=pop_size, 
                                             max_iterations=max_iter, seed=seed)
        best_v2_2 = v2_2.execute()
        
        # Verificar reproducibilidad
        assert best_v2_1.fitness() == best_v2_2.fitness()
        assert v2_1.convergence_curve == v2_2.convergence_curve
    
    # TODO: Agregar más tests según las particularidades del algoritmo


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        return template
    
    def migrate(self) -> bool:
        """Ejecuta la migración completa."""
        click.echo(f"\n🔄 Migrando {self.algorithm_name} a v2...")
        
        # Parsear archivo fuente
        if not self.parse_source():
            return False
        
        if not self.individual_class_name or not self.algorithm_class_name:
            click.echo("❌ No se pudieron identificar las clases principales")
            return False
        
        click.echo(f"  📋 Individual: {self.individual_class_name}")
        click.echo(f"  📋 Algorithm: {self.algorithm_class_name}")
        click.echo(f"  📋 Move params: {', '.join(self.move_params)}")
        
        # Generar código v2
        v2_code = self.generate_v2_code()
        test_code = self.generate_test_code()
        
        # Escribir archivos
        with open(self.target_file, 'w') as f:
            f.write(v2_code)
        click.echo(f"  ✅ Creado: {self.target_file}")
        
        with open(self.test_file, 'w') as f:
            f.write(test_code)
        click.echo(f"  ✅ Creado: {self.test_file}")
        
        # Generar checklist
        checklist = f"""
## Checklist de Migración para {self.algorithm_class_name}

### Archivos generados:
- [ ] {self.target_file}
- [ ] {self.test_file}

### Tareas pendientes:

1. **Revisar imports**
   - [ ] Verificar que todos los imports necesarios estén incluidos
   - [ ] Eliminar imports no utilizados

2. **Clase Individual ({self.individual_class_name}V2)**
   - [ ] Revisar atributos especiales en __init__
   - [ ] Implementar initialize() correctamente
   - [ ] Migrar lógica de move() usando MoveContext
   - [ ] Verificar que se invalida fitness cuando cambia posición

3. **Clase Algorithm ({self.algorithm_class_name}V2)**
   - [ ] Agregar parámetros específicos del algoritmo
   - [ ] Implementar _create_move_context() con parámetros necesarios
   - [ ] Verificar _should_sort_population()
   - [ ] Completar summary() con información específica

4. **Tests**
   - [ ] Verificar que test_initialization_compatibility pasa
   - [ ] Verificar que test_individual_creation pasa
   - [ ] Verificar que test_reproducibility pasa
   - [ ] Agregar tests específicos del algoritmo

5. **Documentación**
   - [ ] Agregar docstrings descriptivos
   - [ ] Incluir referencias bibliográficas
   - [ ] Documentar particularidades del algoritmo

6. **Validación final**
   - [ ] Ejecutar todos los tests
   - [ ] Comparar rendimiento con v1
   - [ ] Verificar convergencia en problemas de prueba

### Parámetros originales de move():
{', '.join(self.move_params)}

### Notas:
- Los parámetros ahora vienen en el MoveContext
- Usar context.get_param() para parámetros específicos
- Siempre invalidar fitness después de modificar position
"""
        
        checklist_file = Path(f"docs/migration_checklist_{self.algorithm_name}.md")
        checklist_file.parent.mkdir(exist_ok=True)
        
        with open(checklist_file, 'w') as f:
            f.write(checklist)
        click.echo(f"  ✅ Checklist: {checklist_file}")
        
        return True


