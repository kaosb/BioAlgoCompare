import numpy as np
import random


def random_permutation(size):
    """Genera una permutación aleatoria de tamaño 'size'."""
    return np.random.permutation(size)


def random_continuous_vector(size, lower_bound=0.0, upper_bound=1.0):
    """Genera un vector aleatorio de valores continuos."""
    return np.random.uniform(lower_bound, upper_bound, size)


def sigmoid(x):
    """Función sigmoide para binarización."""
    return 1 / (1 + np.exp(-x))


def continuous_to_binary(x, threshold=0.5):
    """Convierte un vector continuo a binario usando umbral."""
    return np.where(sigmoid(x) > threshold, 1, 0)


def continuous_to_permutation(x):
    """Convierte un vector continuo a una permutación."""
    indices = list(range(len(x)))
    indices.sort(key=lambda i: x[i])
    return indices


def crossover(parent1, parent2, crossover_rate=0.7):
    """Operador de cruce uniforme."""
    if random.random() > crossover_rate:
        return parent1.copy(), parent2.copy()

    size = len(parent1)
    child1 = parent1.copy()
    child2 = parent2.copy()

    for i in range(size):
        if random.random() < 0.5:
            child1[i], child2[i] = child2[i], child1[i]

    return child1, child2


def mutation(solution, mutation_rate=0.1):
    """Operador de mutación."""
    mutated = solution.copy()
    size = len(solution)

    for i in range(size):
        if random.random() < mutation_rate:
            mutated[i] = random.random()

    return mutated


def compute_diversity(population):
    """Calcula la diversidad de la población."""
    if not population:
        return 0

    n = len(population)
    if n <= 1:
        return 0

    total_distance = 0
    for i in range(n):
        for j in range(i + 1, n):
            # Distancia euclidiana entre individuos
            distance = np.linalg.norm(population[i].position - population[j].position)
            total_distance += distance

    # Normalizar por el número de pares
    return total_distance / (n * (n - 1) / 2)


def get_diversity_state(diversity, num_states):
    """Convierte un valor de diversidad a un estado discreto."""
    # Asumimos que la diversidad está en [0, 1]
    state = int(diversity * num_states)
    return min(state, num_states - 1)


def compute_reward(previous_best, current_best, previous_diversity, current_diversity):
    """Calcula la recompensa basada en la mejora y la diversidad."""
    # Mejora en la función objetivo
    improvement = previous_best.fitness() - current_best.fitness()

    # Cambio en la diversidad
    diversity_change = current_diversity - previous_diversity

    # Recompensa combinada
    reward = improvement + 0.1 * diversity_change

    return reward
