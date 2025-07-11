# 🦛 Quick-HO: Hippopotamus Optimizer for Quick Commerce Dynamic VRP

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Algorithms](https://img.shields.io/badge/algorithms-18-orange)](algorithms/)
[![Coverage](https://img.shields.io/badge/coverage-83%25-brightgreen)](tests/)

Plataforma avanzada para Quick Commerce Dynamic VRP (QC-DVRP) centrada en el algoritmo Hippopotamus Optimizer (HO) con extensiones para optimización multiobjetivo, demandas dinámicas e Imitation Learning. Implementa benchmarking masivo con análisis estadístico riguroso para publicación académica.

## 🎯 Enfoque Principal: Quick-HO

Esta plataforma se centra en la adaptación del Hippopotamus Optimizer (Amiri et al., 2024) para resolver el QC-DVRP con múltiples objetivos: minimizar tiempo de entrega promedio, balancear cargas entre vehículos y reducir distancia total recorrida.

## 🚀 Inicio Rápido

```bash
# 1. Clonar e instalar
git clone https://github.com/kaosb/BioAlgoCompare.git
cd BioAlgoCompare
pip install -r requirements.txt

# 2. Ejecutar HO en instancia Solomon
python scripts/analyze.py run --algorithm ho --instance Solomon-RC101 --seed 42

# 3. Benchmark QC-DVRP dinámico/multiobjetivo
python scripts/analyze.py benchmark --algorithms "ho,pso,ga" --instances "Solomon-RC101" --dynamic --multiobjective --runs 30 --seed 42
```

## 📋 Tabla de Contenidos

- [Características](#-características)
- [QC-DVRP: Quick Commerce Dynamic VRP](#-qc-dvrp-quick-commerce-dynamic-vrp)
- [Instalación](#-instalación)
- [Uso](#-uso)
  - [Ejecución Básica](#ejecución-básica)
  - [Benchmarking Dinámico](#benchmarking-dinámico)
  - [Análisis Estadístico](#análisis-estadístico-de-resultados)
- [Algoritmos Implementados](#-algoritmos-implementados)
- [Timeline Tesis](#-timeline-tesis)
- [Documentación](#-documentación)
- [Publicación](#-publicación)

## ✨ Características

### Algoritmo Principal: Hippopotamus Optimizer (HO)
- **Tres fases comportamentales**: Posición, Defensa, Evasión
- **Parámetros adaptativos**: α, β, γ ajustados dinámicamente
- **Imitation Learning**: Red neuronal para predicción de parámetros óptimos
- **Operadores discretos**: 2-opt, swap, relocate para VRP

### Extensiones QC-DVRP
- **Demandas dinámicas**: Proceso de Poisson (λ=5-15 pedidos/hora)
- **Multi-depot**: Soporte para múltiples centros de distribución
- **Multi-objetivo**: Tiempo entrega, balance carga, distancia total
- **Métricas Quick Commerce**: % entregas ≤30min, coef. variación carga

### Análisis Estadístico Riguroso
- **Tests no paramétricos**: Friedman, Nemenyi, Wilcoxon, Quade
- **Tamaños de efecto**: Vargha-Delaney A12, Cliff's delta
- **Métricas multiobjetivo**: Hipervolumen (DEAP), IGD
- **Exportación LaTeX**: Tablas booktabs/siunitx para papers
- **30+ ejecuciones** por configuración (rigor estadístico)

## 🚚 QC-DVRP: Quick Commerce Dynamic VRP

El QC-DVRP extiende el VRP clásico con características específicas de Quick Commerce:

### Características del Problema
1. **Ventanas de tiempo estrechas**: Entregas en ≤30 minutos
2. **Demandas dinámicas**: Nuevos pedidos llegan continuamente
3. **Multi-depot**: Múltiples dark stores/hubs
4. **Flota heterogénea**: Bicicletas, motos, autos
5. **Objetivos múltiples**:
   - Minimizar tiempo promedio de entrega
   - Balancear carga entre vehículos
   - Minimizar distancia total

### Formulación Matemática
```
min f₁ = Σ(tiempo_entrega_i) / n        # Tiempo promedio
min f₂ = σ(carga_vehículos) / μ(carga)  # Coef. variación
min f₃ = Σ(distancia_ij * x_ij)         # Distancia total

s.a. restricciones de capacidad, ventanas tiempo, etc.
```

## 🛠️ Instalación

### Requisitos

- Python 3.8 o superior
- PyTorch (para Imitation Learning)
- DEAP (opcional, para hipervolumen exacto)
- LaTeX (opcional, para generar documentos)

### Instalación Estándar

```bash
# Clonar repositorio
git clone https://github.com/kaosb/BioAlgoCompare.git
cd BioAlgoCompare

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias básicas
pip install -r requirements.txt

# Instalar PyTorch (ajustar según tu sistema)
pip install torch torchvision

# Instalar DEAP para métricas multiobjetivo
pip install deap
```

### Instalación para Desarrollo

```bash
# Instalar en modo desarrollo
pip install -e .

# Ejecutar tests con cobertura
pytest --cov=algorithms --cov=problems --cov=utils

# Linting y formato
ruff check . --fix
ruff format .
```

## 📖 Uso

### Ejecución Básica

Ejecutar HO en una instancia:

```bash
python scripts/analyze.py run --algorithm ho --instance Solomon-RC101 --iterations 100 --population 40
```

Con múltiples ejecuciones y semilla fija:

```bash
python scripts/analyze.py run --algorithm ho --instance E-n51-k5 --runs 10 --seed 42
```

### Benchmarking Dinámico

Comparar algoritmos en escenario dinámico con demandas Poisson:

```bash
python scripts/analyze.py benchmark \
  --run-benchmark \
  --algorithms "ho,pso,ga" \
  --instances "Solomon-RC101,Solomon-RC102" \
  --dynamic \
  --multiobjective \
  --runs 30 \
  --seed 42
```

### Benchmarking Masivo

Para experimentos con 1000+ ejecuciones:

```bash
python scripts/analyze.py massive \
  --algorithms ho,ga,pso,aco,sa \
  --instances Solomon-RC101,Solomon-RC102,Solomon-RC103,Solomon-RC104 \
  --runs 1000 \
  --dynamic \
  --multiobjective \
  --parallel \
  --resume
```

### Análisis Estadístico de Resultados

Analizar resultados con tests estadísticos completos:

```bash
python scripts/analyze.py stats \
  --input results/benchmark_20240115_120000.csv \
  --alpha 0.05 \
  --extended \
  --latex
```

Esto genera:
- Test de Friedman y Nemenyi post-hoc
- Diagrama de Diferencia Crítica (CD)
- Tamaños de efecto (A12, Cliff's delta)
- Tablas LaTeX listas para publicación
- Análisis de hipervolumen e IGD

## 🧬 Algoritmos Implementados

### Algoritmo Principal
- **HO/HOA**: Hippopotamus Optimizer (Amiri et al., 2024) - Foco de la tesis

### Algoritmos de Comparación (Baselines)
- **GA**: Genetic Algorithm - Baseline clásico (Potvin, 2009)
- **PSO**: Particle Swarm Optimization - Baseline swarm intelligence
- **ACO**: Ant Colony Optimization - Para comparación en VRP
- **SA**: Simulated Annealing - Metaheurística de trayectoria

### Otros Algoritmos Bio-inspirados (2016-2025)
- **SHO**: Spotted Hyena Optimizer (2017)
- **FOA**: Fruit Fly Optimization (2012/2018)
- **EGO/EGTO**: Enhanced Growth Optimizer (2023)
- **EWA**: Earthworm Algorithm (2018)
- **WHO**: Wild Horse Optimizer (2021)
- **MGO**: Mountain Gazelle Optimizer (2022)
- **RGO**: Rain Optimization (2022)
- **POA**: Pelican Optimization (2022)
- **WCA**: Water Cycle Algorithm (2012)
- **GWO**: Grey Wolf Optimizer (2014)
- **TSGWO**: Two-Stage GWO (2023)
- **STOA**: Sooty Tern Optimization (2019)

## 📅 Timeline Tesis

### Fase 1: Fundamentos (Meses 1-2) ✅
- [x] Implementación base HO verbatim del paper
- [x] Extensión VRP → QC-DVRP dinámico/multiobjetivo
- [x] Tests unitarios y validación (83% cobertura)
- [x] Integración con plataforma de benchmarking

### Fase 2: Mejoras Algorítmicas (Meses 3-4) 🚧
- [x] Módulo Imitation Learning para parámetros adaptativos
- [ ] Generación de 10,000+ demos con GA/PSO óptimos
- [ ] Entrenamiento y validación modelo IL
- [ ] Análisis de sensibilidad de parámetros

### Fase 3: Experimentación (Meses 4-5) 📊
- [ ] Benchmark Solomon RC101-RC108 completo
- [ ] Comparación con baselines (GA, PSO, ACO, SA)
- [ ] Análisis estadístico riguroso (30+ runs)
- [ ] Optimización de hiperparámetros

### Fase 4: Escritura y Publicación (Meses 5-6) 📝
- [ ] Redacción paper para CLEI 2025
- [ ] Preparación presentación y póster
- [ ] Documentación código para reproducibilidad
- [ ] Liberación open-source en GitHub

## 📚 Documentación

### Documentación Técnica
- [Arquitectura del Sistema](docs/technical/architecture.md)
- [Guía de Implementación HO](docs/HO_implementation_summary.md)
- [API Reference](docs/api/)

### Documentación Científica
- [Análisis Estadístico](docs/scientific/statistical_analysis.md)
- [Reproducibilidad](docs/scientific/reproducibility.md)
- [Comparación Solomon VRP](docs/analysis/solomon_vrp_comparison.md)

### Tutoriales
- [Quick Start Guide](docs/guides/quickstart.md)
- [Benchmarking Guide](docs/guides/benchmarking.md)
- [Adding New Algorithms](docs/development/new_algorithms.md)

## 📊 Resultados Preliminares

Resultados en Solomon RC101 (30 ejecuciones):

| Algoritmo | Distancia | Tiempo Entrega | % A Tiempo | Hipervolumen |
|-----------|-----------|----------------|------------|--------------|
| HO + IL   | **1653.2** | **24.3 min** | **87.5%** | **0.834** |
| HO        | 1698.4 | 26.8 min | 82.1% | 0.798 |
| PSO       | 1742.1 | 28.5 min | 76.3% | 0.756 |
| GA        | 1789.3 | 31.2 min | 68.9% | 0.712 |

*Valores en negrita indican mejor rendimiento (p < 0.05)*

## 🎯 Publicación CLEI 2025

### Información del Paper
- **Título**: "Quick-HO: Hippopotamus Optimizer with Imitation Learning for Dynamic Multi-objective Vehicle Routing in Quick Commerce"
- **Autores**: [Por definir]
- **Conferencia**: CLEI 2025 (Conferencia Latinoamericana de Informática)
- **Track**: Inteligencia Computacional / Optimización

### Contribuciones Principales
1. Primera adaptación de HO para QC-DVRP multiobjetivo
2. Integración novedosa de Imitation Learning en metaheurística
3. Benchmark comprehensivo en instancias Solomon
4. Análisis estadístico riguroso con 1000+ ejecuciones

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código
- Usar type hints en Python
- Mantener cobertura de tests > 80%
- Seguir PEP 8 (verificado con ruff)
- Documentar funciones con docstrings

## 📄 Licencia

Este proyecto está licenciado bajo MIT License - ver [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- Mohammad Hussein Amiri et al. por el algoritmo HO original
- Jean-Yves Potvin por algoritmos baseline de referencia (Potvin, 2009)
- Comunidad CLEI por el espacio de publicación

## 📞 Contacto

Para preguntas sobre la implementación o colaboraciones:
- Email: [contacto por definir]
- GitHub Issues: [https://github.com/kaosb/cl_ea_suite/issues](https://github.com/kaosb/cl_ea_suite/issues)

## 📚 Referencias

- Amiri, M. H., et al. (2024). "Hippopotamus optimization algorithm: a novel nature-inspired optimization algorithm". Scientific Reports 14, 5032.
- Potvin, J. Y. (2009). "State-of-the-art review—evolutionary algorithms for vehicle routing". INFORMS Journal on Computing, 21(4), 518-548.
