"""
Tests for the analyze.py script.
"""

import pytest
import os
import json
import tempfile
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from click.testing import CliRunner

# Import script components
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ensure all required modules are available
try:
    from scripts.cli.analyze import cli, ALGORITHMS
    from utils.benchmarking import BenchmarkResult
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestAnalyzeCLI:
    """Test the analyze CLI commands."""
    
    def test_cli_help(self):
        """Test CLI help functionality."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Herramienta unificada para análisis' in result.output
    
    def test_run_command_help(self):
        """Test run command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['run', '--help'])
        assert result.exit_code == 0
        assert 'Ejecuta algoritmos de optimización' in result.output
    
    @patch('scripts.cli.run.main', create=True)
    def test_run_command_basic(self, mock_run_main):
        """Test basic run command execution."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'run',
            '--algorithm', 'woa',
            '--instance', 'P-n16-k8',
            '--iterations', '50',
            '--population', '20',
            '--runs', '3'
        ])
        
        assert result.exit_code == 0
        mock_run_main.assert_called_once_with(
            'woa', 'P-n16-k8', 50, 20, 3, 
            None, True, True, False
        )
    
    def test_benchmark_command_help(self):
        """Test benchmark command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['benchmark', '--help'])
        assert result.exit_code == 0
        assert 'Analiza resultados de algoritmos' in result.output


class TestBenchmarkCommand:
    """Test the benchmark analysis command."""
    
    def create_test_csv(self, tmpdir, filename='results.csv'):
        """Create a test CSV file with results."""
        data = {
            'Algorithm': ['WOA', 'WOA', 'SMA', 'SMA'],
            'Instance': ['P-n16-k8', 'P-n16-k8', 'P-n16-k8', 'P-n16-k8'],
            'Run': [1, 2, 1, 2],
            'Best': [450.5, 452.3, 448.9, 451.2],
            'Mean': [455.2, 456.1, 453.4, 454.8],
            'Time': [1.23, 1.25, 1.45, 1.48],
            'Time_Std': [0.05, 0.06, 0.07, 0.08]
        }
        df = pd.DataFrame(data)
        csv_path = os.path.join(tmpdir, filename)
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def create_test_json(self, tmpdir, filename='benchmark.json'):
        """Create a test JSON file with benchmark results."""
        results = []
        
        # Create mock BenchmarkResult objects
        for algo in ['woa', 'sma']:
            result = {
                'algorithm_name': algo,
                'instance_name': 'P-n16-k8',
                'fitness_values': [450.5, 452.3],
                'execution_times': [1.23, 1.25],
                'mean_fitness': 451.4,
                'std_fitness': 0.9,
                'best_fitness': 450.5,
                'mean_time': 1.24,
                'std_time': 0.01,
                'gap_to_optimal': None
            }
            results.append(result)
        
        json_path = os.path.join(tmpdir, filename)
        with open(json_path, 'w') as f:
            json.dump(results, f)
        return json_path
    
    @patch('scripts.cli.analyze.create_benchmark_report')
    @patch('scripts.cli.analyze.logger')
    def test_benchmark_load_csv(self, mock_logger, mock_create_report):
        """Test loading results from CSV file."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = self.create_test_csv(tmpdir)
            
            result = runner.invoke(cli, [
                'benchmark',
                '--input', csv_path,
                '--output-dir', tmpdir
            ])
            
            assert result.exit_code == 0
            mock_create_report.assert_called()
            
            # Check that results were loaded
            assert any('Cargados' in str(call) for call in mock_logger.info.call_args_list)
    
    @patch('scripts.cli.analyze.create_benchmark_report')
    @patch('scripts.cli.analyze.load_benchmark_results')
    def test_benchmark_load_json(self, mock_load, mock_create_report):
        """Test loading results from JSON file."""
        runner = CliRunner()
        
        # Mock loaded results
        mock_results = [
            Mock(spec=BenchmarkResult, 
                 algorithm_name='woa',
                 instance_name='P-n16-k8',
                 fitness_values=[450.5],
                 gap_to_optimal=None)
        ]
        mock_load.return_value = mock_results
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = self.create_test_json(tmpdir)
            
            result = runner.invoke(cli, [
                'benchmark',
                '--input', json_path,
                '--output-dir', tmpdir
            ])
            
            assert result.exit_code == 0
            mock_load.assert_called_once_with(json_path)
            mock_create_report.assert_called()
    
    @patch('scripts.cli.analyze.benchmark_function')
    @patch('scripts.cli.analyze.save_benchmark_results')
    @patch('scripts.cli.analyze.create_benchmark_report')
    def test_benchmark_run_new(self, mock_report, mock_save, mock_benchmark):
        """Test running new benchmark."""
        runner = CliRunner()
        
        # Mock benchmark results
        mock_results = [
            Mock(spec=BenchmarkResult,
                 algorithm_name='woa',
                 instance_name='P-n16-k8',
                 fitness_values=[450.5],
                 gap_to_optimal=None)
        ]
        mock_benchmark.return_value = mock_results
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, [
                'benchmark',
                '--run-benchmark',
                '--algorithms', 'woa,sma',
                '--instances', 'P-n16-k8',
                '--runs', '2',
                '--output-dir', tmpdir
            ])
            
            assert result.exit_code == 0
            mock_benchmark.assert_called_once()
            mock_save.assert_called_once()
            mock_report.assert_called()
    
    def test_benchmark_no_input_error(self):
        """Test error when no input is provided."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['benchmark'])
        
        assert result.exit_code == 0  # Should exit gracefully
        assert 'Debe especificar una fuente de datos' in result.output
    
    def test_benchmark_invalid_file_format(self):
        """Test error with invalid file format."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid file
            invalid_path = os.path.join(tmpdir, 'invalid.txt')
            with open(invalid_path, 'w') as f:
                f.write('invalid data')
            
            result = runner.invoke(cli, [
                'benchmark',
                '--input', invalid_path
            ])
            
            assert result.exit_code == 0
            assert 'Formato de archivo no soportado' in result.output


class TestAnalyzeCSVCommand:
    """Test the analyze-csv command."""
    
    def create_test_csv(self, tmpdir):
        """Create test CSV data."""
        data = {
            'Algorithm': ['WOA'] * 5 + ['SMA'] * 5,
            'Instance': ['P-n16-k8'] * 10,
            'Run': list(range(1, 6)) * 2,
            'Best': [450.5, 452.3, 451.8, 453.2, 449.9,
                    448.9, 451.2, 450.3, 452.1, 449.5],
            'Mean': [455.2, 456.1, 454.8, 457.3, 453.9,
                    453.4, 454.8, 452.9, 455.6, 451.8],
            'Time': [1.23, 1.25, 1.22, 1.28, 1.24,
                    1.45, 1.48, 1.43, 1.51, 1.46]
        }
        df = pd.DataFrame(data)
        csv_path = os.path.join(tmpdir, 'test_results.csv')
        df.to_csv(csv_path, index=False)
        return csv_path
    
    @patch('matplotlib.pyplot.savefig')
    @patch('scripts.cli.analyze.logger')
    def test_analyze_csv_basic(self, mock_logger, mock_savefig):
        """Test basic CSV analysis."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = self.create_test_csv(tmpdir)
            output_dir = os.path.join(tmpdir, 'output')
            
            result = runner.invoke(cli, [
                'analyze-csv',
                csv_path,
                '--output-dir', output_dir
            ])
            
            assert result.exit_code == 0
            
            # Check that output directory was created
            assert os.path.exists(output_dir)
            
            # Check that HTML report was created
            html_path = os.path.join(output_dir, 'analysis_report.html')
            assert os.path.exists(html_path)
            
            # Verify HTML content
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            assert 'Análisis de Algoritmos Metaheurísticos' in html_content
            assert 'WOA' in html_content
            assert 'SMA' in html_content
    
    def test_analyze_csv_missing_file(self):
        """Test error with missing CSV file."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'analyze-csv',
            'nonexistent.csv'
        ])
        
        assert result.exit_code != 0


class TestStatsCommand:
    """Test the stats command for advanced statistical analysis."""
    
    @patch('scripts.core.analyze.run_advanced_stats')
    @patch('os.path.exists')
    def test_stats_basic(self, mock_exists, mock_run_stats):
        """Test basic stats command."""
        runner = CliRunner()
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock stats results
        mock_run_stats.return_value = {
            'friedman_p': 0.001,
            'mean_ranks': {'WOA': 1.5, 'SMA': 2.5},
            'critical_distance': 1.0,
            'report': 'report.html',
            'cd_diagram': 'cd_diagram.png'
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'results.csv')
            
            result = runner.invoke(cli, [
                'stats',
                '--csv', csv_path,
                '--out', tmpdir
            ])
            
            assert result.exit_code == 0
            mock_run_stats.assert_called_once_with(csv_path, tmpdir)
            
            # Check output contains expected information
            assert 'Statistical Analysis Summary' in result.output
            assert 'Global p-value: 0.001000' in result.output
            assert 'significant differences' in result.output
    
    def test_stats_missing_file(self):
        """Test error with missing CSV file."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'stats',
            '--csv', 'nonexistent.csv'
        ])
        
        assert result.exit_code == 0
        assert 'CSV file not found' in result.output
    
    @patch('scripts.core.analyze.run_advanced_stats')
    @patch('os.path.exists')
    def test_stats_no_significant_differences(self, mock_exists, mock_run_stats):
        """Test stats output when no significant differences."""
        runner = CliRunner()
        
        mock_exists.return_value = True
        mock_run_stats.return_value = {
            'friedman_p': 0.15,
            'mean_ranks': {'WOA': 1.5, 'SMA': 1.6},
            'critical_distance': 1.0,
            'report': 'report.html',
            'cd_diagram': 'cd_diagram.png'
        }
        
        result = runner.invoke(cli, [
            'stats',
            '--csv', 'test.csv'
        ])
        
        assert result.exit_code == 0
        assert 'No statistically significant differences' in result.output


class TestMassiveCommand:
    """Test the massive benchmark command."""
    
    @patch('scripts.core.analyze.run_massive_benchmark', create=True)
    def test_massive_basic(self, mock_run_massive):
        """Test basic massive benchmark execution."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'massive',
            '--runs', '1000',
            '--iterations', '100',
            '--population', '40',
            '--algorithm', 'woa',
            '--algorithm', 'sma',
            '--instances', 'P-n16-k8',
            '--parallel'
        ])
        
        assert result.exit_code == 0
        # Verificar que se llamó al mock
        mock_run_massive.assert_called_once()
    
    @patch('scripts.core.analyze.run_massive_benchmark', create=True)
    def test_massive_all_algorithms(self, mock_run_massive):
        """Test massive benchmark with all algorithms."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'massive',
            '--algorithm', 'all'
        ])
        
        assert result.exit_code == 0
        # Check that 'all' is passed
        call_args = mock_run_massive.call_args[0]
        assert ('all',) in call_args


class TestOptimizationFeature:
    """Test the optimization feature in benchmark command."""
    
    @patch('scripts.core.analyze.VRPProblem')
    @patch('scripts.core.analyze.VRPOperators')
    @patch('scripts.cli.analyze.create_benchmark_report')
    @patch('os.path.exists')
    def test_benchmark_with_optimization(self, mock_exists, mock_report, 
                                       mock_operators, mock_problem):
        """Test benchmark with local optimization."""
        runner = CliRunner()
        
        # Setup mocks
        mock_exists.return_value = True
        
        # Mock problem
        mock_vrp = Mock()
        mock_vrp.get_dimension.return_value = 10
        mock_vrp.decode_solution.return_value = ([[1, 2, 3]], 100.0, None)
        mock_vrp.distance_matrix = np.zeros((10, 10))
        mock_vrp.demands = [0] * 10
        mock_vrp.capacity = 100
        mock_problem.return_value = mock_vrp
        
        # Mock operators
        mock_operators.optimize_all_routes.return_value = [[1, 2, 3]]
        mock_operators.optimize_between_routes.return_value = [[1, 2, 3]]
        mock_operators.evaluate_solution.return_value = (95.0, True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            csv_path = os.path.join(tmpdir, 'results.csv')
            data = {
                'Algorithm': ['WOA'],
                'Instance': ['P-n16-k8'],
                'Run': [1],
                'Best Fitness': [100.0],
                'Mean Fitness': [105.0],
                'Execution Time (s)': [1.0],
                'Time Std': [0.1]
            }
            pd.DataFrame(data).to_csv(csv_path, index=False)
            
            result = runner.invoke(cli, [
                'benchmark',
                '--input', csv_path,
                '--optimize',
                '--output-dir', tmpdir
            ])
            
            assert result.exit_code == 0
            
            # Verify optimization was called
            mock_operators.optimize_all_routes.assert_called()
            mock_operators.optimize_between_routes.assert_called()
            mock_operators.evaluate_solution.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])