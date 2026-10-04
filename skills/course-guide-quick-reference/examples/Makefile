LATEXMK = latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape
# Treat a path as literal data even when passed as a Make command-line variable.
override BILINGUAL_PDF_SKILL := $(value BILINGUAL_PDF_SKILL)
export BILINGUAL_PDF_SKILL

.PHONY: all check-dependency clean
all: check-dependency
	TEXINPUTS="$${BILINGUAL_PDF_SKILL}/assets//:$${TEXINPUTS}:" $(LATEXMK) notes.tex
	TEXINPUTS="$${BILINGUAL_PDF_SKILL}/assets//:$${TEXINPUTS}:" $(LATEXMK) quick-reference.tex

check-dependency:
	@test -n "$${BILINGUAL_PDF_SKILL}" && test -f "$${BILINGUAL_PDF_SKILL}/assets/paralleltext.sty" || { echo 'Set BILINGUAL_PDF_SKILL to the installed bilingual-pdf directory.' >&2; exit 1; }

clean:
	latexmk -c notes.tex
	latexmk -c quick-reference.tex
