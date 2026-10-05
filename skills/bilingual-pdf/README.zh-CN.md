# Bilingual PDF

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

将对应内容放在便于比较的位置：段落起点、列表项和表格行逐一对齐，物理左右栏之间保持稳定的分隔线。长段落可以保持整组不拆分，也可以跨页延续。原生 LaTeX 和 JSON 共用同一个权威版式包。

调用技能的 agent 提供配对内容。此技能负责渲染，不负责选择译文、改写正文或判断哪些表述相互对应。

此技能只排版已提供的配对文本，不负责 OCR、从已有 PDF 提取内容、自动翻译或保留原 PDF 的页面版式。

## 功能

- 分别对齐每组段落、列表项和表格行，不受译文长度差异影响
- 允许段落跨页延续，并在下一组内容开始前重新对齐
- 将物理左右栏顺序与语言的 LTR/RTL 书写方向分开处理
- 渲染一张共享的通栏图片并配上双语图注，或分别渲染两张本地化图片
- 共用公式与插图计数器，并生成文档内页码链接
- 支持双栏对照、仅左栏语言和仅右栏语言版本，以及可配置的纸张与装订尺寸、封面、页码、语义样式和导航

[![英中使用指南中的段落对齐](examples/en-zh-Hans/preview.png)](examples/en-zh-Hans/output.pdf)

[![英语／希伯来语示例](examples/en-he/preview.png)](examples/en-he/output.pdf)

这些预览来自实际输出。请打开 PDF 查看所有页面；首页图片只是浏览辅助，不能作为完整的视觉验证证据。

## 以自身用法为内容的示例

各版本使用相同的使用指南内容，演示段落、表格、插图、引用和一个简短公式。重复出现的英文和中文段落在各版本中保持完全一致。

| 语言对 | PDF | 结构化源文件 | 原生项目 |
| --- | --- | --- | --- |
| 英语／法语 | [output.pdf](examples/en-fr/output.pdf) | [source.json](examples/en-fr/source.json) | [main.tex](examples/en-fr/main.tex) |
| 英语／中文 | [output.pdf](examples/en-zh-Hans/output.pdf) | [source.json](examples/en-zh-Hans/source.json) | [main.tex](examples/en-zh-Hans/main.tex) |
| 英语／阿拉伯语 | [output.pdf](examples/en-ar/output.pdf) | [source.json](examples/en-ar/source.json) | [main.tex](examples/en-ar/main.tex) |
| 英语／希伯来语 | [output.pdf](examples/en-he/output.pdf) | [source.json](examples/en-he/source.json) | [main.tex](examples/en-he/main.tex) |
| 中文／日语 | [output.pdf](examples/zh-Hans-ja/output.pdf) | [source.json](examples/zh-Hans-ja/source.json) | [main.tex](examples/zh-Hans-ja/main.tex) |

仅用于示例的插图统一存放在 `examples/shared/`，不重复复制。运行时的 `assets/` 包含可复用的版式包和可选配置。原生示例无需 Python 或仓库维护工具即可编译。

## 原生 LaTeX

从此技能的安装目录执行：

```sh
cd examples/en-fr
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape -jobname=output main.tex
```

编写自己的文档时，将完整示例复制到新目录。保留版式包与图片的路径关系，或将所需的包和图片复制进可移交的项目。编辑 `content.tex` 和 `languages.tex`。[完整原生 API](references/latex.md) 说明每个公开命令、参数、默认值和错误边界，并提供最小文档示例。

在导言区设置全局段落策略，并按需为单个段落覆盖：

```tex
\ParallelSetup{paragraph-flow=breakable}
\ParallelParagraph{explanation}{Left paragraph.}{Right paragraph.}
\ParallelParagraph[flow=keep]{short}{Keep this pair together.}{Keep this pair together.}
```

`ParallelText` 始终作为不可拆分单元；`ParallelProse` 明确允许跨页延续。要求保持整组的单元如果过大，会明确报错。渲染器不会缩小或截断内容。

## 结构化 JSON

从此技能的安装目录执行：

```sh
python3 scripts/bilingual_pdf.py export examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-project
python3 scripts/bilingual_pdf.py render examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-build
```

`export` 生成可移交、可编辑的 LaTeX 项目。`render` 还会编译并检查它。输出目录若已存在，会被拒绝。添加 `--mode left` 或 `--mode right` 可生成选定语言的版本。

参阅独立的 [JSON Schema](schemas/document.schema.json) 和[字段参考](references/input.md)。`layout.paragraph_flow` 设置为 `keep` 或 `breakable`，段落自身的 `flow` 可以覆盖它。`atomic` 仍作为 `keep` 的兼容别名。除 Schema 验证外，运行时还会检查 ID、尺寸、引用、字体和资源路径。

图片路径必须解析到输入目录或显式指定的 `--asset-root` 内；绝对路径、目录穿越和通过符号链接越界均会被拒绝。适配器从不下载资源或依赖。

## 无需分叉版式即可配置

[配置参考](references/configuration.md) 覆盖页面尺寸、装订、分隔线外观、页码、间距、样式、语义角色、封面和导航。默认设置无需额外配置即可使用。只覆盖需要调整的设置，或使用文档说明的原生钩子，并将内容、语言／字体映射与呈现方式分开管理。

JSON 表格会对齐各行，但整张表及其标题保持为一个不可拆分单元。原生配对行可放在 `ParallelKeep` 外，以允许在行与行之间分页。单行仍不可拆分；目前不提供行内自动拆分或 longtable 式重复表头。

## 依赖、检查与交付

使用 XeLaTeX、latexmk 以及文档列出的 TeX 包和字体。法语断词、阿拉伯语／希伯来语双向排版、CJK 字体与混合文字片段见[语言设置](references/languages.md)。结构化导入和可选 PDF 检查使用 `requirements.txt` 中的依赖、Fontconfig 和 `kpsewhich`。

按照[渲染验收要求](references/acceptance.md)，检查实际页面的对齐、跨页延续、字形、RTL 字形塑形、裁切、图片、引用和印刷尺寸。机械检查不能证明语义正确。分别报告通过、失败和未执行的检查。

交付 PDF、可移交的原生源项目，以及使用过的 JSON；包含必要资源与许可证。原生 TeX 和 latexmk 配置可执行代码，`-no-shell-escape` 并非沙箱。请使用可信源文件或适当的隔离环境。竖排、任意浮动体／宏参数中的逐字内容、原生 Windows 字体发现及 PDF/UA 不在已测试的支持范围内。

原创代码、教程文本和图示采用 [MIT 许可证](LICENSE)。第三方依赖保留各自的许可证。公开示例中不得包含私有文档内容。
