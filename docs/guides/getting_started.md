# Guía de Inicio Rápido

Esta guía proporciona los pasos básicos para comenzar a utilizar BioAlgoCompare rápidamente.

## Primeros Pasos

Después de [instalar el proyecto](installation.md), puede comenzar a usar BioAlgoCompare para evaluar y comparar algoritmos metaheurísticos bioinspirados en problemas de optimización de rutas de vehículos (VRP).

## Ejecución Básica

### Ejecutar un Algoritmo Individual

Para ejecutar un algoritmo específico en una instancia VRP:

```bash
python run.py --algorithm ewa --instance P-n16-k8 --iterations 100 --population 30
```

Este comando ejecutará el algoritmo EWA (Earthworm Algorithm) en la instancia P-n16-k8 con 100 iteraciones y una población de 30 individuos.

#### Parámetros Principales:

- `--algorithm, -a`: Algoritmo a ejecutar (ewa, foa, gto, etc.)
- `--instance, -i`: Nombre de la instancia VRP (sin extensión)
- `--iterations, -n`: Número de iteraciones
- `--population, -p`: Tamaño de la población
- `--runs, -r`: Número de ejecuciones independientes
- `--seed, -s`: Semilla para reproducibilidad
- `--visualize/--no-visualize`: Activar/desactivar visualización
- `--save/--no-save`: Guardar resultados
- `--parallel/--no-parallel`: Ejecutar en paralelo

### Ejecutar Todos los Algoritmos

Para ejecutar todos los algoritmos implementados:

```bash
python run.py --algorithm all --instance E-n22-k4 --runs 3 --parallel
```

Esto ejecutará todos los algoritmos disponibles en la instancia E-n22-k4, con 3 ejecuciones independientes para cada algoritmo, utilizando procesamiento paralelo.

## Benchmarking Rápido

Para ejecutar un benchmark comparativo entre varios algoritmos:

```bash
python scripts/analyze.py benchmark --run-benchmark --instances E-n22-k4 P-n16-k8 --algorithms foa gto ewa --runs 5 --parallel
```

Este comando ejecutará un benchmark de los algoritmos FOA, GTO y EWA en las instancias E-n22-k4 y P-n16-k8, con 5 ejecuciones por algoritmo/instancia.

## Visualización de Resultados

Los resultados se visualizarán automáticamente (si `--visualize` está activo) y también se guardarán en el directorio `results/`:

- **Soluciones de rutas**: `results/{algoritmo}_{instancia}_solution.png`
- **Curvas de convergencia**: `results/{algoritmo}_{instancia}_convergence.png`
- **Comparativas**: `results/comparison_{instancia}.png`
- **Resultados detallados**: `results/{instancia}_{timestamp}.csv`
- **Resúmenes estadísticos**: `results/{instancia}_{timestamp}_summary.csv`

## Ejemplos Prácticos

### Ejemplo 1: Comparar Dos Algoritmos

```bash
# Ejecutar FOA y EWA con parámetros idénticos
python run.py --algorithm foa --instance P-n16-k8 --iterations 100 --seed 42
python run.py --algorithm ewa --instance P-n16-k8 --iterations 100 --seed 42

# Revisar los resultados
cat results/P-n16-k8_*_summary.csv
```

### Ejemplo 2: Ejecutar con Diferentes Iteraciones

```bash
# Probar el impacto del número de iteraciones
python run.py --algorithm gto --instance E-n22-k4 --iterations 10 --seed 123
python run.py --algorithm gto --instance E-n22-k4 --iterations 100 --seed 123
python run.py --algorithm gto --instance E-n22-k4 --iterations 1000 --seed 123
```

### Ejemplo 3: Benchmarking Masivo

```bash
# Ejecutar un benchmark masivo (1000 ejecuciones)
python scripts/analyze.py massive --runs 1000 --algorithm ewa --instances E-n22-k4 --parallel --resume
```

## Recomendaciones para Primeros Usuarios

1. **Comience con instancias pequeñas**: P-n16-k8 es ideal para pruebas iniciales
2. **Use pocas iteraciones**: Comience con 10-100 iteraciones mientras aprende
3. **Establezca una semilla**: Use `--seed` para resultados reproducibles
4. **Ejecute en paralelo**: Active `--parallel` para aprovechar múltiples núcleos
5. **Compare incrementalmente**: Pruebe diferentes algoritmos/parámetros uno a uno

## Siguientes Pasos

Una vez que se familiarice con las operaciones básicas, puede:

- Explorar la [Guía de Uso Completa](usage.md) para funcionalidades avanzadas
- Consultar la [Documentación de Algoritmos](../algorithms/overview.md) para entender mejor cada método
- Revisar la [Guía de Benchmarking](benchmarking.md) para análisis estadísticos rigurosos
- Explorar los [Análisis Comparativos](../analysis/comparison.md) para entender el rendimiento relativo

## Recursos Adicionales

- [Documentación de la Línea de Comandos](../technical/cli_reference.md)
- [Referencia de Instancias VRP](../technical/vrp_instances.md)
- [Preguntas Frecuentes](../faq.md)