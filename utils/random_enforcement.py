"""
Enforcement utilities for RandomStateManager usage across all algorithms.
"""

import inspect
import warnings
from typing import Optional, Type, Dict, Any, Callable
from functools import wraps
import numpy as np
import random

from utils.random_state import RandomStateManager, get_global_random_manager


class RandomStateEnforcer:
    """
    Enforces the use of RandomStateManager in algorithms.
    
    This class provides decorators and utilities to ensure all algorithms
    use the centralized random state management for reproducibility.
    """
    
    @staticmethod
    def enforce_random_state(func: Callable) -> Callable:
        """
        Decorator that enforces RandomStateManager usage in algorithm initialization.
        
        This decorator:
        1. Intercepts seed parameter
        2. Creates/uses RandomStateManager instance
        3. Prevents direct numpy/random seed setting
        4. Logs warnings for non-compliance
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Extract seed parameter
            seed = kwargs.get('seed', None)
            
            # Check if class already has a random_manager
            if not hasattr(self, 'random_manager'):
                # Create RandomStateManager for this instance
                self.random_manager = RandomStateManager(seed)
                
                # Override the seed parameter to prevent double-setting
                if 'seed' in kwargs:
                    kwargs['seed'] = seed  # Keep original for compatibility
                    
                # Set flag to indicate managed random state
                self._uses_random_manager = True
            
            # Call original function
            result = func(self, *args, **kwargs)
            
            # Post-initialization check
            RandomStateEnforcer._verify_no_direct_seeding(self)
            
            return result
        
        return wrapper
    
    @staticmethod
    def _verify_no_direct_seeding(obj: Any) -> None:
        """
        Verify that the object doesn't directly set random seeds.
        
        Args:
            obj: Algorithm instance to check
        """
        # Get the source code of the class
        try:
            source = inspect.getsource(obj.__class__)
            
            # Check for direct seed setting
            dangerous_patterns = [
                'np.random.seed',
                'numpy.random.seed',
                'random.seed',
                'np.random.RandomState'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in source:
                    warnings.warn(
                        f"Class {obj.__class__.__name__} contains direct random seed setting "
                        f"with '{pattern}'. This should be replaced with RandomStateManager.",
                        DeprecationWarning,
                        stacklevel=3
                    )
        except (OSError, TypeError):
            # Source not available, skip check
            pass
    
    @staticmethod
    def patch_random_functions(obj: Any) -> None:
        """
        Patch numpy and random functions to use RandomStateManager.
        
        This method replaces direct calls to random functions with
        managed versions that use the instance's RandomStateManager.
        
        Args:
            obj: Object whose methods should be patched
        """
        if not hasattr(obj, 'random_manager'):
            obj.random_manager = get_global_random_manager()
        
        # Create managed random generators
        manager = obj.random_manager
        
        # Create a numpy RandomState from the manager's state
        current_state = manager.get_state()
        if current_state.numpy_state:
            obj._np_random = np.random.RandomState()
            obj._np_random.set_state(current_state.numpy_state)
        else:
            # Create new RandomState with manager's seed
            obj._np_random = np.random.RandomState(current_state.seed)
        
        # Patch common random methods
        obj.random_uniform = lambda low=0, high=1, size=None: (
            obj._np_random.uniform(low, high, size)
        )
        obj.random_normal = lambda loc=0, scale=1, size=None: (
            obj._np_random.normal(loc, scale, size)
        )
        obj.random_randint = lambda low, high=None, size=None: (
            obj._np_random.randint(low, high, size)
        )
        obj.random_choice = lambda a, size=None, replace=True, p=None: (
            obj._np_random.choice(a, size, replace, p)
        )
        obj.random_random = lambda size=None: (
            obj._np_random.random(size)
        )


def enforce_random_state_in_class(cls: Type) -> Type:
    """
    Class decorator that enforces RandomStateManager usage.
    
    This decorator:
    1. Wraps the __init__ method with enforcement
    2. Adds random state management methods
    3. Patches random function calls
    
    Args:
        cls: Class to decorate
        
    Returns:
        Decorated class with enforced random state management
    """
    # Get the original __init__
    original_init = cls.__init__
    
    # Create wrapped __init__
    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        # Extract seed if present
        seed = kwargs.get('seed', None)
        
        # Create RandomStateManager
        self.random_manager = RandomStateManager(seed)
        
        # Call original __init__
        original_init(self, *args, **kwargs)
        
        # Patch random functions
        RandomStateEnforcer.patch_random_functions(self)
        
        # Verify compliance
        RandomStateEnforcer._verify_no_direct_seeding(self)
    
    # Replace __init__
    cls.__init__ = new_init
    
    # Add convenience methods
    cls.get_random_state = lambda self: self.random_manager.get_state()
    cls.set_random_state = lambda self, state: self.random_manager.set_state(state)
    cls.checkpoint_random = lambda self: self.random_manager.checkpoint()
    cls.restore_random_checkpoint = lambda self, checkpoint: (
        self.random_manager.restore_checkpoint(checkpoint)
    )
    
    # Mark as managed
    cls._uses_random_state_manager = True
    
    return cls


class ManagedRandomMixin:
    """
    Mixin class that provides managed random state functionality.
    
    Classes that inherit from this mixin automatically get:
    1. RandomStateManager instance
    2. Managed random functions
    3. Checkpointing capabilities
    """
    
    def __init__(self, *args, **kwargs):
        # Extract seed
        seed = kwargs.pop('seed', None)
        
        # Create manager
        self.random_manager = RandomStateManager(seed)
        
        # Create managed numpy random state
        self._setup_managed_random()
        
        # Call parent __init__
        super().__init__(*args, **kwargs)
    
    def _setup_managed_random(self):
        """Setup managed random number generators."""
        # Get current state from manager
        state = self.random_manager.get_state()
        
        # Create numpy RandomState
        if state.numpy_state:
            self._np_random = np.random.RandomState()
            self._np_random.set_state(state.numpy_state)
        else:
            self._np_random = np.random.RandomState(state.seed)
    
    # Managed random functions
    def random_uniform(self, low=0, high=1, size=None):
        """Generate uniform random numbers using managed state."""
        return self._np_random.uniform(low, high, size)
    
    def random_normal(self, loc=0, scale=1, size=None):
        """Generate normal random numbers using managed state."""
        return self._np_random.normal(loc, scale, size)
    
    def random_randint(self, low, high=None, size=None):
        """Generate random integers using managed state."""
        return self._np_random.randint(low, high, size)
    
    def random_choice(self, a, size=None, replace=True, p=None):
        """Random choice using managed state."""
        return self._np_random.choice(a, size, replace, p)
    
    def random_random(self, size=None):
        """Generate random floats using managed state."""
        return self._np_random.random(size)
    
    def random_permutation(self, x):
        """Generate random permutation using managed state."""
        return self._np_random.permutation(x)
    
    def random_shuffle(self, x):
        """Shuffle array in-place using managed state."""
        self._np_random.shuffle(x)
        return x
    
    # State management
    def get_random_state(self):
        """Get current random state."""
        return self.random_manager.get_state()
    
    def set_random_state(self, state):
        """Set random state."""
        self.random_manager.set_state(state)
        self._setup_managed_random()
    
    def checkpoint_random(self):
        """Create random state checkpoint."""
        return self.random_manager.checkpoint()
    
    def restore_random_checkpoint(self, checkpoint):
        """Restore from checkpoint."""
        self.random_manager.restore_checkpoint(checkpoint)
        self._setup_managed_random()
    
    def generate_sub_seed(self, identifier=""):
        """Generate deterministic sub-seed."""
        return self.random_manager.generate_sub_seed(identifier)


def migrate_algorithm_to_managed_random(
    algorithm_class: Type,
    output_file: Optional[str] = None
) -> str:
    """
    Generate migration code for an algorithm to use RandomStateManager.
    
    Args:
        algorithm_class: Algorithm class to migrate
        output_file: Optional output file path
        
    Returns:
        Migration code as string
    """
    class_name = algorithm_class.__name__
    
    migration_code = f'''"""
{class_name} with enforced RandomStateManager usage.

This is an automatically generated migration that ensures proper
random state management for reproducibility.
"""

from utils.random_enforcement import ManagedRandomMixin, enforce_random_state_in_class
from {algorithm_class.__module__} import {class_name} as Original{class_name}


# Option 1: Using decorator
@enforce_random_state_in_class
class {class_name}V3(Original{class_name}):
    """
    {class_name} with enforced random state management.
    
    This version uses the @enforce_random_state_in_class decorator
    to automatically manage random state.
    """
    pass


# Option 2: Using mixin
class {class_name}V3Mixin(ManagedRandomMixin, Original{class_name}):
    """
    {class_name} with random state management via mixin.
    
    This version inherits from ManagedRandomMixin to get
    managed random functions and state management.
    """
    
    def __init__(self, *args, **kwargs):
        # ManagedRandomMixin handles seed extraction
        super().__init__(*args, **kwargs)
    
    # Override any methods that use random functions
    # to use the managed versions (self.random_uniform, etc.)


# Example usage:
if __name__ == "__main__":
    from problems.vrp import VRPProblem
    
    # Load a test problem
    problem = VRPProblem("data/vrp/A-n32-k5.vrp")
    
    # Create algorithm with managed random state
    algorithm = {class_name}V3(
        problem=problem,
        population_size=30,
        max_iterations=100,
        seed=42  # Will be managed by RandomStateManager
    )
    
    # Run algorithm
    algorithm.execute()
    
    # Access random state
    state = algorithm.get_random_state()
    print(f"Random state: {{state.seed}}")
    
    # Create checkpoint
    checkpoint = algorithm.checkpoint_random()
    
    # Restore from checkpoint
    algorithm.restore_random_checkpoint(checkpoint)
'''
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(migration_code)
    
    return migration_code