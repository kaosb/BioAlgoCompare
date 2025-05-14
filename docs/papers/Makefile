# LaTeX compilation Makefile
# Output is generated in docs/papers/cisti_v2/main.pdf

.PHONY: cisti clean

cisti:
	latexmk -lualatex -pdf cisti_v2/main.tex

clean:
	latexmk -C cisti_v2/main.tex