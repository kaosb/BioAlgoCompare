"""
Tests para el módulo evaluate_il.
Cubre todas las funciones de evaluación de HO con Imitation Learning.
"""
import pytest
import os
import sys
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.evaluate_il import (
    calculate_hypervolume,
    evaluate_algorithms,
    analyze_results,
    plot_comparison,
    main
)


class TestCalculateHypervolume:
    """Tests para la función calculate_hypervolume."""
    
    def test_calculate_hypervolume_empty_solutions(self):
        """Test con lista vacía de soluciones."""
        hv = calculate_hypervolume([])
        assert hv == 0.0
    
    def test_calculate_hypervolume_single_solution(self):
        """Test con una sola solución."""
        solutions = [(10.0, 20.0, 30.0)]
        reference_point = (15.0, 25.0, 35.0)
        
        hv = calculate_hypervolume(solutions, reference_point)
        # (15-10) * (25-20) * (35-30) = 5 * 5 * 5 = 125
        assert hv == 125.0
    
    def test_calculate_hypervolume_multiple_solutions(self):
        """Test con múltiples soluciones."""
        solutions = [
            (10.0, 20.0, 30.0),
            (12.0, 18.0, 32.0),
            (11.0, 22.0, 28.0)
        ]
        reference_point = (20.0, 30.0, 40.0)
        
        hv = calculate_hypervolume(solutions, reference_point)
        # Sol1: (20-10) * (30-20) * (40-30) = 10 * 10 * 10 = 1000
        # Sol2: (20-12) * (30-18) * (40-32) = 8 * 12 * 8 = 768
        # Sol3: (20-11) * (30-22) * (40-28) = 9 * 8 * 12 = 864
        # Total: 1000 + 768 + 864 = 2632
        assert hv == 2632.0
    
    def test_calculate_hypervolume_automatic_reference_point(self):
        """Test con punto de referencia automático."""
        solutions = [(10.0, 20.0, 30.0), (15.0, 25.0, 35.0)]
        
        hv = calculate_hypervolume(solutions)
        # Reference point should be (15*1.1, 25*1.1, 35*1.1) = (16.5, 27.5, 38.5)
        assert hv > 0
    
    def test_calculate_hypervolume_dominated_solution(self):
        """Test con solución dominada por el punto de referencia."""
        solutions = [(10.0, 20.0, 30.0)]
        reference_point = (5.0, 15.0, 25.0)  # Domina a la solución
        
        hv = calculate_hypervolume(solutions, reference_point)
        assert hv == 0.0


class TestEvaluateAlgorithms:
    """Tests para la función evaluate_algorithms."""
    
    @patch('utils.evaluate_il.VRPProblem')
    @patch('utils.evaluate_il.HO')
    @patch('os.path.exists')
    def test_evaluate_algorithms_existing_instance(self, mock_exists, mock_ho, mock_vrp):
        """Test evaluación con instancia existente."""
        # Configurar mocks
        mock_exists.return_value = True
        
        # Mock del problema
        mock_problem = Mock()
        mock_vrp.return_value = mock_problem
        
        # Mock del individuo mejor
        mock_best = Mock()
        mock_best.fitness.return_value = 100.0
        
        # Mock del algoritmo HO
        mock_ho_instance = Mock()
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_instance.get_convergence_curve.return_value = [150, 120, 100]
        mock_ho_instance.alpha_min = 0.1
        mock_ho_instance.alpha_max = 0.9
        mock_ho_instance.beta_min = 0.2
        mock_ho_instance.beta_max = 0.8
        mock_ho_instance.gamma_min = 0.3
        mock_ho_instance.gamma_max = 0.7
        mock_ho_instance.use_il = False
        
        mock_ho.return_value = mock_ho_instance
        
        # Ejecutar evaluación
        results = evaluate_algorithms("P-n16-k8", runs=2, il_model_path="model.pth")
        
        # Verificar estructura de resultados
        assert "standard" in results
        assert "il" in results
        
        # Verificar resultados estándar
        assert len(results["standard"]["fitness"]) == 2
        assert all(f == 100.0 for f in results["standard"]["fitness"])
        assert len(results["standard"]["convergence_curves"]) == 2
        assert len(results["standard"]["execution_times"]) == 2
        assert len(results["standard"]["final_params"]) == 2
        
        # Verificar resultados IL
        assert len(results["il"]["fitness"]) == 2
        assert len(results["il"]["convergence_curves"]) == 2
        assert len(results["il"]["execution_times"]) == 2
        assert len(results["il"]["final_params"]) == 2
    
    @patch('utils.evaluate_il.VRPProblem')
    @patch('utils.evaluate_il.HO')
    @patch('os.path.exists')
    @patch('utils.evaluate_il.np.random.uniform')
    @patch('utils.evaluate_il.np.random.randint')
    def test_evaluate_algorithms_synthetic_instance(self, mock_randint, mock_uniform, 
                                                   mock_exists, mock_ho, mock_vrp):
        """Test evaluación con instancia sintética."""
        # Configurar mocks
        mock_exists.return_value = False
        # Necesitamos 40 valores para 20 clientes (x,y para cada uno)
        mock_uniform.side_effect = [i*2.5 - 50 for i in range(40)]  # x, y para 20 clientes
        mock_randint.side_effect = [10 + i for i in range(20)]  # demandas
        
        # Mock del problema
        mock_problem = Mock()
        mock_problem.nodes = []
        mock_problem.demands = []
        mock_vrp.return_value = mock_problem
        
        # Mock del individuo mejor
        mock_best = Mock()
        mock_best.fitness.return_value = 80.0
        
        # Mock del algoritmo HO
        mock_ho_instance = Mock()
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_instance.get_convergence_curve.return_value = [100, 90, 80]
        mock_ho_instance.alpha_min = 0.1
        mock_ho_instance.alpha_max = 0.9
        mock_ho_instance.beta_min = 0.2
        mock_ho_instance.beta_max = 0.8
        mock_ho_instance.gamma_min = 0.3
        mock_ho_instance.gamma_max = 0.7
        mock_ho_instance.use_il = True
        
        mock_ho.return_value = mock_ho_instance
        
        # Ejecutar evaluación
        results = evaluate_algorithms("synthetic-instance", runs=1)
        
        # Verificar que se creó la instancia sintética
        assert mock_problem.capacity == 100
        assert mock_problem.dimension == 21  # 20 clientes + 1 depósito
        
        # Verificar resultados
        assert len(results["standard"]["fitness"]) == 1
        assert len(results["il"]["fitness"]) == 1


class TestAnalyzeResults:
    """Tests para la función analyze_results."""
    
    def test_analyze_results_basic(self):
        """Test análisis básico de resultados."""
        results = {
            "standard": {
                "fitness": [120.0, 110.0, 115.0],
                "execution_times": [1.0, 1.1, 1.05],
                "convergence_curves": [[150, 130, 120], [160, 125, 110], [155, 120, 115]],
                "final_params": [(0.5, 0.5, 0.5)] * 3
            },
            "il": {
                "fitness": [100.0, 95.0, 98.0],
                "execution_times": [1.2, 1.3, 1.25],
                "convergence_curves": [[140, 110, 100], [150, 105, 95], [145, 108, 98]],
                "final_params": [(0.5, 0.5, 0.65)] * 3
            }
        }
        
        analysis = analyze_results(results, "test-instance")
        
        # Verificar análisis de fitness
        assert "fitness" in analysis
        assert analysis["fitness"]["standard_mean"] == 115.0
        assert analysis["fitness"]["standard_best"] == 110.0
        assert analysis["fitness"]["il_mean"] == pytest.approx(97.67, rel=0.01)
        assert analysis["fitness"]["il_best"] == 95.0
        assert analysis["fitness"]["improvement_mean"] > 0
        assert analysis["fitness"]["improvement_best"] > 0
        
        # Verificar análisis de tiempo
        assert "time" in analysis
        assert analysis["time"]["standard_mean"] == pytest.approx(1.05, rel=0.01)
        assert analysis["time"]["il_mean"] == pytest.approx(1.25, rel=0.01)
        assert analysis["time"]["overhead"] > 0
        
        # Verificar análisis de convergencia
        assert "convergence" in analysis
        assert "auc_standard" in analysis["convergence"]
        assert "auc_il" in analysis["convergence"]
        assert "auc_improvement" in analysis["convergence"]
        
        # Verificar análisis estadístico
        assert "statistical" in analysis
        assert "mann_whitney_statistic" in analysis["statistical"]
        assert "p_value" in analysis["statistical"]
        assert "significant" in analysis["statistical"]
    
    @patch('scipy.stats.mannwhitneyu')
    def test_analyze_results_statistical_significance(self, mock_mwu):
        """Test análisis con significancia estadística."""
        # Configurar mock para test significativo
        mock_mwu.return_value = (10.0, 0.03)
        
        results = {
            "standard": {
                "fitness": [120.0, 110.0, 115.0, 125.0, 118.0],
                "execution_times": [1.0] * 5,
                "convergence_curves": [[100]] * 5,
                "final_params": [(0.5, 0.5, 0.5)] * 5
            },
            "il": {
                "fitness": [90.0, 85.0, 88.0, 92.0, 87.0],
                "execution_times": [1.2] * 5,
                "convergence_curves": [[80]] * 5,
                "final_params": [(0.5, 0.5, 0.65)] * 5
            }
        }
        
        analysis = analyze_results(results, "test-instance")
        
        # Verificar que es significativo (p < 0.05)
        assert analysis["statistical"]["p_value"] == 0.03
        assert analysis["statistical"]["significant"] is True


class TestPlotComparison:
    """Tests para la función plot_comparison."""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.tight_layout')
    @patch('matplotlib.pyplot.suptitle')
    @patch('matplotlib.pyplot.subplot')
    @patch('matplotlib.pyplot.subplots')
    @patch('matplotlib.pyplot.fill_between')
    @patch('matplotlib.pyplot.plot')
    @patch('matplotlib.pyplot.legend')
    @patch('matplotlib.pyplot.grid')
    @patch('matplotlib.pyplot.title')
    @patch('matplotlib.pyplot.xlabel')
    @patch('matplotlib.pyplot.ylabel')
    @patch('matplotlib.pyplot.text')
    @patch('matplotlib.pyplot.gca')
    @patch('matplotlib.pyplot.boxplot')
    @patch('matplotlib.pyplot.figure')
    @patch('os.makedirs')
    def test_plot_comparison_creates_plots(self, mock_makedirs, mock_figure, mock_boxplot,
                                         mock_gca, mock_text, mock_ylabel, mock_xlabel,
                                         mock_title, mock_grid, mock_legend, mock_plot,
                                         mock_fill_between, mock_subplots, mock_subplot,
                                         mock_suptitle, mock_tight_layout, mock_close, mock_savefig):
        """Test que se crean todos los gráficos."""
        # Configurar mocks necesarios
        mock_ax = MagicMock()
        mock_gca.return_value = mock_ax
        mock_ax.transAxes = MagicMock()
        
        # Mock para subplots
        mock_axes = [MagicMock(), MagicMock(), MagicMock()]
        mock_fig = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_axes)
        
        results = {
            "standard": {
                "fitness": [120.0, 110.0, 115.0],
                "convergence_curves": [[150, 130, 120], [160, 125, 110], [155, 120, 115]],
                "final_params": [(0.5, 0.5, 0.5), (0.6, 0.4, 0.5), (0.55, 0.45, 0.5)]
            },
            "il": {
                "fitness": [100.0, 95.0, 98.0],
                "convergence_curves": [[140, 110, 100], [150, 105, 95], [145, 108, 98]],
                "final_params": [(0.5, 0.5, 0.65), (0.5, 0.5, 0.65), (0.5, 0.5, 0.65)]
            }
        }
        
        analysis = {
            "fitness": {
                "improvement_mean": 15.0
            }
        }
        
        output_dir = "test_output"
        instance_name = "test-instance"
        
        # Ejecutar
        plot_comparison(results, analysis, instance_name, output_dir)
        
        # Verificar que se creó el directorio
        mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)
        
        # Verificar que se crearon 3 figuras
        assert mock_figure.call_count == 3
        
        # Verificar que se guardaron 3 archivos
        assert mock_savefig.call_count == 3
        
        # Verificar nombres de archivos
        expected_files = [
            os.path.join(output_dir, f"fitness_comparison_{instance_name}.png"),
            os.path.join(output_dir, f"convergence_comparison_{instance_name}.png"),
            os.path.join(output_dir, f"parameters_distribution_{instance_name}.png")
        ]
        
        for expected_file in expected_files:
            assert any(expected_file in str(call) for call in mock_savefig.call_args_list)


class TestMain:
    """Tests para la función main."""
    
    @patch('utils.evaluate_il.argparse.ArgumentParser.parse_args')
    @patch('utils.evaluate_il.evaluate_algorithms')
    @patch('utils.evaluate_il.analyze_results')
    @patch('utils.evaluate_il.plot_comparison')
    @patch('os.path.exists')
    @patch('pandas.DataFrame.to_csv')
    def test_main_basic_execution(self, mock_to_csv, mock_exists, mock_plot, 
                                 mock_analyze, mock_evaluate, mock_parse_args):
        """Test ejecución básica del main."""
        # Configurar argumentos
        mock_args = Mock()
        mock_args.instances = "P-n16-k8,E-n22-k4"
        mock_args.runs = 10
        mock_args.model = "model.pth"
        mock_args.output_dir = "results/test"
        mock_parse_args.return_value = mock_args
        
        # Configurar exists para modelo
        mock_exists.return_value = True
        
        # Configurar resultados de evaluación
        mock_results = {
            "standard": {"fitness": [100.0]},
            "il": {"fitness": [90.0]}
        }
        mock_evaluate.return_value = mock_results
        
        # Configurar análisis
        mock_analysis = {
            "fitness": {
                "standard_mean": 100.0,
                "standard_std": 5.0,
                "il_mean": 90.0,
                "il_std": 4.0,
                "improvement_mean": 10.0,
                "standard_best": 95.0,
                "il_best": 85.0,
                "improvement_best": 11.0
            },
            "statistical": {
                "p_value": 0.03,
                "significant": True
            },
            "time": {
                "overhead": 5.0
            },
            "convergence": {
                "auc_improvement": 8.0
            }
        }
        mock_analyze.return_value = mock_analysis
        
        # Ejecutar main
        main()
        
        # Verificar llamadas
        assert mock_evaluate.call_count == 2  # Una por cada instancia
        assert mock_analyze.call_count == 2
        assert mock_plot.call_count == 2
        
        # Verificar que se guardó el resumen
        mock_to_csv.assert_called_once()
    
    @patch('utils.evaluate_il.argparse.ArgumentParser.parse_args')
    @patch('os.path.exists')
    @patch('utils.evaluate_il.evaluate_algorithms')
    @patch('utils.evaluate_il.analyze_results')
    @patch('utils.evaluate_il.plot_comparison')
    @patch('pandas.DataFrame.to_csv')
    def test_main_model_not_found(self, mock_to_csv, mock_plot, mock_analyze, 
                                 mock_evaluate, mock_exists, mock_parse_args):
        """Test cuando el modelo no existe."""
        # Configurar argumentos
        mock_args = Mock()
        mock_args.instances = "P-n16-k8"
        mock_args.runs = 5
        mock_args.model = "nonexistent.pth"
        mock_args.output_dir = "results/test"
        mock_parse_args.return_value = mock_args
        
        # Configurar exists para que el modelo no exista
        mock_exists.return_value = False
        
        # Configurar resultados mock
        mock_evaluate.return_value = {"standard": {}, "il": {}}
        mock_analyze.return_value = {
            "fitness": {
                "standard_mean": 100, "standard_std": 5, "standard_best": 95,
                "il_mean": 90, "il_std": 4, "il_best": 85,
                "improvement_mean": 10, "improvement_best": 11
            },
            "statistical": {"p_value": 0.05, "significant": False},
            "time": {"overhead": 0},
            "convergence": {"auc_improvement": 0}
        }
        
        # Ejecutar main (no debe fallar)
        main()
        
        # Verificar que se ejecutó aunque el modelo no exista
        assert mock_evaluate.called
        assert mock_analyze.called
    
    @patch('utils.evaluate_il.argparse.ArgumentParser.parse_args')
    @patch('utils.evaluate_il.evaluate_algorithms')
    @patch('utils.evaluate_il.analyze_results')
    @patch('utils.evaluate_il.plot_comparison')
    @patch('os.path.exists')
    @patch('pandas.DataFrame.to_csv')
    def test_main_single_instance(self, mock_to_csv, mock_exists, mock_plot,
                                 mock_analyze, mock_evaluate, mock_parse_args):
        """Test con una sola instancia."""
        # Configurar para una sola instancia
        mock_args = Mock()
        mock_args.instances = "P-n16-k8"
        mock_args.runs = 20
        mock_args.model = "model.pth"
        mock_args.output_dir = "results/single"
        mock_parse_args.return_value = mock_args
        
        mock_exists.return_value = True
        
        # Configurar mocks
        mock_evaluate.return_value = {"standard": {}, "il": {}}
        mock_analyze.return_value = {
            "fitness": {
                "standard_mean": 100, "standard_std": 5, "standard_best": 95,
                "il_mean": 90, "il_std": 4, "il_best": 85,
                "improvement_mean": 10, "improvement_best": 11
            },
            "statistical": {"p_value": 0.02, "significant": True},
            "time": {"overhead": 3},
            "convergence": {"auc_improvement": 7}
        }
        
        # Ejecutar
        main()
        
        # Con una sola instancia, no debe imprimir resumen global
        # Solo verificar que se ejecutó correctamente
        assert mock_evaluate.call_count == 1
        assert mock_analyze.call_count == 1
        assert mock_plot.call_count == 1


class TestIntegration:
    """Tests de integración para el módulo completo."""
    
    @patch('utils.evaluate_il.HO')
    @patch('utils.evaluate_il.VRPProblem')
    @patch('os.path.exists')
    def test_full_evaluation_pipeline(self, mock_exists, mock_vrp, mock_ho):
        """Test del pipeline completo de evaluación."""
        # Configurar mocks
        mock_exists.return_value = True
        
        # Mock del problema
        mock_problem = Mock()
        mock_problem.distance_matrix = np.array([[0, 10], [10, 0]])
        mock_vrp.return_value = mock_problem
        
        # Mock del individuo
        mock_best = Mock()
        mock_best.fitness.return_value = 100.0
        
        # Mock del algoritmo
        mock_ho_instance = Mock()
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_instance.get_convergence_curve.return_value = [120, 110, 100]
        mock_ho_instance.alpha_min = 0.1
        mock_ho_instance.alpha_max = 0.9
        mock_ho_instance.beta_min = 0.2
        mock_ho_instance.beta_max = 0.8
        mock_ho_instance.gamma_min = 0.3
        mock_ho_instance.gamma_max = 0.7
        mock_ho_instance.use_il = False
        
        mock_ho.return_value = mock_ho_instance
        
        # Ejecutar evaluación
        results = evaluate_algorithms("test-instance", runs=3)
        
        # Analizar resultados
        analysis = analyze_results(results, "test-instance")
        
        # Verificar que el pipeline completo funciona
        assert analysis["fitness"]["standard_mean"] == 100.0
        assert analysis["fitness"]["il_mean"] == 100.0
        assert "p_value" in analysis["statistical"]
        assert "auc_improvement" in analysis["convergence"]