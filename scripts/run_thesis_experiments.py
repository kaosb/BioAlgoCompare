#!/usr/bin/env python3
"""
Script principal para ejecutar experimentos de tesis con configuración de máximo rigor.
Basado en estándares CEC y literatura de benchmarking (Derrac et al., 2011).
"""

import os
import sys
import json
import subprocess
from datetime import datetime
import argparse

# Cargar configuración estándar
CONFIG_PATH = "config/experimental_standards.json"

def load_configuration():
    """Cargar configuración experimental estándar."""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def get_preset(config, preset_name):
    """Obtener configuración preset."""
    if preset_name not in config['presets']:
        print(f"❌ Error: Preset '{preset_name}' no encontrado.")
        print(f"Presets disponibles: {list(config['presets'].keys())}")
        sys.exit(1)
    return config['presets'][preset_name]

def build_command(preset, output_dir=None):
    """Construir comando de ejecución."""
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"experimental_results/thesis_{timestamp}"

    cmd = [
        "python", "scripts/analyze.py", "benchmark",
        "--run-benchmark",
        "--algorithms", ",".join(preset['algorithms']),
        "--instances", ",".join(preset['instances']),
        "--runs", str(preset['runs']),
        "--iterations", str(preset['iterations']),
        "--population", str(preset['population']),
        "--output-dir", output_dir
    ]

    # Agregar opciones adicionales si existen
    if preset.get('seed'):
        cmd.extend(["--seed", str(preset['seed'])])
    if preset.get('parallel'):
        cmd.append("--parallel")

    return cmd

def estimate_time(preset):
    """Estimar tiempo de ejecución."""
    total_experiments = len(preset['algorithms']) * len(preset['instances']) * preset['runs']
    time_per_exp = 0.25  # minutos promedio
    total_minutes = total_experiments * time_per_exp

    # Con paralelización (8 cores)
    parallel_minutes = total_minutes / 8

    return {
        'total_experiments': total_experiments,
        'sequential_hours': total_minutes / 60,
        'parallel_hours': parallel_minutes / 60
    }

def main():
    parser = argparse.ArgumentParser(description='Ejecutar experimentos de tesis con máximo rigor')
    parser.add_argument('--preset', type=str, default='thesis_clei2025',
                        help='Preset de configuración a usar')
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostrar comando sin ejecutar')
    parser.add_argument('--output-dir', type=str,
                        help='Directorio de salida personalizado')

    args = parser.parse_args()

    # Cargar configuración
    config = load_configuration()
    preset = get_preset(config, args.preset)

    # Información del experimento
    print("="*70)
    print("🔬 CONFIGURACIÓN EXPERIMENTAL DE MÁXIMO RIGOR")
    print("="*70)
    print(f"Preset: {args.preset}")
    print(f"Algoritmos ({len(preset['algorithms'])}): {', '.join(preset['algorithms'])}")
    print(f"Instancias ({len(preset['instances'])}): {', '.join(preset['instances'])}")
    print(f"Runs por combinación: {preset['runs']}")
    print(f"Iteraciones: {preset['iterations']}")
    print(f"Población: {preset['population']}")

    # Estimación de tiempo
    time_est = estimate_time(preset)
    print(f"\n📊 ESTIMACIÓN:")
    print(f"Total experimentos: {time_est['total_experiments']}")
    print(f"Tiempo secuencial: {time_est['sequential_hours']:.1f} horas")
    print(f"Tiempo paralelo (8 cores): {time_est['parallel_hours']:.1f} horas")

    # Construir comando
    cmd = build_command(preset, args.output_dir)

    print(f"\n💻 COMANDO:")
    print(" ".join(cmd))

    if args.dry_run:
        print("\n✅ Modo dry-run - No se ejecutará el comando")
        return

    # Confirmación
    print(f"\n⚠️  Este experimento tomará aproximadamente {time_est['parallel_hours']:.1f} horas.")
    response = input("¿Deseas continuar? (s/n): ")

    if response.lower() != 's':
        print("❌ Experimento cancelado")
        return

    # Ejecutar
    print("\n🚀 Iniciando experimentos...")
    print("="*70)

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Experimentos completados exitosamente!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Experimento interrumpido por el usuario")
        print("Nota: Puedes reanudar usando --resume en el comando original")
        sys.exit(1)

if __name__ == "__main__":
    main()
