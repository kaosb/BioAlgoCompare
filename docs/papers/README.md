# Papers Directory

This directory contains academic papers related to the optimization algorithms for Vehicle Routing Problem (VRP).

## Structure

- `cisti_v1/`: Contains the first version of the paper for the CISTI conference, focusing on the comparative evaluation of bio-inspired algorithms for VRP.
  - `main.tex`: The main LaTeX document (extarticle class format)
  - `main.pdf`: Compiled PDF version

- `cisti_v2/`: Contains the second version of the paper for the CISTI conference, in IEEE format.
  - `main.tex`: The main LaTeX document (IEEEtran class format)
  - `main.pdf`: Compiled PDF version (pending)

## Using the Documents

To compile the documents locally:

```bash
# For cisti_v1 paper (LuaLaTeX recommended)
cd /path/to/optimizacion
lualatex docs/papers/cisti_v1/main.tex
lualatex docs/papers/cisti_v1/main.tex  # Run twice for references

# For cisti_v2 paper (IEEE format)
cd /path/to/optimizacion
pdflatex docs/papers/cisti_v2/main.tex
bibtex docs/papers/cisti_v2/main
pdflatex docs/papers/cisti_v2/main.tex
pdflatex docs/papers/cisti_v2/main.tex
```

## Document Versions

- **CISTI v1**: Evaluation of Recent Bio-inspired Algorithms for the Vehicle Routing Problem. This is a comparative study of 16 bio-inspired algorithms on Solomon instances. Uses the extarticle document class with a two-column layout.

- **CISTI v2**: The same content as v1 but formatted according to IEEE conference guidelines using the IEEEtran document class.

## Notes

The papers reference figures stored in the main `figures/` directory at the repository root. The bibliography is managed through `docs/references.bib` which is linked from the repository root.

## Paper Versions Comparison

### CISTI v1 (extarticle format)
- Uses the extarticle document class with customized formatting
- Two-column layout with custom margins
- Direct formatting and styling for academic presentation
- Best for general academic use or internal reviews

### CISTI v2 (IEEE format)
- Uses the IEEEtran document class with conference formatting
- Complies with IEEE conference guidelines
- Formatted specifically for the CISTI conference requirements
- Suitable for official conference submission