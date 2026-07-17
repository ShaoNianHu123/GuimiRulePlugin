# -*- encoding: utf-8 -*-
"""
诡秘规则插件——OlivOS 事件入口模块。

基于 OlivaDiceCore 规则插件模板，负责将 OlivOS 事件
路由到 msgReply.py 中对应的处理函数。
"""

import OlivOS
import GuimiRulePlugin
import OlivaDiceCore


class Event(object):
    """OlivOS 标准事件类。"""

    def init(plugin_event, Proc):
        """插件初始化——加载配置。"""
        GuimiRulePlugin.msgReply.unity_init(plugin_event, Proc)

    def init_after(plugin_event, Proc):
        """所有插件初始化完成后——注入自定义回复数据。"""
        GuimiRulePlugin.msgReply.data_init(plugin_event, Proc)

    def private_message(plugin_event, Proc):
        """私聊消息处理。"""
        GuimiRulePlugin.msgReply.unity_reply(plugin_event, Proc)

    def group_message(plugin_event, Proc):
        """群聊消息处理。"""
        GuimiRulePlugin.msgReply.unity_reply(plugin_event, Proc)

    def poke(plugin_event, Proc):
        """戳一戳事件——暂不处理。"""
        pass

    def menu(plugin_event, Proc):
        """菜单事件——暂不处理。"""
        pass
