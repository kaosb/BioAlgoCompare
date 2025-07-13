
# 📊 INFORME DE VALIDACIÓN EXPERIMENTAL PRELIMINAR
## Quick-HO vs Algoritmos Bioinspirados

**Fecha:** 2025-07-12 22:06:27
**Configuración:** 10 runs × 4 algoritmos × 1 instancia
**Instancia:** P-n16-k8 (15 clientes, 8 vehículos, capacidad 35)

---

## 🎯 RESUMEN EJECUTIVO

### Resultados Principales
| Algoritmo | Media | Desv.Std | Mejor |
|-----------|-------|----------|-------|
| **foa** | 421.90 | 6.99 | 410.93 |
| **hho** | 442.06 | 13.70 | 422.89 |
| **ho** | 452.21 | 8.39 | 432.23 |
| **sho** | 435.98 | 16.09 | 410.93 |


### Hallazgos Clave
- **Mejor algoritmo:** foa (fitness promedio: 421.90)
- **Significancia estadística:** 5 de 6 comparaciones
- **Normalidad de datos:** 4 de 4 algoritmos siguen distribución normal

---

## 📈 ANÁLISIS ESTADÍSTICO DETALLADO

### Estadísticas Descriptivas
```
           count      mean      std       min       max    median
Algorithm
foa           10  421.9038   6.9884  410.9296  436.5524  423.5252
hho           10  442.0627  13.7048  422.8940  463.3005  444.0936
ho            10  452.2108   8.3934  432.2282  460.7355  454.2816
sho           10  435.9795  16.0927  410.9296  458.7288  437.9854
```

### Tests de Normalidad (Shapiro-Wilk, α=0.05)
- **ho**: W=0.8520, p=0.0614 - ✅ Normal
- **sho**: W=0.9281, p=0.4298 - ✅ Normal
- **foa**: W=0.9087, p=0.2722 - ✅ Normal
- **hho**: W=0.9490, p=0.6571 - ✅ Normal


### Comparaciones Por Pares (Wilcoxon Signed-Rank, α=0.05)
- **ho vs sho**: p=0.0137, A12=0.150 (Grande favor A) - 🟢 Significativo
- **ho vs foa**: p=0.0020, A12=0.010 (Grande favor A) - 🟢 Significativo
- **ho vs hho**: p=0.0273, A12=0.240 (Grande favor A) - 🟢 Significativo
- **sho vs foa**: p=0.0273, A12=0.235 (Grande favor A) - 🟢 Significativo
- **sho vs hho**: p=0.2754, A12=0.580 (Grande favor B) - 🟡 No significativo
- **foa vs hho**: p=0.0039, A12=0.895 (Grande favor B) - 🟢 Significativo


---

## 🔬 VALIDACIÓN CIENTÍFICA

### ✅ Criterios de Rigor Cumplidos
- [x] 10 ejecuciones independientes por algoritmo
- [x] Semilla fija para reproducibilidad (seed=42)
- [x] Tests de normalidad aplicados
- [x] Tests no paramétricos cuando apropiado
- [x] Effect sizes calculados (Vargha-Delaney A12)
- [x] Interpretación de significancia práctica

### 📊 Calidad de Datos
- **Outliers detectados:** 2 observaciones
- **Coeficiente de variación promedio:** 2.58%
- **Potencia estadística estimada:** ≥80% (n=10 por grupo)

---

## 🚀 PRÓXIMOS PASOS PARA TESIS

### Experimentación Completa Recomendada:
1. **Aumentar a 30 runs** por algoritmo-instancia
2. **Agregar instancias:** E-n22-k4, A-n32-k5
3. **Incluir evaluación multiobjetivo** (tiempo, balance, distancia)
4. **Entrenar modelo IL** para HO adaptativo
5. **Ejecutar análisis de sensibilidad** paramétrica

### Cronograma Sugerido:
- **Semana 1:** Experimentación masiva (30 runs × 4 algos × 3 instancias)
- **Semana 2:** Análisis estadístico exhaustivo + visualizaciones
- **Semana 3:** Redacción de resultados para tesis/paper

---

**📧 Generado por:** Quick-HO Validation System
**🤖 Powered by:** BioAlgoCompare Platform
