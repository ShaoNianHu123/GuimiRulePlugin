# -*- encoding: utf-8 -*-
"""
诡秘规则插件——自定义回复与帮助文档模块。

通过 OlivaDiceCore 的 msgCustom 机制注入自定义回复模板和帮助文档。
所有回复模板使用 {变量} 占位符，运行时替换为实际值。
"""

import OlivOS
import OlivaDiceCore
import GuimiRulePlugin

dictStrCustomDict = {}

# ==================== 自定义回复模板（默认值） ====================
# 键名约定：strGM + 功能组 + 描述
# 变量约定：{nick}=昵称 {target}=目标 {d20}=骰值 {total}=总值
#          {san}=理智 {dex}=敏捷 {seq}=序列 {digest}=消化度
# 用户可通过 OlivOS GUI 编辑这些模板

dictStrCustom = {
    # ---- 属性生成 ----
    'strGMAttrTitle': '<{nick}>命运的馈赠在暗处已标注好了价码：',
    'strGMAttrV4Note': '（4.0属性为测试内容，非最终版本）',

    # ---- D20 检定 ----
    'strGMD20CheckTitle': '<{nick}>对【{target}】进行检定：{tag}',
    'strGMD20CheckLine': 'rd20({d20}) + {attr_display}{skill_info}',
    'strGMD20Result': '= {total}',
    'strGMD20CritSuccess': '『大成功！』命运的眷顾降临于你。',
    'strGMD20CritFail': '『大失败！』命运对你露出了恶意的微笑。',
    'strGMD20TagManual': '【手动】',
    'strGMD20TagAdv': '【奖励投】{d1}/{d2}→取高→{d20}',
    'strGMD20TagDis': '【惩罚投】{d1}/{d2}→取低→{d20}',

    # ---- SC 理智检定 ----
    'strGMSCSTitle': '<{nick}>进行理智检定：',
    'strGMSCCheckLine': 'rd20({d20}) vs 理智({san})',
    'strGMSCSSuccess': '{d20} ≤ {san}，【理智检定成功】',
    'strGMSCSFail': '{d20} > {san}，【理智检定失败】',
    'strGMSCSLossLine': '损失理智: {expr} = {loss}',
    'strGMSCSChangeLine': '理智变化: {old} → {new}',
    'strGMSCSHalfMad': '⚠ 你已陷入【半疯】状态，获得随机疯狂倾向。',
    'strGMSCSTrueMad': '⚠⚠ 你已陷入【真疯】状态，难以沟通。',
    'strGMSCSLost': '☠ 理智归零，你已【失控】！',

    # ---- 序列/消化刷新 ----
    'strGMRefreshSuccess': '<{nick}> {seq_info}  消化{digest}（+{digest_bonus}）\n血量上限→{hp}  灵性→{mp}  理智→{san}  已更新',
    'strGMRefreshSeqInfo': '序列{seq}（{mult}倍）',
    'strGMRefreshNoSeq': '无序列',

    # ---- 先攻检定 ----
    'strGMRiCheck': '<{nick}>先攻检定：rd20({d20}) + 敏捷({dex}) = {total}  已加入先攻列表',

    # ---- 错误提示 ----
    'strGMErrNoCard': '尚未找到你的角色卡。请先用 .st temp gm 绑定GM模板，再创建角色。',
    'strGMErrParam': '参数错误',
    'strGMErrTooMany': '"你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"',
    'strGMErrNoTarget': '请指定技能或属性名称，如 .gm力量 或 .gm格斗',
    'strGMErrNoTargetAdv': '请指定技能或属性名称，如 .gmb力量',
    'strGMErrCheckFail': '检定失败: {error}',
    'strGMErrSCFail': '理智检定失败: {error}',
    'strGMErrRefreshFail': '更新失败: {error}',
}

# ---- 帮助文档 ----
dictHelpDocTemp = {
    '诡秘规则帮助': '''【诡秘之主D20规则 - 帮助】
.诡秘 [数量]         随机生成人物属性（2d3，2~6）
.诡秘4.0 [数量]      使用4.0预览属性表生成
.gm<技能/属性>       D20技能或属性检定
  手动加值：.gm力量+2 / .gm力量5
  改判属性：.gm驯兽/教育
  奖励投：.gmb力量 / .gm 优势 力量
  惩罚投：.gmp力量 / .gm 劣势 力量
.gmsc [损失骰]        理智检定（rd20 vs 理智）
  .gmsc                 默认损失 1/1d2
  .gmsc 1d2/1d4         成功损失1d2，失败损失1d4
  .gmsc 1/1d6           成功损失1，失败损失1d6
.gm 刷新/.gm 更新    根据序列/消化自动计算更新生命灵性理智
.gmri                先攻检定（rd20 + 卡片敏捷）

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

# ---- GUI 中显示的说明（供 OlivaDiceNativeGUI 使用） ----
# 格式：第一行=功能描述，第二行=所属指令+变量列表，第三行=效果示例
dictStrCustomNote = {
    # ===== 属性生成 (.诡秘) =====
    'strGMAttrTitle': '【.诡秘】属性生成时的开场标题\n变量：{nick}=发送者昵称\n示例：<克莱恩>命运的馈赠在暗处已标注好了价码：',
    'strGMAttrV4Note': '【.诡秘4.0】属性表末尾的版本提示\n无变量\n示例：（4.0属性为测试内容，非最终版本）',

    # ===== D20检定 (.gm / .gmb / .gmp) =====
    'strGMD20CheckTitle': '【.gm】检定结果第一行标题\n变量：{nick}=昵称 {target}=检定目标 {tag}=标签（手动/奖励投/惩罚投）\n示例：<克莱恩>对【力量】进行检定：【手动】',
    'strGMD20CheckLine': '【.gm】检定算式行\n变量：{d20}=骰值 {attr_display}=关联属性及数值 {skill_info}=技能信息\n示例：rd20(15) + 力量(5) + 技能格斗(受训:+0)',
    'strGMD20Result': '【.gm】检定结果行（大成功/大失败会在此行后追加显示）\n变量：{total}=最终总值\n示例：= 20  或自定义：这既是命定的结果 = {total}',
    'strGMD20CritSuccess': '【.gm】骰出20时的大成功文本（结果行之后追加）\n变量：{total}=最终总值\n示例：『大成功！』命运的眷顾降临于你。',
    'strGMD20CritFail': '【.gm】骰出1时的大失败文本（结果行之后追加）\n变量：{total}=最终总值\n示例：『大失败！』命运对你露出了恶意的微笑。',
    'strGMD20TagManual': '【.gm+数字】手动指定加值时出现在标题后的标签\n无变量\n示例：【手动】',
    'strGMD20TagAdv': '【.gmb / .gm优势】奖励投标签\n变量：{d1}=第一骰 {d2}=第二骰 {d20}=最终取值\n示例：【奖励投】18/7→取高→18',
    'strGMD20TagDis': '【.gmp / .gm劣势】惩罚投标签\n变量：{d1}=第一骰 {d2}=第二骰 {d20}=最终取值\n示例：【惩罚投】3/15→取低→3',

    # ===== 理智检定 (.gmsc) =====
    'strGMSCSTitle': '【.gmsc】理智检定结果第一行\n变量：{nick}=发送者昵称\n示例：<克莱恩>进行理智检定：',
    'strGMSCCheckLine': '【.gmsc】检定骰值与理智对比行\n变量：{d20}=骰值 {san}=当前理智值\n示例：rd20(12) vs 理智(15)',
    'strGMSCSSuccess': '【.gmsc】检定成功提示行（rd20≤理智）\n变量：{d20}=骰值 {san}=当前理智值\n示例：12 ≤ 15，【理智检定成功】',
    'strGMSCSFail': '【.gmsc】检定失败提示行（rd20>理智）\n变量：{d20}=骰值 {san}=当前理智值\n示例：18 > 15，【理智检定失败】',
    'strGMSCSLossLine': '【.gmsc】理智损失详情行\n变量：{expr}=损失表达式 {loss}=实际损失值\n示例：损失理智: 1d2 = 2',
    'strGMSCSChangeLine': '【.gmsc】理智变化汇总行\n变量：{old}=变化前 {new}=变化后\n示例：理智变化: 15 → 13',
    'strGMSCSHalfMad': '【.gmsc】理智降至8及以下时的半疯警告\n无变量\n示例：⚠ 你已陷入【半疯】状态，获得随机疯狂倾向。',
    'strGMSCSTrueMad': '【.gmsc】理智降至2及以下时的真疯警告\n无变量\n示例：⚠⚠ 你已陷入【真疯】状态，难以沟通。',
    'strGMSCSLost': '【.gmsc】理智降至0时的失控警告\n无变量\n示例：☠ 理智归零，你已【失控】！',

    # ===== 序列/消化刷新 (.gm 刷新) =====
    'strGMRefreshSuccess': '【.gm 刷新】刷新成功摘要（单行输出）\n变量：{nick}=昵称 {seq_info}=序列信息 {digest}=消化度 {digest_bonus}=消化加成 {hp}=生命 {mp}=灵性 {san}=理智\n示例：<克莱恩> 序列9（1倍） 消化15（+3）\n血量上限→18 灵性→14 理智→15 已更新',
    'strGMRefreshSeqInfo': '【.gm 刷新】有序列时的序列描述片段\n变量：{seq}=序列等级 {mult}=加成倍率\n示例：序列9（1倍）',
    'strGMRefreshNoSeq': '【.gm 刷新】未录入序列时的提示片段\n无变量\n示例：无序列',

    # ===== 先攻检定 (.gmri) =====
    'strGMRiCheck': '【.gmri】先攻检定结果（单行输出）\n变量：{nick}=昵称 {d20}=骰值 {dex}=敏捷值 {total}=总先攻值\n示例：<克莱恩>先攻检定：rd20(12) + 敏捷(4) = 16 已加入先攻列表',

    # ===== 错误提示 =====
    'strGMErrNoCard': '【错误】用户未绑定角色卡时的提示\n无变量\n示例：尚未找到你的角色卡。请先用 .st temp gm 绑定GM模板，再创建角色。',
    'strGMErrParam': '【错误】参数不合法时的通用提示\n无变量\n示例：参数错误',
    'strGMErrTooMany': '【错误】.诡秘生成数量超过上限时的提示\n无变量\n示例："你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"',
    'strGMErrNoTarget': '【错误】.gm 未指定目标时的提示\n无变量\n示例：请指定技能或属性名称，如 .gm力量 或 .gm格斗',
    'strGMErrNoTargetAdv': '【错误】.gmb/.gmp 未指定目标时的提示\n无变量\n示例：请指定技能或属性名称，如 .gmb力量',
    'strGMErrCheckFail': '【错误】.gm 检定发生异常时的提示\n变量：{error}=异常信息\n示例：检定失败: division by zero',
    'strGMErrSCFail': '【错误】.gmsc 检定发生异常时的提示\n变量：{error}=异常信息\n示例：理智检定失败: KeyError',
    'strGMErrRefreshFail': '【错误】.gm 刷新发生异常时的提示\n变量：{error}=异常信息\n示例：更新失败: permission denied',
}

# ODC 兼容字段（保持接口一致）
dictStrConst = {}
dictGValue = {}
dictTValue = {}


# ==================== 模板渲染工具 ====================

def safe_format(template: str, **kwargs) -> str:
    """安全格式化模板：用 kwargs 替换 {变量}，缺失变量保留原样。"""
    result = template
    for key, value in kwargs.items():
        result = result.replace('{' + key + '}', str(value))
    return result


def get_template(key: str, bot_hash=None) -> str:
    """
    获取自定义回复模板。
    优先返回用户在 OlivOS GUI 中修改后的值，
    若未修改则返回 msgCustom.dictStrCustom 默认值。
    """
    if bot_hash is not None:
        try:
            import OlivaDiceCore as odc
            if hasattr(odc, 'msgCustom') and hasattr(odc.msgCustom, 'dictStrCustomDict'):
                user_dict = odc.msgCustom.dictStrCustomDict.get(bot_hash, {})
                if key in user_dict and user_dict[key]:
                    return user_dict[key]
        except Exception:
            pass
    return dictStrCustom.get(key, '')


def render(key: str, bot_hash=None, **kwargs) -> str:
    """获取模板并渲染，一步到位。"""
    template = get_template(key, bot_hash)
    if not template:
        return ''
    return safe_format(template, **kwargs)
