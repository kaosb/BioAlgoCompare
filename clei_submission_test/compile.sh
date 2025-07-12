#!/bin/bash
# Compilar documento LaTeX
cd clei_submission
pdflatex paper_clei2025.tex
pdflatex paper_clei2025.tex  # Segunda pasada para referencias
echo "Documento PDF generado: paper_clei2025.pdf"
