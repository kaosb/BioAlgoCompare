# 📖 BioAlgoCompare - Referencia Completa de Comandos

> Documento centralizado con todos los comandos esenciales para usar BioAlgoCompare de manera profesional y rigurosa.

## 📑 Índice

1. [Comandos Básicos](#comandos-básicos)
2. [Benchmarking Comparativo](#benchmarking-comparativo)
3. [Benchmarking Masivo](#benchmarking-masivo)
4. [Análisis Estadístico](#análisis-estadístico)
5. [Comandos para Paper Académico](#comandos-para-paper-académico)
6. [Solución de Problemas](#solución-de-problemas)
7. [Comandos de Desarrollo](#comandos-de-desarrollo)

---

## 🚀 Comandos Básicos

### Ejecutar un Algoritmo Individual

```bash
# Ejecución simple
python scripts/analyze.py run --algorithm hoa --instance A-n32-k5

# Con parámetros específicos
python scripts/analyze.py run \
    --algorithm egto \
    --instance E-n51-k5 \
    --iterations 300 \
    --population 50 \
    --runs 10 \
    --seed 42
```

### Ejecutar Todos los Algoritmos

```bash
# En una instancia específica
python scripts/analyze.py run --algorithm all --instance P-n16-k8

# Con ejecución paralela
python scripts/analyze.py run --algorithm all --instance E-n22-k4 --parallel
```

### Algoritmos Disponibles

| Código | Nombre Completo | Año | Categoría |
|--------|----------------|-----|-----------|
| `woa` | Whale Optimization Algorithm | 2016 | Mamíferos marinos |
| `rro` | Raven Roosting Optimization | 2016 | Aves |
| `sho`/`hoa` | Spotted Hyena Optimizer | 2017 | Mamíferos terrestres |
| `ewa` | Earthworm Algorithm | 2018 | Invertebrados |
| `hho` | Harris Hawks Optimization | 2019 | Aves rapaces |
| `mrfo` | Manta Ray Foraging Optimization | 2020 | Peces |
| `sma` | Slime Mould Algorithm | 2020 | Microorganismos |
| `gto` | Gorilla Troops Optimization | 2021 | Primates |
| `opa` | Orca Predator Algorithm | 2021 | Mamíferos marinos |
| `fsa`/`fgo` | Flamingo Search Algorithm | 2021 | Aves |
| `aha` | Artificial Hummingbird Algorithm | 2022 | Aves |
| `smo` | Starling Murmuration Optimizer | 2022 | Comportamiento colectivo |
| `apo` | Artificial Protozoa Optimizer | 2024 | Microorganismos |
| `foa` | Fossa Optimization Algorithm | 2024 | Mamíferos |
| `egto` | Enhanced Gorilla Troops Optimization | 2024 | Primates mejorado |
| `gvoa` | Griffon Vultures Optimization Algorithm | 2025 | Aves |

---

## 📊 Benchmarking Comparativo

### Benchmark Estándar (30+ runs)

```bash
# Comparar algoritmos específicos
python scripts/analyze.py benchmark --run-benchmark \
    --instances "E-n22-k4,P-n16-k8" \
    --algorithms "hoa,foa,egto" \
    --runs 30 \
    --iterations 100 \
    --population 40 \
    --seed 42 \
    --parallel

# Comparar todos los algoritmos
python scripts/analyze.py benchmark --run-benchmark \
    --instances "A-n32-k5,E-n22-k4,P-n16-k8" \
    --algorithms "all" \
    --runs 30 \
    --parallel
```

### Analizar Resultados Existentes

```bash
# Desde archivo CSV
python scripts/analyze.py benchmark --input results/benchmark_results.csv

# Desde archivo JSON
python scripts/analyze.py benchmark --input results/benchmark_20250709.json
```

---

## 🔬 Benchmarking Masivo

### Ejecución Masiva (1000+ runs)

```bash
# Algoritmos específicos con todas las instancias principales
python scripts/run_massive.py \
    --runs 1000 \
    --algorithm gvoa \
    --algorithm smo \
    --instances A-n32-k5 \
    --instances B-n31-k5 \
    --instances E-n22-k4 \
    --instances E-n51-k5 \
    --instances P-n16-k8 \
    --iterations 100 \
    --population 40 \
    --seed 42 \
    --parallel \
    --resume \
    --output-dir results/gvoa_smo_benchmark_$(date +%Y%m%d_%H%M%S)

# Todos los algoritmos en instancias específicas
python scripts/run_massive.py \
    --runs 1000 \
    --algorithm all \
    --instances E-n22-k4 P-n16-k8 A-n32-k5 \
    --parallel \
    --resume
```

### Benchmark con Instancias Solomon

```bash
# Instancias Solomon para problemas con ventanas de tiempo
python scripts/run_massive.py \
    --runs 1000 \
    --algorithm egto \
    --algorithm foa \
    --algorithm woa \
    --algorithm hho \
    --algorithm mrfo \
    --algorithm sma \
    --instances Solomon/C101 \
    --instances Solomon/R101 \
    --instances Solomon/RC101 \
    --iterations 100 \
    --population 40 \
    --seed 42 \
    --parallel
```

---

## 📈 Análisis Estadístico

### Análisis Estadístico Completo

```bash
# Análisis avanzado con tests de Friedman y Nemenyi
python scripts/analyze.py stats \
    --csv results/massive_benchmark_summary.csv \
    --out results/statistical_analysis

# Análisis desde directorio de benchmark
python scripts/analyze.py stats \
    --csv results/gvoa_smo_benchmark_*/massive_benchmark_summary.csv \
    --out results/paper_statistical_analysis
```

### Análisis de CSV con Visualizaciones

```bash
# Generar todas las visualizaciones
python scripts/analyze.py analyze-csv results/benchmark_results.csv

# Con opciones específicas
python scripts/analyze.py analyze-csv results/benchmark_results.csv \
    --output-dir results/analysis_visualizations
```

---

## 📝 Comandos para Paper Académico

### Benchmark para Publicación (8 algoritmos representativos)

```bash
# Selección estratégica de algoritmos por año y categoría
python scripts/run_massive.py \
    --runs 1000 \
    --algorithm woa \
    --algorithm hho \
    --algorithm sma \
    --algorithm gto \
    --algorithm aha \
    --algorithm smo \
    --algorithm foa \
    --algorithm gvoa \
    --instances A-n32-k5 \
    --instances B-n31-k5 \
    --instances E-n22-k4 \
    --instances E-n51-k5 \
    --instances P-n16-k8 \
    --iterations 100 \
    --population 40 \
    --seed 42 \
    --parallel \
    --resume \
    --output-dir results/paper_benchmark_$(date +%Y%m%d_%H%M%S)
```

### Comparación de Algoritmos Novedosos (2024-2025)

```bash
# Los 4 más recientes
python scripts/run_massive.py \
    --runs 1000 \
    --algorithm apo \
    --algorithm foa \
    --algorithm egto \
    --algorithm gvoa \
    --instances A-n32-k5 B-n31-k5 E-n22-k4 E-n51-k5 P-n16-k8 \
    --iterations 100 \
    --population 40 \
    --seed 42 \
    --parallel \
    --resume \
    --output-dir results/novel_algorithms_benchmark_$(date +%Y%m%d_%H%M%S)
```

### Generar Figuras para Publicación

```bash
# Figuras en formato PDF de alta calidad
python scripts/analyze.py analyze-csv results/paper_benchmark_summary.csv \
    --publication-ready \
    --format pdf \
    --dpi 600 \
    --output-dir results/publication_figures

# Tablas LaTeX
python scripts/analyze.py analyze-csv results/paper_benchmark_summary.csv \
    --export-tables latex \
    --output-dir results/publication_tables
```

---

## 🔧 Solución de Problemas

### Errores Comunes y Soluciones

#### Error: "No such file or directory" con instancias Solomon

**Problema**: Rutas con `/` causan problemas en nombres de archivo.
**Solución**: Ya corregido en `enhanced_benchmarking.py`

#### Error: Confirmación manual en ejecuciones masivas

**Problema**: Script pide confirmación para >10,000 runs.
**Solución**: Modificado para ejecución automática.

#### Error: ImportError o ModuleNotFoundError

```bash
# Asegurar que el directorio actual esté en PYTHONPATH
export PYTHONPATH=./:$PYTHONPATH

# O ejecutar con
PYTHONPATH=./ python scripts/analyze.py ...
```

### Verificar Instalación

```bash
# Verificar dependencias
pip list | grep -E "numpy|pandas|matplotlib|scipy|click"

# Reinstalar si es necesario
pip install -r requirements.txt
```

---

## 🛠️ Comandos de Desarrollo

### Testing

```bash
# Ejecutar todos los tests
pytest --cov=algorithms --cov=problems --cov=utils --cov=scripts

# Test específico
pytest tests/unit/test_algorithm_convergence.py -v

# Tests rápidos (sin los marcados como slow)
pytest -k "not slow"
```

### Linting y Formato

```bash
# Verificar código con ruff
ruff check .

# Corregir automáticamente
ruff check --fix .

# Formatear código
ruff format .
```

### Generación de Documentación

```bash
# Compilar papers académicos
make -C docs/papers all

# Solo paper CISTI v2
make -C docs/papers cisti_v2

# Limpiar archivos LaTeX temporales
make -C docs/papers clean
```

### Git Workflow

```bash
# Crear nueva rama para característica
git checkout -b feature/nueva-mejora

# Después de cambios
git add .
git commit -m "feat: descripción de la mejora"

# Push y crear PR
git push origin feature/nueva-mejora
```

---

## 💡 Tips y Mejores Prácticas

### Para Mejores Resultados

1. **Población**: 
   - Instancias pequeñas (≤30 nodos): 30-40
   - Instancias medianas (30-50 nodos): 40-50
   - Instancias grandes (>50 nodos): 50-100

2. **Iteraciones**:
   - Pruebas rápidas: 100
   - Benchmarks estándar: 100-200
   - Resultados finales: 500+

3. **Runs**:
   - Pruebas exploratorias: 5-10
   - Análisis estadístico básico: 30+
   - Publicación científica: 1000+

### Reproducibilidad

```bash
# Siempre usar semilla fija
--seed 42

# Documentar entorno
pip freeze > requirements_experiment.txt

# Guardar comando exacto
echo "COMANDO_USADO" > experiment_command.txt

# Información del sistema
uname -a > system_info.txt
lscpu > cpu_info.txt
```

### Rendimiento

```bash
# Para ejecuciones largas, usar screen o tmux
screen -S benchmark
python scripts/run_massive.py ... # comando largo
# Ctrl+A, D para desconectar
# screen -r benchmark para reconectar

# Monitorear progreso
tail -f results/*/benchmark_state.json
```

---

## 📚 Referencias Adicionales

- [README Principal](../README.md) - Visión general del proyecto
- [Guía de Benchmarking](guides/benchmarking.md) - Detalles sobre metodología
- [Análisis Estadístico](scientific/statistical_analysis.md) - Teoría estadística
- [Arquitectura](technical/architecture.md) - Diseño del sistema

---

*Última actualización: Julio 2025*
*Versión: 1.0*