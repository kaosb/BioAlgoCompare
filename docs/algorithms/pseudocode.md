# Pseudocódigo de Algoritmos Metaheurísticos implementados

Este documento recopila el pseudocódigo de los 11 algoritmos bioinspirados que hemos implementado, basado en los artículos científicos originales:

---

## 1. Harris Hawks Optimization (HHO)

**Paper:** Heidari et al. (2019), *Harris Hawks Optimization: Algorithm and Applications*

```
Inicializar población de H halcones con posiciones aleatorias
Evaluar fitness de cada halcón
Determinar mejor solución X*
Para t = 1 hasta T:
  Para cada halcón X_i:
    Calcular factor de energía E = 2 * (1 - t/T)
    Generar r ∈ U(0,1)
    Si |E| ≥ 1:
      # Fase exploración
      Seleccionar aleatoriamente X_r
      X_{i}^{t+1} = X_r - r * |X_r - 2 * r * X_i|
    Sino:
      # Fase explotación: cuatro estrategias según r2 y r3
      Si r2 < 0.5 y |E| < 0.5:
        X_{i}^{t+1} = X* - E * |J*X* - X_i|
      Si r2 ≥ 0.5 y |E| < 0.5:
        D = |X* - X_i|
        X_{i}^{t+1} = D * e^{b l} * cos(2π l) + X*
      Si r2 < 0.5 y |E| ≥ 0.5:
        X_{i}^{t+1} = X* - E * |J*X* - X_i|
      Si r2 ≥ 0.5 y |E| ≥ 0.5:
        D = |X* - X_i|
        X_{i}^{t+1} = D * e^{b l} * cos(2π l) + X*
  Actualizar X* si mejora
Retornar X*
```

---

## 2. Whale Optimization Algorithm (WOA)

**Paper:** Mirjalili & Lewis (2016), *The Whale Optimization Algorithm*

```
Inicializar población de ballenas con posiciones aleatorias
Evaluar fitness y seleccionar mejor X*
Para t = 1 hasta T:
  Calcular a = 2 * (1 - t/T)
  Para cada ballena X_i:
    Generar r1, r2 ∈ U(0,1), p ∈ U(0,1)
    Calcular A = 2·a·r1 - a, C = 2·r2
    Si p < 0.5:
      Si |A| < 1:
        # Encierre alrededor de la mejor
        D = |C * X* - X_i|
        X_{i}^{t+1} = X* - A * D
      Sino:
        # Exploración con individuo aleatorio
        Seleccionar X_rand
        D = |C * X_rand - X_i|
        X_{i}^{t+1} = X_rand - A * D
    Sino:
      # Movimiento en espiral
      D = |X* - X_i|
      X_{i}^{t+1} = D * e^{b·l}·cos(2π·l) + X*
  Actualizar X* si mejora
Retornar X*
```

---

## 3. Earthworm Optimization Algorithm (EWA)

**Paper:** Wang & Tan (2018), *Earthworm Optimization Algorithm: A Bio-inspired Metaheuristic*

```
Inicializar población de lombrices con posiciones aleatorias
Evaluar fitness y seleccionar best
Para t = 1 hasta T:
  Para cada lombriz u_i:
    # Reproducción 1 (autocopia modificada)
    u1 = UB + LB - α·u_i
    # Reproducción 2 (crossover uniforme)
    Generar u12 y u22 mezclando bits con otro padre
    Seleccionar u2 = u12 o u22 aleatoriamente
    # Suma ponderada
    β_t = β * γ^t
    u' = β_t·u1 + (1 - β_t)·u2
    # Mutación Cauchy
    W = promedio(u_i)
    Cd ∼ Cauchy()
    u_final = u' + W·ω·Cd
    Aplicar clip[u_final]
    Reemplazar si mejora
Retornar mejor lombriz
```

---

## 4. Slime Mould Algorithm (SMA)

**Paper:** Li et al. (2020), *Slime Mould Algorithm: A New Method for Stochastic Optimization*

```
Inicializar población de mohos con posiciones aleatorias
Para t = 1 hasta T:
  Calcular a = arctanh(-t/T + 1)
  p = tanh(|f_i - f_best|)
  vb ∈ U(-a,a), vc ∈ U(-1,1)*(1 - t/T)
  Para cada moho X_i:
    r ∈ U(0,1)
    Si r < z:
      X_{i} = aleatorio en dominio
    Sino:
      Para cada dimensión j:
        Si r < p:
          X_{i,j} = best_j + vb_j * W_i * (X_Aj - X_Bj)
        Sino:
          X_{i,j} = vc_j * X_{i,j}
    Aplicar clip[X_i]
    Evaluar y actualizar best si mejora
Retornar best
```

---

## 5. Manta Ray Foraging Optimization (MRFO)

**Paper:** Zhao et al. (2020), *Manta Ray Foraging Optimization*

```
Inicializar población de rayas con posiciones aleatorias
Para t = 1 hasta T:
  Para cada raya X_i:
    r1,r2,r3 ∈ U(0,1)
    β = 2·e^{1 - t/T}·sin(2π·r1)
    Si t/T < 0.5:
      # Chain foraging
      X_{i}^{t+1} = X_i + β·(X_best - X_i) + β·r2
    Sino:
      # Cyclone foraging
      if uniform() < 0.5:
        X_{i}^{t+1} = X_best + e^{-βt}·cos(2π·r2)·(X_best - X_i)
      else:
        X_{i}^{t+1} = X_i + e^{-βt}·(X_best - X_i)
    # Somersault foraging opcional
    if rand < P_s:
      X_{i} += S_range * (X_best - X_i)
    Aplicar clip
  Actualizar X_best
Retornar X_best
```

---

## 6. Gorilla Troops Optimizer (GTO)

**Paper:** Abdollahzadeh et al. (2021), *Artificial Gorilla Troops Optimizer*

```
Inicializar población de gorilas con posiciones aleatorias
Para t = 1 hasta T:
  Calcular F = cos(2π·r)+1, C = F*(1 - t/T), l ∈ U(-1,1), L = C*l
  Para cada gorila X_i:
    Generar r ∈ U(0,1)
    Si r < p:
      # Exploración
      r1 = U(0,1)
      X = lower + (upper-lower)*r1
      D = C*(Vecino - X_i)
      X_i = X_i + D*L
    Sino:
      # Explotación
      Si C < W:
        if rand<0.5:
          M = promedio(población)
          X_i = L*(M - X_i) + X_best
        else:
          Q = 2·rand -1
          E = (rand>=0.5? U: N)
          A = π·E
          X_i = X_best - Q*(X_best - X_i)*A
    Aplicar clip
  Actualizar X_best
Retornar X_best
```

---

## 7. Enhanced GTO + MPA (EGTO)

**Paper:** Hassan et al. (2024), *Enhanced Gorilla Troops Optimizer powered by Marine Predator Algorithm*

```
Inicializar población de EnhancedGorilla
Para t = 1 hasta T:
  Para cada individuo X_i:
    Si t < T/3:
      # Alta velocidad (Browniano)
      RB ∼ N(0,1)
      S = rand()*X_i
      X_i += P * RB * S
    Elif t < 2T/3:
      # Media velocidad
      R = U(0,1)
      S = R*(X_best - R*X_i)
      X_i += P*CF*S
    Else:
      # Baja velocidad (Lévy)
      if rand < FADs:
        LF ∼ Lévy()
        X_i += LF*X_i
      else:
        X_i += P*(X_best - X_i)
    Aplicar clip con LB,UB
    Actualizar fitness
Retornar X_best
```

---

## 8. Fossa Optimization Algorithm (FOA)

**Paper:** Hamadneh et al. (2024), *Fossa Optimization Algorithm*

```
Inicializar población de Fossa
Para t = 1 hasta T:
  Para cada fosa X_i con índice i:
    Obtener lista de lemures (mejores vecinos)
    Si no hay lemures: continuar
    Si t ≤ T/2:
      # Exploración (Eq.5)
      I ∼ {1,2}, r ∈ U(0,1)
      X_new = X_i + r*(Lemur - I*X_i)
    Sino:
      # Explotación (Eq.7)
      r ∈ U(0,1)
      X_new = X_i + (1 - 2r)*(ub-lb)/t
    Evaluar X_new
    Si mejora: X_i = X_new
    Aplicar clip
  Actualizar mejor
Retornar mejor
```

---

## 9. Flamingo Search Algorithm (FSA / FGO)

**Paper:** Wang & Liu (2021), *Flamingo Search Algorithm: A New Swarm Intelligence Optimization Algorithm*

```
Inicializar población de flamencos
Para t = 1 hasta T:
  Dividir población en MPo, MPr, MPt
  # Migración inicial (MPo)
  Para i en MPo:
    X_i = X_i + N(0,σn)*(X_best - X_i)
  # Forrajeo (MPr)
  Para i en MPr:
    G1,G2 ∼ N(0,1), λ1,λ2 ∈ {-1,1}, K ∼ χ^2(n)
    step = G1*X_best + λ2*X_i
    scan = G2*|step|, foot = λ1*X_best
    X_new = X_i + scan + foot + K
    X_i = clip(X_new)
  # Migración final (MPt)
  Para i en MPt:
    σ ∼ N(0,σn)
    X_i += σ*(X_best - X_i)
  Actualizar X_best
Retornar X_best
```

---

## 10. Spotted Hyena Optimizer (SHO / HOA)

**Paper:** Mirjalili et al. (2017), *Spotted Hyena Optimizer*

```
Inicializar población de hienas
Para t = 1 hasta T:
  a = 2 - t*(2/T)
  Para cada hiena X_i:
    r1,r2 ∈ U(0,1)
    A = 2a·r1 - a, C = 2·r2
    Si |A| < 1:
      X_new = X_best - A*|C*X_best - X_i|
    Sino:
      RandIndex aleatorio entre {α,β,δ}
      Xs = posiciones de los 3 líderes
      X_new = promedio(Xs) - A*|C*promedio(Xs) - X_i|
    X_i = clip(X_new)
  Actualizar X_best y líderes
Retornar X_best
```

---

## 11. Artificial Protozoa Optimizer (APO)

**Paper:** Wang et al. (2024), *Artificial Protozoa Optimizer*

```
Inicializar población de protozoos
Para t = 1 hasta T:
  ps = tamaño de población, i = indice de Protozoa
  pf, pah, pdr = función de t, ps, i (Eqs.15-17)
  Para cada Protozoa X_i:
    Si rand < pf:
      Si rand < pdr:
        # Dormancia (Eq.11)
        X_i = lb + rand*(ub-lb)
      Sino:
        # Reproducción (Eq.13)
        Mr = vector máscara aleatorio
        delta = rand*(lb + rand*(ub-lb))
        X_i += ε·delta·ω·Mr
    Sino:
      Mf = máscara proporcional a i/ps
      Si rand < pah:
        # Autotrofia (Eq.1)
        wa = exp(-|f(i-1)|/|f(i+1)|)
        delta = (X_j - X_i + wa*(X_{i-1}-X_{i+1}))/npairs
        f = rand*(1+cos(π·t/T))
        X_i += f * delta·ω·Mf
      Sino:
        # Heterotrofia (Eq.7)
        wh = ... similar, con Xnear = ...
    Aplicar clip
  Actualizar mejor
Retornar mejor
```

---

*Referencias bibliográficas completas en la carpeta **`docs/references.bib`**.*