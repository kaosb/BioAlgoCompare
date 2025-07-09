#!/usr/bin/env python3
"""
Verificador de convenciones de nombres para BioAlgoCompare.

Valida que todos los archivos y símbolos sigan las convenciones
de nombres establecidas en el proyecto.
"""

import ast
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import argparse


class NamingConventionChecker(ast.NodeVisitor):
    """Verificador de convenciones de nombres usando AST."""
    
    # Patrones de nombres válidos
    PATTERNS = {
        'module': re.compile(r'^[a-z_][a-z0-9_]*$'),  # snake_case
        'class': re.compile(r'^[A-Z][a-zA-Z0-9]*$'),  # PascalCase
        'function': re.compile(r'^[a-z_][a-z0-9_]*$'),  # snake_case
        'method': re.compile(r'^[a-z_][a-z0-9_]*$'),  # snake_case
        'variable': re.compile(r'^[a-z_][a-z0-9_]*$'),  # snake_case
        'constant': re.compile(r'^[A-Z][A-Z0-9_]*$'),  # UPPER_SNAKE_CASE
        'private': re.compile(r'^_[a-z_][a-z0-9_]*$'),  # _snake_case
        'dunder': re.compile(r'^__[a-z]+__$'),  # __dunder__
    }
    
    # Excepciones permitidas
    EXCEPTIONS = {
        'class': {'T', 'P', 'R', 'VRP'},  # Type vars y acrónimos
        'variable': {'i', 'j', 'k', 'x', 'y', 'z', 'n', 'm', '_'},  # Iteradores comunes
        'function': {'_'},  # Placeholder común
    }
    
    def __init__(self, filename: str):
        """
        Inicializa el verificador.
        
        Args:
            filename: Nombre del archivo siendo verificado
        """
        self.filename = filename
        self.violations: List[Tuple[int, str, str]] = []
        self.current_class: Optional[str] = None
        self.in_module_level = True
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Verifica nombres de clases."""
        if not self._is_valid_name(node.name, 'class'):
            self.violations.append(
                (node.lineno, 'class', f"Class '{node.name}' should be PascalCase")
            )
        
        # Guardar contexto de clase
        old_class = self.current_class
        old_module_level = self.in_module_level
        self.current_class = node.name
        self.in_module_level = False
        
        # Verificar herencia (opcional)
        for base in node.bases:
            if isinstance(base, ast.Name):
                # Podríamos verificar nombres de clases base aquí
                pass
        
        self.generic_visit(node)
        
        # Restaurar contexto
        self.current_class = old_class
        self.in_module_level = old_module_level
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Verifica nombres de funciones y métodos."""
        self._visit_function(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Verifica nombres de funciones asíncronas."""
        self._visit_function(node)
    
    def _visit_function(self, node: Any) -> None:
        """Verifica nombres de funciones/métodos."""
        # Determinar si es método o función
        is_method = self.current_class is not None
        
        # Verificar casos especiales
        if node.name.startswith('__') and node.name.endswith('__'):
            # Método dunder
            if not self._is_valid_name(node.name, 'dunder'):
                self.violations.append(
                    (node.lineno, 'dunder', f"Dunder method '{node.name}' is not standard")
                )
        elif node.name.startswith('_'):
            # Método/función privada
            if not self._is_valid_name(node.name, 'private'):
                self.violations.append(
                    (node.lineno, 'private', f"Private {'method' if is_method else 'function'} '{node.name}' should be _snake_case")
                )
        else:
            # Método/función pública
            name_type = 'method' if is_method else 'function'
            if not self._is_valid_name(node.name, name_type):
                self.violations.append(
                    (node.lineno, name_type, f"{name_type.capitalize()} '{node.name}' should be snake_case")
                )
        
        # Verificar parámetros
        for arg in node.args.args:
            if arg.arg != 'self' and arg.arg != 'cls':
                if not self._is_valid_name(arg.arg, 'variable'):
                    self.violations.append(
                        (node.lineno, 'parameter', f"Parameter '{arg.arg}' should be snake_case")
                    )
        
        old_module_level = self.in_module_level
        self.in_module_level = False
        self.generic_visit(node)
        self.in_module_level = old_module_level
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Verifica nombres de variables y constantes."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Determinar si es constante o variable
                if self.in_module_level and target.id.isupper():
                    # Constante a nivel de módulo
                    if not self._is_valid_name(target.id, 'constant'):
                        self.violations.append(
                            (node.lineno, 'constant', f"Constant '{target.id}' should be UPPER_SNAKE_CASE")
                        )
                else:
                    # Variable regular
                    if not target.id.startswith('_'):
                        if not self._is_valid_name(target.id, 'variable'):
                            self.violations.append(
                                (node.lineno, 'variable', f"Variable '{target.id}' should be snake_case")
                            )
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Verifica nombres de variables con anotaciones."""
        if isinstance(node.target, ast.Name):
            if not self._is_valid_name(node.target.id, 'variable'):
                self.violations.append(
                    (node.lineno, 'variable', f"Variable '{node.target.id}' should be snake_case")
                )
        
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For) -> None:
        """Verifica nombres de variables de iteración."""
        if isinstance(node.target, ast.Name):
            # Los iteradores simples como i, j, k están permitidos
            if not self._is_valid_name(node.target.id, 'variable'):
                self.violations.append(
                    (node.lineno, 'iterator', f"Iterator '{node.target.id}' should be snake_case")
                )
        
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Verifica nombres de excepciones."""
        if node.name:
            if not self._is_valid_name(node.name, 'variable'):
                self.violations.append(
                    (node.lineno, 'exception', f"Exception variable '{node.name}' should be snake_case")
                )
        
        self.generic_visit(node)
    
    def _is_valid_name(self, name: str, name_type: str) -> bool:
        """
        Verifica si un nombre cumple con las convenciones.
        
        Args:
            name: Nombre a verificar
            name_type: Tipo de nombre (class, function, etc.)
            
        Returns:
            True si el nombre es válido
        """
        # Verificar excepciones
        if name_type in self.EXCEPTIONS and name in self.EXCEPTIONS[name_type]:
            return True
        
        # Verificar patrón
        pattern = self.PATTERNS.get(name_type)
        if pattern:
            return bool(pattern.match(name))
        
        return True  # Por defecto aceptar


def check_file_naming(filepath: Path) -> List[str]:
    """
    Verifica el nombre del archivo.
    
    Args:
        filepath: Ruta del archivo
        
    Returns:
        Lista de violaciones
    """
    violations = []
    filename = filepath.stem
    
    # Los archivos deben ser snake_case
    if not re.match(r'^[a-z_][a-z0-9_]*$', filename):
        # Excepciones para archivos especiales
        if filename not in ['__init__', 'README', 'LICENSE', 'CLAUDE']:
            violations.append(f"Filename '{filename}' should be snake_case")
    
    # Verificar estructura de directorios
    parts = filepath.parts
    for part in parts[:-1]:  # Excluir el archivo
        if part.startswith('.'):  # Ignorar directorios ocultos
            continue
        if not re.match(r'^[a-z_][a-z0-9_]*$', part):
            if part not in ['BioAlgoCompare', 'TODO_COMPLETED']:  # Excepciones
                violations.append(f"Directory '{part}' should be snake_case")
    
    return violations


def check_file(filepath: Path) -> Tuple[int, List[str]]:
    """
    Verifica un archivo Python.
    
    Args:
        filepath: Ruta del archivo
        
    Returns:
        (número de violaciones, lista de mensajes)
    """
    violations = []
    
    # Verificar nombre del archivo
    file_violations = check_file_naming(filepath)
    violations.extend([f"{filepath}: {v}" for v in file_violations])
    
    # Verificar contenido
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        checker = NamingConventionChecker(str(filepath))
        checker.visit(tree)
        
        for lineno, vtype, msg in checker.violations:
            violations.append(f"{filepath}:{lineno}: [{vtype}] {msg}")
    
    except SyntaxError as e:
        violations.append(f"{filepath}: Syntax error - {e}")
    except Exception as e:
        violations.append(f"{filepath}: Error checking file - {e}")
    
    return len(violations), violations


def check_project(paths: List[Path], 
                 exclude_patterns: List[str] = None) -> Tuple[int, List[str]]:
    """
    Verifica múltiples archivos del proyecto.
    
    Args:
        paths: Lista de rutas a verificar
        exclude_patterns: Patrones a excluir
        
    Returns:
        (total de violaciones, lista de mensajes)
    """
    exclude_patterns = exclude_patterns or ['test_', '__pycache__', '.git']
    total_violations = 0
    all_messages = []
    
    for path in paths:
        # Verificar exclusiones
        if any(pattern in str(path) for pattern in exclude_patterns):
            continue
        
        if path.is_file() and path.suffix == '.py':
            violations, messages = check_file(path)
            total_violations += violations
            all_messages.extend(messages)
        elif path.is_dir():
            # Recursivamente verificar directorio
            for py_file in path.rglob('*.py'):
                if not any(pattern in str(py_file) for pattern in exclude_patterns):
                    violations, messages = check_file(py_file)
                    total_violations += violations
                    all_messages.extend(messages)
    
    return total_violations, all_messages


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Check naming conventions in Python files'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        help='Files or directories to check'
    )
    parser.add_argument(
        '--exclude',
        action='append',
        help='Patterns to exclude'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Only show summary'
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
    
    # Verificar archivos
    total_violations, messages = check_project(paths, args.exclude)
    
    # Mostrar resultados
    if not args.quiet and messages:
        print("\n".join(messages))
    
    if total_violations > 0:
        print(f"\n❌ Found {total_violations} naming convention violations")
        return 1
    else:
        print("✅ All files follow naming conventions")
        return 0


if __name__ == '__main__':
    sys.exit(main())