LATEXMK = latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape
PRODUCTS ?= notes quick-reference
STUDY_NOTES_SKILL ?= ..
# Installed paths are literal data, including spaces and Make-like characters.
override BILINGUAL_PDF_SKILL := $(value BILINGUAL_PDF_SKILL)
override STUDY_NOTES_SKILL := $(value STUDY_NOTES_SKILL)
override PRODUCTS := $(value PRODUCTS)
export BILINGUAL_PDF_SKILL STUDY_NOTES_SKILL PRODUCTS

.PHONY: all check-dependency clean
all: check-dependency
	@set -eu; test -n "$${PRODUCTS}" || { echo 'Select at least one product.' >&2; exit 1; }; \
	notes=false; for product in $${PRODUCTS}; do case "$$product" in notes) notes=true;; quick-reference|keyword-index|decision-tree) ;; *) echo "Unknown product: $$product" >&2; exit 1;; esac; done; \
	printf '\\newif\\ifStudyBuildNotes\\StudyBuildNotes%s\n' "$$notes" > .build-products.tex; \
	export TEXINPUTS="$${STUDY_NOTES_SKILL}/assets//:$${BILINGUAL_PDF_SKILL}/assets//:$${TEXINPUTS:-}:"; \
	if test "$$notes" = true; then $(LATEXMK) notes.tex; fi; \
	for product in $${PRODUCTS}; do if test "$$product" != notes; then $(LATEXMK) "$$product.tex"; fi; done

check-dependency:
	@test -n "$${BILINGUAL_PDF_SKILL}" && test -f "$${BILINGUAL_PDF_SKILL}/assets/paralleltext.sty" && test -f "$${BILINGUAL_PDF_SKILL}/SKILL.md" || { echo 'Set BILINGUAL_PDF_SKILL to the installed bilingual-pdf directory.' >&2; exit 1; }
	@test -f "$${STUDY_NOTES_SKILL}/assets/studytools.sty" && test -f "$${STUDY_NOTES_SKILL}/assets/study-tree.tex" || { echo 'Set STUDY_NOTES_SKILL to the installed study-notes directory.' >&2; exit 1; }

clean:
	latexmk -c notes.tex quick-reference.tex keyword-index.tex decision-tree.tex
