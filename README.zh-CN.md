# 面向双语 PDF、学习笔记与测试的 Agent 技能

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

用于制作双语文档、编写学习资料，以及兼顾成本与风险开展软件验证的技能。

- [bilingual-pdf](skills/bilingual-pdf/README.zh-CN.md)：在固定的物理左右栏中，对齐段落起点、表格行和列表项。长段落可选择跨页延续，下一组内容会重新对齐。原生 LaTeX 和 JSON 共用一个渲染器，支持 LTR、RTL 和 CJK 语言配置。
- [study-notes](skills/study-notes/README.zh-CN.md)：制作讲解型笔记、统一速查手册、关键词索引或决策树。可以只选一种，也可以组合多种形式。原生 LaTeX 记录复用已安装的双语渲染器。
- [testing-workflow](skills/testing-workflow/SKILL.md)：利用项目现有的测试框架，设计和维护自动化测试与基准测试。批量执行检查，根据风险和成本选择足够的验证证据。

[![双语使用指南](skills/bilingual-pdf/examples/en-zh-Hans/preview.png)](skills/bilingual-pdf/examples/en-zh-Hans/output.pdf)

示例以技能自身的使用方法为内容，同时展示输出效果。源文件、PDF 和预览图放在一起。面向读者的使用指南、原生 API 参考、配置文档和 JSON Schema 仍作为独立、可读的文本保留。

## 从任务开始

- 已有配对文本，要制作同页双栏的中英对照文章、报告或阅读材料？使用 `bilingual-pdf`：[最小原生 LaTeX 与构建命令](skills/bilingual-pdf/references/latex.md#project-and-build-contract)，或[最小 JSON、预检与渲染命令](skills/bilingual-pdf/references/input.md#minimal-input)。两条路径都交付可编辑源文件；先检查[字体与语言要求](skills/bilingual-pdf/references/languages.md)。
- 要把学习来源整理为讲解或便于查阅的资料？从 [study-notes](skills/study-notes/README.zh-CN.md) 开始，并显式安装其渲染依赖。
- 要为软件制定测试方案、补充回归测试或基准测试？从 [testing-workflow](skills/testing-workflow/SKILL.md) 开始。

PDF 路径只排版已提供的配对文本，不负责 OCR、从已有 PDF 提取内容、自动翻译或保留原 PDF 的页面版式。

## 安装

使用 [Skills CLI](https://github.com/vercel-labs/skills) 或兼容的安装工具：

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
```

普通的双语对照文档只需安装 `bilingual-pdf`。`study-notes` 依赖它。也可以将所需技能的完整目录复制到宿主支持的位置。 `testing-workflow` 独立使用，不依赖这两个 PDF 技能。

通过宿主查找 `bilingual-pdf` 的实际安装目录，构建学习文档时将其作为 `BILINGUAL_PDF_SKILL` 传入。这些技能不假定安装目录相邻，也不会自动下载依赖。TeX、字体和可选的 Python 质量检查依赖见各技能指南。

## 单一实现，明确分工

`bilingual-pdf` 负责 `paralleltext.sty`、结构化输入、版式和渲染检查。`study-notes` 添加轻量的原生记录与导航层，以及学习资料编写流程，不携带第二套渲染器。下游文档项目应固定经过测试的修订版本，并将自身内容和配置分开管理。

调用技能的 agent 提供内容及语义对应关系，排版工具负责其呈现位置。原生 TeX 可以执行代码；禁用 shell escape 并不等于文件系统沙箱。发布、外部处理和源材料使用权分别需要相应授权。

可复现测试及历史结果与当前结果的区别见[验证说明](tests/README.md)。精选示例 PDF 与源文件一同纳入版本控制；Actions 用于检查仓库，不作为示例交付渠道。

原创代码与示例内容采用 [MIT 许可证](LICENSE)。依赖保留[各自的许可证](THIRD_PARTY_NOTICES.md)。本项目不声称已获得适用于所有语言、打印机或无障碍场景的认证。
