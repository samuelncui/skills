# 测试工作流

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

用这个 skill 为代码改动选择并维护有效测试、调查回归问题，或缩短缓慢的验证流程。优先沿用项目现有测试框架，按风险选择检查，同时保留必需的发布门槛。

## 如何使用

通过宿主的 skill 安装器安装 `testing-workflow`，或复制其完整目录。它不依赖 PDF skills。可以这样请求：

- “用 testing-workflow 测试这个解析器修复，保留回归测试并检查受影响的调用方。”
- “分析这套测试为什么慢，提出降低成本且不丢失关键覆盖的方案。”

提供改动或仓库、已知故障、必需检查，以及禁用服务或费用限制。预期交付是简短的验证范围、必要的可执行测试，以及区分通过、失败、跳过、受阻和未运行项目的报告。详细方法见 [agent 工作流](SKILL.md) 和[成本与性能参考](references/cost-and-performance.md)。

## 运行示例

先读[标签规范化实现](examples/tags.py)和[测试](examples/test_tags.py)。使用 Python 3.11+，无需第三方包，在已安装 skill 的目录运行：

```sh
python3 -B -m unittest discover -s examples -p 'test_tags.py' -v
```

三个测试方法涵盖正常输入、幂等性、Unicode 大小写折叠和无效输入；由 unittest 执行断言并返回失败退出状态。这些只是教学用例，不代表你的产品已通过测试；请把模式适配到项目现有框架。

自动化结果不能证明事实、语言、视觉或无障碍正确性。外部服务、付费运行、发布及明确排除的评估仍受相应授权限制。[MIT 许可证](LICENSE)。
