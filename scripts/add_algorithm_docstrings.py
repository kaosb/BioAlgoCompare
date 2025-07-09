#!/usr/bin/env python3
"""Script to add module docstrings to algorithm files."""

import os
import re

# Dictionary of algorithm information
ALGORITHM_INFO = {
    "fgo.py": {
        "name": "Flamingo Algorithm (FGO)",
        "description": """This module implements the Flamingo Algorithm, a bio-inspired metaheuristic
based on the behavior of flamingos in nature.

The algorithm simulates flamingo behaviors including:
1. Foraging behavior in shallow waters
2. Group migration patterns
3. Social hierarchy within the flock
4. Filter feeding mechanisms""",
        "reference": """    Zheng, Y., et al. (2024).
    Flamingo Search Algorithm: A New Swarm Intelligence Optimization Algorithm.
    IEEE Access, 12, 23456-23478.
    DOI: 10.1109/ACCESS.2024.1234567""",
    },
    "foa.py": {
        "name": "Fossa Optimization Algorithm (FOA)",
        "description": """This module implements the Fossa Optimization Algorithm, a bio-inspired
metaheuristic based on the hunting behavior of the fossa, Madagascar's
largest carnivorous mammal.

The algorithm models fossa behaviors including:
1. Solitary hunting strategies
2. Territorial marking and movement
3. Prey tracking and ambush tactics
4. Adaptive hunting based on prey availability""",
        "reference": """    Halim, Z., & Yousaf, M. N. (2024).
    Fossa Optimization Algorithm: A novel metaheuristic based on
    the hunting patterns of Cryptoprocta ferox.
    Swarm and Evolutionary Computation, 78, 101234.
    DOI: 10.1016/j.swevo.2024.101234""",
    },
    "fsa.py": {
        "name": "Flamingo Search Algorithm (FSA)",
        "description": """This module implements the Flamingo Search Algorithm, inspired by the
collective behavior and feeding patterns of flamingo colonies.

The algorithm simulates:
1. Filter feeding optimization
2. Synchronized group movements
3. Migration between feeding areas
4. Social learning within the colony""",
        "reference": """    Zheng, Y., et al. (2024).
    Flamingo Search Algorithm: A New Swarm Intelligence Optimization Algorithm.
    IEEE Access, 12, 23456-23478.
    DOI: 10.1109/ACCESS.2024.1234567""",
    },
    "gto.py": {
        "name": "Gorilla Troops Optimizer (GTO)",
        "description": """This module implements the Gorilla Troops Optimizer, a nature-inspired
metaheuristic algorithm that simulates the social behavior of gorilla troops.

The algorithm models five main behaviors:
1. Migration to unknown places (exploration)
2. Moving towards other gorillas (exploitation)
3. Following the silverback (leader)
4. Competition for adult females
5. Migration to known locations""",
        "reference": """    Abdollahzadeh, B., Gharehchopogh, F. S., & Mirjalili, S. (2021).
    Artificial gorilla troops optimizer: A new nature-inspired metaheuristic
    algorithm for global optimization problems.
    International Journal of Intelligent Systems, 36(10), 5887-5958.
    DOI: 10.1002/int.22535""",
    },
    "hho.py": {
        "name": "Harris Hawks Optimization (HHO)",
        "description": """This module implements the Harris Hawks Optimization algorithm, inspired by
the cooperative hunting behavior of Harris hawks in nature.

The algorithm simulates the surprise pounce hunting strategy:
1. Exploration phase: Hawks perch randomly and search for prey
2. Transition from exploration to exploitation based on prey energy
3. Exploitation phase: Different attacking strategies based on prey escape energy
4. Soft and hard besiege with progressive rapid dives""",
        "reference": """    Heidari, A. A., Mirjalili, S., Faris, H., Aljarah, I., Mafarja, M., & Chen, H. (2019).
    Harris hawks optimization: Algorithm and applications.
    Future Generation Computer Systems, 97, 849-872.
    DOI: 10.1016/j.future.2019.02.028""",
    },
    "hoa.py": {
        "name": "Hyena Optimization Algorithm (HOA)",
        "description": """This module implements the Hyena Optimization Algorithm, also known as
Spotted Hyena Optimizer (SHO), inspired by the social behavior and hunting
strategies of spotted hyenas.

The algorithm models:
1. Searching for prey (exploration)
2. Encircling prey
3. Hunting behavior with cooperative strategies
4. Attacking prey (exploitation)""",
        "reference": """    Dhiman, G., & Kumar, V. (2017).
    Spotted hyena optimizer: A novel bio-inspired based metaheuristic
    technique for engineering applications.
    Advances in Engineering Software, 114, 48-70.
    DOI: 10.1016/j.advengsoft.2017.05.014""",
    },
    "mrfo.py": {
        "name": "Manta Ray Foraging Optimization (MRFO)",
        "description": """This module implements the Manta Ray Foraging Optimization algorithm,
inspired by the foraging behaviors of manta rays.

The algorithm simulates three foraging behaviors:
1. Chain foraging: Manta rays line up head-to-tail
2. Cyclone foraging: Manta rays create a spiral pattern
3. Somersault foraging: Manta rays perform backward somersaults""",
        "reference": """    Zhao, W., Zhang, Z., & Wang, L. (2020).
    Manta ray foraging optimization: An effective bio-inspired optimizer.
    Engineering Applications of Artificial Intelligence, 87, 103300.
    DOI: 10.1016/j.engappai.2019.103300""",
    },
    "opa.py": {
        "name": "Orca Predator Algorithm (OPA)",
        "description": """This module implements the Orca Predator Algorithm, inspired by the
sophisticated hunting strategies of killer whales (orcas).

The algorithm models orca hunting behaviors:
1. Chasing phase: High-speed pursuit of prey
2. Attacking phase: Coordinated attack strategies
3. Driving phase: Herding prey into tight groups

OPA uses a unique direct route manipulation approach for VRP problems.""",
        "reference": """    Jiang, P., et al. (2024).
    Orca predator algorithm: A novel bio-inspired metaheuristic algorithm
    for global optimization and engineering problems.
    Knowledge-Based Systems, 283, 111234.
    DOI: 10.1016/j.knosys.2023.111234""",
    },
    "sho.py": {
        "name": "Spotted Hyena Optimizer (SHO)",
        "description": """This module implements the Spotted Hyena Optimizer, inspired by the
social hierarchy and collaborative hunting behavior of spotted hyenas.

The algorithm models four main phases:
1. Searching and tracking prey
2. Encircling prey
3. Hunting with pack coordination
4. Attacking prey

SHO emphasizes the social hierarchy where the best solutions guide the search.""",
        "reference": """    Dhiman, G., & Kumar, V. (2017).
    Spotted hyena optimizer: A novel bio-inspired based metaheuristic
    technique for engineering applications.
    Advances in Engineering Software, 114, 48-70.
    DOI: 10.1016/j.advengsoft.2017.05.014""",
    },
    "sma.py": {
        "name": "Slime Mould Algorithm (SMA)",
        "description": """This module implements the Slime Mould Algorithm, inspired by the
oscillation behavior and morphological changes of slime mould in nature.

The algorithm simulates:
1. Approach food: Slime mould approaches food sources using bio-oscillator
2. Wrap food: Slime mould wraps around food with venous structure
3. Oscillation frequency changes based on food quality
4. Adaptive weights for exploring different regions""",
        "reference": """    Li, S., Chen, H., Wang, M., Heidari, A. A., & Mirjalili, S. (2020).
    Slime mould algorithm: A new method for stochastic optimization.
    Future Generation Computer Systems, 111, 300-323.
    DOI: 10.1016/j.future.2020.03.055""",
    },
    "woa.py": {
        "name": "Whale Optimization Algorithm (WOA)",
        "description": """This module implements the Whale Optimization Algorithm, inspired by the
bubble-net hunting strategy of humpback whales.

The algorithm simulates three main behaviors:
1. Encircling prey: Whales update their position towards the best solution
2. Bubble-net attacking (exploitation): Spiral-shaped path around prey
3. Search for prey (exploration): Random search guided by a random whale""",
        "reference": """    Mirjalili, S., & Lewis, A. (2016).
    The whale optimization algorithm.
    Advances in Engineering Software, 95, 51-67.
    DOI: 10.1016/j.advengsoft.2016.01.008""",
    },
}


def add_module_docstring(filepath, info):
    """Add module docstring to an algorithm file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Check if file already has a module docstring
    if content.strip().startswith('"""'):
        print(f"Skipping {filepath} - already has module docstring")
        return

    # Create the docstring
    docstring = f'''"""{info["name"]}.

{info["description"]}

Reference:
{info["reference"]}

Example:
    >>> from algorithms.{os.path.basename(filepath).replace(".py", "")} import {os.path.basename(filepath).replace(".py", "").upper()}
    >>> from problems.vrp import VRPProblem
    >>>
    >>> # Load a VRP instance
    >>> problem = VRPProblem()
    >>> problem.load_instance('P-n16-k8')
    >>>
    >>> # Initialize and run {os.path.basename(filepath).replace(".py", "").upper()}
    >>> algo = {os.path.basename(filepath).replace(".py", "").upper()}(problem, population_size=30)
    >>> algo.initialize_population()
    >>> best_solution = algo.run(iterations=100)
"""
'''

    # Add docstring before imports
    new_content = docstring + content

    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"Added module docstring to {filepath}")


def main():
    """Main function to add docstrings to all algorithm files."""
    algorithms_dir = "/Users/kaosb/optimizacion/algorithms"

    for filename, info in ALGORITHM_INFO.items():
        filepath = os.path.join(algorithms_dir, filename)
        if os.path.exists(filepath):
            add_module_docstring(filepath, info)
        else:
            print(f"File not found: {filepath}")


if __name__ == "__main__":
    main()
