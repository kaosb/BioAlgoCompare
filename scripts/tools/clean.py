#!/usr/bin/env python3
"""
Script para limpiar archivos temporales y de caché del proyecto.
"""

import os
import shutil
import click
from pathlib import Path


@click.command()
@click.option('--dry-run', is_flag=True, help='Mostrar qué se eliminaría sin eliminar')
@click.option('--all', 'clean_all', is_flag=True, help='Limpiar todo incluyendo resultados')
def clean(dry_run, clean_all):
    """Limpia archivos temporales y de caché del proyecto."""
    
    project_root = Path(__file__).parent.parent.parent
    
    # Patrones de archivos a eliminar
    patterns = [
        '**/__pycache__',
        '**/*.pyc',
        '**/*.pyo',
        '**/*~',
        '**/*.bak',
        '**/.DS_Store',
        '**/.coverage',
        '**/.pytest_cache',
        '**/htmlcov',
        '**/*.egg-info',
        'build/',
        'dist/',
    ]
    
    if clean_all:
        patterns.extend([
            'results/**/*.json',
            'results/**/*.csv',
            'plots/**/*.png',
            'plots/**/*.pdf',
            'checkpoints/**/*',
        ])
    
    files_removed = 0
    dirs_removed = 0
    
    click.echo("🧹 Limpiando archivos temporales...")
    
    for pattern in patterns:
        for path in project_root.glob(pattern):
            # Ignorar venv y .git
            if any(part in str(path) for part in ['.git', 'venv', 'env']):
                continue
                
            if dry_run:
                click.echo(f"  Se eliminaría: {path}")
            else:
                if path.is_dir():
                    shutil.rmtree(path)
                    dirs_removed += 1
                else:
                    path.unlink()
                    files_removed += 1
    
    # Limpiar archivos vacíos en results si no es clean_all
    if not clean_all:
        results_dir = project_root / 'results'
        if results_dir.exists():
            for file in results_dir.rglob('*'):
                if file.is_file() and file.stat().st_size == 0:
                    if dry_run:
                        click.echo(f"  Se eliminaría archivo vacío: {file}")
                    else:
                        file.unlink()
                        files_removed += 1
    
    # Recrear directorios necesarios si fueron eliminados
    if not dry_run:
        for dir_name in ['results', 'plots', 'checkpoints']:
            dir_path = project_root / dir_name
            dir_path.mkdir(exist_ok=True)
    
    # Resumen
    if dry_run:
        click.echo("\n⚠️  Modo dry-run: no se eliminó nada")
        click.echo("   Ejecuta sin --dry-run para eliminar los archivos")
    else:
        click.echo(f"\n✅ Limpieza completada:")
        click.echo(f"   - {files_removed} archivos eliminados")
        click.echo(f"   - {dirs_removed} directorios eliminados")
        
        # Tamaño liberado (aproximado)
        click.echo(f"\n💾 Espacio liberado: ~{(files_removed * 10 + dirs_removed * 100) / 1024:.1f} MB")


if __name__ == '__main__':
    clean()