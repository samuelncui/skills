LATEXMK = latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape

.PHONY: all clean
all:
	$(LATEXMK) notes.tex
	$(LATEXMK) quick-reference.tex

clean:
	latexmk -c notes.tex
	latexmk -c quick-reference.tex
