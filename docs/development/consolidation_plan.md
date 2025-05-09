# Plan de Consolidación de Scripts y Mejora Científica

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
BioAlgoCompare/
├── bioalgo/                 # Módulo principal para instalación
│   ├── __init__.py          # Inicialización del módulo
│   ├── cli.py               # Punto de entrada CLI unificado
│   ├── runners/             # Módulos de ejecución
│   │   ├── __init__.py      
│   │   ├── run.py           # Ejecución de algoritmos individuales
│   │   └── massive.py       # Ejecución masiva
│   └── analysis/            # Módulos de análisis
│       ├── __init__.py
│       ├── benchmark.py     # Benchmarking
│       ├── statistics.py    # Análisis estadístico
│       └── visualization.py # Visualización científica
├── scripts/                 # Scripts de conveniencia (wrappers)
│   ├── run_bioalgo.py       # Wrapper para bioalgo run
│   └── analyze_bioalgo.py   # Wrapper para bioalgo analyze
```

### 2.2 Principales Cambios Propuestos

1. **Crear un módulo `bioalgo` instalable**:
   - Facilita la instalación y uso del proyecto
   - Sigue buenas prácticas de estructuración de paquetes Python
   - Permite invocar el comando `bioalgo` desde cualquier directorio

2. **Implementar un CLI unificado con subcomandos**:
   - `bioalgo run`: Para ejecución de algoritmos individuales
   - `bioalgo benchmark`: Para benchmarking comparativo
   - `bioalgo analyze`: Para análisis estadístico de resultados
   - `bioalgo massive`: Para ejecuciones masivas (1000+)

3. **Mantener scripts wrapper en `scripts/`**:
   - Asegurar compatibilidad con comandos anteriores
   - Facilitar la transición a la nueva estructura

4. **Eliminar scripts duplicados del directorio raíz**:
   - Una vez confirmada la funcionalidad completa en la estructura consolidada

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

### Fase 1: Reorganización de Scripts

1. Crear la estructura básica del módulo `bioalgo`
2. Migrar funcionalidad de `scripts/analyze.py` a `bioalgo/cli.py`
3. Implementar wrappers compatibles en `scripts/`
4. Validar funcionalidad con pruebas comparativas

### Fase 2: Mejoras Científicas

1. Implementar mejoras de reproducibilidad
2. Mejorar sistema de logging y transparencia
3. Extender estadísticas y visualizaciones
4. Documentar cada componente con enfoque científico

### Fase 3: Documentación Final

1. Actualizar guías de instalación y uso
2. Crear documentación adicional para análisis científicos
3. Desarrollar notebooks de ejemplo para casos de uso comunes
4. Implementar tests automatizados para validar resultados

## 5. Referencias y Estándares

- [The Practice of Reproducible Research](https://www.practicereproducibleresearch.org/)
- [Nature's Reporting Standards for Statistical Analyses](https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards)
- [FAIR Principles for Scientific Data](https://www.go-fair.org/fair-principles/)
- [Software Carpentry Best Practices](https://software-carpentry.org/lessons/)