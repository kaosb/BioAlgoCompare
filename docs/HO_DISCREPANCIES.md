# Discrepancias HO implementacion vs Amiri et al. (2024)

Fecha auditoria: 22 Marzo 2026
Paper original: Scientific Reports 14, Article 5032 (2024)

## Decision

La implementacion actual se mantiene para **consistencia con Paper 1 (IWINAC 2026)**,
que fue revisado y aprobado por el director de tesis (Dr. Rodrigo Olivares) y
sometido a CISTI el 3 de marzo de 2026. Las discrepancias se documentan aqui
para correccion en una version futura.

## Discrepancias identificadas

### D1 [CRITICA] — Asignacion de fases a individuos

**Paper:** Fase 1 macho aplica a `i = 1..N/2`, Fase 1 hembra a `i = N/2+1..N`.
Fase 2 (defensa) aplica solo a `i > N/2`. Fase 3 (evasion) aplica a todos.

**Implementacion:** Todas las fases (macho, hembra, defensa, evasion) se aplican
a TODOS los N individuos secuencialmente.

**Impacto:** Cada individuo recibe el doble de actualizaciones en Fase 1.
Cambia la dinamica de exploracion/explotacion.

**Ubicacion:** `algorithms/ho.py` linea 211 (loop `for i in range(self.population_size)`)

### D2 [CRITICA] — Fase 2: RL + predator vs RL * predator

**Paper (Eq. 15):** `x = RL * Predator + (f-d)*cos(2*pi*g) * (1/D)`
Usa multiplicacion element-wise entre Levy flight y posicion del depredador.

**Implementacion:** `x = RL + predator + ...` (suma en vez de multiplicacion).

**Ubicacion:** `algorithms/ho.py` lineas 300, 307

### D3 [CRITICA] — Fase 2: factor de distancia cuando predador es peor

**Paper (Eq. 15b):** `... * 1/(2*D + rand)` — reciproco de (2D + rand).

**Implementacion:** `... * 12 * D_vec + r9` — producto directo con constante 12.
Probable confusion tipografica: `1/2` leido como `12`.

**Ubicacion:** `algorithms/ho.py` linea 308

### D4 [MEDIA] — Vector h rango

**Paper:** `(~rho1) * (2*r2 - 1)` produce rango [-1, 1] cuando rho1=0.

**Implementacion:** `(1-rho1) * 2 * (r2 - 1)` produce rango [-2, 0] cuando rho1=0.

**Correccion:** Cambiar `2 * (r2 - 1)` por `(2 * r2 - 1)`.

**Ubicacion:** `algorithms/ho.py` linea 251

### D5 [BAJA] — MG_i no incluye individuo actual

**Paper:** "including current hippopotamus" en el grupo aleatorio.

**Implementacion:** `rng.choice` sin forzar inclusion del individuo i.

### D6 [BAJA] — abs() en D_vec

**Paper:** `D = Predator - x_i` (con signo).

**Implementacion:** `D_vec = np.abs(predator - x_i)` (valor absoluto).

## Plan de correccion futura

1. Crear branch `fix/ho-faithful` con las correcciones D1-D6
2. Re-ejecutar experimentos del Paper 1 para verificar impacto
3. Si los resultados cambian significativamente, reportar en Paper 2 extendido (Biomimetics)
4. Si los resultados son similares, documentar como "variante de implementacion"

## Nota sobre ambiguedad del paper original

El paper de Amiri et al. (2024) tiene ambiguedades en las ecuaciones que permiten
multiples interpretaciones. La implementacion actual es una interpretacion valida
que ha producido resultados competitivos en VRP (Paper 1). Las discrepancias
identificadas se basan en una lectura mas detallada del pseudocodigo y codigo
MATLAB original.
