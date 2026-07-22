# -*- encoding: utf-8 -*-
"""
轻量工具函数模块。

为诡秘规则插件提供 OlivOS 与 OlivaDiceCore 的基础交互封装。
包含日志、消息提取、安全回复、命令解析等功能。
"""

import re
import traceback

from . import config
from . import msgCustom

# 全局缓存运行期 Proc（目前仅 reply_message fallback 使用）
_runtime_proc = None


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
    """从事件中安全获取原始消息文本。"""
    try:
        return str(getattr(plugin_event.data, 'message', ''))
    except Exception:
        return ''


def reply_message(plugin_event, message: str) -> None:
    """统一回复消息（封装 try/except）。"""
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
    """解析「.诡秘」相关命令。"""
    result = {'is_guimi': False, 'sub_cmd': None, 'count': 1, 'error': None}
    text = message_text.strip()
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
    if tail == '4.0':
        result['sub_cmd'] = 'attr_v4'
        result['count'] = 1
        return result
    if tail in ('', '3.0', '3.5'):
        result['sub_cmd'] = 'attr'
        result['count'] = 1
        return result
    if tail.isdigit():
        num = int(tail)
        if num < 1:
            result['error'] = msgCustom.get_template('strGMErrParam')
            return result
        if num > config.max_generate_count:
            result['error'] = msgCustom.get_template('strGMErrTooMany')
            return result
        result['sub_cmd'] = 'attr'
        result['count'] = num
        return result
    count_part = ''
    if tail.startswith('4.0'):
        count_part = tail[3:].strip()
        result['sub_cmd'] = 'attr_v4'
    elif tail.startswith('3.0'):
        count_part = tail[3:].strip()
        result['sub_cmd'] = 'attr'
    elif tail.startswith('3.5'):
        count_part = tail[3:].strip()
        result['sub_cmd'] = 'attr'
    else:
        count_part = tail.strip()
        result['sub_cmd'] = 'attr'
        if count_part.isdigit():
            num = int(count_part)
            if num < 1:
                result['error'] = msgCustom.get_template('strGMErrParam')
                return result
            if num > config.max_generate_count:
                result['error'] = msgCustom.get_template('strGMErrTooMany')
                return result
            result['count'] = num
        elif count_part:
            result['error'] = msgCustom.get_template('strGMErrParam')
            return result
        return result
    digit_match = re.search(r'\d+', count_part)
    if digit_match:
        num = int(digit_match.group())
        if num < 1:
            result['error'] = msgCustom.get_template('strGMErrParam')
            return result
        if num > config.max_generate_count:
            result['error'] = msgCustom.get_template('strGMErrTooMany')
            return result
        result['count'] = num
    elif count_part:
        result['error'] = msgCustom.get_template('strGMErrParam')
        return result
    else:
        result['count'] = 1
    return result


def parse_gm_command(message_text: str) -> dict:
    """解析「.gm <技能/属性>」命令。"""
    result = {'is_gm': False, 'target': None, 'error': None}
    text = message_text.strip()
    matched_prefix = None
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            matched_prefix = prefix
            break
    if matched_prefix is None:
        return result
    rest = text[len(matched_prefix):]
    if not rest.lower().startswith('gm'):
        return result
    result['is_gm'] = True
    tail = rest[2:].strip()
    if not tail:
        result['error'] = msgCustom.get_template('strGMErrNoTarget')
        return result
    roll_mode = None
    for keyword, mode in [('优势', 'adv'), ('劣势', 'dis')]:
        if tail.startswith(keyword) and len(tail) > len(keyword):
            roll_mode = mode
            tail = tail[len(keyword):].strip()
            break
    result['target'] = tail
    result['roll_mode'] = roll_mode
    return result


def parse_gmb_command(message_text: str) -> dict:
    """解析「.gmb <技能/属性>」奖励投命令。"""
    result = {'is_gm': False, 'target': None, 'error': None, 'roll_mode': 'adv'}
    text = message_text.strip()
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            rest = text[len(prefix):]
            if not rest.lower().startswith('gmb'):
                return {'is_gm': False, 'target': None, 'error': None, 'roll_mode': None}
            tail = rest[3:].strip()
            if not tail:
                result['is_gm'] = True
                result['error'] = msgCustom.get_template('strGMErrNoTargetAdv')
                return result
            result['is_gm'] = True
            result['target'] = tail
            return result
    return result


def parse_gmp_command(message_text: str) -> dict:
    """解析「.gmp <技能/属性>」惩罚投命令。"""
    result = {'is_gm': False, 'target': None, 'error': None, 'roll_mode': 'dis'}
    text = message_text.strip()
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            rest = text[len(prefix):]
            if not rest.lower().startswith('gmp'):
                return {'is_gm': False, 'target': None, 'error': None, 'roll_mode': None}
            tail = rest[3:].strip()
            if not tail:
                result['is_gm'] = True
                result['error'] = msgCustom.get_template('strGMErrNoTargetAdv')
                return result
            result['is_gm'] = True
            result['target'] = tail
            return result
    return result


def parse_gmri_command(message_text: str) -> dict:
    """解析「.gmri」先攻检定命令。"""
    result = {'is_gmri': False}
    text = message_text.strip()
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            rest = text[len(prefix):]
            if rest.lower().startswith('gmri'):
                result['is_gmri'] = True
            return result
    return result


def parse_sc_command(message_text: str) -> dict:
    """解析「.gmsc [损失骰]」理智检定命令。"""
    result = {'is_sc': False, 'loss_on_success': None, 'loss_on_fail': None, 'error': None}
    text = message_text.strip()
    matched_prefix = None
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            matched_prefix = prefix
            break
    if matched_prefix is None:
        return result
    rest = text[len(matched_prefix):]
    if not rest.lower().startswith('gmsc'):
        return result
    result['is_sc'] = True
    tail = rest[4:].strip()
    if tail:
        parts = re.split(r'[/\s]+', tail)
        parts = [p for p in parts if p]
        if len(parts) >= 1:
            result['loss_on_success'] = parts[0]
        if len(parts) >= 2:
            result['loss_on_fail'] = parts[1]
    return result


def extract_guimi_tail(message_text: str) -> str:
    """从「.诡秘<内容>」中提取 tail，用于互通路由。"""
    text = message_text.strip()
    for prefix in config.allowed_prefix_list:
        if text.startswith(prefix):
            rest = text[len(prefix):]
            if rest.startswith(config.main_command):
                tail = rest[len(config.main_command):].strip()
                if tail in ('', '3.0', '3.5', '4.0'):
                    return ''
                if tail.isdigit():
                    return ''
                if tail.startswith('4.0') and (len(tail) == 3 or tail[3:].strip().isdigit()):
                    return ''
                if tail.startswith('3.0') or tail.startswith('3.5'):
                    rem = tail[3:].strip()
                    if rem == '' or rem.isdigit():
                        return ''
                return tail
            break
    return ''
