# -*- encoding: utf-8 -*-
"""
诡秘规则插件——核心业务函数模块。

负责：
1. 属性随机生成（2d3，范围 2-6）
2. D20 技能/属性检定（rd20 + 属性 + 技能加值）
3. 理智检定（SC：rd20 ≤ 理智 = 成功）
4. 格式化输出回复文本（全部通过 msgCustom 模板渲染）
"""

import random
import re

from . import config
from . import msgCustom

# 合并 v3 + v4 全部属性名（用于属性/技能判断）
_ALL_ATTR_NAMES = list(set(
    [a['name'] for a in config.attrs_v3] + [a['name'] for a in config.attrs_v4]
))

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


def format_attrs(stats: dict, is_v4: bool = False,
                 bot_hash=None) -> str:
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
        result += '\n\n' + msgCustom.render('strGMAttrV4Note', bot_hash=bot_hash)

    return result


def build_attr_reply(nick: str, count: int, is_v4: bool = False,
                     bot_hash=None) -> str:
    """构建完整的属性生成回复消息（模板渲染）。"""
    title = msgCustom.render('strGMAttrTitle', bot_hash=bot_hash, nick=nick)

    for _ in range(count):
        attr_text = format_attrs(generate_attrs(is_v4), is_v4, bot_hash=bot_hash)
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
    从目标字符串中分离技能/属性名、手动加值、改判属性和奖励/惩罚投。

    例: '力量+5'       → ('力量', 5, 'adjust', None, None, None)
        '格斗-2'       → ('格斗', -2, 'adjust', None, None, None)
        '格斗+2+3'     → ('格斗', 5, 'adjust', None, None, None)  # +2+3 合并求和
        '力量5'        → ('力量', 5, 'absolute', None, None, None)
        '驯兽/教育'    → ('驯兽', None, None, '教育', None, None)
        '格斗+3/灵感'  → ('格斗', 3, 'adjust', '灵感', None, None)
        '力量 adv'     → ('力量', None, None, None, 'adv', None)
        '格斗 dis'     → ('格斗', None, None, None, 'dis', None)

    返回: (clean_name, value, mode, override_attr, roll_mode, extra_attr)
          extra_attr 保留字段，当前始终为 None（+N+M 格式合并求和到 value）
    """
    override_attr = None
    roll_mode = None

    # 提取 adv/dis/优势/劣势 后缀
    adv_match = re.search(r'\s+(adv|优势|dis|劣势)\s*$', raw_target, re.IGNORECASE)
    if adv_match:
        keyword = adv_match.group(1).lower()
        roll_mode = 'adv' if keyword in ('adv', '优势') else 'dis'
        raw_target = raw_target[:adv_match.start()].strip()
    # 提取 /属性 后缀（改判属性）
    slash_match = re.search(r'/(.+)$', raw_target)
    if slash_match:
        override_attr = slash_match.group(1).strip()
        raw_target = raw_target[:slash_match.start()].strip()
    # 匹配带符号的：+N 或 -N 序列（全部累加为一个总调整值）
    match = re.search(r'((?:[+\-]\d+)+)$', raw_target)
    if match:
        mod_str = match.group(1)
        total_mod = sum(int(x) for x in re.findall(r'[+\-]\d+', mod_str))
        clean = raw_target[:match.start()].strip()
        if clean:
            return (clean, total_mod, 'adjust', override_attr, roll_mode, None)
    # 匹配纯数字后缀（绝对指定）
    match = re.search(r'(\d+)$', raw_target)
    if match:
        num_str = match.group(1)
        clean = raw_target[:match.start()].strip()
        if clean:
            return (clean, int(num_str), 'absolute', override_attr, roll_mode, None)
    return (raw_target.strip(), None, None, override_attr, roll_mode, None)


def perform_d20_check(pcHash, hagID, target: str, nick: str,
                      extra_attr: int = None,
                      extra_skill: int = None,
                      absolute_attr: int = None,
                      absolute_skill: int = None,
                      override_attr: str = None,
                      roll_mode: str = None,
                      bot_hash=None) -> str:
    """
    执行一次 D20 技能/属性检定（全部通过模板渲染）。

    参数:
        pcHash: 用户哈希
        hagID: 群组上下文
        target: 目标技能或属性名称（已去除手动加值后缀）
        nick: 发送者昵称
        extra_attr: 叠加的属性调整值（+/-格式，叠加在卡片值之上）
        extra_skill: 叠加的技能调整值
        absolute_attr: 绝对指定的属性值（纯数字格式，替换卡片值）
        absolute_skill: 绝对指定的技能加值
        override_attr: 改判属性名
        roll_mode: None=普通, 'adv'=奖励投(取高), 'dis'=惩罚投(取低)
        bot_hash: 机器人哈希，用于读取用户自定义模板
    """
    # 奖励投/惩罚投：掷两次取高/低
    if roll_mode == 'adv':
        d20_1 = random.randint(1, 20)
        d20_2 = random.randint(1, 20)
        d20 = max(d20_1, d20_2)
        roll_tag = msgCustom.render('strGMD20TagAdv', bot_hash=bot_hash,
                                    d1=d20_1, d2=d20_2, d20=d20)
    elif roll_mode == 'dis':
        d20_1 = random.randint(1, 20)
        d20_2 = random.randint(1, 20)
        d20 = min(d20_1, d20_2)
        roll_tag = msgCustom.render('strGMD20TagDis', bot_hash=bot_hash,
                                    d1=d20_1, d2=d20_2, d20=d20)
    else:
        d20 = random.randint(1, 20)
        roll_tag = None

    # 仅 8 种属性名走属性检定，其它（含用户自定义）一律技能
    is_skill = target not in _ALL_ATTR_NAMES
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

    # 组装 tag 字符串
    tags = []
    if has_manual:
        tags.append(msgCustom.render('strGMD20TagManual', bot_hash=bot_hash))
    if roll_tag:
        tags.append(roll_tag)
    tag_str = ' '.join(tags)

    # 标题行（先渲染，因为后面的 lines 需要以此为第一行）
    lines = [msgCustom.render('strGMD20CheckTitle', bot_hash=bot_hash,
                              nick=nick, target=target, tag=tag_str)]

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
        lines.append(msgCustom.render('strGMD20CheckLine', bot_hash=bot_hash,
                                      d20=d20, attr_display=attr_display,
                                      skill_info=skill_info))
    else:
        lines.append(msgCustom.render('strGMD20CheckLine', bot_hash=bot_hash,
                                      d20=d20, attr_display=attr_display,
                                      skill_info=''))

    total = d20 + bonus

    is_crit_success = (d20 == 20)
    is_crit_fail = (d20 == 1)

    # 结果行（始终显示，大成功/大失败在之后追加）
    lines.append(msgCustom.render('strGMD20Result', bot_hash=bot_hash, total=total))

    if is_crit_success:
        lines.append(msgCustom.render('strGMD20CritSuccess', bot_hash=bot_hash,
                                      total=total))
    elif is_crit_fail:
        lines.append(msgCustom.render('strGMD20CritFail', bot_hash=bot_hash,
                                      total=total))

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
                      loss_on_fail: str = None,
                      bot_hash=None) -> str:
    """
    执行一次理智检定（SC）（全部通过模板渲染）。

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
    lines.append(msgCustom.render('strGMSCSTitle', bot_hash=bot_hash, nick=nick))
    lines.append(msgCustom.render('strGMSCCheckLine', bot_hash=bot_hash,
                                  d20=d20, san=current_san))

    if success:
        lines.append(msgCustom.render('strGMSCSSuccess', bot_hash=bot_hash,
                                      d20=d20, san=current_san))
        loss = _roll_dice(loss_on_success)
        loss_expr_display = loss_on_success
    else:
        lines.append(msgCustom.render('strGMSCSFail', bot_hash=bot_hash,
                                      d20=d20, san=current_san))
        loss = _roll_dice(loss_on_fail)
        loss_expr_display = loss_on_fail

    lines.append(msgCustom.render('strGMSCSLossLine', bot_hash=bot_hash,
                                  expr=loss_expr_display, loss=loss))

    # 提示剩余理智
    new_san = max(0, current_san - loss)
    lines.append(msgCustom.render('strGMSCSChangeLine', bot_hash=bot_hash,
                                  old=current_san, new=new_san))

    # 疯狂阈值警告（独立 if，非互斥——可能同时触发多个阈值）
    if new_san <= 0 and current_san > 0:
        lines.append(msgCustom.render('strGMSCSLost', bot_hash=bot_hash))
    if new_san <= 2 and current_san > 2:
        lines.append(msgCustom.render('strGMSCSTrueMad', bot_hash=bot_hash))
    if new_san <= 8 and current_san > 8:
        lines.append(msgCustom.render('strGMSCSHalfMad', bot_hash=bot_hash))

    return '\n'.join(lines)


# ===================== 综合入口 =====================

def handle_stat_command(nick: str, count: int, is_v4: bool = False,
                        bot_hash=None) -> str:
    """处理 .诡秘 属性生成命令。"""
    return build_attr_reply(nick, count, is_v4, bot_hash=bot_hash)


def handle_gm_command(pcHash, hagID, target: str, nick: str,
                      roll_mode: str = None, bot_hash=None) -> str:
    """处理 .gm 检定命令。支持手动加值、改判属性、奖励投/惩罚投。"""
    if target.strip().lower() == 'help':
        return msgCustom.dictHelpDocTemp.get('诡秘规则帮助', '暂无帮助信息')
    # 解析手动加值后缀
    clean_target, manual_mod, mod_mode, override_attr, parsed_roll_mode, _ = _parse_manual_modifier(target)

    # 外部传入的 roll_mode（来自 .gmb/.gmp/.gm 优势 等）优先
    if roll_mode:
        parsed_roll_mode = roll_mode

    if clean_target is None:
        # 回退：理论上不应到达，但保留安全兜底
        clean_target = target
        manual_mod = None
        mod_mode = None
        override_attr = None
        parsed_roll_mode = None

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
    is_skill = final_target in config.SKILL_ATTR_MAP or final_target not in _ALL_ATTR_NAMES
    if manual_mod is not None:
        if mod_mode == 'absolute':
            if is_skill:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         absolute_skill=manual_mod,
                                         override_attr=override_attr,
                                         roll_mode=parsed_roll_mode,
                                         bot_hash=bot_hash)
            else:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         absolute_attr=manual_mod,
                                         override_attr=override_attr,
                                         roll_mode=parsed_roll_mode,
                                         bot_hash=bot_hash)
        else:
            if is_skill:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         extra_skill=manual_mod,
                                         override_attr=override_attr,
                                         roll_mode=parsed_roll_mode,
                                         bot_hash=bot_hash)
            else:
                return perform_d20_check(pcHash, hagID, final_target, nick,
                                         extra_attr=manual_mod,
                                         override_attr=override_attr,
                                         roll_mode=parsed_roll_mode,
                                         bot_hash=bot_hash)
    else:
        return perform_d20_check(pcHash, hagID, final_target, nick,
                                 override_attr=override_attr,
                                 roll_mode=parsed_roll_mode,
                                 bot_hash=bot_hash)


def handle_sc_command(pcHash, hagID, nick: str,
                      loss_on_success: str = None,
                      loss_on_fail: str = None,
                      bot_hash=None) -> str:
    """处理 .gmsc 理智检定命令。"""
    return perform_san_check(pcHash, hagID, nick, loss_on_success, loss_on_fail,
                             bot_hash=bot_hash)


# ===================== 序列/消化 & 属性计算 =====================

def _get_special_value(pcHash, hagID, key: str) -> int:
    """读取角色卡中特殊值（序列/消化），未录入返回 None。"""
    odc = _get_odc()
    try:
        val = odc.pcCard.pcCardDataGetBySkillName(pcHash, key, hagID)
        if val is not None:
            return int(val)
    except Exception:
        pass
    return None


def refresh_derived_stats(pcHash, hagID, nick: str, bot_hash=None) -> str:
    """
    根据卡片中的序列等级、消化度、属性，自动计算并更新生命/灵性。
    返回格式化的结果说明（模板渲染）。
    """
    odc = _get_odc()
    seq_raw = _get_special_value(pcHash, hagID, '序列')
    digest = _get_special_value(pcHash, hagID, '消化') or 0
    con = _get_user_stat(pcHash, hagID, '体质')
    pow_val = _get_user_stat(pcHash, hagID, '意志')
    int_val = _get_user_stat(pcHash, hagID, '灵感')

    # 序列加成：序列9→1倍, 序列8→2倍, ..., 序列0→10倍
    seq_mult = min(max(0 if seq_raw is None else (10 - seq_raw), 0), 10)
    digest_bonus = digest // 5

    hp_new = 10 + con + seq_mult * con + digest_bonus
    mp_new = pow_val + int_val + seq_mult * int_val + digest_bonus
    san_new = 10 + pow_val

    # 写入卡片
    try:
        odc.pcCard.setPcSkillAPI(
            pcHash=pcHash, skillName='血量上限', skillValue=hp_new,
            hagId=hagID
        )
        odc.pcCard.setPcSkillAPI(
            pcHash=pcHash, skillName='血量', skillValue=hp_new,
            hagId=hagID
        )
        odc.pcCard.setPcSkillAPI(
            pcHash=pcHash, skillName='灵性', skillValue=mp_new,
            hagId=hagID
        )
        odc.pcCard.setPcSkillAPI(
            pcHash=pcHash, skillName='理智', skillValue=san_new,
            hagId=hagID
        )
    except Exception as e:
        return msgCustom.render('strGMErrRefreshFail', bot_hash=bot_hash, error=e)

    # 序列信息片段
    if seq_raw is not None:
        seq_info = msgCustom.render('strGMRefreshSeqInfo', bot_hash=bot_hash,
                                    seq=seq_raw, mult=seq_mult)
    else:
        seq_info = msgCustom.render('strGMRefreshNoSeq', bot_hash=bot_hash)

    return msgCustom.render('strGMRefreshSuccess', bot_hash=bot_hash,
                            nick=nick, seq_info=seq_info,
                            digest=digest, digest_bonus=digest_bonus,
                            hp=hp_new, mp=mp_new, san=san_new)


def ri_check(plugin_event, pcHash, hagID, nick: str) -> str:
    """先攻检定：rd20 + 卡片敏捷，并注册到 ODC 先攻列表。"""
    odc = _get_odc()
    d20 = random.randint(1, 20)
    dex = _get_user_stat(pcHash, hagID, '敏捷')
    total = d20 + dex

    # 从 plugin_event 提取 bot_hash（后续复用）
    bot_hash = plugin_event.bot_info.hash if hasattr(plugin_event, 'bot_info') else None

    # 注册到 ODC 的先攻系统
    try:
        platform = plugin_event.platform['platform']
        user_id = plugin_event.data.user_id
        hag_id = (str(plugin_event.data.host_id) + '|' + str(plugin_event.data.group_id)) \
            if plugin_event.data.host_id else str(plugin_event.data.group_id)
        odc.msgReplyModel.setUserConfigForInit(
            tmp_hagID=hag_id,
            tmp_pc_platform=platform,
            bot_hash=bot_hash,
            config_key='groupInitList',
            init_name=nick,
            init_value=total,
        )
        odc.msgReplyModel.setUserConfigForInit(
            tmp_hagID=hag_id,
            tmp_pc_platform=platform,
            bot_hash=bot_hash,
            config_key='groupInitParaList',
            init_name=nick,
            init_value=f'rd20+敏捷({dex})',
        )
        odc.msgReplyModel.setUserConfigForInit(
            tmp_hagID=hag_id,
            tmp_pc_platform=platform,
            bot_hash=bot_hash,
            config_key='groupInitUserList',
            init_name=nick,
            init_value={'userId': user_id, 'platform': platform},
        )
    except Exception as e:
        from .utils import error_log
        error_log(None, f'ri_check 先攻注册异常: {type(e).__name__}: {e}')

    return msgCustom.render('strGMRiCheck', bot_hash=bot_hash,
                            nick=nick, d20=d20, dex=dex, total=total)
