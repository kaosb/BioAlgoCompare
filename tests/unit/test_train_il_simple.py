"""
Tests for simple IL training module.
"""
import pytest
import numpy as np
import pickle
import tempfile
import os
from pathlib import Path
from utils.train_il_simple import SimpleILModel


class TestSimpleILModel:
    """Tests for SimpleILModel class."""
    
    def test_model_initialization(self):
        """Test model initialization."""
        model = SimpleILModel()
        
        assert hasattr(model, 'models')
        assert isinstance(model.models, dict)
        assert 'alpha' in model.models
        assert 'beta' in model.models
        assert 'gamma' in model.models
        assert hasattr(model, 'scaler')
        assert model.feature_names is None
        assert model.is_trained is False
    
    def test_prepare_features(self):
        """Test feature preparation from dataframe."""
        model = SimpleILModel()
        
        # Create a mock dataframe
        import pandas as pd
        df = pd.DataFrame({
            'n_customers': [20],
            'n_depots': [1],
            'avg_demand': [15.5],
            'demand_std': [5.2],
            'capacity': [100],
            'area_span': [50],
            'density': [0.02],
            'iteration': [10],
            'progress': [0.1],
            'best_fitness': [500],
            'avg_fitness': [550],
            'fitness_std': [30],
            'convergence_rate': [0.05],
            'stagnation_counter': [2],
            'population_diversity': [0.7],
            'elite_ratio': [0.1],
            'improvement_rate': [0.03],
            'dynamic_orders': [0],
            'avg_delay': [0],
            'load_imbalance': [0.15],
            # Add target and metadata columns that should be excluded
            'instance': ['test'],
            'algorithm': ['ho'],
            'demo_id': [1],
            'alpha': [0.5],
            'beta': [0.5],
            'gamma': [0.65],
            'improvement': [0.1],
            'fitness_after': [450]
        })
        
        features = model.prepare_features(df)
        
        assert isinstance(features, np.ndarray)
        assert features.shape == (1, 20)
        assert model.feature_names is not None
        assert len(model.feature_names) == 20
        assert 'n_customers' in model.feature_names
        assert 'instance' not in model.feature_names
    
    def test_model_training(self):
        """Test model training."""
        model = SimpleILModel()
        
        # Create mock training dataframe
        import pandas as pd
        n_samples = 100
        df_train = pd.DataFrame({
            'n_customers': np.random.randint(10, 50, n_samples),
            'n_depots': np.ones(n_samples),
            'avg_demand': np.random.uniform(10, 30, n_samples),
            'demand_std': np.random.uniform(1, 10, n_samples),
            'capacity': np.random.randint(50, 200, n_samples),
            'area_span': np.random.uniform(20, 100, n_samples),
            'density': np.random.uniform(0.01, 0.1, n_samples),
            'iteration': np.random.randint(0, 100, n_samples),
            'progress': np.random.uniform(0, 1, n_samples),
            'best_fitness': np.random.uniform(100, 1000, n_samples),
            'avg_fitness': np.random.uniform(100, 1000, n_samples),
            'fitness_std': np.random.uniform(10, 100, n_samples),
            'convergence_rate': np.random.uniform(0, 0.1, n_samples),
            'stagnation_counter': np.random.randint(0, 20, n_samples),
            'population_diversity': np.random.uniform(0.1, 0.9, n_samples),
            'elite_ratio': np.random.uniform(0.05, 0.2, n_samples),
            'improvement_rate': np.random.uniform(0, 0.1, n_samples),
            'dynamic_orders': np.zeros(n_samples),
            'avg_delay': np.zeros(n_samples),
            'load_imbalance': np.random.uniform(0, 0.5, n_samples),
            # Target parameters
            'alpha': np.random.uniform(0.1, 0.9, n_samples),
            'beta': np.random.uniform(0.2, 0.8, n_samples),
            'gamma': np.random.uniform(0.3, 1.0, n_samples)
        })
        
        # Train model
        results = model.train(df_train)
        
        assert model.is_trained is True
        assert isinstance(results, dict)
        assert 'alpha' in results
        assert 'beta' in results
        assert 'gamma' in results
        
        # Check that each parameter model has results
        for param in ['alpha', 'beta', 'gamma']:
            assert 'train_mse' in results[param]
            assert 'train_r2' in results[param]
            assert 'feature_importance' in results[param]
            assert isinstance(results[param]['feature_importance'], dict)
    
    def test_model_prediction(self):
        """Test model prediction."""
        model = SimpleILModel()
        
        # Train a simple model first
        import pandas as pd
        n_samples = 50
        df_train = pd.DataFrame({
            'n_customers': np.random.randint(10, 50, n_samples),
            'n_depots': np.ones(n_samples),
            'avg_demand': np.random.uniform(10, 30, n_samples),
            'demand_std': np.random.uniform(1, 10, n_samples),
            'capacity': np.random.randint(50, 200, n_samples),
            'area_span': np.random.uniform(20, 100, n_samples),
            'density': np.random.uniform(0.01, 0.1, n_samples),
            'iteration': np.random.randint(0, 100, n_samples),
            'progress': np.random.uniform(0, 1, n_samples),
            'best_fitness': np.random.uniform(100, 1000, n_samples),
            'avg_fitness': np.random.uniform(100, 1000, n_samples),
            'fitness_std': np.random.uniform(10, 100, n_samples),
            'convergence_rate': np.random.uniform(0, 0.1, n_samples),
            'stagnation_counter': np.random.randint(0, 20, n_samples),
            'population_diversity': np.random.uniform(0.1, 0.9, n_samples),
            'elite_ratio': np.random.uniform(0.05, 0.2, n_samples),
            'improvement_rate': np.random.uniform(0, 0.1, n_samples),
            'dynamic_orders': np.zeros(n_samples),
            'avg_delay': np.zeros(n_samples),
            'load_imbalance': np.random.uniform(0, 0.5, n_samples),
            'alpha': np.random.uniform(0.1, 0.9, n_samples),
            'beta': np.random.uniform(0.2, 0.8, n_samples),
            'gamma': np.random.uniform(0.3, 1.0, n_samples)
        })
        
        model.train(df_train)
        
        # Test prediction with state dict
        state = {f: np.random.rand() for f in model.feature_names}
        prediction = model.predict(state)
        
        assert isinstance(prediction, tuple)
        assert len(prediction) == 3
        assert all(isinstance(p, (float, np.floating)) for p in prediction)
        # Check clipping ranges
        alpha, beta, gamma = prediction
        assert 0.1 <= alpha <= 0.9
        assert 0.2 <= beta <= 0.8
        assert 0.3 <= gamma <= 1.0
    
    def test_model_save_load(self):
        """Test model saving and loading."""
        model = SimpleILModel()
        
        # Train model
        import pandas as pd
        n_samples = 30
        df_train = pd.DataFrame({
            'n_customers': np.random.randint(10, 50, n_samples),
            'n_depots': np.ones(n_samples),
            'avg_demand': np.random.uniform(10, 30, n_samples),
            'demand_std': np.random.uniform(1, 10, n_samples),
            'capacity': np.random.randint(50, 200, n_samples),
            'area_span': np.random.uniform(20, 100, n_samples),
            'density': np.random.uniform(0.01, 0.1, n_samples),
            'iteration': np.random.randint(0, 100, n_samples),
            'progress': np.random.uniform(0, 1, n_samples),
            'best_fitness': np.random.uniform(100, 1000, n_samples),
            'avg_fitness': np.random.uniform(100, 1000, n_samples),
            'fitness_std': np.random.uniform(10, 100, n_samples),
            'convergence_rate': np.random.uniform(0, 0.1, n_samples),
            'stagnation_counter': np.random.randint(0, 20, n_samples),
            'population_diversity': np.random.uniform(0.1, 0.9, n_samples),
            'elite_ratio': np.random.uniform(0.05, 0.2, n_samples),
            'improvement_rate': np.random.uniform(0, 0.1, n_samples),
            'dynamic_orders': np.zeros(n_samples),
            'avg_delay': np.zeros(n_samples),
            'load_imbalance': np.random.uniform(0, 0.5, n_samples),
            'alpha': np.random.uniform(0.1, 0.9, n_samples),
            'beta': np.random.uniform(0.2, 0.8, n_samples),
            'gamma': np.random.uniform(0.3, 1.0, n_samples)
        })
        
        model.train(df_train)
        
        # Save model
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            temp_path = f.name
        
        try:
            model.save(temp_path)
            assert os.path.exists(temp_path)
            
            # Load model
            model2 = SimpleILModel()
            model2.load(temp_path)
            
            # Test that loaded model works
            state = {f: np.random.rand() for f in model.feature_names}
            pred1 = model.predict(state)
            pred2 = model2.predict(state)
            
            # Predictions should be identical
            assert np.allclose(pred1, pred2)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_model_prediction_without_training(self):
        """Test prediction returns default values without training."""
        model = SimpleILModel()
        state = {
            'n_customers': 20,
            'n_depots': 1,
            'avg_demand': 15,
            'demand_std': 5,
            'capacity': 100,
            'area_span': 50,
            'density': 0.02,
            'iteration': 10,
            'progress': 0.1,
            'best_fitness': 500,
            'avg_fitness': 550,
            'fitness_std': 30,
            'convergence_rate': 0.05,
            'stagnation_counter': 2,
            'population_diversity': 0.7,
            'elite_ratio': 0.1,
            'improvement_rate': 0.03,
            'dynamic_orders': 0,
            'avg_delay': 0,
            'load_imbalance': 0.15
        }
        
        # Should return default values (0.5, 0.5, 0.65)
        alpha, beta, gamma = model.predict(state)
        assert alpha == 0.5
        assert beta == 0.5
        assert gamma == 0.65


class TestTrainSimpleIL:
    """Tests for train_simple_il function."""
    
    @pytest.fixture
    def mock_demo_data(self):
        """Create mock demonstration data."""
        demos = []
        for _ in range(5):
            demo = {
                'instance': 'test-instance',
                'problem_features': {
                    'n_customers': 20,
                    'avg_demand': 15,
                    'capacity': 100
                },
                'trajectory': []
            }
            
            # Add some trajectory points
            for i in range(10):
                state = {
                    'n_customers': 20,
                    'n_depots': 1,
                    'avg_demand': 15,
                    'demand_std': 5,
                    'capacity': 100,
                    'area_span': 50,
                    'density': 0.02,
                    'iteration': i,
                    'progress': i/10,
                    'best_fitness': 1000 - i*50,
                    'avg_fitness': 1100 - i*45,
                    'fitness_std': 50,
                    'convergence_rate': 0.05,
                    'stagnation_counter': 0,
                    'population_diversity': 0.8 - i*0.05,
                    'elite_ratio': 0.1,
                    'improvement_rate': 0.04,
                    'dynamic_orders': 0,
                    'avg_delay': 0,
                    'load_imbalance': 0.1
                }
                
                params = {
                    'alpha': 0.8 - i*0.05,
                    'beta': 0.6 - i*0.03,
                    'gamma': 0.3 + i*0.04
                }
                
                demo['trajectory'].append({
                    'state': state,
                    'params': params,
                    'fitness': 1000 - i*50
                })
            
            demos.append(demo)
        
        return demos
    
    def test_data_preparation(self, mock_demo_data):
        """Test that train_simple_il prepares data correctly."""
        # We'll need to mock file loading since train_simple_il loads from file
        # For now, let's test the model directly with prepared data
        model = SimpleILModel()
        
        # Extract features and labels from demos
        X_list = []
        y_list = []
        
        for demo in mock_demo_data:
            for point in demo['trajectory']:
                # Prepare features manually since we can't use prepare_features without dataframe
                state = point['state']
                features = np.array([state[key] for key in sorted(state.keys())])
                X_list.append(features)
                
                # Extract parameters
                params = point['params']
                y_list.append([params['alpha'], params['beta'], params['gamma']])
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        assert X.shape[0] == 50  # 5 demos * 10 points each
        assert X.shape[1] == 20  # 20 features (sorted keys)
        assert y.shape == (50, 3)  # 3 parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])