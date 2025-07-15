#!/usr/bin/env python3
"""Test quick to verify HO uses IL in benchmarks"""

from problems.vrp import VRPProblem
from algorithms.ho import HO

# Test instance
problem = VRPProblem("data/vrp/P-n16-k8.vrp")

print("🧪 Testing HO with IL enabled...")
print("="*50)

# Test 1: HO with IL explicitly enabled
print("\n1. HO with IL=True:")
ho_il = HO(problem, population_size=20, max_iterations=50, seed=42, use_il=True)
ho_il.initialize_population()

# Run a few iterations to see if IL is being used
for i in range(5):
    ho_il.update_population()
    print(f"   Iteration {i}: Fitness = {ho_il.best_solution.fitness():.2f}")

# Test 2: HO without IL
print("\n2. HO with IL=False:")
ho_std = HO(problem, population_size=20, max_iterations=50, seed=42, use_il=False)
best_std = ho_std.execute()
print(f"   Final fitness = {best_std.fitness():.2f}")

# Test 3: Default HO (should not use IL by default)
print("\n3. HO default (no IL specified):")
ho_default = HO(problem, population_size=20, max_iterations=50, seed=42)
best_default = ho_default.execute()
print(f"   Final fitness = {best_default.fitness():.2f}")

print("\n" + "="*50)
print("✅ Test completed. Check messages above for IL loading.")