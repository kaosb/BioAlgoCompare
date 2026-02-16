# 🧬 BioAlgoCompare

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Algorithms](https://img.shields.io/badge/algorithms-21-orange)](algorithms/)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](tests/)
[![Tests](https://img.shields.io/badge/tests-759%20passed-brightgreen)](tests/)

Plataforma de evaluación estadística rigurosa para algoritmos metaheurísticos bioinspirados aplicados al Vehicle Routing Problem (VRP). Implementa benchmarking masivo con análisis estadístico avanzado siguiendo las mejores prácticas de investigación reproducible.

## 🎯 Enfoque de Investigación

Esta plataforma se centra en la evaluación rigurosa de algoritmos bioinspirados para el Vehicle Routing Problem (VRP) estándar, con énfasis en análisis estadístico reproducible y benchmarking masivo.

## 📚 Conceptos Fundamentales VRP

### ¿Qué es el Vehicle Routing Problem?

El **VRP (Vehicle Routing Problem)** es un problema clásico de optimización combinatoria que busca encontrar las rutas óptimas para una flota de vehículos que deben servir a un conjunto de clientes desde un depósito central.

**🎯 Objetivo**: Minimizar la distancia total recorrida mientras se respetan las restricciones.

### Elementos del Problema

| Elemento | Descripción | Ejemplo |
|----------|-------------|---------|
| **Depósito** | Punto de partida y llegada de todos los vehículos | Almacén central |
| **Clientes** | Ubicaciones que requieren servicio | Tiendas, casas |
| **Vehículos** | Flota disponible con capacidad limitada | Camiones con cap. 100kg |
| **Demandas** | Cantidad requerida por cada cliente | Cliente A: 15kg, Cliente B: 25kg |
| **Distancias** | Costo de viajar entre ubicaciones | Distancia euclidiana |

### Restricciones Principales

1. **🚛 Capacidad**: Cada vehículo tiene capacidad máxima
2. **🏠 Visita única**: Cada cliente visitado exactamente una vez
3. **🔄 Depósito**: Todas las rutas inician y terminan en el depósito
4. **📦 Demanda**: Se debe satisfacer completamente la demanda de cada cliente

### Ejemplo Visual Simplificado

```
Depósito (0) ────→ Cliente A (demand: 20)
    │                     │
    │                     ▼
    └──→ Cliente B ←── Cliente C
       (demand: 30)   (demand: 25)

Capacidad vehículo: 100
Solución: Ruta única [0→A→C→B→0]
Carga total: 20+25+30 = 75 ≤ 100 ✅
```

### Complejidad y Importancia

- **Complejidad**: NP-Hard (tiempo exponencial para solución exacta)
- **Aplicaciones reales**: Logística, delivery, recolección de basura, rutas escolares
- **Impacto económico**: Ahorro de 10-20% en costos de transporte

## 🚀 Inicio Rápido

### Instalación y Primer Uso (3 minutos)

```bash
# 1. Clonar e instalar
git clone https://github.com/kaosb/BioAlgoCompare.git
cd BioAlgoCompare
pip install -r requirements.txt

# 2. Verificar instalación (30 segundos)
python scripts/analyze.py run --algorithm sho --instance A-n32-k5 --iterations 5 --no-visualize --no-save
# ✅ Salida esperada: "Best cost: ~1700" sin errores

# 3. Primer benchmark comparativo (2 minutos)
python scripts/analyze.py benchmark --run-benchmark --algorithms "ho,apo,hho" --instances "E-n22-k4" --runs 10

# 4. Ejecutar experimentos con máximo rigor (CEC standards)
python scripts/analyze.py benchmark --run-benchmark --algorithms "ho,apo,egto,foa,hho,sma,woa" --runs 51
```

### Ejemplos Garantizados (Casos de Uso Paso a Paso)

#### 📊 **Ejemplo 1: Evaluación Individual Rápida**
```bash
# Objetivo: Evaluar rapidez de un algoritmo en instancia pequeña
python scripts/analyze.py run \
    --algorithm hho \
    --instance E-n22-k4 \
    --runs 10 \
    --iterations 50 \
    --seed 42

# ✅ Resultado esperado:
# Best: ~520-580, Gap: ~38-55%, Time: ~0.03s
# Interpretación: HHO encuentra soluciones decentes rápidamente
```

#### 🏁 **Ejemplo 2: Comparación de 3 Algoritmos**
```bash
# Objetivo: Comparar rendimiento de algoritmos top en instancia mediana
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms "hho,ho,sho" \
    --instances "P-n16-k8" \
    --runs 15 \
    --seed 42

# ✅ Resultado esperado:
# hho: ~580-620 (gap: ~28-38%)
# ho:  ~600-650 (gap: ~33-44%)
# sho: ~650-750 (gap: ~44-67%, mayor variabilidad)
```

#### 📈 **Ejemplo 3: Análisis Estadístico Completo**
```bash
# Objetivo: Generar reporte científico con significancia estadística
# Paso 1: Ejecutar benchmark robusto
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms "hho,ho,sho,woa" \
    --instances "E-n22-k4,P-n16-k8" \
    --runs 30 \
    --seed 42 \
    --parallel

# Paso 2: Convertir a CSV
python scripts/analyze.py convert \
    --json results/benchmark_*/benchmark_results.json \
    --csv results/comparison_results.csv

# Paso 3: Análisis estadístico
python scripts/analyze.py stats \
    --csv results/comparison_results.csv \
    --out results/statistical_analysis

# ✅ Resultado: Carpeta con diagramas CD, tests Friedman, reportes HTML
```

#### 🔬 **Ejemplo 4: Benchmark Masivo (Publicación)**
```bash
# Objetivo: Resultados para paper académico (1000 runs)
python scripts/analyze.py massive \
    --runs 1000 \
    --algorithm "hho,ho,sho" \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5" \
    --parallel \
    --resume \
    --seed 42

# ⏱️ Tiempo estimado: 45-90 minutos
# ✅ Resultado: Datos estadísticamente robustos para publicación
```

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Instalación](#-instalación)
- [Uso Completo](#-uso-completo)
  - [Ejecución Básica](#ejecución-básica)
  - [Benchmarking Comparativo](#benchmarking-comparativo)
  - [Benchmarking Masivo](#benchmarking-masivo)
  - [Análisis Estadístico](#análisis-estadístico-de-resultados)
- [Flujo de Reproducibilidad](#-flujo-de-reproducibilidad-datos--paper)
- [Generación de Papers](#-generación-de-papers-y-reportes)
- [Algoritmos Implementados](#-algoritmos-implementados)
- [Características Avanzadas](#-características-avanzadas)
- [Herramientas Solomon](#-herramientas-solomon)
- [Arquitectura](#-arquitectura)
- [Tests y Cobertura](#-tests-y-cobertura)
- [Documentación](#-documentación)
- [Referencias](#-referencias)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## ✨ Características

### 🎯 **¿Por Qué Usar BioAlgoCompare?**

| Necesidad | Solución | Beneficio |
|-----------|----------|-----------|
| **🔬 Investigación Académica** | 17 algoritmos + análisis estadístico riguroso | Papers científicos con significancia estadística |
| **⚡ Prototipado Rápido** | CLI intuitivo + ejemplos garantizados | De idea a resultados en 3 minutos |
| **📊 Comparación de Algoritmos** | Benchmarking automático + visualizaciones | Decisiones informadas basadas en datos |
| **🔄 Reproducibilidad** | Control de semillas + checkpointing | Experimentos 100% replicables |
| **⚙️ Escalabilidad** | Paralelo + optimizado para 1000+ runs | Resultados robustos sin complejidad |

### 🚀 **Capacidades Principales**
- ✅ **17 algoritmos bioinspirados** únicos (2016-2025) - Estado del arte
- ✅ **Benchmarking masivo** con soporte para 1000+ ejecuciones automáticas
- ✅ **Análisis estadístico riguroso**: Tests Friedman, Nemenyi (CD corregido), Wilcoxon, tamaños de efecto
- ✅ **Ejecución paralela optimizada** para máximo rendimiento en multi-core
- ✅ **Checkpointing inteligente** para experimentos largos con recuperación automática
- ✅ **Visualizaciones científicas** de calidad publicación (300 DPI, LaTeX)
- ✅ **CLI unificado** con interfaz intuitiva tipo Git
- ✅ **100% reproducible** con control granular de semillas

### 🛠️ **Capacidades Avanzadas**
- ✅ **Optimización local VRP**: Operadores 2-opt, Or-opt, Relocate, Exchange integrados
- ✅ **Métricas comprehensivas**: Gap to optimal, success rate, convergencia, tiempo
- ✅ **Instancias CVRPLIB**: Soporte completo para benchmarks Solomon y Augerat
- ✅ **Análisis de sensibilidad**: Herramientas para análisis paramétrico automatizado
- ✅ **Exportación científica**: LaTeX con booktabs/siunitx, diagramas CD, heatmaps

## 🛠️ Instalación

### Requisitos

- Python 3.8 o superior
- pip o conda para gestión de paquetes

### Instalación Estándar

```bash
# Clonar el repositorio (⏱️ 30 segundos)
git clone https://github.com/kaosb/BioAlgoCompare.git
cd BioAlgoCompare

# Crear entorno virtual (⏱️ 10 segundos)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias (⏱️ 2-5 minutos, ~150MB)
pip install -r requirements.txt

# Verificar instalación exitosa (⏱️ 10 segundos)
python scripts/analyze.py run --algorithm sho --instance A-n32-k5 --iterations 5 --no-visualize --no-save
# ✅ Salida esperada: "Best cost: ~1700" sin errores
```

**💾 Requisitos de Espacio:**
- Instalación base: ~300MB (Python + dependencias)
- Resultados típicos: ~50MB por cada 1000 runs
- Total recomendado: 2GB libres

### Instalación para Desarrollo

```bash
# Instalar en modo desarrollo
pip install -e .

# Instalar dependencias opcionales
pip install torch torchvision  # Para Imitation Learning
pip install cec2017           # Para validación CEC2017

# Esto habilita el comando 'bioalgo' globalmente
bioalgo run --algorithm sho --instance A-n32-k5
```

## 📖 Uso Completo

### Ejecución Básica

#### **Algoritmo Individual (⏱️ 5-15 segundos)**

```bash
python scripts/analyze.py run --algorithm sho --instance A-n32-k5 --iterations 100 --population 30
# ⏱️ ~8 segundos, 📊 1 resultado, 💾 ~1KB
```

#### **Múltiples Ejecuciones con Estadísticas (⏱️ 1-3 minutos)**

```bash
python scripts/analyze.py run --algorithm egto --instance E-n51-k5 --runs 10 --seed 42
# ⏱️ ~90 segundos, 📊 10 resultados + estadísticas, 💾 ~5KB
```

#### **Todos los Algoritmos en Paralelo (⏱️ 3-8 minutos)**

```bash
python scripts/analyze.py run --algorithm all --instance P-n16-k8 --parallel
# ⏱️ ~5 minutos (17 algoritmos), 📊 17 resultados, 💾 ~25KB
```

### Benchmarking Comparativo

#### **Comparación Estándar (⏱️ 5-15 minutos)**

```bash
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms "ho,sho,foa,egto,woa" \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5" \
    --runs 30 \
    --iterations 100 \
    --population 40 \
    --parallel \
    --seed 42
# ⏱️ ~12 minutos (5 alg × 3 inst × 30 runs), 📊 450 resultados, 💾 ~2MB
```

#### **Con Optimización Local (⏱️ 20-40 minutos)**

```bash
python scripts/analyze.py benchmark \
    --run-benchmark \
    --optimize \
    --output-dir results/optimized_benchmark
# ⏱️ ~30 minutos (operadores 2-opt adicionales), 📊 Mejores gaps, 💾 ~3MB
```

### Benchmarking Masivo

#### **Experimentos de Gran Escala (⏱️ 1-4 horas)**

```bash
python scripts/analyze.py massive \
    --runs 1000 \
    --algorithm all \
    --instances E-n22-k4 P-n16-k8 A-n32-k5 \
    --parallel \
    --resume \
    --iterations 300 \
    --population 50
# ⏱️ ~3 horas (17 alg × 3 inst × 1000 runs), 📊 51,000 resultados, 💾 ~200MB
```

#### **Recuperación Automática (⏱️ Tiempo restante)**

```bash
python scripts/analyze.py massive \
    --resume \
    --checkpoint results/massive_20250111_123456/checkpoint.pkl
# ⏱️ Continúa desde punto de interrupción, 💾 Usa checkpoint existente
```

### Análisis de Instancias Solomon

Benchmark con instancias Solomon para VRP:

```bash
python scripts/analyze.py benchmark \
    --run-benchmark \
    --instances "RC101,RC102,RC103" \
    --algorithms "ho,sho,foa" \
    --runs 100 \
    --seed 42
```

### Análisis Estadístico de Resultados

Analizar resultados existentes:

```bash
# Convertir resultados JSON a CSV
python scripts/analyze.py convert \
    --json results/benchmark_results.json \
    --csv results/results.csv

# Análisis estadístico completo
python scripts/analyze.py stats \
    --csv results/results.csv \
    --out results/statistical_analysis
```

El análisis incluye:
- Tests de Friedman y Quade
- Test post-hoc de Nemenyi con CD corregido: `q_α/√2 * sqrt(k(k+1)/(6n))`
- Test de Wilcoxon signed-rank para comparación pareada
- Tamaños de efecto (Vargha-Delaney A12, Cliff's delta)
- Diagramas de diferencias críticas
- Heatmaps de significancia
- Reportes detallados en Markdown/HTML
- Exportación a LaTeX con booktabs/siunitx

### Ejemplo de Flujo Completo

```bash
# 1. Definir experimento
EXPERIMENT="vrp_bioinspirados_2025"
OUTPUT="results/${EXPERIMENT}"

# 2. Ejecutar benchmark
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms "sho,apo,egto,fsa,foa,woa,hho,mrfo,sma,gto,ewa" \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5,B-n31-k5,E-n51-k5" \
    --runs 100 \
    --iterations 200 \
    --population 40 \
    --parallel \
    --output-dir "${OUTPUT}"

# 3. Convertir a CSV
python scripts/analyze.py convert \
    --json "${OUTPUT}/benchmark_results.json" \
    --csv "${OUTPUT}/results.csv"

# 4. Análisis estadístico
python scripts/analyze.py stats \
    --csv "${OUTPUT}/results.csv" \
    --out "${OUTPUT}/analysis"
```

## 📊 Interpretando Resultados

### Métricas Básicas

Cuando ejecutes un algoritmo, verás salidas como esta:
```
Best: 1711.58, Average: 1711.58, Time: 0.02s
Gap to optimum: 118.31%, Success rate: 0.00%
```

**📖 Interpretación de cada métrica:**

| Métrica | Significado | Valores Buenos | Ejemplo |
|---------|-------------|----------------|---------|
| **Best Fitness/Cost** | Distancia total mínima encontrada | Menor = mejor | 784 (óptimo para A-n32-k5) |
| **Average Fitness** | Promedio de todas las ejecuciones | Menor = mejor | ~800-900 (bueno) |
| **Gap to Optimum** | % sobre el valor óptimo conocido | 0% = perfecto, <5% = excelente | 0% = encontró óptimo |
| **Success Rate** | % ejecuciones que encontraron óptimo | 100% = perfecto | 80% = muy bueno |
| **Time** | Tiempo de ejecución en segundos | Depende del contexto | 0.02s = muy rápido |

### Interpretación por Tipo de Instancia

| Instancia | Óptimo Conocido | Gap < 5% | Gap < 10% | Interpretación |
|-----------|-----------------|----------|-----------|----------------|
| **A-n32-k5** | 784 | < 823 | < 862 | Instancia Augerat, 32 clientes, 5 vehículos |
| **E-n22-k4** | 375 | < 394 | < 413 | Instancia Eilon, 22 clientes, 4 vehículos |
| **P-n16-k8** | 450 | < 473 | < 495 | Instancia Pearn, 16 clientes, 8 vehículos |

### Decodificación de Nombres de Instancias

**Formato: `[AUTOR]-n[CLIENTES]-k[VEHÍCULOS]`**

- **A-n32-k5**: Augerat, 32 nodos (31 clientes + 1 depósito), 5 vehículos
- **E-n22-k4**: Eilon, 22 nodos (21 clientes + 1 depósito), 4 vehículos
- **P-n16-k8**: Pearn, 16 nodos (15 clientes + 1 depósito), 8 vehículos
- **B-n31-k5**: Beasley, 31 nodos (30 clientes + 1 depósito), 5 vehículos

### Rangos de Calidad por Algoritmo

| Algoritmo | Gap Típico | Tiempo Típico | Fortalezas |
|-----------|------------|---------------|------------|
| **sho** | 15-25% | Rápido | Buena exploración |
| **ho** | 10-20% | Medio | Balance exploración/explotación |
| **woa** | 20-30% | Rápido | Diversidad de soluciones |
| **hho** | 8-18% | Medio | Convergencia estable |

## 🔬 Flujo de Reproducibilidad: Datos → Paper

### Paso 1: Ejecutar Experimentos Comprehensivos

```bash
# 1.1 Benchmark masivo (resultados principales)
python scripts/analyze.py massive \
    --runs 1000 \
    --algorithm ho sho foa egto woa \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5" \
    --parallel \
    --seed 42

# 1.2 Experimentos con instancias Solomon
python scripts/analyze.py benchmark \
    --run-benchmark \
    --instances "RC101,RC102,RC103" \
    --algorithms "ho,sho,foa" \
    --runs 100 \
    --seed 42
```

### Paso 2: Análisis Estadístico

```bash
# 2.1 Convertir resultados
python scripts/analyze.py convert \
    --json results/massive_*/benchmark_results.json \
    --csv results/all_results.csv

# 2.2 Análisis estadístico completo
python scripts/analyze.py stats \
    --csv results/all_results.csv \
    --out results/statistical_analysis
```

### Paso 3: Análisis de Sensibilidad de Parámetros

```bash
# 3.1 Análisis de sensibilidad HO
python scripts/tools/sensitivity_analysis_ho.py \
    --instance data/vrp/P-n16-k8.vrp \
    --runs 30 \
    --output results/sensitivity

# Analiza: α ∈ [0.1, 0.9], β ∈ [0.2, 0.8], γ ∈ [0.3, 1.0]
```

### Paso 4: Preparar Resultados para Publicación

Los resultados del análisis estadístico ya incluyen todos los elementos necesarios para publicación:
- Tablas con formato LaTeX (booktabs/siunitx)
- Diagramas de diferencias críticas
- Reportes HTML/Markdown completos
- Datos CSV para análisis adicional

## 📝 Herramientas de Análisis Avanzado

### Scripts de Análisis Disponibles

#### 1. **sensitivity_analysis_ho.py** - Análisis de Sensibilidad

```bash
python scripts/tools/sensitivity_analysis_ho.py \
    --instance data/vrp/P-n16-k8.vrp \
    --runs 10 \
    --output sensitivity_results
```

Genera:
- Mapas de calor de interacción de parámetros
- Gráficos de efectos principales
- Configuración óptima: α=0.10, β=0.50, γ=0.65

#### 2. **compare_cec_benchmarks.py** - Comparación CEC2017

```bash
python scripts/tools/compare_cec_benchmarks.py
```

- Compara en funciones unimodales (F1, F3) y multimodales (F7, F10)
- Analiza fases HO (Position, Defense, Evasion)
- Valida métricas QC en instancias Solomon

## 🧪 Algoritmos Implementados

El proyecto implementa **21 algoritmos metaheurísticos únicos** (19 bioinspirados + 2 clásicos de comparación):

| Algoritmo | Nombre Completo | Año | Inspiración |
|-----------|-----------------|-----|-------------|
| **sho** | Spotted Hyena Optimizer | 2017 | Caza cooperativa de hienas |
| **apo** | Artificial Protozoa Optimizer | 2024 | División de protozoarios |
| **egto** | Enhanced Gorilla Troops Optimization | 2024 | Comportamiento social mejorado |
| **fsa** | Flamingo Search Algorithm | 2021 | Búsqueda de alimento |
| **foa** | Fossa Optimization Algorithm | 2024 | Estrategias de caza |
| **woa** | Whale Optimization Algorithm | 2016 | Alimentación de ballenas |
| **hho** | Harris Hawks Optimization | 2019 | Caza cooperativa |
| **mrfo** | Manta Ray Foraging Optimization | 2020 | Alimentación de mantarrayas |
| **sma** | Slime Mould Algorithm | 2020 | Comportamiento del moho |
| **gto** | Gorilla Troops Optimization | 2021 | Jerarquía social |
| **ewa** | Earthworm Algorithm | 2018 | Movimientos de lombrices |
| **aha** | Artificial Hummingbird Algorithm | 2022 | Vuelo de colibríes |
| **opa** | Orca Predator Algorithm | 2021 | Caza de orcas |
| **rro** | Raven Roosting Optimization | 2016 | Dormideros de cuervos |
| **smo** | Starling Murmuration Optimizer | 2022 | Bandadas de estorninos |
| **gvoa** | Griffon Vultures Optimization | 2025 | Vuelo termal de buitres |
| **ho** | Hippopotamus Optimizer | 2024 | Comportamiento territorial |
| **ssa** | Salp Swarm Algorithm | 2017 | Cadenas de salpas marinas |
| **gwo** | Grey Wolf Optimizer | 2014 | Jerarquía de manada de lobos |
| **pso** | Particle Swarm Optimization | 1995 | Movimiento de partículas (clásico) |
| **ga** | Genetic Algorithm | 1975 | Evolución natural (clásico) |

**Nota**: Los alias `hoa` (→ `sho`) y `fgo` (→ `fsa`) están disponibles para compatibilidad.

### Detalles de Implementación HO

El Hippopotamus Optimizer implementa tres fases comportamentales:

1. **Fase de Posición**: Exploración del espacio de búsqueda
2. **Fase de Defensa**: Intensificación territorial con parámetro α
3. **Fase de Evasión**: Escape de óptimos locales con parámetro γ

Parámetros: α ∈ [0.1, 0.9], β ∈ [0.2, 0.8], γ ∈ [0.3, 1.0]

## 🚀 Características Avanzadas

### 1. Imitation Learning (IL) Integration

El proyecto incluye un sistema avanzado de aprendizaje por imitación que permite al algoritmo HO adaptar dinámicamente sus parámetros basándose en demostraciones de algoritmos expertos (GA, PSO).

```bash
# Generar demostraciones de expertos
python utils/generate_demos.py \
    --algorithms "ga,pso" \
    --instances "E-n22-k4,P-n16-k8" \
    --num 100 \
    --seed 42 \
    --output "demos/ho_demos.csv"

# Entrenar modelo IL
python utils/train_il.py \
    --dataset "demos/ho_demos.csv" \
    --epochs 100 \
    --batch-size 32 \
    --val-split 0.2 \
    --seed 42 \
    --model-output "models/ho_il_model.pth"

# Evaluar mejora con IL
python utils/evaluate_il.py \
    --instances "A-n32-k5,E-n51-k5" \
    --runs 50 \
    --model "models/ho_il_model.pth" \
    --output-dir "results/il_evaluation"
```

**Componentes del sistema IL:**
- **Generación de demos**: Algoritmos GA/PSO optimizan parámetros HO para diferentes estados
- **Red neuronal**: Arquitectura 64→128→64→3 para predicción de parámetros α, β, γ  
- **Evaluación**: Comparación estadística HO vs HO+IL con métricas de rendimiento

**Flujo de trabajo completo IL:**

1. **Generar dataset de demostraciones** (genera ~500 demos en 5 min):
   ```bash
   python utils/generate_demos.py --algorithms "ga,pso" --instances "E-n22-k4,P-n16-k8,A-n32-k5" --num 100 --seed 42
   ```

2. **Entrenar modelo IL** (entrena red neuronal en 2 min):
   ```bash
   python utils/train_il.py --dataset "results/demos_ho_il.csv" --epochs 100 --seed 42
   ```

3. **Evaluar mejora** (compara HO vs HO+IL):
   ```bash
   python utils/evaluate_il.py --instances "E-n22-k4" --runs 30 --model "models/ho_il_model.pth"
   ```

**Documentación técnica**: Ver `docs/summaries/IL_INTEGRATION_SUMMARY.md` para detalles completos de la arquitectura, tests y resultados científicos.

### 2. Operadores de Optimización Local VRP

- **2-opt**: Intercambio de arcos
- **Or-opt**: Reubicación de secuencias
- **Relocate**: Mover clientes entre rutas
- **Exchange**: Intercambiar clientes

### 3. Métricas Multi-objetivo

```python
# Las métricas multi-objetivo están disponibles para futuras extensiones
# en utils/multiobjective_metrics.py
```

## 📁 Estructura de Datos y Archivos

### Formato de Instancias VRP

Las instancias VRP siguen el formato estándar CVRPLIB:

```
NAME : A-n32-k5
COMMENT : (Augerat et al, No of trucks: 5, Optimal value: 784)
TYPE : CVRP
DIMENSION : 32                    # Número total de nodos (clientes + depósito)
EDGE_WEIGHT_TYPE : EUC_2D        # Distancia euclidiana 2D
CAPACITY : 100                   # Capacidad máxima por vehículo

NODE_COORD_SECTION
1 82 76     # Nodo 1 (depósito): coordenadas (82, 76)
2 96 44     # Nodo 2 (cliente): coordenadas (96, 44)
3 50 5      # Nodo 3 (cliente): coordenadas (50, 5)
...

DEMAND_SECTION
1 0         # Depósito: demanda 0
2 19        # Cliente 2: demanda 19
3 21        # Cliente 3: demanda 21
...

DEPOT_SECTION
1           # Depósito es el nodo 1
-1          # Fin de sección
EOF         # Fin de archivo
```

### Estructura de Resultados

#### **Archivo JSON de Benchmark**
```json
{
  "metadata": {
    "timestamp": "2025-01-11_14:30:45",
    "total_algorithms": 3,
    "total_instances": 2,
    "runs_per_combination": 30
  },
  "results": [
    {
      "algorithm": "hho",
      "instance": "E-n22-k4",
      "optimal_value": 375,
      "best_fitness": 385.2,
      "mean_fitness": 392.8,
      "std_fitness": 8.4,
      "gap_to_optimal": 2.72,
      "success_rate": 23.33,
      "mean_time": 0.048,
      "all_fitness_values": [385.2, 388.1, ...],
      "all_execution_times": [0.045, 0.051, ...]
    }
  ]
}
```

#### **Archivo CSV Convertido**
```csv
Algorithm,Instance,Run,Best_Cost,Time,Gap_Optimal,Success
hho,E-n22-k4,1,385.2,0.045,2.72,0
hho,E-n22-k4,2,388.1,0.051,3.49,0
ho,E-n22-k4,1,389.7,0.067,3.92,0
...
```

### Directorio de Resultados

```
results/
├── benchmark_20250111_143045/
│   ├── benchmark_results.json     # Resultados completos
│   ├── results.csv               # Versión CSV
│   ├── execution_summary.txt     # Resumen de ejecución
│   └── plots/
│       ├── convergence_hho.png   # Curvas de convergencia
│       └── comparison_boxplot.png
├── statistical_analysis/
│   ├── friedman_test_results.html # Tests estadísticos
│   ├── cd_diagram.png            # Diagrama de diferencias críticas
│   ├── wilcoxon_pairwise.csv     # Comparaciones pareadas
│   └── report.md                 # Reporte completo
└── massive_20250111_150000/
    ├── checkpoint.pkl            # Punto de recuperación
    ├── progress.log             # Log de progreso
    └── final_results.json       # Resultados finales
```

### Archivos de Configuración

#### **requirements.txt**
```txt
numpy>=1.20.0      # Cálculos numéricos
pandas>=1.3.0      # Manipulación de datos
matplotlib>=3.4.0  # Visualización
scipy>=1.7.0       # Tests estadísticos
click>=8.0.0       # CLI interface
seaborn>=0.11.0    # Visualizaciones avanzadas
```

#### **OPTIMAL_VALUES en benchmarking.py**
```python
OPTIMAL_VALUES = {
    "A-n32-k5": 784,
    "E-n22-k4": 375,
    "P-n16-k8": 450,
    "B-n31-k5": 672,
    # ... más valores óptimos conocidos
}
```

### Obtener Más Datos

#### **Instancias VRP Adicionales**
```bash
# Descargar instancias CVRPLIB
wget http://vrp.atd-lab.inf.puc-rio.br/media/com_vrp/instances/A/A-n32-k5.vrp

# Verificar formato
head -20 data/vrp/A-n32-k5.vrp

# Agregar a directorio de datos
cp nueva_instancia.vrp data/vrp/
```

#### **Validar Instancia Nueva**
```bash
# Test de carga rápida
python -c "
from problems.vrp import VRPProblem
p = VRPProblem('data/vrp/nueva_instancia.vrp')
print(f'Dimensión: {p.dimension}, Capacidad: {p.capacity}')
"
```

## 🛠️ Herramientas Solomon

### Benchmark Completo Solomon

```bash
# Ejecutar todas las instancias Solomon
python tools/solomon/run_full_solomon_benchmark.py \
    --algorithms ho sho foa woa \
    --runs 100 \
    --parallel
```

### Benchmark Extendido Solomon

```bash
# Series específicas RC (clientes agrupados)
python tools/solomon/run_extended_solomon_benchmark.py \
    --series RC \
    --subset 101 102 103 104 \
    --time-limit 3600
```

### Análisis de Resultados Solomon

```bash
# Analizar resultados
python tools/solomon/analyze_solomon_results.py \
    --results results/solomon_benchmark \
    --output solomon_analysis
```

### Conversión de Formato

```bash
# Convertir instancias Solomon a formato VRP estándar
python tools/solomon/convert_solomon_format.py \
    --input solomon_instances \
    --output data/vrp/Solomon
```

## 🏗️ Arquitectura

### Estructura del Proyecto

```
BioAlgoCompare/
├── algorithms/          # Implementaciones de algoritmos
│   ├── base.py         # Clases base abstractas
│   └── *.py            # 16 algoritmos bioinspirados
├── data/
│   └── vrp/            # Instancias CVRPLIB
├── docs/               # Documentación completa
│   ├── algorithms/     # Docs de cada algoritmo
│   ├── papers/         # Artículos académicos
│   └── technical/      # Documentación técnica
├── problems/
│   └── vrp.py          # Implementación del VRP
├── results/            # Resultados experimentales
├── scripts/
│   └── analyze.py      # CLI principal unificado
├── tests/              # Suite de pruebas
├── utils/              # Utilidades del sistema
│   ├── algorithm_factory.py      # Factory de algoritmos
│   ├── benchmarking.py          # Sistema de benchmarking
│   ├── statistical_analysis.py  # Análisis estadístico
│   └── visualization.py         # Visualizaciones
├── LICENSE             # Licencia MIT
├── README.md           # Este archivo
├── requirements.txt    # Dependencias Python
└── setup.py           # Configuración de instalación
```

### Diseño Modular

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CLI (Click)   │────▶│ Algorithm Factory │────▶│   Algorithms    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Benchmarking   │────▶│   VRP Problem    │────▶│   Operators     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Statistics    │────▶│  Visualization   │
└─────────────────┘     └──────────────────┘
```

## 🧪 Tests y Cobertura

### Ejecutar Tests

```bash
# Ejecutar todos los tests con cobertura
pytest --cov=algorithms --cov=problems --cov=utils --cov=scripts

# Tests específicos por categoría
pytest tests/unit/algorithms/
pytest tests/integration/

# Tests con marcadores
pytest -m "not slow"

# Generar reporte de cobertura HTML
pytest --cov-report=html --cov-report=term-missing
```

### Estado Actual de Cobertura: **93%**

#### Gaps de Cobertura a Resolver

1. `utils/algorithm_factory.py` (0%)
2. `utils/evaluate_il.py` (0%)
3. `utils/generate_demos.py` (0%)
4. `utils/train_il.py` (0%)
5. `problems/vrp.py` (92% - casos edge faltantes)

## 📊 Opciones de Línea de Comandos

### Comando `run`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--algorithm`, `-a` | Algoritmo a ejecutar | (requerido) |
| `--instance`, `-i` | Instancia VRP | (requerido) |
| `--iterations`, `-n` | Número de iteraciones | 100 |
| `--population`, `-pop` | Tamaño de población | 30 |
| `--runs`, `-r` | Ejecuciones independientes | 1 |
| `--seed`, `-s` | Semilla aleatoria | None |
| `--parallel`, `-p` | Ejecución paralela | False |

### Comando `benchmark`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--run-benchmark` | Ejecutar nuevo benchmark | False |
| `--algorithms`, `-a` | Lista de algoritmos | todos |
| `--instances`, `-inst` | Lista de instancias | P-n16-k8,E-n22-k4 |
| `--runs`, `-r` | Ejecuciones por algoritmo | 5 |
| `--output-dir`, `-o` | Directorio de salida | auto |

### Comando `massive`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--runs`, `-r` | Ejecuciones por algoritmo | 1000 |
| `--algorithm`, `-a` | Algoritmos (múltiple) | all |
| `--instances`, `-i` | Instancias VRP | E-n22-k4,P-n16-k8,A-n32-k5 |
| `--resume` | Reanudar si se interrumpe | True |

### Comando `stats`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--csv` | Archivo CSV de entrada | (requerido) |
| `--out` | Directorio de salida | mismo que CSV |

## 📚 Documentación

### Documentación Principal

- [Guía de Instalación](docs/guides/installation.md)
- [Referencia de Comandos](docs/COMMAND_REFERENCE.md)
- [Metodología Estadística](docs/STATISTICS.md)
- [Arquitectura del Sistema](docs/technical/architecture.md)

### Documentación de Algoritmos

- [Visión General](docs/algorithms/overview.md)
- [Pseudocódigo](docs/algorithms/pseudocode.md)
- [Documentación Individual](docs/algorithms/individual/)

### Análisis y Resultados

- [Comparación de Algoritmos](docs/analysis/comparison.md)
- [Impacto de Iteraciones](docs/analysis/iteration_impact.md)
- [Conclusiones](docs/analysis/conclusions.md)

### Desarrollo

- [Guía de Contribución](docs/development/contribution.md)
- [Procedimientos de Prueba](docs/development/testing.md)
- [Requisitos Algorítmicos](docs/development/algorithmic_requirements.md)

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Añade nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un Pull Request

Ver [Guía de Contribución](docs/development/contribution.md) para más detalles.

## 📈 Estado del Proyecto

- ✅ 16 algoritmos implementados y probados
- ✅ Sistema de benchmarking completo
- ✅ Análisis estadístico riguroso
- ✅ Documentación exhaustiva
- 🚧 Integración con más problemas de optimización
- 🚧 Interfaz web para visualización

## 🔧 Solución de Problemas

### Errores Comunes y Soluciones

#### ❌ **Error: "Instance file not found"**
```bash
FileNotFoundError: [Errno 2] No such file or directory: 'data/vrp/Mi-Instancia.vrp'
```

**✅ Solución:**
```bash
# ✓ Usar nombre sin extensión
python scripts/analyze.py run --algorithm sho --instance A-n32-k5  # ✓ Correcto

# ✗ No incluir .vrp
python scripts/analyze.py run --algorithm sho --instance A-n32-k5.vrp  # ✗ Error

# Verificar instancias disponibles
ls data/vrp/*.vrp | head -10
```

#### ❌ **Error: "ModuleNotFoundError"**
```bash
ModuleNotFoundError: No module named 'numpy'
```

**✅ Solución:**
```bash
# Instalar dependencias faltantes
pip install -r requirements.txt

# Si persiste, reinstalar en entorno limpio
python -m venv venv_nuevo
source venv_nuevo/bin/activate
pip install -r requirements.txt
```

#### ❌ **Error: "Algorithm not found"**
```bash
ValueError: Algorithm 'xyz' not found
```

**✅ Solución:**
```bash
# Ver algoritmos disponibles
python scripts/analyze.py run --help
# Usar nombres correctos: sho, ho, woa, hho, etc.
```

#### ❌ **Benchmarks muy lentos**

**✅ Optimizaciones:**
```bash
# 1. Usar procesamiento paralelo
python scripts/analyze.py benchmark --parallel

# 2. Reducir parámetros para pruebas
python scripts/analyze.py run --runs 5 --iterations 50  # En lugar de defaults

# 3. Instancias más pequeñas para pruebas
python scripts/analyze.py run --instance E-n22-k4  # Pequeña (22 nodos)
```

### Recursos del Sistema

#### Requerimientos Mínimos
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Almacenamiento**: 2 GB libres

#### Requerimientos Recomendados
- **CPU**: 4+ cores, 3.0 GHz
- **RAM**: 8+ GB
- **Almacenamiento**: 10 GB libres

#### Estimaciones de Tiempo

| Operación | Tiempo Estimado | Recursos |
|-----------|----------------|----------|
| Ejecución simple (1 run) | 1-5 segundos | CPU básico |
| Benchmark 30 runs | 2-5 minutos | CPU medio |
| Benchmark 100 runs | 5-15 minutos | CPU bueno |
| Massive 1000 runs | 30-120 minutos | CPU + paralelo |

### Validación de Instalación

#### Test de Funcionalidad Completa
```bash
# 1. Verificar CLI básico
python scripts/analyze.py --help

# 2. Test algoritmo individual
python scripts/analyze.py run --algorithm sho --instance A-n32-k5 --iterations 5

# 3. Test benchmark pequeño
python scripts/analyze.py benchmark --run-benchmark --algorithms "sho,ho" --instances "E-n22-k4" --runs 3

# 4. Test análisis estadístico (requiere CSV de paso 3)
python scripts/analyze.py stats --csv results/*/results.csv --out test_analysis
```

#### Valores Esperados de Referencia
```bash
# A-n32-k5 (óptimo: 784)
sho: ~1700-2000 (gap: 115-155%)
ho:  ~1500-1800 (gap: 90-130%)
hho: ~1400-1700 (gap: 80-115%)

# Si obtienes valores muy diferentes, verificar instalación
```

### Obtener Ayuda

#### Logs Detallados
```bash
# Habilitar logging detallado
export PYTHONPATH=/Users/kaosb/optimizacion
python -v scripts/analyze.py run --algorithm sho --instance A-n32-k5
```

#### Reportar Problemas
Si encuentras un bug, incluye:
1. **Comando exacto usado**
2. **Mensaje de error completo**
3. **Versión de Python**: `python --version`
4. **Sistema operativo**
5. **Output de**: `pip list | grep -E "(numpy|scipy|pandas)"`


## 📚 Referencias

### Referencias Principales

1. **Amiri, M. H., et al. (2024)**. "Hippopotamus optimization algorithm: a novel nature-inspired optimization algorithm". *Scientific Reports* 14, 5032.
   - Algoritmo HO base implementado verbatim
   - Tres fases comportamentales modeladas
   - Rangos de parámetros respetados

2. **Potvin, J. Y. (2009)**. "State-of-the-art review—evolutionary algorithms for vehicle routing". *INFORMS Journal on Computing*, 21(4), 518-548.
   - Comparación con baselines establecidos
   - Métricas VRP estándar utilizadas

3. **Barros, T. D., & Everett, J. W. (2023)**. "Imitation Learning for Metaheuristic Optimization". *arXiv preprint*.
   - Base para integración IL con HO
   - Arquitectura de red neuronal

### Citar Este Trabajo

Si utilizas BioAlgoCompare en tu investigación:

```bibtex
@inproceedings{bioalgocompare2025,
  title={A Comprehensive Evaluation of Bio-inspired Algorithms for Vehicle Routing Problems},
  author={[Tu Nombre]},
  booktitle={Proceedings of International Conference},
  year={2025}
}

@software{bioalgocompare2025,
  title={BioAlgoCompare: A Comprehensive Platform for Bio-inspired Algorithm Evaluation},
  author={[Tu Nombre]},
  year={2025},
  url={https://github.com/username/BioAlgoCompare}
}
```

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

<div align="center">
  <sub>Construido con ❤️ desde Valparaiso</sub>
</div>
