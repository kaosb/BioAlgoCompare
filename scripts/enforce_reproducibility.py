#!/usr/bin/env python3
"""
Script para aplicar estándares de reproducibilidad a todos los algoritmos.

Este script analiza y corrige automáticamente problemas comunes de
reproducibilidad en los algoritmos del proyecto.
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReproducibilityEnforcer:
    """
    Aplica correcciones de reproducibilidad a archivos de algoritmos.
    """
    
    def __init__(self, dry_run: bool = True):
        """
        Inicializa el enforcer.
        
        Args:
            dry_run: Si True, solo muestra cambios sin aplicarlos
        """
        self.dry_run = dry_run
        self.fixes_applied = []
        self.files_modified = 0
    
    def process_directory(self, directory: Path) -> Dict[str, List[str]]:
        """
        Procesa todos los archivos Python en un directorio.
        
        Args:
            directory: Directorio a procesar
            
        Returns:
            Dict con archivos modificados y cambios aplicados
        """
        results = {}
        
        for py_file in directory.rglob("*.py"):
            # Skip archivos de test y legacy
            if any(skip in str(py_file) for skip in ['test_', '__pycache__', 'legacy', '_v2', '_v3']):
                continue
            
            changes = self.process_file(py_file)
            if changes:
                results[str(py_file)] = changes
                self.files_modified += 1
        
        return results
    
    def process_file(self, filepath: Path) -> List[str]:
        """
        Procesa un archivo individual.
        
        Args:
            filepath: Ruta del archivo
            
        Returns:
            Lista de cambios aplicados
        """
        logger.info(f"Processing {filepath}")
        
        try:
            content = filepath.read_text()
            original_content = content
            changes = []
            
            # Aplicar todas las correcciones
            content, change = self._fix_random_imports(content)
            if change:
                changes.append(change)
            
            content, change = self._fix_init_method(content, filepath.stem)
            if change:
                changes.append(change)
            
            content, change = self._fix_random_usage(content)
            if change:
                changes.append(change)
            
            content, change = self._fix_initialize_population(content)
            if change:
                changes.append(change)
            
            content, change = self._add_docstring_seed_info(content)
            if change:
                changes.append(change)
            
            # Guardar si hay cambios
            if content != original_content:
                if not self.dry_run:
                    filepath.write_text(content)
                    logger.info(f"Modified {filepath} with {len(changes)} changes")
                else:
                    logger.info(f"Would modify {filepath} with {len(changes)} changes")
            
            return changes
            
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return []
    
    def _fix_random_imports(self, content: str) -> Tuple[str, str]:
        """Corrige imports de random para usar solo lo necesario."""
        change = None
        
        # Eliminar import random si existe
        if 'import random\n' in content and 'self.random_state' in content:
            content = content.replace('import random\n', '')
            change = "Removed unnecessary 'import random'"
        
        # Asegurar que numpy esté importado correctamente
        if 'import numpy' not in content and 'np.' in content:
            # Añadir import después de docstring
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith(('"""', '#')):
                    lines.insert(i, 'import numpy as np')
                    content = '\n'.join(lines)
                    change = "Added 'import numpy as np'"
                    break
        
        return content, change or ""
    
    def _fix_init_method(self, content: str, class_name: str) -> Tuple[str, str]:
        """Corrige el método __init__ para incluir seed."""
        change = None
        
        # Buscar definición de __init__
        init_pattern = r'def __init__\(self([^)]*)\):'
        match = re.search(init_pattern, content)
        
        if match:
            params = match.group(1)
            
            # Verificar si seed está presente
            if 'seed' not in params:
                # Añadir seed al final de parámetros
                new_params = params.rstrip()
                if new_params and not new_params.endswith(','):
                    new_params += ','
                new_params += ' seed=None'
                
                new_init = f'def __init__(self{new_params}):'
                content = content.replace(match.group(0), new_init)
                change = "Added seed parameter to __init__"
            
            # Verificar que seed se pase a super()
            super_pattern = r'super\(\).__init__\(([^)]*)\)'
            super_match = re.search(super_pattern, content)
            
            if super_match and 'seed=' not in super_match.group(1):
                super_params = super_match.group(1).rstrip()
                if super_params and not super_params.endswith(','):
                    super_params += ','
                super_params += ' seed=seed'
                
                new_super = f'super().__init__({super_params})'
                content = content.replace(super_match.group(0), new_super)
                
                if change:
                    change += " and passed to super()"
                else:
                    change = "Added seed parameter to super().__init__"
        
        return content, change or ""
    
    def _fix_random_usage(self, content: str) -> Tuple[str, str]:
        """Reemplaza usos directos de random con self.random_state."""
        changes = []
        
        # Patrones de reemplazo
        replacements = [
            (r'\brandom\.random\(\)', 'self.random_state.random()'),
            (r'\brandom\.randint\(', 'self.random_state.randint('),
            (r'\brandom\.choice\(', 'self.random_state.choice('),
            (r'\brandom\.uniform\(', 'self.random_state.uniform('),
            (r'\brandom\.gauss\(', 'self.random_state.normal('),
            (r'\bnp\.random\.random\(\)', 'self.random_state.random()'),
            (r'\bnp\.random\.rand\(', 'self.random_state.rand('),
            (r'\bnp\.random\.randint\(', 'self.random_state.randint('),
            (r'\bnp\.random\.choice\(', 'self.random_state.choice('),
            (r'\bnp\.random\.uniform\(', 'self.random_state.uniform('),
            (r'\bnp\.random\.normal\(', 'self.random_state.normal('),
        ]
        
        for pattern, replacement in replacements:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes.append(f"Replaced {pattern} with {replacement}")
        
        change = f"Fixed {len(changes)} random usage patterns" if changes else ""
        return content, change
    
    def _fix_initialize_population(self, content: str) -> Tuple[str, str]:
        """Corrige el método initialize_population para usar random_state."""
        change = None
        
        # Buscar método initialize_population
        method_pattern = r'def initialize_population\(self\):(.*?)(?=\n    def|\n\nclass|\Z)'
        match = re.search(method_pattern, content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            
            # Verificar si usa Individual.initialize sin random_state
            if 'initialize()' in method_body and 'self.random_state' not in method_body:
                # Reemplazar initialize() con initialize(self.random_state)
                new_body = method_body.replace('initialize()', 'initialize(self.random_state)')
                content = content.replace(method_body, new_body)
                change = "Added self.random_state to Individual.initialize() calls"
        
        return content, change or ""
    
    def _add_docstring_seed_info(self, content: str) -> Tuple[str, str]:
        """Añade información sobre seed en docstrings."""
        change = None
        
        # Buscar docstring de la clase
        class_pattern = r'(class\s+\w+[^:]*:\s*\n\s*""")(.*?)(""")'
        match = re.search(class_pattern, content, re.DOTALL)
        
        if match:
            docstring = match.group(2)
            
            # Verificar si ya menciona seed/reproducibility
            if 'seed' not in docstring.lower() and 'reproduc' not in docstring.lower():
                # Añadir sección de reproducibilidad
                new_docstring = docstring.rstrip() + '\n\n    Reproducibility:\n        This algorithm supports full reproducibility through the seed parameter.\n        All random operations use self.random_state for deterministic behavior.\n    '
                
                content = content.replace(
                    match.group(0),
                    match.group(1) + new_docstring + match.group(3)
                )
                change = "Added reproducibility information to class docstring"
        
        return content, change or ""
    
    def generate_report(self, results: Dict[str, List[str]]) -> str:
        """
        Genera reporte de cambios aplicados.
        
        Args:
            results: Resultados del procesamiento
            
        Returns:
            Reporte en formato markdown
        """
        report = "# Reproducibility Enforcement Report\n\n"
        report += f"Mode: {'DRY RUN' if self.dry_run else 'APPLIED'}\n\n"
        
        if not results:
            report += "✅ No changes needed - all files comply with reproducibility standards!\n"
        else:
            report += f"## Summary\n\n"
            report += f"- Files modified: {len(results)}\n"
            report += f"- Total changes: {sum(len(changes) for changes in results.values())}\n\n"
            
            report += "## Changes by File\n\n"
            
            for filepath, changes in sorted(results.items()):
                report += f"### {filepath}\n\n"
                for change in changes:
                    report += f"- {change}\n"
                report += "\n"
        
        return report


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Enforce reproducibility standards in algorithm implementations'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes (default is dry run)'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='algorithms',
        help='Directory to process (default: algorithms)'
    )
    parser.add_argument(
        '--report',
        type=str,
        default='reproducibility_enforcement_report.md',
        help='Report file path'
    )
    
    args = parser.parse_args()
    
    # Crear enforcer
    enforcer = ReproducibilityEnforcer(dry_run=not args.apply)
    
    # Procesar directorio
    directory = Path(args.directory)
    if not directory.exists():
        logger.error(f"Directory {directory} does not exist")
        return 1
    
    logger.info(f"Processing directory: {directory}")
    results = enforcer.process_directory(directory)
    
    # Generar reporte
    report = enforcer.generate_report(results)
    
    # Guardar reporte
    report_path = Path(args.report)
    report_path.write_text(report)
    logger.info(f"Report saved to {report_path}")
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("REPRODUCIBILITY ENFORCEMENT SUMMARY")
    print("="*60)
    print(f"Mode: {'DRY RUN' if not args.apply else 'CHANGES APPLIED'}")
    print(f"Files analyzed: {len(list(directory.rglob('*.py')))}")
    print(f"Files modified: {len(results)}")
    print(f"Total changes: {sum(len(changes) for changes in results.values())}")
    
    if not args.apply and results:
        print("\nTo apply changes, run with --apply flag")
    
    return 0


if __name__ == '__main__':
    exit(main())