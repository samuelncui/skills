# Bilingual HTML

把已有的双语配对文本生成为可离线浏览的便携网页。每一段的两种语言始终放在一起：桌面端并列，移动端先源文、后译文。表格、列表、共享图片和双语图注保留各自的语义结构。

需要 Python 3.11 或更新版本。渲染已有配对内容无需第三方 Python 包，也无需翻译技能。

```sh
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

在此技能目录中运行。输出目录必须尚不存在，其父目录须已存在。打开 `page/index.html`，交付时保留整个目录。

- [完整教程输入](examples/tutorial/layout.json)及[生成的网页](examples/tutorial/site/index.html)
- [格式、样式、字体、图片与检查说明](references/rendering.md)
- [渲染格式定义](schemas/layout.schema.json)
- [Agent 工作流程](SKILL.md)

第 1 版仅渲染纯文本和本地 PNG/JPEG，不解析 HTML、Markdown 或 TeX。可为两种语言分别配置字体，但须检查实际字形；字体名称并不保证覆盖所有字符。结构检查不能替代翻译、视觉或无障碍检查。

若需要从原文翻译，请通过宿主的技能发现机制查找单独安装的 `bilingual-translation`。使用明确的 `--translation-skill` 路径可导入其已复核的 v1 配对内容；不会自动安装依赖。[导入与版本固定](references/rendering.md#optional-translation-import)。

代码、文档和原创示例素材采用 [MIT 许可证](LICENSE)。
