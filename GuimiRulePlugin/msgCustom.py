# -*- encoding: utf-8 -*-
"""
诡秘规则插件——自定义回复与帮助文档模块。

通过 OlivaDiceCore 的 msgCustom 机制注入自定义回复模板和帮助文档。
"""

import OlivOS
import OlivaDiceCore
import GuimiRulePlugin

dictStrCustomDict = {}

dictStrCustom = {
    'strGMAttrCheck': '【诡秘之主D20规则】属性检定结果',
    'strGMSkillCheck': '【诡秘之主D20规则】技能检定结果',
    'strGMSCResult': '【诡秘之主D20规则】理智检定结果',
}

dictStrConst = {
}

dictGValue = {
}

dictTValue = {
}

dictStrCustomNote = {
    'strGMAttrCheck': '【属性检定】.gm<属性名>\n示例：.gm力量 → rd20+力量值',
    'strGMSkillCheck': '【技能检定】.gm<技能名>\n示例：.gm格斗 → rd20+力量+格斗技能值',
    'strGMSCResult': '【理智检定】.sc [成功损失/失败损失]\n示例：.sc 1d2/1d4 → 理智检定',
}

dictHelpDocTemp = {
    '诡秘规则帮助': '''【诡秘之主D20规则 - 帮助】
.诡秘 [数量]         随机生成人物属性（2d3，2~6）
.诡秘4.0 [数量]      使用4.0预览属性表生成
.gm<技能/属性>       D20技能或属性检定
  支持手动加值：.gm力量+2（叠加）/ .gm力量5（指定）
.gmsc [损失骰]        理智检定（rd20 vs 理智）
  .gmsc                 默认损失 1/1d2
  .gmsc 1d2/1d4         成功损失1d2，失败损失1d4
  .gmsc 1/1d6           成功损失1，失败损失1d6

—— OlivaDiceCore 配套指令 ——
.set temp gm            切换本群/频道诡秘房规
.st temp gm             切换GM人物卡模板
.st rule gm             切换GM人物卡规则

—— 人物卡录入（ODC内置）——
.st <卡名>-<技能><值>...   建卡批量录入
.st <技能><值>...          当前卡批量录入
.st rm <技能>              删除技能
.st blockrm <块名>         删除技能块

例：.st 克莱恩-力量5体质4敏捷3灵感6意志5教育4幸运3
    .st 格斗2 手枪1 闪避1 侦查1 神秘学2
''',
}
