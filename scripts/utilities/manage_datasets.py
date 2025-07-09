#!/usr/bin/env python3
"""
Script para gestionar datasets del proyecto BioAlgoCompare.
Verifica disponibilidad, descarga faltantes y crea enlaces simbólicos.
"""

import os
import sys
import shutil
import urllib.request
import zipfile
from pathlib import Path
import click

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class DatasetManager:
    """Gestor de datasets para el proyecto."""
    
    def __init__(self, data_dir="data/vrp"):
        self.data_dir = Path(data_dir)
        self.solomon_dir = self.data_dir / "Solomon"
        self.converted_dir = self.solomon_dir / "converted"
        
        # Datasets esperados de Solomon
        self.solomon_instances = [
            "R101", "R102", "R103", "R104", "R105",
            "C101", "C102", "C103", "C104", "C105",
            "RC101", "RC102", "RC103", "RC104", "RC105",
            "R201", "R202", "R203", "R204", "R205",
            "C201", "C202", "C203", "C204", "C205",
            "RC201", "RC202", "RC203", "RC204", "RC205"
        ]
        
        # Datasets pequeños para pruebas
        self.test_instances = [
            "P-n16-k8", "P-n19-k2", "P-n20-k2",
            "E-n22-k4", "E-n23-k3", "E-n30-k3",
            "A-n32-k5", "A-n33-k5", "A-n33-k6",
            "B-n31-k5", "B-n35-k5", "B-n38-k6"
        ]
    
    def check_datasets(self):
        """Verifica qué datasets están disponibles."""
        print("🔍 Verificando datasets disponibles...\n")
        
        # Verificar directorio principal
        if not self.data_dir.exists():
            print(f"❌ Directorio de datos no existe: {self.data_dir}")
            return False
        
        # Verificar instancias de prueba
        print("📦 Instancias de prueba:")
        test_available = []
        test_missing = []
        
        for instance in self.test_instances:
            path = self.data_dir / f"{instance}.vrp"
            if path.exists():
                test_available.append(instance)
            else:
                test_missing.append(instance)
        
        print(f"  ✅ Disponibles: {len(test_available)}/{len(self.test_instances)}")
        if test_missing:
            print(f"  ❌ Faltantes: {', '.join(test_missing[:5])}{'...' if len(test_missing) > 5 else ''}")
        
        # Verificar instancias Solomon
        print(f"\n📦 Instancias Solomon:")
        solomon_available = []
        solomon_missing = []
        
        for instance in self.solomon_instances:
            # Buscar en diferentes ubicaciones
            locations = [
                self.solomon_dir / f"{instance}.vrp",
                self.converted_dir / f"{instance}.vrp"
            ]
            
            found = False
            for loc in locations:
                if loc.exists():
                    solomon_available.append(instance)
                    found = True
                    break
            
            if not found:
                solomon_missing.append(instance)
        
        print(f"  ✅ Disponibles: {len(solomon_available)}/{len(self.solomon_instances)}")
        if solomon_missing:
            print(f"  ❌ Faltantes: {', '.join(solomon_missing[:5])}{'...' if len(solomon_missing) > 5 else ''}")
        
        return len(test_missing) == 0 and len(solomon_missing) == 0
    
    def fix_solomon_paths(self):
        """Crea enlaces simbólicos para que Solomon esté disponible en el path esperado."""
        print("\n🔧 Arreglando paths de Solomon...")
        
        if not self.solomon_dir.exists():
            self.solomon_dir.mkdir(parents=True, exist_ok=True)
        
        fixed = 0
        for instance in self.solomon_instances:
            main_path = self.solomon_dir / f"{instance}.vrp"
            converted_path = self.converted_dir / f"{instance}.vrp"
            
            # Si existe en converted pero no en principal
            if converted_path.exists() and not main_path.exists():
                # Copiar en lugar de enlace simbólico para evitar problemas
                shutil.copy2(converted_path, main_path)
                fixed += 1
                print(f"  ✅ Copiado: {instance}.vrp")
        
        if fixed > 0:
            print(f"\n  📋 Total arreglados: {fixed} archivos")
        else:
            print("  ℹ️  No se necesitaron arreglos")
    
    def create_test_instances(self):
        """Crea instancias sintéticas pequeñas para pruebas rápidas."""
        print("\n🏗️  Creando instancias de prueba sintéticas...")
        
        test_dir = self.data_dir / "test"
        test_dir.mkdir(exist_ok=True)
        
        # Crear instancia mínima de prueba
        test_instance = """NAME : test-n5-k2
COMMENT : Synthetic test instance with 5 nodes and 2 vehicles
TYPE : CVRP
DIMENSION : 5
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 100
NODE_COORD_SECTION
1 0 0
2 10 0
3 10 10
4 0 10
5 5 5
DEMAND_SECTION
1 0
2 20
3 30
4 25
5 15
DEPOT_SECTION
1
-1
EOF
"""
        
        test_path = test_dir / "test-n5-k2.vrp"
        with open(test_path, 'w') as f:
            f.write(test_instance)
        
        print(f"  ✅ Creada instancia de prueba: {test_path}")
        
        # Crear otra instancia un poco más grande
        test_instance2 = """NAME : test-n10-k3
COMMENT : Synthetic test instance with 10 nodes and 3 vehicles
TYPE : CVRP
DIMENSION : 10
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 150
NODE_COORD_SECTION
1 50 50
2 60 40
3 70 50
4 60 60
5 40 60
6 30 50
7 40 40
8 50 30
9 50 70
10 50 50
DEMAND_SECTION
1 0
2 20
3 30
4 25
5 15
6 35
7 20
8 25
9 30
10 20
DEPOT_SECTION
1
-1
EOF
"""
        
        test_path2 = test_dir / "test-n10-k3.vrp"
        with open(test_path2, 'w') as f:
            f.write(test_instance2)
        
        print(f"  ✅ Creada instancia de prueba: {test_path2}")
    
    def download_missing_datasets(self):
        """Descarga datasets faltantes (placeholder - requiere URLs reales)."""
        print("\n📥 Descarga de datasets faltantes...")
        print("  ⚠️  Nota: La descarga automática requiere URLs de fuentes oficiales")
        print("  📌 Por favor, descarga manualmente de:")
        print("     - CVRPLIB: http://vrp.atd-lab.inf.puc-rio.br/index.php/en/")
        print("     - Solomon: https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/")
    
    def generate_report(self):
        """Genera un reporte del estado de los datasets."""
        report_path = self.data_dir / "dataset_status.txt"
        
        with open(report_path, 'w') as f:
            f.write("Dataset Status Report\n")
            f.write("===================\n\n")
            
            # Listar todos los archivos VRP
            vrp_files = sorted(self.data_dir.rglob("*.vrp"))
            f.write(f"Total VRP files: {len(vrp_files)}\n\n")
            
            f.write("Available files:\n")
            for file in vrp_files:
                relative_path = file.relative_to(self.data_dir)
                f.write(f"  - {relative_path}\n")
        
        print(f"\n📄 Reporte generado: {report_path}")


@click.command()
@click.option('--check', is_flag=True, help='Solo verificar datasets disponibles')
@click.option('--fix', is_flag=True, help='Arreglar paths de Solomon')
@click.option('--create-test', is_flag=True, help='Crear instancias de prueba')
@click.option('--all', is_flag=True, help='Ejecutar todas las operaciones')
def main(check, fix, create_test, all):
    """Gestiona los datasets del proyecto BioAlgoCompare."""
    
    manager = DatasetManager()
    
    print("🚀 BioAlgoCompare Dataset Manager")
    print("="*40 + "\n")
    
    if all or check:
        manager.check_datasets()
    
    if all or fix:
        manager.fix_solomon_paths()
    
    if all or create_test:
        manager.create_test_instances()
    
    if not (check or fix or create_test or all):
        # Si no se especifica nada, hacer check por defecto
        manager.check_datasets()
        print("\n💡 Usa --help para ver todas las opciones")
    
    # Siempre generar reporte
    manager.generate_report()
    
    print("\n✨ Proceso completado")


if __name__ == "__main__":
    main()