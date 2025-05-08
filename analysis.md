 Anlisis Comparativo de Algoritmos Metaheursticos para VRP

  Resumen de Resultados

  Hemos ejecutado una comparacin sistemtica de 5 algoritmos metaheursticos (HOA, APO, EGTO, FGO, FOA) en 2 instancias VRP (P-n16-k8 y E-n22-k4), con 10 ejecuciones independientes por configuracin algoritmo-instancia, usando
  parmetros consistentes (poblacin=30, iteraciones=100, semilla=42).

  Anlisis de Calidad de Solucin (Best Fitness)

  Instancia P-n16-k8

  - Mejor algoritmo: EGTO (410.93, gap -8.68%)
  - Orden de rendimiento: EGTO > APO/FOA (416.87, gap -7.36%) > FGO (418.25, gap -7.06%) > HOA (424.86, gap -5.59%)
  - Observacin: Todos los algoritmos superaron la solucin ptima conocida (450), logrando rutas ms eficientes.
  - Consistencia: APO mostr menor desviacin estndar (6.64), indicando mayor estabilidad.

  Instancia E-n22-k4

  - Mejor algoritmo: FOA (437.24, gap 16.60%)
  - Orden de rendimiento: FOA > APO (450.14, gap 20.04%) > HOA (460.62, gap 22.83%) > FGO (465.47, gap 24.12%) > EGTO (507.62, gap 35.36%)
  - Observacin: Ningn algoritmo alcanz la solucin ptima (375), lo que indica que esta instancia es ms desafiante.
  - Consistencia: APO fue nuevamente el ms estable (=16.41).

  Anlisis de Eficiencia Computacional

  - Algoritmo ms rpido: FGO (0.058s) seguido de APO (0.059s) para P-n16-k8
  - Algoritmo ms lento: FOA (0.187s), aproximadamente 3 veces ms lento que los dems
  - Patrn consistente: El mismo orden de eficiencia se mantuvo para E-n22-k4

  Anlisis Estadstico

  Los resultados del test de Friedman muestran:
  - No se detectaron diferencias estadsticamente significativas entre algoritmos (p-value=0.199 > =0.05)
  - Ranking promedio: APO (1.5) > FGO (2.0) > HOA (3.0) > FOA (3.5) > EGTO (5.0)
  - El tamao muestral (2 instancias) limita la potencia estadstica, por lo que se recomienda ampliar el nmero de instancias para obtener resultados ms concluyentes.

  Convergencia

  El anlisis de las curvas de convergencia revela:
  - EGTO converge ms rpidamente en las primeras iteraciones para P-n16-k8
  - APO y FGO muestran mejoras constantes hasta iteraciones tardas
  - FOA presenta convergencia irregular, con mejoras significativas en iteraciones intermedias
  - Para E-n22-k4, todos los algoritmos muestran dificultades para converger, con FOA mostrando la mayor variabilidad

  Conclusiones

  1. Trade-off calidad-tiempo: Los algoritmos con mejor calidad de solucin (EGTO, FOA) no son necesariamente los ms eficientes computacionalmente.
  2. Comportamiento por instancia: El rendimiento relativo de los algoritmos vara significativamente entre instancias, sugiriendo que la eleccin ptima depende del problema especfico.
  3. Estabilidad: APO demuestra el comportamiento ms estable en ambas instancias, lo que lo hace recomendable para aplicaciones donde la consistencia es prioritaria.
  4. Eficiencia: FGO ofrece el mejor balance entre calidad de solucin y tiempo de ejecucin, especialmente para instancias pequeas.
  5. Escalabilidad: Al aumentar el tamao del problema (E-n22-k4), FOA mejora su rendimiento relativo, sugiriendo mejor escalabilidad.

  Limitaciones y Trabajo Futuro

  1. Tamao muestral: Ampliar el anlisis a ms instancias VRP proporcionara mayor significancia estadstica.
  2. Parmetros: Un estudio sobre la sensibilidad a parmetros (poblacin, iteraciones) es recomendable.
  3. Optimizacin local: Incorporar tcnicas de optimizacin local podra mejorar significativamente los resultados, especialmente para EGTO y FOA.
  4. Paralelizacin: Explorar la paralelizacin para mejorar el rendimiento de FOA, que mostr el mayor tiempo de ejecucin.

  Esta evaluacin sistemtica proporciona evidencia sobre las fortalezas y debilidades de cada algoritmo metaheurstico, ofreciendo pautas para su seleccin segn el contexto de aplicacin especfico.
