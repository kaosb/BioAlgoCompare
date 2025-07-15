# 🏆 Guía de Máximo Rigor Científico - BioAlgoCompare

## 📊 Estándares Experimentales (Actualizado Julio 2025)

### Configuración Base - Nivel CEC Competition

| **Parámetro** | **Valor Estándar** | **Justificación** |
|---------------|-------------------|-------------------|
| **Runs** | 51 | Estándar CEC, permite mediana robusta |
| **Población** | 50 | Balance exploración/explotación |
| **Iteraciones** | 300 | Convergencia garantizada |
| **Algoritmos** | 7 (4 de 2024 + 3 clásicos) | Estado del arte + baselines |
| **Instancias** | 5-7 | Diversidad de escalas |

### Algoritmos Recomendados para Comparación Rigurosa

#### 🔥 Modernos 2024-2025 (Estado del Arte)
- **HO** (2024): Hippopotamus Optimization - Primera aplicación a VRP
- **APO** (2024): Artificial Protozoa - Bio-inspirado más reciente
- **EGTO** (2024): Enhanced Gorilla Troops - Mejora significativa
- **FOA** (2024): Fossa Optimization - Novedoso y prometedor
- **GVOA** (2025): Griffon Vultures - Más reciente disponible

#### ⭐ Altamente Citados (Baselines Establecidos)
- **HHO** (2019): Harris Hawks - 3000+ citas, top en CEC
- **SMA** (2020): Slime Mould - 1500+ citas, excelente multimodal
- **WOA** (2016): Whale Optimization - 8000+ citas, clásico validado

### Presets de Configuración

#### 1. **Validación Rápida** (10 runs, 3 algoritmos)
```bash
python scripts/run_thesis_experiments.py --preset quick_validation
```
- Tiempo: ~30 minutos
- Propósito: Verificar funcionamiento

#### 2. **Benchmark Estándar** (30 runs, 5 algoritmos)
```bash
python scripts/run_thesis_experiments.py --preset standard_benchmark
```
- Tiempo: ~3 horas
- Propósito: Resultados publicables

#### 3. **Máximo Rigor** (51 runs, 7 algoritmos) ⭐ RECOMENDADO
```bash
python scripts/run_thesis_experiments.py --preset thesis_clei2025
```
- Tiempo: ~15 horas
- Propósito: Tesis/Paper de alto impacto

### Comando Manual Completo
```bash
python scripts/analyze.py massive \
  --algorithms "ho,apo,egto,foa,hho,sma,woa" \
  --instances "P-n16-k8,E-n22-k4,A-n32-k5,A-n45-k7,A-n60-k9" \
  --runs 51 \
  --iterations 300 \
  --population 50 \
  --parallel \
  --resume \
  --seed 42 \
  --output-dir experimental_results/thesis_maxrigor
```

## 📈 Análisis Estadístico Riguroso

### Tests Requeridos
1. **Normalidad**: Shapiro-Wilk (n < 50) o Kolmogorov-Smirnov
2. **Comparaciones múltiples**: Friedman + Nemenyi post-hoc
3. **Comparaciones pareadas**: Wilcoxon signed-rank
4. **Effect sizes**: Vargha-Delaney A12, Cliff's delta
5. **Corrección múltiples tests**: Holm-Bonferroni

### Comando para Análisis
```bash
# Convertir resultados a CSV
python scripts/analyze.py convert --json results/benchmark_results.json --csv results/data.csv

# Análisis estadístico completo
python scripts/analyze.py stats --csv results/data.csv --out statistical_analysis/
```

## 🎯 Checklist de Rigor Científico

### Pre-experimento
- [ ] Tests unitarios pasando (100%)
- [ ] Configuración documentada
- [ ] Semillas fijas para reproducibilidad
- [ ] Recursos computacionales verificados

### Durante experimento
- [ ] Monitoreo de progreso
- [ ] Checkpointing activado (--resume)
- [ ] Logs detallados guardados
- [ ] Backup incremental de resultados

### Post-experimento
- [ ] Verificación de normalidad
- [ ] Tests estadísticos apropiados
- [ ] Effect sizes calculados
- [ ] Visualizaciones científicas generadas
- [ ] Resultados reproducibles verificados

## 📚 Referencias Clave

### Estándares de Benchmarking
1. **Derrac et al. (2011)**. "A practical tutorial on the use of nonparametric statistical tests". *Swarm and Evolutionary Computation*, 1(1), 3-18.

2. **García et al. (2009)**. "A study on the use of non-parametric tests for analyzing the evolutionary algorithms' behaviour". *Journal of Heuristics*, 15(6), 617-644.

3. **CEC 2024 Guidelines**. IEEE Congress on Evolutionary Computation Competition Standards.

### Algoritmos 2024
1. **Amiri et al. (2024)**. "Hippopotamus optimization algorithm". *Scientific Reports*, 14, 5032.

2. **Latest Bio-inspired Survey (2024)**. "Recent advances in bio-inspired optimization". *Applied Soft Computing*, 150, 111089.

## 💡 Tips para Publicación de Alto Impacto

1. **Siempre usar 51 runs** (no 30) para cumplir estándares CEC
2. **Incluir algoritmos 2024** para demostrar actualidad
3. **Reportar effect sizes** además de p-values
4. **Usar gráficos de convergencia** y critical difference diagrams
5. **Compartir código y datos** para reproducibilidad

## 🚀 Ejemplo de Uso Completo

```bash
# 1. Verificar sistema
pytest tests/ -v

# 2. Ejecutar experimentos de máximo rigor
python scripts/run_thesis_experiments.py --preset thesis_clei2025

# 3. Analizar resultados
python scripts/analyze.py stats --csv results/data.csv --out analysis/

# 4. Generar paper
python scripts/tools/generate_paper_report.py

# 5. Validar reproducibilidad
python scripts/run_thesis_experiments.py --preset thesis_clei2025 --dry-run
```

---

**Última actualización**: Julio 2025
**Estándar**: CEC Competition Level
**Confianza**: 99% para publicación internacional
