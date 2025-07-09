#!/usr/bin/env python3
"""
Verificador de complejidad ciclomática para BioAlgoCompare.

Analiza la complejidad del código y reporta funciones/métodos
que excedan los límites establecidos.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import argparse
from dataclasses import dataclass


@dataclass
class ComplexityResult:
    """Resultado del análisis de complejidad."""
    name: str
    line: int
    complexity: int
    type: str  # 'function', 'method', 'class'
    filepath: str


class ComplexityCalculator(ast.NodeVisitor):
    """Calcula la complejidad ciclomática usando AST."""
    
    def __init__(self):
        """Inicializa el calculador."""
        self.complexity = 1  # Base complexity
        self.current_function = None
        self.results: List[ComplexityResult] = []
        self.filepath = ""
        self.current_class = None
    
    def calculate_complexity(self, node: ast.AST, filepath: str) -> List[ComplexityResult]:
        """
        Calcula la complejidad de un AST.
        
        Args:
            node: Nodo AST a analizar
            filepath: Ruta del archivo
            
        Returns:
            Lista de resultados de complejidad
        """
        self.filepath = filepath
        self.results = []
        self.visit(node)
        return self.results
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visita definición de clase."""
        old_class = self.current_class
        self.current_class = node.name
        
        # Calcular complejidad de la clase (suma de métodos)
        class_complexity = 0
        
        # Visitar métodos
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.visit(item)
                # Encontrar el resultado del método recién visitado
                if self.results and self.results[-1].name.startswith(f"{node.name}."):
                    class_complexity += self.results[-1].complexity
        
        # Registrar complejidad de la clase si es significativa
        if class_complexity > 10:  # Umbral para clases
            self.results.append(ComplexityResult(
                name=node.name,
                line=node.lineno,
                complexity=class_complexity,
                type='class',
                filepath=self.filepath
            ))
        
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visita definición de función."""
        self._analyze_function(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visita definición de función asíncrona."""
        self._analyze_function(node)
    
    def _analyze_function(self, node: Any) -> None:
        """Analiza la complejidad de una función/método."""
        old_function = self.current_function
        old_complexity = self.complexity
        
        # Nombre completo
        if self.current_class:
            full_name = f"{self.current_class}.{node.name}"
            node_type = 'method'
        else:
            full_name = node.name
            node_type = 'function'
        
        self.current_function = full_name
        self.complexity = 1  # Reset para esta función
        
        # Visitar el cuerpo
        for stmt in node.body:
            self.visit(stmt)
        
        # Registrar resultado
        self.results.append(ComplexityResult(
            name=full_name,
            line=node.lineno,
            complexity=self.complexity,
            type=node_type,
            filepath=self.filepath
        ))
        
        # Restaurar estado
        self.current_function = old_function
        self.complexity = old_complexity
    
    # Nodos que incrementan la complejidad
    def visit_If(self, node: ast.If) -> None:
        """if statement incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node: ast.While) -> None:
        """while loop incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For) -> None:
        """for loop incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """except handler incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node: ast.With) -> None:
        """with statement incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Assert(self, node: ast.Assert) -> None:
        """assert statement incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Raise(self, node: ast.Raise) -> None:
        """raise statement incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Operadores booleanos (and/or) incrementan complejidad."""
        # Cada operador adicional añade complejidad
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Lambda incrementa complejidad."""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ListComp(self, node: ast.ListComp) -> None:
        """List comprehension incrementa complejidad."""
        self._visit_comprehension(node)
    
    def visit_SetComp(self, node: ast.SetComp) -> None:
        """Set comprehension incrementa complejidad."""
        self._visit_comprehension(node)
    
    def visit_DictComp(self, node: ast.DictComp) -> None:
        """Dict comprehension incrementa complejidad."""
        self._visit_comprehension(node)
    
    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        """Generator expression incrementa complejidad."""
        self._visit_comprehension(node)
    
    def _visit_comprehension(self, node: Any) -> None:
        """Visita comprehensions."""
        # Cada generador añade complejidad
        for generator in node.generators:
            self.complexity += 1
            # Cada if en el generador también
            self.complexity += len(generator.ifs)
        self.generic_visit(node)


def calculate_halstead_metrics(node: ast.AST) -> Dict[str, float]:
    """
    Calcula métricas de Halstead (simplificado).
    
    Args:
        node: Nodo AST a analizar
        
    Returns:
        Diccionario con métricas
    """
    operators = set()
    operands = set()
    total_operators = 0
    total_operands = 0
    
    class HalsteadVisitor(ast.NodeVisitor):
        def visit_BinOp(self, node):
            nonlocal total_operators
            operators.add(type(node.op).__name__)
            total_operators += 1
            self.generic_visit(node)
        
        def visit_UnaryOp(self, node):
            nonlocal total_operators
            operators.add(type(node.op).__name__)
            total_operators += 1
            self.generic_visit(node)
        
        def visit_Compare(self, node):
            nonlocal total_operators
            for op in node.ops:
                operators.add(type(op).__name__)
                total_operators += 1
            self.generic_visit(node)
        
        def visit_Name(self, node):
            nonlocal total_operands
            operands.add(node.id)
            total_operands += 1
            self.generic_visit(node)
        
        def visit_Constant(self, node):
            nonlocal total_operands
            operands.add(str(node.value))
            total_operands += 1
            self.generic_visit(node)
    
    visitor = HalsteadVisitor()
    visitor.visit(node)
    
    n1 = len(operators)  # Operadores únicos
    n2 = len(operands)   # Operandos únicos
    N1 = total_operators # Total operadores
    N2 = total_operands  # Total operandos
    
    # Métricas de Halstead
    vocabulary = n1 + n2
    length = N1 + N2
    volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
    difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
    effort = volume * difficulty
    
    return {
        'vocabulary': vocabulary,
        'length': length,
        'volume': volume,
        'difficulty': difficulty,
        'effort': effort
    }


def analyze_file(filepath: Path, max_complexity: int = 10) -> Tuple[List[ComplexityResult], List[str]]:
    """
    Analiza la complejidad de un archivo.
    
    Args:
        filepath: Ruta del archivo
        max_complexity: Complejidad máxima permitida
        
    Returns:
        (resultados, violaciones)
    """
    violations = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        calculator = ComplexityCalculator()
        results = calculator.calculate_complexity(tree, str(filepath))
        
        # Filtrar violaciones
        for result in results:
            if result.complexity > max_complexity:
                violations.append(
                    f"{filepath}:{result.line}: {result.type} '{result.name}' "
                    f"has complexity {result.complexity} (max: {max_complexity})"
                )
        
        return results, violations
    
    except SyntaxError as e:
        return [], [f"{filepath}: Syntax error - {e}"]
    except Exception as e:
        return [], [f"{filepath}: Error analyzing file - {e}"]


def generate_complexity_report(results: List[ComplexityResult]) -> str:
    """
    Genera reporte de complejidad.
    
    Args:
        results: Resultados del análisis
        
    Returns:
        Reporte en formato texto
    """
    if not results:
        return "No complexity results to report"
    
    # Ordenar por complejidad descendente
    sorted_results = sorted(results, key=lambda x: x.complexity, reverse=True)
    
    report = "Complexity Report\n"
    report += "=" * 80 + "\n\n"
    
    # Top 10 más complejos
    report += "Top 10 Most Complex Functions/Methods:\n"
    report += "-" * 80 + "\n"
    report += f"{'Name':<50} {'Type':<10} {'Complexity':<10} {'File':<30}\n"
    report += "-" * 80 + "\n"
    
    for result in sorted_results[:10]:
        name = result.name[:47] + "..." if len(result.name) > 50 else result.name
        file = Path(result.filepath).name
        report += f"{name:<50} {result.type:<10} {result.complexity:<10} {file:<30}\n"
    
    # Estadísticas
    report += "\n" + "=" * 80 + "\n"
    report += "Statistics:\n"
    report += "-" * 80 + "\n"
    
    total = len(results)
    avg_complexity = sum(r.complexity for r in results) / total if total > 0 else 0
    max_complexity = max(r.complexity for r in results) if results else 0
    
    report += f"Total functions/methods analyzed: {total}\n"
    report += f"Average complexity: {avg_complexity:.2f}\n"
    report += f"Maximum complexity: {max_complexity}\n"
    
    # Distribución
    distribution = {
        "Low (1-5)": sum(1 for r in results if r.complexity <= 5),
        "Medium (6-10)": sum(1 for r in results if 6 <= r.complexity <= 10),
        "High (11-20)": sum(1 for r in results if 11 <= r.complexity <= 20),
        "Very High (>20)": sum(1 for r in results if r.complexity > 20),
    }
    
    report += "\nComplexity Distribution:\n"
    for category, count in distribution.items():
        percentage = (count / total * 100) if total > 0 else 0
        report += f"  {category:<20} {count:>5} ({percentage:>5.1f}%)\n"
    
    return report


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Check cyclomatic complexity of Python code'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        help='Files or directories to check'
    )
    parser.add_argument(
        '--max-complexity',
        type=int,
        default=10,
        help='Maximum allowed complexity (default: 10)'
    )
    parser.add_argument(
        '--exclude',
        action='append',
        help='Patterns to exclude'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed report'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Only show violations'
    )
    
    args = parser.parse_args()
    
    # Si no se especifican rutas, usar archivos staged de git
    if not args.paths:
        import subprocess
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            paths = [Path(f) for f in result.stdout.strip().split('\n') if f and f.endswith('.py')]
        else:
            paths = []
    else:
        paths = [Path(p) for p in args.paths]
    
    if not paths:
        print("No files to check")
        return 0
    
    # Analizar archivos
    all_results = []
    all_violations = []
    exclude_patterns = args.exclude or ['test_', '__pycache__', '.git']
    
    for path in paths:
        if any(pattern in str(path) for pattern in exclude_patterns):
            continue
        
        if path.is_file() and path.suffix == '.py':
            results, violations = analyze_file(path, args.max_complexity)
            all_results.extend(results)
            all_violations.extend(violations)
        elif path.is_dir():
            for py_file in path.rglob('*.py'):
                if not any(pattern in str(py_file) for pattern in exclude_patterns):
                    results, violations = analyze_file(py_file, args.max_complexity)
                    all_results.extend(results)
                    all_violations.extend(violations)
    
    # Mostrar violaciones
    if all_violations and not args.quiet:
        print("\n".join(all_violations))
    
    # Generar reporte si se solicita
    if args.report and all_results:
        print("\n" + generate_complexity_report(all_results))
    
    # Resumen
    if all_violations:
        print(f"\n❌ Found {len(all_violations)} complexity violations")
        return 1
    else:
        if not args.quiet:
            print(f"✅ All {len(all_results)} functions/methods are within complexity limits")
        return 0


if __name__ == '__main__':
    sys.exit(main())