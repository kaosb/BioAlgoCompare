# Guía de Reproducibilidad y Rigor Científico

Este documento proporciona directrices detalladas para garantizar la reproducibilidad, transparencia y rigor científico en los experimentos realizados con BioAlgoCompare. Está dirigido a investigadores, académicos y profesionales que buscan realizar estudios comparativos rigurosos de algoritmos metaheurísticos.

## Contenido

1. [Principios de Reproducibilidad](#principios-de-reproducibilidad)
2. [Control de Semillas Aleatorias](#control-de-semillas-aleatorias)
3. [Documentación Experimental Completa](#documentación-experimental-completa)
4. [Garantías Estadísticas](#garantías-estadísticas)
5. [Visualización Científica](#visualización-científica)
6. [Generación de Informes Reproducibles](#generación-de-informes-reproducibles)
7. [Lista de Verificación para Publicaciones](#lista-de-verificación-para-publicaciones)

## Principios de Reproducibilidad

La investigación reproducible requiere que los experimentos computacionales puedan ser replicados exactamente por otros investigadores. BioAlgoCompare aplica estos principios fundamentales:

### 1. Determinismo Controlado

Todos los componentes aleatorios del sistema pueden ser controlados mediante semillas explícitas. Esto garantiza que:

- Las mismas entradas producen exactamente las mismas salidas
- Las variaciones observadas se deben a factores experimentales, no a la inicialización aleatoria
- Los experimentos pueden ser validados de forma independiente

### 2. Documentación Experimental Completa

Cada experimento registra automáticamente:

- Parámetros completos de algoritmos
- Configuración de ejecución
- Semillas aleatorias
- Metadatos del entorno de ejecución

### 3. Transparencia y Verificabilidad

- Código fuente abierto y disponible
- Datos brutos accesibles
- Procedimientos analíticos documentados
- Análisis estadístico reproducible

## Control de Semillas Aleatorias

### Importancia de las Semillas

Las semillas aleatorias controlan la inicialización de los generadores de números pseudo-aleatorios. En los algoritmos metaheurísticos, esto afecta a:

- Generación de la población inicial
- Operadores estocásticos (mutación, cruce, etc.)
- Selección probabilística
- Cualquier decisión basada en aleatoriedad

### Implementación en BioAlgoCompare

Todos los scripts aceptan un parámetro `--seed` que:

1. **Establece la semilla global de NumPy**: `np.random.seed(seed)`
2. **Establece la semilla de algoritmos individuales**:
   ```python
   algo = Algorithm(problem, seed=run_seed)
   ```
3. **En ejecuciones múltiples, deriva semillas sistemáticamente**:
   ```python
   run_seed = base_seed + run_index
   ```

### Mejores Prácticas para Semillas

1. **Usar semillas explícitas en todos los experimentos**:
   ```bash
   python scripts/run.py --algorithm egto --instance E-n22-k4 --seed 42
   ```

2. **Documentar la semilla utilizada**:
   ```bash
   echo "Seed: 42" >> experiment_metadata.txt
   ```

3. **Para comparaciones justas, usar la misma semilla en todos los algoritmos**:
   ```bash
   python scripts/analyze.py benchmark --run-benchmark --seed 42 \
       --algorithms egto,foa,hoa
   ```

4. **Para análisis estadísticos, usar múltiples semillas**:
   ```bash
   python scripts/analyze.py massive --runs 1000 --seed 42
   ```

## Documentación Experimental Completa

### Metadatos Automáticos

Cada ejecución guarda automáticamente:

1. **Parámetros de algoritmo**:
   - Nombre del algoritmo
   - Tamaño de población
   - Número de iteraciones
   - Parámetros específicos

2. **Parámetros de problema**:
   - Instancia VRP
   - Dimensión, capacidad
   - Valor óptimo conocido

3. **Condiciones de ejecución**:
   - Semilla aleatoria
   - Timestamp
   - Número de repeticiones
   - Configuración de paralelización

### Metadatos Complementarios

Para experimentos académicos completos, documente adicionalmente:

1. **Entorno computacional**:
   ```bash
   # Guardar información del sistema
   uname -a > system_info.txt

   # Guardar versiones de software
   pip freeze > requirements_frozen.txt

   # Guardar información de CPU
   lscpu > cpu_info.txt
   ```

2. **Procedimiento experimental completo**:
   - Crear un archivo README.md con la metodología
   - Incluir el comando exacto ejecutado
   - Documentar pre/post-procesamiento

3. **Código fuente utilizado**:
   - Si se modificó el código, incluir los cambios
   - O proporcionar la versión/commit exacto usado

## Garantías Estadísticas

### Tamaño de Muestra Adecuado

El número mínimo de ejecuciones depende del análisis:

1. **Estudios exploratorios**: 5-10 ejecuciones
2. **Comparaciones estadísticas**: 30+ ejecuciones
3. **Análisis de alta precisión**: 1000+ ejecuciones

```bash
# Para análisis estadístico riguroso
python scripts/analyze.py benchmark --run-benchmark \
    --runs 30 --seed 42 \
    --algorithms egto,foa,hoa
```

### Tests Estadísticos Implementados

BioAlgoCompare implementa automáticamente:

1. **Pruebas de normalidad**:
   - Shapiro-Wilk para comprobar distribución normal
   - QQ-plots para visualización

2. **Comparación múltiple**:
   - Test de Friedman (no paramétrico)
   - ANOVA (paramétrico, si aplicable)
   - Ajuste post-hoc con corrección

3. **Comparación por pares**:
   - Wilcoxon signed-rank test
   - T-test pareado (si aplicable)

4. **Tamaño del efecto**:
   - A12 de Vargha-Delaney
   - Delta de Cliff

### Interpretación Correcta

La documentación incluye guía para interpretar:

- Nivel de significancia (α) y p-valores
- Intervalos de confianza
- Medidas de tamaño del efecto

## Visualización Científica

### Visualizaciones Estadísticamente Rigurosas

1. **Boxplots con notches**:
   - Muestran mediana e IQR
   - Notches para test visual de diferencia
   - Outliers identificados explícitamente

2. **Curvas de convergencia con intervalos**:
   - Media/mediana de múltiples ejecuciones
   - Intervalo de confianza/IQR sombreado
   - Escala logarítmica cuando apropiado

3. **Diagramas de ranking crítico**:
   - Basados en test de Nemenyi
   - Muestran significancia con agrupaciones

### Generación con BioAlgoCompare

```bash
# Visualizaciones para publicación
python scripts/analyze.py analyze-csv results/benchmark_final.csv \
    --publication-ready \
    --format pdf \
    --dpi 600
```

## Generación de Informes Reproducibles

BioAlgoCompare puede generar:

1. **Informes HTML interactivos**:
   - Visualizaciones dinámicas
   - Tablas completas de resultados
   - Metadatos y metodología documentados

2. **Tablas LaTeX** para publicaciones:
   ```bash
   python scripts/analyze.py analyze-csv results/benchmark_final.csv \
       --export-tables latex
   ```

3. **Gráficos vectoriales** para publicaciones:
   ```bash
   python scripts/analyze.py analyze-csv results/benchmark_final.csv \
       --publication-ready \
       --format pdf
   ```

## Lista de Verificación para Publicaciones

Antes de finalizar una investigación para publicación, asegúrese de:

### 1. Diseño Experimental

- [ ] Definir hipótesis clara a contrastar
- [ ] Seleccionar algoritmos representativos
- [ ] Elegir instancias de problema adecuadas
- [ ] Determinar número de ejecuciones estadísticamente válido
- [ ] Definir medidas de rendimiento y métricas

### 2. Ejecución Rigurosa

- [ ] Usar semillas aleatorias explícitas
- [ ] Garantizar condiciones iguales para todos los algoritmos
- [ ] Documentar entorno computacional completo
- [ ] Guardar resultados brutos y procesados
- [ ] Mantener provenance de todos los datos

### 3. Análisis Estadístico

- [ ] Verificar normalidad de los datos
- [ ] Aplicar tests estadísticos apropiados
- [ ] Usar corrección para comparaciones múltiples
- [ ] Reportar intervalos de confianza
- [ ] Incluir medidas de tamaño del efecto

### 4. Reporte

- [ ] Incluir toda la metodología experimental
- [ ] Reportar configuración de parámetros completa
- [ ] Presentar visualizaciones estadísticamente rigurosas
- [ ] Discutir limitaciones del estudio
- [ ] Proporcionar código y datos para reproducibilidad

## Recursos Adicionales

- [Principios FAIR de datos científicos](https://www.go-fair.org/fair-principles/)
- [Journal of Open Source Software (Guidelines)](https://joss.readthedocs.io/en/latest/review_criteria.html)
- [Lineamientos de reproducibilidad de ACM](https://www.acm.org/publications/policies/artifact-review-and-badging-current)
- [Checklist for Computational Research de Nature](https://www.nature.com/documents/nr-reporting-summary-flat.pdf)
