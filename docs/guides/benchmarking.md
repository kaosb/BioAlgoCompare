# Guía de Benchmarking

Esta guía proporciona instrucciones detalladas para realizar benchmarks rigurosos y análisis estadísticos de algoritmos metaheurísticos con BioAlgoCompare. Enfocada en metodología científica, reproducibilidad y explicabilidad de los resultados.

## Contenido

1. [Principios de Benchmarking Científico](#principios-de-benchmarking-científico)
2. [Tipos de Benchmarks](#tipos-de-benchmarks)
3. [Configuración de Benchmarks](#configuración-de-benchmarks)
4. [Uso del script run_massive.py](#uso-del-script-run_massive.py)
5. [Análisis Estadístico](#análisis-estadístico)
6. [Visualización de Resultados](#visualización-de-resultados)
7. [Ciclo Completo de Benchmarking](#ciclo-completo-de-benchmarking)
8. [Interpretación de Resultados](#interpretación-de-resultados)
9. [Publicación de Resultados](#publicación-de-resultados)

## Principios de Benchmarking Científico

El benchmarking de algoritmos metaheurísticos en BioAlgoCompare sigue estos principios:

### 1. Reproducibilidad

- **Control de semilla**: Todas las ejecuciones usan semillas explícitas para permitir reproducción exacta
- **Documentación completa**: Todos los parámetros son registrados automáticamente
- **Versiones de software**: Se recomienda documentar las versiones exactas de todas las dependencias

### 2. Rigor Estadístico

- **Tamaño de muestra adecuado**: Mínimo 30 ejecuciones para pruebas paramétricas
- **Tests apropiados**: Tests no paramétricos para comparaciones entre algoritmos
- **Corrección para comparaciones múltiples**: Bonferroni, Holm, etc.
- **Intervalos de confianza**: Reportados al 95% por defecto

### 3. Equidad en Comparaciones

- **Recursos computacionales equivalentes**: Mismo número de evaluaciones de función objetivo
- **Inicialización consistente**: Mismos métodos de inicialización para todos los algoritmos
- **Criterios de parada unificados**: Mismo número de iteraciones o tiempo de ejecución

### 4. Transparencia

- **Código abierto**: Todo el código del benchmark es inspeccionable
- **Datos disponibles**: Resultados brutos disponibles para verificación
- **Metodología explícita**: Documentación clara del proceso experimental

## Tipos de Benchmarks

BioAlgoCompare admite varios tipos de benchmarks:

### 1. Benchmark Comparativo Estándar

Compara varios algoritmos en una o más instancias, con múltiples ejecuciones independientes:

```bash
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto,foa,hoa,woa \
    --instances "E-n22-k4,P-n16-k8" \
    --runs 30 --seed 42 --parallel
```

### 2. Benchmark Masivo

Ejecuta un gran número de repeticiones (1000+) para análisis estadístico detallado:

```bash
python scripts/analyze.py massive \
    --algorithm egto,foa,hoa \
    --instances "E-n22-k4" \
    --runs 1000 --parallel --resume
```

### 3. Benchmark de Parámetros

Compara un mismo algoritmo con diferentes configuraciones de parámetros:

```bash
# Usando benchmark con diferentes poblaciones
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto \
    --instances "E-n22-k4" \
    --population 20,50,100 \
    --runs 30 --seed 42
```

### 4. Benchmark de Iteraciones

Evalúa el impacto del número de iteraciones en la calidad de las soluciones:

```bash
# Ejecución manual con diferentes iteraciones
python scripts/run.py --algorithm egto --instance E-n22-k4 --iterations 100 --runs 10 --seed 42
python scripts/run.py --algorithm egto --instance E-n22-k4 --iterations 500 --runs 10 --seed 42
python scripts/run.py --algorithm egto --instance E-n22-k4 --iterations 1000 --runs 10 --seed 42
```

## Configuración de Benchmarks

Aquí se describen los parámetros clave para configurar los benchmarks en BioAlgoCompare:

### Parámetros Clave de Benchmarking

| Parámetro | Descripción | Uso Científico Recomendado | Efecto en Benchmark |
|-----------|-------------|----------------------------|---------------------|
| `--runs`  | Número de ejecuciones por algoritmo/instancia | ≥30 para significancia estadística | Determina la robustez de los resultados |
| `--seed`  | Semilla para control de aleatoriedad | Fijo documentado para reproducibilidad | Asegura que los mismos resultados se obtienen en ejecuciones consecutivas |
| `--population` | Tamaño de la población de soluciones | Consistente entre comparaciones | Afecta la calidad de convergencia y exploración del espacio de soluciones |
| `--iterations` | Número de iteraciones por ejecución | Suficientes para convergencia | Mejora la calidad de los resultados obtenidos |
| `--parallel` | Ejecutar en paralelo | Recomendado en pruebas largas | Acelera el tiempo total de benchmark |
| `--optimize` | Aplicar optimización local (opcional) | Debe aplicarse de forma consistente | Mejora la calidad de las soluciones encontradas |

## Uso del script `run_massive.py`

El script `run_massive.py` se utiliza para ejecutar un gran número de pruebas en algoritmos metaheurísticos, ideal para análisis estadísticos rigurosos. Permite configurar varios parámetros para controlar el comportamiento del benchmark:

### Parámetros de `run_massive.py`

| Parámetro | Descripción | Valor por Defecto | Notas |
|-----------|-------------|-------------------|-------|
| `--runs`, `-r` | Número de ejecuciones por algoritmo/instancia | 1000 | Para estudios de alta precisión, se recomiendan 1000+ ejecuciones. |
| `--iterations`, `-n` | Número de iteraciones por ejecución | 100 | Ajustar según la velocidad de convergencia esperada del algoritmo. |
| `--population`, `-p` | Tamaño de la población | 40 | Un tamaño mayor puede mejorar la exploración, a costa de tiempo computacional. |
| `--seed`, `-s` | Semilla base para la generación de números aleatorios | 42 | Usar una semilla fija garantiza la reproducibilidad del experimento. |
| `--algorithm`, `-a` | Algoritmos a ejecutar (puede ser múltiple) | all | Aceptar múltiples valores separados por espacio o coma. Use 'all' para incluir todos. |
| `--instances`, `-i` | Instancias a evaluar (puede ser múltiple) | ['E-n22-k4', 'P-n16-k8', 'A-n32-k5'] | Aceptar múltiples valores separados por espacio o coma (sin extensión .vrp). |
| `--parallel/--no-parallel` | Habilitar/deshabilitar ejecución paralela | True | Aprovecha múltiples núcleos para acelerar el benchmark. |
| `--resume/--no-resume` | Reanudar benchmark interrumpido | True | Permite continuar desde el último checkpoint guardado. |
| `--output-dir`, `-o` | Directorio para guardar los resultados | Generado automáticamente (e.g., `results/massive_benchmark_YYYYMMDD_HHMMSS`) | Permite organizar los resultados de diferentes experimentos. |
| `--profile/--no-profile` | Activar/desactivar perfil de rendimiento | False | Genera perfiles de cProfile por algoritmo para identificar cuellos de botella. |

### Ejemplos de Uso de `run_massive.py`

#### 1. Ejecución Masiva con Configuración por Defecto
```bash
PYTHONPATH=./ python scripts/run_massive.py
```
*   Ejecuta todos los algoritmos en las instancias por defecto con 1000 runs, 100 iteraciones, población 40, paralelo, reanudación activada y semilla 42.

#### 2. Ejecución Masiva con Algoritmos e Instancias Específicas
```bash
PYTHONPATH=./ python scripts/run_massive.py \
    --instances "E-n22-k4,P-n16-k8" \
    --algorithm "sho,apo" \
    --runs 100 \
    --iterations 500 \
    --population 30 \
    --parallel \
    --seed 100
```
*   Ejecuta SHO y APO en las instancias E-n22-k4 y P-n16-k8 con 100 runs, 500 iteraciones, población 30, en paralelo y con semilla 100.

#### 3. Reanudar un Benchmark Masivo Interrumpido
```bash
PYTHONPATH=./ python scripts/run_massive.py --resume
```
*   Continúa la última ejecución masiva interrumpida (basado en el archivo de estado en el directorio de salida).

#### 4. Ejecución sin Paralelismo y con Directorio de Salida Personalizado
```bash
PYTHONPATH=./ python scripts/run_massive.py \
    --instances "A-n32-k5" \
    --algorithm "all" \
    --runs 50 \
    --iterations 2000 \
    --no-parallel \
    --output-dir results/experimento_A-n32-k5_largo \
    --seed 200
```
*   Ejecuta todos los algoritmos en la instancia A-n32-k5 con 50 runs, 2000 iteraciones, sin paralelismo, guardando resultados en un directorio específico y con semilla 200.

#### 5. Activar Perfil de Rendimiento
```bash
PYTHONPATH=./ python scripts/run_massive.py \
    --instances "E-n22-k4" \
    --algorithm "egto" \
    --runs 10 \
    --iterations 100 \
    --profile
```
*   Ejecuta EGTO en E-n22-k4 con 10 runs, 100 iteraciones, generando perfiles de rendimiento en el directorio de salida.

### Reproducibilidad Total

Para asegurar la reproducibilidad y rigurosidad de los experimentos, usar el script `run_massive.py` permite ejecutar pruebas detalladas sobre un conjunto de parámetros. La documentación completa de los parámetros utilizados y el entorno es crucial.

#### Documentación de un Experimento Reproducible

Para garantizar reproducibilidad completa del benchmark, además de especificar la semilla en el comando `run_massive.py`:

1.  **Documentar versiones de software**: Guardar el estado exacto de las librerías Python utilizadas.
    ```bash
    pip freeze > benchmark_environment.txt
    ```

2.  **Guardar comandos exactos**: Registrar el comando `run_massive.py` completo utilizado para ejecutar el experimento.
    ```bash
    echo "PYTHONPATH=./ python scripts/run_massive.py --instances \"E-n22-k4,P-n16-k8\" --algorithm \"all\" --runs 100 --iterations 1000 --population 50 --parallel --seed 42" > benchmark_command.txt
    ```

3.  **Guardar metadatos del entorno**: Capturar información del sistema y hardware.
    ```bash
    uname -a > system_info.txt
    lscpu > cpu_info.txt
    ```

4.  **Mantener control de versiones**: Si se realizaron modificaciones al código de BioAlgoCompare, registrar el commit exacto utilizado.

Al compartir estos archivos (`benchmark_environment.txt`, `benchmark_command.txt`, `system_info.txt`, `cpu_info.txt`, y el commit hash), otros investigadores pueden replicar tu entorno y tu experimento exacto.

## Análisis Estadístico

BioAlgoCompare aplica automáticamente análisis estadístico riguroso a los resultados:

### Tests Aplicados

1. **Pruebas de Normalidad**:
   - Shapiro-Wilk para determinar si los datos siguen distribución normal
   - Determina si se usan tests paramétricos o no paramétricos

2. **Comparación de Múltiples Algoritmos**:
   - Test de Friedman (no paramétrico) para detectar diferencias significativas
   - Test de Kruskal-Wallis como alternativa
   - ANOVA para datos normalmente distribuidos

3. **Comparaciones Por Pares**:
   - Test post-hoc de Nemenyi para rankings
   - Test de Wilcoxon con corrección para múltiples comparaciones
   - Corrección de Bonferroni o Holm para controlar la tasa de error

4. **Medidas de Tamaño del Efecto**:
   - A12 de Vargha-Delaney para interpretación práctica
   - Delta de Cliff para estimar la magnitud de las diferencias

### Personalización del Análisis

```bash
# Análisis con nivel de significancia personalizado
python scripts/analyze.py analyze-csv results/benchmark_results.csv \
    --significance-level 0.01 \
    --correction-method holm
```

## Visualización de Resultados

BioAlgoCompare proporciona herramientas para visualizar los resultados de manera clara y científica:

### Tipos de Visualizaciones

1. **Boxplots Comparativos**:
   - Comparación directa de distribución de resultados
   - Outliers claramente identificados
   - Intervalos de confianza mostrados

2. **Curvas de Convergencia**:
   - Media con intervalos de confianza sombreados
   - Permiten analizar velocidad de convergencia
   - Identificación de estancamiento

3. **Diagramas de Diferencia Crítica**:
   - Representación visual de tests post-hoc
   - Grupos de algoritmos sin diferencias significativas
   - Ranking relativo de algoritmos

4. **Soluciones VRP**:
   - Visualización de rutas óptimas encontradas
   - Comparación con soluciones conocidas

### Generación de Visualizaciones

Las visualizaciones se generan automáticamente al ejecutar benchmarks o al analizar archivos CSV existentes:

```bash
# Generar visualizaciones a partir de un archivo de resultados CSV
python scripts/analyze.py analyze-csv results/massive_benchmark_summary.csv
```

### Visualizaciones para Publicación

Para generar visualizaciones de calidad para publicación científica:

```bash
python scripts/analyze.py analyze-csv results/benchmark_final.csv \
    --publication-ready \
    --format pdf \
    --dpi 600 \
    --output-dir results/publication_figures
```
*   La opción `--publication-ready` ajusta el formato para su uso en publicaciones (fuentes, tamaños de línea, etc.).
*   `--format` permite elegir el formato del archivo (png, pdf, svg).
*   `--dpi` controla la resolución para formatos rasterizados (png).

## Ciclo Completo de Benchmarking

Un ciclo completo de benchmarking científico con BioAlgoCompare incluye estos pasos:

### 1. Planificación

- Definir claramente los objetivos del experimento (¿qué algoritmos comparar, en qué instancias, qué métricas evaluar?).
- Seleccionar algoritmos e instancias relevantes para el estudio.
- Determinar las métricas de rendimiento clave (calidad de solución, tiempo, robustez).
- Establecer un tamaño de muestra (número de runs) adecuado para el análisis estadístico planeado.
- Definir hipótesis a comprobar (ej: El algoritmo X es significativamente mejor que el algoritmo Y en la instancia Z).

### 2. Ejecución Exploratoria

Realizar ejecuciones rápidas con pocos runs e iteraciones para:
- Familiarizarse con el comportamiento de los algoritmos en las instancias seleccionadas.
- Estimar tiempos de ejecución y memoria para planificar el benchmark principal.
- Identificar posibles problemas o errores tempranamente.

```bash
# Ejecución exploratoria para estimar parámetros
python scripts/run.py --algorithm all --instance P-n16-k8 --runs 5 --iterations 100
```

### 3. Configuración de Parámetros

Si es necesario, explorar diferentes configuraciones de parámetros (población, operadores, etc.) para cada algoritmo con el fin de optimizar su rendimiento en las instancias seleccionadas. Esto puede requerir varios benchmarks de parámetros.

```bash
# Explorar configuraciones de parámetros para un algoritmo (ej. tamaño de población)
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto \
    --instances "P-n16-k8" \
    --population 20,30,50,100 \
    --runs 10 --seed 42
```

### 4. Benchmark Principal

Ejecutar el benchmark definitivo con los parámetros optimizados y un número suficiente de runs para análisis estadístico (≥30). Registrar cuidadosamente los parámetros y el entorno.

```bash
# Benchmark definitivo con parámetros optimizados
python scripts/analyze.py benchmark --run-benchmark \
    --algorithms egto,foa,hoa,woa,hho \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5" \
    --runs 30 --seed 42 --parallel
```

### 5. Validación Masiva (Opcional)

Para estudios que requieren muy alta confianza estadística o para caracterizar completamente el comportamiento de los mejores algoritmos, realizar una validación masiva con 1000+ runs por configuración. Utilizar la opción `--resume` es crucial para estas ejecuciones largas.

```bash
# Validación masiva de los mejores algoritmos
PYTHONPATH=./ python scripts/run_massive.py \
    --algorithm "egto,foa,hoa" \
    --instances "E-n22-k4" \
    --runs 1000 --parallel --resume
```

### 6. Análisis y Visualización

Utilizar las herramientas de análisis (`analyze-csv`) para procesar los resultados, realizar tests estadísticos, y generar visualizaciones. Consultar las secciones correspondientes de esta guía para más detalles.

```bash
# Análisis final con visualizaciones para publicación
python scripts/analyze.py analyze-csv \
    results/massive_benchmark_summary.csv \
    --publication-ready \
    --output-dir analysis_final
```

### 7. Interpretación de Resultados

Interpretar los resultados estadísticos y visuales en el contexto de las hipótesis planteadas. Identificar algoritmos con rendimiento significativamente diferente y cuantificar la magnitud de las diferencias (tamaño del efecto).

### 8. Reporte y Publicación

Documentar la metodología experimental, parámetros, entorno, y resultados de forma clara y transparente. Generar tablas y figuras de calidad para publicaciones científicas. Compartir código y datos para permitir la reproducibilidad.

## Interpretación de Resultados

Esta sección provee guía para interpretar las métricas y resultados estadísticos generados por BioAlgoCompare.

### Métricas Principales de Rendimiento

1. **Calidad de la Solución**:
   - **Mejor fitness encontrado**: El valor de la función objetivo de la mejor solución hallada. Se reporta la media, mediana y el mejor valor absoluto de múltiples runs.
   - **Gap respecto al óptimo conocido**: Diferencia porcentual entre el mejor fitness encontrado y el valor óptimo conocido para la instancia. Permite comparar el rendimiento de los algoritmos con el estado del arte.
   - **Desviación estándar y coeficiente de variación**: Miden la dispersión de los resultados entre múltiples runs, indicando la robustez o estabilidad del algoritmo.

2. **Eficiencia**:
   - **Tiempo de ejecución**: Tiempo que tarda un algoritmo en completar una ejecución. Crucial para aplicaciones con restricciones de tiempo.
   - **Número de evaluaciones de función objetivo**: Una medida independiente del hardware para comparar la eficiencia computacional de los algoritmos. BioAlgoCompare rastrea este número automáticamente.
   - **Velocidad de convergencia**: Qué tan rápido un algoritmo se acerca a una buena solución. Se visualiza con las curvas de convergencia.

3. **Robustez**:
   - **Consistencia entre ejecuciones**: Evaluada por la baja desviación estándar de los resultados. Un algoritmo robusto produce resultados similares en runs independientes.
   - **Sensibilidad a la inicialización**: Cómo varía el rendimiento con diferentes semillas aleatorias. Los benchmarks masivos con múltiples semillas ayudan a evaluar esto.
   - **Comportamiento en diferentes instancias**: Qué tan bien se generaliza el rendimiento de un algoritmo a distintas características de problemas (tamaño, estructura).

### Interpretación Estadística Rigurosa

BioAlgoCompare utiliza pruebas estadísticas no paramétricas (como Friedman y Wilcoxon) que no asumen normalidad de los datos, comunes en resultados de optimización. La interpretación se basa en:

- **Nivel de significancia (α)**: Por defecto 0.05. Representa la probabilidad de rechazar la hipótesis nula (H₀) cuando es verdadera (error Tipo I). Un p-valor menor a α indica evidencia contra H₀.
- **p-valor**: La probabilidad de observar los datos (o datos más extremos) si la hipótesis nula fuera verdadera. Si p-valor < α, se rechaza H₀.
- **Ranking**: El orden de desempeño promedio de los algoritmos basado en los rangos asignados en las pruebas no paramétricas (ej. test de Friedman). Un ranking menor suele indicar mejor rendimiento (para problemas de minimización).
- **Tamaño del efecto**: Cuantifica la magnitud práctica de la diferencia entre algoritmos, complementando la significancia estadística. Medidas como A12 de Vargha-Delaney y Delta de Cliff indican si una diferencia estadísticamente significativa es también relevante en la práctica. Guías para interpretar A12 se proveen en la sección de Análisis Estadístico.
- **Intervalos de confianza**: Proporcionan un rango estimado para el verdadero valor de una métrica (ej. media del fitness). Si los intervalos de confianza del 95% para dos algoritmos no se solapan, sugiere una diferencia estadísticamente significativa.

### Ejemplo de Interpretación Completa

Para ilustrar cómo combinar los resultados de un benchmark riguroso, consideremos un ejemplo ficticio:

*   **Contexto**: Benchmark de 4 algoritmos (A, B, C, D) en 5 instancias VRP, con 30 runs por configuración.
*   **Resultados Estadísticos**: Test de Friedman (p < 0.01) indica diferencias significativas. Pruebas post-hoc de Nemenyi y análisis de tamaño del efecto A12.

```
Resultado: El test de Friedman indica diferencias estadísticamente significativas entre los algoritmos (p < 0.001). 
Las pruebas post-hoc de Nemenyi muestran que el Algoritmo A supera significativamente a los Algoritmos C y D (p_adj < 0.01), 
con un tamaño de efecto grande (A12 = 0.85 y 0.91, respectivamente). El Algoritmo B no 
presenta diferencias significativas con el Algoritmo A (p_adj = 0.14), pero sí supera a los Algoritmos C y D 
(p_adj < 0.05, A12 = 0.68 y 0.75).

Conclusión: El Algoritmo A y el Algoritmo B forman un grupo de algoritmos con el mejor desempeño en las instancias evaluadas, 
siendo estadísticamente indistinguibles entre sí en este benchmark particular. Ambos algoritmos superan significativamente 
en rendimiento a los Algoritmos C y D, con diferencias que se consideran de magnitud práctica relevante.
Se recomienda utilizar el Algoritmo A o B para aplicaciones que requieran alta calidad de solución en estas instancias. 
Para una selección final entre A y B, se podrían considerar otras métricas como tiempo de ejecución o robustez en un conjunto más amplio de instancias.
```

Este ejemplo demuestra cómo los p-valores, los rankings, el tamaño del efecto y los intervalos de confianza se combinan para extraer conclusiones científicas sólidas a partir de los resultados de benchmarking.

## Publicación de Resultados

Para preparar resultados de benchmark para publicación científica, BioAlgoCompare facilita la generación de los elementos necesarios:

### 1. Tablas de Resultados

Generar tablas resumen con métricas clave para cada algoritmo e instancia. El formato LaTeX es común en publicaciones científicas.

```bash
# Generar tablas LaTeX para publicación
python scripts/analyze.py analyze-csv results/benchmark_final.csv \
    --export-tables latex \
    --output-dir results/publication
```
*   Esto generará archivos `.tex` con tablas formateadas.

### 2. Figuras

Generar visualizaciones de alta calidad (vectoriales preferiblemente) para ilustrar los hallazgos. Boxplots, curvas de convergencia y diagramas CD son esenciales.

```bash
# Generar figuras vectoriales de alta calidad
python scripts/analyze.py analyze-csv results/benchmark_final.csv \
    --publication-ready \
    --format pdf \
    --dpi 600 \
    --output-dir results/publication
```
*   La opción `--publication-ready` optimiza el formato visual.
*   Especificar `--format pdf` o `--format svg` para figuras vectoriales.

### 3. Protocolo Experimental Completo

En la sección de metodología de la publicación, documente siempre:

- **Hardware utilizado**: Especificaciones de CPU, cantidad de RAM, tipo de almacenamiento, sistema operativo.
- **Software**: Versión de Python, lista exacta de bibliotecas Python (`pip freeze > requirements.txt`), y la versión o commit de BioAlgoCompare utilizado.
- **Parámetros completos**: Todos los parámetros utilizados para cada algoritmo y en los scripts de benchmark (`--runs`, `--iterations`, `--population`, `--seed`, `--parallel`, etc.). Guardar el comando exacto ejecutado es muy útil.
- **Metodología estadística**: Los tests aplicados (Friedman, Wilcoxon, etc.), el nivel de significancia (α), y el método de corrección para comparaciones múltiples (Bonferroni, Holm).
- **Código fuente y Datos**: Proporcionar un enlace al repositorio de código fuente de BioAlgoCompare (si se usó la versión pública) o incluir una copia del código con las modificaciones realizadas. Hacer los datos brutos y procesados accesibles para verificación y análisis independiente (repositorio de datos, suplemento).

### 4. Datos y Entorno para Reproducibilidad

Para facilitar que otros investigadores reproduzcan exactamente los resultados, considere empaquetar los datos y la información del entorno:

```bash
# Comprimir todos los resultados, metadatos y información del entorno para compartir
tar -czf benchmark_complete_results.tar.gz \
    results/massive_benchmark_summary.csv \
    results/benchmark_final.csv  # Incluir otros archivos relevantes si existen \
    benchmark_environment.txt \
    benchmark_command.txt \
    system_info.txt \
    cpu_info.txt
```

## Recursos Adicionales

- [Referencia de Comandos](../COMMAND_REFERENCE.md)
- [Referencia Técnica de Scripts](../technical/scripts_reference.md)
- [Documentación de Algoritmos](../algorithms/overview.md)
- [Análisis Comparativo](../analysis/comparison.md)
- [Principios FAIR de datos científicos](https://www.go-fair.org/fair-principles/)
- [Journal of Open Source Software (Guidelines)](https://joss.readthedocs.io/en/latest/review_criteria.html)
- [Lineamientos de reproducibilidad de ACM](https://www.acm.org/publications/policies/artifact-review-and-badging-current)
- [Checklist for Computational Research de Nature](https://www.nature.com/documents/nr-reporting-summary-flat.pdf)

---

*Última actualización: 16 de mayo de 2025*