# -*- encoding: utf-8 -*-
"""
诡秘规则插件——核心业务函数模块。

负责：
1. 属性随机生成（2d3，范围 2-6）
2. D20 技能/属性检定（rd20 + 属性 + 技能加值）
3. 理智检定（SC：rd20 ≤ 理智 = 成功）
4. 格式化输出回复文本
"""

import random
import re

from . import config
from . import msgCustom

# OlivaDiceCore 仅在实际调用时才引用，避免导入时依赖缺失导致崩溃
_ODC = None


def _get_odc():
    """延迟获取 OlivaDiceCore 模块引用。"""
    global _ODC
    if _ODC is None:
        import OlivaDiceCore as odc
        _ODC = odc
    return _ODC


# ===================== 属性生成 =====================

def _roll_stat() -> int:
    """模拟 ranint(1,3) + ranint(1,3)，返回 2~6 的整数。"""
    return random.randint(1, 3) + random.randint(1, 3)


def generate_attrs(is_v4: bool = False) -> dict:
    """
    生成一套完整属性。

    返回格式: {var_name: value}
    保证所有可能需要的 var 都有值，包括 3.5 和 4.0 两套键名。
    """
    stats = {
        'str': _roll_stat(),
        'con': _roll_stat(),
        'dex': _roll_stat(),
        'app': _roll_stat(),
        'int': _roll_stat(),
        'pow': _roll_stat(),
        'edu': _roll_stat(),
        'lingx': _roll_stat(),
        'luck': _roll_stat(),
        'int1': _roll_stat(),
    }
    return stats


def format_attrs(stats: dict, is_v4: bool = False) -> str:
    """
    将属性数据格式化为可读的文本块。

    格式：每行3个属性，末尾显示 [不含幸运总和/总属性总和]。
    """
    attrs = config.attrs_v4 if is_v4 else config.attrs_v3

    total_all = 0
    total_no_luck = 0
    for attr in attrs:
        val = stats.get(attr['var'], 0)
        total_all += val
        if attr['var'] != 'luck':
            total_no_luck += val

    lines = []
    line_buf = []
    for attr in attrs:
        line_buf.append(f"{attr['name']}:{stats.get(attr['var'], 0)}")
        if len(line_buf) == 3:
            lines.append(' '.join(line_buf))
            line_buf = []
    if line_buf:
        lines.append(' '.join(line_buf))

    lines.append(f'［{total_no_luck}/{total_all}］')

    result = '\n'.join(lines)

    if is_v4:
        result += '\n\n（4.0属性为测试内容，非最终版本）'

    return result


def build_attr_reply(nick: str, count: int, is_v4: bool = False) -> str:
    """构建完整的属性生成回复消息。"""
    title = f'<{nick}>命运的馈赠在暗处已标注好了价码：'

    for _ in range(count):
        attr_text = format_attrs(generate_attrs(is_v4), is_v4)
        title += '\n\n' + attr_text

    return title


# ===================== D20 检定 =====================

def _get_user_stat(pcHash, hagID, stat_name: str) -> int:
    """
    从 OlivaDiceCore 角色卡中读取用户属性值。

    尝试多种可能的键名（中英文别名），返回找到的第一个非零值。
    若全部未找到或为零，返回 0。
    """
    odc = _get_odc()
    aliases = config.ATTR_NAME_ALIASES.get(stat_name, [stat_name])
    for alias in aliases:
        try:
            val = odc.pcCard.pcCardDataGetBySkillName(pcHash, alias, hagID)
            if val is not None and val != 0:
                return int(val)
        except Exception:
            continue
    return 0


def _get_user_skill(pcHash, hagID, skill_name: str) -> int:
    """
    从角色卡中读取用户技能值。

    返回技能数值，若不存在则返回 0。
    """
    odc = _get_odc()
    try:
        val = odc.pcCard.pcCardDataGetBySkillName(pcHash, skill_name, hagID)
        if val is not None:
            return int(val)
    except Exception:
        pass
    return 0


def _get_user_san(pcHash, hagID) -> int:
    """
    从角色卡中读取用户理智值（SAN）。

    规则书：理智上限 = 10 + 意志。
    角色卡中可能存储为「理智」「san」「SAN」等。
    """
    odc = _get_odc()
    for san_name in config.SAN_ATTR_NAMES:
        try:
            val = odc.pcCard.pcCardDataGetBySkillName(pcHash, san_name, hagID)
            if val is not None and val != 0:
                return int(val)
        except Exception:
            continue

    # 回退：理智 = 10 + 意志
    try:
        will = _get_user_stat(pcHash, hagID, '意志')
        if will > 0:
            return 10 + will
    except Exception:
        pass

    return 10  # 最终默认值


def _parse_skill_level(skill_value: int) -> tuple:
    """
    根据技能值解析技能等级和加值。

    等级编号（0-based）：0=未受训, 1=受训, 2=熟练,
    3=进阶, 4=精通, 5=博学, 6=大师。
    小于 0 视为未受训。

    返回: (等级名, 加值)
    """
    level_map = [
        ('未受训', -4),
        ('受训', 0),
        ('熟练', 2),
        ('进阶', 4),
        ('精通', 6),
        ('博学', 8),
        ('大师', 10),
    ]
    if skill_value < 0:
        skill_value = 0
    if skill_value >= len(level_map):
        skill_value = len(level_map) - 1
    return level_map[skill_value]


def _parse_manual_modifier(raw_target: str) -> tuple:
    """
    从目标字符串中分离技能/属性名、手动加值和改判属性。

    例: '力量+5'     → ('力量', 5, 'adjust', None)
        '格斗-2'     → ('格斗', -2, 'adjust', None)
        '力量5'      → ('力量', 5, 'absolute', None)
        '驯兽/教育'  → ('驯兽', None, None, '教育')
        '格斗+3/灵感'→ ('格斗', 3, 'adjust', '灵感')
        '力量'       → ('力量', None, None, None)

    返回: (clean_name, value_or_None, mode_or_None, override_attr_or_None)
          mode: 'adjust'=叠加, 'absolute'=覆盖
    """
    override_attr = None
    # 先提取 /属性 后缀（改判属性）
    slash_match = re.search(r'/(.+)$', raw_target)
    if slash_match:
        override_attr = slash_match.group(1).strip()
        raw_target = raw_target[:slash_match.start()].strip()
    # 匹配带符号的：+N 或 -N（叠加调整）
    match = re.search(r'([+\-]\d+)$', raw_target)
    if match:
        mod_str = match.group(1)
        clean = raw_target[:match.start()].strip()
        if clean:
            return (clean, int(mod_str), 'adjust', override_attr)
    # 匹配纯数字后缀（绝对指定）
    match = re.search(r'(\d+)$', raw_target)
    if match:
        num_str = match.group(1)
        clean = raw_target[:match.start()].strip()
        if clean:
            return (clean, int(num_str), 'absolute', override_attr)
    return (raw_target.strip(), None, None, override_attr)


def perform_d20_check(pcHash, hagID, target: str, nick: str,
                      extra_attr: int = None,
                      extra_skill: int = None,
                      absolute_attr: int = None,
                      absolute_skill: int = None,
                      override_attr: str = None) -> str:
    """
    执行一次 D20 技能/属性检定。

    参数:
        pcHash: 用户哈希
        hagID: 群组上下文
        target: 目标技能或属性名称（已去除手动加值后缀）
        nick: 发送者昵称
        extra_attr: 叠加的属性调整值（+/-格式，叠加在卡片值之上）
        extra_skill: 叠加的技能调整值
        absolute_attr: 绝对指定的属性值（纯数字格式，替换卡片值）
        absolute_skill: 绝对指定的技能加值
    """
    d20 = random.randint(1, 20)

    # 仅 8 种属性名走属性检定，其它（含用户自定义）一律技能
    attr_names = [a['name'] for a in config.attrs_v3]
    is_skill = target not in attr_names
    linked_attr_name = override_attr if override_attr else config.SKILL_ATTR_MAP.get(target, '力量')

    # 读取卡片属性值
    card_attr = _get_user_stat(pcHash, hagID, linked_attr_name)

    # 绝对指定优先，否则用卡片值 + 叠加调整
    if absolute_attr is not None:
        attr_val = absolute_attr
        attr_display = f'{linked_attr_name}({attr_val} 手动指定)'
    else:
        extra_a = extra_attr if extra_attr is not None else 0
        attr_val = card_attr + extra_a
        if extra_a != 0:
            attr_display = f'{linked_attr_name}(卡片{card_attr} + 调整{extra_a:+d})'
        else:
            attr_display = f'{linked_attr_name}({card_attr})'

    has_manual = (absolute_attr is not None or absolute_skill is not None
                  or extra_attr is not None or extra_skill is not None)

    lines = []
    manual_tag = '【手动】' if has_manual else ''
    lines.append(f'<{nick}>对【{target}】进行检定：{manual_tag}')

    bonus = attr_val
    skill_info = ''

    if is_skill:
        card_skill = _get_user_skill(pcHash, hagID, target)
        level_name, card_skill_bonus = _parse_skill_level(card_skill)

        if absolute_skill is not None:
            lv_name, skill_bonus = _parse_skill_level(absolute_skill)
            skill_info = f' + 技能{target}(手动指定 等级{absolute_skill} {lv_name}:{skill_bonus:+d})'
        else:
            extra_s = extra_skill if extra_skill is not None else 0
            skill_bonus = card_skill_bonus + extra_s
            if extra_s != 0:
                skill_info = f' + 技能{target}(卡片{level_name}:{card_skill_bonus:+d} + 调整{extra_s:+d})'
            else:
                skill_info = f' + 技能{target}({level_name}:{skill_bonus:+d})'

        bonus = attr_val + skill_bonus
        lines.append(f'rd20({d20}) + {attr_display}{skill_info}')
    else:
        lines.append(f'rd20({d20}) + {attr_display}')

    total = d20 + bonus

    is_crit_success = (d20 == 20)
    is_crit_fail = (d20 == 1)

    lines.append(f'= {total}')

    if is_crit_success:
        lines.append('『大成功！』命运的眷顾降临于你。')
    elif is_crit_fail:
        lines.append('『大失败！』命运对你露出了恶意的微笑。')
    else:
        lines.append(f'检定结果: {total}')

    skill_summary = f'+技能({skill_bonus})' if is_skill else ''
    lines.append(f'（对抗时以此值比较：{d20}+{attr_val}{skill_summary}={total}）')

    return '\n'.join(lines)


# ===================== 理智检定（SC） =====================

def _parse_dice_expr(expr: str) -> tuple:
    """
    解析骰子表达式如 '1d2'、'2d6'、'1d4'，返回 (次数, 面数)。

    若无法解析，返回 (1, 2) 作为默认。
    """
    if not expr:
        return (1, 2)
    expr = expr.lower().strip()
    match = re.match(r'^(\d*)\s*d\s*(\d+)$', expr)
    if match:
        count = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        return (count, sides)
    return (1, 2)


def _roll_dice(expr: str) -> int:
    """掷骰并返回总和。"""
    count, sides = _parse_dice_expr(expr)
    total = 0
    for _ in range(count):
        total += random.randint(1, sides)
    return total


def perform_san_check(pcHash, hagID, nick: str,
                      loss_on_success: str = None,
                      loss_on_fail: str = None) -> str:
    """
    执行一次理智检定（SC）。

    规则书：rd20 ≤ 当前理智 = 成功，rd20 > 理智 = 失败。
    理智损失格式：「成功损失/失败损失」，如未指定则默认 1/1d2。

    返回: 格式化的检定结果字符串
    """
    current_san = _get_user_san(pcHash, hagID)
    d20 = random.randint(1, 20)

    success = d20 <= current_san

    # 默认损失值
    if loss_on_success is None:
        loss_on_success = '1'
    if loss_on_fail is None:
        loss_on_fail = '1d2'

    lines = []
    lines.append(f'<{nick}>进行理智检定：')

    if '最大' in str(current_san) or True:
        lines.append(f'rd20({d20}) vs 理智({current_san})')

    if success:
        lines.append(f'{d20} ≤ {current_san}，【理智检定成功】')
        loss = _roll_dice(loss_on_success)
        loss_expr_display = loss_on_success
        lines.append(f'损失理智: {loss_expr_display} = {loss}')
        result_type = '成功'
        result_loss = loss
        result_loss_expr = loss_on_success
    else:
        lines.append(f'{d20} > {current_san}，【理智检定失败】')
        loss = _roll_dice(loss_on_fail)
        loss_expr_display = loss_on_fail
        lines.append(f'损失理智: {loss_expr_display} = {loss}')
        result_type = '失败'
        result_loss = loss
        result_loss_expr = loss_on_fail

    # 提示剩余理智
    new_san = max(0, current_san - result_loss)
    lines.append(f'理智变化: {current_san} → {new_san}')

    # 疯狂阈值警告
    if new_san <= 8 and current_san > 8:
        lines.append('⚠ 你已陷入【半疯】状态，获得随机疯狂倾向。')
    elif new_san <= 2 and current_san > 2:
        lines.append('⚠⚠ 你已陷入【真疯】状态，难以沟通。')
    elif new_san <= 0 and current_san > 0:
        lines.append('☠ 理智归零，你已【失控】！')

    return '\n'.join(lines)


# ===================== 综合入口 =====================

def handle_stat_command(nick: str, count: int, is_v4: bool = False) -> str:
    """处理 .诡秘 属性生成命令。"""
    return build_attr_reply(nick, count, is_v4)


def handle_gm_command(pcHash, hagID, target: str, nick: str) -> str:
    """处理 .gm 检定命令。支持手动加值格式如 .gm力量+5 或 .gm格斗+3。"""
    # help 指令（双保险）
    if target.strip().lower() == 'help':
        return msgCustom.dictHelpDocTemp.get(
            '诡秘规则帮助', '暂无帮助信息'
        )
    # 解析手动加值后缀
    clean_target, manual_mod, mod_mode, override_attr = _parse_manual_modifier(target)

    if clean_target is None:
        clean_target = target
        manual_mod = None
        mod_mode = None
        override_attr = None

    # 检查目标是否在已知的技能/属性列表中
    found = None
    if clean_target in config.SKILL_ATTR_MAP:
        found = clean_target
    else:
        # 模糊匹配：技能列表中查找
        for skill_name in config.SKILL_ATTR_MAP:
            if skill_name == clean_target or skill_name.startswith(clean_target):
                found = skill_name
                break
        # 属性列表中查找
        if found is None:
            for attr_def in config.attrs_v3:
                if attr_def['name'] == clean_target:
                    found = clean_target
                    break
            for attr_def in config.attrs_v4:
                if attr_def['name'] == clean_target:
                    found = clean_target
                    break

    final_target = found if found is not None else clean_target

    # 手动加值判定
    # 不在已知列表中的名称默认视为技能（属性仅8种，误判率低）
    is_skill = final_target in config.SKILL_ATTR_MAP or final_target not in [
        a['name'] for a in config.attrs_v3
    ]
    if manual_mod is not None:
        if mod_mode == 'absolute':
            # 纯数字格式 → 绝对指定（数字表示技能等级，非加值）
            if is_skill:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         absolute_skill=manual_mod,
                                         override_attr=override_attr)
            else:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         absolute_attr=manual_mod,
                                         override_attr=override_attr)
        else:
            # +/-格式 → 叠加调整
            if is_skill:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         extra_skill=manual_mod,
                                         override_attr=override_attr)
            else:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         extra_attr=manual_mod,
                                         override_attr=override_attr)
    else:
        return perform_d20_check(pcHash, hagID, final_target, nick,
                                 override_attr=override_attr)


def handle_sc_command(pcHash, hagID, nick: str,
                      loss_on_success: str = None,
                      loss_on_fail: str = None) -> str:
    """处理 .sc 理智检定命令。"""
    return perform_san_check(pcHash, hagID, nick, loss_on_success, loss_on_fail)
