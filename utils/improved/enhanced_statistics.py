#!/usr/bin/env python3
"""
Módulo para análisis estadístico avanzado de algoritmos metaheurísticos.
Implementa pruebas no paramétricas, análisis de potencia, y métodos de bootstrap
para generar conclusiones estadísticamente rigurosas.
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.stats import rankdata, friedmanchisquare, wilcoxon
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations
import os
import logging
from datetime import datetime
import warnings
from statsmodels.stats.multicomp import MultiComparison

# Ignorar advertencias
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enhanced_statistics")

class EnhancedStatisticalAnalysis:
    """Clase para análisis estadístico avanzado de resultados de algoritmos."""
    
    @staticmethod
    def prepare_data_for_statistics(benchmark_results, metric='best_fitness', include_opt=True):
        """
        Prepara los datos para análisis estadístico.
        
        Args:
            benchmark_results: Lista de objetos BenchmarkResult
            metric: Métrica a analizar (best_fitness, mean_fitness, etc.)
            include_opt: Si se incluyen versiones optimizadas de algoritmos
            
        Returns:
            DataFrame con los datos para análisis
        """
        # Verificar que hay resultados
        if not benchmark_results:
            logger.warning("No hay resultados para preparar datos")
            return pd.DataFrame()
        
        # Crear DataFrame
        data_rows = []
        
        for result in benchmark_results:
            # Verificar si se incluyen algoritmos _OPT
            if not include_opt and result.algorithm_name.endswith('_OPT'):
                continue
                
            # Obtener valores según la métrica
            if metric == 'best_fitness':
                value = result.best_fitness
            elif metric == 'mean_fitness':
                value = result.mean_fitness
            elif metric == 'execution_time':
                value = result.mean_time
            elif metric == 'gap_to_optimal':
                value = result.gap_to_optimal
            else:
                logger.warning(f"Métrica desconocida: {metric}")
                continue
                
            # Añadir fila
            data_rows.append({
                'Algorithm': result.algorithm_name,
                'Instance': result.instance_name,
                'Value': value
            })
        
        return pd.DataFrame(data_rows)
    
    @staticmethod
    def prepare_raw_data_for_statistics(benchmark_results, include_opt=True):
        """
        Prepara datos a nivel de ejecución individual para análisis.
        
        Args:
            benchmark_results: Lista de objetos BenchmarkResult
            include_opt: Si se incluyen versiones optimizadas de algoritmos
            
        Returns:
            DataFrame con los datos para análisis
        """
        # Verificar que hay resultados
        if not benchmark_results:
            logger.warning("No hay resultados para preparar datos")
            return pd.DataFrame()
        
        # Crear DataFrame
        data_rows = []
        
        for result in benchmark_results:
            # Verificar si se incluyen algoritmos _OPT
            if not include_opt and result.algorithm_name.endswith('_OPT'):
                continue
                
            # Añadir una fila por cada ejecución individual
            for run_id, (fitness, time) in enumerate(zip(result.fitness_values, result.execution_times), 1):
                data_rows.append({
                    'algorithm': result.algorithm_name,
                    'instance': result.instance_name,
                    'run': run_id,
                    'fitness': fitness,
                    'time': time
                })
        
        return pd.DataFrame(data_rows)
    
    @staticmethod
    def perform_friedman_test(data, alpha=0.05):
        """
        Realiza el test de Friedman para comparar múltiples algoritmos.
        
        Args:
            data: DataFrame con las columnas Algorithm, Instance, Value
            alpha: Nivel de significancia
            
        Returns:
            Diccionario con resultados del test
        """
        # Verificar que hay suficientes datos
        if len(data) < 5:
            logger.warning("No hay suficientes datos para el test de Friedman")
            return {
                'test': 'Friedman',
                'reject_h0': False,
                'p_value': None,
                'statistic': None,
                'alpha': alpha,
                'rank_dict': {},
                'error': 'Datos insuficientes'
            }
        
        # Crear matriz de datos (filas=instancias, columnas=algoritmos)
        pivot = data.pivot(index='Instance', columns='Algorithm', values='Value')
        
        # Verificar que hay suficientes algoritmos e instancias
        if pivot.shape[0] < 2 or pivot.shape[1] < 2:
            logger.warning("Se requieren al menos 2 algoritmos y 2 instancias para el test de Friedman")
            return {
                'test': 'Friedman',
                'reject_h0': False,
                'p_value': None,
                'statistic': None,
                'alpha': alpha,
                'rank_dict': {},
                'error': 'Se requieren al menos 2 algoritmos y 2 instancias'
            }
        
        # Calcular rankings por filas (instancias)
        ranks = pivot.rank(axis=1, method='average', ascending=True)
        
        # Calcular ranking promedio por algoritmo
        avg_ranks = ranks.mean()
        
        # Calcular estadístico de Friedman
        n = pivot.shape[0]  # Número de instancias
        k = pivot.shape[1]  # Número de algoritmos
        
        r_j_squared_sum = np.sum(avg_ranks ** 2)
        statistic = (12 * n) / (k * (k + 1)) * (r_j_squared_sum - k * (k + 1) ** 2 / 4)
        
        # Calcular p-value usando chi-cuadrado con k-1 grados de libertad
        p_value = 1 - stats.chi2.cdf(statistic, k - 1)
        
        # Calcular distancia crítica para Nemenyi
        critical_distance = stats.t.ppf(1 - alpha / 2, n - 1) * np.sqrt((k * (k + 1)) / (6 * n))
        
        # Determinar si rechazar la hipótesis nula
        reject_h0 = p_value < alpha
        
        # Crear diccionario con resultados
        result = {
            'test': 'Friedman',
            'statistic': statistic,
            'p_value': p_value,
            'reject_h0': reject_h0,
            'alpha': alpha,
            'rank_dict': avg_ranks.to_dict(),
            'critical_distance': critical_distance,
            'n_instances': n,
            'n_algorithms': k
        }
        
        return result
    
    @staticmethod
    def perform_nemenyi_test(friedman_result):
        """
        Realiza el test post-hoc de Nemenyi para comparaciones múltiples.
        
        Args:
            friedman_result: Resultados del test de Friedman
            
        Returns:
            Diccionario con resultados del test de Nemenyi
        """
        # Verificar que hay resultados de Friedman
        if 'rank_dict' not in friedman_result or not friedman_result['rank_dict']:
            logger.warning("No hay resultados de Friedman para realizar test de Nemenyi")
            return {
                'test': 'Nemenyi',
                'error': 'No hay resultados de Friedman'
            }
        
        # Extraer datos
        rank_dict = friedman_result['rank_dict']
        cd = friedman_result['critical_distance']
        
        # Crear matriz de comparaciones
        algorithms = list(rank_dict.keys())
        n_algos = len(algorithms)
        
        comparison_matrix = np.zeros((n_algos, n_algos), dtype=bool)
        diff_matrix = np.zeros((n_algos, n_algos))
        
        # Realizar comparaciones por pares
        for i, algo1 in enumerate(algorithms):
            for j, algo2 in enumerate(algorithms):
                if i != j:
                    diff = abs(rank_dict[algo1] - rank_dict[algo2])
                    diff_matrix[i, j] = diff
                    comparison_matrix[i, j] = diff > cd
        
        # Crear resultado
        result = {
            'test': 'Nemenyi',
            'critical_distance': cd,
            'rank_dict': rank_dict,
            'algorithms': algorithms,
            'significant_diff': comparison_matrix,
            'rank_diff': diff_matrix
        }
        
        return result
    
    @staticmethod
    def perform_wilcoxon_test(data, alpha=0.05):
        """
        Realiza el test de Wilcoxon para comparaciones por pares.
        
        Args:
            data: DataFrame con datos a nivel de ejecución individual
            alpha: Nivel de significancia
            
        Returns:
            DataFrame con resultados de las comparaciones
        """
        # Verificar que hay datos
        if len(data) < 5:
            logger.warning("No hay suficientes datos para el test de Wilcoxon")
            return pd.DataFrame()
        
        # Obtener algoritmos únicos
        algorithms = data['algorithm'].unique()
        
        if len(algorithms) < 2:
            logger.warning("Se requieren al menos 2 algoritmos para el test de Wilcoxon")
            return pd.DataFrame()
        
        # Crear DataFrame para resultados
        result_rows = []
        
        # Agrupar por instancia
        instances = data['instance'].unique()
        
        for instance in instances:
            inst_data = data[data['instance'] == instance]
            
            # Realizar test para cada par de algoritmos
            for algo1, algo2 in combinations(algorithms, 2):
                algo1_fitness = inst_data[inst_data['algorithm'] == algo1]['fitness'].values
                algo2_fitness = inst_data[inst_data['algorithm'] == algo2]['fitness'].values
                
                # Verificar que hay suficientes datos
                if len(algo1_fitness) < 5 or len(algo2_fitness) < 5:
                    logger.warning(f"Datos insuficientes para {algo1} vs {algo2} en {instance}")
                    continue
                
                # Realizar test (para problemas de minimización, valores más bajos son mejores)
                try:
                    # Emparejar los datos (usar el mínimo número de ejecuciones)
                    min_size = min(len(algo1_fitness), len(algo2_fitness))
                    paired_data1 = algo1_fitness[:min_size]
                    paired_data2 = algo2_fitness[:min_size]
                    
                    statistic, p_value = wilcoxon(paired_data1, paired_data2)
                    
                    # Calcular tamaño del efecto (r = Z / sqrt(N))
                    effect_size = statistic / np.sqrt(min_size)
                    
                    # Determinar ganador
                    mean1 = np.mean(paired_data1)
                    mean2 = np.mean(paired_data2)
                    winner = algo1 if mean1 < mean2 else algo2
                    
                    # Añadir resultado
                    result_rows.append({
                        'Instance': instance,
                        'Algorithm1': algo1,
                        'Algorithm2': algo2,
                        'Mean1': mean1,
                        'Mean2': mean2,
                        'p_value': p_value,
                        'Significant': p_value < alpha,
                        'Winner': winner if p_value < alpha else 'No significant difference',
                        'Effect_Size': effect_size
                    })
                except Exception as e:
                    logger.warning(f"Error en test de Wilcoxon para {algo1} vs {algo2} en {instance}: {str(e)}")
        
        return pd.DataFrame(result_rows)
    
    @staticmethod
    def perform_bootstrap_analysis(data, metric='fitness', n_bootstrap=1000, confidence=0.95):
        """
        Realiza análisis de bootstrap para estimar intervalos de confianza.
        
        Args:
            data: DataFrame con datos a nivel de ejecución individual
            metric: Métrica a analizar (fitness, time)
            n_bootstrap: Número de muestras de bootstrap
            confidence: Nivel de confianza
            
        Returns:
            DataFrame con resultados de bootstrap
        """
        # Verificar que hay datos
        if len(data) < 10:
            logger.warning("No hay suficientes datos para análisis de bootstrap")
            return pd.DataFrame()
        
        # Agrupar por algoritmo e instancia
        grouped = data.groupby(['algorithm', 'instance'])
        
        # Crear DataFrame para resultados
        result_rows = []
        
        for (algo, instance), group in grouped:
            # Obtener valores
            values = group[metric].values
            
            # Verificar que hay suficientes datos
            if len(values) < 10:
                logger.warning(f"Datos insuficientes para bootstrap: {algo}, {instance}")
                continue
            
            # Realizar bootstrap
            bootstrap_means = []
            
            for _ in range(n_bootstrap):
                bootstrap_sample = np.random.choice(values, size=len(values), replace=True)
                bootstrap_means.append(np.mean(bootstrap_sample))
            
            # Calcular intervalos de confianza
            lower = np.percentile(bootstrap_means, (1 - confidence) * 100 / 2)
            upper = np.percentile(bootstrap_means, 100 - (1 - confidence) * 100 / 2)
            
            # Añadir resultado
            result_rows.append({
                'Algorithm': algo,
                'Instance': instance,
                'Mean': np.mean(values),
                'CI_Lower': lower,
                'CI_Upper': upper,
                'CI_Width': upper - lower,
                'StdDev': np.std(values),
                'Min': np.min(values),
                'Max': np.max(values),
                'Samples': len(values)
            })
        
        return pd.DataFrame(result_rows)
    
    @staticmethod
    def perform_kruskal_wallis_test(data, metric='fitness', alpha=0.05):
        """
        Realiza el test de Kruskal-Wallis para comparar múltiples algoritmos.
        
        Args:
            data: DataFrame con datos a nivel de ejecución individual
            metric: Métrica a analizar (fitness, time)
            alpha: Nivel de significancia
            
        Returns:
            DataFrame con resultados del test
        """
        # Verificar que hay datos
        if len(data) < 10:
            logger.warning("No hay suficientes datos para test de Kruskal-Wallis")
            return pd.DataFrame()
        
        # Agrupar por instancia
        instances = data['instance'].unique()
        
        # Crear DataFrame para resultados
        result_rows = []
        
        for instance in instances:
            inst_data = data[data['instance'] == instance]
            
            # Verificar que hay al menos 2 algoritmos
            algorithms = inst_data['algorithm'].unique()
            if len(algorithms) < 2:
                logger.warning(f"Se requieren al menos 2 algoritmos para {instance}")
                continue
            
            # Preparar datos para el test
            samples = []
            sample_names = []
            
            for algo in algorithms:
                algo_values = inst_data[inst_data['algorithm'] == algo][metric].values
                
                # Verificar que hay suficientes datos
                if len(algo_values) < 5:
                    logger.warning(f"Datos insuficientes para {algo} en {instance}")
                    continue
                
                samples.append(algo_values)
                sample_names.append(algo)
            
            # Verificar que hay suficientes algoritmos después de filtrar
            if len(samples) < 2:
                logger.warning(f"Datos insuficientes para test en {instance}")
                continue
            
            # Realizar test
            try:
                statistic, p_value = stats.kruskal(*samples)
                
                # Añadir resultado
                result_rows.append({
                    'Instance': instance,
                    'Statistic': statistic,
                    'p_value': p_value,
                    'Significant': p_value < alpha,
                    'Algorithms': len(samples)
                })
                
                # Si hay diferencia significativa, realizar post-hoc
                if p_value < alpha:
                    # Crear array para comparaciones post-hoc
                    all_values = np.concatenate(samples)
                    all_labels = np.concatenate([[algo] * len(s) for algo, s in zip(sample_names, samples)])
                    
                    # Realizar comparaciones múltiples
                    mc = MultiComparison(all_values, all_labels)
                    result = mc.tukeyhsd()
                    
                    # Extraer resultados
                    for i, (algo1, algo2) in enumerate(result.data[0]):
                        reject = result.reject[i]
                        diff = -result.meandiffs[i]  # Negativo porque queremos minimizar
                        conf_lower = -result.confint[i][1]  # Negativo y cambiado porque queremos minimizar
                        conf_upper = -result.confint[i][0]  # Negativo y cambiado porque queremos minimizar
                        
                        winner = algo1 if diff < 0 else algo2
                        
                        # Añadir resultados de post-hoc
                        result_rows.append({
                            'Instance': instance,
                            'Algorithm1': algo1,
                            'Algorithm2': algo2,
                            'Mean_Diff': diff,
                            'CI_Lower': conf_lower,
                            'CI_Upper': conf_upper,
                            'Significant': reject,
                            'Winner': winner if reject else 'No significant difference',
                            'Test': 'Tukey HSD'
                        })
            except Exception as e:
                logger.warning(f"Error en test de Kruskal-Wallis para {instance}: {str(e)}")
        
        return pd.DataFrame(result_rows)
    
    @staticmethod
    def calculate_effect_sizes(data, metric='fitness'):
        """
        Calcula tamaños de efecto (Cohen's d) entre pares de algoritmos.
        
        Args:
            data: DataFrame con datos a nivel de ejecución individual
            metric: Métrica a analizar (fitness, time)
            
        Returns:
            DataFrame con tamaños de efecto
        """
        # Verificar que hay datos
        if len(data) < 10:
            logger.warning("No hay suficientes datos para calcular tamaños de efecto")
            return pd.DataFrame()
        
        # Agrupar por instancia
        instances = data['instance'].unique()
        
        # Crear DataFrame para resultados
        result_rows = []
        
        for instance in instances:
            inst_data = data[data['instance'] == instance]
            
            # Obtener algoritmos
            algorithms = inst_data['algorithm'].unique()
            
            # Calcular tamaño de efecto para cada par
            for algo1, algo2 in combinations(algorithms, 2):
                algo1_values = inst_data[inst_data['algorithm'] == algo1][metric].values
                algo2_values = inst_data[inst_data['algorithm'] == algo2][metric].values
                
                # Verificar que hay suficientes datos
                if len(algo1_values) < 5 or len(algo2_values) < 5:
                    logger.warning(f"Datos insuficientes para {algo1} vs {algo2} en {instance}")
                    continue
                
                # Calcular Cohen's d
                mean1 = np.mean(algo1_values)
                mean2 = np.mean(algo2_values)
                
                # Calcular desviación estándar agrupada
                n1 = len(algo1_values)
                n2 = len(algo2_values)
                s1 = np.std(algo1_values, ddof=1)
                s2 = np.std(algo2_values, ddof=1)
                
                s_pooled = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
                
                # Calcular d
                if s_pooled == 0:
                    d = np.nan
                else:
                    d = (mean1 - mean2) / s_pooled
                
                # Interpretar tamaño del efecto
                if np.isnan(d):
                    magnitude = 'N/A'
                elif abs(d) < 0.2:
                    magnitude = 'Negligible'
                elif abs(d) < 0.5:
                    magnitude = 'Small'
                elif abs(d) < 0.8:
                    magnitude = 'Medium'
                else:
                    magnitude = 'Large'
                
                # Para problemas de minimización, un d negativo indica que algo1 es mejor
                better_algo = algo1 if d < 0 else algo2
                
                # Añadir resultado
                result_rows.append({
                    'Instance': instance,
                    'Algorithm1': algo1,
                    'Algorithm2': algo2,
                    'Mean1': mean1,
                    'Mean2': mean2,
                    'Effect_Size': abs(d),  # Valor absoluto para facilitar interpretación
                    'Direction': 'algo1 better' if d < 0 else 'algo2 better',
                    'Better_Algorithm': better_algo,
                    'Magnitude': magnitude
                })
        
        return pd.DataFrame(result_rows)
    
    @staticmethod
    def run_comprehensive_statistical_analysis(benchmark_results, metrics=None, output_dir=None, alpha=0.05):
        """
        Ejecuta un análisis estadístico completo con múltiples pruebas.
        
        Args:
            benchmark_results: Lista de objetos BenchmarkResult
            metrics: Lista de métricas a analizar (None = todas)
            output_dir: Directorio para guardar resultados
            alpha: Nivel de significancia
            
        Returns:
            Diccionario con rutas a los informes generados
        """
        if metrics is None:
            metrics = ['best_fitness', 'mean_fitness', 'execution_time']
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"results/statistical_analysis_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Crear datos a nivel de ejecución individual
        raw_data = EnhancedStatisticalAnalysis.prepare_raw_data_for_statistics(benchmark_results)
        
        # Informes generados
        report_paths = {}
        
        for metric in metrics:
            logger.info(f"Procesando métrica: {metric}")
            
            # Preparar datos para esta métrica
            data = EnhancedStatisticalAnalysis.prepare_data_for_statistics(benchmark_results, metric=metric)
            
            if len(data) < 2:
                logger.warning(f"Datos insuficientes para métrica {metric}")
                continue
            
            # Crear directorio para esta métrica
            metric_dir = os.path.join(output_dir, metric)
            os.makedirs(metric_dir, exist_ok=True)
            
            # 1. Test de Friedman
            try:
                logger.info(f"Ejecutando test de Friedman para {metric}")
                friedman_result = EnhancedStatisticalAnalysis.perform_friedman_test(data, alpha=alpha)
                
                # Guardar resultados
                friedman_file = os.path.join(metric_dir, "friedman_test.json")
                with open(friedman_file, 'w') as f:
                    import json
                    json.dump(friedman_result, f, indent=2, default=lambda x: float(x) if isinstance(x, np.float64) else x)
                
                # Si Friedman es significativo, realizar Nemenyi
                if friedman_result['reject_h0']:
                    logger.info(f"Test de Friedman significativo. Ejecutando Nemenyi para {metric}")
                    nemenyi_result = EnhancedStatisticalAnalysis.perform_nemenyi_test(friedman_result)
                    
                    # Guardar resultados
                    nemenyi_file = os.path.join(metric_dir, "nemenyi_test.json")
                    with open(nemenyi_file, 'w') as f:
                        # Convertir matrices numpy a listas
                        nemenyi_result_json = dict(nemenyi_result)
                        if 'significant_diff' in nemenyi_result_json:
                            nemenyi_result_json['significant_diff'] = nemenyi_result_json['significant_diff'].tolist()
                        if 'rank_diff' in nemenyi_result_json:
                            nemenyi_result_json['rank_diff'] = nemenyi_result_json['rank_diff'].tolist()
                        
                        json.dump(nemenyi_result_json, f, indent=2)
                    
                    # Crear diagrama CD
                    try:
                        from utils.improved.advanced_visualization import create_cd_diagram
                        
                        # Extraer rankings
                        ranks = np.array(list(friedman_result['rank_dict'].values()))
                        names = list(friedman_result['rank_dict'].keys())
                        
                        # Crear diagrama
                        cd_file = os.path.join(metric_dir, "cd_diagram.png")
                        create_cd_diagram(ranks, names, cd=friedman_result['critical_distance'], output_file=cd_file)
                    except Exception as e:
                        logger.warning(f"Error al crear diagrama CD: {str(e)}")
            except Exception as e:
                logger.warning(f"Error en test de Friedman para {metric}: {str(e)}")
            
            # 2. Tests de Wilcoxon
            try:
                if metric == 'best_fitness' or metric == 'mean_fitness':
                    logger.info(f"Ejecutando tests de Wilcoxon para {metric}")
                    wilcoxon_results = EnhancedStatisticalAnalysis.perform_wilcoxon_test(raw_data, alpha=alpha)
                    
                    # Guardar resultados
                    if not wilcoxon_results.empty:
                        wilcoxon_file = os.path.join(metric_dir, "wilcoxon_tests.csv")
                        wilcoxon_results.to_csv(wilcoxon_file, index=False)
            except Exception as e:
                logger.warning(f"Error en tests de Wilcoxon para {metric}: {str(e)}")
            
            # 3. Análisis de bootstrap
            try:
                if metric == 'best_fitness' or metric == 'mean_fitness':
                    logger.info(f"Ejecutando análisis de bootstrap para {metric}")
                    bootstrap_results = EnhancedStatisticalAnalysis.perform_bootstrap_analysis(
                        raw_data, metric='fitness', n_bootstrap=1000, confidence=0.95
                    )
                    
                    # Guardar resultados
                    if not bootstrap_results.empty:
                        bootstrap_file = os.path.join(metric_dir, "bootstrap_analysis.csv")
                        bootstrap_results.to_csv(bootstrap_file, index=False)
            except Exception as e:
                logger.warning(f"Error en análisis de bootstrap para {metric}: {str(e)}")
            
            # 4. Tamaños de efecto
            try:
                if metric == 'best_fitness' or metric == 'mean_fitness':
                    logger.info(f"Calculando tamaños de efecto para {metric}")
                    effect_sizes = EnhancedStatisticalAnalysis.calculate_effect_sizes(raw_data, metric='fitness')
                    
                    # Guardar resultados
                    if not effect_sizes.empty:
                        effect_file = os.path.join(metric_dir, "effect_sizes.csv")
                        effect_sizes.to_csv(effect_file, index=False)
            except Exception as e:
                logger.warning(f"Error al calcular tamaños de efecto para {metric}: {str(e)}")
            
            # 5. Crear informe HTML
            try:
                report_file = os.path.join(output_dir, f"report_{metric}.html")
                report_paths[metric] = EnhancedStatisticalAnalysis.generate_statistical_analysis_report(
                    data, metric=metric, alpha=alpha, output_file=report_file
                )
            except Exception as e:
                logger.warning(f"Error al generar informe para {metric}: {str(e)}")
        
        # Crear índice general
        try:
            index_file = os.path.join(output_dir, "index.html")
            with open(index_file, 'w') as f:
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Análisis Estadístico Completo</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                            line-height: 1.6;
                        }}
                        h1, h2, h3 {{
                            color: #2c3e50;
                        }}
                        ul {{
                            list-style-type: none;
                            padding: 0;
                        }}
                        li {{
                            margin-bottom: 10px;
                        }}
                        a {{
                            text-decoration: none;
                            color: #3498db;
                            padding: 5px 10px;
                            border: 1px solid #3498db;
                            border-radius: 5px;
                        }}
                        a:hover {{
                            background-color: #3498db;
                            color: white;
                        }}
                        .warning {{
                            color: #e67e22;
                            background-color: #fff3e0;
                            padding: 10px;
                            border-left: 5px solid #e67e22;
                            margin-bottom: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <h1>Análisis Estadístico Completo</h1>
                    <p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    
                    
                    
                    <h2>Informes por Métrica</h2>
                    <ul>
                """
                
                for metric, path in report_paths.items():
                    rel_path = os.path.relpath(path, output_dir)
                    html_content += f"""
                        <li><a href="{rel_path}">{metric}</a></li>
                    """
                
                html_content += """
                    </ul>
                </body>
                </html>
                """
                
                f.write(html_content)
            
            report_paths['index'] = index_file
        except Exception as e:
            logger.warning(f"Error al generar índice: {str(e)}")
        
        return report_paths
    
    @staticmethod
    def generate_statistical_analysis_report(data_df, metric='best_fitness', alpha=0.05, output_file=None):
        """
        Genera un informe HTML con resultados de análisis estadístico.
        
        Args:
            data_df: DataFrame con datos para análisis
            metric: Métrica analizada
            alpha: Nivel de significancia
            output_file: Ruta para guardar el informe
            
        Returns:
            Ruta al informe generado
        """
        # Configurar ruta de salida
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"results/statistical_report_{metric}_{timestamp}.html"
        
        # Ejecutar test de Friedman
        friedman_result = EnhancedStatisticalAnalysis.perform_friedman_test(data_df, alpha=alpha)
        
        # Generar contenido HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Análisis Estadístico - {metric}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    line-height: 1.6;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 20px;
                }}
                th, td {{
                    text-align: left;
                    padding: 8px;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .significant {{
                    font-weight: bold;
                    color: #e74c3c;
                }}
                .not-significant {{
                    color: #7f8c8d;
                }}
                .conclusion {{
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-left: 5px solid #3498db;
                    margin-bottom: 20px;
                }}
                .highlight {{
                    font-weight: bold;
                    background-color: #ffffcc;
                    padding: 2px 5px;
                }}
            </style>
        </head>
        <body>
            <h1>Análisis Estadístico - {metric}</h1>
            <p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Test de Friedman</h2>
        """
        
        # Añadir resultados de Friedman
        if 'error' in friedman_result:
            html_content += f"""
            <p>Error en test de Friedman: {friedman_result['error']}</p>
            """
        else:
            p_value = friedman_result['p_value']
            statistic = friedman_result['statistic']
            reject_h0 = friedman_result['reject_h0']
            rank_dict = friedman_result['rank_dict']
            
            # Ordenar algoritmos por ranking
            sorted_algos = sorted(rank_dict.items(), key=lambda x: x[1])
            
            html_content += f"""
            <p>Estadístico de Friedman: {statistic:.4f}</p>
            <p>p-valor: {p_value:.6f}</p>
            <p>Nivel de significancia: {alpha}</p>
            <p>Conclusión: {'Rechazar' if reject_h0 else 'No rechazar'} H0 
               <span class="{'significant' if reject_h0 else 'not-significant'}">
                   (Hay{'diferencias significativas' if reject_h0 else 'diferencias NO significativas'} entre algoritmos)
               </span>
            </p>
            
            <h3>Rankings promedio</h3>
            <table>
                <tr>
                    <th>Algoritmo</th>
                    <th>Ranking promedio</th>
                </tr>
            """
            
            # Añadir filas de ranking
            for algo, rank in sorted_algos:
                html_content += f"""
                <tr>
                    <td>{algo}</td>
                    <td>{rank:.2f}</td>
                </tr>
                """
            
            html_content += """
            </table>
            """
            
            # Si Friedman es significativo, añadir resultados de Nemenyi
            if reject_h0:
                html_content += """
                <h2>Test post-hoc de Nemenyi</h2>
                """
                
                # Ejecutar Nemenyi
                nemenyi_result = EnhancedStatisticalAnalysis.perform_nemenyi_test(friedman_result)
                
                if 'error' in nemenyi_result:
                    html_content += f"""
                    <p>Error en test de Nemenyi: {nemenyi_result['error']}</p>
                    """
                else:
                    cd = nemenyi_result['critical_distance']
                    algorithms = nemenyi_result['algorithms']
                    significant_diff = nemenyi_result['significant_diff']
                    rank_diff = nemenyi_result['rank_diff']
                    
                    html_content += f"""
                    <p>Diferencia crítica (CD): {cd:.4f}</p>
                    
                    <h3>Comparaciones por pares</h3>
                    <table>
                        <tr>
                            <th>Algoritmo 1</th>
                            <th>Algoritmo 2</th>
                            <th>Diferencia de ranking</th>
                            <th>Significativa</th>
                        </tr>
                    """
                    
                    # Añadir filas de comparaciones
                    for i, algo1 in enumerate(algorithms):
                        for j, algo2 in enumerate(algorithms):
                            if i < j:  # Evitar duplicados
                                diff = rank_diff[i, j]
                                is_significant = significant_diff[i, j]
                                
                                html_content += f"""
                                <tr>
                                    <td>{algo1}</td>
                                    <td>{algo2}</td>
                                    <td>{diff:.4f}</td>
                                    <td class="{'significant' if is_significant else 'not-significant'}">
                                        {'Sí' if is_significant else 'No'}
                                    </td>
                                </tr>
                                """
                    
                    html_content += """
                    </table>
                    """
                    
                    # Añadir conclusiones
                    html_content += """
                    <h3>Conclusiones</h3>
                    <div class="conclusion">
                    """
                    
                    # Identificar grupos significativamente diferentes
                    groups = []
                    visited = set()
                    
                    for i, algo1 in enumerate(algorithms):
                        if algo1 in visited:
                            continue
                            
                        group = [algo1]
                        visited.add(algo1)
                        
                        for j, algo2 in enumerate(algorithms):
                            if algo2 in visited:
                                continue
                                
                            # Si no hay diferencia significativa, añadir al grupo
                            if i < j and not significant_diff[i, j]:
                                group.append(algo2)
                                visited.add(algo2)
                            elif j < i and not significant_diff[j, i]:
                                group.append(algo2)
                                visited.add(algo2)
                        
                        if group:
                            groups.append(group)
                    
                    # Mostrar grupos
                    if groups:
                        html_content += """
                        <p>Se identificaron los siguientes grupos de algoritmos sin diferencias significativas entre sí:</p>
                        <ul>
                        """
                        
                        for i, group in enumerate(groups):
                            html_content += f"""
                            <li>Grupo {i+1}: {', '.join(group)}</li>
                            """
                        
                        html_content += """
                        </ul>
                        """
                    
                    # Identificar algoritmo con mejor ranking
                    best_algo = sorted_algos[0][0]
                    best_rank = sorted_algos[0][1]
                    
                    html_content += f"""
                    <p>El algoritmo con mejor ranking promedio es <span class="highlight">{best_algo}</span> con un ranking de {best_rank:.2f}.</p>
                    """
                    
                    # Verificar si es significativamente mejor que todos
                    all_better = True
                    for i, (algo, _) in enumerate(sorted_algos):
                        if i > 0:  # Comparar con los demás
                            idx1 = algorithms.index(best_algo)
                            idx2 = algorithms.index(algo)
                            
                            if idx1 < idx2 and not significant_diff[idx1, idx2]:
                                all_better = False
                                break
                            elif idx2 < idx1 and not significant_diff[idx2, idx1]:
                                all_better = False
                                break
                    
                    if all_better:
                        html_content += f"""
                        <p><span class="highlight">{best_algo}</span> es significativamente mejor que todos los demás algoritmos.</p>
                        """
                    else:
                        # Identificar algoritmos no significativamente diferentes al mejor
                        similar_algos = [best_algo]
                        
                        for i, (algo, _) in enumerate(sorted_algos):
                            if i > 0:  # Comparar con los demás
                                idx1 = algorithms.index(best_algo)
                                idx2 = algorithms.index(algo)
                                
                                if idx1 < idx2 and not significant_diff[idx1, idx2]:
                                    similar_algos.append(algo)
                                elif idx2 < idx1 and not significant_diff[idx2, idx1]:
                                    similar_algos.append(algo)
                        
                        if len(similar_algos) > 1:
                            html_content += f"""
                            <p>No hay diferencias significativas entre los siguientes algoritmos: <span class="highlight">{', '.join(similar_algos)}</span>.</p>
                            """
                    
                    html_content += """
                    </div>
                    """
            
            else:
                # Si Friedman no es significativo, añadir conclusión
                html_content += """
                <div class="conclusion">
                    <p>El test de Friedman no encontró diferencias significativas entre los algoritmos.</p>
                    <p>No es necesario realizar pruebas post-hoc.</p>
                </div>
                """
        
        # Cerrar HTML
        html_content += """
        </body>
        </html>
        """
        
        # Guardar archivo
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Informe generado: {output_file}")
        
        return output_file