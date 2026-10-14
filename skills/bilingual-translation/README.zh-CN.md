# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

维护一份原文优先、稳定对齐的翻译主稿。Agent 先读完整原文，自选语义切分点，逐批保存，再独立通读所有已保存的原译对照内容并审校。

安装完整技能目录。JSONL 工具需要 Python 3.11+ 和 POSIX 文件锁，无需第三方包或联网服务。Markdown 导入器无法表达的富内容仍可使用同等支持的原生配对 TeX。

可以这样请求：“用 bilingual-translation 将这份指南译成法语，把段落和表格单元格保存在一份已审校主稿中。”提供原文、目标语言、受众和术语要求。

Agent 入口是 scripts/workflow.py：prepare 阅读并初始化原文；translate 每批分发合计不超过 2048 原文码点的单元；review 独立完整对照审校。保存／接受后直接返回下一批，用短引用代替手抄哈希；版本、哈希和重试校验仍由工具执行。修改后只重审受影响的原译对。

[Agent 流程](SKILL.md) · [命令和边界](references/workflow-v2.md)

已审校 JSONL 可直接交给另行发现的 bilingual-pdf。HTML 使用自己的排版 JSON 或旧版 v1 导入，不直接读取 JSONL。已有配对文本无须重新翻译。

## 旧版 v1 兼容

保留原有 [v1 协议](references/contract-v1.md)、[完整英法示例](references/example-guide.md)和 translation_contract.py API，它们与受门禁保护的 JSONL 流程分开。仅在下游需要 v1 JSON 时使用 workflow.py export，JSONL 始终为主稿。

自动验证检查结构及审校记录是否有效；语义由 agent 审校，PDF 外观另在实际渲染页面上检查。

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
