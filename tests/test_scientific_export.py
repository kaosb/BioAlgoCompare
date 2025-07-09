"""
Tests para el sistema unificado de exportación científica.
"""

import pytest
import json
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from utils.scientific_export import (
    ScientificExportPipeline,
    CSVExporter,
    JSONExporter,
    LaTeXExporter,
    ExcelExporter,
    export_scientific_results
)


@pytest.fixture
def sample_results_data():
    """Datos de ejemplo para tests."""
    return [
        {
            'algorithm': 'HOA',
            'instance': 'E-n22-k4',
            'fitness': 375.28,
            'execution_time': 1.23,
            'seed': 42
        },
        {
            'algorithm': 'HOA',
            'instance': 'E-n22-k4',
            'fitness': 378.95,
            'execution_time': 1.25,
            'seed': 43
        },
        {
            'algorithm': 'FOA',
            'instance': 'E-n22-k4',
            'fitness': 380.12,
            'execution_time': 1.45,
            'seed': 42
        },
        {
            'algorithm': 'FOA',
            'instance': 'E-n22-k4',
            'fitness': 382.45,
            'execution_time': 1.48,
            'seed': 43
        },
        {
            'algorithm': 'HOA',
            'instance': 'P-n16-k8',
            'fitness': 450.23,
            'execution_time': 0.98,
            'seed': 42
        },
        {
            'algorithm': 'FOA',
            'instance': 'P-n16-k8',
            'fitness': 455.67,
            'execution_time': 1.12,
            'seed': 42
        }
    ]


@pytest.fixture
def sample_dataframe(sample_results_data):
    """DataFrame de ejemplo."""
    return pd.DataFrame(sample_results_data)


@pytest.fixture
def temp_output_dir():
    """Directorio temporal para tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_metadata():
    """Metadatos de ejemplo."""
    return {
        'export_date': datetime.now().isoformat(),
        'experiment_name': 'Test Experiment',
        'total_runs': 6,
        'algorithms': ['HOA', 'FOA'],
        'instances': ['E-n22-k4', 'P-n16-k8']
    }


class TestExportFormats:
    """Tests para formatos individuales de exportación."""
    
    def test_csv_exporter(self, sample_dataframe, sample_metadata, temp_output_dir):
        """Test exportador CSV."""
        exporter = CSVExporter()
        output_path = temp_output_dir / "test_results"
        
        csv_path = exporter.export(sample_dataframe, sample_metadata, output_path)
        
        assert csv_path.exists()
        assert csv_path.suffix == '.csv'
        
        # Verificar contenido
        content = csv_path.read_text()
        assert '# BioAlgoCompare Export' in content
        assert 'algorithm,instance,fitness' in content
        
        # Verificar que se puede leer
        df_loaded = pd.read_csv(csv_path, comment='#')
        assert len(df_loaded) == len(sample_dataframe)
    
    def test_json_exporter(self, sample_dataframe, sample_metadata, temp_output_dir):
        """Test exportador JSON."""
        exporter = JSONExporter()
        output_path = temp_output_dir / "test_results"
        
        json_path = exporter.export(sample_dataframe, sample_metadata, output_path)
        
        assert json_path.exists()
        assert json_path.suffix == '.json'
        
        # Verificar contenido
        with open(json_path) as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert 'summary' in data
        assert 'results' in data
        assert len(data['results']) == 2  # HOA y FOA
        assert 'HOA' in data['results']
        assert 'E-n22-k4' in data['results']['HOA']
    
    def test_latex_exporter(self, sample_dataframe, sample_metadata, temp_output_dir):
        """Test exportador LaTeX."""
        exporter = LaTeXExporter()
        output_path = temp_output_dir / "test_results"
        
        latex_dir = exporter.export(sample_dataframe, sample_metadata, output_path)
        
        assert latex_dir.exists()
        assert latex_dir.is_dir()
        
        # Verificar archivos generados
        expected_files = [
            'descriptive_stats.tex',
            'rankings.tex',
            'statistical_tests.tex',
            'main_tables.tex'
        ]
        
        for filename in expected_files:
            file_path = latex_dir / filename
            assert file_path.exists(), f"Missing {filename}"
            
            # Verificar contenido LaTeX válido
            content = file_path.read_text()
            assert '\\begin{table}' in content or '\\documentclass' in content
    
    def test_excel_exporter(self, sample_dataframe, sample_metadata, temp_output_dir):
        """Test exportador Excel."""
        exporter = ExcelExporter()
        output_path = temp_output_dir / "test_results"
        
        excel_path = exporter.export(sample_dataframe, sample_metadata, output_path)
        
        assert excel_path.exists()
        assert excel_path.suffix == '.xlsx'
        
        # Verificar contenido
        xl = pd.ExcelFile(excel_path)
        assert 'Raw Data' in xl.sheet_names
        assert 'Algorithm Statistics' in xl.sheet_names
        assert 'Instance Statistics' in xl.sheet_names
        assert 'Pivot Summary' in xl.sheet_names
        assert 'Metadata' in xl.sheet_names
        
        # Verificar datos
        raw_data = pd.read_excel(excel_path, sheet_name='Raw Data')
        assert len(raw_data) == len(sample_dataframe)


class TestScientificExportPipeline:
    """Tests para el pipeline completo de exportación."""
    
    def test_pipeline_initialization(self, temp_output_dir):
        """Test inicialización del pipeline."""
        pipeline = ScientificExportPipeline(
            results_source=temp_output_dir,
            output_dir=temp_output_dir / 'export'
        )
        
        assert pipeline.output_dir.exists()
        assert len(pipeline.exporters) >= 4
    
    def test_load_from_directory(self, temp_output_dir, sample_results_data):
        """Test carga desde directorio."""
        # Crear archivo JSON de prueba
        json_file = temp_output_dir / 'results.json'
        with open(json_file, 'w') as f:
            json.dump(sample_results_data, f)
        
        pipeline = ScientificExportPipeline(results_source=temp_output_dir)
        data = pipeline.load_results()
        
        assert len(data) == len(sample_results_data)
        assert set(data['algorithm'].unique()) == {'HOA', 'FOA'}
    
    def test_generate_metadata(self, temp_output_dir, sample_dataframe):
        """Test generación de metadatos."""
        pipeline = ScientificExportPipeline(results_source=temp_output_dir)
        pipeline._data_cache = sample_dataframe
        
        metadata = pipeline.generate_metadata()
        
        assert 'export_info' in metadata
        assert 'experiment_info' in metadata
        assert 'statistical_summary' in metadata
        assert 'data_integrity' in metadata
        
        assert metadata['experiment_info']['total_runs'] == 6
        assert len(metadata['experiment_info']['unique_algorithms']) == 2
    
    def test_export_all_formats(self, temp_output_dir, sample_dataframe):
        """Test exportación en todos los formatos."""
        pipeline = ScientificExportPipeline(
            results_source=temp_output_dir,
            output_dir=temp_output_dir / 'export'
        )
        pipeline._data_cache = sample_dataframe
        
        files = pipeline.export(
            formats=['csv', 'json'],
            include_plots=False,
            create_archive=False
        )
        
        assert 'csv' in files
        assert 'json' in files
        assert files['csv'].exists()
        assert files['json'].exists()
    
    def test_export_with_plots(self, temp_output_dir, sample_dataframe):
        """Test exportación con visualizaciones."""
        pipeline = ScientificExportPipeline(
            results_source=temp_output_dir,
            output_dir=temp_output_dir / 'export'
        )
        pipeline._data_cache = sample_dataframe
        
        files = pipeline.export(
            formats=['csv'],
            include_plots=True,
            create_archive=False
        )
        
        # Verificar que se generaron plots
        assert any('boxplots' in k or 'ranking' in k for k in files.keys())
    
    def test_export_with_archive(self, temp_output_dir, sample_dataframe):
        """Test creación de archivo ZIP."""
        pipeline = ScientificExportPipeline(
            results_source=temp_output_dir,
            output_dir=temp_output_dir / 'export'
        )
        pipeline._data_cache = sample_dataframe
        
        files = pipeline.export(
            formats=['csv'],
            include_plots=False,
            create_archive=True
        )
        
        assert 'archive' in files
        assert files['archive'].exists()
        assert files['archive'].suffix == '.zip'
    
    def test_conference_export(self, temp_output_dir, sample_dataframe):
        """Test exportación para conferencia."""
        pipeline = ScientificExportPipeline(
            results_source=temp_output_dir,
            output_dir=temp_output_dir / 'export'
        )
        pipeline._data_cache = sample_dataframe
        
        files = pipeline.export_for_conference(
            conference='cisti2025',
            include_supplementary=True
        )
        
        # Verificar formatos específicos de conferencia
        assert 'latex' in files
        assert 'csv' in files
        assert 'json' in files
        
        # Verificar material suplementario
        assert any('replication_script' in k or 'environment_info' in k 
                  for k in files.keys())


class TestIntegration:
    """Tests de integración."""
    
    def test_export_scientific_results_function(self, temp_output_dir, sample_dataframe):
        """Test función de conveniencia."""
        # Crear archivo de datos
        csv_file = temp_output_dir / 'data.csv'
        sample_dataframe.to_csv(csv_file, index=False)
        
        files = export_scientific_results(
            results_source=csv_file,
            output_dir=temp_output_dir / 'export',
            formats=['csv', 'json']
        )
        
        assert len(files) >= 2
        assert all(Path(f).exists() for f in files.values() if isinstance(f, Path))
    
    def test_standardresultv2_format(self, temp_output_dir):
        """Test con formato StandardResultV2."""
        # Crear resultado en formato V2
        v2_result = {
            'result_id': 'test-001',
            'algorithm_info': {
                'algorithm_name': 'HOA',
                'version': '1.0'
            },
            'problem_info': {
                'instance_name': 'E-n22-k4',
                'dimension': 22
            },
            'runs': [
                {
                    'run_id': 'run-001',
                    'fitness': 375.28,
                    'execution_time': 1.23,
                    'seed': 42,
                    'iterations': 100
                },
                {
                    'run_id': 'run-002',
                    'fitness': 378.95,
                    'execution_time': 1.25,
                    'seed': 43,
                    'iterations': 100
                }
            ]
        }
        
        # Guardar archivo
        json_file = temp_output_dir / 'v2_results.json'
        with open(json_file, 'w') as f:
            json.dump([v2_result], f)
        
        # Exportar
        pipeline = ScientificExportPipeline(results_source=temp_output_dir)
        data = pipeline.load_results()
        
        assert len(data) == 2  # 2 runs
        assert data['algorithm'].iloc[0] == 'HOA'
        assert data['instance'].iloc[0] == 'E-n22-k4'


class TestErrorHandling:
    """Tests de manejo de errores."""
    
    def test_invalid_source(self):
        """Test con fuente inválida."""
        with pytest.raises(ValueError):
            pipeline = ScientificExportPipeline(results_source=123)
            pipeline.load_results()
    
    def test_empty_directory(self, temp_output_dir):
        """Test con directorio vacío."""
        pipeline = ScientificExportPipeline(results_source=temp_output_dir)
        data = pipeline.load_results()
        
        assert len(data) == 0
    
    def test_export_with_empty_data(self, temp_output_dir):
        """Test exportación sin datos."""
        pipeline = ScientificExportPipeline(
            results_source=temp_output_dir,
            output_dir=temp_output_dir / 'export'
        )
        
        # Forzar datos vacíos
        pipeline._data_cache = pd.DataFrame()
        
        files = pipeline.export(formats=['csv'], include_plots=False)
        
        # Debe exportar aunque esté vacío
        assert 'csv' in files
        assert files['csv'].exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])