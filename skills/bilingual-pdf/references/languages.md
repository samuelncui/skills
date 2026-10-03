# Native language contexts

XeLaTeX, Polyglossia and fontspec select the active language inside each side. This provides language-specific line breaking, punctuation and hyphenation where the installed distribution supplies patterns. Text direction does not reorder the physical columns.

The bundled JSON profiles map to these native names/fonts:

| Profile | Polyglossia | Body font |
| --- | --- | --- |
| en | english | Latin Modern Roman |
| fr | french | Latin Modern Roman |
| zh-Hans | chinese | Noto Serif CJK SC |
| zh-Hant | chinese, traditional variant | Noto Serif CJK TC |
| ja | japanese | Noto Serif CJK JP |
| ar | arabic, western numerals | Noto Naskh Arabic |

Noto Sans CJK provides CJK headings. Arabic uses its own font for both body and headings. Latin Modern Math supplies mathematical glyphs, and a Latin marker font supplies bullets/numbers missing in some Arabic fonts. Do not silently substitute a vaguely similar installed font.

In an authored project, configure languages normally before `\begin{document}`:

```tex
\setotherlanguage[numerals=maghrib]{arabic}
\newfontfamily\arabicfont[Script=Arabic]{Noto Naskh Arabic}
\newfontfamily\arabicfontsf[Script=Arabic]{Noto Naskh Arabic}
\ParallelLanguages{english}{arabic}
```

For Chinese or Japanese, use `\setotherlanguage{chinese}` / `\setotherlanguage{japanese}` and the corresponding `\chinesefont`, `\chinesefontsf`, `\japanesefont`, `\japanesefontsf` definitions. Start from the tested examples rather than relying on a font name to establish a language. Use `\textenglish{2026-10-03, 09:30}` for an isolated Latin run inside Arabic.

Install a coherent TeX distribution. Polyglossia 2.3 introduced automatic Chinese/Japanese line breaking. For older distribution versions, the package supplies a narrowly guarded equivalent, including restoration after nested English/Arabic runs; it does not change the line-break penalty. French hyphenation normally needs its language-pattern package (`texlive-lang-french` on Debian/Ubuntu); merely having Polyglossia installed is not enough. Arabic needs the matching `bidi` package (`texlive-lang-arabic`). Do not mix a newer bidi patch with an older array/LaTeX kernel and then blame the manuscript for undefined commands. Keep distribution packages consistent. The package contains a narrowly guarded correction for a trailing table-space defect in bidi 25.2.2; it does not alter other releases. The reference CI uses Ubuntu's matching packages, including latexmk, XeLaTeX, LaTeX extra/science, French/Arabic language packages, Latin Modern and Noto fonts.

Native `.tex` can configure additional languages/fonts through Polyglossia, but each new combination needs actual compilation, glyph, direction and page review. The demonstrated cases are Latin–Latin (English/French), Latin–CJK (English/Chinese), Latin–RTL (English/Arabic) and CJK–CJK (Chinese/Japanese). Traditional Chinese and other combinations are not implicitly certified. The JSON adapter rejects a mixed simplified/traditional Chinese pair because both map to one Polyglossia language; native custom variants require separate configuration and testing. Vertical writing, PDF/UA, unrestricted cross-script font fallback and native Windows font discovery are not claimed.
