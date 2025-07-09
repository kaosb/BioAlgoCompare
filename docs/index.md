# Documentación de BioAlgoCompare

Bienvenido a la documentación oficial de BioAlgoCompare, una plataforma para evaluación estadística rigurosa de algoritmos bio-inspirados en problemas de optimización.

## Estructura de la Documentación

### Documentación Principal

- [README del proyecto](../README.md) - Visión general del proyecto
- [Análisis de Iteraciones](analysis/iteration_impact.md) - Impacto del número de iteraciones
- [Conclusiones de Optimización](analysis/conclusions.md) - Conclusiones generales

### Guías de Usuario

- [Referencia de Comandos](COMMAND_REFERENCE.md) - Guía completa de comandos y uso
- [Instalación](guides/installation.md) - Instrucciones detalladas de instalación
- [Benchmarking](guides/benchmarking.md) - Instrucciones para ejecutar y analizar benchmarks

### Documentación Científica

- [Reproducibilidad y Rigor Científico](scientific/reproducibility.md) - Garantías de reproducibilidad y rigor en experimentos
- [Análisis Estadístico](scientific/statistical_analysis.md) - Metodología estadística detallada
  - Test de Friedman alineado
  - Test post-hoc de Nemenyi
  - Tamaños de efecto A12 de Vargha-Delaney
  - Diagramas de Diferencia Crítica (CD)

### Algoritmos Implementados

- [Visión General](algorithms/overview.md) - Descripción general de todos los algoritmos
- [Pseudocódigo](algorithms/pseudocode.md) - Pseudocódigo de los algoritmos implementados
- Documentación Individual de Algoritmos:
  - [Artificial Hummingbird Algorithm (AHA)](algorithms/individual/aha.md)
  - [Artificial Protozoa Optimizer (APO)](algorithms/individual/apo.md)
  - [Earthworm Algorithm (EWA)](algorithms/individual/ewa.md)
  - [Enhanced Gorilla Troops Optimization (EGTO)](algorithms/individual/egto.md)
  - [Flamingo Search Algorithm (FSA/FGO)](algorithms/individual/fsa.md)
  - [Fossa Optimization Algorithm (FOA)](algorithms/individual/foa.md)
  - [Gorilla Troops Optimization (GTO)](algorithms/individual/gto.md)
  - [Griffon Vultures Optimization Algorithm (GVOA)](algorithms/individual/gvoa.md)
  - [Harris Hawks Optimization (HHO)](algorithms/individual/hho.md)
  - [Manta Ray Foraging Optimization (MRFO)](algorithms/individual/mrfo.md)
  - [Raven Roosting Optimization (RRO)](algorithms/individual/rro.md)
  - [Slime Mould Algorithm (SMA)](algorithms/individual/sma.md)
  - [Spotted Hyena Optimizer (SHO)](algorithms/individual/sho.md)
  - [Starling Murmuration Optimizer (SMO)](algorithms/individual/smo.md)
  - [Whale Optimization Algorithm (WOA)](algorithms/individual/woa.md)

### Informes de Análisis

- [Impacto de Iteraciones](analysis/iteration_impact.md) - Análisis del impacto del número de iteraciones
- [Análisis Comparativo](analysis/comparison.md) - Comparación exhaustiva entre algoritmos
  - Incluye comparativas de algoritmos por familia biológica
  - Análisis detallado de versiones modificadas (SMO, GVOA)
  - Recomendaciones por contexto de uso
- [Conclusiones de Optimización](analysis/conclusions.md) - Conclusiones generales y recomendaciones prácticas

### Guías para Desarrolladores

- [Flujo de Trabajo Git](development/git_workflow.md) - Guía del flujo de trabajo con Git
- [Contribución](development/contribution.md) - Cómo contribuir al proyecto
- [Requisitos Algorítmicos](development/algorithmic_requirements.md) - Requisitos para implementación de algoritmos

### Documentación Técnica

- [Arquitectura del Sistema](technical/architecture.md) - Descripción de la arquitectura y componentes
- [Detalles de Implementación](technical/implementation.md) - Detalles técnicos de implementación
- [Referencia de Scripts](technical/scripts_reference.md) - Documentación completa de los scripts ejecutables
- [Estado de Consolidación](technical/consolidation_status.md) - Estado actual de la consolidación de scripts

## Resultados de Experimentos

Los resultados de todas las ejecuciones experimentales se encuentran en el directorio `/results/` organizados por fecha y configuración.

## Acerca del Proyecto

BioAlgoCompare es una plataforma para evaluación estadística rigurosa de algoritmos bio-inspirados. Implementa benchmarking masivo (1000+ ejecuciones), análisis estadístico avanzado y visualizaciones científicas para comparar metaheurísticas en problemas de optimización. Incluye checkpointing, intervalos de confianza y tests no paramétricos para conclusiones estadísticamente significativas.

El proyecto forma parte de una investigación académica para la Jornada Chilena de Computación 2025, cuyo objetivo es evaluar y comparar algoritmos bioinspirados recientes aplicados al Vehicle Routing Problem (VRP).

## Referencias

- [Repositorio en GitHub](https://github.com/kaosb/BioAlgoCompare)

---

*Última actualización: 10 de mayo de 2025*