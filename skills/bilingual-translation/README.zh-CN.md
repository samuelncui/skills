# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

维护一份原文优先、稳定对齐的翻译主稿。默认由当前主 agent 读完整原文、自选语义切分点、逐批保存，再对全部原译对照独立审校。独立审校指同一主 agent 内的单独审读阶段。

进度约每推进 5% 报告各阶段的实际完成数、总数和百分比，也会明确报告完成及修改后的校对进度回退。

Subagent 可能丢失上下文，造成术语、风格或细节不一致。委派前须说明风险并取得你对具体范围的明确授权；仅表示很急不构成授权。当前请求已明确批准的委派无须重复询问。

安装完整技能目录。JSONL 工具需要 Python 3.11+ 和 POSIX 文件锁，无需第三方包或联网服务。Markdown 导入器无法表达的富内容仍可使用同等支持的原生配对 TeX。

可以这样请求：“用 bilingual-translation 将这份指南译成法语，把段落和表格单元格保存在一份已审校主稿中。”提供原文、目标语言、受众和术语要求。

Agent 入口是 scripts/workflow.py。准备阶段按完整单元返回至少 8192 个原文码点，尾批可少；超过 2048 的单元须在当前批次拆分完再继续。翻译和审校每批均不超过 2048 个原文码点，审校不计译文长度。保存与获取下一批是独立动作。可逐条运行命令，也可通过 run 接收 stdin JSONL，每行一个动作、各自携带引用值；批次最多包含一个正文读取动作，且必须放在最后。原样回传工具提供的引用值。切分时由 agent 选原文相邻锚点，工具负责定位和长度校验，无须手算偏移。

修正使用精确 old/new 补丁，读完修改后的对照，再另行接受。局部问题局部复核，多处或全局问题重新完整审校；未解决问题用 todo 跟踪。导出须通过当前完整复核和待办解决门禁，不提供草稿绕过。

[Agent 流程](SKILL.md) · [命令和边界](references/workflow.md)

已审校 JSONL 可直接交给另行发现的 bilingual-pdf。HTML 使用自己的排版 JSON 或导入语义交换格式，不直接读取 JSONL。已有配对文本无须重新翻译。

## 语义交换格式

[语义交换格式](references/semantic-exchange.md)和[完整英法示例](references/example-guide.md)说明渲染交接。下游需要语义交换 JSON 时使用 workflow.py export，JSONL 始终为主稿。下游通过 translation_contract.py 的只读 validate_document API 验证交换文档。

自动验证检查结构及审校记录是否有效；语义由 agent 审校，PDF 外观另在实际渲染页面上检查。

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
