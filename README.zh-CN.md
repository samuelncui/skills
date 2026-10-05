# 面向双语 PDF、学习笔记与测试的 Agent 技能

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

用于制作双语文档、编写学习资料，以及兼顾成本与风险开展软件验证的技能。

- [bilingual-pdf](skills/bilingual-pdf/README.zh-CN.md): 将配对文本排版为同页双栏的双语文章、报告或阅读材料。
- [study-notes](skills/study-notes/README.zh-CN.md): 将学习来源整理为讲解型笔记、速查手册、关键词索引或决策树。
- [testing-workflow](skills/testing-workflow/README.zh-CN.md): 针对软件变更，设计并执行兼顾成本与风险的自动化测试和基准测试。
- [write-if-statements](skills/write-if-statements/README.zh-CN.md)：编写和审查易读的 if 语句，并在保持行为不变的前提下重构条件逻辑。

## 安装

使用 [Skills CLI](https://github.com/vercel-labs/skills) 或兼容的安装工具：

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
npx skills add samuelncui/skills --skill write-if-statements
```

按上述命令或宿主支持的安装方式，安装所需技能的完整目录。`study-notes` 还需要 `bilingual-pdf`；`testing-workflow` 独立使用。各技能的设置、用法与示例见上方链接的指南。

## 仓库约定

各技能分别维护自身实现与文档。面向读者的指南放在技能 README，agent 工作流放在 SKILL.md。共享实现只有一个归属；依赖技能通过宿主查找已安装的依赖，不假定目录相邻。下游项目应固定经过测试的修订版本。

可复现的仓库检查及历史结果与当前结果的区别见[验证说明](tests/README.md)。精选示例保留在所属技能内。私有内容不得进入此公开仓库；外部处理与发布需取得适用授权。

原创代码与示例内容采用 [MIT 许可证](LICENSE)。依赖保留[各自的许可证](THIRD_PARTY_NOTICES.md)。
