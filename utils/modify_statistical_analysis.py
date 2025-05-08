#!/usr/bin/env python3
"""
Script para integrar la versión corregida del método en el módulo original.
"""

import inspect
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.fixed_method import perform_statistical_analysis_report

def modify_statistical_analysis():
    """
    Modifica el módulo utils.statistical_analysis para reemplazar
    el método generate_statistical_analysis_report con la versión corregida.
    """
    import utils.statistical_analysis as sa
    from utils.fixed_method import perform_statistical_analysis_report
    
    # Obtener el módulo actual
    module = sa.StatisticalAnalysis
    
    # Definir una función wrapper que invoca la implementación corregida
    def new_method(cls, data_df, metric='best_fitness', alpha=0.05, output_file=None):
        # Usar la implementación arreglada
        return perform_statistical_analysis_report(data_df, metric, alpha, output_file, cls)
    
    # Asignar la nueva implementación al método original, preservando atributos
    new_method.__module__ = module.__module__
    new_method.__qualname__ = f"{module.__name__}.generate_statistical_analysis_report"
    new_method.__name__ = "generate_statistical_analysis_report"
    new_method.__doc__ = perform_statistical_analysis_report.__doc__
    
    # Reemplazar el método en la clase
    setattr(sa.StatisticalAnalysis, 'generate_statistical_analysis_report', staticmethod(new_method))
    
    # Informar del éxito
    print(f"Método 'generate_statistical_analysis_report' reemplazado correctamente.")

if __name__ == "__main__":
    modify_statistical_analysis()
