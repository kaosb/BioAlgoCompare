# Discrete Optimization Problems

This directory is reserved for discrete/combinatorial optimization problems.

## Purpose
Implement discrete optimization problems beyond VRP for comprehensive algorithm testing.

## Planned Problems
- **Traveling Salesman Problem (TSP)**
  - Standard TSP
  - Asymmetric TSP
  - Multiple TSP
  
- **Knapsack Problems**
  - 0/1 Knapsack
  - Multiple Knapsack
  - Bounded Knapsack
  
- **Scheduling Problems**
  - Job Shop Scheduling
  - Flow Shop Scheduling
  - Project Scheduling
  
- **Assignment Problems**
  - Quadratic Assignment
  - Generalized Assignment
  - Weapon-Target Assignment

## Implementation Pattern
Each problem will extend a base `DiscreteProblem` class:
```python
class DiscreteProblem:
    def __init__(self, instance_data):
        self.load_instance(instance_data)
    
    def evaluate(self, solution):
        raise NotImplementedError
    
    def is_valid(self, solution):
        raise NotImplementedError
```

## Future Integration
These problems will enable:
- Cross-domain algorithm evaluation
- Robustness testing
- Generalization capability assessment