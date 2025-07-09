# Tareas de Estabilización - BioAlgoCompare

## 🔴 CRÍTICO - Sistema Unificado de Resultados (Semana 1-2)

### Tarea 1: Auditoría y Decisión de Sistema de Resultados
- [ ] Analizar en detalle los 4 sistemas existentes
- [ ] Documentar pros/contras de cada uno
- [ ] Decidir sistema base (recomendado: StandardResult)
- [ ] Crear plan de migración

### Tarea 2: Refactorizar StandardResult como Sistema Único
- [ ] Integrar mejores características de otros sistemas
- [ ] Añadir campos faltantes (git_hash, memory_usage, etc.)
- [ ] Implementar serialización robusta
- [ ] Crear validadores de esquema

### Tarea 3: Implementar Pipeline Unificado
- [ ] Modificar base_v2.py para usar StandardResult
- [ ] Crear ResultCollector para captura automática
- [ ] Implementar almacenamiento en SQLite
- [ ] Crear sistema de caché de resultados

### Tarea 4: Migrar Algoritmos Existentes
- [ ] Actualizar HOA para usar nuevo sistema
- [ ] Migrar resto de algoritmos (uno por uno)
- [ ] Actualizar tests correspondientes
- [ ] Validar backward compatibility

### Tarea 5: Implementar Exportadores Estándar
- [ ] Crear ResultExporter base class
- [ ] Implementar CSVExporter con formato fijo
- [ ] Implementar JSONExporter con metadatos completos
- [ ] Implementar LaTeXExporter para tablas
- [ ] Implementar HDF5Exporter para big data

## 🟠 ALTA PRIORIDAD - Eliminación de Duplicados (Semana 3)

### Tarea 6: Extraer Operadores Comunes
- [ ] Crear utils/metaheuristic_operators.py
- [ ] Mover levy_flight() y variantes
- [ ] Mover operadores de mutación
- [ ] Actualizar imports en algoritmos
- [ ] Eliminar código duplicado

### Tarea 7: Unificar Clases Individual
- [ ] Analizar variaciones entre clases Individual
- [ ] Crear IndividualFactory
- [ ] Implementar mixins para comportamientos
- [ ] Migrar algoritmos a factory pattern
- [ ] Eliminar clases Individual redundantes

### Tarea 8: Consolidar Validación de Parámetros  
- [ ] Crear sistema de decoradores @validate_parameters
- [ ] Definir esquemas de parámetros por algoritmo
- [ ] Implementar validación automática
- [ ] Eliminar código de validación duplicado
- [ ] Añadir tests de validación

## 🟡 ALTA - Reorganización Estructural (Semana 4)

### Tarea 9: Limpiar y Reorganizar Scripts
- [ ] Crear nueva estructura scripts/cli/, scripts/tools/
- [ ] Consolidar scripts de ejecución
- [ ] Eliminar scripts deprecated
- [ ] Actualizar entry points en setup.py
- [ ] Documentar uso de cada script

### Tarea 10: Resolver Estado de Archivos Legacy
- [ ] Crear branch legacy-v1 con código antiguo
- [ ] Eliminar legacy/ del main branch
- [ ] Actualizar imports y referencias
- [ ] Documentar migración en CHANGELOG
- [ ] Limpiar git history

### Tarea 11: Consolidar Documentación
- [ ] Crear estructura docs/{user_guide,developer,api,algorithms,theory}
- [ ] Mover documentos a carpetas apropiadas
- [ ] Crear índice principal README.md
- [ ] Eliminar documentos redundantes
- [ ] Generar documentación API automática

## 🟢 MEDIA - Testing y Calidad (Semana 5)

### Tarea 12: Refactorizar Tests de Migración
- [ ] Crear test base parametrizado
- [ ] Eliminar duplicación en tests
- [ ] Añadir tests de edge cases
- [ ] Mejorar cobertura a >80%
- [ ] Documentar estrategia de testing

### Tarea 13: Implementar CI/CD Completo
- [ ] Configurar GitHub Actions
- [ ] Añadir badge de cobertura
- [ ] Configurar linting automático
- [ ] Implementar deployment automático de docs
- [ ] Añadir checks de seguridad

### Tarea 14: Resolver TODOs y FIXMEs
- [ ] Listar todos los TODOs/FIXMEs
- [ ] Priorizar y resolver o eliminar
- [ ] Completar implementaciones con 'pass'
- [ ] Documentar decisiones tomadas
- [ ] Añadir política de no-TODOs

## 🔵 ALTA - Reproducibilidad Científica (Semana 6)

### Tarea 15: Forzar RandomStateManager
- [ ] Validar uso en todos los algoritmos
- [ ] Añadir checks en __init__
- [ ] Crear tests de reproducibilidad
- [ ] Documentar mejores prácticas
- [ ] Eliminar uso directo de np.random

### Tarea 16: Implementar Versionado de Resultados
- [ ] Añadir VERSION a result schema
- [ ] Implementar migración de versiones
- [ ] Crear validador de compatibilidad
- [ ] Documentar cambios entre versiones
- [ ] Añadir tests de migración

### Tarea 17: Completar Sistema de Metadatos
- [ ] Definir metadatos obligatorios
- [ ] Capturar información de sistema automáticamente
- [ ] Registrar dependencias y versiones
- [ ] Añadir git hash y branch info
- [ ] Validar completitud de metadatos

## ⚪ MEDIA - Preparación Publicación (Semana 7)

### Tarea 18: Crear Utils de Publicación
- [ ] Implementar generador de tablas LaTeX
- [ ] Crear templates para IEEE/Elsevier/Springer
- [ ] Implementar gráficos de calidad publicación
- [ ] Añadir análisis estadístico automático
- [ ] Crear ejemplos de uso

### Tarea 19: Sistema de Validación de Resultados
- [ ] Implementar comparación con óptimos conocidos
- [ ] Crear detector de anomalías
- [ ] Añadir validación estadística
- [ ] Implementar certificación con hash
- [ ] Documentar proceso de validación

### Tarea 20: Documentación Final
- [ ] Crear guía de usuario completa
- [ ] Documentar proceso de investigación
- [ ] Crear tutoriales paso a paso
- [ ] Generar API reference
- [ ] Preparar material suplementario para papers

## 📊 Métricas de Progreso

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Sistemas de resultados | 4 | 1 |
| Código duplicado | ~25% | <5% |
| Cobertura de tests | Desconocida | >80% |
| TODOs pendientes | 20+ | 0 |
| Documentación | Dispersa | Organizada |
| Reproducibilidad | Parcial | 100% |

## 🚀 Quick Wins (Hacer Primero)

1. **Eliminar imports no usados** (30 min)
2. **Crear .gitignore para limpiar status** (15 min)
3. **Resolver archivos legacy** (1 hora)
4. **Parametrizar un test de migración como ejemplo** (1 hora)
5. **Documentar decisión sobre sistema de resultados** (2 horas)

## 📝 Notas Importantes

- Cada tarea completada debe documentarse en CHANGELOG
- Crear PRs pequeños y enfocados
- Mantener backward compatibility cuando sea posible
- Priorizar cambios que afecten la reproducibilidad
- Testear exhaustivamente cambios en sistema de resultados