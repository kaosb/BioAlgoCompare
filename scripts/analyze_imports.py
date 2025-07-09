#!/usr/bin/env python3
"""
Analiza dependencias circulares y problemas de imports en el proyecto.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import json
import graphviz


class ImportAnalyzer:
    def __init__(self, root_dir: Path = Path('.')):
        self.root_dir = root_dir
        self.imports = defaultdict(set)  # file -> set of imported modules
        self.dependencies = defaultdict(set)  # module -> set of modules it depends on
        self.reverse_deps = defaultdict(set)  # module -> set of modules that depend on it
        self.circular_deps = []
        self.import_errors = []
        self.unused_imports = defaultdict(list)
        self.star_imports = []
        
    def analyze_project(self):
        """Analiza todo el proyecto."""
        print("=" * 80)
        print("IMPORT ANALYSIS")
        print("=" * 80)
        
        # Fase 1: Recolectar todos los imports
        self._collect_imports()
        
        # Fase 2: Detectar dependencias circulares
        self._detect_circular_dependencies()
        
        # Fase 3: Detectar imports problemáticos
        self._detect_problematic_imports()
        
        # Fase 4: Detectar imports no utilizados
        self._detect_unused_imports()
        
        # Fase 5: Generar reporte
        self._generate_report()
        
    def _collect_imports(self):
        """Recolecta todos los imports del proyecto."""
        py_files = list(self.root_dir.rglob('*.py'))
        
        # Filtrar archivos a ignorar
        py_files = [f for f in py_files if not any(
            skip in str(f) for skip in ['.git', '__pycache__', 'venv', '.tox', 'legacy']
        )]
        
        print(f"\nAnalyzing {len(py_files)} Python files...")
        
        for py_file in py_files:
            self._analyze_file_imports(py_file)
    
    def _analyze_file_imports(self, file_path: Path):
        """Analiza los imports de un archivo."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            module_name = self._path_to_module(file_path)
            imports_in_file = []
            used_names = set()
            
            # Recolectar todos los nombres usados en el archivo
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # Analizar imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_module = alias.name
                        import_name = alias.asname or alias.name.split('.')[-1]
                        
                        self.imports[module_name].add(imported_module)
                        self.dependencies[module_name].add(imported_module)
                        self.reverse_deps[imported_module].add(module_name)
                        
                        imports_in_file.append({
                            'module': imported_module,
                            'name': import_name,
                            'line': node.lineno,
                            'type': 'import'
                        })
                        
                        # Check si es star import
                        if alias.name == '*':
                            self.star_imports.append({
                                'file': str(file_path),
                                'line': node.lineno,
                                'module': imported_module
                            })
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Manejar imports relativos
                        if node.level > 0:
                            # Import relativo
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
                        
                        self.imports[module_name].add(imported_module)
                        self.dependencies[module_name].add(imported_module)
                        self.reverse_deps[imported_module].add(module_name)
                        
                        for alias in node.names:
                            if alias.name == '*':
                                self.star_imports.append({
                                    'file': str(file_path),
                                    'line': node.lineno,
                                    'module': imported_module
                                })
                            else:
                                import_name = alias.asname or alias.name
                                imports_in_file.append({
                                    'module': imported_module,
                                    'name': import_name,
                                    'line': node.lineno,
                                    'type': 'from'
                                })
            
            # Detectar imports no utilizados
            for imp in imports_in_file:
                if imp['name'] not in used_names and imp['type'] == 'import':
                    # Para 'import X', verificar si se usa X
                    if imp['name'] not in used_names:
                        self.unused_imports[str(file_path)].append(imp)
                elif imp['type'] == 'from' and imp['name'] not in used_names:
                    # Para 'from X import Y', verificar si se usa Y
                    self.unused_imports[str(file_path)].append(imp)
                    
        except Exception as e:
            self.import_errors.append({
                'file': str(file_path),
                'error': str(e)
            })
    
    def _path_to_module(self, path: Path) -> str:
        """Convierte una ruta de archivo a nombre de módulo."""
        relative = path.relative_to(self.root_dir)
        parts = list(relative.parts[:-1]) + [relative.stem]
        return '.'.join(parts)
    
    def _detect_circular_dependencies(self):
        """Detecta dependencias circulares usando DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(module: str, path: List[str]) -> bool:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)
            
            for dep in self.dependencies.get(module, []):
                if dep not in visited:
                    if dfs(dep, path.copy()):
                        return True
                elif dep in rec_stack:
                    # Encontramos un ciclo
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    self.circular_deps.append(cycle)
            
            rec_stack.remove(module)
            return False
        
        # Buscar ciclos desde cada módulo
        for module in self.dependencies:
            if module not in visited:
                dfs(module, [])
        
        # Eliminar ciclos duplicados
        unique_cycles = []
        for cycle in self.circular_deps:
            # Normalizar el ciclo (empezar desde el elemento más pequeño)
            min_idx = cycle.index(min(cycle))
            normalized = cycle[min_idx:] + cycle[:min_idx]
            if normalized not in unique_cycles:
                unique_cycles.append(normalized)
        
        self.circular_deps = unique_cycles
    
    def _detect_problematic_imports(self):
        """Detecta imports problemáticos."""
        # Ya detectamos star imports en _analyze_file_imports
        pass
    
    def _detect_unused_imports(self):
        """Los imports no utilizados ya se detectan en _analyze_file_imports."""
        pass
    
    def _generate_report(self):
        """Genera reporte del análisis."""
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        # Estadísticas generales
        total_modules = len(self.dependencies)
        total_deps = sum(len(deps) for deps in self.dependencies.values())
        
        print(f"\n📊 STATISTICS:")
        print(f"  Total modules: {total_modules}")
        print(f"  Total dependencies: {total_deps}")
        print(f"  Average dependencies per module: {total_deps/total_modules:.1f}")
        
        # Dependencias circulares
        if self.circular_deps:
            print(f"\n🔄 CIRCULAR DEPENDENCIES ({len(self.circular_deps)} found):")
            for i, cycle in enumerate(self.circular_deps, 1):
                print(f"\n  Cycle {i}:")
                for j in range(len(cycle) - 1):
                    print(f"    {cycle[j]} → {cycle[j+1]}")
        else:
            print("\n✅ No circular dependencies found!")
        
        # Star imports
        if self.star_imports:
            print(f"\n⚠️  STAR IMPORTS ({len(self.star_imports)} found):")
            for imp in self.star_imports[:10]:
                print(f"  - {imp['file']}:{imp['line']} - from {imp['module']} import *")
            if len(self.star_imports) > 10:
                print(f"  ... and {len(self.star_imports) - 10} more")
        
        # Imports no utilizados
        total_unused = sum(len(imps) for imps in self.unused_imports.values())
        if total_unused > 0:
            print(f"\n🗑️  UNUSED IMPORTS ({total_unused} found):")
            shown = 0
            for file, imports in list(self.unused_imports.items())[:5]:
                print(f"\n  {os.path.relpath(file)}:")
                for imp in imports[:3]:
                    print(f"    - Line {imp['line']}: {imp['name']} from {imp['module']}")
                    shown += 1
                if len(imports) > 3:
                    print(f"    ... and {len(imports) - 3} more")
            if len(self.unused_imports) > 5:
                print(f"\n  ... and {total_unused - shown} more in other files")
        
        # Módulos más dependientes
        print("\n📈 MOST DEPENDENT MODULES:")
        deps_count = [(m, len(deps)) for m, deps in self.dependencies.items()]
        deps_count.sort(key=lambda x: x[1], reverse=True)
        for module, count in deps_count[:5]:
            print(f"  - {module}: {count} dependencies")
        
        # Módulos más importados
        print("\n📥 MOST IMPORTED MODULES:")
        imported_count = [(m, len(deps)) for m, deps in self.reverse_deps.items()]
        imported_count.sort(key=lambda x: x[1], reverse=True)
        for module, count in imported_count[:5]:
            print(f"  - {module}: imported by {count} modules")
        
        # Errores de análisis
        if self.import_errors:
            print(f"\n❌ ANALYSIS ERRORS ({len(self.import_errors)}):")
            for err in self.import_errors[:5]:
                print(f"  - {err['file']}: {err['error']}")
        
        # Guardar reporte detallado
        self._save_detailed_report()
        
        # Generar gráfico de dependencias
        self._generate_dependency_graph()
    
    def _save_detailed_report(self):
        """Guarda reporte detallado en JSON."""
        report = {
            'statistics': {
                'total_modules': len(self.dependencies),
                'total_dependencies': sum(len(deps) for deps in self.dependencies.values()),
                'circular_dependencies': len(self.circular_deps),
                'star_imports': len(self.star_imports),
                'unused_imports': sum(len(imps) for imps in self.unused_imports.values())
            },
            'circular_dependencies': self.circular_deps,
            'star_imports': self.star_imports,
            'unused_imports': dict(self.unused_imports),
            'dependencies': {k: list(v) for k, v in self.dependencies.items()},
            'import_errors': self.import_errors
        }
        
        report_path = Path('import_analysis_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
    
    def _generate_dependency_graph(self):
        """Genera gráfico de dependencias con graphviz."""
        try:
            dot = graphviz.Digraph(comment='Import Dependencies')
            dot.attr(rankdir='LR')
            
            # Añadir nodos coloreados por tipo
            for module in self.dependencies:
                if 'test' in module:
                    dot.node(module, color='green')
                elif 'utils' in module:
                    dot.node(module, color='blue')
                elif 'algorithms' in module:
                    dot.node(module, color='red')
                else:
                    dot.node(module)
            
            # Añadir aristas
            for module, deps in self.dependencies.items():
                for dep in deps:
                    # Marcar dependencias circulares en rojo
                    is_circular = any(
                        module in cycle and dep in cycle 
                        for cycle in self.circular_deps
                    )
                    if is_circular:
                        dot.edge(module, dep, color='red', style='bold')
                    else:
                        dot.edge(module, dep)
            
            # Guardar gráfico
            dot.render('import_dependencies', format='png', cleanup=True)
            print("📊 Dependency graph saved to: import_dependencies.png")
            
        except Exception as e:
            print(f"⚠️  Could not generate graph: {e}")


def main():
    analyzer = ImportAnalyzer()
    analyzer.analyze_project()
    
    # Generar script de limpieza
    print("\n" + "=" * 80)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 80)
    
    print("\nTo clean up unused imports, you can use:")
    print("  - autoflake --remove-all-unused-imports --in-place <file>")
    print("  - isort <file> (to organize imports)")
    print("\nTo fix circular dependencies:")
    print("  - Move shared code to a common module")
    print("  - Use lazy imports (import inside functions)")
    print("  - Refactor to reduce coupling")


if __name__ == '__main__':
    main()