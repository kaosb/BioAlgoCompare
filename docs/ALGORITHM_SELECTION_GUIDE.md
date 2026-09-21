# Algorithm Selection Guide

This guide helps you choose the most appropriate bio-inspired algorithm for your Vehicle Routing Problem (VRP) based on problem characteristics and requirements.

## Table of Contents
1. [Algorithm Overview](#algorithm-overview)
2. [Selection Criteria](#selection-criteria)
3. [Algorithm Characteristics](#algorithm-characteristics)
4. [Performance Comparison](#performance-comparison)
5. [Recommendations by Scenario](#recommendations-by-scenario)
6. [Fine-Tuning Guidelines](#fine-tuning-guidelines)

## Algorithm Overview

BioAlgoCompare includes 18 bio-inspired metaheuristic algorithms, each with unique characteristics:

### Nature-Inspired Categories

**Mammal-Inspired**
- **EWA** (Earthworm): Reproduction-based search
- **WOA** (Whale): Bubble-net hunting strategy
- **GTO/EGTO** (Gorilla): Social hierarchy and migration
- **HOA/SHO** (Hyena): Pack hunting strategies
- **OPA** (Orca): Sophisticated hunting tactics
- **FOA** (Fossa): Ambush predator behavior

**Bird-Inspired**
- **AHA** (Hummingbird): Intelligent foraging with memory
- **HHO** (Harris Hawks): Cooperative hunting
- **RRO** (Raven): Roosting and foraging
- **GVOA** (Griffon Vultures): Scavenging optimization
- **FSA/FGO** (Flamingo): Filter feeding and migration
- **SMO** (Starling): Murmuration patterns

**Marine-Inspired**
- **MRFO** (Manta Ray): Chain, cyclone, and somersault foraging
- **WOA** (Whale): Encircling and spiral movements
- **OPA** (Orca): Direct route manipulation for VRP

**Microorganism-Inspired**
- **SMA** (Slime Mould): Adaptive oscillation
- **APO** (Protozoa): Dormancy and reproduction

## Selection Criteria

### 1. Problem Size
- **Small (< 50 nodes)**: Most algorithms work well
- **Medium (50-100 nodes)**: Focus on efficiency
- **Large (> 100 nodes)**: Need scalable algorithms

### 2. Solution Quality vs Speed
- **Quality Priority**: SMA, AHA, OPA
- **Speed Priority**: HHO, EWA, FOA
- **Balanced**: GTO, WOA, MRFO

### 3. Exploration vs Exploitation
- **High Exploration**: APO, RRO, GVOA
- **High Exploitation**: FOA, HHO, OPA
- **Adaptive Balance**: SMA, AHA, SMO

### 4. Constraint Handling
- **Strong Constraints**: OPA (VRP-specific)
- **Flexible Constraints**: EWA, SMA
- **Penalty-Based**: Most algorithms

## Algorithm Characteristics

### Detailed Comparison Table

| Algorithm | Exploration | Exploitation | Convergence | Memory | VRP-Specific |
|-----------|------------|--------------|-------------|---------|--------------|
| **AHA** | High | High | Medium | Yes | No |
| **APO** | High | Medium | Slow | No | No |
| **EGTO** | High | High | Fast | No | No |
| **EWA** | Medium | High | Fast | No | No |
| **FOA** | Low | High | Fast | No | No |
| **GTO** | High | Medium | Medium | No | No |
| **HHO** | Medium | High | Very Fast | No | No |
| **HOA** | Medium | Medium | Medium | No | No |
| **MRFO** | High | Medium | Medium | No | No |
| **OPA** | Low | Very High | Fast | Yes | Yes |
| **RRO** | High | Low | Slow | No | No |
| **SHO** | Medium | Medium | Medium | No | No |
| **SMA** | Adaptive | Adaptive | Medium | No | No |
| **SMO** | High | Medium | Medium | Yes | No |
| **WOA** | Medium | High | Fast | No | No |
| **GVOA** | High | Medium | Medium | Yes | No |

### Key Features

**AHA (Artificial Hummingbird)**
- ✓ Memory mechanism prevents revisiting
- ✓ Three flight skills for diverse search
- ✓ Good for complex landscapes
- ✗ Higher computational cost

**EWA (Earthworm)**
- ✓ Simple and fast
- ✓ Good exploitation
- ✓ Reliable convergence
- ✗ Limited exploration

**OPA (Orca Predator)**
- ✓ Direct route manipulation
- ✓ VRP-specific operators
- ✓ Excellent for VRP
- ✗ Less general purpose

**SMA (Slime Mould)**
- ✓ Adaptive parameters
- ✓ Self-adjusting behavior
- ✓ Good balance
- ✗ Parameter sensitive

**WOA (Whale Optimization)**
- ✓ Simple implementation
- ✓ Good convergence
- ✓ Reliable results
- ✗ Can get trapped locally

## Performance Comparison

Based on extensive benchmarking on standard VRP instances:

### Best Fitness (Solution Quality)
1. **OPA** - Specialized for VRP
2. **SMA** - Adaptive behavior
3. **AHA** - Memory mechanism
4. **EWA** - Strong exploitation
5. **WOA** - Reliable performance

### Convergence Speed
1. **HHO** - Fastest convergence
2. **FOA** - Quick exploitation
3. **EWA** - Efficient search
4. **OPA** - Direct manipulation
5. **WOA** - Smooth convergence

### Robustness (Consistency)
1. **EWA** - Most consistent
2. **WOA** - Reliable across instances
3. **SMA** - Adaptive to problems
4. **GTO** - Stable performance
5. **MRFO** - Good reliability

### Scalability
1. **OPA** - Scales well with VRP
2. **EWA** - Efficient scaling
3. **HHO** - Maintains speed
4. **FOA** - Good for large problems
5. **WOA** - Reasonable scaling

## Recommendations by Scenario

### Scenario 1: First-Time User
**Recommended**: EWA or WOA
```bash
python scripts/analyze.py run --algorithm ewa --instance P-n16-k8
```
- Simple to use
- Reliable results
- Good default parameters

### Scenario 2: Best Quality Needed
**Recommended**: OPA or SMA
```bash
python scripts/analyze.py run --algorithm opa --instance E-n22-k4 --iterations 500
```
- Maximum solution quality
- Worth the extra computation

### Scenario 3: Quick Solutions
**Recommended**: HHO or FOA
```bash
python scripts/analyze.py run --algorithm hho --instance A-n32-k5 --iterations 100
```
- Fast convergence
- Good enough quality
- Minimal computation

### Scenario 4: Research Comparison
**Recommended**: Run multiple algorithms
```bash
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms ewa,opa,sma,woa,hho \
    --instances P-n16-k8,E-n22-k4 \
    --runs 30
```

### Scenario 5: Unknown Problem
**Recommended**: Adaptive algorithms (SMA, AHA)
```bash
python scripts/analyze.py run --algorithm sma --instance YOUR_INSTANCE --runs 10
```
- Self-adjusting parameters
- Good exploration

### Scenario 6: Large-Scale VRP
**Recommended**: OPA or EWA with larger population
```bash
python scripts/analyze.py run --algorithm opa \
    --instance LARGE_INSTANCE \
    --population 100 \
    --iterations 300 \
    --parallel
```

## Fine-Tuning Guidelines

### Population Size
- **Small instances (<30 nodes)**: 20-30 individuals
- **Medium instances (30-100 nodes)**: 30-50 individuals
- **Large instances (>100 nodes)**: 50-100 individuals

### Iteration Count
- **Testing**: 100-200 iterations
- **Good results**: 300-500 iterations
- **Best quality**: 500-1000 iterations

### Algorithm-Specific Tips

**EWA**
- Increase population for better diversity
- Works well with default parameters

**OPA**
- Benefits from larger populations
- Adjust acceptance probability for exploration

**SMA**
- Sensitive to initial parameters
- Let it self-adapt over iterations

**AHA**
- Memory table size affects performance
- More iterations utilize memory better

**HHO**
- Fast convergence, increase iterations carefully
- Good for time-constrained scenarios

## Decision Tree

```
Start
│
├─ Need VRP-specific features?
│  └─ Yes → OPA
│  └─ No → Continue
│
├─ Priority: Speed or Quality?
│  ├─ Speed → HHO, FOA, EWA
│  └─ Quality → Continue
│
├─ Problem complexity?
│  ├─ Simple → EWA, WOA
│  ├─ Complex → AHA, SMA
│  └─ Unknown → SMA (adaptive)
│
└─ First time user?
   ├─ Yes → EWA (simple, reliable)
   └─ No → Try multiple algorithms
```

## Best Practices

1. **Always run multiple times** (30+ runs) for statistical validity
2. **Start with default parameters** before tuning
3. **Use parallel execution** for multiple runs
4. **Compare 3-5 algorithms** for new problems
5. **Set random seed** for reproducibility

## Conclusion

For most VRP problems:
- **Start with**: EWA (reliable, fast)
- **For best quality**: OPA (VRP-specific)
- **For adaptability**: SMA (self-adjusting)
- **For speed**: HHO (rapid convergence)
- **For research**: Compare top 5 algorithms

Remember that algorithm performance can vary by problem instance, so testing multiple algorithms is recommended for critical applications.
