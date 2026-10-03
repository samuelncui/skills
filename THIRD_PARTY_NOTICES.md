# Third-party dependencies

The repository does not bundle third-party fonts or a TeX distribution. Install dependencies from their official sources and retain their license notices when redistributing them.

- TeX Live packages have individual licenses. In particular fontspec, unicode-math, Polyglossia, [paracol](https://ctan.org/pkg/paracol), hyperref/xr-hyper and [bidi](https://ctan.org/pkg/bidi) use LaTeX Project Public License terms. Consult the actual installed package notices.
- Noto fonts use the [SIL Open Font License](https://github.com/notofonts/arabic/blob/main/OFL.txt). Font embedding does not by itself apply the font license to a document's text. Redistribution of font files requires their accompanying license and applicable name conditions.
- [Latin Modern fonts](https://ctan.org/pkg/lm) carry the GUST Font License. They are external dependencies here.
- [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) is available under AGPL or commercial licensing. Check its current terms for your use and redistribution; this repository's MIT license does not relicense it. Pillow and fonttools also retain their own licenses.

Original example text and the authored renderer/templates in this repository are covered by the repository license unless a file states otherwise. Do not copy restricted templates or educational material into this project simply because they are visible online.

The shared photograph in all four article examples is by D. Benjamin Miller and is dedicated to the public domain under CC0 1.0. Its source and transformations are recorded in [the photo credit](skills/bilingual-pdf/references/photo-credit.md); it is not relicensed as authored repository content.
