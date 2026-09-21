import matplotlib.pyplot as plt
import numpy as np
import random
import matplotlib.colors as mcolors


def plot_vrp_solution(problem, routes, title=None):
    """
    Visualiza una solución VRP.

    Args:
        problem: Instancia del problema VRP
        routes: Lista de rutas (cada ruta es una lista de índices de nodos)
        title: Título opcional para el gráfico
    """
    plt.figure(figsize=(10, 8))

    # Extraer coordenadas
    x = [node[0] for node in problem.nodes]
    y = [node[1] for node in problem.nodes]

    # Dibujar todos los nodos
    plt.scatter(x, y, c="lightgray", s=50)

    # Resaltar el depósito
    depot_x, depot_y = problem.nodes[problem.depot_index]
    plt.scatter([depot_x], [depot_y], c="red", s=100, marker="*")

    # Colores para las rutas
    colors = list(mcolors.TABLEAU_COLORS.values())

    # Dibujar cada ruta
    for i, route in enumerate(routes):
        route_x = [problem.nodes[idx][0] for idx in route]
        route_y = [problem.nodes[idx][1] for idx in route]

        color = colors[i % len(colors)]
        plt.plot(route_x, route_y, c=color, linewidth=2, alpha=0.7)

    # Añadir etiquetas a los nodos
    for i, (xi, yi) in enumerate(zip(x, y)):
        plt.annotate(f"{i}", (xi, yi), xytext=(5, 5), textcoords="offset points")

    if title:
        plt.title(title)
    else:
        plt.title(f"VRP Solution - {len(routes)} routes")

    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    return plt


def plot_convergence(convergence_curve, title=None):
    """
    Visualiza la curva de convergencia de un algoritmo.

    Args:
        convergence_curve: Lista de valores de fitness por iteración
        title: Título opcional para el gráfico
    """
    plt.figure(figsize=(10, 6))

    iterations = list(range(1, len(convergence_curve) + 1))
    plt.plot(iterations, convergence_curve, "b-", linewidth=2)

    if title:
        plt.title(title)
    else:
        plt.title("Convergence Curve")

    plt.xlabel("Iteration")
    plt.ylabel("Fitness (Distance)")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    return plt


def compare_algorithms(results_dict, title=None):
    """
    Compara las curvas de convergencia de varios algoritmos.

    Args:
        results_dict: Diccionario con nombres de algoritmos como claves y curvas de convergencia como valores
        title: Título opcional para el gráfico
    """
    plt.figure(figsize=(12, 8))

    for algo_name, curve in results_dict.items():
        iterations = list(range(1, len(curve) + 1))
        plt.plot(iterations, curve, linewidth=2, label=algo_name)

    if title:
        plt.title(title)
    else:
        plt.title("Algorithm Comparison")

    plt.xlabel("Iteration")
    plt.ylabel("Fitness (Distance)")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()

    return plt
