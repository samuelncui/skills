# Bilingual HTML

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

把已有的双语配对文本生成为可离线浏览的便携文档。每段的两种语言始终放在一起：桌面端分为两栏，窄屏端先源文、后译文。适合需要在浏览器中对照阅读的文章、说明和讲义。

调用方负责提供对应文本。此技能保留原文措辞并排版；提取源内容、翻译以及判断哪些表述互相对应，由调用方的工作流负责。

## 功能

- 对齐每组标题、段落和列表项的起点
- 保留真实的表格行和单元格，每个单元格包含两种语言；宽表格支持键盘横向滚动
- 每幅图使用一张共享图片，配有双语图注和替代描述
- 分别设置两种语言的 LTR/RTL 方向，独立控制桌面端左右栏顺序
- 可配置宽度、间距、颜色和每种语言的字体
- 输出 HTML、CSS 和本地资源，无需 JavaScript、远程字体或运行时服务器

## 完整示例与预览

原创英法教程以技能自身的用法为内容，演示标题、正文、有序／无序列表、表格和图片：

- [可编辑的排版 JSON](examples/tutorial/layout.json)
- [完整生成的 HTML](examples/tutorial/site/index.html)，下载整个 `site/` 目录后可打开浏览
- [原创图片](examples/tutorial/images/pairs.png)与[示例清单](examples/MANIFEST.json)

在此技能的安装目录执行：

```sh
set -eu
python3 --version
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

需要 Python 3.11 或更新版本。输出目录 `page` 必须尚不存在，父目录须已存在。直接用浏览器打开 `page/index.html`，无需服务器或构建工具；仓库网站可能只显示 HTML 源代码，不直接渲染网页。

## 结构化 JSON：使用已有配对内容

按内嵌对译文本的排版格式编写输入，参阅[可直接运行的最小示例](references/rendering.md#minimal-structured-example)、[字段约定](references/rendering.md#embedded-pair-layout)和 [JSON Schema](schemas/layout.schema.json)。以下命令复制完整教程，保留安装包内的原始示例：

```sh
set -eu
mkdir html-work
cp examples/tutorial/layout.json html-work/layout.json
cp -R examples/tutorial/images html-work/images
python3 scripts/bilingual_html.py render html-work/layout.json --output html-work/page
```

编辑复制后的 `layout.json`，为每个标题、段落、列表项、表格单元格、图注和替代文本对保留唯一 ID。源文／译文角色保持稳定，语言标签和方向应明确设置。图片路径相对于该 JSON 所在目录。

`render` 在写入前检查文档和资源，生成 `index.html`、`style.css`、`LICENSE` 以及所需图片，不修改输入。后续修改应输出到新的目录，如 `html-work/page-v2`；没有增量 `build` 或独立 `preflight` 命令。详见 [CLI 与输出约定](references/rendering.md#commands-and-output-lifecycle)。

## 原生 HTML：可信内容的手动编写

生成的网页就是可编辑的普通 HTML。无需 Python 即可从完整示例开始：

```sh
set -eu
test ! -e native-page && cp -R examples/tutorial/site native-page
```

编辑 `native-page/index.html` 和 `native-page/style.css`，然后重新打开网页。[最小原生页面与 DOM 规则](references/rendering.md#native-html-authoring)说明如何在一个 `.pair` 容器中保留带语言标签的源文和译文子元素。复用技能自有样式表、真实表格结构和双语图片描述。

这条路径需要人工审查 HTML/CSS。JSON 渲染器不会导入 HTML、检查手动修改，也不能把富文本无损转换回 JSON。请选定 JSON 或编辑后的原生页面作为创作源文件。新增标记、链接、资源和行为应单独审查；不可信 HTML 可能执行代码或访问网络。

## 翻译与排版衔接

需要从原文翻译时，先通过宿主发现单独安装的 `bilingual-translation`，按其流程完成翻译和审校。将 `TRANSLATION_SKILL` 设为核实后的安装路径。对于内容最新且已审校的 `master.jsonl`，执行：

```sh
set -eu
python3 "$TRANSLATION_SKILL/scripts/workflow.py" export master.jsonl --output reviewed.json
python3 scripts/bilingual_html.py import-pairs reviewed.json \
  --translation-skill "$TRANSLATION_SKILL" --output imported
python3 scripts/bilingual_html.py render imported/layout.json --output translated-page
```

按项目位置调整输入路径，并使用尚不存在的输出目标。第一步导出翻译交换格式，第二步转换成 HTML 自己独立的排版格式。HTML 不直接读取 JSONL。已有经过审校的交换格式 JSON 时，可从 `import-pairs` 开始。

导入时调用指定翻译技能的验证器，拒绝未完成或过期译文，保留配对字符串、ID 和顺序，输出 `layout.json`、复制的受支持图片和 `import-record.json`。保留 JSONL 主稿及交换文件作为翻译历史；排版 JSON 是渲染用的派生文件。导出会将拆分子块合回父级配对，因此 HTML 不保留子块级对齐或审校记录。[资源准备、版本／哈希固定与交接限制](references/rendering.md#optional-translation-import)详见参考文档。已有排版配对内容无需翻译依赖，也不会自动安装缺失技能。

## 配置与检查

默认设置无需额外配置即可使用。可选 `config` 支持 `browser_title`、`desktop_order` 和按需覆盖的 `styles`，例如：

```json
{"desktop_order":"target-first","styles":{"column_gap":"2rem","source_weight":1,"target_weight":1.25,"source_font":["Noto Sans","sans-serif"],"target_font":["Noto Naskh Arabic","serif"]}}
```

把此对象放入 `config`，按声明的语言调整字体。[所有字段、单位与默认值](references/rendering.md#styling)统一在参考文档说明。桌面顺序只改变 CSS 呈现，DOM 和移动端仍为先源文、后译文，断点为 48rem。字体必须已存在于浏览设备；技能不下载或打包字体。

交付前按[检查清单](references/rendering.md#review-boundaries)验收：

1. 对照提供的材料阅读两种语言，检查完整性和含义。
2. 离线打开实际网页，检查桌面和窄屏宽度、反转桌面顺序及相关 RTL/CJK 文本，查看字形、塑形、换行、长单元格、数字和浏览器缩放。
3. 用键盘聚焦并滚动宽表格；检查图片、图注和两种替代描述，并按目标读者的需要检查对比度与辅助技术表现。
4. 分别报告结构检查、语言审校和视觉／无障碍检查，包括失败及未执行项。渲染成功不代表翻译获批或无障碍认证。

## 独立安装、依赖与交付

通过宿主的技能安装流程安装完整的 `bilingual-html` 目录，保留 `SKILL.md`、脚本、资源、schema、参考文档、示例和 `LICENSE`。无需仓库源码、维护工具、`bilingual-pdf` 或 `bilingual-translation` 即可独立工作。在安装目录外运行时，使用已发现的脚本路径；安装位置只读时，在可写的项目目录中操作。

渲染和导入需要 Python 3.11+ 标准库。浏览或手动编辑已有原生文件包只需浏览器／文本编辑器及适合的本地字体。仅翻译导入额外需要明确发现的兼容翻译技能。

交付整个输出目录，保留相对路径，并按需附上可编辑 JSON／原生源文件。使用翻译路径时，项目中保留导入记录和翻译主稿。网页依赖附带 CSS 或图片时，不要只交付 `index.html`。

## 限制与安全

排版格式 接受 Unicode 纯文本和本地 PNG/JPEG 图片。HTML、Markdown 和 TeX 按字面显示；JSON 不提供富文本、公式、超链接或脚本语法。此技能不负责 OCR、翻译或提取已有网页的版式。浏览器打印样式只是基础辅助，不提供可控的 PDF 分页。

图片路径、大小和结构受限；远程 URL、目录穿越、符号链接和 SVG 输入会被拒绝。详见[资源限制](references/rendering.md#assets-and-output)与[可信 SVG 的保真栅格派生](references/rendering.md#faithful-derivatives-of-trusted-svg-originals)。文件头检查不会完整解码图片，必须查看真实浏览器输出；少量语言样例不能证明通用语言支持或无障碍合规。

[Agent 工作流程](SKILL.md)提供精简操作步骤。代码、文档和原创示例素材采用 [MIT 许可证](LICENSE)；新增资源保留其许可证，公开示例中不得包含私有材料。
