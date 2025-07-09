"""
Traveling Salesman Problem (TSP) implementation.

The TSP seeks the shortest tour that visits all cities exactly once
and returns to the starting city.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import os
from problems.discrete.base import PermutationProblem


class TSPProblem(PermutationProblem):
    """
    Traveling Salesman Problem.
    
    Finds the shortest tour visiting all cities exactly once.
    """
    
    def __init__(
        self,
        distance_matrix: Optional[np.ndarray] = None,
        coordinates: Optional[np.ndarray] = None,
        name: str = "TSP"
    ):
        """
        Initialize TSP problem.
        
        Args:
            distance_matrix: Pre-computed distance matrix
            coordinates: 2D coordinates of cities (will compute distances)
            name: Problem instance name
        """
        if distance_matrix is None and coordinates is None:
            raise ValueError("Either distance_matrix or coordinates must be provided")
        
        if distance_matrix is not None:
            self.distance_matrix = np.asarray(distance_matrix)
            self.n_cities = len(self.distance_matrix)
        else:
            self.coordinates = np.asarray(coordinates)
            self.n_cities = len(self.coordinates)
            self._compute_distance_matrix()
        
        super().__init__(name if "-" in name else f"{name}-{self.n_cities}", self.n_cities)
        
        # Known optimal value (if available)
        self._best_known = None
        self._optimal_tour = None
    
    def _compute_distance_matrix(self) -> None:
        """Compute Euclidean distance matrix from coordinates."""
        n = self.n_cities
        self.distance_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(self.coordinates[i] - self.coordinates[j])
                self.distance_matrix[i, j] = dist
                self.distance_matrix[j, i] = dist
    
    def evaluate(self, tour: List[int]) -> float:
        """
        Calculate total tour length.
        
        Args:
            tour: Permutation of city indices
            
        Returns:
            Total distance of the tour
        """
        self._evaluations += 1
        
        if len(tour) != self.n_cities:
            return float('inf')
        
        total_distance = 0.0
        for i in range(self.n_cities):
            from_city = tour[i]
            to_city = tour[(i + 1) % self.n_cities]
            total_distance += self.distance_matrix[from_city, to_city]
        
        return total_distance
    
    def get_distance(self, city1: int, city2: int) -> float:
        """Get distance between two cities."""
        return self.distance_matrix[city1, city2]
    
    def nearest_neighbor_heuristic(self, start_city: int = 0) -> Tuple[List[int], float]:
        """
        Construct tour using nearest neighbor heuristic.
        
        Args:
            start_city: Starting city index
            
        Returns:
            tour: Constructed tour
            distance: Tour length
        """
        unvisited = set(range(self.n_cities))
        tour = [start_city]
        unvisited.remove(start_city)
        current = start_city
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: self.distance_matrix[current, x])
            tour.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return tour, self.evaluate(tour)
    
    def two_opt_improvement(self, tour: List[int], max_iterations: int = 1000) -> Tuple[List[int], float]:
        """
        Improve tour using 2-opt local search.
        
        Args:
            tour: Initial tour
            max_iterations: Maximum iterations
            
        Returns:
            Improved tour and its distance
        """
        best_tour = tour.copy()
        best_distance = self.evaluate(best_tour)
        improved = True
        iterations = 0
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i in range(self.n_cities):
                for j in range(i + 2, self.n_cities):
                    # Create new tour by reversing segment between i and j
                    new_tour = best_tour.copy()
                    new_tour[i:j] = reversed(new_tour[i:j])
                    
                    new_distance = self.evaluate(new_tour)
                    
                    if new_distance < best_distance - 1e-9:  # Improvement found
                        best_tour = new_tour
                        best_distance = new_distance
                        improved = True
                        break
                
                if improved:
                    break
        
        return best_tour, best_distance
    
    @classmethod
    def from_tsplib(cls, filepath: str) -> 'TSPProblem':
        """
        Load TSP instance from TSPLIB format file.
        
        Args:
            filepath: Path to TSPLIB file
            
        Returns:
            TSPProblem instance
        """
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        name = None
        dimension = None
        edge_weight_type = None
        node_coord_section = False
        edge_weight_section = False
        coordinates = []
        weights = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('NAME'):
                name = line.split(':')[1].strip()
            elif line.startswith('DIMENSION'):
                dimension = int(line.split(':')[1].strip())
            elif line.startswith('EDGE_WEIGHT_TYPE'):
                edge_weight_type = line.split(':')[1].strip()
            elif line == 'NODE_COORD_SECTION':
                node_coord_section = True
                edge_weight_section = False
            elif line == 'EDGE_WEIGHT_SECTION':
                edge_weight_section = True
                node_coord_section = False
            elif line == 'EOF':
                break
            elif node_coord_section and line:
                parts = line.split()
                if len(parts) >= 3:
                    # Format: index x y
                    x, y = float(parts[1]), float(parts[2])
                    coordinates.append([x, y])
            elif edge_weight_section and line:
                # Handle explicit edge weights
                weights.extend([float(x) for x in line.split()])
        
        # Create problem instance
        if coordinates:
            problem = cls(coordinates=np.array(coordinates), name=name or "TSP")
        elif weights and dimension:
            # Reconstruct distance matrix from weights
            matrix = np.zeros((dimension, dimension))
            idx = 0
            for i in range(dimension):
                for j in range(i + 1, dimension):
                    matrix[i, j] = weights[idx]
                    matrix[j, i] = weights[idx]
                    idx += 1
            problem = cls(distance_matrix=matrix, name=name or "TSP")
        else:
            raise ValueError("Could not parse TSP instance from file")
        
        return problem
    
    @classmethod
    def generate_random(cls, n_cities: int, seed: Optional[int] = None) -> 'TSPProblem':
        """
        Generate random TSP instance.
        
        Args:
            n_cities: Number of cities
            seed: Random seed
            
        Returns:
            Random TSP instance
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Generate random coordinates in [0, 100]²
        coordinates = np.random.uniform(0, 100, size=(n_cities, 2))
        return cls(coordinates=coordinates, name=f"Random-{n_cities}")
    
    def save_solution(self, tour: List[int], filename: str) -> None:
        """
        Save tour to file.
        
        Args:
            tour: Tour to save
            filename: Output filename
        """
        with open(filename, 'w') as f:
            f.write(f"NAME : {self.name} Solution\n")
            f.write(f"TYPE : TOUR\n")
            f.write(f"DIMENSION : {self.n_cities}\n")
            f.write(f"TOUR_SECTION\n")
            for city in tour:
                f.write(f"{city + 1}\n")  # TSPLIB uses 1-based indexing
            f.write("-1\nEOF\n")
    
    def plot_tour(self, tour: List[int], title: Optional[str] = None) -> None:
        """
        Plot TSP tour (requires matplotlib).
        
        Args:
            tour: Tour to plot
            title: Plot title
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib not available for plotting")
            return
        
        if not hasattr(self, 'coordinates'):
            print("Cannot plot without city coordinates")
            return
        
        plt.figure(figsize=(10, 8))
        
        # Plot cities
        x = self.coordinates[:, 0]
        y = self.coordinates[:, 1]
        plt.scatter(x, y, c='red', s=100, zorder=2)
        
        # Plot tour
        tour_x = [self.coordinates[tour[i], 0] for i in range(len(tour))]
        tour_y = [self.coordinates[tour[i], 1] for i in range(len(tour))]
        tour_x.append(tour_x[0])  # Close the tour
        tour_y.append(tour_y[0])
        plt.plot(tour_x, tour_y, 'b-', alpha=0.7, linewidth=2, zorder=1)
        
        # Add city labels
        for i in range(self.n_cities):
            plt.annotate(str(i), (x[i], y[i]), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8)
        
        plt.title(title or f"TSP Tour - Length: {self.evaluate(tour):.2f}")
        plt.xlabel("X coordinate")
        plt.ylabel("Y coordinate")
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.tight_layout()
        plt.show()
    
    def get_neighbors(self, tour: List[int]) -> List[List[int]]:
        """
        Get all 2-opt neighbors of a tour.
        
        Args:
            tour: Current tour
            
        Returns:
            List of neighboring tours
        """
        neighbors = []
        n = len(tour)
        
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                
                neighbor = tour.copy()
                neighbor[i+1:j+1] = neighbor[i+1:j+1][::-1]
                neighbors.append(neighbor)
        
        return neighbors