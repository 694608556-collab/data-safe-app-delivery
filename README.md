# 保护数据的跨端应用交付

**data-safe-app-delivery · v1.0.0**

一份从真实 Windows、Android 和 iOS 应用开发经历中提炼的 Agent Skill。用于接续已有项目、处理导入/搜索/导出与性能问题，以及完成保留数据的构建、验证和安装交付。

## 下载与使用

- [下载完整技能包 1.0.0](releases/data-safe-app-delivery-1.0.0.zip)
- [技能正文](SKILL.md)
- [验证说明](VERIFICATION.md)
- [案例及方法来源](references/casebook-and-provenance.md)

将技能包解压到当前 AI 工具支持的 skills 目录，保留 `data-safe-app-delivery/SKILL.md` 这一结构。在支持本地技能的 Codex 环境中，可显式调用：

```text
请使用 $data-safe-app-delivery 接续这个应用。
先保护已有工作与正式数据，再完成本次修复、验证和交付。
```

也可以只指定一个阶段，例如：

```text
请使用 $data-safe-app-delivery 排查 Android 表格导入慢的问题，
先区分界面反馈与完整预览耗时，保持完整内容和原有校验。
```

不同宿主的安装目录、调用方式和工具能力可能不同；技能中的流程可以迁移，平台命令和验证条件需要按实际环境核对。该技能不要求额外的 MCP 服务；文件摘要脚本使用 Python 3.9+ 标准库。

## 适合哪些任务

- 接手存在未提交、暂存、未跟踪和有意删除内容的应用项目。
- 将桌面已有功能移植到 Android/iOS，明确共享业务和平台边界。
- 处理完整正文、表格、备份、搜索、PDF与其他导出的正确性和性能问题。
- 核对首次与后续性能、原生实现和不同处理器架构的验证结果。
- 关联源码、测试与实际安装包，执行保留数据的更新和明确范围的清理。

普通技术问答、文案总结或不涉及交付的小改动，不需要套用完整流程。用户当前指令优先；技能不增加删除、上传、安装或发布权限。

## 文件结构

```text
SKILL.md                           技能入口，按任务选择参考资料
agents/openai.yaml                Codex界面信息
references/
  intake-and-continuation.md       接手、保护、范围与接续
  integrity-and-storage.md         完整内容、原子保存与差分验证
  performance.md                  耗时定位、流水线与冷首测
  platforms.md                    Windows/Android/iOS差异
  verification-and-delivery.md    验证、制品身份与交付
  casebook-and-provenance.md       历史案例、提取依据和社区参考
assets/handoff-template.md        接续模板
scripts/artifact_manifest.py      只读文件大小与SHA-256
evals/                            脱敏场景、评分标准与脚本测试
```

## 怎样提炼出来

本技能取材于 COC 跑团记录簿的代表性开发记录、桌面更新与提交历史、移动端交接和性能文档，以及部分已保存的历史回顾。没有重新逐条扫描全部原始会话。

提取时保留问题触发条件、有效处理、验证依据和适用边界；版本、设备、具体耗时与窗口大小作为案例，不变成其他产品的默认要求。个人偏好、项目契约与工具事实分别处理。

方法参考包括社区的 [Claudeception](https://github.com/lycfyi/Claudeception)、[ECC](https://github.com/affaan-m/ECC)、[noodle ruminate](https://github.com/poteto/noodle/blob/main/.agents/skills/ruminate/SKILL.md) 和 [retro-skill](https://github.com/netresearch/retro-skill)。技能说明为自行组织的中文内容，没有复制这些项目的源码，也不自动安装其后台监听或配置。

## 验证与边界

1. 技能结构、UTF-8、内部引用、YAML/JSON与Python语法检查通过。
2. 文件摘要脚本9项测试通过，无跳过。
3. 8个脱敏场景经过独立会话执行、人工按评分标准核对；首轮发现的架构验证遗漏补强后，由新的独立会话复测。
4. 技能ZIP完成CRC及逐文件字节核对。

这些场景验证了方案、诊断和交付判断，没有操作真实应用或设备；未做无技能基线或统计效率比较。详细限制见 [VERIFICATION.md](VERIFICATION.md)。

运行摘要脚本测试：

```text
python -B evals/test_artifact_manifest.py
```

只读生成指定文件的摘要：

```text
python scripts/artifact_manifest.py -- package.apk package.ipa
```

文件摘要只证明文件身份，不证明签名有效、测试通过或实机性能。输出可能包含私人绝对路径，公开前需要脱敏。

## 数据保护

仓库不包含私人正文、真实输入、原始会话/日志、数据库、设备序列号或签名材料。示例输入为脱敏场景。技能不会自动读取全部历史或把用户材料上传到外部服务。

后续更新应依据新的实际失败或有效案例，优先窄修正已有规则，避免不断累积全局规定。
