# LaTeX compilation Makefile para papers CISTI
# ==========================================
#
# Este Makefile compila el paper en formato IEEE Conference (IEEEtran).
#
# Uso:
#   make -C docs/papers cisti      - Compila el paper usando LuaLaTeX (recomendado)
#                                   - Genera el archivo docs/papers/cisti_v2/main.pdf
#
#   make -C docs/papers clean      - Elimina todos los archivos auxiliares de la compilación
#                                   - Útil para limpiar artefactos temporales
#
# Notas:
#   - Se usa LuaLaTeX para mejor soporte de fuentes y Unicode
#   - Las referencias bibliográficas se encuentran en docs/references.bib
#   - Las figuras se encuentran en el directorio figures/

.PHONY: cisti clean

# Compilar el paper principal en formato IEEE
cisti:
	@echo "Compilando paper CISTI v2 con LuaLaTeX..."
	latexmk -lualatex -pdf cisti_v2/main.tex
	@echo "Compilación terminada. El PDF está disponible en docs/papers/cisti_v2/main.pdf"

# Limpiar archivos temporales
clean:
	@echo "Limpiando archivos temporales de LaTeX..."
	latexmk -C cisti_v2/main.tex
	@echo "Limpieza completada"