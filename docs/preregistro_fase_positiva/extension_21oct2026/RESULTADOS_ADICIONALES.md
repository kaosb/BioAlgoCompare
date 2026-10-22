# Resultados adicionales — cálculo automático completo

Tabla derivada de `RESULTADOS_ADICIONALES.json`, la salida del analizador; la interpretación está en el artículo (§5.5) y en D38 del registro de desviaciones.

| Configuración | Contraste | Mejor/igual/peor | Mediana r | Mediana d |
|---|---|---|---|---|
| GWOGA_5000 | C1_shared/C1_div | 7/64/0 | 1.000 | 0.000 |
| GWOGA_5000 | CTRLg/C1_shared | 0/66/5 | -0.275 | 0.018 |
| GWOGA_5000 | C3p/C1_shared | 0/71/0 | -0.048 | 0.000 |
| GWOGA_5000 | REPLAY/PERMUTED | 0/71/0 | 0.055 | 0.000 |
| GWOGA_5000 | C3p/LSHADE | 6/21/44 | -0.732 | 0.185 |
| GWOGA_5000 | C1_shared/LSHADE | 7/20/44 | -0.754 | 0.191 |
| GWOGA_50000 | C1_shared/C1_div | 0/61/10 | -1.000 | 0.000 |
| GWOGA_50000 | CTRLg/C1_shared | 0/71/0 | 0.035 | -0.001 |
| GWOGA_50000 | C3p/C1_shared | 0/70/1 | -0.128 | 0.005 |
| GWOGA_50000 | REPLAY/PERMUTED | 0/71/0 | 0.099 | 0.000 |
| GWOGA_50000 | C3p/LSHADE | 1/1/69 | -1.000 | 0.929 |
| GWOGA_50000 | C1_shared/LSHADE | 1/1/69 | -1.000 | 0.925 |
| DEGA_5000 | C1_shared/C1_div | 0/71/0 | -1.000 | 0.000 |
| DEGA_5000 | CTRLg/C1_shared | 21/40/10 | 0.291 | -0.011 |
| DEGA_5000 | C3p/C1_shared | 5/55/11 | -0.192 | 0.007 |
| DEGA_5000 | REPLAY/PERMUTED | 0/71/0 | 0.000 | 0.000 |
| DEGA_5000 | C3p/LSHADE | 5/8/58 | -0.967 | 0.291 |
| DEGA_5000 | C1_shared/LSHADE | 5/8/58 | -0.973 | 0.303 |
| DEGA_50000 | C1_shared/C1_div | 0/71/0 | 0.000 | 0.000 |
| DEGA_50000 | CTRLg/C1_shared | 15/32/24 | 0.018 | -0.000 |
| DEGA_50000 | C3p/C1_shared | 1/44/26 | -0.233 | 0.035 |
| DEGA_50000 | REPLAY/PERMUTED | 0/68/3 | -0.077 | 0.002 |
| DEGA_50000 | C3p/LSHADE | 2/4/65 | -0.998 | 0.743 |
| DEGA_50000 | C1_shared/LSHADE | 5/1/65 | -0.997 | 0.732 |
| PSOACO_5000 | C1_shared/C1_div | 0/65/6 | 0.200 | 0.000 |
| PSOACO_5000 | CTRLg/C1_shared | 0/27/44 | -0.724 | 0.105 |
| PSOACO_5000 | C3p/C1_shared | 3/58/10 | -0.042 | 0.000 |
| PSOACO_5000 | REPLAY/PERMUTED | 0/71/0 | 0.247 | -0.000 |
| PSOACO_5000 | C3p/LSHADE | 6/23/42 | -0.661 | 0.168 |
| PSOACO_5000 | C1_shared/LSHADE | 7/24/40 | -0.612 | 0.230 |
| PSOACO_50000 | C1_shared/C1_div | 4/65/2 | 1.000 | 0.000 |
| PSOACO_50000 | CTRLg/C1_shared | 3/61/7 | -0.011 | -0.000 |
| PSOACO_50000 | C3p/C1_shared | 0/63/8 | -0.163 | 0.004 |
| PSOACO_50000 | REPLAY/PERMUTED | 1/70/0 | 0.210 | 0.000 |
| PSOACO_50000 | C3p/LSHADE | 0/3/68 | -1.000 | 0.900 |
| PSOACO_50000 | C1_shared/LSHADE | 1/5/65 | -0.998 | 0.784 |

## Perturbación efectiva y presupuesto

| Configuración | Corridas con secuencia modificada | Corridas totales | FES L-SHADE mín./máx. |
|---|---|---|---|
| GWOGA_5000 | 689 | 3621 | [5000, 5000] |
| GWOGA_50000 | 3161 | 3621 | [47581, 50000] |
| DEGA_5000 | 644 | 3621 | [5000, 5000] |
| DEGA_50000 | 3060 | 3621 | [47581, 50000] |
| PSOACO_5000 | 1256 | 3621 | [5000, 5000] |
| PSOACO_50000 | 2117 | 3621 | [47581, 50000] |
