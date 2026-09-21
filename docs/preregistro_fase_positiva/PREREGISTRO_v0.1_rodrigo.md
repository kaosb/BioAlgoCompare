Pre-registro: cooperación entre metaheurísticas heterogéneas, fase
positiva

Versión 0.1 · 21 de septiembre de 2026 · Estudio que sigue al borrador
BORRADOR_transferencia_v11

1\. Propósito y regla de uso

Este documento fija, antes de correr nada, los mecanismos, baselines y
criterios de éxito y abandono del estudio que sigue al borrador v11. Se
versiona en el repositorio del framework y se congela con un hash antes
de la primera corrida de la Fase 2.

Regla de uso: nada se edita in situ después del congelamiento. Todo
cambio se anota como enmienda fechada en el registro de desviaciones del
repositorio y se declara en el paper. Un recorte declarado es una
restricción de recursos; el mismo recorte sin declarar es un defecto de
integridad.

Alcance: optimización continua acotada en \[−100, 100\]\^D, bancos CEC
2014, 2017 y 2022, cooperación entre metaheurísticas heterogéneas a
presupuesto total equitativo.

Flujo de fases y puntos de corte:

- Fase 0, reencuadre y congelamiento → Fase 1, cotas sobre datos
  existentes.

- Corte 1: si ninguna cota supera el umbral → paper alterno (gate como
  seguridad + protocolo); si alguna lo supera → Fase 2, piloto de
  candidatos A, B y C.

- Corte 2: si ningún candidato cumple el criterio de éxito → paper
  alterno; si alguno lo cumple → Fase 3, confirmatorio bajo protocolo
  CEC → Fase 4, redacción elsarticle.

Dos puntos de corte baratos preceden al cómputo confirmatorio, y el
camino alterno queda pre-registrado y también es publicable.

2\. Pregunta e hipótesis

Pregunta: ¿existe un mecanismo de cooperación entre solvers
complementarios que supere al portafolio de reparto igual (C1_div) a
igual presupuesto, de forma consistente por presupuesto y dimensión?

Hipótesis falsables, cada una con su contraste primario:

- H1 (asignación). Un controlador reactivo de presupuesto guiado por
  mejora relativa supera a C1_div en más funciones de las que pierde, a
  5·10³ y 5·10⁴ en 10D.

- H2 (estructural). La migración de élite admitida por estado y
  revertida por stop-loss supera a la migración fija (C1_island) y a
  C1_div.

- H3 (régimen por efecto). La selección de régimen por efecto observado
  supera a la selección por intención fija (C3p) y no es inferior a
  C1_div.

- H4 (escala). La ventaja de H1 o H2 se mantiene a 5·10⁵ con Δ fijo y en
  50D.

- H5 (referencia externa). La cooperación no es inferior a L-SHADE
  aislado a igual presupuesto. Si se rechaza, el claim se acota al
  portafolio de los mismos solvers.

Resultado alterno pre-registrado: si las cotas de la Fase 1 no superan
el umbral, la contribución positiva es el gate como componente de
seguridad más el protocolo de atribución, con los datos ya existentes.

3\. Fase 0: reencuadre

La pregunta pasa de "cuándo no transferir" a "qué transferir y cómo
repartir". El resultado negativo del borrador v11 se conserva como
sección de diagnóstico que motiva el diseño; no se descarta.

Se conserva: el orquestador con contador de FES compartido y aserciones
de presupuesto, la escalera de atribución, las semillas CRN, las curvas
C0 y las reglas de admisión y stop-loss.

Se cambia antes de correr:

- Δ desacoplado del presupuesto: Δ fijo en evaluaciones, igual en todos
  los niveles.

- Memoria de efectos activa (métrica de mediana) en los tres pares; la
  campaña con memoria inerte pasa al suplementario como verificación
  bit-idéntica.

- 51 corridas en toda celda que llegue a una tabla, incluidos los
  estudios discriminantes.

- Vocabulario de regímenes acotado a las regiones de convergencia de
  cada solver (F ≤ 1, w \< 1, ξ \< 1, a ≤ 2).

- Tabla de parámetros base θ_k por solver, con tamaño de población y
  procedencia bibliográfica.

Entregables:

- [ ] Este pre-registro congelado con hash y tag en el repositorio

- [ ] deviations-log.md creado a partir de la plantilla del protocolo

- [ ] Tabla θ_k por solver con fuente y tamaño de población

4\. Fase 1: cotas sobre datos existentes

Las corridas C0 ya disponibles bastan para acotar la ganancia máxima de
cada mecanismo antes de gastar cómputo. Ningún análisis de esta fase
requiere corridas nuevas.

  ------------------------------------------------------------------------
  **Análisis**           **Datos         **Qué acota**   **Umbral
                         usados**                        propuesto**
  ---------------------- --------------- --------------- -----------------
  Virtual-best por       Curvas C0, 70   Ganancia máxima Mejor en ≥ 20/70
  función (todo el       funciones,      de asignación   con Holm y
  presupuesto al mejor   5·10³ a 5·10⁵   estática        mediana r ≥ 0.3
  solver de esa función)                                 
  vs C1_div                                              

  Oráculo de conmutación Curvas C0 por   Ganancia máxima Igual que la fila
  por Δ (en cada punto   iteración       de un           anterior
  de control, el solver                  controlador     
  que más mejora) vs                     reactivo        
  C1_div                                                 

  Cribado de             Resultados C0,  Fracción del    Cambio de ganador
  complementariedad 70   más SSA y WOA   banco con algo  en ≥ 40 % de las
  funciones × 7 solvers                  que explotar    funciones

  Estabilidad del efecto Logs de memoria Viabilidad del  Signo del efecto
  por régimen            de E2 y E4      candidato C     por triple
                                                         estable en ≥ 70 %
                                                         de las semillas
  ------------------------------------------------------------------------

Los umbrales son propuestas y se fijan en la enmienda v0.2 antes de
ejecutar el análisis. Los scripts leen los CSV crudos y quedan
versionados junto con este documento.

Regla de decisión: si ninguna cota de las dos primeras filas supera su
umbral, se abandona la Fase 2 y se sigue el camino alterno de la sección
2.

- [ ] Script de cotas sobre los crudos C0

- [ ] Tabla de cotas por par y presupuesto

- [ ] Decisión de continuar registrada en el log de desviaciones

5\. Fase 2: candidatos y piloto

Tres mecanismos entran al piloto, ordenados por probabilidad de éxito
según la evidencia del borrador v11. Solo los que cumplan el criterio de
éxito pasan al confirmatorio.

  ------------------------------------------------------------------------------------
  **Candidato**   **Mecanismo**     **Señal         **Por qué puede  **Por qué puede
                                    reutilizada**   ganar**          fallar**
  --------------- ----------------- --------------- ---------------- -----------------
  A. Asignación   Bandit que mueve  Reglas de       El efecto        La cota del
  dinámica de     la fracción de    admisión        portafolio es    virtual-best
  presupuesto     presupuesto hacia (fuente en      real y crece con puede ser pequeña
                  el solver en      mejora, destino el presupuesto;  
                  mejora; el        estancado)      no transfiere    
                  stop-loss                         nada, así que no 
                  revierte al                       sufre daño de    
                  reparto igual si                  vocabulario      
                  no hay progreso                                    

  B.              Reinyección de la Reglas de       Está descrita en Homogeneización
  Transferencia   mejor solución de admisión,       el método y      de la población
  estructural con la fuente en el   stop-loss,      nunca se evaluó  destino
  admisión        destino solo bajo memoria por     a escala;        
                  admisión;         efecto          comparable con   
                  rollback si el                    la literatura de 
                  mejor histórico                   islas            
                  no mejora en Δ                                     

  C. Régimen por  UCB por (destino, Memoria de      E3 mostró que    E1 y el hallazgo
  efecto          estado) sobre     efectos         etiquetar a mano previo apuntan a
  observado       vocabulario       convertida en   falla y E2 que   óptimo de nivel,
                  acotado; el       crédito         la memoria por   no de schedule
                  crédito viene del positivo        efecto funciona  
                  efecto medido, no                                  
                  de la etiqueta                                     
  ------------------------------------------------------------------------------------

Diseño del piloto:

- 12 funciones CEC 2014 en 10D, fijadas por taxonomía y disjuntas de las
  6 del cribado anterior. Propuesta: F2, F3 (unimodales); F5, F8, F11,
  F14 (multimodales); F17, F18, F20 (híbridas); F24, F26, F29
  (composición).

- 51 corridas pareadas por CRN, presupuestos 5·10³ y 5·10⁴, tres pares
  (GWO+GA, DE+GA, PSO+ACO), Δ = 500 evaluaciones.

- Parámetros de cada candidato fijados antes de correr y sin ajuste
  posterior.

- Control positivo de transferencia benigna: inyectar el mejor régimen
  estático por función de E1, para medir la tasa de falsos positivos del
  gate.

Criterio de éxito por candidato, frente a C1_div con Wilcoxon de rangos
con signo y Holm sobre las 12 funciones:

- Más funciones mejor que peor en ambos presupuestos.

- Mediana del rank-biserial ≥ 0.3.

- Peor en ≤ 2 de 12 funciones.

- Se cumple en al menos 2 de los 3 pares.

Criterio de abandono: incumplir el criterio en ambos presupuestos y en
los tres pares. El candidato abandonado se reporta en el suplementario
con sus tablas completas.

- [ ] Fijar lista de funciones y parámetros de A, B, C (enmienda v0.2)

- [ ] Implementar los tres candidatos sobre el orquestador

- [ ] Correr el piloto y emitir tablas desde crudos

6\. Fase 3: confirmatorio

El confirmatorio corre una única configuración del mecanismo ganador
sobre la matriz completa del protocolo CEC. Nada se ajusta por función,
presupuesto ni dimensión.

  -------------------------------------------------------------------------------------
  **Conjunto**   **Funciones**          **Dimensión**   **Presupuestos   **Corridas**
                                                        (MaxFES)**       
  -------------- ---------------------- --------------- ---------------- --------------
  CEC_72_10      CEC 2014 (30), CEC     10D             5·10³, 5·10⁴,    51
                 2017 (30, o 29 sin                     5·10⁵, 5·10⁶     
                 F2), CEC 2022 (12)                                      

  CEC_72_50      Las mismas             50D en 2014 y   5·10³, 5·10⁴,    51
                                        2017; 20D en    5·10⁵, 5·10⁶     
                                        2022                             
  -------------------------------------------------------------------------------------

Reglas de ejecución:

- Cada presupuesto parte de cero con su propia semilla; ninguna corrida
  es continuación de otra.

- El contador de FES incluye la población inicial y cualquier evaluación
  que consuma el mecanismo.

- 5·10⁶ puede restringirse a las 12 funciones del piloto si el costo lo
  exige; la restricción se declara aquí antes de lanzar.

- F22 de CEC 2014 y F12 de CEC 2022 vuelven al banco o se excluyen con
  razón verificable, igual para todos los tratamientos.

- Manejo de límites del dominio documentado y común a todos los solvers.

Costo: estimar con el planificador del protocolo antes de lanzar;
registrar horas de pared, núcleos y almacenamiento en el suplementario.

- [ ] Decisión sobre F2, F22 y F12 registrada

- [ ] Estimación de costo y recorte declarado, si aplica

- [ ] Corridas con guardado incremental reanudable

7\. Baselines y competidores

La lista se cierra con el hash del pre-registro y no cambia después de
ver resultados. Los parámetros de cada competidor vienen de su
publicación original, sin retuning.

  ------------------------------------------------------------------------
  **Tratamiento**             **Rol en la             **Fuente de
                              comparación**           parámetros**
  --------------------------- ----------------------- --------------------
  SBS (mejor solver aislado   Piso clásico de         Tabla θ_k
  del par)                    portafolios             

  Virtual-best por función    Cota superior de        Derivado de C0
                              selección a posteriori  

  C1_div (reparto igual, sin  Contraste primario      Tabla θ_k
  comunicación)                                       

  C1_island (migración fija   Baseline de modelos de  Convención de islas,
  de una élite cada Δ)        islas                   citada

  Portafolio cooperativo con  Cooperativo publicado   Paper original o
  diversidad (Żychowski et                            código de los
  al. 2025)                                           autores

  C2p y C3p (intención fija,  Referencia de lo que no Tabla 1 del borrador
  borrador v11)               funciona                

  L-SHADE aislado con         Referencia externa      Tanabe y Fukunaga
  presupuesto completo        fuerte (H5)             2014

  Propuesta (A o B, más C si  Tratamiento             Fijados en la Fase 2
  supera el piloto)                                   
  ------------------------------------------------------------------------

Si el código del portafolio cooperativo no es reproducible, se reemplaza
por un modelo de islas con topología de anillo y se anota en el log de
desviaciones.

8\. Análisis estadístico

El análisis es por configuración (banco × dimensión × presupuesto) y
nunca agrega entre presupuestos. Los scripts leen los CSV crudos y
regeneran cada tabla del paper.

- Métrica: error f(x̂) − f(x\*), truncado a 0 bajo 10⁻⁸; comparación por
  mediana de 51 corridas y por rangos.

- Rangos promedio por configuración con empate a 10⁻⁸; desviación
  estándar de rangos entre tratamientos.

- Friedman con corrección de Iman-Davenport, reportando χ², grados de
  libertad y p; post-hoc de Shaffer sobre los tratamientos.

- Contraste primario: propuesta vs C1_div, Wilcoxon de rangos con signo
  por función sobre 51 pares CRN, Holm sobre la familia de funciones,
  empates descartados (declarado).

- Contrastes secundarios en el mismo formato: vs SBS, vs L-SHADE, vs
  C1_island, vs portafolio publicado, vs C3p.

- Tamaño de efecto: rank-biserial pareado por función; tabla
  better/equal/worse por presupuesto y dimensión.

- Exploratorio y etiquetado como tal: análisis por clase taxonómica y
  ablación de componentes del mecanismo ganador.

- Suplementario: media, mediana y desviación estándar de las 51 corridas
  por celda.

9\. Criterios de éxito y abandono por fase

Cada fase tiene un criterio que se evalúa antes de gastar la siguiente.
Un abandono en la Fase 3 no cancela el paper: el protocolo exige
reportar dónde gana y dónde no, y esa discusión es parte del resultado.

  --------------------------------------------------------------------------
  **Fase**        **Éxito**              **Abandono**    **Acción si
                                                         abandono**
  --------------- ---------------------- --------------- -------------------
  1\. Cotas       Virtual-best u oráculo Ninguna cota    Paper alterno con
                  supera a C1_div en ≥   supera el       datos existentes
                  20/70 con Holm,        umbral          
                  mediana r ≥ 0.3                        

  2\. Piloto      Un candidato cumple    Ningún          Paper alterno;
                  los cuatro criterios   candidato los   candidatos al
                  de la sección 5 en ≥ 2 cumple          suplementario
                  pares                                  

  3\.             Propuesta mejor que    Peor que mejor  Reportar igual;
  Confirmatorio   peor vs C1_div con     en ≥ 2          acotar el claim al
  10D             Holm en ≥ 3 de 4       presupuestos    régimen donde gana
                  presupuestos                           

  3\.             Mismo criterio que 10D Mismo criterio  Reportar igual;
  Confirmatorio                                          declarar
  50D                                                    dependencia de
                                                         dimensión

  3\. Referencia  No inferior en ≥ 2     Inferior en     Acotar el claim al
  L-SHADE         presupuestos           todos           portafolio de los
                                                         mismos solvers
  --------------------------------------------------------------------------

10\. Desviaciones admisibles y registro

Toda desviación se anota en deviations-log.md con fecha, descripción,
motivo e impacto, y se declara en el setup experimental o en las
limitaciones del paper.

  -----------------------------------------------------------------------
  **Admisible con declaración         **No admisible**
  previa**                            
  ----------------------------------- -----------------------------------
  Restringir 5·10⁶ a las 12 funciones Bajar de 51 corridas en cualquier
  del piloto                          celda

  Excluir F2 de CEC 2017 para todos   Evaluar un solo presupuesto
  los tratamientos                    

  Reemplazar un competidor no         Cambiar la lista de competidores
  reproducible por su equivalente     tras ver resultados
  declarado                           

  Usar implementaciones oficiales de  Retunear la propuesta por función,
  los autores                         presupuesto o dimensión

  Reducir CEC 2022 a 20D por          Elegir funciones o pares después de
  definición del banco                ver resultados

  Aplazar 50D a una segunda entrega,  Retirar el baseline C1_div de
  declarado en limitaciones           cualquier tabla
  -----------------------------------------------------------------------
