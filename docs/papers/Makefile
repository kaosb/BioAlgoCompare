# LaTeX compilation Makefile para papers CISTI
# ==========================================
#
# Este Makefile permite compilar ambas versiones del paper CISTI.
#
# Uso:
#   make -C docs/papers cisti_v2   - Compila la versión 2 (extarticle) del paper usando LuaLaTeX
#                                   - Genera el archivo docs/papers/cisti_v2/main.pdf
#
#   make -C docs/papers cisti_v1   - Compila la versión 1 (IEEEtran) del paper usando LuaLaTeX
#                                   - Genera el archivo docs/papers/cisti_v1/main.pdf
#
#   make -C docs/papers cisti      - Alias para cisti_v2 (versión actual)
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

.PHONY: cisti cisti_v1 cisti_v2 all clean

# Alias para la versión actual (v2)
cisti: cisti_v2

# Compilar la versión 1 (formato IEEEtran para conferencia IEEE)
cisti_v1:
	@echo "Compilando paper CISTI v1 (IEEEtran) con LuaLaTeX..."
	cd cisti_v1 && latexmk -lualatex -pdf main.tex
	@echo "Compilación terminada. El PDF está disponible en docs/papers/cisti_v1/main.pdf"

# Compilar la versión 2 (formato extarticle - versión completa)
cisti_v2:
	@echo "Compilando paper CISTI v2 (extarticle) con LuaLaTeX..."
	cd cisti_v2 && latexmk -lualatex -pdf main.tex
	@echo "Compilación terminada. El PDF está disponible en docs/papers/cisti_v2/main.pdf"

# Compilar ambas versiones
all: cisti_v1 cisti_v2
	@echo "Todas las versiones compiladas correctamente."

# Limpiar archivos temporales
clean:
	@echo "Limpiando archivos temporales de LaTeX..."
	cd cisti_v1 && latexmk -C main.tex
	cd cisti_v2 && latexmk -C main.tex
	rm -f *.aux *.log *.out *.bbl *.blg *.fdb_latexmk *.fls *.synctex.gz main.pdf
	@echo "Limpieza completada"