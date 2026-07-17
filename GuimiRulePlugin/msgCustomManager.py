# -*- encoding: utf-8 -*-
"""
msgCustom.py 的自定义回复管理器。

负责将插件自定义回复注入 OlivaDiceCore 的全局字典中，
使其在 GUI 中可见并可编辑。
"""

import OlivOS
import OlivaDiceCore
import GuimiRulePlugin
import os
import json

has_NativeGUI = False
try:
    import OlivaDiceNativeGUI
    has_NativeGUI = True
except ImportError:
    has_NativeGUI = False


def initMsgCustom(bot_info_dict):
    """在 data_init 时调用，将自定义回复注入全局字典。"""
    for bot_info_dict_this in bot_info_dict:
        if bot_info_dict_this not in OlivaDiceCore.msgCustom.dictStrCustomDict:
            OlivaDiceCore.msgCustom.dictStrCustomDict[bot_info_dict_this] = {}
        for dictStrCustom_this in GuimiRulePlugin.msgCustom.dictStrCustom:
            if dictStrCustom_this not in OlivaDiceCore.msgCustom.dictStrCustomDict[bot_info_dict_this]:
                OlivaDiceCore.msgCustom.dictStrCustomDict[bot_info_dict_this][
                    dictStrCustom_this
                ] = GuimiRulePlugin.msgCustom.dictStrCustom[dictStrCustom_this]
        for dictHelpDoc_this in GuimiRulePlugin.msgCustom.dictHelpDocTemp:
            if dictHelpDoc_this not in OlivaDiceCore.helpDocData.dictHelpDoc[bot_info_dict_this]:
                OlivaDiceCore.helpDocData.dictHelpDoc[bot_info_dict_this][
                    dictHelpDoc_this
                ] = GuimiRulePlugin.msgCustom.dictHelpDocTemp[dictHelpDoc_this]
        if has_NativeGUI:
            for dictStrCustomNote_this in GuimiRulePlugin.msgCustom.dictStrCustomNote:
                if dictStrCustomNote_this not in OlivaDiceNativeGUI.msgCustom.dictStrCustomNote:
                    OlivaDiceNativeGUI.msgCustom.dictStrCustomNote[
                        dictStrCustomNote_this
                    ] = GuimiRulePlugin.msgCustom.dictStrCustomNote[dictStrCustomNote_this]
    OlivaDiceCore.msgCustom.dictStrConst.update(GuimiRulePlugin.msgCustom.dictStrConst)
    OlivaDiceCore.msgCustom.dictGValue.update(GuimiRulePlugin.msgCustom.dictGValue)
    OlivaDiceCore.msgCustom.dictTValue.update(GuimiRulePlugin.msgCustom.dictTValue)
    if has_NativeGUI:
        OlivaDiceNativeGUI.msgCustom.dictStrCustomNote.update(
            GuimiRulePlugin.msgCustom.dictStrCustomNote
        )
