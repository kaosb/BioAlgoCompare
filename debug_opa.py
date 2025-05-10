#!/usr/bin/env python3
import sys
import numpy as np
from problems.vrp import VRPProblem
from algorithms.opa import OPA, Orca, _ensure_routes

# Configuración para depuración
np.set_printoptions(threshold=sys.maxsize)

# Cargar una instancia pequeña para depuración
instance_path = "data/vrp/P-n16-k8.vrp"  # Usamos una instancia pequeña
problem = VRPProblem(instance_path)

print(f"Instancia cargada: {problem.name}")
print(f"Dimensión: {problem.dimension}, Capacidad: {problem.capacity}")

# Generar una solución aleatoria
random_solution = problem.random_solution()
print("\nSolución aleatoria:")
print(f"Tipo: {type(random_solution)}")
print(f"Forma: {random_solution.shape}")
print(f"Contenido: {random_solution}")

# Probar la función _ensure_routes
print("\nProbando _ensure_routes:")
routes = _ensure_routes(random_solution)
print(f"Tipo: {type(routes)}")
print(f"Contenido: {routes}")
print(f"Longitud: {len(routes)}")

if len(routes) > 0:
    print(f"Primera ruta: {routes[0]}")
    print(f"Tipo de la primera ruta: {type(routes[0])}")
    print(f"Longitud de la primera ruta: {len(routes[0])}")

# Probar los métodos de Orca con la solución
print("\nProbando Orca:")
orca = Orca(problem)
print(f"Posición inicial: {orca.position}")
print(f"Fitness inicial: {orca.fitness()}")

# Probar los operadores discretos
print("\nProbando operadores discretos:")
if len(orca.position) > 0 and len(orca.position[0]) > 0:
    print("  _random_swap:")
    try:
        orca._random_swap(orca.position)
        print("    OK")
    except Exception as e:
        print(f"    Error: {str(e)}")
    
    if len(orca.position[0]) >= 4:
        print("  _two_opt:")
        try:
            orca._two_opt(orca.position[0])
            print("    OK")
        except Exception as e:
            print(f"    Error: {str(e)}")
    else:
        print("  _two_opt: No se puede probar, ruta demasiado corta")
    
    # Crear un g_best para pruebas
    g_best = []
    if len(orca.position) > 0:
        g_best = orca.position.copy()
    
    print("  _relocate:")
    try:
        orca._relocate(orca.position, g_best)
        print("    OK")
    except Exception as e:
        print(f"    Error: {str(e)}")

# Probar la inicialización del algoritmo
print("\nProbando inicialización de OPA:")
try:
    algo = OPA(problem, population_size=10, max_iterations=10, seed=42)
    algo.initialize_population()
    print("  Inicialización OK")
    print(f"  Tamaño de población: {len(algo.population)}")
    print(f"  Mejor fitness inicial: {algo.best_solution.fitness()}")
except Exception as e:
    print(f"  Error en inicialización: {str(e)}")

# Probar la actualización de la población
print("\nProbando OPA.update_population:")
try:
    algo.update_population()
    print("  Primera actualización OK")
    print(f"  Mejor fitness después de actualización: {algo.best_solution.fitness()}")
except Exception as e:
    print(f"  Error en actualización: {str(e)}")
    import traceback
    traceback.print_exc()

# Probar la ejecución completa con pocas iteraciones
print("\nProbando OPA.execute con pocas iteraciones:")
try:
    algo = OPA(problem, population_size=5, max_iterations=2, seed=42)
    best = algo.execute()
    print("  Ejecución OK")
    print(f"  Mejor fitness: {best.fitness()}")
    print(f"  Tiempo de ejecución: {algo.get_execution_time():.4f}s")
except Exception as e:
    print(f"  Error en ejecución: {str(e)}")
    import traceback
    traceback.print_exc()