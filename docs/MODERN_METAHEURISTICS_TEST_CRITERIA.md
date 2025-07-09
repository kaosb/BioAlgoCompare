# Criterios de Test Apropiados para Metaheurísticas Modernas

## 1. Problemas con los Criterios Actuales

### Criterios Actuales (Demasiado Estrictos)
```python
MIN_IMPROVEMENT_RATIO = 0.01  # 1% mejora mínima esperada
MAX_STAGNATION_RATIO = 0.9   # Máximo 90% iteraciones sin mejora
# Mejora monotónica estricta (nunca empeorar)
```

### Por Qué Son Inadecuados
1. **Asumen comportamiento determinista** en algoritmos estocásticos
2. **Ignoran fases de exploración** necesarias para evitar óptimos locales
3. **Penalizan diversificación** que es crucial en metaheurísticas modernas
4. **No consideran trade-offs** entre exploración y explotación

## 2. Criterios Recomendados para Metaheurísticas Modernas

### A. Convergencia y Mejora

```python
# Criterios más realistas
MIN_IMPROVEMENT_RATIO = 0.001      # 0.1% mejora (vs 1% actual)
MAX_STAGNATION_RATIO = 0.95        # 95% estancamiento permitido (vs 90%)
IMPROVEMENT_WINDOW = 10            # Evaluar mejora en ventanas de iteraciones
```

**Justificación**: Las metaheurísticas pueden pasar largos períodos explorando antes de encontrar mejoras significativas.

### B. Monotonía Flexible

```python
# Permitir degradación temporal controlada
ALLOWED_DEGRADATION = 0.05         # 5% de empeoramiento temporal permitido
DEGRADATION_FREQUENCY = 0.1        # Máximo 10% de iteraciones con degradación
```

**Justificación**: Algoritmos como Simulated Annealing, GVOA y RRO deliberadamente aceptan soluciones peores.

### C. Métricas de Calidad Multi-Criterio

```python
# Evaluar múltiples aspectos
class MetaheuristicTestCriteria:
    # 1. Calidad de Solución
    ACCEPTABLE_GAP_FROM_KNOWN = 0.15   # 15% del óptimo conocido
    
    # 2. Robustez
    MAX_VARIANCE_RATIO = 0.1           # Varianza < 10% del promedio
    MIN_SUCCESS_RATE = 0.8             # 80% de runs exitosos
    
    # 3. Eficiencia
    CONVERGENCE_SPEED_PERCENTILE = 50  # Converger antes del 50% de iteraciones
    
    # 4. Diversidad
    MIN_POPULATION_DIVERSITY = 0.2     # Mantener 20% de diversidad
```

## 3. Métricas Específicas por Tipo de Algoritmo

### A. Algoritmos Basados en Población
```python
# Para GA, PSO, DE, etc.
POPULATION_METRICS = {
    'diversity_threshold': 0.15,        # Diversidad mínima
    'convergence_balance': 0.7,         # 70% explotación, 30% exploración
    'elite_retention': 0.1              # 10% élite preservada
}
```

### B. Algoritmos de Trayectoria Única
```python
# Para SA, VNS, ILS, etc.
TRAJECTORY_METRICS = {
    'acceptance_ratio': 0.2,            # 20% movimientos de empeoramiento
    'restart_threshold': 50,            # Reiniciar tras 50 iter sin mejora
    'intensification_ratio': 0.6        # 60% intensificación
}
```

### C. Algoritmos Híbridos/Adaptativos
```python
# Para algoritmos con múltiples fases
ADAPTIVE_METRICS = {
    'phase_transition_smooth': True,    # Transiciones suaves entre fases
    'parameter_adaptation_range': 0.5,  # Rango de adaptación de parámetros
    'learning_improvement': 0.05        # 5% mejora por aprendizaje
}
```

## 4. Tests Estadísticos Apropiados

### A. Tests de Rendimiento
```python
# En lugar de una sola ejecución
STATISTICAL_TESTS = {
    'min_runs': 30,                    # Mínimo 30 ejecuciones
    'confidence_level': 0.95,          # 95% confianza
    'test_type': 'wilcoxon',           # Test no paramétrico
    'effect_size': 'cohen_d'           # Tamaño del efecto
}
```

### B. Tests de Convergencia
```python
def test_convergence_trend():
    """Evaluar tendencia general, no cada iteración"""
    # Regresión lineal sobre ventanas de iteraciones
    window_size = max_iter // 10
    improvements = []
    
    for i in range(0, len(curve), window_size):
        window = curve[i:i+window_size]
        trend = linear_regression(window)
        improvements.append(trend.slope < 0)  # Tendencia negativa = mejora
    
    # Al menos 60% de ventanas deben mostrar mejora
    assert sum(improvements) / len(improvements) >= 0.6
```

### C. Tests de Robustez
```python
def test_algorithm_robustness():
    """Evaluar consistencia entre múltiples ejecuciones"""
    results = []
    for seed in range(30):
        algo = Algorithm(seed=seed)
        best = algo.run()
        results.append(best.fitness())
    
    # Coeficiente de variación < 10%
    cv = np.std(results) / np.mean(results)
    assert cv < 0.1
```

## 5. Implementación Propuesta

### Nuevo Framework de Testing
```python
class ModernMetaheuristicTest:
    def __init__(self):
        self.criteria = {
            'convergence': {
                'min_improvement': 0.001,
                'max_stagnation': 0.95,
                'evaluation_window': 10
            },
            'quality': {
                'acceptable_gap': 0.15,
                'min_success_rate': 0.8
            },
            'robustness': {
                'max_cv': 0.1,
                'min_runs': 30
            },
            'flexibility': {
                'allow_degradation': 0.05,
                'degradation_frequency': 0.1
            }
        }
    
    def evaluate_algorithm(self, algo_class, problem, runs=30):
        """Evaluación comprehensiva del algoritmo"""
        results = {
            'quality_scores': [],
            'convergence_speeds': [],
            'robustness_measure': 0,
            'passed_criteria': []
        }
        
        # Multiple runs
        for seed in range(runs):
            algo = algo_class(problem, seed=seed)
            algo.run()
            
            # Collect metrics
            results['quality_scores'].append(algo.best_fitness)
            results['convergence_speeds'].append(
                self._measure_convergence_speed(algo.convergence_curve)
            )
        
        # Statistical analysis
        results['robustness_measure'] = self._calculate_robustness(results)
        results['passed_criteria'] = self._check_all_criteria(results)
        
        return results
```

## 6. Beneficios de los Nuevos Criterios

1. **Realismo**: Reflejan el comportamiento real de metaheurísticas
2. **Flexibilidad**: Permiten diferentes estrategias de búsqueda
3. **Robustez**: Evalúan consistencia estadística
4. **Comparabilidad**: Permiten comparación justa entre algoritmos
5. **Informatividad**: Proporcionan métricas detalladas de rendimiento

## 7. Aplicación a BioAlgoCompare

### Tests Sugeridos para el Proyecto
```python
# tests/unit/test_modern_convergence.py
class TestModernConvergence:
    """Tests diseñados para metaheurísticas modernas"""
    
    def test_statistical_convergence(self, algo_name):
        """Test basado en múltiples ejecuciones"""
        # 30 runs con diferentes seeds
        # Evaluar distribución de resultados
        # Verificar convergencia estadística
    
    def test_adaptive_behavior(self, algo_name):
        """Test de comportamiento adaptativo"""
        # Verificar balance exploración/explotación
        # Evaluar adaptación de parámetros
        # Medir diversidad poblacional
    
    def test_solution_quality(self, algo_name):
        """Test de calidad de solución"""
        # Comparar con bounds conocidos
        # Evaluar consistencia
        # Medir tiempo hasta solución aceptable
```

## Conclusión

Los criterios modernos deben reconocer que las metaheurísticas:
- **No son deterministas**: Requieren análisis estadístico
- **Balancean objetivos múltiples**: Calidad vs tiempo vs robustez
- **Incluyen mecanismos adaptativos**: Que pueden parecer "errores" en tests simples
- **Están diseñadas para problemas difíciles**: Donde el óptimo global es desconocido

Implementar estos criterios resultaría en una evaluación más justa y realista del rendimiento algorítmico.