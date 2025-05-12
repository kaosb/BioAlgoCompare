"""
Operadores genéricos para algoritmos metaheurísticos.
Incluye operadores de cruce, mutación, selección, reparación, etc.
"""
import numpy as np


def sbx_crossover(parent1, parent2, probability=0.9, distribution_index=15):
    """
    Cruce binario simulado (SBX).
    
    Args:
        parent1: Vector de genes del primer padre
        parent2: Vector de genes del segundo padre
        probability: Probabilidad de aplicar el cruce
        distribution_index: Índice de distribución (mayor = más parecido a padres)
        
    Returns:
        Nuevo vector de genes resultante del cruce
    """
    child = np.copy(parent1)
    
    if np.random.random() <= probability:
        for i in range(len(parent1)):
            if np.random.random() <= 0.5:
                y1, y2 = parent1[i], parent2[i]
                
                if abs(y1 - y2) > 1e-10:
                    if y1 > y2:
                        y1, y2 = y2, y1
                    
                    # Calcular beta
                    rand = np.random.random()
                    beta = 1.0 + (2.0 * (y1 - 0.0) / (y2 - y1))
                    alpha = 2.0 - beta ** (-(distribution_index + 1.0))
                    
                    if rand <= (1.0 / alpha):
                        beta_q = (rand * alpha) ** (1.0 / (distribution_index + 1.0))
                    else:
                        beta_q = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (distribution_index + 1.0))
                    
                    # Calcular hijo
                    c = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))
                    
                    # Limitar al rango [0, 1]
                    c = max(0.0, min(1.0, c))
                    
                    child[i] = c
    
    return child


def polynomial_mutation(solution, probability=0.1, distribution_index=20):
    """
    Mutación polinomial.
    
    Args:
        solution: Vector de genes a mutar
        probability: Probabilidad de mutar cada gen
        distribution_index: Índice de distribución (mayor = cambios más pequeños)
        
    Returns:
        Vector mutado
    """
    mutated = np.copy(solution)
    
    for i in range(len(solution)):
        if np.random.random() <= probability:
            y = solution[i]
            lb, ub = 0.0, 1.0  # Límites inferior y superior
            
            # Calcular delta
            delta1 = (y - lb) / (ub - lb)
            delta2 = (ub - y) / (ub - lb)
            
            rand = np.random.random()
            mut_pow = 1.0 / (distribution_index + 1.0)
            
            if rand < 0.5:
                xy = 1.0 - delta1
                val = 2.0 * rand + (1.0 - 2.0 * rand) * (xy ** (distribution_index + 1.0))
                deltaq = val ** mut_pow - 1.0
            else:
                xy = 1.0 - delta2
                val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * (xy ** (distribution_index + 1.0))
                deltaq = 1.0 - val ** mut_pow
            
            y = y + deltaq * (ub - lb)
            y = max(lb, min(ub, y))  # Mantener en rango
            
            mutated[i] = y
    
    return mutated


def repair_bounds(solution, lb=0.0, ub=1.0):
    """
    Repara una solución para mantenerla dentro de los límites.
    
    Args:
        solution: Vector de genes a reparar
        lb: Límite inferior
        ub: Límite superior
        
    Returns:
        Vector reparado
    """
    return np.clip(solution, lb, ub)