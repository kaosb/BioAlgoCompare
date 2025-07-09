# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-XX

### 🎉 Mayor Release - Arquitectura v2

Esta versión representa una reescritura completa del framework con mejoras significativas en arquitectura, rendimiento y usabilidad.

### ✨ Agregado

#### Nueva Arquitectura
- **Arquitectura v2** completamente rediseñada con `base_v2.py`
- Sistema de **MoveContext** para paso consistente de parámetros
- **Factory patterns** para creación de objetos
- **RandomStateManager** para reproducibilidad mejorada
- Sistema completo de **validación de parámetros** con mensajes descriptivos

#### CLI Unificado
- Nuevo comando `bioalgocompare` que integra toda la funcionalidad
- Comandos: `run`, `benchmark`, `analyze`, `datasets`, `migrate`, `info`, `inventory`, `dashboard`
- Soporte para modos: `standard`, `massive` (1000 runs), `experiment`
- Sistema de checkpoints para ejecuciones largas
- Ejecución paralela mejorada con control de workers

#### Algoritmos Migrados a v2
- **18 algoritmos** completamente migrados y optimizados:
  - WOA (Whale Optimization Algorithm)
  - SMA (Slime Mould Algorithm)
  - GTO (Gorilla Troops Optimizer)
  - MRFO (Manta Ray Foraging Optimization)
  - EGTO (Enhanced Gorilla Troops Optimizer)
  - AHA (Artificial Hummingbird Algorithm)
  - EWA (Earthworm Algorithm)
  - FSA (Fish School Algorithm)
  - APO (African Penguin Optimization)
  - GVOA (Growth Variation Optimization Algorithm)
  - OPA (Orca Predation Algorithm)
  - RRO (Raven Roosting Optimization)
  - SMO (Starling Murmuration Optimizer)
  - HOA (Hyena Optimization Algorithm)
  - FGO (Flamingo Optimization Algorithm)
  - SHO (Spotted Hyena Optimizer)
  - FOA (Fruit Fly Optimization Algorithm)
  - HHO (Harris Hawks Optimization)

#### Documentación
- Guía completa de instalación (`INSTALLATION.md`)
- Guía de inicio rápido (`QUICKSTART.md`)
- Documentación de API (`API.md`)
- Documentación del CLI (`CLI.md`)
- Guía de validación de parámetros (`VALIDATION_GUIDE.md`)
- Guía de migración v1 a v2 (`MIGRATION_GUIDE.md`)

#### Testing
- Suite completa de tests para todos los algoritmos v2
- Tests de validación de parámetros
- Tests de migración v1 a v2
- Cobertura de código mejorada

### 🔄 Cambiado

#### Estructura del Proyecto
- Scripts consolidados en estructura organizada:
  - `scripts/core/`: Scripts principales (`run.py`, `analyze.py`)
  - `scripts/utilities/`: Utilidades y herramientas
  - `scripts/deprecated/`: Scripts legacy movidos aquí
- Imports mejorados y eliminación de dependencias circulares

#### Mejoras de Rendimiento
- Caching de fitness para evitar recálculos
- Gestión de memoria optimizada
- Paralelización mejorada con mejor distribución de carga

#### Interfaz de Usuario
- Salida más clara y estructurada
- Emojis informativos en la salida (🚀, ✅, ❌, 📊)
- Barras de progreso mejoradas
- Mensajes de error más descriptivos

### 🐛 Corregido

- Problema de convergencia prematura en varios algoritmos
- Gestión incorrecta de límites en el espacio de búsqueda
- Problemas de reproducibilidad con semillas aleatorias
- Memory leaks en ejecuciones largas
- Conflictos de nombres entre archivos (RRO_v2.py vs rro_v2.py)
- Problemas de importación circular

### 🗑️ Eliminado

- Código duplicado entre algoritmos
- Dependencias no utilizadas
- Scripts obsoletos (movidos a `deprecated/`)
- Archivos temporales y de respaldo

### 🔧 Técnico

- Python 3.8+ requerido
- Nuevas dependencias: `click>=8.0` para CLI
- Integración con `setuptools` para instalación pip
- Soporte para Docker (Dockerfile incluido)
- GitHub Actions para CI/CD

## [1.5.0] - 2023-12-XX

### Agregado
- Análisis estadístico avanzado
- Visualización mejorada de resultados
- Soporte para datasets Solomon

### Cambiado
- Mejorada la estructura de archivos VRP
- Optimización de operadores VRP

## [1.0.0] - 2023-XX-XX

### Inicial
- Primera versión con 18 algoritmos bio-inspirados
- Soporte básico para VRP
- Scripts individuales para ejecución

---

## Guía de Migración v1 → v2

### Para Usuarios

1. **Instalar la nueva versión**:
   ```bash
   pip install -e .
   ```

2. **Usar el nuevo CLI**:
   ```bash
   # Antes
   python run.py --algorithm woa --instance P-n16-k8.vrp
   
   # Ahora
   bioalgocompare run woa P-n16-k8.vrp
   ```

3. **Migrar resultados**:
   - Los archivos de resultados son compatibles
   - Use `bioalgocompare analyze` para analizar resultados antiguos

### Para Desarrolladores

1. **Migrar algoritmos personalizados**:
   ```bash
   bioalgocompare migrate algorithm mi_algoritmo
   ```

2. **Actualizar imports**:
   ```python
   # Antes
   from algorithms.base import Individual, Metaheuristic
   
   # Ahora
   from algorithms.base_v2 import Individual, MetaheuristicAlgorithm
   ```

3. **Usar validación de parámetros**:
   ```python
   from algorithms.validators import ParameterValidator
   
   self.param = ParameterValidator.validate_probability(param, "param")
   ```

## Planes Futuros

- [ ] Dashboard web interactivo
- [ ] Sistema de plugins para algoritmos externos
- [ ] Soporte para más tipos de problemas (TSP, Job Shop, etc.)
- [ ] Integración con herramientas de optimización bayesiana
- [ ] API REST para ejecución remota