# 诡秘之主D20跑团规则插件 (GuimiRulePlugin)
> **⚠️ 声明**：本插件由 **AI 辅助编程** 完成，使用 [olivos-plugin-developer](https://github.com/Desom-fu/OlivOS-Plugin-Skill) skill 开发，用于 **OlivOS** 框架。  
> AI 不保证代码零缺陷，使用前请自行测试。

---

## 🎲 功能

| 指令 | 说明 | 示例 |
|------|------|------|
| `.诡秘 [数量]` | 随机生成人物属性（2d3，范围 2~6） | `.诡秘` `.诡秘5` |
| `.诡秘4.0 [数量]` | 使用 4.0 预览属性表生成 | `.诡秘4.0` |
| `.gm <技能/属性>` | D20 技能/属性检定（`rd20 + 属性 + 技能加值`） | `.gm力量` `.gm格斗` `.gm手枪` |
| `.gmsc [成功损/失败损]` | 理智检定（`rd20 ≤ san = 成功`） | `.gmsc` `.gmsc 1d2/1d4` |

- 属性含 **3.5 版**（8 项）和 **4.0 预览版**（9 项）两套
- 支持 50+ 技能，自动匹配关联属性
- 大成功（`rd20=20`）/ 大失败（`rd20=1`）判定
- SC 检定含半疯 / 真疯 / 失控阈值警告

## 📦 安装

### 前置依赖

- [OlivOS](https://github.com/OlivOS-Team/OlivOS) ≥ 0.11.x
- [OlivaDiceCore](https://github.com/OlivOS-Team/OlivaDiceCore)

### 部署步骤

**两部分独立安装，缺一不可：**

| 文件 | 安装方式 | 说明 |
|------|---------|------|
| `OlivOS_GuimiRulePlugin.zip` | 解压到 OlivOS `plugin/` | 插件本体 |
| `OlivOS_gm.zip` | 解压到 ODC `unity/extend/template/` | 人物卡模板 |

### 快速上手

```
.set temp gm            ← 切换群/频道诡秘房规
.st temp gm             ← 切换 GM 人物卡模板
.st rule gm             ← 切换 GM 人物卡规则
.诡秘                   ← 生成属性
.gm力量                 ← D20 属性检定
.gmsc 1d2/1d4           ← 理智检定
```
