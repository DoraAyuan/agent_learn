[Root Directory](../CLAUDE.md) > **skills/**

# skills 模块

## Module Responsibilities

`skills/` 目录存放所有技能定义文件，以 Markdown 格式描述每个技能的标准操作流程（SOP）。这些文件由 `app/skill_loader.py` 自动扫描和解析，无需手动注册。

## Skill 文件规范

每个 `.md` 文件必须包含以下结构：

```markdown
# Skill: <技能名称>

## Purpose
技能用途描述

## When to use
触发条件

## Input
需要的输入信息

## Steps
执行步骤

## Output Format
输出格式要求

## Constraints
约束条件
```

## 当前技能列表

| 文件名 | 技能名称 | 用途 |
|--------|---------|------|
| `paper_summary.md` | paper_summary | 总结论文/综述，提取核心信息 |
| `code_debug.md` | code_debug | 分析代码报错，定位问题并给出修复建议 |
| `study_plan.md` | study_plan | 根据用户目标和基础制定学习计划 |
| `test.md` | test | 测试用技能（内容极简） |

## 扩展方式

直接在本目录下新建 `.md` 文件，遵循上述规范即可。`skill_loader.py` 会自动发现并加载新文件，无需修改任何代码。

## Related File List

| 文件 | 说明 |
|------|------|
| `paper_summary.md` | 论文总结技能 |
| `code_debug.md` | 代码调试技能 |
| `study_plan.md` | 学习计划技能 |
| `test.md` | 测试技能（内容简洁，用于验证加载器） |

## Change Log

| 日期 | 变更内容 |
|------|---------|
| 2026-05-14 | 增量扫描确认：技能文件内容无变更，文档保持同步 |
| 2026-05-05 | 初始化模块 AI 上下文文档 |
