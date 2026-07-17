# -*- encoding: utf-8 -*-
"""
轻量工具函数模块。

为诡秘规则插件提供 OlivOS 与 OlivaDiceCore 的基础交互封装。
包含日志、消息提取、安全回复、命令解析等功能。
"""

import re
import traceback

from . import config

# 全局缓存运行期 Proc
_runtime_proc = None


def set_runtime_proc(Proc) -> None:
    """缓存运行期 Proc。"""
    global _runtime_proc
    if Proc is not None:
        _runtime_proc = Proc


def get_runtime_proc():
    """获取缓存的 Proc。"""
    return _runtime_proc


def info_log(Proc, message: str) -> None:
    """输出 info 级日志。"""
    full = f'[{config.plugin_name}][INFO] {message}'
    if Proc is not None and hasattr(Proc, 'log'):
        try:
            Proc.log(2, full, [])
            return
        except Exception:
            pass
    print(full)


def error_log(Proc, message: str) -> None:
    """输出 error 级日志。"""
    full = f'[{config.plugin_name}][ERROR] {message}'
    if Proc is not None and hasattr(Proc, 'log'):
        try:
            Proc.log(4, full, [])
            return
        except Exception:
            pass
    print(full)


def get_message_text_from_event(plugin_event) -> str:
    """从事件中安全获取原始消息文本（CQ 码格式）。"""
    try:
        return str(getattr(plugin_event.data, 'message', ''))
    except Exception:
        return ''


def reply_message(plugin_event, message: str) -> None:
    """
    统一回复消息（封装 try/except）。
    优先使用 OlivaDiceCore 的 replyMsg，失败时回退到 plugin_event.reply。
    """
    try:
        import OlivaDiceCore
        OlivaDiceCore.msgReply.replyMsg(plugin_event, str(message))
    except Exception:
        try:
            plugin_event.reply(str(message))
        except Exception as exc:
            error_log(
                _runtime_proc,
                f'reply_message 失败: {type(exc).__name__}: {exc}',
            )


def parse_command(message_text: str) -> dict:
    """
    解析「.诡秘」相关命令。

    返回:
        {
            'is_guimi': bool,    # 是否为 .诡秘 命令
            'sub_cmd': str,      # 子命令: 'attr'|'attr_v4'|None
            'count': int,        # 生成套数
            'error': str|None,   # 错误信息
        }
    """
    result = {
        'is_guimi': False,
        'sub_cmd': None,
        'count': 1,
        'error': None,
    }

    text = message_text.strip()

    # 匹配前缀
    matched_prefix = None
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            matched_prefix = prefix
            break
    if matched_prefix is None:
        return result

    rest = text[len(matched_prefix):]
    if not rest.startswith(config.main_command):
        return result

    result['is_guimi'] = True
    tail = rest[len(config.main_command):]

    # 「.诡秘4.0」
    if tail == '4.0':
        result['sub_cmd'] = 'attr_v4'
        result['count'] = 1
        return result

    # 「.诡秘」「.诡秘3.0」「.诡秘3.5」
    if tail in ('', '3.0', '3.5'):
        result['sub_cmd'] = 'attr'
        result['count'] = 1
        return result

    # 「.诡秘5」（纯数字后缀）
    if tail.isdigit():
        num = int(tail)
        if num < 1:
            result['error'] = '参数错误'
            return result
        if num > config.max_generate_count:
            result['error'] = (
                '"你应该去向伟大的宿命之环祈祷，'
                '这要观察的【命运】也太多了，我没这么大能耐。"'
            )
            return result
        result['sub_cmd'] = 'attr'
        result['count'] = num
        return result

    # 「.诡秘4.0 3」或「.诡秘 3」
    version_part = ''
    count_part = ''
    if tail.startswith('4.0'):
        version_part = '4.0'
        count_part = tail[3:].strip()
        result['sub_cmd'] = 'attr_v4'
    elif tail.startswith('3.0'):
        version_part = '3.0'
        count_part = tail[3:].strip()
        result['sub_cmd'] = 'attr'
    elif tail.startswith('3.5'):
        version_part = '3.5'
        count_part = tail[3:].strip()
        result['sub_cmd'] = 'attr'
    else:
        count_part = tail.strip()
        result['sub_cmd'] = 'attr'

    digit_match = re.search(r'\d+', count_part)
    if digit_match:
        num = int(digit_match.group())
        if num < 1:
            result['error'] = '参数错误'
            return result
        if num > config.max_generate_count:
            result['error'] = (
                '"你应该去向伟大的宿命之环祈祷，'
                '这要观察的【命运】也太多了，我没这么大能耐。"'
            )
            return result
        result['count'] = num
    elif count_part:
        result['error'] = '参数错误'
        return result
    else:
        result['count'] = 1

    return result


def parse_gm_command(message_text: str) -> dict:
    """
    解析「.gm <技能/属性>」命令。

    返回:
        {
            'is_gm': bool,
            'target': str|None,   # 目标技能或属性名称
            'error': str|None,
        }
    """
    result = {
        'is_gm': False,
        'target': None,
        'error': None,
    }

    text = message_text.strip()

    # 匹配前缀
    matched_prefix = None
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            matched_prefix = prefix
            break
    if matched_prefix is None:
        return result

    rest = text[len(matched_prefix):]

    # 必须以「gm」或「GM」开头（不区分大小写）
    if not (rest.lower().startswith('gm') and (len(rest) == 2 or rest[2] in (' ', '\u3000'))):
        return result

    result['is_gm'] = True

    # 提取 gm 后面的部分
    tail = rest[2:].strip()
    if not tail:
        result['error'] = '请指定技能或属性名称，如 .gm力量 或 .gm格斗'
        return result

    result['target'] = tail
    return result


def parse_sc_command(message_text: str) -> dict:
    """
    解析「.sc [参数]」命令。

    返回:
        {
            'is_sc': bool,
            'loss_on_success': str|None,   # 成功损失骰（如 '1d2'）
            'loss_on_fail': str|None,      # 失败损失骰（如 '1d4'）
            'error': str|None,
        }
    """
    result = {
        'is_sc': False,
        'loss_on_success': None,
        'loss_on_fail': None,
        'error': None,
    }

    text = message_text.strip()

    # 匹配前缀
    matched_prefix = None
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            matched_prefix = prefix
            break
    if matched_prefix is None:
        return result

    rest = text[len(matched_prefix):]

    # 必须「sc」开头（不区分大小写）
    if not (rest.lower().startswith('sc') and (len(rest) == 2 or rest[2] in (' ', '\u3000'))):
        return result

    result['is_sc'] = True

    # 提取参数
    tail = rest[2:].strip()
    if tail:
        # 解析如 "1d2/1d4" 或 "1d2 1d4" 的格式
        parts = re.split(r'[/\s]+', tail)
        parts = [p for p in parts if p]  # 去空
        if len(parts) >= 1:
            result['loss_on_success'] = parts[0]
        if len(parts) >= 2:
            result['loss_on_fail'] = parts[1]

    return result
