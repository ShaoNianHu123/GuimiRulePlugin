# -*- encoding: utf-8 -*-
"""
诡秘规则插件——消息处理与指令路由模块。

基于 OlivaDiceCore 规则插件模板，处理以下指令：
- .诡秘 [数量/版本]  → 人物属性随机生成
- .gm <技能/属性>    → D20 技能/属性检定
- .sc [损失骰]       → 理智检定（rd20 ≤ 理智 = 成功）
"""

import OlivOS
import GuimiRulePlugin
import OlivaDiceCore
import copy
import traceback


def unity_init(plugin_event, Proc):
    """插件初始化——暂不处理。"""
    pass


def data_init(plugin_event, Proc):
    """数据初始化——注入自定义回复到 OlivaDiceCore 全局字典。"""
    # 注入自定义回复
    try:
        GuimiRulePlugin.msgCustomManager.initMsgCustom(Proc.Proc_data['bot_info_dict'])
    except Exception as e:
        GuimiRulePlugin.utils.error_log(
            Proc, f'data_init msgCustom 异常: {type(e).__name__}: {e}'
        )


def unity_reply(plugin_event, Proc):
    """
    统一消息回复入口。

    参照 OlivaDiceCore 规则插件模板的处理流程：
    1. 基础权限校验（群/频道开关、AT 触发等）
    2. 命令前缀解析
    3. 分发到具体指令处理
    """
    try:
        OlivaDiceCore.userConfig.setMsgCount()
    except Exception:
        pass

    # ---- 构建模板变量 ----
    dictTValue = OlivaDiceCore.msgCustom.dictTValue.copy()
    dictTValue['tUserName'] = plugin_event.data.sender['name']
    dictTValue['tName'] = plugin_event.data.sender['name']
    dictStrCustom = OlivaDiceCore.msgCustom.dictStrCustomDict[plugin_event.bot_info.hash]
    dictGValue = OlivaDiceCore.msgCustom.dictGValue
    dictTValue.update(dictGValue)
    dictTValue = OlivaDiceCore.msgCustomManager.dictTValueInit(plugin_event, dictTValue)

    # ---- 引用 OlivaDiceCore 工具函数 ----
    replyMsg = OlivaDiceCore.msgReply.replyMsg
    isMatchWordStart = OlivaDiceCore.msgReply.isMatchWordStart
    getMatchWordStartRight = OlivaDiceCore.msgReply.getMatchWordStartRight
    skipSpaceStart = OlivaDiceCore.msgReply.skipSpaceStart
    skipToRight = OlivaDiceCore.msgReply.skipToRight
    msgIsCommand = OlivaDiceCore.msgReply.msgIsCommand

    # ---- AT 检测 ----
    tmp_at_str = OlivOS.messageAPI.PARA.at(plugin_event.base_info['self_id']).CQ()
    tmp_id_str = str(plugin_event.base_info['self_id'])
    tmp_at_str_sub = None
    tmp_id_str_sub = None
    if 'sub_self_id' in plugin_event.data.extend:
        if plugin_event.data.extend['sub_self_id'] is not None:
            tmp_at_str_sub = OlivOS.messageAPI.PARA.at(
                plugin_event.data.extend['sub_self_id']
            ).CQ()
            tmp_id_str_sub = str(plugin_event.data.extend['sub_self_id'])

    tmp_reast_str = plugin_event.data.message
    flag_force_reply = False
    flag_is_command = False

    # 处理 CQ 回复引用
    if isMatchWordStart(tmp_reast_str, '[CQ:reply,id='):
        tmp_reast_str = skipToRight(tmp_reast_str, ']')
        tmp_reast_str = tmp_reast_str[1:]

    # 检测 AT 机器人
    if flag_force_reply is False:
        tmp_reast_str_old = tmp_reast_str
        tmp_reast_obj = OlivOS.messageAPI.Message_templet(
            'old_string', tmp_reast_str
        )
        tmp_at_list = []
        for tmp_reast_obj_this in tmp_reast_obj.data:
            tmp_para_str_this = tmp_reast_obj_this.CQ()
            if type(tmp_reast_obj_this) is OlivOS.messageAPI.PARA.at:
                tmp_at_list.append(str(tmp_reast_obj_this.data['id']))
                tmp_reast_str = tmp_reast_str.lstrip(tmp_para_str_this)
            elif type(tmp_reast_obj_this) is OlivOS.messageAPI.PARA.text:
                if tmp_para_str_this.strip(' ') == '':
                    tmp_reast_str = tmp_reast_str.lstrip(tmp_para_str_this)
                else:
                    break
            else:
                break
        if tmp_id_str in tmp_at_list:
            flag_force_reply = True
        if tmp_id_str_sub in tmp_at_list:
            flag_force_reply = True
        if 'all' in tmp_at_list:
            flag_force_reply = True
        if flag_force_reply is True:
            tmp_reast_str = skipSpaceStart(tmp_reast_str)
        else:
            tmp_reast_str = tmp_reast_str_old

    # ---- 命令前缀检测 ----
    [tmp_reast_str, flag_is_command] = msgIsCommand(
        tmp_reast_str,
        OlivaDiceCore.crossHook.dictHookList['prefix']
    )

    if not flag_is_command:
        return

    # ---- 判断消息来源 ----
    tmp_userID = plugin_event.data.user_id
    flag_is_from_master = OlivaDiceCore.ordinaryInviteManager.isInMasterList(
        plugin_event.bot_info.hash,
        OlivaDiceCore.userConfig.getUserHash(
            plugin_event.data.user_id, 'user', plugin_event.platform['platform']
        )
    )
    flag_is_from_group = False
    flag_is_from_host = False
    flag_is_from_group_admin = False

    if plugin_event.plugin_info['func_type'] == 'group_message':
        if plugin_event.data.host_id is not None:
            flag_is_from_host = True
        flag_is_from_group = True
    elif plugin_event.plugin_info['func_type'] == 'private_message':
        flag_is_from_group = False

    if flag_is_from_group:
        if 'role' in plugin_event.data.sender:
            if plugin_event.data.sender['role'] in ['owner', 'admin', 'sub_admin']:
                flag_is_from_group_admin = True

    # ---- 群/频道开关检测 ----
    tmp_hagID = None
    if flag_is_from_host and flag_is_from_group:
        tmp_hagID = '%s|%s' % (
            str(plugin_event.data.host_id), str(plugin_event.data.group_id)
        )
    elif flag_is_from_group:
        tmp_hagID = str(plugin_event.data.group_id)

    flag_hostEnable = True
    if flag_is_from_host:
        flag_hostEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId=plugin_event.data.host_id, userType='host',
            platform=plugin_event.platform['platform'],
            userConfigKey='hostEnable', botHash=plugin_event.bot_info.hash
        )
    flag_hostLocalEnable = True
    if flag_is_from_host:
        flag_hostLocalEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
            userId=plugin_event.data.host_id, userType='host',
            platform=plugin_event.platform['platform'],
            userConfigKey='hostLocalEnable', botHash=plugin_event.bot_info.hash
        )
    flag_groupEnable = True
    if flag_is_from_group:
        if flag_is_from_host:
            if flag_hostEnable:
                flag_groupEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID, userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='groupEnable', botHash=plugin_event.bot_info.hash
                )
            else:
                flag_groupEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                    userId=tmp_hagID, userType='group',
                    platform=plugin_event.platform['platform'],
                    userConfigKey='groupWithHostEnable',
                    botHash=plugin_event.bot_info.hash
                )
        else:
            flag_groupEnable = OlivaDiceCore.userConfig.getUserConfigByKey(
                userId=tmp_hagID, userType='group',
                platform=plugin_event.platform['platform'],
                userConfigKey='groupEnable', botHash=plugin_event.bot_info.hash
            )

    if not flag_hostLocalEnable and not flag_force_reply:
        return
    if not flag_groupEnable and not flag_force_reply:
        return

    # ========== 指令处理 ==========
    msg_text = plugin_event.data.message

    # ---- 获取上下文信息 ----
    nick = plugin_event.data.sender.get('name', str(tmp_userID))
    platform = plugin_event.platform['platform']

    # OlivaDiceCore 上下文
    try:
        pcHash = OlivaDiceCore.pcCard.getPcHash(tmp_userID, platform)
    except Exception:
        pcHash = None
    try:
        hagID = OlivaDiceCore.pcCard.getHagIDFromMsg(plugin_event, Proc)
    except Exception:
        hagID = None

    # ---- 处理 .诡秘 / .gm（互通路由）----
    cmd_attr = GuimiRulePlugin.utils.parse_command(msg_text)
    cmd_gm = GuimiRulePlugin.utils.parse_gm_command(msg_text)

    # 情况1: .诡秘 后面跟了技能/属性名 → 当作 .gm 检定
    if cmd_attr['is_guimi'] and cmd_attr['error']:
        tail = GuimiRulePlugin.utils.extract_guimi_tail(msg_text)
        if tail:
            cmd_gm = {'is_gm': True, 'target': tail, 'error': None}
            cmd_attr = {'is_guimi': False, 'sub_cmd': None, 'count': 1, 'error': None}

    # 情况2: .gm 后面跟了纯数字 → 当作 .诡秘 属性生成
    if cmd_gm['is_gm'] and cmd_gm['target'] is not None and cmd_gm['target'].isdigit():
        num = int(cmd_gm['target'])
        if num < 1:
            replyMsg(plugin_event, '参数错误')
            return
        if num > GuimiRulePlugin.config.max_generate_count:
            replyMsg(plugin_event, '"你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"')
            return
        cmd_attr = {'is_guimi': True, 'sub_cmd': 'attr', 'count': num, 'error': None}
        cmd_gm = {'is_gm': False, 'target': None, 'error': None}

    # ---- 处理属性生成 ----
    if cmd_attr['is_guimi']:
        if cmd_attr['error']:
            replyMsg(plugin_event, cmd_attr['error'])
            return
        is_v4 = (cmd_attr['sub_cmd'] == 'attr_v4')
        reply_text = GuimiRulePlugin.function.handle_stat_command(
            nick=nick,
            count=cmd_attr['count'],
            is_v4=is_v4,
        )
        replyMsg(plugin_event, reply_text)
        return

    # ---- 处理 .gm 技能/属性检定 ----
    if cmd_gm['is_gm']:
        if cmd_gm['error']:
            replyMsg(plugin_event, cmd_gm['error'])
            return
        # help 指令
        if cmd_gm['target'] and cmd_gm['target'].strip() == 'help':
            help_text = GuimiRulePlugin.msgCustom.dictHelpDocTemp.get(
                '诡秘规则帮助', '暂无帮助信息'
            )
            replyMsg(plugin_event, help_text)
            return
        # 用户未通过 .st temp gm 绑定卡片时的提示
        if pcHash is None:
            replyMsg(
                plugin_event,
                '尚未找到你的角色卡。请先用 .st temp gm 绑定GM模板，再创建角色。'
            )
            return
        try:
            reply_text = GuimiRulePlugin.function.handle_gm_command(
                pcHash=pcHash,
                hagID=hagID,
                target=cmd_gm['target'],
                nick=nick,
            )
            replyMsg(plugin_event, reply_text)
        except Exception as e:
            GuimiRulePlugin.utils.error_log(
                Proc, f'.gm 指令异常: {type(e).__name__}: {e}'
            )
            GuimiRulePlugin.utils.error_log(Proc, traceback.format_exc())
            replyMsg(plugin_event, f'检定失败: {e}')
        return

    # ---- 处理 .sc 理智检定 ----
    cmd_sc = GuimiRulePlugin.utils.parse_sc_command(msg_text)
    if cmd_sc['is_sc']:
        if cmd_sc['error']:
            replyMsg(plugin_event, cmd_sc['error'])
            return
        if pcHash is None:
            replyMsg(
                plugin_event,
                '尚未找到你的角色卡。请先用 .st temp gm 绑定GM模板，再创建角色。'
            )
            return
        try:
            reply_text = GuimiRulePlugin.function.handle_sc_command(
                pcHash=pcHash,
                hagID=hagID,
                nick=nick,
                loss_on_success=cmd_sc['loss_on_success'],
                loss_on_fail=cmd_sc['loss_on_fail'],
            )
            replyMsg(plugin_event, reply_text)
        except Exception as e:
            GuimiRulePlugin.utils.error_log(
                Proc, f'.sc 指令异常: {type(e).__name__}: {e}'
            )
            GuimiRulePlugin.utils.error_log(Proc, traceback.format_exc())
            replyMsg(plugin_event, f'理智检定失败: {e}')
        return
