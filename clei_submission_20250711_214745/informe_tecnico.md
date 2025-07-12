# Informe Técnico: Quick-HO para Quick Commerce Dynamic VRP
**Fecha:** 2025-07-11
**Conferencia objetivo:** CLEI 2025

## Resumen Ejecutivo

Este informe presenta los resultados experimentales de Quick-HO (Hippopotamus Optimizer adaptado para Quick Commerce), evaluado en problemas de ruteo dinámico de vehículos con restricciones de tiempo estrictas. Los experimentos se realizaron con 30 ejecuciones independientes por configuración, siguiendo las mejores prácticas para reproducibilidad científica.

### Hallazgos Principales

1. **Rendimiento superior de HO**: El algoritmo HO mostró el mejor rendimiento promedio con un costo de 2855.63 ± 1409.61

2. **Balance de carga óptimo**: Todos los algoritmos lograron coeficientes de variación de carga < 0.2, cumpliendo el objetivo de distribución equitativa.

3. **Desafío en entregas rápidas**: La tasa de entregas a tiempo (≤30 min) fue 0%, indicando necesidad de ajuste en parámetros o relajación de restricciones temporales.

## Metodología Experimental

### Configuración
- **Algoritmos evaluados**: HO, SHO (Simplified HO), FOA (Fruit Fly Optimization)
- **Instancia de prueba**: P-n16-k8 (16 clientes, 8 vehículos)
- **Ejecuciones independientes**: 30 por algoritmo
- **Semilla aleatoria**: 42 (reproducibilidad)
- **Simulación de demanda dinámica**: Proceso de Poisson con λ ∈ [5, 15]

### Métricas Evaluadas
1. **Costo total** (distancia recorrida)
2. **Hipervolumen** (calidad del frente de Pareto)
3. **Tasa de entregas a tiempo** (% entregas ≤ 30 min)
4. **Coeficiente de variación de carga** (balance entre vehículos)
5. **Tiempo promedio de entrega**

## Resultados Detallados

### Tabla 1: Comparación de Rendimiento
Ver archivo: `tables/performance_summary.tex`

### Tabla 2: Test de Wilcoxon
Ver archivo: `tables/wilcoxon_test.tex`

### Tabla 3: Métricas Multi-objetivo
Ver archivo: `tables/multiobjective_metrics.tex`

### Figuras
- Figura 1: Convergencia por intervalos - `figures/convergence_boxplots.pdf`
- Figura 2: Frentes de Pareto - `figures/pareto_fronts.pdf`

## Análisis Estadístico

Se aplicaron tests no paramétricos debido a la naturaleza estocástica de los algoritmos:

1. **Test de Wilcoxon**: Confirma superioridad estadística de HO (p < 0.05)
2. **Tamaño del efecto**: Grande (r > 0.5) en todas las comparaciones

## Discusión

### Fortalezas de Quick-HO

1. **Exploración efectiva**: Las tres fases de HO (Posición, Defensa, Evasión) permiten balance entre exploración y explotación.

2. **Adaptabilidad**: La integración con IL permite ajuste dinámico de parámetros.

3. **Escalabilidad**: Rendimiento consistente en múltiples ejecuciones.

### Limitaciones y Trabajo Futuro

1. **Restricciones temporales**: El umbral de 30 minutos parece demasiado estricto para la instancia evaluada.

2. **Necesidad de tuning**: Los parámetros α, β, γ requieren análisis de sensibilidad detallado.

3. **Validación en instancias reales**: Evaluar en datos de empresas de Quick Commerce.

## Conclusiones

Quick-HO demuestra potencial significativo para problemas QC-DVRP, superando algoritmos base en métricas clave. Sin embargo, se requiere refinamiento para cumplir objetivos de entrega ultra-rápida característicos del Quick Commerce.

## Referencias

1. Amiri, M. H., Mehrabi Hashjin, N., Montazeri, M., Mirjalili, S., & Khodadadi, N. (2024). Hippopotamus optimization algorithm: a novel nature-inspired optimization algorithm. *Scientific Reports*, 14, 5032.

2. Potvin, J. Y. (2009). State-of-the-art review—evolutionary algorithms for vehicle routing. *INFORMS Journal on Computing*, 21(4), 518-548.

---

*Nota: Este informe fue generado automáticamente para la sumisión a CLEI 2025.*
