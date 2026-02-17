# Papers Directory

This directory contains academic papers related to the optimization algorithms for Vehicle Routing Problem (VRP).

## Structure

- `paper_ieee/`: Contains the paper in IEEE conference format, focusing on the comparative evaluation of bio-inspired algorithms for VRP.
  - `main.tex`: The main LaTeX document (extarticle class format)
  - `main.pdf`: Compiled PDF version

- `paper_extended/`: Contains the extended version of the paper with additional analysis.
  - `main.tex`: The main LaTeX document (IEEEtran class format)
  - `main.pdf`: Compiled PDF version (pending)

## Using the Documents

To compile the documents locally:

```bash
# For IEEE format paper (LuaLaTeX recommended)
cd /path/to/optimizacion
lualatex docs/papers/paper_ieee/main.tex
lualatex docs/papers/paper_ieee/main.tex  # Run twice for references

# For extended paper
cd /path/to/optimizacion
pdflatex docs/papers/paper_extended/main.tex
bibtex docs/papers/paper_extended/main
pdflatex docs/papers/paper_extended/main.tex
pdflatex docs/papers/paper_extended/main.tex
```

## Document Versions

- **IEEE Format Paper**: Evaluation of Recent Bio-inspired Algorithms for the Vehicle Routing Problem. This is a comparative study of 16 bio-inspired algorithms on standard VRP instances. Uses the IEEEtran document class.

- **Extended Paper**: Extended analysis with additional experiments and detailed results. Uses the extarticle document class with a two-column layout.

## IWINAC 2026 Paper (QC-DVRP)

Paper basado en los resultados del simulador QC-DVRP de este repositorio:

- **Titulo:** "Hippopotamus Optimization Algorithm Applied to Dynamic Vehicle Routing in Quick Commerce"
- **Autores:** Felipe Gonzalez, Rodrigo Olivares (Universidad de Valparaiso)
- **Formato:** Springer LNCS
- **Datos:** `results/dvrp_full_lam5_rh300/` (30 runs x 6 algoritmos)
- **Tablas LaTeX:** `results/dvrp_full_lam5_rh300/tables_v9/`
- **Source LaTeX:** Externo (directorio de tesis, no incluido en este repo)
- **Version:** v9 (Feb 2026) — incluye Nemenyi post-hoc, Fitness Z, boxplot DSR

## Notes

The papers reference figures stored in the main `figures/` directory at the repository root. The bibliography is managed through `docs/references.bib` which is linked from the repository root.

## Paper Versions Comparison

### IEEE Format Paper
- Uses the extarticle document class with customized formatting
- Two-column layout with custom margins
- Direct formatting and styling for academic presentation
- Best for general academic use or internal reviews

### Extended Paper Format
- Uses the extarticle document class
- Extended analysis with comprehensive results
- Detailed experimental methodology
- Suitable for journal submission or technical reports
