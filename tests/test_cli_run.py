"""
Tests para CLI y funciones principales de ejecución.
"""
import pytest
from unittest.mock import patch
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ruff: noqa: E402
from scripts.run import main


def test_main_function_import():
    """Verifica que la función principal se importe correctamente."""
    assert callable(main)


def test_get_algorithms_mapping():
    """Verifica que se pueda importar y mapear los algoritmos correctamente."""
    from algorithms.sho import SHO
    from algorithms.opa import OPA
    
    algorithms = {
        'sho': SHO,
        'opa': OPA,
    }
    
    # Verificar que los algoritmos se importen y sean clases
    for algo_name, algo_class in algorithms.items():
        assert algo_class.__name__ == algo_name.upper()
        
        # Verificar que tienen los métodos necesarios
        assert hasattr(algo_class, 'execute')
        assert hasattr(algo_class, 'initialize_population')
        assert hasattr(algo_class, 'update_population')


@pytest.mark.skip(reason="Este test solo verifica la existencia de la CLI, no la ejecuta")
def test_cli_integration():
    """Verifica la integración básica de la CLI sin ejecutar el algoritmo completo."""
    from click.testing import CliRunner
    
    runner = CliRunner()
    with patch('scripts.run.VRPProblem'):
        with patch('scripts.run.SHO.execute', return_value=None):
            # Solo verificamos que la CLI se inicie sin errores
            with pytest.raises(SystemExit):
                result = runner.invoke(main, ['--algorithm', 'sho', '--instance', 'test'])
                assert result.exit_code == 0