# Plan de Consolidación de Scripts y Mejora Científica (Revisado)

Este documento detalla el plan para consolidar los scripts duplicados y mejorar la estructura del proyecto con un enfoque en investigación científica, reproducibilidad, transparencia, verbosidad, precisión y explicabilidad.

## 1. Situación Actual

Actualmente, el proyecto presenta duplicidad de scripts entre el directorio raíz y el subdirectorio `scripts/`:

| Script en Raíz | Script en `scripts/` | Observaciones |
|----------------|----------------------|---------------|
| `run.py` | `scripts/run.py` | Versión del raíz ligeramente más actualizada |
| `analyze_results.py` | `scripts/analyze_results.py` | Versión en `scripts/` más completa |
| `run_massive.py` | `scripts/run_massive.py` | Idénticos |
| `analyze_1000runs.py` | Funcionalidad incluida en `scripts/analyze.py` | Consolidado en script unificado |

Además, existe un script unificado `scripts/analyze.py` que integra la funcionalidad de varios scripts de análisis anteriores.

## 2. Estrategia de Consolidación

### 2.1 Estructura Consolidada Propuesta

```
optimizacion/
├── scripts/                 # Todos los scripts ejecutables principales
│   ├── run.py               # Ejecución de algoritmos individuales
│   ├── run_massive.py       # Ejecución masiva (1000+ repeticiones)
│   ├── analyze.py           # Script unificado de análisis (CLI principal)
│   └── legacy/              # Scripts antiguos (por compatibilidad)
│       ├── analyze_results.py   # Versión anterior, mantenida para compatibilidad
│       └── analyze_csv.py       # Versión anterior, mantenida para compatibilidad
├── utils/                   # Utilidades y herramientas
│   ├── benchmarking.py       # Sistema de benchmarking
│   ├── statistical_analysis.py # Análisis estadístico
│   ├── visualization.py      # Visualización básica
│   └── improved/             # Módulos mejorados
│       ├── enhanced_benchmarking.py  # Benchmarking con checkpoints
│       ├── advanced_visualization.py # Visualizaciones avanzadas 
│       └── enhanced_statistics.py    # Estadísticas rigurosas
```

### 2.2 Principales Cambios Propuestos

1. **Consolidar todos los scripts principales en directorio `scripts/`**:
   - Centralizar todos los scripts ejecutables en una ubicación
   - Eliminar duplicados en el directorio raíz
   - Mover `analyze.py` a primer nivel en `scripts/` como entrada principal
   - Usar subcomandos en `analyze.py` para todas las funcionalidades

2. **Mantener compatibilidad con instrucciones existentes**:
   - Crear enlaces simbólicos en raíz si es necesario
   - Documentar claramente la estructura y uso

3. **Reorganizar scripts obsoletos**:
   - Mover scripts antiguos o duplicados a `scripts/legacy/`
   - Mantenerlos por compatibilidad pero advertir sobre su eventual eliminación

## 3. Mejoras para Investigación Científica

### 3.1 Reproducibilidad

1. **Gestión de semillas aleatorias**:
   - Documentar claramente el uso y control de semillas
   - Almacenar semilla usada en los resultados
   - Permitir reproducir exactamente cualquier experimento

2. **Registro de configuración completa**:
   - Guardar todos los parámetros usados en cada ejecución
   - Incluir versiones de bibliotecas/dependencias

3. **Persistencia de datos intermedios**:
   - Permitir guardar estados intermedios en ejecuciones largas
   - Sistema de checkpoint para recuperar experimentos interrumpidos

### 3.2 Transparencia

1. **Registro detallado (logging)**:
   - Implementar logging a múltiples niveles
   - Documentar cada paso del proceso de optimización
   - Capturar advertencias y errores

2. **Informes auto-explicativos**:
   - Generar informes HTML con metadata completa
   - Incluir detalles metodológicos en los resultados

### 3.3 Precisión y Verbosidad

1. **Estadísticas robustas**:
   - Implementar intervalos de confianza para todas las métricas
   - Aplicar tests estadísticos con corrección para comparaciones múltiples
   - Reportar tamaño del efecto además de significancia

2. **Documentación extendida**:
   - Describir detalladamente cada algoritmo y sus parámetros
   - Documentar las instancias VRP con sus características
   - Explicar las métricas de evaluación utilizadas

### 3.4 Explicabilidad

1. **Visualizaciones avanzadas**:
   - Implementar gráficos comparativos con intervalos de confianza
   - Visualizar distribuciones completas, no solo promedios
   - Crear diagramas de ranking y diferencia crítica

2. **Análisis de convergencia**:
   - Estudiar patrones de convergencia de algoritmos
   - Comparar velocidad de convergencia entre métodos
   - Identificar estancamiento y comportamiento asintótico

## 4. Plan de Implementación

### Fase 1: Consolidación de Scripts

1. Identificar las versiones más actualizadas de cada script (COMPLETADO)
2. Mover los scripts seleccionados a sus ubicaciones finales
3. Eliminar los scripts redundantes o moverlos a `scripts/legacy/`
4. Validar la funcionalidad con pruebas comparativas

### Fase 2: Mejoras de Documentación

1. Actualizar guías de instalación y uso para reflejar la nueva estructura
2. Completar guías faltantes mencionadas en la documentación
3. Mejorar la documentación científica sobre algoritmos, instancias y análisis
4. Crear ejemplos de uso para casos comunes

### Fase 3: Mejoras Científicas

1. Implementar mejoras en transparencia y logging
2. Extender estadísticas y visualizaciones
3. Documentar cada componente con enfoque científico

## 5. Estándares de Documentación Científica

Para asegurar que la documentación cumpla con estándares científicos rigurosos, seguiremos estas pautas:

1. **Precisión Terminológica**:
   - Utilizar términos técnicos precisos y consistentes
   - Definir claramente conceptos especializados
   - Evitar ambigüedades en la descripción de algoritmos y métodos

2. **Estructura Científica**:
   - Incluir siempre: Objetivo, Método, Resultados, Conclusiones
   - Separar claramente hechos de interpretaciones
   - Presentar evidencia antes de conclusiones

3. **Transparencia Metodológica**:
   - Describir en detalle todos los parámetros y su influencia
   - Explicar los procedimientos de inicialización
   - Documentar decisiones de diseño y sus justificaciones

4. **Rigor Estadístico**:
   - Especificar las pruebas estadísticas utilizadas
   - Incluir información de significancia y potencia estadística
   - Documentar limitaciones y posibles sesgos

5. **Reproducibilidad**:
   - Proporcionar todos los detalles necesarios para reproducir experimentos
   - Incluir versiones de software y dependencias
   - Usar semillas aleatorias y documentarlas

## 6. Referencias y Estándares

- [The Practice of Reproducible Research](https://www.practicereproducibleresearch.org/)
- [Nature's Reporting Standards for Statistical Analyses](https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards)
- [FAIR Principles for Scientific Data](https://www.go-fair.org/fair-principles/)
- [Software Carpentry Best Practices](https://software-carpentry.org/lessons/)