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
.sc [损失骰]         理智检定（rd20 vs 理智）
  .sc                   默认损失 1/1d2
  .sc 1d2/1d4           成功损失1d2，失败损失1d4
  .sc 1/1d6             成功损失1，失败损失1d6
''',
}
