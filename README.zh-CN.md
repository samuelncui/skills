# 文档与软件工作流 Agent 技能

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

七个技能，涵盖翻译、文档排版、学习资料、软件质量和技能改进。

## 翻译与文档

- [bilingual-translation](skills/bilingual-translation/README.zh-CN.md): 先读完整原文，按有界语义分组保存，再独立审校一份原译对照主稿。
- [bilingual-html](skills/bilingual-html/README.zh-CN.md): 将已有配对文本排为可移植的响应式 HTML，支持逻辑配对顺序、RTL、真实表格和共享图片。
- [bilingual-pdf](skills/bilingual-pdf/README.zh-CN.md): 将配对文本排版为同页双栏的双语文章、报告或阅读材料。
- [study-notes](skills/study-notes/README.zh-CN.md): 将学习来源整理为讲解型笔记、速查手册、关键词索引或决策树。
## 软件与技能质量

- [testing-workflow](skills/testing-workflow/README.zh-CN.md): 针对软件变更，设计并执行兼顾成本与风险的自动化测试和基准测试。
- [write-if-statements](skills/write-if-statements/README.zh-CN.md)：编写和审查易读的 if 语句，并在保持行为不变的前提下重构条件逻辑。
- [skill-optimization](skills/skill-optimization/README.zh-CN.md): 通过真实的全新上下文试验和针对性修正改进技能。

## 安装

使用 [Skills CLI](https://github.com/vercel-labs/skills) 或兼容的安装工具：

```sh
npx skills add samuelncui/skills --skill bilingual-translation
npx skills add samuelncui/skills --skill bilingual-html
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
npx skills add samuelncui/skills --skill write-if-statements
npx skills add samuelncui/skills --skill skill-optimization
```

按需安装完整技能目录。已有配对文本只需 bilingual-pdf 或 bilingual-html；从原文翻译需 bilingual-translation。PDF 可直接接收已审校 JSONL，HTML 使用自己的排版 JSON 或语义交换格式导入器。study-notes 依赖 bilingual-pdf。三个软件／技能质量指南本身不要求运行时，测试使用目标项目的工具链。通过宿主发现依赖，不自动安装；配置和示例见各技能指南。

## 仓库约定

各技能分别维护自身实现与文档。面向读者的指南放在技能 README，agent 工作流放在 SKILL.md。共享实现只有一个归属；依赖技能通过宿主查找已安装的依赖，不假定目录相邻。下游项目应固定经过测试的修订版本。

可复现的仓库检查及历史结果与当前结果的区别见[验证说明](tests/README.md)。精选示例保留在所属技能内。私有内容不得进入此公开仓库；外部处理与发布需取得适用授权。

原创代码与示例内容采用 [MIT 许可证](LICENSE)。依赖保留[各自的许可证](THIRD_PARTY_NOTICES.md)。
