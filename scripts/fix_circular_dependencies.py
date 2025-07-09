#!/usr/bin/env python3
"""
Script para detectar y proponer soluciones a dependencias circulares.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import json
import networkx as nx


class CircularDependencyResolver:
    def __init__(self):
        self.dependencies = defaultdict(set)
        self.circular_deps = []
        self.module_contents = {}
        self.shared_elements = defaultdict(list)
        
    def analyze_project(self, root_dir: Path = Path('.')):
        """Analiza el proyecto completo."""
        print("=" * 80)
        print("CIRCULAR DEPENDENCY ANALYSIS")
        print("=" * 80)
        
        # Recolectar todas las dependencias
        self._collect_dependencies(root_dir)
        
        # Detectar ciclos
        self._detect_cycles()
        
        # Analizar contenido de módulos en ciclos
        if self.circular_deps:
            self._analyze_circular_modules()
            
            # Proponer soluciones
            self._propose_solutions()
        else:
            print("\n✅ No circular dependencies found!")
    
    def _collect_dependencies(self, root_dir: Path):
        """Recolecta todas las dependencias del proyecto."""
        py_files = list(root_dir.rglob('*.py'))
        
        # Filtrar archivos
        py_files = [f for f in py_files if not any(
            skip in str(f) for skip in ['.git', '__pycache__', 'venv', '.tox', 'legacy']
        )]
        
        print(f"\nAnalyzing {len(py_files)} Python files...")
        
        for py_file in py_files:
            module_name = self._path_to_module(py_file, root_dir)
            self._analyze_imports(py_file, module_name, root_dir)
    
    def _path_to_module(self, path: Path, root_dir: Path) -> str:
        """Convierte path a nombre de módulo."""
        try:
            relative = path.relative_to(root_dir)
            parts = list(relative.parts[:-1]) + [relative.stem]
            return '.'.join(parts)
        except:
            return str(path)
    
    def _analyze_imports(self, file_path: Path, module_name: str, root_dir: Path):
        """Analiza imports de un archivo."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            # Guardar contenido para análisis posterior
            self.module_contents[module_name] = {
                'path': file_path,
                'tree': tree,
                'classes': [],
                'functions': [],
                'imports': []
            }
            
            # Analizar estructura del módulo
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    self.module_contents[module_name]['classes'].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    self.module_contents[module_name]['functions'].append(node.name)
            
            # Analizar imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.dependencies[module_name].add(alias.name)
                        self.module_contents[module_name]['imports'].append({
                            'module': alias.name,
                            'names': ['*'],
                            'line': node.lineno
                        })
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Manejar imports relativos
                        if node.level > 0:
                            base_parts = module_name.split('.')
                            if node.level <= len(base_parts):
                                base = '.'.join(base_parts[:-node.level])
                                if node.module:
                                    imported_module = f"{base}.{node.module}"
                                else:
                                    imported_module = base
                            else:
                                imported_module = node.module
                        else:
                            imported_module = node.module
                        
                        self.dependencies[module_name].add(imported_module)
                        
                        # Guardar qué se importa específicamente
                        imported_names = []
                        for alias in node.names:
                            imported_names.append(alias.name)
                        
                        self.module_contents[module_name]['imports'].append({
                            'module': imported_module,
                            'names': imported_names,
                            'line': node.lineno
                        })
                        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _detect_cycles(self):
        """Detecta ciclos usando NetworkX."""
        # Crear grafo dirigido
        G = nx.DiGraph()
        
        for module, deps in self.dependencies.items():
            for dep in deps:
                G.add_edge(module, dep)
        
        # Encontrar todos los ciclos
        try:
            cycles = list(nx.simple_cycles(G))
            
            # Eliminar duplicados y normalizar
            unique_cycles = []
            for cycle in cycles:
                # Normalizar ciclo (empezar desde el elemento menor)
                min_idx = cycle.index(min(cycle))
                normalized = cycle[min_idx:] + cycle[:min_idx]
                if normalized not in unique_cycles:
                    unique_cycles.append(normalized)
            
            self.circular_deps = unique_cycles
            
        except nx.NetworkXNoCycle:
            self.circular_deps = []
    
    def _analyze_circular_modules(self):
        """Analiza el contenido de módulos en dependencias circulares."""
        print(f"\n🔄 Found {len(self.circular_deps)} circular dependencies:")
        
        for i, cycle in enumerate(self.circular_deps, 1):
            print(f"\nCycle {i}:")
            for j in range(len(cycle)):
                print(f"  {cycle[j]} → {cycle[(j+1) % len(cycle)]}")
            
            # Analizar qué elementos se comparten
            self._analyze_shared_elements(cycle)
    
    def _analyze_shared_elements(self, cycle: List[str]):
        """Analiza qué elementos causan la dependencia circular."""
        # Para cada par de módulos en el ciclo
        for i in range(len(cycle)):
            module1 = cycle[i]
            module2 = cycle[(i+1) % len(cycle)]
            
            if module1 in self.module_contents and module2 in self.module_contents:
                # Ver qué importa module1 de module2
                imports_from_module2 = []
                for imp in self.module_contents[module1]['imports']:
                    if imp['module'] == module2:
                        imports_from_module2.extend(imp['names'])
                
                if imports_from_module2:
                    self.shared_elements[tuple(cycle)].append({
                        'from': module1,
                        'imports': module2,
                        'elements': imports_from_module2
                    })
    
    def _propose_solutions(self):
        """Propone soluciones para resolver dependencias circulares."""
        print("\n" + "=" * 80)
        print("PROPOSED SOLUTIONS")
        print("=" * 80)
        
        for i, cycle in enumerate(self.circular_deps, 1):
            print(f"\n📍 Solution for Cycle {i}: {' → '.join(cycle + [cycle[0]])}")
            
            # Estrategia 1: Crear módulo común
            print("\n  Strategy 1: Extract shared code to common module")
            common_module = self._suggest_common_module(cycle)
            print(f"    - Create: {common_module}")
            print(f"    - Move shared classes/functions from circular modules")
            print(f"    - Update imports to use the common module")
            
            # Estrategia 2: Lazy imports
            print("\n  Strategy 2: Use lazy imports")
            for module in cycle:
                print(f"    - In {module}: Move imports inside functions that use them")
            
            # Estrategia 3: Refactoring de interfaces
            print("\n  Strategy 3: Refactor using interfaces/protocols")
            print(f"    - Define protocols/ABCs for shared interfaces")
            print(f"    - Implement dependency injection")
            
            # Generar script de refactoring
            self._generate_refactoring_script(cycle, i)
    
    def _suggest_common_module(self, cycle: List[str]) -> str:
        """Sugiere nombre para módulo común."""
        # Encontrar prefijo común
        if all('.' in m for m in cycle):
            parts = [m.split('.') for m in cycle]
            common_parts = []
            
            for i in range(min(len(p) for p in parts)):
                if all(p[i] == parts[0][i] for p in parts):
                    common_parts.append(parts[0][i])
                else:
                    break
            
            if common_parts:
                return '.'.join(common_parts + ['common'])
        
        return 'common.shared'
    
    def _generate_refactoring_script(self, cycle: List[str], cycle_num: int):
        """Genera script para refactorizar dependencias circulares."""
        script_path = Path(f'refactor_cycle_{cycle_num}.py')
        
        script_content = f'''#!/usr/bin/env python3
"""
Auto-generated refactoring script for circular dependency:
{' → '.join(cycle + [cycle[0]])}
"""

import os
import ast
from pathlib import Path

def refactor_cycle():
    """Refactoriza el ciclo de dependencias."""
    
    # Módulos involucrados
    modules = {cycle}
    
    # 1. Crear módulo común
    common_module = "{self._suggest_common_module(cycle)}"
    common_path = Path(common_module.replace('.', '/') + '.py')
    
    print(f"Creating common module: {{common_path}}")
    common_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Mover código compartido
    # TODO: Identificar y mover clases/funciones compartidas
    
    # 3. Actualizar imports
    for module in modules:
        module_path = Path(module.replace('.', '/') + '.py')
        if module_path.exists():
            print(f"Updating imports in: {{module_path}}")
            # TODO: Actualizar imports para usar módulo común
    
    print("\\nRefactoring complete!")
    print("Please review changes and test thoroughly.")

if __name__ == "__main__":
    refactor_cycle()
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print(f"\n  📝 Generated refactoring script: {script_path}")
    
    def generate_report(self):
        """Genera reporte detallado."""
        report = {
            'circular_dependencies': [
                {
                    'cycle': cycle,
                    'modules': len(cycle),
                    'shared_elements': [
                        {
                            'from': se['from'],
                            'imports': se['imports'],
                            'elements': se['elements']
                        }
                        for se in self.shared_elements.get(tuple(cycle), [])
                    ]
                }
                for cycle in self.circular_deps
            ],
            'total_cycles': len(self.circular_deps),
            'affected_modules': len(set(m for cycle in self.circular_deps for m in cycle))
        }
        
        report_path = Path('circular_dependencies_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # También generar reporte markdown
        md_path = Path('circular_dependencies_analysis.md')
        with open(md_path, 'w') as f:
            f.write("# Circular Dependencies Analysis\n\n")
            f.write(f"## Summary\n")
            f.write(f"- Total cycles found: {len(self.circular_deps)}\n")
            f.write(f"- Affected modules: {report['affected_modules']}\n\n")
            
            if self.circular_deps:
                f.write("## Detected Cycles\n\n")
                for i, cycle in enumerate(self.circular_deps, 1):
                    f.write(f"### Cycle {i}\n")
                    f.write("```\n")
                    for j in range(len(cycle)):
                        f.write(f"{cycle[j]} → {cycle[(j+1) % len(cycle)]}\n")
                    f.write("```\n\n")
                    
                    # Soluciones propuestas
                    f.write("**Proposed Solutions:**\n")
                    f.write(f"1. Extract to common module: `{self._suggest_common_module(cycle)}`\n")
                    f.write("2. Use lazy imports in affected modules\n")
                    f.write("3. Refactor using dependency injection\n\n")
        
        print(f"\n📄 Reports saved:")
        print(f"  - JSON: {report_path}")
        print(f"  - Markdown: {md_path}")


def main():
    resolver = CircularDependencyResolver()
    resolver.analyze_project()
    resolver.generate_report()


if __name__ == '__main__':
    main()