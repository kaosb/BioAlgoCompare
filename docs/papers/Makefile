# LaTeX compilation Makefile for research papers
# ==============================================
#
# This Makefile compiles different versions of the research paper.
#
# Uso:
#   make -C docs/papers paper_extended - Compiles the extended version (extarticle) using LuaLaTeX
#                                       - Generates docs/papers/paper_extended/main.pdf
#
#   make -C docs/papers paper_ieee    - Compiles the IEEE format version using LuaLaTeX
#                                       - Generates docs/papers/paper_ieee/main.pdf
#
#   make -C docs/papers paper         - Alias for paper_extended (current version)
#
#   make -C docs/papers all        - Compila ambas versiones del paper
#
#   make -C docs/papers clean      - Elimina todos los archivos auxiliares de la compilación
#                                   - Útil para limpiar artefactos temporales
#
# Notas:
#   - Se usa LuaLaTeX para mejor soporte de fuentes y Unicode
#   - Las referencias bibliográficas se encuentran en docs/references.bib
#   - Las figuras se encuentran en el directorio figures/

.PHONY: paper paper_ieee paper_extended all clean

# Alias for current version (extended)
paper: paper_extended

# Compile IEEE format version
paper_ieee:
	@echo "Compiling IEEE format paper with LuaLaTeX..."
	cd paper_ieee && latexmk -lualatex -pdf main.tex
	@echo "Compilation finished. PDF available at docs/papers/paper_ieee/main.pdf"

# Compile extended version (extarticle format)
paper_extended:
	@echo "Compiling extended paper with LuaLaTeX..."
	cd paper_extended && latexmk -lualatex -pdf main.tex
	@echo "Compilation finished. PDF available at docs/papers/paper_extended/main.pdf"

# Compile current version
paper_current:
	@echo "Compiling current paper with PDFLaTeX..."
	cd paper_current && pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex
	@echo "Compilation finished. PDF available at docs/papers/paper_current/paper.pdf"

# Compile all versions
all: paper_ieee paper_extended paper_current
	@echo "All paper versions compiled successfully."

# Clean temporary files
clean:
	@echo "Cleaning LaTeX temporary files..."
	cd paper_ieee && latexmk -C main.tex
	cd paper_extended && latexmk -C main.tex
	cd paper_current && rm -f *.aux *.log *.out *.bbl *.blg *.fdb_latexmk *.fls *.synctex.gz
	rm -f *.aux *.log *.out *.bbl *.blg *.fdb_latexmk *.fls *.synctex.gz main.pdf
	@echo "Cleanup completed"
