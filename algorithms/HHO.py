import random as rnd
import copy
import time

class Hawk:
    def __init__(self):
        self.nVariables = Problem.subnetworks
        self.x = [rnd.randint(0, 1) for _ in range(self.nVariables)]  # Posición inicial del halcón
        self.E0 = rnd.uniform(-1, 1)  # Energía inicial del halcón
        self.E = self.E0  # Energía actual
        self.D = [0] * self.nVariables  # Diferencia entre el halcón y la presa
        self.q = rnd.random()  # Factor aleatorio para exploración/explotación
        self.r = rnd.random()  # Parámetro aleatorio para el comportamiento de caza
    
    def is_better_than(self, g):
        return self.scalering() <= g.scalering()

    def scalering(self):
        return abs(self.fitness_z1() * (-1) + self.fitness_z2() + self.fitness_z3() * (-1))

    def fitness_z1(self):
        return sum(x * cost for x, cost in zip(self.x, Problem.costs))

    def fitness_z2(self):
        return sum(x * direct for x, direct in zip(self.x, Problem.directs))

    def fitness_z3(self):
        return sum(x * indirect for x, indirect in zip(self.x, Problem.indirects))

    def is_feasible(self):
        return self.is_feasible_probability() and self.is_feasible_cover()

    def is_feasible_probability(self):
        sum_num = sum(prob * (1 - xi) for prob, xi in zip(Problem.probabilities, self.x))
        sum_den = sum(Problem.probabilities)
        return sum_num / sum_den <= 1 - Problem.umbral

    def is_feasible_cover(self):
        return any(self.x)

    def move(self, g):
        for j in range(self.nVariables):
            self.E = 2 * self.E0 * rnd.random() - self.E0  # Energía del halcón actualizada
            if abs(self.E) >= 1:  # Exploración
                self.q = rnd.random()  # Parámetro aleatorio de exploración
                if self.q < 0.5:
                    self.D[j] = abs(self.C[j] * g.x[j] - self.x[j])
                    self.x[j] = g.x[j] - self.E * self.D[j]
                else:
                    self.x[j] = rnd.uniform(0, 1)  # Saltos aleatorios para explorar
            else:  # Explotación (cuando la energía es baja)
                if self.r >= 0.5 and abs(self.E) < 0.5:  # Espiral descendente (ataque suave)
                    self.D[j] = abs(g.x[j] - self.x[j])
                    self.x[j] = self.D[j] * math.exp(self.E) * math.cos(2 * math.pi * self.E) + g.x[j]
                elif self.r < 0.5 and abs(self.E) >= 0.5:  # Ataque fuerte (asalto rápido)
                    self.D[j] = abs(g.x[j] - self.x[j])
                    self.x[j] = g.x[j] - self.E * abs(g.x[j] - self.x[j])

    def update_energy(self, max_iterations, current_iteration):
        self.E0 = 2 * (1 - current_iteration / max_iterations)  # La energía decrece con las iteraciones

    def copy(self, other):
        if isinstance(other, Hawk):
            self.x = other.x.copy()

    def sum(self):
        return sum(self.x)

    def __str__(self):
        return f"{self.x}, {self.scalering()}, {self.sum()}, {self.nVariables}"


class HHO:
    def __init__(self):
        self.nHawks = 10  # Número de halcones
        self.T = 100  # Número de iteraciones

        self.flock = None  # Enjambre de halcones
        self.g = None  # Mejor solución global
        self.sTime = 0
        self.eTime = 0
        # Parámetros para Q-learning
        self.num_states = 10
        self.actions = [
            (0.75, 1.25),
            (0.85, 1.15),
            (0.65, 1.35),
            # ... otras combinaciones pueden ser agregadas
        ]
        self.num_actions = len(self.actions)
        self.q_learner = QLearner(self.num_states, self.num_actions)

    def execute(self):
        self.start_time()
        self.init()
        self.run()
        self.end_time()
        self.log()

    def start_time(self):
        self.sTime = time.time()

    def init(self):
        self.flock = []
        self.g = Hawk()  # Instancia de la mejor ballena (solución)
        w = None
        for _ in range(1, self.nHawks + 1):
            while True:
                w = Hawk()
                if w.is_feasible():
                    break
            self.flock.append(w)

        # Encontrar la mejor ballena inicial
        self.g.copy(self.flock[0])
        for i in range(1, self.nHawks):
            if self.flock[i].is_better_than(self.g):
                self.g.copy(self.flock[i])

    def run(self):
        t = 1
        w = Hawk()
        while t <= self.T:
            # Guardar una copia profunda del mejor halcón actual
            previous_g = copy.deepcopy(self.g)

            # Calcular la diversidad del enjambre actual
            previous_diversity = Utils.compute_diversity(self.flock)

            # Obtener el estado actual basado en la diversidad
            current_state = Utils.get_diversity_state(previous_diversity, self.num_states)

            # Elegir una acción usando Q-learning
            action_idx = self.q_learner.choose_action(current_state)

            # Actualizar los parámetros de HHO basados en la acción elegida
            self.fmin, self.fmax = self.actions[action_idx]

            for i in range(self.nHawks):
                while True:
                    w.copy(self.flock[i])
                    w.move(self.g)

                    if w.is_feasible():
                        break

                if w.is_better_than(self.flock[i]):
                    self.flock[i].copy(w)

                if w.is_better_than(self.g):
                    self.g.copy(w)

            # Calcular la recompensa basada en la mejora de la función objetivo y la diversidad
            current_g = self.g
            current_diversity = Utils.compute_diversity(self.flock)
            reward = Utils.compute_reward(previous_g, current_g, previous_diversity, current_diversity)

            # Actualizar la tabla Q con la recompensa obtenida
            next_state = Utils.get_diversity_state(current_diversity, self.num_states)
            self.q_learner.update_q_table(current_state, action_idx, reward, next_state)

            t += 1
          #  print(f"{self.g}")

    def end_time(self):
        self.eTime = time.time()

    def log(self):
        print(f"{self.g}\t t={self.eTime - self.sTime}")

    def dist(self):
        dist = 0
        for i in range(self.nHawks):
            dist += abs(self.flock[i].scalering() - self.g.scalering())
        return dist

    def average(self):
        data = [w.E for w in self.flock]  # Calcula el promedio de las energías de los halcones
        return sum(data) / len(data)