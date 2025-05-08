# Estrategia de Commits para Organización del Repositorio

## 1. Archivos a modificar en el .gitignore

El actual `.gitignore` necesita actualizaciones para excluir apropiadamente archivos temporales y de resultados. Propongo añadir:

```
# Logs
*.log
benchmark.log
massive_benchmark.log
analyze_massive.log

# Resultados masivos y temporales
results/massive_*/checkpoints/
results/*_parallel_info.json
results/analysis_*
results/statistical_analysis_*
results/benchmark_*
*.json.gz

# Archivos Claude
.claude/
```

## 2. Estructura de Commits

### Commit 1: Actualizar .gitignore y requirements.txt
- Actualizar `.gitignore` para excluir archivos temporales y de resultados
- Actualizar `requirements.txt` con todas las dependencias necesarias

### Commit 2: Agregar módulos principales del sistema de análisis
- `utils/benchmarking.py`: Sistema base de benchmarking
- `utils/statistical_analysis.py`: Herramientas para análisis estadístico
- `utils/vrp_operators.py`: Operadores específicos para VRP
- `utils/fixed_method.py`: Corrección de métodos estadísticos
- `utils/html_generator.py`: Generación de reportes HTML
- `utils/modify_statistical_analysis.py`: Modificaciones para análisis estadístico

### Commit 3: Agregar scripts de análisis
- `analyze_results.py`: Script principal para análisis de resultados
- `analyze_csv.py`: Análisis directo desde archivos CSV
- `fix_report.py`: Correcciones para reportes

### Commit 4: Agregar sistema avanzado de benchmarking (subfolder utils/improved)
- `utils/improved/enhanced_benchmarking.py`: Sistema mejorado de benchmarking
- `utils/improved/advanced_visualization.py`: Visualizaciones avanzadas
- `utils/improved/enhanced_statistics.py`: Estadísticas avanzadas

### Commit 5: Agregar scripts para ejecución masiva de pruebas
- `run_massive.py`: Ejecución de benchmarks masivos
- `analyze_massive.py`: Análisis de resultados masivos
- `analyze_1000runs.py`: Análisis específico para 1000 ejecuciones

### Commit 6: Agregar documentación ampliada
- `CLAUDE.md`: Instrucciones para Claude
- `README_MEJORAS.md`: Documentación de mejoras
- `README_AUDITORIA.md`: Documentación de auditoría

### Commit 7: Agregar documentos de análisis y conclusiones
- `analysis.md`: Notas y análisis general
- `CONCLUSIONES_1000_EJECUCIONES.md`: Conclusiones del análisis de 1000 ejecuciones

## 3. Archivos a Consolidar o Eliminar

### Posibles consolidaciones:
- `analyze_csv.py` y `analyze_results.py` podrían consolidarse, ya que comparten funcionalidad similar.
- `analyze_massive.py` podría integrarse en `run_massive.py` como una función.

### Archivos a considerar para eliminación:
- Resultados temporales en `results/`: Todos los archivos CSV intermedios y JSON de información paralela.
- Archivos de log: `benchmark.log`, `massive_benchmark.log`, `analyze_massive.log`

## 4. Preservación de Datos Importantes

Aunque algunos archivos de resultados no se versionarán, es crucial preservar:
- `results/massive_1000runs/massive_benchmark_summary.csv`: Resumen del benchmark de 1000 ejecuciones
- `results/statistical_analysis_1000runs/algorithm_comparison.csv`: Comparación estadística final
- Archivos HTML de reportes finales

## 5. Consideraciones Futuras

1. Crear una estructura más organizada para los scripts de benchmarking y análisis
2. Implementar un sistema de gestión de datos para resultados experimentales
3. Considerar la migración a un sistema de gestión de experimentos como MLflow
4. Documentar adecuadamente los parámetros y opciones de todos los scripts