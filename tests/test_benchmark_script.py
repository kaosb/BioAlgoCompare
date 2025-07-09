"""
Tests for the benchmark.py script.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess

# Import the script components
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.benchmark import BenchmarkRunner
try:
    from scripts.algorithms_v2 import ALGORITHMS
except ImportError:
    # Fallback for testing
    ALGORITHMS = {
        "woa": "woa", "sma": "sma", "gto": "gto", "mrfo": "mrfo",
        "egto": "egto", "aha": "aha", "ewa": "ewa", "fsa": "fsa",
        "apo": "apo", "gvoa": "gvoa", "opa": "opa", "rro": "rro",
        "smo": "smo", "hoa": "hoa", "fgo": "fgo", "sho": "sho",
        "foa": "foa", "hho": "hho"
    }


class TestBenchmarkRunner:
    """Test cases for BenchmarkRunner class."""
    
    def test_init(self):
        """Test BenchmarkRunner initialization."""
        runner = BenchmarkRunner()
        assert runner.result_base_dir == 'results'
        assert runner.results == []
        
        runner = BenchmarkRunner('custom_results')
        assert runner.result_base_dir == 'custom_results'
    
    def test_create_result_directory(self):
        """Test result directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = BenchmarkRunner(tmpdir)
            
            # Test with custom timestamp
            result_dir = runner.create_result_directory('20240101_120000')
            expected_path = os.path.join(tmpdir, 'benchmark_20240101_120000')
            assert result_dir == expected_path
            assert os.path.exists(result_dir)
            
            # Test with automatic timestamp
            result_dir2 = runner.create_result_directory()
            assert result_dir2.startswith(os.path.join(tmpdir, 'benchmark_'))
            assert os.path.exists(result_dir2)
    
    def test_validate_instances_valid(self):
        """Test validation of valid instances."""
        runner = BenchmarkRunner()
        
        # Mock file existence checks
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Test with .vrp extension
            instances = runner.validate_instances(['P-n16-k8.vrp'])
            assert instances == ['P-n16-k8']
            
            # Test without extension
            instances = runner.validate_instances(['P-n16-k8'])
            assert instances == ['P-n16-k8']
            
            # Test multiple instances
            instances = runner.validate_instances(['P-n16-k8', 'E-n22-k4'])
            assert instances == ['P-n16-k8', 'E-n22-k4']
    
    def test_validate_instances_invalid(self):
        """Test validation of invalid instances."""
        runner = BenchmarkRunner()
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            with pytest.raises(ValueError, match="Instancia no encontrada"):
                runner.validate_instances(['nonexistent'])
    
    def test_validate_instances_solomon(self):
        """Test validation of Solomon instances."""
        runner = BenchmarkRunner()
        
        with patch('pathlib.Path.exists') as mock_exists:
            # First call returns False (main dir), second returns True (Solomon dir)
            mock_exists.side_effect = [False, True]
            
            instances = runner.validate_instances(['RC101'])
            assert instances == ['RC101']
    
    def test_run_algorithm_success(self):
        """Test successful algorithm execution."""
        runner = BenchmarkRunner()
        
        # Mock subprocess.run
        mock_result = Mock()
        mock_result.stdout = "Algorithm completed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = runner.run_algorithm(
                'woa', 'P-n16-k8', 100, 30, 5, parallel=False
            )
            
            assert result['algorithm'] == 'woa'
            assert result['instance'] == 'P-n16-k8'
            assert result['status'] == 'success'
            assert result['stdout'] == "Algorithm completed"
            assert result['stderr'] == ""
            assert result['returncode'] == 0
            
            # Check command construction
            mock_run.assert_called_once()
            command = mock_run.call_args[0][0]
            assert 'scripts/core/run.py' in command
            assert '--algorithm' in command
            assert 'woa' in command
            assert '--instance' in command
            assert 'P-n16-k8' in command
            assert '--iterations' in command
            assert '100' in command
            assert '--population' in command
            assert '30' in command
            assert '--runs' in command
            assert '5' in command
            assert '--v2' in command
            assert '--parallel' not in command
    
    def test_run_algorithm_with_parallel(self):
        """Test algorithm execution with parallel flag."""
        runner = BenchmarkRunner()
        
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = runner.run_algorithm(
                'sma', 'E-n22-k4', 50, 20, 3, parallel=True
            )
            
            # Check that --parallel flag is included
            command = mock_run.call_args[0][0]
            assert '--parallel' in command
    
    def test_run_algorithm_error(self):
        """Test algorithm execution with error."""
        runner = BenchmarkRunner()
        
        # Mock subprocess.CalledProcessError
        error = subprocess.CalledProcessError(
            1, 'cmd', output='', stderr='Error occurred'
        )
        error.stdout = ''
        error.stderr = 'Error occurred'
        
        with patch('subprocess.run', side_effect=error):
            result = runner.run_algorithm(
                'gto', 'P-n16-k8', 100, 30, 5, parallel=False
            )
            
            assert result['algorithm'] == 'gto'
            assert result['instance'] == 'P-n16-k8'
            assert result['status'] == 'error'
            assert result['stderr'] == 'Error occurred'
            assert result['returncode'] == 1
            assert 'error' in result
    
    def test_run_benchmark(self):
        """Test complete benchmark execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = BenchmarkRunner(tmpdir)
            
            # Mock methods
            runner.validate_instances = Mock(return_value=['P-n16-k8', 'E-n22-k4'])
            runner.run_algorithm = Mock(return_value={
                'algorithm': 'test',
                'instance': 'test',
                'status': 'success',
                'stdout': '',
                'stderr': '',
                'returncode': 0
            })
            runner.save_summary = Mock()
            
            with patch('click.echo'):
                result_dir = runner.run_benchmark(
                    ['woa', 'sma'],
                    ['P-n16-k8', 'E-n22-k4'],
                    runs=5,
                    iterations=100,
                    population=30,
                    parallel=False
                )
            
            # Verify calls
            runner.validate_instances.assert_called_once_with(['P-n16-k8', 'E-n22-k4'])
            assert runner.run_algorithm.call_count == 4  # 2 algorithms × 2 instances
            runner.save_summary.assert_called_once()
            
            # Check results
            assert len(runner.results) == 4
            assert result_dir.startswith(tmpdir)
    
    def test_save_summary(self):
        """Test summary saving functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = BenchmarkRunner()
            
            # Add some results
            runner.results = [
                {
                    'algorithm': 'woa',
                    'instance': 'P-n16-k8',
                    'status': 'success',
                    'stdout': 'output',
                    'stderr': '',
                    'returncode': 0
                },
                {
                    'algorithm': 'sma',
                    'instance': 'P-n16-k8',
                    'status': 'error',
                    'stdout': '',
                    'stderr': 'error',
                    'returncode': 1,
                    'error': 'Test error'
                }
            ]
            
            runner.save_summary(
                tmpdir,
                ['woa', 'sma'],
                ['P-n16-k8'],
                runs=5,
                iterations=100,
                population=30
            )
            
            # Check JSON file
            json_path = os.path.join(tmpdir, 'summary_report.json')
            assert os.path.exists(json_path)
            
            with open(json_path, 'r') as f:
                summary = json.load(f)
            
            assert summary['parameters']['algorithms'] == ['woa', 'sma']
            assert summary['parameters']['instances'] == ['P-n16-k8']
            assert summary['parameters']['runs'] == 5
            assert summary['parameters']['iterations'] == 100
            assert summary['parameters']['population'] == 30
            assert summary['results']['total'] == 2
            assert summary['results']['successes'] == 1
            assert summary['results']['errors'] == 1
            assert len(summary['executions']) == 2
            
            # Check text report
            report_path = os.path.join(tmpdir, 'report.txt')
            assert os.path.exists(report_path)
            
            with open(report_path, 'r') as f:
                report = f.read()
            
            assert 'Benchmark Report' in report
            assert 'Algorithms: woa, sma' in report
            assert 'Instances: P-n16-k8' in report
            assert 'Successful: 1' in report
            assert 'Errors: 1' in report


class TestBenchmarkCLI:
    """Test CLI functionality of benchmark script."""
    
    @patch('scripts.benchmark.BenchmarkRunner')
    @patch('click.echo')
    def test_cli_basic(self, mock_echo, mock_runner_class):
        """Test basic CLI execution."""
        from scripts.benchmark import ejecutar_benchmark
        from click.testing import CliRunner
        
        # Setup mock
        mock_runner = Mock()
        mock_runner.results = [
            {'status': 'success'},
            {'status': 'success'},
            {'status': 'error'}
        ]
        mock_runner.run_benchmark.return_value = '/tmp/results'
        mock_runner_class.return_value = mock_runner
        
        runner = CliRunner()
        result = runner.invoke(ejecutar_benchmark, [
            '--algorithms', 'woa',
            '--algorithms', 'sma',
            '--instances', 'P-n16-k8',
            '--runs', '5',
            '--iterations', '100',
            '--population', '30',
            '--no-parallel'
        ])
        
        assert result.exit_code == 0
        mock_runner.run_benchmark.assert_called_once_with(
            ['woa', 'sma'],
            ['P-n16-k8'],
            5, 100, 30, False
        )
    
    @patch('scripts.benchmark.BenchmarkRunner')
    def test_cli_with_error(self, mock_runner_class):
        """Test CLI with error handling."""
        from scripts.benchmark import ejecutar_benchmark
        from click.testing import CliRunner
        
        # Setup mock to raise error
        mock_runner = Mock()
        mock_runner.run_benchmark.side_effect = ValueError("Test error")
        mock_runner_class.return_value = mock_runner
        
        runner = CliRunner()
        result = runner.invoke(ejecutar_benchmark, [
            '--algorithms', 'woa',
            '--instances', 'invalid'
        ])
        
        assert result.exit_code == 1
        assert "Error: Test error" in result.output
    
    def test_cli_algorithm_choices(self):
        """Test that CLI accepts valid algorithm choices."""
        from scripts.benchmark import ejecutar_benchmark
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Test invalid algorithm
        result = runner.invoke(ejecutar_benchmark, [
            '--algorithms', 'invalid_algo',
            '--instances', 'P-n16-k8'
        ])
        
        assert result.exit_code != 0
        assert 'Invalid value' in result.output
    
    @patch('scripts.benchmark.BenchmarkRunner')
    def test_cli_output_dir(self, mock_runner_class):
        """Test custom output directory."""
        from scripts.benchmark import ejecutar_benchmark
        from click.testing import CliRunner
        
        mock_runner = Mock()
        mock_runner.results = []
        mock_runner.run_benchmark.return_value = '/custom/results'
        mock_runner_class.return_value = mock_runner
        
        runner = CliRunner()
        result = runner.invoke(ejecutar_benchmark, [
            '--algorithms', 'woa',
            '--instances', 'P-n16-k8',
            '--output-dir', '/custom'
        ])
        
        assert result.exit_code == 0
        mock_runner_class.assert_called_with('/custom')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])