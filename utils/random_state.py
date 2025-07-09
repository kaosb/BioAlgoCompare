"""
Random State Manager for ensuring reproducibility across the framework.
Provides centralized management of random number generation.
"""

import random
import numpy as np
from typing import Optional, Dict, Any, Tuple
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RandomState:
    """Container for random state information."""
    seed: Optional[int]
    numpy_state: Optional[Tuple] = None
    python_state: Optional[Tuple] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'seed': self.seed,
            'numpy_state': self.numpy_state,
            'python_state': self.python_state,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RandomState':
        """Create from dictionary."""
        return cls(
            seed=data.get('seed'),
            numpy_state=data.get('numpy_state'),
            python_state=data.get('python_state'),
            timestamp=data.get('timestamp', datetime.now().isoformat())
        )


class RandomStateManager:
    """
    Centralized manager for random state across the framework.
    
    This class ensures reproducibility by:
    1. Managing both numpy and Python's random states
    2. Providing checkpointing capabilities
    3. Generating deterministic sub-seeds for parallel execution
    4. Logging all random state changes for debugging
    """
    
    def __init__(self, master_seed: Optional[int] = None):
        """
        Initialize the random state manager.
        
        Args:
            master_seed: Master seed for all random operations.
                        If None, uses current time-based seed.
        """
        self.master_seed = master_seed or self._generate_time_seed()
        self.current_state: Optional[RandomState] = None
        self.state_history: list[RandomState] = []
        self.sub_seed_counter: int = 0
        
        # Initialize with master seed
        self.set_seed(self.master_seed)
    
    @staticmethod
    def _generate_time_seed() -> int:
        """Generate a seed based on current time."""
        import time
        return int(time.time() * 1000000) % 2**32
    
    def set_seed(self, seed: Optional[int]) -> None:
        """
        Set the random seed for both numpy and Python's random.
        
        Args:
            seed: The seed value. If None, generates a time-based seed.
        """
        if seed is None:
            seed = self._generate_time_seed()
        
        # Set seeds
        np.random.seed(seed)
        random.seed(seed)
        
        # Save state
        self.current_state = RandomState(
            seed=seed,
            numpy_state=np.random.get_state(),
            python_state=random.getstate()
        )
        
        # Add to history
        self.state_history.append(self.current_state)
    
    def get_state(self) -> RandomState:
        """
        Get the current random state.
        
        Returns:
            Current RandomState object
        """
        if self.current_state is None:
            self.set_seed(self.master_seed)
        
        # Get current state from random modules
        current_state = RandomState(
            seed=self.current_state.seed,
            numpy_state=np.random.get_state(),
            python_state=random.getstate(),
            timestamp=datetime.now().isoformat()
        )
        
        # Update stored state
        self.current_state = current_state
        
        return current_state
    
    def set_state(self, state: RandomState) -> None:
        """
        Restore a previous random state.
        
        Args:
            state: RandomState object to restore
        """
        if state.numpy_state is not None:
            np.random.set_state(state.numpy_state)
        
        if state.python_state is not None:
            random.setstate(state.python_state)
        
        self.current_state = state
        self.state_history.append(state)
    
    def generate_sub_seed(self, identifier: str = "") -> int:
        """
        Generate a deterministic sub-seed for parallel execution.
        
        Args:
            identifier: Optional string identifier for the sub-seed
            
        Returns:
            Deterministic sub-seed based on master seed and identifier
        """
        self.sub_seed_counter += 1
        
        # Create unique string for hashing
        unique_str = f"{self.master_seed}:{self.sub_seed_counter}:{identifier}"
        
        # Generate deterministic hash
        hash_obj = hashlib.md5(unique_str.encode())
        sub_seed = int(hash_obj.hexdigest(), 16) % 2**32
        
        return sub_seed
    
    def checkpoint(self) -> Dict[str, Any]:
        """
        Create a checkpoint of the current state.
        
        Returns:
            Dictionary containing all state information
        """
        # Get current state before creating checkpoint
        current = self.get_state()
        
        return {
            'master_seed': self.master_seed,
            'current_state': current.to_dict(),
            'sub_seed_counter': self.sub_seed_counter,
            'history_length': len(self.state_history)
        }
    
    def restore_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """
        Restore from a checkpoint.
        
        Args:
            checkpoint: Checkpoint dictionary from checkpoint() method
        """
        self.master_seed = checkpoint['master_seed']
        self.sub_seed_counter = checkpoint['sub_seed_counter']
        
        if checkpoint['current_state']:
            state = RandomState.from_dict(checkpoint['current_state'])
            self.set_state(state)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the current state to a JSON file.
        
        Args:
            filepath: Path to save the state
        """
        checkpoint = self.checkpoint()
        
        # Convert numpy states to lists for JSON serialization
        if checkpoint['current_state'] and checkpoint['current_state']['numpy_state']:
            numpy_state = checkpoint['current_state']['numpy_state']
            checkpoint['current_state']['numpy_state'] = {
                'MT19937': numpy_state[1].tolist(),
                'pos': int(numpy_state[2]),
                'has_gauss': numpy_state[3],
                'cached_gaussian': numpy_state[4]
            }
        
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def load_from_file(self, filepath: str) -> None:
        """
        Load state from a JSON file.
        
        Args:
            filepath: Path to load the state from
        """
        with open(filepath, 'r') as f:
            checkpoint = json.load(f)
        
        # Convert numpy state back from JSON format
        if checkpoint['current_state'] and checkpoint['current_state']['numpy_state']:
            numpy_dict = checkpoint['current_state']['numpy_state']
            checkpoint['current_state']['numpy_state'] = (
                'MT19937',
                np.array(numpy_dict['MT19937'], dtype=np.uint32),
                numpy_dict['pos'],
                numpy_dict['has_gauss'],
                numpy_dict['cached_gaussian']
            )
        
        self.restore_checkpoint(checkpoint)
    
    def reset(self) -> None:
        """Reset the manager to initial state."""
        self.current_state = None
        self.state_history.clear()
        self.sub_seed_counter = 0
        self.set_seed(self.master_seed)


# Global instance for convenience
_global_manager: Optional[RandomStateManager] = None


def get_global_random_manager() -> RandomStateManager:
    """
    Get the global random state manager.
    
    Returns:
        Global RandomStateManager instance
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = RandomStateManager()
    return _global_manager


def set_global_seed(seed: Optional[int]) -> None:
    """
    Set the global random seed.
    
    Args:
        seed: Seed value
    """
    manager = get_global_random_manager()
    manager.set_seed(seed)


def generate_algorithm_seeds(
    n_algorithms: int,
    n_runs: int,
    base_seed: int = 42
) -> Dict[str, list[int]]:
    """
    Generate reproducible seeds for multiple algorithms and runs.
    
    Args:
        n_algorithms: Number of algorithms
        n_runs: Number of runs per algorithm
        base_seed: Base seed for generation
        
    Returns:
        Dictionary mapping algorithm index to list of seeds
    """
    manager = RandomStateManager(base_seed)
    seeds = {}
    
    for algo_idx in range(n_algorithms):
        algo_seeds = []
        for run_idx in range(n_runs):
            seed = manager.generate_sub_seed(f"algo_{algo_idx}_run_{run_idx}")
            algo_seeds.append(seed)
        seeds[f"algorithm_{algo_idx}"] = algo_seeds
    
    return seeds