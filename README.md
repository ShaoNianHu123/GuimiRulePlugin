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
| `.sc [成功损/失败损]` | 理智检定（`rd20 ≤ san = 成功`） | `.sc` `.sc 1d2/1d4` |

- 属性含 **3.5 版**（8 项）和 **4.0 预览版**（9 项）两套
- 支持 50+ 技能，自动匹配关联属性
- 大成功（`rd20=1`）/ 大失败（`rd20=20`）判定
- SC 检定含半疯 / 真疯 / 失控阈值警告

---

## 📦 安装

### 前置依赖

- [OlivOS](https://github.com/OlivOS-Team/OlivOS) ≥ 0.11.x
- [OlivaDiceCore](https://github.com/OlivOS-Team/OlivaDiceCore)

### 部署步骤

**两部分独立安装，缺一不可：**

| 文件 | 安装位置 | 说明 |
|------|---------|------|
| `GuimiRulePlugin.opk` | OlivOS `plugin/` | 插件本体 |
| `gm.json` | ODC `unity/extend/template/` | 人物卡模板 |

> ⚠️ 插件与模板**互相锁定**：
> - 插件 → `requireTemplate: {name: "gm", minVersion: "1.0.0"}`
> - 模板 → `requirePlugin: {namespace: "GuimiRulePlugin", minVersion: "0.0.1"}`

### 快速上手

```
.set gm           ← 切换至诡秘规则集
.st temp gm       ← 绑定 GM 角色卡模板
.诡秘             ← 生成属性（手动填入角色卡）
.gm力量           ← 进行 D20 属性检定
.sc 1d2/1d4       ← 进行理智检定（成功损1d2/失败损1d4）
```

---

## 📂 文件结构

```
GuimiRulePlugin/
├── __init__.py
├── app.json
├── main.py              # OlivOS 事件入口
├── msgReply.py           # 消息路由与权限校验
├── msgCustom.py          # 自定义回复模板
├── msgCustomManager.py   # 注入管理器
├── config.py             # 属性/技能/关联配置
├── function.py           # 核心业务逻辑
├── utils.py              # 命令解析工具
└── gui.py

gm.json                   # 独立人物卡模板（放入 ODC extend/template/）
```
