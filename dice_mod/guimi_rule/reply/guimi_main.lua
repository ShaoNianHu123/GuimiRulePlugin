--[[
    诡秘之主 D20 规则插件 for Dice! —— Reply 路由注册
    原 OlivOS GuimiRulePlugin v0.1.0 的 Dice! Lua 移植版

    作者: 少年狐 (ShaoNianHu123)
    GitHub: https://github.com/ShaoNianHu123
    QQ: 1690676242
]]

-- .诡秘 属性生成
reply.guimi_attr = {
    type = "Order",
    title = "诡秘属性生成",
    keyword = { prefix = "诡秘" },
    echo = { lua = "guimi_main" }
}

-- .gm 家族指令（gm/gmb/gmp/gmsc/gmri）
-- 注册从最具体到最通用，Dice! 应匹最长的前缀
reply.guimi_gm = {
    type = "Order",
    title = "诡秘GM检定",
    keyword = { prefix = {"gmsc", "gmri", "gmb", "gmp", "gm"} },
    echo = { lua = "guimi_main" }
}
