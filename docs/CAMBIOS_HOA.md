# Análisis del Algoritmo HOA

Este documento detalla las características y rendimiento del algoritmo HOA (Hyena Optimization Algorithm) en la resolución de problemas VRP.

## Evaluación del Algoritmo HOA

**Fecha:** 8 de mayo de 2025

### Características del Algoritmo

El algoritmo HOA se inspira en el comportamiento social de las hienas durante la caza, con las siguientes características principales:

1. **Jerarquía social**:
   - Implementa una estructura jerárquica con tres líderes: alpha, beta y delta
   - El resto de la población sigue a estos líderes durante la búsqueda
   - Esta jerarquía permite una transferencia eficiente de información entre individuos

2. **Mecanismo de caza**:
   - Divide la búsqueda en dos fases: exploración y explotación, controladas por el parámetro A
   - Cuando |A| ≥ 1, realiza exploración siguiendo a un líder elegido aleatoriamente
   - Cuando |A| < 1, realiza explotación considerando las posiciones de todos los líderes

3. **Estrategia de ataque en círculo**:
   - Durante la fase de explotación, combina la información de los tres líderes
   - Calcula la posición promedio basada en los movimientos hacia alpha, beta y delta
   - Este enfoque permite una convergencia más precisa hacia áreas prometedoras

4. **Parámetros adaptativos**:
   - El parámetro a decrece linealmente de 2 a 0 a lo largo de las iteraciones
   - Los coeficientes A y C introducen aleatoriedad y énfasis en diferentes aspectos de la búsqueda
   - Este diseño permite un balance dinámico entre exploración y explotación

### Resultados de las Pruebas

Las pruebas realizadas con el algoritmo HOA en la instancia E-n22-k4 muestran:

1. **Rendimiento**:
   - Mejor fitness encontrado: 485.19
   - Comparado con el valor óptimo conocido (375.28), representa un desvío del 29.28%

2. **Eficiencia**:
   - Tiempo de ejecución: 0.12s
   - Eficiencia baja comparada con algoritmos como EGTO (0.04s) o APO (0.08s)

3. **Convergencia**:
   - El algoritmo converge a soluciones subóptimas
   - La estrategia de ataque en círculo no parece adaptarse bien a las características del problema VRP

### Análisis Comparativo

Comparado con otros algoritmos:

1. HOA muestra un rendimiento inferior a algoritmos como GTO, HHO, WOA, EGTO y APO en términos de calidad de solución
2. El tiempo de ejecución (0.12s) es relativamente alto, siendo uno de los más lentos entre los algoritmos probados
3. La estrategia jerárquica y de ataque en círculo, aunque teóricamente efectiva, no logra buenos resultados en problemas VRP

## Conclusión

El algoritmo HOA presenta un enfoque interesante basado en el comportamiento de caza de las hienas, pero su desempeño en problemas VRP es deficiente:

1. Sus mecanismos de jerarquía social y ataque en círculo no parecen adaptarse bien a las características específicas de los problemas VRP
2. El rendimiento en términos de calidad de solución es significativamente inferior a la mayoría de los otros algoritmos probados
3. El tiempo de ejecución es relativamente alto, lo que reduce su atractivo para aplicaciones prácticas

Para mejorar el rendimiento de HOA en problemas VRP, se podría considerar:

1. Modificar la estrategia de ataque en círculo para incorporar conocimiento específico del dominio VRP
2. Reducir la complejidad computacional de los cálculos de actualización de posición
3. Ajustar los parámetros de control para favorecer una explotación más agresiva en etapas finales

HOA podría ser más adecuado para problemas con estructuras diferentes a las del VRP, donde su enfoque jerárquico y de ataque coordinado pueda ser más efectivo. En su estado actual, no es recomendable para problemas VRP cuando existen alternativas más eficientes como GTO, HHO o EGTO.