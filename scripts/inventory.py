#!/usr/bin/env python3
"""
Script para generar un inventario completo del repositorio:
- Archivos y sus características (tamaño, líneas)
- Imports entre módulos
- Archivos no referenciados
- Archivos en data/ no utilizados en tests ni scripts
"""

import os
import sys
import ast
import re
import csv
from pathlib import Path
from collections import defaultdict
import importlib.util
import json
import pandas as pd
import markdown

# Rutas a ignorar
IGNORE_DIRS = [
    '.git', '__pycache__', '.pytest_cache', '.ruff_cache', 
    'results', 'logs', 'bioalgocompare.egg-info'
]

# Extensiones a considerar para código Python
PY_EXTENSIONS = ['.py']

# Extensiones a considerar para datos
DATA_EXTENSIONS = ['.vrp', '.csv', '.json', '.txt']

def count_lines(file_path):
    """Cuenta las líneas de un archivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception as e:
        print(f"Error al leer {file_path}: {e}")
        return 0

def get_imports(file_path):
    """Extrae los imports de un archivo Python."""
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        try:
            # Intentar parsear el archivo con AST
            tree = ast.parse(content)
            
            # Buscar imports tradicionales (import X, import X as Y)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    # from X import Y
                    if node.module:
                        module = node.module
                        for name in node.names:
                            imports.append(f"{module}.{name.name}")
            
            # También buscar imports en comentarios y strings para detectar imports condicionales
            import_pattern = r'(?:from\s+(\w+(?:\.\w+)*)\s+import|\bimport\s+(\w+(?:\.\w+)*))'
            for match in re.finditer(import_pattern, content):
                import_path = match.group(1) or match.group(2)
                if import_path and import_path not in imports:
                    imports.append(import_path)
                    
        except SyntaxError as e:
            print(f"Error de sintaxis en {file_path}: {e}")
            # Intentar extraer imports solo con regex como fallback
            import_pattern = r'(?:from\s+(\w+(?:\.\w+)*)\s+import|\bimport\s+(\w+(?:\.\w+)*))'
            for match in re.finditer(import_pattern, content):
                import_path = match.group(1) or match.group(2)
                if import_path and import_path not in imports:
                    imports.append(import_path)
    
    except Exception as e:
        print(f"Error al procesar imports de {file_path}: {e}")
    
    return sorted(set(imports))

def is_local_import(import_name, module_list):
    """Determina si un import corresponde a un módulo local del proyecto."""
    # Primera parte del import (antes del primer punto)
    base_module = import_name.split('.')[0]
    
    # Verificar si el módulo base existe en la lista de módulos del proyecto
    return base_module in module_list

def scan_repository(repo_root):
    """Escanea el repositorio y recopila información de archivos e imports."""
    files_info = []
    imports_map = defaultdict(list)
    module_list = set()
    repo_path = Path(repo_root)
    
    # Primero, recopilamos la lista de todos los módulos Python del proyecto
    for root, dirs, files in os.walk(repo_root):
        # Filtrar directorios a ignorar
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                # Obtener el nombre de módulo a partir de la ruta
                file_path = Path(os.path.join(root, file))
                rel_path = file_path.relative_to(repo_path)
                
                # Convertir path/to/file.py a path.to.file
                if file == '__init__.py':
                    module_name = str(rel_path.parent).replace('/', '.')
                else:
                    module_name = str(rel_path.with_suffix('')).replace('/', '.')
                
                module_list.add(module_name)
                # También añadir el nombre del directorio para imports tipo "from dir import file"
                if '.' in module_name:
                    module_list.add(module_name.split('.')[0])
    
    # Luego, escaneamos los archivos y sus imports
    for root, dirs, files in os.walk(repo_root):
        # Filtrar directorios a ignorar
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_root)
            file_size = os.path.getsize(file_path)
            
            # Omitir archivos ocultos
            if file.startswith('.'):
                continue
                
            # Para archivos Python, contar líneas y extraer imports
            imports = []
            referenced_files = []
            lines = 0
            
            if any(file.endswith(ext) for ext in PY_EXTENSIONS):
                lines = count_lines(file_path)
                imports = get_imports(file_path)
                
                # Filtrar solo imports locales del proyecto
                local_imports = [imp for imp in imports if is_local_import(imp, module_list)]
                
                # Actualizar el mapa de imports
                for imp in local_imports:
                    # Convertir el import a ruta de archivo para añadirlo al mapa
                    parts = imp.split('.')
                    
                    # Manejar diferentes formatos de import
                    if len(parts) > 1:
                        # Puede ser un import de subpaquete o módulo
                        if os.path.exists(os.path.join(repo_root, *parts) + '.py'):
                            # Es un módulo directo: package.module
                            imp_path = os.path.join(*parts) + '.py'
                            referenced_files.append(imp_path)
                        elif os.path.exists(os.path.join(repo_root, *parts[:-1], f"{parts[-1]}.py")):
                            # Es un import desde: from package import module
                            imp_path = os.path.join(*parts[:-1], f"{parts[-1]}.py")
                            referenced_files.append(imp_path)
                        elif os.path.exists(os.path.join(repo_root, *parts[:-1], '__init__.py')):
                            # Es un import de paquete: from package import *
                            imp_path = os.path.join(*parts[:-1], '__init__.py')
                            referenced_files.append(imp_path)
                    else:
                        # Es un paquete base: import package
                        if os.path.exists(os.path.join(repo_root, parts[0], '__init__.py')):
                            imp_path = os.path.join(parts[0], '__init__.py')
                            referenced_files.append(imp_path)
                        elif os.path.exists(os.path.join(repo_root, f"{parts[0]}.py")):
                            imp_path = f"{parts[0]}.py"
                            referenced_files.append(imp_path)
            
            # Agregar información del archivo
            files_info.append({
                'path': rel_path,
                'size': file_size,
                'lines': lines,
                'imports': imports,
                'referenced_files': referenced_files
            })
            
            # Actualizar el mapa de imports para cada archivo referenciado
            for ref_file in referenced_files:
                imports_map[ref_file].append(rel_path)
    
    return files_info, imports_map, module_list

def detect_data_usage(files_info):
    """Detecta el uso de archivos de datos en scripts y tests."""
    data_usages = defaultdict(list)
    
    # Primero identificamos todos los archivos de datos
    data_files = [f['path'] for f in files_info 
                if f['path'].startswith('data/') and 
                any(f['path'].endswith(ext) for ext in DATA_EXTENSIONS)]
    
    # Luego buscamos referencias a estos archivos en el código
    for file_info in files_info:
        if any(file_info['path'].endswith(ext) for ext in PY_EXTENSIONS):
            # Leer el contenido del archivo para buscar referencias a datos
            try:
                with open(os.path.join(os.getcwd(), file_info['path']), 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Buscar referencias a archivos de datos
                    for data_file in data_files:
                        # Normalizar la ruta para búsqueda
                        data_basename = os.path.basename(data_file)
                        data_dir = os.path.dirname(data_file)
                        
                        # Patrones comunes de referencia a archivos de datos
                        patterns = [
                            re.escape(data_file),
                            re.escape(data_basename),
                            r"['\"]" + re.escape(data_dir) + r".*" + re.escape(data_basename) + r"['\"]"
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, content):
                                data_usages[data_file].append(file_info['path'])
                                break
            except Exception as e:
                print(f"Error al buscar referencias en {file_info['path']}: {e}")
    
    return data_usages

def generate_inventory_report(files_info, imports_map, module_list, data_usages):
    """Genera un informe de inventario en formato Markdown."""
    report = []
    
    # Título y descripción
    report.append("# Reporte de Inventario del Repositorio\n")
    report.append("## Análisis completo de archivos, dependencias y cobertura\n")
    
    # Resumen general
    py_files = [f for f in files_info if f['path'].endswith('.py')]
    total_py_lines = sum(f['lines'] for f in py_files)
    
    report.append("## Resumen General\n")
    report.append(f"- **Total de archivos:** {len(files_info)}")
    report.append(f"- **Archivos Python:** {len(py_files)}")
    report.append(f"- **Líneas de código Python:** {total_py_lines}")
    report.append(f"- **Módulos:** {len(module_list)}")
    report.append("")
    
    # Módulos y quién los importa
    report.append("## Módulos y quién los importa\n")
    report.append("| Módulo | Importado por | Número de referencias |")
    report.append("|--------|--------------|------------------------|")
    
    imported_modules = sorted([(k, v) for k, v in imports_map.items()], 
                             key=lambda x: len(x[1]), reverse=True)
    
    for module, references in imported_modules:
        ref_list = ", ".join([ref for ref in references[:5]])
        if len(references) > 5:
            ref_list += f" y {len(references) - 5} más"
        report.append(f"| {module} | {ref_list} | {len(references)} |")
    report.append("")
    
    # Archivos no referenciados
    report.append("## Archivos huérfanos (no referenciados)\n")
    report.append("| Archivo | Tamaño (bytes) | Líneas |")
    report.append("|---------|----------------|--------|")
    
    # Identificar archivos Python no importados
    py_files_paths = {f['path'] for f in py_files}
    referenced_paths = set()
    for refs in imports_map.values():
        referenced_paths.update(refs)

    # Excluir explícitamente algorithms/*.py y problems/vrp.py de la lista de huérfanos
    # ya que estos son modelos y problemas principales del sistema
    orphaned_files = [f for f in py_files
                     if f['path'] not in referenced_paths
                     and not f['path'].startswith('tests/')  # Los tests son "entry points"
                     and not f['path'].startswith('algorithms/')  # Los algoritmos son el núcleo del sistema
                     and not f['path'] == 'problems/vrp.py']  # El problema VRP es central
    
    # Ordenar por tamaño descendente
    orphaned_files.sort(key=lambda x: x['size'], reverse=True)
    
    for file in orphaned_files:
        report.append(f"| {file['path']} | {file['size']} | {file['lines']} |")
    report.append("")
    
    # Archivos de datos y su uso
    report.append("## Archivos de datos y su uso\n")
    report.append("| Archivo de datos | Usado por | Número de usos |")
    report.append("|------------------|-----------|----------------|")
    
    # Ordenar por número de usos descendente
    data_usage_sorted = sorted([(k, v) for k, v in data_usages.items()], 
                               key=lambda x: len(x[1]), reverse=True)
    
    for data_file, usages in data_usage_sorted:
        usage_list = ", ".join([usage for usage in usages[:5]])
        if len(usages) > 5:
            usage_list += f" y {len(usages) - 5} más"
        report.append(f"| {data_file} | {usage_list} | {len(usages)} |")
    
    # Archivos de datos sin usar
    data_files = [f['path'] for f in files_info 
                if f['path'].startswith('data/') and 
                any(f['path'].endswith(ext) for ext in DATA_EXTENSIONS)]
    unused_data = [file for file in data_files if file not in data_usages]
    
    if unused_data:
        report.append("\n### Archivos de datos no utilizados\n")
        report.append("| Archivo | Tamaño (bytes) |")
        report.append("|---------|----------------|")
        
        for file in unused_data:
            file_info = next((f for f in files_info if f['path'] == file), None)
            if file_info:
                report.append(f"| {file} | {file_info['size']} |")
    
    report.append("")
    
    # Generar y retornar el informe completo
    return "\n".join(report)

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Escaneando repositorio en: {repo_root}")
    
    files_info, imports_map, module_list = scan_repository(repo_root)
    data_usages = detect_data_usage(files_info)
    
    # Generar reporte en Markdown
    report = generate_inventory_report(files_info, imports_map, module_list, data_usages)
    
    # Guardar reporte
    report_path = os.path.join(repo_root, 'docs', 'technical', 'inventory_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Reporte de inventario generado en: {report_path}")

if __name__ == "__main__":
    main()