# Guía de Inicio Rápido

Esta guía te ayudará a comenzar con BioAlgoCompare en minutos.

## Conceptos Básicos

BioAlgoCompare es un framework para experimentar con algoritmos metaheurísticos bio-inspirados aplicados al Problema de Ruteo de Vehículos (VRP).

### Componentes Principales

1. **Algoritmos**: 18 metaheurísticas bio-inspiradas
2. **Problemas**: Instancias VRP estándar
3. **CLI**: Interfaz de línea de comandos unificada
4. **Análisis**: Herramientas estadísticas y visualización

## Tu Primera Ejecución

### 1. Ejecutar un Algoritmo Simple

```bash
# Ejecutar Whale Optimization Algorithm
bioalgocompare run woa P-n16-k8.vrp
```

Esto ejecutará:
- Algoritmo: WOA (Whale Optimization Algorithm)
- Instancia: P-n16-k8 (16 nodos, 8 vehículos)
- Parámetros por defecto: 30 individuos, 100 iteraciones, 30 runs

### 2. Personalizar Parámetros

```bash
# Más individuos y iteraciones
bioalgocompare run sma P-n19-k2.vrp -p 50 -n 200 -r 10

# Donde:
# -p 50: población de 50 individuos
# -n 200: 200 iteraciones
# -r 10: 10 ejecuciones independientes
```

### 3. Ejecutar con Visualización

```bash
# Generar gráficos de convergencia
bioalgocompare run gto P-n16-k8.vrp --plot
```

## Comparar Algoritmos

### 1. Benchmark Rápido

```bash
# Comparar 3 algoritmos en 2 instancias
bioalgocompare benchmark \
  -a woa,sma,gto \
  -i P-n16-k8,P-n19-k2 \
  -r 30
```

### 2. Benchmark Completo

```bash
# Todos los algoritmos top en múltiples instancias
bioalgocompare benchmark \
  -a woa,sma,gto,mrfo,aha,ewa \
  -i P-n16-k8,P-n19-k2,P-n20-k2,P-n23-k8 \
  -p 50 -n 200 -r 50
```

## Analizar Resultados

### 1. Análisis Básico

```bash
# Ver resumen de resultados
bioalgocompare analyze results/experiment_*.json
```

### 2. Análisis Detallado

```bash
# Análisis estadístico completo
bioalgocompare analyze results/benchmark_*.json \
  --format detailed \
  --compare \
  --plot
```

### 3. Guardar Reporte

```bash
# Generar reporte en Markdown
bioalgocompare analyze results/data.json \
  --format statistical \
  -o report.md
```

## Modos de Ejecución

### Modo Standard (Por defecto)

```bash
bioalgocompare run woa instance.vrp
```

### Modo Massive (1000 runs)

```bash
# Para análisis estadístico robusto
bioalgocompare run woa instance.vrp \
  --mode massive \
  --checkpoint-interval 100
```

### Modo Experiment

```bash
# Con semillas específicas para reproducibilidad
bioalgocompare run opa instance.vrp \
  --mode experiment \
  --experiment-seeds "42,123,456,789,1001"
```

## Flujos de Trabajo Comunes

### 1. Evaluación de un Nuevo Algoritmo

```bash
# Paso 1: Test inicial
bioalgocompare run mi_algo P-n16-k8.vrp -r 5

# Paso 2: Si funciona bien, más runs
bioalgocompare run mi_algo P-n16-k8.vrp -r 30

# Paso 3: Comparar con baseline
bioalgocompare benchmark -a mi_algo,woa,sma -i P-n16-k8
```

### 2. Optimización de Parámetros

```bash
# Probar diferentes tamaños de población
for pop in 20 30 50 100; do
  bioalgocompare run woa P-n16-k8.vrp -p $pop -r 30
done

# Analizar todos los resultados
bioalgocompare analyze results/*.json --compare
```

### 3. Estudio Completo

```bash
# 1. Verificar datasets
bioalgocompare datasets check

# 2. Ejecutar benchmark principal
bioalgocompare benchmark \
  -a woa,sma,gto,mrfo,aha \
  -i P-n16-k8,P-n19-k2,P-n20-k2 \
  -r 50

# 3. Analizar y generar reporte
bioalgocompare analyze results/benchmark_*.json \
  --format detailed \
  --compare \
  -o informe_final.md
```

## Tips y Mejores Prácticas

### 1. Reproducibilidad

```bash
# Siempre usar semilla para experimentos reproducibles
bioalgocompare run woa instance.vrp --seed 42
```

### 2. Paralelización

```bash
# Usar todos los cores disponibles
bioalgocompare run woa instance.vrp --parallel

# Limitar workers
bioalgocompare run woa instance.vrp --parallel --workers 4
```

### 3. Gestión de Memoria

```bash
# Para instancias grandes, ejecutar secuencialmente
bioalgocompare run woa instance_grande.vrp --no-parallel

# O reducir población
bioalgocompare run woa instance_grande.vrp -p 20
```

### 4. Checkpoints

```bash
# Para ejecuciones largas, usar checkpoints
bioalgocompare run woa instance.vrp \
  --mode massive \
  --checkpoint-interval 50

# Reanudar desde checkpoint
bioalgocompare run woa instance.vrp \
  --mode massive \
  --resume
```

## Interpretación de Resultados

### Métricas Principales

- **best_fitness**: Mejor solución encontrada (menor es mejor)
- **mean_fitness**: Promedio de todas las ejecuciones
- **std_fitness**: Desviación estándar (consistencia)
- **median_fitness**: Mediana (robustez)

### Ejemplo de Salida

```
📊 Estadísticas Generales:
  Algoritmo: woa
  Instancia: P-n16-k8
  Mejor fitness: 450.3421
  Media ± Std: 465.7892 ± 12.3456
  Mediana: 463.2145
```

### Criterios de Evaluación

1. **Calidad**: ¿Qué tan buena es la mejor solución?
2. **Consistencia**: ¿Qué tan pequeña es la desviación?
3. **Robustez**: ¿La mediana está cerca de la media?
4. **Eficiencia**: ¿Cuánto tiempo toma?

## Comandos Útiles

```bash
# Ver todos los algoritmos disponibles
bioalgocompare info

# Verificar versión
bioalgocompare --version

# Ayuda general
bioalgocompare --help

# Ayuda de un comando
bioalgocompare run --help

# Listar resultados
ls -la results/

# Ver convergencia en tiempo real (desarrollo)
tail -f results/current_run.log
```

## Siguiente Paso

- Para más detalles sobre algoritmos: [Documentación de Algoritmos](ALGORITHMS.md)
- Para desarrollo: [Guía de Desarrollo](DEVELOPMENT.md)
- Para análisis avanzado: [Análisis Estadístico](ANALYSIS.md)