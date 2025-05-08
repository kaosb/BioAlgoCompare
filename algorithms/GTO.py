import random as rnd
import copy
import time

class Gorilla:
    def __init__(self):
        self.nVariables = Problem.subnetworks
        self.x = [rnd.randint(0, 1) for _ in range(self.nVariables)]  # Posición inicial del gorila
        self.fitness = None  # Fitness de la solución
        self.D = [0] * self.nVariables  # Diferencia entre el gorila y la mejor solución

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
            r = rnd.random()  # Aleatorio entre 0 y 1
            if r < 0.5:  # Movimiento de exploración
                self.D[j] = abs(g.x[j] - self.x[j])
                self.x[j] = g.x[j] - r * self.D[j]
            else:  # Movimiento de ataque
                self.D[j] = abs(g.x[j] - self.x[j])
                self.x[j] = self.x[j] + r * (g.x[j] - self.x[j])
            self.x[j] = 1 if (1 / (1 + math.exp(-self.x[j]))) > rnd.uniform(0, 1) else 0

    def copy(self, other):
        if isinstance(other, Gorilla):
            self.x = other.x.copy()

class GTO:
    def __init__(self):
        self.nGorillas = 10  # Número de gorilas
        self.T = 100  # Número de iteraciones

        self.flock = None  # Enjambre de gorilas
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
        self.g = Gorilla()  # Instancia de la mejor solución
        g = None
        for _ in range(1, self.nGorillas + 1):
            while True:
                g = Gorilla()
                if g.is_feasible():
                    break
            self.flock.append(g)

        # Encontrar el mejor gorila inicial
        self.g.copy(self.flock[0])
        for i in range(1, self.nGorillas):
            if self.flock[i].is_better_than(self.g):
                self.g.copy(self.flock[i])

    def run(self):
        t = 1
        g = Gorilla()
        while t <= self.T:
            # Guardar una copia profunda del mejor gorila actual
            previous_g = copy.deepcopy(self.g)

            # Calcular la diversidad del enjambre actual
            previous_diversity = Utils.compute_diversity(self.flock)

            # Obtener el estado actual basado en la diversidad
            current_state = Utils.get_diversity_state(previous_diversity, self.num_states)

            # Elegir una acción usando Q-learning
            action_idx = self.q_learner.choose_action(current_state)

            # Actualizar los parámetros de GTO basados en la acción elegida
            self.fmin, self.fmax = self.actions[action_idx]

            for i in range(self.nGorillas):
                while True:
                    g.copy(self.flock[i])
                    g.move(self.g)

                    if g.is_feasible():
                        break

                if g.is_better_than(self.flock[i]):
                    self.flock[i].copy(g)

                if g.is_better_than(self.g):
                    self.g.copy(g)

            # Calcular la recompensa basada en la mejora de la función objetivo y la diversidad
            current_g = self.g
            current_diversity = Utils.compute_diversity(self.flock)
            reward = Utils.compute_reward(previous_g, current_g, previous_diversity, current_diversity)

            # Actualizar la tabla Q con la recompensa obtenida
            next_state = Utils.get_diversity_state(current_diversity, self.num_states)
            self.q_learner.update_q_table(current_state, action_idx, reward, next_state)

            t += 1

    def end_time(self):
        self.eTime = time.time()

    def log(self):
        print(f"{self.g}\t t={self.eTime - self.sTime}")