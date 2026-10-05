# if 语句如何写

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

这个 skill 用于编写新的条件逻辑、审查分支密集的函数，或在保持行为不变的前提下简化代码。目标是让判断容易理解，而不是减少 `if` 的数量。

## 安装与使用

通过 Skills CLI 或宿主支持的兼容安装方式安装：

```sh
npx skills add samuelncui/skills --skill write-if-statements
```

保留完整的 skill 目录，包括许可证、参考资料和示例。阅读指导不依赖其他 skill，也不需要安装 Python；只有运行附带示例时才需要 Python 3。

请编程助手使用 `$write-if-statements`，或在宿主中选择该 skill。提供相关代码、调用方、预期行为和可用的测试命令。例如：

- “为这个客户端编写重试判断：只在错误是暂时性的且还有剩余次数时重试。保持简单，并测试边界。”
- “审查这个路由函数，说明查找表能否保留首次匹配优先级和短路行为。先不要修改。”
- “降低这个嵌套处理函数的缩进层次，不改变返回值、异常或资源清理。补充回归测试并运行相关测试。”

你应得到范围明确的审查或补丁、结构选择的理由，以及测试结果和未验证的边界。清楚的简单分支可以保留；疑似 bug 应与保持行为的重构区分开。

## 运行示例

结合阅读[实现](examples/conditionals.py)与[测试](examples/test_conditionals.py)。在这个 skill 目录内运行：

```sh
python3 -B -m unittest discover -s examples -p 'test_conditionals.py' -v
```

七个测试方法覆盖卫语句的结果与清理、异常传播、有重叠条件的顺序规则、被跳过的判断、分派时仅执行选中的处理函数，以及值得保留的简单合取条件。只使用标准库；测试验证的是教学示例，不是你的应用程序。

## 边界与延伸阅读

有顺序的条件链不一定能等价替换为字典。移动判断位置可能改变执行时机、异常发生时机，以及读取到的状态。相关取舍见[语义陷阱与一手参考资料](references/semantic-traps.md)；面向 agent 的流程见 [SKILL.md](SKILL.md)。

独立编写的资料和示例使用附带的 [MIT 许可证](LICENSE)。外部链接内容保留其自身权利。
