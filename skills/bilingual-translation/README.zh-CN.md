# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

维护一份原文优先、稳定对齐的翻译主稿。默认由当前主 agent 读完整原文、自选语义切分点、逐批保存，再对全部原译对照独立审校。独立审校指同一主 agent 内的单独审读阶段。

进度约每推进 5% 报告各阶段的实际完成数、总数和百分比，也会明确报告完成及修改后的校对进度回退。

Subagent 可能丢失上下文，造成术语、风格或细节不一致。委派前须说明风险并取得你对具体范围的明确授权；仅表示很急不构成授权。当前请求已明确批准的委派无须重复询问。

安装完整技能目录。JSONL 工具需要 Python 3.11+ 和 POSIX 文件锁，无需第三方包或联网服务。Markdown 导入器无法表达的富内容仍可使用同等支持的原生配对 TeX。

可以这样请求：“用 bilingual-translation 将这份指南译成法语，把段落和表格单元格保存在一份已审校主稿中。”提供原文、目标语言、受众和术语要求。

Agent 入口是 scripts/workflow.py：prepare 阅读并初始化原文；translate 每批分发合计不超过 2048 原文码点的单元；review 单独完整对照审校。保存／接受后直接返回下一批。原样回传工具提供的引用值。修改后只重审受影响的原译对。

[Agent 流程](SKILL.md) · [命令和边界](references/workflow.md)

已审校 JSONL 可直接交给另行发现的 bilingual-pdf。HTML 使用自己的排版 JSON 或导入语义交换格式，不直接读取 JSONL。已有配对文本无须重新翻译。

## 语义交换格式

[语义交换格式](references/semantic-exchange.md)和[完整英法示例](references/example-guide.md)说明渲染交接。下游需要语义交换 JSON 时使用 workflow.py export，JSONL 始终为主稿。下游通过 translation_contract.py 的只读 validate_document API 验证交换文档。

自动验证检查结构及审校记录是否有效；语义由 agent 审校，PDF 外观另在实际渲染页面上检查。

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
