"""
Defines the available v2 algorithms for the benchmark system.
"""

# This dictionary maps the command-line algorithm names to their module names.
# It is the single source of truth for which algorithms can be run.
ALGORITHMS = {
    "sho": "sho",      # Spotted Hyena Optimizer
    "apo": "apo",      # Artificial Protozoa Optimizer
    "egto": "egto",    # Enhanced Gorilla Troops Optimizer
    "fsa": "fsa",      # Flamingo Search Algorithm
    "foa": "foa",      # Fossa Optimization Algorithm
    "woa": "woa",      # Whale Optimization Algorithm
    "hho": "hho",      # Harris Hawks Optimization
    "mrfo": "mrfo",    # Manta Ray Foraging Optimization
    "sma": "sma",      # Slime Mould Algorithm
    "gto": "gto",      # Gorilla Troops Optimizer
    "ewa": "ewa",      # Earthworm Algorithm
    "aha": "aha",      # Artificial Hummingbird Algorithm
    "rro": "rro",      # Raven Roosting Optimization
    "gvoa": "gvoa",    # Griffon Vultures Optimization Algorithm
    "smo": "smo",      # Starling Murmuration Optimizer
    "opa": "opa",      # Orca Predator Algorithm
    "hoa": "hoa",      # Hyena Optimization Algorithm
    "fgo": "fgo",      # Flamingo Optimization Algorithm
}

# Detailed information about each algorithm
ALGORITHMS_INFO = {
    "aha": {
        "name": "Artificial Hummingbird Algorithm",
        "year": 2022,
        "version": "v2",
        "inspiration": "Hummingbird flight and foraging behavior"
    },
    "apo": {
        "name": "Artificial Protozoa Optimizer", 
        "year": 2024,
        "version": "v2",
        "inspiration": "Protozoan movement and division behavior"
    },
    "egto": {
        "name": "Enhanced Gorilla Troops Optimization",
        "year": 2024,
        "version": "v2",
        "inspiration": "Gorilla social behavior with PSO components"
    },
    "ewa": {
        "name": "Earthworm Algorithm",
        "year": 2018,
        "version": "v2",
        "inspiration": "Earthworm movement patterns"
    },
    "fgo": {
        "name": "Flamingo Optimization Algorithm",
        "year": 2025,
        "version": "v2",
        "inspiration": "Flamingo group behavior"
    },
    "foa": {
        "name": "Fossa Optimization Algorithm",
        "year": 2024,
        "version": "v2",
        "inspiration": "Fossa hunting and territorial strategies"
    },
    "fsa": {
        "name": "Flamingo Search Algorithm",
        "year": 2021,
        "version": "v2",
        "inspiration": "Flamingo food search patterns"
    },
    "gto": {
        "name": "Gorilla Troops Optimization",
        "year": 2021,
        "version": "v2",
        "inspiration": "Gorilla hierarchy and social behavior"
    },
    "gvoa": {
        "name": "Griffon Vultures Optimization Algorithm",
        "year": 2025,
        "version": "v2",
        "inspiration": "Griffon vulture thermal soaring behavior"
    },
    "hho": {
        "name": "Harris Hawks Optimization",
        "year": 2019,
        "version": "v2",
        "inspiration": "Harris hawk cooperative hunting"
    },
    "hoa": {
        "name": "Hyena Optimization Algorithm",
        "year": 2017,
        "version": "v2",
        "inspiration": "Hyena cooperative hunting strategies"
    },
    "mrfo": {
        "name": "Manta Ray Foraging Optimization",
        "year": 2020,
        "version": "v2",
        "inspiration": "Manta ray feeding techniques"
    },
    "opa": {
        "name": "Orca Predator Algorithm",
        "year": 2021,
        "version": "v2",
        "inspiration": "Orca cooperative hunting strategies"
    },
    "rro": {
        "name": "Raven Roosting Optimization",
        "year": 2016,
        "version": "v2",
        "inspiration": "Raven roosting behavior"
    },
    "sho": {
        "name": "Spotted Hyena Optimizer",
        "year": 2017,
        "version": "v2",
        "inspiration": "Spotted hyena cooperative hunting"
    },
    "sma": {
        "name": "Slime Mould Algorithm",
        "year": 2020,
        "version": "v2",
        "inspiration": "Slime mould food-seeking behavior"
    },
    "smo": {
        "name": "Starling Murmuration Optimizer",
        "year": 2022,
        "version": "v2",
        "inspiration": "Starling murmuration and emergent behavior"
    },
    "woa": {
        "name": "Whale Optimization Algorithm",
        "year": 2016,
        "version": "v2",
        "inspiration": "Humpback whale feeding strategy"
    }
}
