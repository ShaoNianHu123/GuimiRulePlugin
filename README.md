# 诡秘之主D20跑团规则插件 (GuimiRulePlugin)

> **作者**：少年狐　|　[GitHub](https://github.com/ShaoNianHu123/GuimiRulePlugin)　|　QQ：1690676242  
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

---

## 📋 更新日志

### v0.1.0
- ✨ 序列与消化度系统：`.st 序列9` `.st 消化12` 录入，`.gm 刷新`/`.gm 更新` 自动计算生命/灵性/理智
- ✨ 衍生属性自动计算（生命=10+体质+序列加成+消化÷5，灵性=意志+灵感+序列加成+消化÷5，理智=10+意志）
- ✨ `.gmri` 先攻检定（rd20+卡片敏捷，注册到ODC先攻列表）
- ✨ `.sn` 模板优化（显示名称+hp+敏捷+mp+san）
- 🔧 `.gm` 不带参数默认生成1套属性
- 🔧 自动刷新序列/消化变更时触发更新
- 🔧 消化度参与 mapping 计算

### v0.0.2
- 🔧 技能等级改为 0-based（0=未受训, 1=受训, 2=熟练, 3=进阶, 4=精通, 5=博学, 6=大师）
- 🔧 属性/技能硬区分：仅 8 属性走属性检定，其余一律技能
- 🔧 大成功/大失败调换：20=大成功，1=大失败
- 🔧 理智检定改为 `.gmsc`，避免与 COC 的 `.sc` 冲突
- 🔧 修正全体技能关联属性（投掷→力量、贸易→灵感、神秘学→灵感等 7 处）
- 🔧 补充 20+ 缺失技能（占卜/通灵/仪式魔法/攀爬/游泳等）
- 🔧 模板默认值：闪避+8母语→受训，其余→未受训
- ✨ 属性改判：`.gm驯兽/教育`（用教育代替魅力）
- ✨ 奖励投/惩罚投：`.gmb力量` `.gm 优势 力量` / `.gmp力量` `.gm 劣势 力量`
- ✨ 无限累加附加值：`.gm格斗+2+3+4` → 全部求和
- ✨ `.gm help` / `.诡秘 help` 帮助指令

### v0.0.1
- 初始版本：属性生成、D20检定、理智检定

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
.set temp gm            ← 切换群/频道诡秘房规
.st temp gm             ← 切换 GM 人物卡模板
.st rule gm             ← 切换 GM 人物卡规则
.诡秘                   ← 生成属性
.gm力量                 ← D20 属性检定
.gmsc 1d2/1d4           ← 理智检定
```

### 📝 人物卡录入（OlivaDiceCore 内置指令）

```
.st <卡名>-<技能名><值><技能名><值>...    建卡并批量录入
.st <技能名><值><技能名><值>...           当前卡批量录入
.st &<武器名>=<表达式>                    自定义武器录入
.st rm <技能名>                          删除技能
.st rm <技能名1><技能名2>...              删除多个技能
.st blockrm <技能块>                      删除技能块
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
