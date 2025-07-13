"""
Tests para el módulo train_il.
Cubre el entrenamiento del modelo de Imitation Learning para HO.
"""
import pytest
import os
import sys
import numpy as np
import pandas as pd
import torch
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.train_il import plot_training_history, analyze_predictions, main


class TestPlotTrainingHistory:
    """Tests para la función plot_training_history."""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.tight_layout')
    @patch('matplotlib.pyplot.grid')
    @patch('matplotlib.pyplot.legend')
    @patch('matplotlib.pyplot.title')
    @patch('matplotlib.pyplot.ylabel')
    @patch('matplotlib.pyplot.xlabel')
    @patch('matplotlib.pyplot.plot')
    @patch('matplotlib.pyplot.figure')
    def test_plot_training_history_basic(self, mock_figure, mock_plot, mock_xlabel,
                                       mock_ylabel, mock_title, mock_legend, mock_grid,
                                       mock_tight_layout, mock_close, mock_savefig):
        """Test generación básica del gráfico de entrenamiento."""
        # Datos de ejemplo
        history = {
            "train_losses": [0.5, 0.4, 0.3, 0.25, 0.2],
            "val_losses": [0.6, 0.45, 0.35, 0.3, 0.28]
        }
        output_path = "test_plot.png"
        
        # Ejecutar
        plot_training_history(history, output_path)
        
        # Verificar llamadas
        mock_figure.assert_called_once_with(figsize=(10, 6))
        
        # Debe hacer 2 llamadas a plot (train y val)
        assert mock_plot.call_count == 2
        
        # Verificar primera llamada (train)
        call_args_1 = mock_plot.call_args_list[0]
        epochs_1 = call_args_1[0][0]
        losses_1 = call_args_1[0][1]
        assert list(epochs_1) == [1, 2, 3, 4, 5]
        assert losses_1 == history["train_losses"]
        assert call_args_1[0][2] == "b-"
        
        # Verificar segunda llamada (val)
        call_args_2 = mock_plot.call_args_list[1]
        losses_2 = call_args_2[0][1]
        assert losses_2 == history["val_losses"]
        assert call_args_2[0][2] == "r-"
        
        # Verificar etiquetas y configuración
        mock_xlabel.assert_called_once_with("Epoch")
        mock_ylabel.assert_called_once_with("MSE Loss")
        mock_title.assert_called_once_with("Training History - HO Imitation Learning")
        mock_legend.assert_called_once()
        mock_grid.assert_called_once_with(True, alpha=0.3)
        
        # Verificar guardado
        mock_savefig.assert_called_once_with(output_path)
        mock_close.assert_called_once()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.tight_layout')
    @patch('matplotlib.pyplot.grid')
    @patch('matplotlib.pyplot.legend')
    @patch('matplotlib.pyplot.title')
    @patch('matplotlib.pyplot.ylabel')
    @patch('matplotlib.pyplot.xlabel')
    @patch('matplotlib.pyplot.plot')
    @patch('matplotlib.pyplot.figure')
    def test_plot_training_history_empty(self, mock_figure, mock_plot, mock_xlabel,
                                       mock_ylabel, mock_title, mock_legend, mock_grid,
                                       mock_tight_layout, mock_close, mock_savefig):
        """Test con historial vacío."""
        history = {
            "train_losses": [],
            "val_losses": []
        }
        
        plot_training_history(history, "empty_plot.png")
        
        # Debe crear la figura
        mock_figure.assert_called_with(figsize=(10, 6))
        # Debe guardar aunque esté vacío
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()


class TestAnalyzePredictions:
    """Tests para la función analyze_predictions."""
    
    @pytest.fixture
    def mock_model(self):
        """Mock del modelo HOImitationLearning."""
        model = Mock()
        # Predicciones con pequeño error
        model.predict.side_effect = lambda state: (
            state.get("alpha", 0.5) + 0.01,
            state.get("beta", 0.5) + 0.02,
            state.get("gamma", 0.65) - 0.01
        )
        return model
    
    def test_analyze_predictions_basic(self, mock_model):
        """Test análisis básico de predicciones."""
        # Datos de prueba
        test_data = pd.DataFrame({
            "iteration_progress": [0.3, 0.5, 0.7],
            "fitness_diversity": [0.5, 0.4, 0.3],
            "alpha": [0.4, 0.5, 0.6],
            "beta": [0.5, 0.5, 0.5],
            "gamma": [0.6, 0.65, 0.7]
        })
        
        # Ejecutar análisis
        errors = analyze_predictions(mock_model, test_data)
        
        # Verificar estructura de errores
        assert "alpha" in errors
        assert "beta" in errors
        assert "gamma" in errors
        
        # Verificar que se calcularon errores para cada fila
        assert len(errors["alpha"]) == 3
        assert len(errors["beta"]) == 3
        assert len(errors["gamma"]) == 3
        
        # Verificar que los errores son positivos (valor absoluto)
        for param in ["alpha", "beta", "gamma"]:
            assert all(e >= 0 for e in errors[param])
        
        # Verificar que se llamó predict para cada fila
        assert mock_model.predict.call_count == 3
    
    def test_analyze_predictions_perfect_model(self):
        """Test con modelo perfecto (sin error)."""
        # Mock de modelo perfecto
        model = Mock()
        model.predict.side_effect = lambda state: (
            state.get("alpha", 0.5),
            state.get("beta", 0.5),
            state.get("gamma", 0.65)
        )
        
        # Datos donde el modelo predice perfectamente
        test_data = pd.DataFrame({
            "feature1": [0.1],
            "alpha": [0.5],
            "beta": [0.5],
            "gamma": [0.65]
        })
        
        errors = analyze_predictions(model, test_data)
        
        # Todos los errores deben ser 0
        assert errors["alpha"][0] == 0.0
        assert errors["beta"][0] == 0.0
        assert errors["gamma"][0] == 0.0
    
    def test_analyze_predictions_excludes_target_columns(self, mock_model):
        """Test que excluye columnas objetivo del estado."""
        test_data = pd.DataFrame({
            "feature1": [0.1],
            "feature2": [0.2],
            "alpha": [0.5],
            "beta": [0.5],
            "gamma": [0.65]
        })
        
        analyze_predictions(mock_model, test_data)
        
        # Verificar que el estado pasado no incluye alpha, beta, gamma
        call_args = mock_model.predict.call_args[0][0]
        assert "alpha" not in call_args
        assert "beta" not in call_args
        assert "gamma" not in call_args
        assert "feature1" in call_args
        assert "feature2" in call_args


class TestMain:
    """Tests para la función main."""
    
    @patch('utils.train_il.argparse.ArgumentParser.parse_args')
    @patch('os.path.exists')
    @patch('builtins.print')  # Mock print para evitar output
    def test_main_dataset_not_found(self, mock_print, mock_exists, mock_parse_args):
        """Test cuando el dataset no existe."""
        # Configurar argumentos
        mock_args = Mock()
        mock_args.dataset = "nonexistent.csv"
        mock_args.epochs = 10
        mock_args.batch_size = 32
        mock_args.val_split = 0.2
        mock_args.seed = 42
        mock_args.model_output = "model.pth"
        mock_parse_args.return_value = mock_args
        
        # Dataset no existe
        mock_exists.return_value = False
        
        # Ejecutar main (debe retornar sin error)
        result = main()
        
        # Verificar que se verificó la existencia del dataset
        # (puede haber otras llamadas a exists por las librerías)
        assert any(call[0][0] == "nonexistent.csv" for call in mock_exists.call_args_list)
        
        # Verificar que se imprimió el mensaje de error
        mock_print.assert_any_call("\nError: No se encontró el dataset nonexistent.csv")
        
        # Verificar que retornó None (terminó temprano)
        assert result is None
    
    @patch('utils.train_il.argparse.ArgumentParser.parse_args')
    @patch('utils.train_il.HOImitationLearning')
    @patch('utils.train_il.plot_training_history')
    @patch('utils.train_il.analyze_predictions')
    @patch('pandas.read_csv')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('torch.cuda.is_available')
    def test_main_full_execution(self, mock_cuda, mock_exists, mock_makedirs,
                                mock_read_csv, mock_analyze, mock_plot,
                                mock_il_class, mock_parse_args):
        """Test ejecución completa del main."""
        # Configurar argumentos
        mock_args = Mock()
        mock_args.dataset = "demos.csv"
        mock_args.epochs = 50
        mock_args.batch_size = 16
        mock_args.val_split = 0.2
        mock_args.seed = 42
        mock_args.model_output = "test_model.pth"
        mock_parse_args.return_value = mock_args
        
        # Configurar mocks
        mock_cuda.return_value = False  # CPU
        mock_exists.return_value = True  # Dataset existe
        
        # Mock del modelo
        mock_model = Mock()
        mock_model.train.return_value = {
            "train_losses": [0.5, 0.4, 0.3],
            "val_losses": [0.6, 0.5, 0.4]
        }
        mock_model.predict.return_value = (0.5, 0.5, 0.65)
        mock_model.save = Mock()
        mock_il_class.return_value = mock_model
        
        # Mock de los datos
        mock_df = pd.DataFrame({
            "feature1": list(range(100)),
            "alpha": [0.5] * 100,
            "beta": [0.5] * 100,
            "gamma": [0.65] * 100
        })
        mock_read_csv.return_value = mock_df
        
        # Ejecutar
        main()
        
        # Verificar creación del modelo
        mock_il_class.assert_called_once_with(input_dim=64, device="cpu")
        
        # Verificar entrenamiento
        mock_model.train.assert_called_once_with(
            demos_csv="demos.csv",
            epochs=50,
            batch_size=16,
            validation_split=0.2,
            seed=42
        )
        
        # Verificar guardado del modelo
        mock_makedirs.assert_called_with("models", exist_ok=True)
        mock_model.save.assert_called_once_with("models/test_model.pth")
        
        # Verificar generación de gráfico
        mock_plot.assert_called_once()
        plot_args = mock_plot.call_args[0]
        assert plot_args[1] == "results/ho_il_training_history.png"
        
        # Verificar análisis
        mock_analyze.assert_called_once()
        analyze_args = mock_analyze.call_args[0]
        assert analyze_args[0] == mock_model
        assert len(analyze_args[1]) == 20  # 20% de 100 filas
        
        # Verificar predicción de ejemplo
        mock_model.predict.assert_called()
        last_predict_call = mock_model.predict.call_args[0][0]
        assert "n_customers" in last_predict_call
        assert last_predict_call["n_customers"] == 50
    
    @patch('utils.train_il.argparse.ArgumentParser.parse_args')
    @patch('utils.train_il.HOImitationLearning')
    @patch('utils.train_il.plot_training_history')
    @patch('utils.train_il.analyze_predictions')
    @patch('pandas.read_csv')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('torch.cuda.is_available')
    def test_main_with_cuda(self, mock_cuda, mock_exists, mock_makedirs,
                           mock_read_csv, mock_analyze, mock_plot,
                           mock_il_class, mock_parse_args):
        """Test ejecución con CUDA disponible."""
        # Configurar para CUDA
        mock_cuda.return_value = True
        
        # Configurar argumentos mínimos
        mock_args = Mock()
        mock_args.dataset = "demos.csv"
        mock_args.epochs = 10
        mock_args.batch_size = 32
        mock_args.val_split = 0.2
        mock_args.seed = 42
        mock_args.model_output = "model.pth"
        mock_parse_args.return_value = mock_args
        
        # Configurar otros mocks
        mock_exists.return_value = True
        mock_model = Mock()
        mock_model.train.return_value = {"train_losses": [], "val_losses": []}
        mock_model.predict.return_value = (0.5, 0.5, 0.65)
        mock_il_class.return_value = mock_model
        
        mock_df = pd.DataFrame({
            "feature1": [1, 2, 3],
            "alpha": [0.5, 0.5, 0.5],
            "beta": [0.5, 0.5, 0.5],
            "gamma": [0.65, 0.65, 0.65]
        })
        mock_read_csv.return_value = mock_df
        
        # Ejecutar
        main()
        
        # Verificar que se usó CUDA
        mock_il_class.assert_called_once_with(input_dim=64, device="cuda")
    
    @patch('utils.train_il.argparse.ArgumentParser.parse_args')
    @patch('utils.train_il.HOImitationLearning')
    @patch('utils.train_il.plot_training_history')
    @patch('utils.train_il.analyze_predictions')
    @patch('pandas.read_csv')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('torch.cuda.is_available')
    def test_main_small_dataset(self, mock_cuda, mock_exists, mock_makedirs,
                               mock_read_csv, mock_analyze, mock_plot,
                               mock_il_class, mock_parse_args):
        """Test con dataset pequeño."""
        # Configurar argumentos
        mock_args = Mock()
        mock_args.dataset = "small_demos.csv"
        mock_args.epochs = 5
        mock_args.batch_size = 4
        mock_args.val_split = 0.5  # 50% validación
        mock_args.seed = 123
        mock_args.model_output = "small_model.pth"
        mock_parse_args.return_value = mock_args
        
        # Configurar mocks
        mock_cuda.return_value = False
        mock_exists.return_value = True
        
        mock_model = Mock()
        mock_model.train.return_value = {"train_losses": [0.5], "val_losses": [0.6]}
        mock_model.predict.return_value = (0.4, 0.5, 0.6)
        mock_il_class.return_value = mock_model
        
        # Dataset pequeño
        mock_df = pd.DataFrame({
            "feature1": [1, 2, 3, 4],
            "alpha": [0.4, 0.5, 0.6, 0.5],
            "beta": [0.5, 0.5, 0.5, 0.5],
            "gamma": [0.6, 0.65, 0.7, 0.65]
        })
        mock_read_csv.return_value = mock_df
        
        # Ejecutar
        main()
        
        # Verificar que el análisis usa 50% de los datos (2 filas)
        mock_analyze.assert_called_once()
        test_data = mock_analyze.call_args[0][1]
        assert len(test_data) == 2


class TestIntegration:
    """Tests de integración."""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.tight_layout')
    @patch('matplotlib.pyplot.grid')
    @patch('matplotlib.pyplot.legend')
    @patch('matplotlib.pyplot.title')
    @patch('matplotlib.pyplot.ylabel')
    @patch('matplotlib.pyplot.xlabel')
    @patch('matplotlib.pyplot.plot')
    @patch('matplotlib.pyplot.figure')
    def test_plot_and_history_integration(self, mock_figure, mock_plot, mock_xlabel,
                                        mock_ylabel, mock_title, mock_legend, mock_grid,
                                        mock_tight_layout, mock_close, mock_savefig):
        """Test integración entre historial y generación de gráfico."""
        # Simular un historial de entrenamiento típico
        history = {
            "train_losses": [1.0, 0.8, 0.6, 0.5, 0.45, 0.4, 0.38, 0.35, 0.33, 0.32],
            "val_losses": [1.1, 0.85, 0.65, 0.55, 0.5, 0.48, 0.47, 0.46, 0.45, 0.45]
        }
        
        # Generar gráfico
        output_path = "test_integration_plot.png"
        plot_training_history(history, output_path)
        
        # Verificar que se creó y guardó
        mock_figure.assert_called_with(figsize=(10, 6))
        mock_savefig.assert_called_once_with(output_path)
        mock_close.assert_called_once()
        
        # Verificar que se graficaron ambas curvas
        assert mock_plot.call_count == 2
    
    def test_analyze_predictions_statistics(self):
        """Test que las estadísticas de análisis son correctas."""
        # Mock de modelo con error sistemático
        model = Mock()
        model.predict.side_effect = lambda state: (
            0.5,  # alpha siempre 0.5
            0.6,  # beta siempre 0.6
            0.7   # gamma siempre 0.7
        )
        
        # Datos de prueba con valores conocidos
        test_data = pd.DataFrame({
            "feature": [1, 2, 3, 4, 5],
            "alpha": [0.4, 0.5, 0.6, 0.5, 0.4],
            "beta": [0.5, 0.6, 0.7, 0.6, 0.5],
            "gamma": [0.6, 0.7, 0.8, 0.7, 0.6]
        })
        
        errors = analyze_predictions(model, test_data)
        
        # Calcular MAE esperado manualmente
        expected_mae_alpha = np.mean([0.1, 0.0, 0.1, 0.0, 0.1])  # 0.06
        expected_mae_beta = np.mean([0.1, 0.0, 0.1, 0.0, 0.1])   # 0.06
        expected_mae_gamma = np.mean([0.1, 0.0, 0.1, 0.0, 0.1])  # 0.06
        
        actual_mae_alpha = np.mean(errors["alpha"])
        actual_mae_beta = np.mean(errors["beta"])
        actual_mae_gamma = np.mean(errors["gamma"])
        
        assert np.isclose(actual_mae_alpha, expected_mae_alpha, atol=0.01)
        assert np.isclose(actual_mae_beta, expected_mae_beta, atol=0.01)
        assert np.isclose(actual_mae_gamma, expected_mae_gamma, atol=0.01)