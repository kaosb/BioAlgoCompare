# Random State Management Migration Plan

## TODO #80 - Enforce RandomStateManager Usage

### Overview

This document outlines the plan to migrate all algorithms to use the centralized RandomStateManager for ensuring reproducibility across the framework.

### Current State

- **RandomStateManager** exists in `utils/random_state.py` with full functionality
- Base class (`algorithms/base_v2.py`) directly sets `random.seed()` and `np.random.seed()`
- Individual algorithms inherit this behavior but don't add their own seed setting
- No algorithms currently use RandomStateManager

### Migration Strategy

#### Phase 1: Create Enhanced Base Class (✓ Completed)

1. Created `algorithms/base_v2_enforced.py` that:
   - Uses RandomStateManager instead of direct seed setting
   - Patches numpy.random during execution to ensure all calls use managed state
   - Provides convenience methods for random number generation
   - Maintains backward compatibility

2. Created `algorithms/base_v2_random.py` with:
   - ManagedMetaheuristicAlgorithm class using ManagedRandomMixin
   - Full integration with RandomStateManager
   - Checkpointing and parallel execution support

3. Created enforcement utilities in `utils/random_enforcement.py`:
   - Decorators for automatic enforcement
   - Mixin classes for easy integration
   - Migration helpers

#### Phase 2: Gradual Migration Approach

Instead of modifying all algorithms at once, we'll use a gradual approach:

1. **Option A - Import Redirect** (Recommended for immediate enforcement):
   ```python
   # In algorithms/base_v2.py, add at the top:
   from algorithms.base_v2_enforced import MetaheuristicAlgorithm, Individual
   
   # This makes all algorithms automatically use the enforced version
   ```

2. **Option B - Individual Algorithm Migration**:
   - Migrate high-impact algorithms first (HOA, EGTO, FGO)
   - Update imports in each algorithm file
   - Test thoroughly before moving to next

3. **Option C - Parallel Versions**:
   - Keep v2 algorithms unchanged
   - Create v3 versions with RandomStateManager
   - Gradually deprecate v2 versions

#### Phase 3: Testing and Validation

1. **Reproducibility Tests**:
   ```python
   # Test that same seed produces identical results
   alg1 = Algorithm(seed=42)
   alg2 = Algorithm(seed=42)
   assert alg1.execute() == alg2.execute()
   ```

2. **Checkpoint Tests**:
   ```python
   # Test state save/restore
   checkpoint = alg.random_manager.checkpoint()
   # ... run more iterations ...
   alg.random_manager.restore_checkpoint(checkpoint)
   ```

3. **Parallel Execution Tests**:
   ```python
   # Test deterministic sub-seeds
   seeds = [alg.generate_sub_seed(f"thread_{i}") for i in range(4)]
   # Seeds should be deterministic but different
   ```

### Implementation Steps

1. **Update Base Class Import** (Simplest approach):
   ```python
   # In algorithms/__init__.py or base_v2.py
   from algorithms.base_v2_enforced import (
       MetaheuristicAlgorithm, 
       Individual,
       MoveContext
   )
   ```

2. **Add Tests for Random State Management**:
   - Create `tests/test_random_state_enforcement.py`
   - Test each algorithm for reproducibility
   - Verify no direct seed setting

3. **Update Documentation**:
   - Add section on random state management to CLAUDE.md
   - Update algorithm implementation guide
   - Document best practices

### Benefits

1. **Guaranteed Reproducibility**: All algorithms use same random state system
2. **Parallel Execution Support**: Deterministic sub-seeds for threads
3. **State Checkpointing**: Save/restore capability for long runs
4. **Debugging Support**: Track all random state changes
5. **Scientific Rigor**: Essential for published results

### Migration Timeline

- **Week 1**: Implement base class enforcement ✓
- **Week 2**: Test with key algorithms (HOA, EGTO, FGO)
- **Week 3**: Full rollout and documentation
- **Week 4**: Deprecate direct seed setting

### Code Examples

#### Using Enforced Base Class

```python
from algorithms.base_v2_enforced import MetaheuristicAlgorithm, Individual

class MyAlgorithm(MetaheuristicAlgorithm):
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)
        # RandomStateManager automatically created and managed
    
    def update_population(self):
        # Use managed random functions
        random_value = self.random_uniform(0, 1)
        random_int = self.random_randint(0, 10)
        
        # Or use numpy.random directly (automatically patched)
        another_value = np.random.uniform(0, 1)
```

#### Checkpointing Example

```python
# Save state
checkpoint = algorithm.random_manager.checkpoint()

# Later, restore state
algorithm.random_manager.restore_checkpoint(checkpoint)
```

#### Parallel Execution Example

```python
# Generate deterministic sub-seeds
thread_seeds = [
    algorithm.generate_sub_seed(f"thread_{i}")
    for i in range(n_threads)
]
```

### Verification Script

```bash
# Analyze current compliance
python scripts/tools/enforce_random_state.py analyze

# Generate migration code
python scripts/tools/enforce_random_state.py migrate

# Run reproducibility tests
pytest tests/test_random_state_enforcement.py -v
```

### Next Steps

1. Choose migration approach (Option A recommended)
2. Implement chosen approach
3. Run comprehensive tests
4. Update documentation
5. Mark TODO #80 as complete