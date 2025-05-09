# Estado de Consolidación de Scripts

Este documento registra el estado actual de la consolidación de scripts en el proyecto BioAlgoCompare, siguiendo el plan descrito en [consolidation_plan_revised.md](../development/consolidation_plan_revised.md).

## Resumen Actual

| Script | Ubicación | Estado | Notas |
|--------|-----------|--------|-------|
| `run.py` | `scripts/run.py` | ✅ Consolidado | Versión de raíz movida a scripts/ |
| `analyze_results.py` | `scripts/legacy/analyze_results.py` | ✅ Consolidado | Versión antigua, movida a legacy/ |
| `analyze_1000runs.py` | `scripts/legacy/analyze_1000runs.py` | ✅ Consolidado | Versión antigua, movida a legacy/ |
| `run_massive.py` | `scripts/run_massive.py` | ✅ Consolidado | Versión idéntica en ambas ubicaciones |
| `analyze.py` | `scripts/analyze.py` | ✅ Consolidado | Script unificado principal |

## Pasos Completados

1. ✅ Análisis inicial de scripts duplicados
2. ✅ Identificación de versiones más actualizadas
3. ✅ Creación de estructura `scripts/legacy/` para scripts obsoletos
4. ✅ Movimiento de scripts redundantes a la estructura correcta
5. ✅ Documentación completa de scripts en [scripts_reference.md](scripts_reference.md)
6. ✅ Actualización de guías para reflejar nueva estructura

## Estrategia de Ejecución

Tras la consolidación, los scripts deben ejecutarse de la siguiente manera:

### Ejecución de Algoritmos Individuales

```bash
python scripts/run.py --algorithm ALGORITMO --instance INSTANCIA [opciones]
```

### Benchmarking y Análisis

```bash
python scripts/analyze.py COMANDO [opciones]
```

Comandos disponibles:
- `run`: Ejecución de algoritmos (similar a `run.py`)
- `benchmark`: Benchmarking comparativo
- `massive`: Ejecuciones masivas (1000+)
- `analyze-csv`: Análisis de resultados existentes

### Script Legacy (Mantienen compatibilidad)

Los scripts en `scripts/legacy/` se mantienen por compatibilidad con trabajos anteriores, pero se desaconseja su uso para nuevos proyectos:

```bash
# NO RECOMENDADO (usar scripts/analyze.py en su lugar)
python scripts/legacy/analyze_results.py [opciones]
```

## Ventajas de la Consolidación

1. **Simplificación**: Un punto de entrada claro para cada tipo de funcionalidad
2. **Mantenibilidad**: Código duplicado eliminado
3. **Consistencia**: Estándares uniformes en todos los scripts
4. **Claridad**: Documentación completa y actualizada

## Próximos Pasos

Si se necesitan nuevas funcionalidades, se recomienda:

1. Extender `scripts/analyze.py` con nuevos subcomandos
2. Documentar cualquier adición en `scripts_reference.md`
3. Actualizar guías relevantes

## Metodología Científica

El enfoque consolidado facilita la reproducibilidad científica mediante:

1. **Provenance completa**: Todos los parámetros y configuraciones quedan documentados
2. **Versionado**: Control claro de versiones de scripts
3. **Transparencia**: Flujo de trabajo documentado y estructurado
4. **Simplicidad**: Reducción en complejidad para usuarios y desarrolladores

Para información completa sobre rigor científico, consulte [reproducibility.md](../scientific/reproducibility.md).