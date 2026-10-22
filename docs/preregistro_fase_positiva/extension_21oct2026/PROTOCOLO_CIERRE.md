# Extensión de cierre experimental — 21 de octubre de 2026

Estado: diseño adicional prospectivo, motivado por resultados ya conocidos. No reemplaza el registro ni el análisis primario de v20. No constituye confirmación independiente de la hipótesis original. Se congela código y este protocolo antes de la campaña; pruebas funcionales y estimación temporal usan semillas 99000+, excluidas del análisis.

## Preguntas y matriz fija

1. Ejecutor: comparar C1_shared (mismo runner paramétrico y controles neutrales, sin propuestas) con C1_div, y CTRLg/C3p existentes con C1_shared.
2. Exposición: volver a ejecutar C3p con trazas, reproducir su secuencia en bucle abierto y compararla con una permutación condicionada de las etiquetas activas. Se preservan ventanas activas/neutrales, receptor y cantidades de FES por etiqueta al permutar solo entre intervalos con igual duración en FES del receptor. El orden de etiquetas puede cambiar; no se afirma igualdad de segmentación en episodios consecutivos. El control responde al valor de alinear etiquetas con los tiempos de una trayectoria observada, no a toda información de fuente ni a una política implementable sin esa trayectoria.
3. Referencia externa: L-SHADE (implementación minionpy, opciones documentadas del adaptador existente), con presupuesto completo y registro de FES efectivamente consumidas; no etiquetar como implementación oficial de los autores sin verificar procedencia.

Matriz principal: las 71 funciones corregidas CEC2014/2017/2022, 10D, pares GWO+GA/DE+GA/PSO+ACO, B=5000/50000, 51 semillas 13000–13050. L-SHADE se ejecuta una vez por función/presupuesto/semilla y se reutiliza como referencia entre pares, sin fingir replicaciones independientes.

No se eligen funciones, pares, semillas o umbrales tras mirar los nuevos resultados. Comparaciones primarias adicionales: C1_shared/C1_div; CTRLg/C1_shared; C3p/C1_shared; C3p_replay/C3p_permutado; C3p/L-SHADE y C1_shared/L-SHADE. Cada contraste/configuración lleva Holm sobre 71 funciones, alfa 0.05, Wilcoxon pareado bilateral exacto condicional con ceros excluidos y rangos empatados. Reportar conteos, rank-biserial y magnitud normalizada de medianas. Son análisis adicionales; no recalibrar G1 ni G1b. Si el control permutado no cambia la secuencia en una corrida, se conserva como empate y se reporta la proporción de perturbaciones efectivas, sin excluirla ni forzar diferencias.

## Controles de validez antes de interpretar

- Presupuesto consumido y asignación por solver registrados.
- C3p con instrumentación debe reproducir bit a bit el error archivado para la misma función/semilla y los controles originales en pruebas puente. Fallar implica detener la interpretación y diagnosticar; no mezclar series incompatibles.
- Replay de identidad debe reproducir bit a bit C3p y los mismos tiempos/FES por solver. De lo contrario, no analizar el control de etiquetas como equiparado.
- Permutación usa RNG separado, determinista por semilla; no consume RNG de optimizadores. Debe conservar máscara activa/neutra y FES por etiqueta y receptor exactamente.
- Guardado incremental, sin sobrescribir v20 ni las campañas históricas. Reanudación valida huellas y dimensiones, no solo existencia del archivo.
- Semillas de medición temporal/pruebas no forman parte del banco analizado.

## Otros límites y cierre documental

Una sensibilidad de parámetros o una política sin óptimo conocido exige un diseño adicional y no debe insertarse retrospectivamente como si fuese el tratamiento original. Primero se evaluará la contribución del ejecutor y la alineación de etiquetas. La memoria sin caducidad y la mediana monotónica de ciertos receptores son propiedades del método estudiado; cambiarlo produciría otro método. El cierre honesto consiste en medir su alcance y no afirmar garantías ausentes.


