import random as rnd
import copy
import time

class MRFO:
    def __init__(self):
        self.nRays = 10  # Número de mantarrayas
        self.T = 100  # Número de iteraciones

        self.flock = None  # Enjambre de mantarrayas
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
        self.g = MantaRay()  # Instancia de la mejor mantarraya (solución)
        m = None
        for _ in range(1, self.nRays + 1):
            while True:
                m = MantaRay()
                if m.is_feasible():
                    break
            self.flock.append(m)

        # Encontrar la mejor mantarraya inicial
        self.g.copy(self.flock[0])
        for i in range(1, self.nRays):
            if self.flock[i].is_better_than(self.g):
                self.g.copy(self.flock[i])

    def run(self):
        t = 1
        m = MantaRay()
        while t <= self.T:
            # Guardar una copia profunda de la mejor mantarraya actual
            previous_g = copy.deepcopy(self.g)

            # Calcular la diversidad del enjambre actual
            previous_diversity = Utils.compute_diversity(self.flock)

            # Obtener el estado actual basado en la diversidad
            current_state = Utils.get_diversity_state(previous_diversity, self.num_states)

            # Elegir una acción usando Q-learning
            action_idx = self.q_learner.choose_action(current_state)

            # Actualizar los parámetros de MRFO basados en la acción elegida
            self.fmin, self.fmax = self.actions[action_idx]

            for i in range(self.nRays):
                while True:
                    m.copy(self.flock[i])
                    m.move(self.g)

                    if m.is_feasible():
                        break

                if m.is_better_than(self.flock[i]):
                    self.flock[i].copy(m)

                if m.is_better_than(self.g):
                    self.g.copy(m)

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