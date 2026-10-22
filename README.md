# BioAlgoCompare

Código, datos y registro experimental de estudios sobre metaheurísticas. El
estudio actual, pre-registrado, evalúa la cooperación entre optimizadores
heterogéneos con presupuesto total compartido y una salvaguarda frente a la
transferencia negativa. La plataforma conserva además el código y los resultados
históricos de VRP y de aprendizaje por imitación, con alcance y validez distintos.

## Revisar el estudio actual

1. [Guía de la fase de transferencia](README_FASE_POSITIVA.md): estado,
   validez de los datos, pre-registro y enmiendas, entorno, pruebas y origen de
   cada tabla del borrador (incluida la extensión del 21-Oct-2026).
2. [Pre-registro, enmiendas y registro de desviaciones](docs/preregistro_fase_positiva/README.md)
   (`deviations-log.md`, D0–D40).
3. [Validez de los resultados](results/cooperative/LEEME_VALIDEZ.md): campañas
   corregidas y registros invalidados o superados.
4. [Componentes del código](cooperative/README.md): orquestador, gate,
   memoria y contabilidad del presupuesto.

## Entorno y comprobación rápida

Python 3.12 con [`requirements-fase-positiva.lock`](requirements-fase-positiva.lock):

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-fase-positiva.lock
.venv/bin/python -m pytest -q -p no:cacheprovider -o addopts="" \
    tests/test_cec_official.py tests/test_cooperative_invariants.py   # 192 pruebas
.venv/bin/python scripts/cec_harness/tablas_paper_v13.py --salida /ruta/de/salida
```

## Material histórico

- [Plataforma original para VRP](README_VRP.md). El artículo sobre QC-DVRP de esa etapa
  (González y Olivares) se publicó en CISTI 2026.
- [Estudio IL × CEC](REPRODUCIBILITY.md): sus resultados CEC quedaron
  invalidados al corregir el benchmark (D16).
- [Índice de documentación técnica](docs/index.md).

## Cita

```bibtex
@software{gonzalez2026bioalgocompare,
  title={BioAlgoCompare: evaluación de metaheurísticas bioinspiradas y cooperación entre solvers},
  author={Gonz\'alez, Felipe and Olivares, Rodrigo},
  year={2026},
  url={https://github.com/kaosb/BioAlgoCompare}
}
```

Licencia MIT (ver [LICENSE](LICENSE)).
