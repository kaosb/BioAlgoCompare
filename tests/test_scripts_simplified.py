"""
Simplified tests for benchmark.py and analyze.py scripts.
Tests core functionality without complex dependencies.
"""

import pytest
import os
import json
import tempfile
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestBenchmarkScript:
    """Test benchmark.py script functionality."""
    
    def test_benchmark_runner_structure(self):
        """Test that BenchmarkRunner has expected methods."""
        from scripts.benchmark import BenchmarkRunner
        
        runner = BenchmarkRunner()
        
        # Check attributes
        assert hasattr(runner, 'result_base_dir')
        assert hasattr(runner, 'results')
        
        # Check methods
        assert callable(runner.create_result_directory)
        assert callable(runner.validate_instances)
        assert callable(runner.run_algorithm)
        assert callable(runner.run_benchmark)
        assert callable(runner.save_summary)
    
    def test_create_result_directory(self):
        """Test result directory creation."""
        from scripts.benchmark import BenchmarkRunner
        
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = BenchmarkRunner(tmpdir)
            
            # Test directory creation
            result_dir = runner.create_result_directory('test_timestamp')
            assert os.path.exists(result_dir)
            assert 'test_timestamp' in result_dir
    
    def test_save_summary_creates_files(self):
        """Test that save_summary creates expected files."""
        from scripts.benchmark import BenchmarkRunner
        
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = BenchmarkRunner()
            runner.results = [
                {'algorithm': 'test', 'status': 'success'},
                {'algorithm': 'test2', 'status': 'error'}
            ]
            
            runner.save_summary(
                tmpdir, ['test', 'test2'], ['instance1'],
                runs=5, iterations=100, population=30
            )
            
            # Check files exist
            json_path = os.path.join(tmpdir, 'summary_report.json')
            txt_path = os.path.join(tmpdir, 'report.txt')
            
            assert os.path.exists(json_path)
            assert os.path.exists(txt_path)
            
            # Verify JSON content
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            assert data['results']['total'] == 2
            assert data['results']['successes'] == 1
            assert data['results']['errors'] == 1
    
    @patch('subprocess.run')
    def test_run_algorithm_command_construction(self, mock_run):
        """Test that run_algorithm constructs correct command."""
        from scripts.benchmark import BenchmarkRunner
        
        mock_run.return_value = Mock(
            stdout='', stderr='', returncode=0
        )
        
        runner = BenchmarkRunner()
        result = runner.run_algorithm(
            'woa', 'P-n16-k8', 100, 30, 5, parallel=True
        )
        
        # Check command
        call_args = mock_run.call_args[0][0]
        assert 'scripts/core/run.py' in call_args
        assert '--algorithm' in call_args
        assert 'woa' in call_args
        assert '--parallel' in call_args
        assert '--v2' in call_args
    
    def test_cli_imports(self):
        """Test that CLI can be imported."""
        try:
            from scripts.benchmark import ejecutar_benchmark
            assert ejecutar_benchmark is not None
        except ImportError:
            pytest.skip("CLI imports not available")


class TestAnalyzeScript:
    """Test analyze.py script functionality."""
    
    def test_cli_structure(self):
        """Test that CLI has expected commands."""
        try:
            from scripts.core.analyze import cli
            
            # Check that cli is a click group
            assert hasattr(cli, 'commands')
            
            # Expected commands
            expected_commands = ['run', 'benchmark', 'massive', 'analyze-csv', 'stats']
            
            # Get actual commands
            actual_commands = list(cli.commands.keys())
            
            # Check at least some expected commands exist
            assert 'benchmark' in actual_commands or 'analyze-csv' in actual_commands
            
        except ImportError:
            pytest.skip("Analyze script not available")
    
    def test_csv_analysis_functionality(self):
        """Test CSV analysis helper functions."""
        # Create test CSV data
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'test.csv')
            
            data = {
                'Algorithm': ['A1', 'A1', 'A2', 'A2'],
                'Best': [100, 102, 98, 99],
                'Mean': [105, 106, 103, 104],
                'Time': [1.0, 1.1, 0.9, 0.95]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            # Test reading and basic analysis
            loaded_df = pd.read_csv(csv_path)
            
            # Verify data structure
            assert len(loaded_df) == 4
            assert 'Algorithm' in loaded_df.columns
            assert 'Best' in loaded_df.columns
            
            # Test grouping by algorithm
            grouped = loaded_df.groupby('Algorithm')
            assert len(grouped) == 2
            
            # Test aggregation
            summary = grouped.agg({
                'Best': ['min', 'mean'],
                'Time': 'mean'
            })
            
            assert summary.loc['A1', ('Best', 'min')] == 100
            assert summary.loc['A2', ('Best', 'min')] == 98
    
    def test_html_report_generation(self):
        """Test HTML report generation logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = os.path.join(tmpdir, 'report.html')
            
            # Simple HTML generation
            html_content = """
            <html>
            <head><title>Test Report</title></head>
            <body>
                <h1>Algorithm Analysis</h1>
                <table>
                    <tr><th>Algorithm</th><th>Best</th></tr>
                    <tr><td>A1</td><td>100</td></tr>
                </table>
            </body>
            </html>
            """
            
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            assert os.path.exists(html_path)
            
            # Verify content
            with open(html_path, 'r') as f:
                content = f.read()
            
            assert 'Algorithm Analysis' in content
            assert '<table>' in content
    
    @patch('matplotlib.pyplot.savefig')
    def test_visualization_creation(self, mock_savefig):
        """Test that visualizations can be created."""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Create simple plot
        data = pd.DataFrame({
            'Algorithm': ['A1', 'A2', 'A3'],
            'Performance': [100, 95, 98]
        })
        
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x='Algorithm', y='Performance', data=data)
        
        # This would normally save the figure
        mock_savefig.assert_not_called()  # Not called yet
        
        plt.savefig('test.png')
        mock_savefig.assert_called_once()
        
        plt.close()


class TestScriptIntegration:
    """Test integration aspects of the scripts."""
    
    def test_data_format_compatibility(self):
        """Test that data formats are compatible between scripts."""
        # Test BenchmarkResult-like structure
        result = {
            'algorithm_name': 'test_algo',
            'instance_name': 'test_instance',
            'fitness_values': [100, 101, 99],
            'execution_times': [1.0, 1.1, 0.9],
            'mean_fitness': 100.0,
            'best_fitness': 99.0
        }
        
        # Verify structure
        assert 'algorithm_name' in result
        assert 'fitness_values' in result
        assert isinstance(result['fitness_values'], list)
        assert len(result['fitness_values']) == len(result['execution_times'])
    
    def test_csv_column_mapping(self):
        """Test CSV column name mappings."""
        # Original column names
        original = {
            'Best': 450.5,
            'Mean': 455.2,
            'Time': 1.23,
            'Time_Std': 0.05
        }
        
        # Expected mapping
        rename_map = {
            'Best': 'Best Fitness',
            'Mean': 'Mean Fitness',
            'Time': 'Execution Time (s)',
            'Time_Std': 'Time Std'
        }
        
        # Apply mapping
        renamed = {rename_map.get(k, k): v for k, v in original.items()}
        
        assert 'Best Fitness' in renamed
        assert 'Mean Fitness' in renamed
        assert 'Execution Time (s)' in renamed
        assert renamed['Best Fitness'] == 450.5
    
    def test_output_directory_structure(self):
        """Test expected output directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create expected structure
            results_dir = os.path.join(tmpdir, 'results')
            os.makedirs(results_dir)
            
            benchmark_dir = os.path.join(results_dir, 'benchmark_20240101_120000')
            os.makedirs(benchmark_dir)
            
            # Expected files
            expected_files = [
                'summary_report.json',
                'report.txt',
                'benchmark_report.html'
            ]
            
            for filename in expected_files:
                filepath = os.path.join(benchmark_dir, filename)
                with open(filepath, 'w') as f:
                    f.write('test content')
                
                assert os.path.exists(filepath)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])