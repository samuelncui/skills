# Language, font and direction API

XeLaTeX, Polyglossia and fontspec establish each side's language, shaping, line breaking and fonts. Direction never swaps physical columns: \ParallelLanguages{english}{hebrew} places English left and Hebrew right. \ParallelSelect{right} selects right content, regardless of its direction.

The calling agent supplies logical Unicode text. The renderer does not translate or infer which pieces correspond.

## Built-in structured profiles

| JSON ID | Polyglossia name/options | Direction | Body / heading family |
| --- | --- | --- | --- |
| en | english | LTR | Latin Modern Roman / Latin Modern Sans |
| fr | french | LTR | Latin Modern Roman / Latin Modern Sans |
| zh-Hans | chinese | LTR | Noto Serif CJK SC / Noto Sans CJK SC |
| zh-Hant | chinese, variant=traditional | LTR | Noto Serif CJK TC / Noto Sans CJK TC |
| ja | japanese | LTR | Noto Serif CJK JP / Noto Sans CJK JP |
| ar | arabic, numerals=maghrib | RTL | Noto Naskh Arabic / Noto Naskh Arabic |
| he | hebrew | RTL | DejaVu Sans / DejaVu Sans |

Both sides may use one profile. Other BCP-47-looking IDs are not automatically supported. Mixed zh-Hans/zh-Hant is rejected by the JSON adapter because both configure one native language name; native custom variants need separate configuration/testing.

Latin Modern Math supplies shared math glyphs. \MarkerFont uses Latin Modern Roman for bullets/counters missing from some script fonts. Heading-font selection is independent of body selection; verify both. Exact preflight rejects fontconfig substitutions rather than silently treating them as the requested family.

## Native setup

The package initially loads English and Latin Modern Roman/Sans/Math. Declare languages and roman/sans families in the preamble, then choose ordered sides. \ParallelLanguages takes native names, not JSON IDs; it does not declare languages/fonts.

### English and Hebrew

~~~tex
\setotherlanguage{hebrew}
\newfontfamily\hebrewfont[Script=Hebrew]{DejaVu Sans}
\newfontfamily\hebrewfontsf[Script=Hebrew]{DejaVu Sans}
\ParallelLanguages{english}{hebrew}
% Body:
\ParallelText{sample}
  {A pair begins at the same height.}
  {זוג מתחיל באותו גובה.}
\ParallelText{time}
  {The time is 09:30.}
  {השעה היא \textenglish{09:30}.}
~~~

Supply logical text, not manually reversed glyphs. Script=Hebrew enables intended shaping. Test punctuation, parentheses, dates/numbers and vowel/cantillation marks present in actual content. Unpointed examples do not demonstrate every combining-mark combination.

### English and Arabic

~~~tex
\setotherlanguage[numerals=maghrib]{arabic}
\newfontfamily\arabicfont[Script=Arabic]{Noto Naskh Arabic}
\newfontfamily\arabicfontsf[Script=Arabic]{Noto Naskh Arabic}
\ParallelLanguages{english}{arabic}
~~~

The profile chooses western/Maghrib numerals. Native authors may choose another documented Polyglossia policy and test it. Arabic body/headings deliberately share the Naskh family.

### French, Chinese and Japanese

~~~tex
\setotherlanguage{french}
\newfontfamily\frenchfont{Latin Modern Roman}
\newfontfamily\frenchfontsf{Latin Modern Sans}

\setotherlanguage{chinese}
\newfontfamily\chinesefont{Noto Serif CJK SC}
\newfontfamily\chinesefontsf{Noto Sans CJK SC}

\setotherlanguage{japanese}
\newfontfamily\japanesefont{Noto Serif CJK JP}
\newfontfamily\japanesefontsf{Noto Sans CJK JP}
\ParallelLanguages{chinese}{japanese}
~~~

For traditional Chinese, configure \setotherlanguage[variant=traditional]{chinese} and TC families instead of SC. Defining both variants through the same family command does not keep them independent.

## Mixed direction and scripts

Inside Hebrew/Arabic use \textenglish{2026-10-05, 09:30} to isolate LTR dates, numbers or identifiers. Use configured language commands for other script changes. Direction boundaries and font selection are distinct; a font name alone does not create a language context.

The JSON run form on RTL sides is:

~~~json
{"runs":[
  {"text":"זמן: ","direction":"rtl"},
  {"text":"09:30","direction":"ltr"}
]}
~~~

Include intended spaces in each run. LTR maps to textenglish; RTL inherits Arabic/Hebrew. The same run objects are accepted in paired block text, list items and table header/body cells on an Arabic/Hebrew side. Non-RTL sides require plain strings; document titles require plain strings on both sides. This is not an arbitrary per-run language API, and embedded bidi controls are rejected in content text. Use trusted native TeX for mixed-direction titles or language/font switches beyond this run model. Table runs do not change the bounded layout: the complete JSON table and captions must fit on one page, with no row pagination or continuation headers. See the independent [input API](input.md).

\ParallelEquation uses explicit LTR math and one counter; native unnumbered math may appear inside side bodies. Counter/folio/reference suffixes are isolated to avoid reversing Latin digits/parentheses. Inspect their visual order rather than relying on extracted PDF text order.

Running headers, footers and tabs use furniture-language (default main language) at shipout. Wrap additional scripts in configured language commands. Entry-headword helpers select their own left/right language. See [configuration](configuration.md).

## CJK and coherent dependencies

Polyglossia 2.3 introduced automatic Chinese/Japanese line-breaking setup. Older distributions receive the package's narrowly guarded equivalent, including restoration after nested language switches. It does not change line-break penalties or make Latin fonts cover CJK. Inspect punctuation, long lines and returns to CJK after embedded Latin/RTL runs.

Use a coherent TeX distribution. French needs hyphenation patterns as well as Polyglossia (commonly texlive-lang-french on Debian/Ubuntu). Arabic/Hebrew require their language support and a matching bidi package; distributions may supply these through language packages such as texlive-lang-arabic and texlive-lang-other. Names vary: inspect actual installed packages. Do not mix an arbitrarily newer bidi patch with an older kernel/array implementation.

The package has a narrowly version-guarded correction for a trailing table-space defect in bidi 25.2.2; other versions are untouched. A warning about an unrecognized definition calls for actual table-width QA.

## Verification scope

Structured preflight checks body/heading families, Latin Modern Math, marker family and text glyph coverage using fontconfig/fontTools. A profile listing does not prove fonts exist on this machine. Install dependencies only through the authorized environment workflow; do not substitute/download fonts silently.

For each used combination, compile and inspect:
- Physical column order, synchronized starts and continuation pages
- Requested body/headings, embedded fonts, glyphs and combining marks
- RTL shaping, punctuation, numbers, equations and links
- CJK line breaking, mixed-script returns and table/list widths
- Selected-language editions, furniture and both print parities

Examples exercise selected Latin–Latin, Latin–CJK, Latin–RTL (Arabic/Hebrew) and CJK–CJK combinations. Report actual tested artifacts separately; do not infer universal support from the profile list or a small example matrix. Native authoring may configure more Polyglossia languages/fonts, but every new combination needs verification. Vertical writing, unrestricted cross-script fallback, PDF/UA and native Windows font discovery are not claimed.
