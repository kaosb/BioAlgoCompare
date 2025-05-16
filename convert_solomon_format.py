#!/usr/bin/env python3
"""
Script para convertir archivos Solomon 101 al formato requerido por VRPProblem
"""

import os
import sys
import re
from pathlib import Path
import argparse

def extract_data_from_solomon(file_path):
    """
    Extrae datos de un archivo Solomon en formato original
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Extraer nombre
    name = lines[0].strip()
    
    # Extraer capacidad
    capacity_line = None
    for i, line in enumerate(lines):
        if "CAPACITY" in line:
            capacity_line = i
            break
    
    if capacity_line is None:
        raise ValueError("No se encontró la línea de capacidad")
    
    capacity = lines[capacity_line + 1].strip().split()[-1]
    
    # Extraer coordenadas y demandas
    customer_line = None
    for i, line in enumerate(lines):
        if "CUSTOMER" in line:
            customer_line = i
            break
    
    if customer_line is None:
        raise ValueError("No se encontró la sección de clientes")
    
    nodes = []
    demands = []
    
    for line in lines[customer_line + 2:]:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        if len(parts) < 7:
            continue
        
        try:
            # Convertir a enteros/flotantes para validar
            node_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            demand = int(parts[3])
            
            nodes.append((node_id, x, y))
            demands.append((node_id, demand))
        except (ValueError, IndexError):
            continue
    
    return {
        "name": name,
        "capacity": capacity,
        "nodes": nodes,
        "demands": demands,
        "dimension": len(nodes)
    }

def convert_to_vrp_format(data, output_path):
    """
    Convierte los datos extraídos al formato VRP requerido por el parser
    """
    with open(output_path, 'w') as f:
        # Escribir encabezado original
        f.write(f"{data['name']}\n\n")
        f.write("VEHICLE\n")
        f.write("NUMBER     CAPACITY\n")
        f.write(f"  25         {data['capacity']}\n\n")
        f.write("CUSTOMER\n")
        f.write("CUST NO.   XCOORD.   YCOORD.    DEMAND   READY TIME   DUE DATE   SERVICE TIME\n")
        f.write(" \n")
        
        # Ordenar nodos por id
        sorted_nodes = sorted(data['nodes'], key=lambda x: x[0])
        demands_dict = {d[0]: d[1] for d in data['demands']}
        
        # Escribir datos de clientes (conservamos la parte original)
        for node_id, x, y in sorted_nodes:
            f.write(f"{node_id:5d}      {x:<9.0f} {y:<9.0f} {demands_dict[node_id]:<9d}")
            # Agregar valores ficticios para ready time, due date y service time
            # (estos valores no son utilizados en VRP básico)
            if node_id == 0:  # Depósito
                f.write(f"{0:<10d} {1236:<11d} {0:<3d}   \n")
            else:
                f.write(f"{10:<10d} {100:<11d} {90:<3d}  \n")
        
        # Agregar secciones requeridas por el parser VRPProblem
        f.write(f"\nNAME : {data['name']}\n")
        f.write(f"DIMENSION : {data['dimension']}\n")
        f.write(f"CAPACITY : {data['capacity']}\n")
        
        # Sección de coordenadas
        f.write("NODE_COORD_SECTION\n")
        for node_id, x, y in sorted_nodes:
            f.write(f"{node_id} {x} {y}\n")
        
        # Sección de demandas
        f.write("DEMAND_SECTION\n")
        for node_id, x, y in sorted_nodes:
            f.write(f"{node_id} {demands_dict[node_id]}\n")
        
        # Sección de depósito
        f.write("DEPOT_SECTION\n")
        f.write("0\n")
        f.write("-1\n")
        f.write("EOF")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Convierte archivos Solomon 101 al formato requerido por VRPProblem")
    parser.add_argument("files", nargs="+", help="Archivos o patrones a convertir")
    parser.add_argument("--output-dir", "-o", default=None, help="Directorio de salida (por defecto, sobrescribe los originales)")
    
    args = parser.parse_args()
    
    # Expandir patrones glob
    import glob
    all_files = []
    for pattern in args.files:
        matched = glob.glob(pattern)
        if matched:
            all_files.extend(matched)
        else:
            print(f"Advertencia: No se encontraron archivos para '{pattern}'")
    
    if not all_files:
        print("Error: No se encontraron archivos para procesar")
        sys.exit(1)
    
    for file_path in all_files:
        try:
            print(f"Procesando: {file_path}")
            data = extract_data_from_solomon(file_path)
            
            # Determinar ruta de salida
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(exist_ok=True, parents=True)
                output_path = output_dir / Path(file_path).name
            else:
                output_path = file_path
            
            # Convertir y guardar
            convert_to_vrp_format(data, output_path)
            print(f"  Convertido exitosamente: {output_path}")
        
        except Exception as e:
            print(f"  Error al procesar {file_path}: {str(e)}")
    
    print("Conversión completada.")

if __name__ == "__main__":
    main()
