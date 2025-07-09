"""
Job Shop Scheduling Problem (JSP) implementation.

The JSP involves scheduling n jobs on m machines, where each job has a specific
sequence of operations that must be performed on different machines.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from problems.discrete.base import DiscreteOptimizationProblem


class Operation:
    """Represents a single operation in a job."""
    
    def __init__(self, job_id: int, op_id: int, machine_id: int, processing_time: int):
        """
        Initialize an operation.
        
        Args:
            job_id: ID of the job this operation belongs to
            op_id: ID of this operation within the job
            machine_id: Machine required for this operation
            processing_time: Time required to process this operation
        """
        self.job_id = job_id
        self.op_id = op_id
        self.machine_id = machine_id
        self.processing_time = processing_time
        self.start_time = 0
        self.end_time = 0
    
    def __repr__(self):
        return f"Op(J{self.job_id}-{self.op_id}, M{self.machine_id}, t={self.processing_time})"


class JobShopProblem(DiscreteOptimizationProblem):
    """
    Job Shop Scheduling Problem implementation.
    
    The problem consists of:
    - n jobs, each with a sequence of operations
    - m machines, each can process one operation at a time
    - Each operation must be processed on a specific machine
    - Operations of a job must be processed in order
    - Minimize makespan (total completion time)
    """
    
    def __init__(
        self,
        jobs: List[List[Tuple[int, int]]],
        name: str = "JSP"
    ):
        """
        Initialize a Job Shop Problem instance.
        
        Args:
            jobs: List of jobs, where each job is a list of (machine_id, processing_time) tuples
            name: Problem instance name
        """
        self.n_jobs = len(jobs)
        self.n_machines = max(machine for job in jobs for machine, _ in job) + 1
        self.n_operations = sum(len(job) for job in jobs)
        
        # Create operations list
        self.operations: List[Operation] = []
        self.job_operations: Dict[int, List[Operation]] = {i: [] for i in range(self.n_jobs)}
        
        op_count = 0
        for job_id, job in enumerate(jobs):
            for op_id, (machine_id, proc_time) in enumerate(job):
                op = Operation(job_id, op_id, machine_id, proc_time)
                self.operations.append(op)
                self.job_operations[job_id].append(op)
                op_count += 1
        
        # Initialize base class with dimension = number of operations
        # We'll use priority-based encoding
        super().__init__(
            name=f"{name}-{self.n_jobs}x{self.n_machines}",
            dimension=self.n_operations
        )
        
        # Cache for decoding
        self._last_continuous = None
        self._last_schedule = None
        self._last_makespan = None
    
    def encode_continuous(self, continuous: np.ndarray) -> List[int]:
        """
        Convert continuous representation to operation sequence.
        
        Uses priority-based encoding where each continuous value represents
        the priority of an operation. Operations are scheduled in order of priority.
        
        Args:
            continuous: Vector of priorities in [0, 1]
            
        Returns:
            List of operation indices representing the schedule
        """
        # Sort operations by priority
        priorities = list(enumerate(continuous))
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Extract operation order
        return [idx for idx, _ in priorities]
    
    def decode_to_continuous(self, discrete: List[int]) -> np.ndarray:
        """
        Convert operation sequence to continuous representation.
        
        Args:
            discrete: List of operation indices
            
        Returns:
            Continuous vector with priorities
        """
        n = len(discrete)
        continuous = np.zeros(n)
        
        # Assign priorities based on position in sequence
        for i, op_idx in enumerate(discrete):
            continuous[op_idx] = 1.0 - (i / n)
        
        return continuous
    
    def evaluate(self, solution: Any) -> float:
        """
        Evaluate a solution by computing its makespan.
        
        For infeasible solutions, returns a large penalty value instead
        of infinity to help algorithms navigate the search space.
        
        Args:
            solution: Either continuous vector or discrete sequence
            
        Returns:
            Makespan (total completion time) or penalty for infeasible solutions
        """
        self._evaluations += 1
        
        # Handle both continuous and discrete inputs
        if isinstance(solution, np.ndarray):
            # Check cache
            if self._last_continuous is not None and np.array_equal(solution, self._last_continuous):
                return self._last_makespan
            
            sequence = self.encode_continuous(solution)
            self._last_continuous = solution.copy()
        else:
            sequence = solution
        
        # Build schedule and compute makespan
        makespan = self._compute_makespan(sequence)
        
        # Apply penalty for infeasible solutions instead of infinity
        if makespan == float('inf'):
            # Large penalty based on problem size
            penalty_base = 10000 * self.n_operations
            # Add some variation based on solution to avoid plateaus
            solution_hash = hash(tuple(sequence)) % 1000
            makespan = penalty_base + solution_hash
        
        self._last_makespan = makespan
        self._last_schedule = sequence
        
        return makespan
    
    def _compute_makespan(self, sequence: List[int]) -> float:
        """
        Compute makespan for a given operation sequence.
        
        Args:
            sequence: List of operation indices
            
        Returns:
            Makespan value
        """
        # Initialize tracking structures
        job_next_op = [0] * self.n_jobs  # Next operation index for each job
        machine_available = [0] * self.n_machines  # When each machine becomes available
        job_available = [0] * self.n_jobs  # When each job's last op finished
        
        makespan = 0
        
        # Process operations in given sequence
        for op_idx in sequence:
            op = self.operations[op_idx]
            
            # Check if this operation can be scheduled (precedence constraint)
            if job_next_op[op.job_id] != op.op_id:
                # Invalid sequence - precedence violated
                return float('inf')
            
            # Calculate start time (max of machine and job availability)
            start_time = max(machine_available[op.machine_id], job_available[op.job_id])
            end_time = start_time + op.processing_time
            
            # Update tracking
            op.start_time = start_time
            op.end_time = end_time
            machine_available[op.machine_id] = end_time
            job_available[op.job_id] = end_time
            job_next_op[op.job_id] += 1
            
            makespan = max(makespan, end_time)
        
        # Check if all operations were scheduled
        if any(job_next_op[i] != len(self.job_operations[i]) for i in range(self.n_jobs)):
            return float('inf')  # Invalid sequence
        
        return float(makespan)
    
    def random_solution(self) -> List[int]:
        """
        Generate a random feasible solution.
        
        Returns:
            Valid operation sequence
        """
        # Use a priority-based approach
        remaining_ops = []
        for job_id in range(self.n_jobs):
            for op in self.job_operations[job_id]:
                remaining_ops.append((job_id, op))
        
        sequence = []
        job_next = [0] * self.n_jobs
        
        while remaining_ops:
            # Get eligible operations (next operation of each job)
            eligible = []
            for i, (job_id, op) in enumerate(remaining_ops):
                if op.op_id == job_next[job_id]:
                    eligible.append(i)
            
            if not eligible:
                break  # Should not happen with valid input
            
            # Randomly select one
            idx = np.random.choice(eligible)
            job_id, op = remaining_ops.pop(idx)
            
            # Find operation index in global list
            op_idx = self.operations.index(op)
            sequence.append(op_idx)
            job_next[job_id] += 1
        
        return sequence
    
    def is_feasible(self, solution: Any) -> bool:
        """
        Check if a solution respects precedence constraints.
        
        Args:
            solution: Solution to check
            
        Returns:
            True if feasible
        """
        if isinstance(solution, np.ndarray):
            sequence = self.encode_continuous(solution)
        else:
            sequence = solution
        
        # Check precedence constraints
        job_next_op = [0] * self.n_jobs
        
        for op_idx in sequence:
            op = self.operations[op_idx]
            if job_next_op[op.job_id] != op.op_id:
                return False
            job_next_op[op.job_id] += 1
        
        # Check all operations scheduled
        return all(job_next_op[i] == len(self.job_operations[i]) for i in range(self.n_jobs))
    
    @property
    def search_space_size(self) -> int:
        """
        Get the size of the discrete search space.
        
        For JSP with n jobs and m machines, the search space is all
        possible permutations of n*m operations.
        
        Returns:
            Factorial of n_operations
        """
        import math
        return math.factorial(self.n_operations)
    
    def get_schedule_gantt_data(self, solution: Any = None) -> List[Dict[str, Any]]:
        """
        Get Gantt chart data for visualization.
        
        Args:
            solution: Solution to visualize (uses last evaluated if None)
            
        Returns:
            List of operation data for Gantt chart
        """
        if solution is not None:
            self.evaluate(solution)
        
        gantt_data = []
        for op in self.operations:
            gantt_data.append({
                'job': f"Job {op.job_id}",
                'machine': f"Machine {op.machine_id}",
                'start': op.start_time,
                'end': op.end_time,
                'operation': f"J{op.job_id}-O{op.op_id}"
            })
        
        return gantt_data
    
    def critical_path(self, solution: Any = None) -> List[Operation]:
        """
        Find the critical path in the schedule.
        
        Args:
            solution: Solution to analyze (uses last evaluated if None)
            
        Returns:
            List of operations on the critical path
        """
        if solution is not None:
            self.evaluate(solution)
        
        # Build precedence graph and find critical path
        # This is a simplified version - full implementation would use
        # topological sort and longest path algorithm
        critical = []
        makespan = max(op.end_time for op in self.operations)
        
        # Find operations that end at makespan
        for op in self.operations:
            if op.end_time == makespan:
                critical.append(op)
                break
        
        return critical
    
    @classmethod
    def from_standard_instance(cls, instance_data: Dict[str, Any]) -> 'JobShopProblem':
        """
        Create JSP from standard benchmark format.
        
        Args:
            instance_data: Dictionary with 'jobs' key containing job data
            
        Returns:
            JobShopProblem instance
        """
        return cls(instance_data['jobs'], instance_data.get('name', 'JSP'))
    
    @classmethod
    def generate_random(
        cls,
        n_jobs: int,
        n_machines: int,
        min_time: int = 1,
        max_time: int = 99,
        seed: Optional[int] = None
    ) -> 'JobShopProblem':
        """
        Generate a random JSP instance.
        
        Args:
            n_jobs: Number of jobs
            n_machines: Number of machines
            min_time: Minimum processing time
            max_time: Maximum processing time
            seed: Random seed
            
        Returns:
            Random JSP instance
        """
        if seed is not None:
            np.random.seed(seed)
        
        jobs = []
        for _ in range(n_jobs):
            # Random permutation of machines
            machines = np.random.permutation(n_machines)
            # Random processing times
            times = np.random.randint(min_time, max_time + 1, n_machines)
            
            job = [(int(m), int(t)) for m, t in zip(machines, times)]
            jobs.append(job)
        
        return cls(jobs, "Random")
    
    # Compatibility methods for legacy interface
    def get_dimension(self) -> int:
        """Get problem dimension for continuous encoding."""
        return self.dimension
    
    def get_lower_bounds(self) -> np.ndarray:
        """Get lower bounds for continuous representation."""
        return np.zeros(self.dimension)
    
    def get_upper_bounds(self) -> np.ndarray:
        """Get upper bounds for continuous representation."""
        return np.ones(self.dimension)