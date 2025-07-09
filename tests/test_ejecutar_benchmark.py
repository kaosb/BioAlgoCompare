"""
Tests para el script ejecutar_benchmark_v2.py.
Incluye pruebas unitarias para BenchmarkRunner y pruebas de integración.
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.ejecutar_benchmark_v2 import BenchmarkRunner


class TestBenchmarkRunner:
    """Test suite para la clase BenchmarkRunner."""
    
    def setup_method(self):
        """Setup para cada test."""
        # Crear directorio temporal para pruebas
        self.temp_dir = tempfile.mkdtemp()
        self.runner = BenchmarkRunner(self.temp_dir)
        
    def teardown_method(self):
        """Cleanup después de cada test."""
        # Limpiar directorio temporal
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test de inicialización del runner."""
        assert self.runner.result_base_dir == self.temp_dir
        assert self.runner.results == []
    
    def test_create_result_directory_default_timestamp(self):
        """Test creación de directorio con timestamp automático."""
        # Mock datetime para timestamp predecible
        with patch('scripts.ejecutar_benchmark_v2.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20231215_120000'
            
            result_dir = self.runner.create_result_directory()
            
            expected_dir = os.path.join(self.temp_dir, 'benchmark_20231215_120000')
            assert result_dir == expected_dir
            assert os.path.exists(result_dir)
    
    def test_create_result_directory_custom_timestamp(self):
        """Test creación de directorio con timestamp personalizado."""
        custom_timestamp = '20231215_150000'
        result_dir = self.runner.create_result_directory(custom_timestamp)
        
        expected_dir = os.path.join(self.temp_dir, f'benchmark_{custom_timestamp}')
        assert result_dir == expected_dir
        assert os.path.exists(result_dir)
    
    def test_validate_instances_valid(self):
        """Test validación de instancias válidas."""
        # Crear estructura de directorios de prueba
        data_dir = Path('data/vrp')
        os.makedirs(data_dir, exist_ok=True)
        
        # Crear archivos de instancia ficticios
        test_instances = ['test1.vrp', 'test2.vrp']
        for instance in test_instances:
            (data_dir / instance).touch()
        
        try:
            # Test con extensión .vrp
            valid = self.runner.validate_instances(['test1', 'test2'])
            assert valid == ['test1', 'test2']
            
            # Test sin extensión
            valid = self.runner.validate_instances(['test1.vrp', 'test2.vrp'])
            assert valid == ['test1', 'test2']
        finally:
            # Limpiar archivos de prueba
            for instance in test_instances:
                (data_dir / instance).unlink(missing_ok=True)
    
    def test_validate_instances_solomon(self):
        """Test validación de instancias Solomon."""
        # Verificar si ya existe Solomon con datos reales
        solomon_dir = Path('data/vrp/Solomon')
        
        if solomon_dir.exists() and (solomon_dir / 'R101.vrp').exists():
            # Usar instancia real existente
            valid = self.runner.validate_instances(['R101'])
            assert valid == ['R101']
        else:
            # Crear estructura temporal
            os.makedirs(solomon_dir, exist_ok=True)
            created_file = False
            
            try:
                if not (solomon_dir / 'R101.vrp').exists():
                    (solomon_dir / 'R101.vrp').touch()
                    created_file = True
                
                valid = self.runner.validate_instances(['R101'])
                assert valid == ['R101']
            finally:
                # Solo limpiar si creamos el archivo
                if created_file:
                    (solomon_dir / 'R101.vrp').unlink(missing_ok=True)
    
    def test_validate_instances_invalid(self):
        """Test validación con instancia no existente."""
        with pytest.raises(ValueError, match="Instancia no encontrada: nonexistent"):
            self.runner.validate_instances(['nonexistent'])
    
    @patch('subprocess.run')
    def test_run_algorithm_success(self, mock_run):
        """Test ejecución exitosa de algoritmo."""
        # Configurar mock
        mock_result = MagicMock()
        mock_result.stdout = "Algorithm output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Ejecutar
        result = self.runner.run_algorithm(
            algorithm="hho",
            instance="test",
            iterations=10,
            population=20,
            runs=5,
            parallel=True
        )
        
        # Verificar resultado
        assert result["algorithm"] == "hho"
        assert result["instance"] == "test"
        assert result["status"] == "success"
        assert result["stdout"] == "Algorithm output"
        assert result["returncode"] == 0
        
        # Verificar comando llamado
        expected_command = [
            sys.executable,
            "scripts/run.py",
            "--algorithm", "hho",
            "--instance", "test",
            "--iterations", "10",
            "--population", "20",
            "--runs", "5",
            "--parallel"
        ]
        mock_run.assert_called_once_with(
            expected_command,
            capture_output=True,
            text=True,
            check=True
        )
    
    @patch('subprocess.run')
    def test_run_algorithm_failure(self, mock_run):
        """Test manejo de error en ejecución de algoritmo."""
        # Configurar mock para fallar
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(
            1, 
            "cmd",
            output="",
            stderr="Error message"
        )
        
        # Ejecutar
        result = self.runner.run_algorithm(
            algorithm="hho",
            instance="test",
            iterations=10,
            population=20,
            runs=5,
            parallel=False
        )
        
        # Verificar resultado
        assert result["algorithm"] == "hho"
        assert result["instance"] == "test"
        assert result["status"] == "error"
        assert result["returncode"] == 1
        assert "returned non-zero exit status" in result["error"] or "CalledProcessError" in result["error"]
    
    @patch.object(BenchmarkRunner, 'validate_instances')
    @patch.object(BenchmarkRunner, 'run_algorithm')
    @patch.object(BenchmarkRunner, 'save_summary')
    def test_run_benchmark(self, mock_save, mock_run_algo, mock_validate):
        """Test ejecución completa de benchmark."""
        # Configurar mocks
        mock_validate.return_value = ['test1', 'test2']
        mock_run_algo.return_value = {
            "status": "success",
            "algorithm": "hho",
            "instance": "test1",
            "stdout": "output",
            "stderr": "",
            "returncode": 0
        }
        
        # Ejecutar benchmark
        algorithms = ['hho', 'foa']
        instances = ['test1', 'test2']
        
        result_dir = self.runner.run_benchmark(
            algorithms=algorithms,
            instances=instances,
            runs=5,
            iterations=10,
            population=20,
            parallel=True
        )
        
        # Verificar llamadas
        mock_validate.assert_called_once_with(instances)
        
        # Verificar que se ejecutó para cada combinación
        assert mock_run_algo.call_count == 4  # 2 algorithms x 2 instances
        
        # Verificar parámetros de llamadas
        # El orden real es: para cada instancia, ejecutar todos los algoritmos
        expected_calls = [
            call('hho', 'test1', 10, 20, 5, True),
            call('foa', 'test1', 10, 20, 5, True),
            call('hho', 'test2', 10, 20, 5, True),
            call('foa', 'test2', 10, 20, 5, True),
        ]
        mock_run_algo.assert_has_calls(expected_calls, any_order=False)
        
        # Verificar que se guardó el resumen
        mock_save.assert_called_once()
        
        # Verificar que se creó el directorio
        assert os.path.exists(result_dir)
    
    def test_save_summary(self):
        """Test guardado de resumen de resultados."""
        # Configurar datos de prueba
        self.runner.results = [
            {"status": "success", "algorithm": "hho", "instance": "test1"},
            {"status": "success", "algorithm": "foa", "instance": "test1"},
            {"status": "error", "algorithm": "hho", "instance": "test2"},
        ]
        
        # Crear directorio de resultados
        result_dir = self.runner.create_result_directory()
        
        # Guardar resumen
        self.runner.save_summary(
            result_dir=result_dir,
            algorithms=["hho", "foa"],
            instances=["test1", "test2"],
            runs=5,
            iterations=10,
            population=20
        )
        
        # Verificar archivo JSON
        json_path = os.path.join(result_dir, 'summary_report.json')
        assert os.path.exists(json_path)
        
        with open(json_path, 'r') as f:
            summary = json.load(f)
        
        assert summary["parameters"]["algorithms"] == ["hho", "foa"]
        assert summary["parameters"]["instances"] == ["test1", "test2"]
        assert summary["parameters"]["runs"] == 5
        assert summary["results"]["total"] == 3
        assert summary["results"]["successes"] == 2
        assert summary["results"]["errors"] == 1
        
        # Verificar archivo de texto
        txt_path = os.path.join(result_dir, 'report.txt')
        assert os.path.exists(txt_path)
        
        with open(txt_path, 'r') as f:
            content = f.read()
        
        assert "Benchmark Report" in content
        assert "Algorithms: hho, foa" in content
        assert "Total executions: 3" in content
        assert "Successful: 2" in content
        assert "Errors: 1" in content


class TestBenchmarkCLI:
    """Tests para la interfaz de línea de comandos."""
    
    @patch('scripts.ejecutar_benchmark_v2.BenchmarkRunner')
    def test_cli_basic(self, mock_runner_class):
        """Test ejecución básica del CLI."""
        from click.testing import CliRunner
        from scripts.ejecutar_benchmark_v2 import ejecutar_benchmark
        
        # Configurar mock
        mock_runner = Mock()
        mock_runner.run_benchmark.return_value = "/path/to/results"
        mock_runner.results = [{"status": "success"}]
        mock_runner_class.return_value = mock_runner
        
        # Ejecutar comando
        runner = CliRunner()
        result = runner.invoke(ejecutar_benchmark, [
            '--algorithms', 'hho',
            '--algorithms', 'foa',
            '--instances', 'test1',
            '--instances', 'test2',
            '--runs', '5',
            '--iterations', '10',
            '--population', '20',
            '--no-parallel'
        ])
        
        # Verificar resultado
        assert result.exit_code == 0
        assert "Benchmark completado" in result.output
        
        # Verificar llamadas
        mock_runner_class.assert_called_once_with("results")
        mock_runner.run_benchmark.assert_called_once_with(
            ['hho', 'foa'],
            ['test1', 'test2'],
            5, 10, 20, False
        )
    
    @patch('scripts.ejecutar_benchmark_v2.BenchmarkRunner')
    def test_cli_with_output_dir(self, mock_runner_class):
        """Test CLI con directorio de salida personalizado."""
        from click.testing import CliRunner
        from scripts.ejecutar_benchmark_v2 import ejecutar_benchmark
        
        # Configurar mock
        mock_runner = Mock()
        mock_runner.run_benchmark.return_value = "/custom/path"
        mock_runner.results = []
        mock_runner_class.return_value = mock_runner
        
        # Ejecutar comando
        runner = CliRunner()
        result = runner.invoke(ejecutar_benchmark, [
            '--algorithms', 'hho',
            '--instances', 'test1',
            '--output-dir', '/custom/output'
        ])
        
        # Verificar
        assert result.exit_code == 0
        mock_runner_class.assert_called_once_with("/custom/output")
    
    @patch('scripts.ejecutar_benchmark_v2.BenchmarkRunner')
    def test_cli_error_handling(self, mock_runner_class):
        """Test manejo de errores en CLI."""
        from click.testing import CliRunner
        from scripts.ejecutar_benchmark_v2 import ejecutar_benchmark
        
        # Configurar mock para lanzar excepción
        mock_runner = Mock()
        mock_runner.run_benchmark.side_effect = ValueError("Test error")
        mock_runner_class.return_value = mock_runner
        
        # Ejecutar comando
        runner = CliRunner()
        result = runner.invoke(ejecutar_benchmark, [
            '--algorithms', 'hho',
            '--instances', 'invalid'
        ])
        
        # Verificar
        assert result.exit_code == 1
        assert "Error: Test error" in result.output


class TestIntegration:
    """Tests de integración para el sistema completo."""
    
    @pytest.mark.integration
    def test_full_benchmark_flow(self):
        """Test de flujo completo con datos reales mínimos."""
        # Este test requiere que existan las instancias y algoritmos
        # Solo ejecutar si el entorno está configurado correctamente
        
        data_dir = Path('data/vrp')
        if not data_dir.exists():
            pytest.skip("No data directory found")
        
        # Buscar una instancia pequeña para test rápido
        test_instance = None
        for instance in ['P-n16-k8.vrp', 'E-n22-k4.vrp']:
            if (data_dir / instance).exists():
                test_instance = instance.replace('.vrp', '')
                break
        
        if not test_instance:
            pytest.skip("No test instances found")
        
        # Crear runner temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = BenchmarkRunner(temp_dir)
            
            # Ejecutar benchmark mínimo
            result_dir = runner.run_benchmark(
                algorithms=['hho'],  # Solo un algoritmo
                instances=[test_instance],
                runs=2,  # Pocas ejecuciones
                iterations=5,  # Pocas iteraciones
                population=10,  # Población pequeña
                parallel=False
            )
            
            # Verificar resultados
            assert os.path.exists(result_dir)
            assert os.path.exists(os.path.join(result_dir, 'summary_report.json'))
            assert os.path.exists(os.path.join(result_dir, 'report.txt'))
            
            # Verificar contenido del resumen
            with open(os.path.join(result_dir, 'summary_report.json'), 'r') as f:
                summary = json.load(f)
            
            assert summary['results']['total'] == 1
            # No verificamos success/error porque depende del sistema


if __name__ == "__main__":
    pytest.main([__file__, "-v"])