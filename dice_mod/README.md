# 诡秘之主 D20 规则 —— Dice! 移植版

> 原 [OlivOS GuimiRulePlugin v0.1.0](../GuimiRulePlugin/) 的 **Dice! Lua 移植版**。
> 适用于 [Dice!](https://github.com/Dice-Developer-Team/DiceV2) ≥ 2.6.4(build612)。

**作者**: 少年狐 (ShaoNianHu123)  
**GitHub**: [https://github.com/ShaoNianHu123](https://github.com/ShaoNianHu123)  
**QQ**: 1690676242

---

## 功能对照

| 原指令（OlivOS） | Dice! 指令 | 说明 |
|---|---|---|
| `.诡秘 [数量]` | `.诡秘 [数量]` | 属性生成 (2d3, 2~6) |
| `.诡秘4.0 [数量]` | `.诡秘4.0 [数量]` | 4.0 预览属性表 |
| `.gm <目标>` | `.gm <目标>` | D20 技能/属性检定 |
| `.gmb <目标>` | `.gmb <目标>` | 奖励投（取高） |
| `.gmp <目标>` | `.gmp <目标>` | 惩罚投（取低） |
| `.gm 优势 <目标>` | `.gm 优势 <目标>` | 奖励投（中文） |
| `.gm 劣势 <目标>` | `.gm 劣势 <目标>` | 惩罚投（中文） |
| `.gmsc [损失骰]` | `.gmsc [损失骰]` | 理智检定 |
| `.gmri` | `.gmri` | 先攻检定 |
| `.gm 刷新/更新` | `.gm 刷新/更新` | 衍生属性刷新 |
| `.gm help` | `.gm help` | 帮助 |

**支持特性：**
- 手动加值 `.gm力量+2` / 绝对指定 `.gm力量5`
- 改判属性 `.gm驯兽/教育`
- 无限累加 `.gm格斗+2+3+4`
- 50+ 技能自动匹配关联属性
- 大成功 (rd20=20) / 大失败 (rd20=1)
- SC 半疯/真疯/失控阈值警告
- 序列 & 消化度系统（`.gm 刷新` 自动计算生命/灵性/理智）

---

## 安装

> ⚠️ **与 OlivOS 版完全独立**，两者可并存，互不影响。

### 方式一：手动安装

1. 将 `guimi_rule.json` 和 `guimi_rule/` 文件夹放入 Dice! 的 **`mod/`** 目录
2. 启动 Dice! 或执行 `.system load`

```
[DiceData]
  └── mod/
       ├── guimi_rule.json
       └── guimi_rule/
            ├── reply/
            │    └── guimi_main.lua
            └── script/
                 └── guimi_main.lua
```

### 方式二：WebUI 安装

1. 将整个 `dice_mod/` 打包为 zip（确保 json 和文件夹在 zip 根层）
2. WebUI → 模块管理 → 远程资源 → 手动安装

---

## 数据录入

Dice! 原生支持 `.st` 录入角色卡（和 ODC 一样），无需额外指令：

```
.pc new 克莱恩          ← 1. 新建角色卡
.pc tag 克莱恩           ← 2. 绑定到本群
.st 力量 5               ← 3. 录入属性
.st 格斗 2               ← 4. 录入技能等级（0~6）
.st 序列 9
.st 消化 12
.gm 格斗                 ← 5. 开始检定！
```

> `.st` 数据自动存入 Dice! 角色卡，`.gm` 通过 `getPlayerCardAttr` 直接读取。

---

## 文件结构

```
dice_mod/
├── README.md
├── guimi_rule.json           # Mod 元数据
└── guimi_rule/
    ├── reply/
    │   └── guimi_main.lua    # 关键词路由注册
    └── script/
        └── guimi_main.lua    # 核心逻辑
```

与 OlivOS 原版文件在同一项目根目录，互不冲突：

```
诡秘规则插件 琉璃版/
├── GuimiRulePlugin/          ← OlivOS 插件 (不动)
├── gm.json                   ← ODC 模板 (不动)
└── dice_mod/                 ← Dice! 移植版 (新增)
```

---

## 与原 OlivOS 版的差异

| 方面 | OlivOS 版 | Dice! 版 |
|------|----------|---------|
| 语言 | Python | Lua |
| 人物卡 | ODC pcCard 系统 | Dice! 原生角色卡 (getPlayerCardAttr) |
| 模板 | gm.json mapping 自动计算 | 手动 `.gm 刷新` 触发 |
| 回复模板 | msgCustom 注入 | 内联文本 |
| 群开关 | ODC 群/频道权限检测 | 依赖 Dice! 自身的权限系统 |
| 先攻列表 | ODC groupInitList | 群配置简易存储；也可用 Dice! 原生 `.ri` |
