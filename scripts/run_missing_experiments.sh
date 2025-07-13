#!/bin/bash

# Run missing experiments

echo "🔧 Running missing experiments..."

# GA for E-n22-k4
echo "Running GA on E-n22-k4..."
python scripts/analyze.py massive \
    --runs 51 \
    --algorithm ga \
    --instances E-n22-k4 \
    --iterations 300 \
    --population 50 \
    --output-dir "/Users/kaosb/optimizacion/results/thesis_E-n22-k4_20250713_072835/ga" \
    --parallel \
    --seed 42

# GA for P-n16-k8
echo "Running GA on P-n16-k8..."
python scripts/analyze.py massive \
    --runs 51 \
    --algorithm ga \
    --instances P-n16-k8 \
    --iterations 300 \
    --population 50 \
    --output-dir "/Users/kaosb/optimizacion/results/thesis_P-n16-k8_20250713_072835/ga" \
    --parallel \
    --seed 42

# PSO for P-n16-k8
echo "Running PSO on P-n16-k8..."
python scripts/analyze.py massive \
    --runs 51 \
    --algorithm pso \
    --instances P-n16-k8 \
    --iterations 300 \
    --population 50 \
    --output-dir "/Users/kaosb/optimizacion/results/thesis_P-n16-k8_20250713_072835/pso" \
    --parallel \
    --seed 42

echo "✅ Missing experiments completed!"