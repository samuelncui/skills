# 双语翻译

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

把原文整理为一份可逐项审校的双语主稿。先通读所需完整原文，再逐个完整段落或语义单元翻译、核对，并保存到同一主稿后继续。稳定 ID 保持对应关系；原文修改后，相应译文须重新核对。

通过宿主的技能安装器安装整个目录。原生双语 TeX 是同等有效的入口。纯文本 JSON 和 Python 3.11+ 标准库校验器均为可选，可独立于 PDF/HTML 渲染器使用。

示例请求：“用 bilingual-translation 把这份指南译成法语，在同一份双语稿中保留每个段落和表格单元格。”请提供原文、目标语言、读者和术语要求。已有双语稿可直接交给渲染器。

参阅[工作流](SKILL.md)、[可选格式契约](references/contract-v1.md)和[完整原创英法示例](references/example-guide.md)，其中包含原文、表格和共享插图。在技能目录运行：

```sh
python3 -B scripts/translation_contract.py validate examples/guide/translation.json --ready
```

该命令检查结构、原文哈希及已记录审校状态是否仍适用；翻译准确性仍需阅读原文和译文确认。

[设计来源](references/design-provenance.md) · [MIT 许可](LICENSE)
