--[[
    诡秘之主 D20 规则插件 for Dice! —— 核心逻辑
    原 OlivOS GuimiRulePlugin v0.1.0 的 Dice! Lua 移植版

    作者: 少年狐 (ShaoNianHu123)
    GitHub: https://github.com/ShaoNianHu123
    QQ: 1690676242

    指令:
      .诡秘 [数量]        属性生成 (2d3, 2~6)
      .诡秘4.0 [数量]     4.0预览属性表
      .gm <技能/属性>     D20 检定
      .gmb <目标>         奖励投 (取高)
      .gmp <目标>         惩罚投 (取低)
      .gmsc [损失骰]      理智检定
      .gmri               先攻检定
      .gm 刷新/.gm 更新   衍生属性刷新

    依赖 Dice! 原生角色卡系统：
      用户需先用 .pc new / .pc tag 绑卡，再 .st 录入属性/技能
]]

-- ============================================================
--  配置数据
-- ============================================================

local CMD_PREFIXES = {".", "。", "/", "／"}

-- 最大生成套数
local MAX_GEN = 10

-- 3.5 版本属性列表 (8项)
local ATTRS_V3 = {
    {name = "力量", var = "str"},
    {name = "体质", var = "con"},
    {name = "敏捷", var = "dex"},
    {name = "魅力", var = "app"},
    {name = "灵感", var = "int"},
    {name = "意志", var = "pow"},
    {name = "教育", var = "edu"},
    {name = "幸运", var = "luck"},
}

-- 4.0 版本属性列表 (9项)
local ATTRS_V4 = {
    {name = "力量", var = "str"},
    {name = "体质", var = "con"},
    {name = "敏捷", var = "dex"},
    {name = "心灵", var = "lingx"},
    {name = "智力", var = "int1"},
    {name = "灵感", var = "int"},
    {name = "精神", var = "app"},
    {name = "意志", var = "pow"},
    {name = "幸运", var = "luck"},
}

-- V3 属性名集合（用于判断是否为纯属性检定）
local V3_ATTR_NAMES = {}
for _, a in ipairs(ATTRS_V3) do
    V3_ATTR_NAMES[a.name] = true
end

-- 技能 → 关联属性映射
local SKILL_ATTR_MAP = {
    -- 力量相关
    ["攀爬"] = "力量", ["跳跃"] = "力量", ["格斗"] = "力量",
    ["肉搏"] = "力量", ["刀剑"] = "力量", ["长柄武器"] = "力量",
    ["巨型武器"] = "力量", ["特种武器"] = "力量", ["投掷"] = "力量",
    ["恐吓"] = "力量", ["驯兽"] = "力量",
    -- 敏捷相关
    ["潜行"] = "敏捷", ["隐匿"] = "敏捷", ["妙手"] = "敏捷",
    ["巧手"] = "敏捷", ["偷窃"] = "敏捷", ["游泳"] = "敏捷",
    ["锁匠"] = "敏捷", ["射击"] = "敏捷", ["手枪"] = "敏捷",
    ["步枪"] = "敏捷", ["猎枪"] = "敏捷", ["机枪"] = "敏捷",
    ["弓箭"] = "敏捷", ["弩"] = "敏捷", ["闪避"] = "敏捷",
    ["驾驶"] = "敏捷", ["骑乘"] = "敏捷",
    -- 魅力相关
    ["取悦"] = "魅力", ["信誉"] = "魅力", ["欺骗"] = "魅力",
    ["说服"] = "魅力", ["挑衅"] = "魅力", ["心理学"] = "魅力",
    ["心理引导"] = "魅力", ["表演"] = "魅力", ["乔装"] = "魅力",
    -- 灵感相关
    ["聆听"] = "灵感", ["侦查"] = "灵感", ["搜索"] = "灵感",
    ["读唇"] = "灵感", ["追踪"] = "灵感", ["机械维修"] = "灵感",
    ["贸易"] = "灵感", ["厨艺"] = "灵感", ["乐理"] = "灵感",
    ["歌唱"] = "灵感", ["工艺制造"] = "灵感", ["神秘学"] = "灵感",
    ["占卜"] = "灵感", ["通灵"] = "灵感", ["星象学"] = "灵感",
    ["仪式魔法"] = "灵感", ["宗教"] = "灵感", ["非凡之物学"] = "灵感",
    ["神秘历史学"] = "灵感", ["非凡学识"] = "灵感",
    -- 教育相关
    ["图书馆使用"] = "教育", ["领航"] = "教育", ["生存"] = "教育",
    ["医学"] = "教育", ["写作"] = "教育", ["爆破"] = "教育",
    ["法律"] = "教育", ["潜水"] = "教育", ["考古"] = "教育",
    ["现实学识"] = "教育", ["化学"] = "教育", ["药学"] = "教育",
    ["社会学"] = "教育", ["植物学"] = "教育", ["农业"] = "教育",
    ["天文学"] = "教育", ["历史"] = "教育", ["工程学"] = "教育",
    ["博物学"] = "教育", ["生物学"] = "教育", ["科学"] = "教育",
    -- 语言类 (教育)
    ["鲁恩语"] = "教育", ["因蒂斯语"] = "教育", ["弗萨克语"] = "教育",
    ["高原语"] = "教育", ["伦堡语"] = "教育", ["古弗萨克语"] = "教育",
    ["都坦语"] = "教育", ["高地语"] = "教育", ["旧日语言"] = "教育",
    -- 神秘学语言 (灵感)
    ["赫密斯语"] = "灵感", ["古赫密斯语"] = "灵感", ["巨人语"] = "灵感",
    ["巨龙语"] = "灵感", ["精灵语"] = "灵感",
}

-- 属性中英文别名
local ATTR_ALIASES = {
    ["力量"] = {"力量", "str", "STR"},
    ["体质"] = {"体质", "con", "CON"},
    ["敏捷"] = {"敏捷", "dex", "DEX"},
    ["魅力"] = {"魅力", "app", "APP"},
    ["灵感"] = {"灵感", "int", "INT"},
    ["意志"] = {"意志", "pow", "POW"},
    ["教育"] = {"教育", "edu", "EDU"},
    ["幸运"] = {"幸运", "luck", "LUCK"},
}

-- 理智相关属性名
local SAN_NAMES = {"理智", "san", "SAN", "sanity"}

-- 技能等级加值 (0-based)
local SKILL_LEVELS = {
    {bonus = -4, name = "未受训"},
    {bonus =  0, name = "受训"},
    {bonus =  2, name = "熟练"},
    {bonus =  4, name = "进阶"},
    {bonus =  6, name = "精通"},
    {bonus =  8, name = "博学"},
    {bonus = 10, name = "大师"},
}

-- ============================================================
--  帮助文本
-- ============================================================

local HELP_TEXT = [[【诡秘之主D20规则 - 帮助】
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
.gmri                先攻检定（rd20 + 敏捷）

—— Dice! 角色卡录入指令 ——
.pc new <卡名>           新建角色卡（如 .pc new 克莱恩）
.pc tag <卡名>           绑定本群使用的角色卡
.st <属性名> <值>        录入属性值到当前绑卡
.st <技能名> <值>        录入技能等级(0~6)
例：
  .pc new 克莱恩
  .pc tag 克莱恩
  .st 力量 5
  .st 格斗 2
  .st 序列 9
  .st 消化 12
  .gm 格斗               ← 开始检定！
]]

-- ============================================================
--  工具函数
-- ============================================================

-- 模拟 2d3 掷骰
local function roll_stat()
    return ranint(1, 3) + ranint(1, 3)
end

-- 字符串 trim
local function trim(s)
    if not s then return "" end
    return (string.gsub(s, "^%s*(.-)%s*$", "%1"))
end

-- 判断 s 是否以 prefix 开头
local function starts_with(s, prefix)
    return string.sub(s, 1, #prefix) == prefix
end

-- 拆分命令前缀（. / 。 / / 等）
local function strip_cmd_prefix(text)
    for _, p in ipairs(CMD_PREFIXES) do
        if starts_with(text, p) then
            return p, string.sub(text, #p + 1)
        end
    end
    return nil, text
end

-- 从 Dice! 角色卡读取属性值（尝试中英文别名）
local function get_card_attr(gid, userID, stat_name)
    local aliases = ATTR_ALIASES[stat_name]
    if not aliases then
        local val = getPlayerCardAttr(userID, gid, stat_name, 0)
        if val and val ~= 0 then return val end
        return 0
    end
    for _, alias in ipairs(aliases) do
        local val = getPlayerCardAttr(userID, gid, alias, 0)
        if val and val ~= 0 then return val end
    end
    return 0
end

-- 从 Dice! 角色卡读取技能等级
local function get_card_skill(gid, userID, skill_name)
    local val = getPlayerCardAttr(userID, gid, skill_name, 0)
    if val then return val end
    return 0
end

-- 从 Dice! 角色卡读取理智值
local function get_card_san(gid, userID)
    for _, san_name in ipairs(SAN_NAMES) do
        local val = getPlayerCardAttr(userID, gid, san_name, 0)
        if val and val ~= 0 then return val end
    end
    -- 回退：理智 = 10 + 意志
    local will = get_card_attr(gid, userID, "意志")
    if will > 0 then return 10 + will end
    return 10
end

-- 解析技能等级 → (等级名, 加值)
local function parse_skill_level(skill_value)
    if not skill_value or skill_value < 0 then skill_value = 0 end
    if skill_value > 6 then skill_value = 6 end
    local lv = SKILL_LEVELS[skill_value + 1]
    return lv.name, lv.bonus
end

-- ============================================================
--  命令解析
-- ============================================================

-- 解析 .诡秘 命令尾部
local function parse_guimi(tail)
    tail = trim(tail)
    local result = {is_guimi = true, sub_cmd = "attr", count = 1, error = nil, tail_for_gm = nil}

    if tail == "" or tail == "3.0" or tail == "3.5" then
        result.sub_cmd = "attr"
        result.count = 1
        return result
    end

    if tail == "4.0" then
        result.sub_cmd = "attr_v4"
        result.count = 1
        return result
    end

    -- 纯数字后缀
    local num = tonumber(tail)
    if num then
        if num < 1 then
            result.error = "参数错误"
            return result
        end
        if num > MAX_GEN then
            result.error = '"你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"'
            return result
        end
        result.count = num
        return result
    end

    -- 版本号前缀
    if starts_with(tail, "4.0") then
        result.sub_cmd = "attr_v4"
        local after = trim(string.sub(tail, 4))
        local anum = tonumber(after)
        if after == "" then
            result.count = 1
        elseif anum then
            if anum < 1 then result.error = "参数错误"
            elseif anum > MAX_GEN then result.error = '"你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"'
            else result.count = anum end
        else
            result.tail_for_gm = tail
        end
        return result
    end

    if starts_with(tail, "3.0") or starts_with(tail, "3.5") then
        result.sub_cmd = "attr"
        local after = trim(string.sub(tail, 4))
        local anum = tonumber(after)
        if after == "" then
            result.count = 1
        elseif anum then
            if anum < 1 then result.error = "参数错误"
            elseif anum > MAX_GEN then result.error = '"你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"'
            else result.count = anum end
        else
            result.tail_for_gm = tail
        end
        return result
    end

    -- 非数字非版本号 → 交给 gm 路由
    result.tail_for_gm = tail
    return result
end

-- 解析 .gm 家族命令
local function parse_gm(rest)
    local cmd_type = "gm"
    local after = rest

    if starts_with(rest, "gmsc") or starts_with(rest, "GMSC") then
        cmd_type = "gmsc"
        after = trim(string.sub(rest, 5))
    elseif starts_with(rest, "gmri") or starts_with(rest, "GMRI") then
        cmd_type = "gmri"
        after = trim(string.sub(rest, 5))
    elseif starts_with(rest, "gmb") or starts_with(rest, "GMB") then
        cmd_type = "gmb"
        after = trim(string.sub(rest, 4))
    elseif starts_with(rest, "gmp") or starts_with(rest, "GMP") then
        cmd_type = "gmp"
        after = trim(string.sub(rest, 4))
    elseif starts_with(rest, "gm") or starts_with(rest, "GM") then
        cmd_type = "gm"
        after = trim(string.sub(rest, 3))
    end

    local result = {cmd_type = cmd_type, target = nil, error = nil, roll_mode = nil,
                    sc_success = nil, sc_fail = nil}

    if cmd_type == "gmri" then
        return result
    end

    if cmd_type == "gmb" then
        result.roll_mode = "adv"
        if after == "" then
            result.error = "请指定技能或属性名称，如 .gmb力量"
            return result
        end
        result.target = after
        return result
    end

    if cmd_type == "gmp" then
        result.roll_mode = "dis"
        if after == "" then
            result.error = "请指定技能或属性名称，如 .gmp力量"
            return result
        end
        result.target = after
        return result
    end

    if cmd_type == "gmsc" then
        if after ~= "" then
            local parts = {}
            for part in string.gmatch(after, "[^/%s]+") do
                table.insert(parts, part)
            end
            if #parts >= 1 then result.sc_success = parts[1] end
            if #parts >= 2 then result.sc_fail = parts[2] end
        end
        return result
    end

    -- cmd_type == "gm"
    if after == "" then
        result.error = "请指定技能或属性名称，如 .gm力量 或 .gm格斗"
        return result
    end

    if string.lower(after) == "help" then
        result.cmd_type = "help"
        return result
    end

    if after == "刷新" or after == "更新" then
        result.cmd_type = "refresh"
        return result
    end

    -- 中文前置: 优势/劣势
    if starts_with(after, "优势") then
        local tail = trim(string.sub(after, 7))
        if tail ~= "" then
            result.roll_mode = "adv"
            result.target = tail
            return result
        end
    end
    if starts_with(after, "劣势") then
        local tail = trim(string.sub(after, 7))
        if tail ~= "" then
            result.roll_mode = "dis"
            result.target = tail
            return result
        end
    end

    result.target = after
    return result
end

-- 解析 .gm 目标中的手动加值/改判/优劣势后缀
local function parse_manual_modifier(raw_target)
    if not raw_target or raw_target == "" then
        return raw_target, nil, nil, nil, nil
    end

    local override_attr = nil
    local roll_mode = nil
    local target = raw_target

    -- 提取尾部 adv/dis/优势/劣势
    local function extract_roll_mode(t, keyword, mode)
        local len = #keyword
        if #t >= len + 1 and string.sub(t, -len) == keyword
           and string.sub(t, -(len + 1), -(len + 1)) == " " then
            return trim(string.sub(t, 1, -(len + 2))), mode
        end
        return nil, nil
    end

    local new_target, rm
    new_target, rm = extract_roll_mode(target, "adv", "adv")
    if new_target then target = new_target; roll_mode = rm end
    if not roll_mode then
        new_target, rm = extract_roll_mode(target, "dis", "dis")
        if new_target then target = new_target; roll_mode = rm end
    end
    if not roll_mode then
        new_target, rm = extract_roll_mode(target, "优势", "adv")
        if new_target then target = new_target; roll_mode = rm end
    end
    if not roll_mode then
        new_target, rm = extract_roll_mode(target, "劣势", "dis")
        if new_target then target = new_target; roll_mode = rm end
    end

    -- 提取 /属性 后缀（改判）
    local slash_pos = string.find(target, "/")
    if slash_pos then
        override_attr = trim(string.sub(target, slash_pos + 1))
        target = trim(string.sub(target, 1, slash_pos - 1))
    end

    -- 匹配 +/- 数字序列
    local sign_start, sign_end = string.find(target, "[%+%-]%d+")
    if sign_start then
        local mod_str = string.sub(target, sign_start)
        local total_mod = 0
        for num_str in string.gmatch(mod_str, "[%+%-]%d+") do
            total_mod = total_mod + tonumber(num_str)
        end
        local clean = trim(string.sub(target, 1, sign_start - 1))
        if clean ~= "" then
            return clean, total_mod, "adjust", override_attr, roll_mode
        end
    end

    -- 匹配纯数字后缀
    local digit_start, digit_end = string.find(target, "%d+$")
    if digit_start then
        local num = tonumber(string.sub(target, digit_start, digit_end))
        local clean = trim(string.sub(target, 1, digit_start - 1))
        if clean ~= "" then
            return clean, num, "absolute", override_attr, roll_mode
        end
    end

    return target, nil, nil, override_attr, roll_mode
end

-- ============================================================
--  属性生成
-- ============================================================

local function generate_attrs()
    local stats = {}
    stats["str"] = roll_stat()
    stats["con"] = roll_stat()
    stats["dex"] = roll_stat()
    stats["app"] = roll_stat()
    stats["int"] = roll_stat()
    stats["pow"] = roll_stat()
    stats["edu"] = roll_stat()
    stats["luck"] = roll_stat()
    stats["lingx"] = roll_stat()
    stats["int1"] = roll_stat()
    return stats
end

local function format_attrs(stats, is_v4)
    local attrs = is_v4 and ATTRS_V4 or ATTRS_V3
    local total_all = 0
    local total_no_luck = 0
    local vals = {}
    for _, attr in ipairs(attrs) do
        local val = stats[attr.var] or 0
        total_all = total_all + val
        if attr.var ~= "luck" then
            total_no_luck = total_no_luck + val
        end
        table.insert(vals, attr.name .. ":" .. val)
    end

    local lines = {}
    for i = 1, #vals, 3 do
        local buf = {}
        for j = 0, 2 do
            if i + j <= #vals then
                table.insert(buf, vals[i + j])
            end
        end
        table.insert(lines, table.concat(buf, " "))
    end
    table.insert(lines, "［" .. total_no_luck .. "/" .. total_all .. "］")

    local result = table.concat(lines, "\n")
    if is_v4 then
        result = result .. "\n\n（4.0属性为测试内容，非最终版本）"
    end
    return result
end

-- .诡秘 入口
local function handle_guimi(msg, tail)
    local parsed = parse_guimi(tail)

    if parsed.tail_for_gm then
        return handle_gm_check(msg, parsed.tail_for_gm, nil)
    end

    if parsed.error then return parsed.error end

    -- 昵称：优先 Dice! 角色卡姓名，其次用户昵称，最后 QQ 号
    local userID = msg.fromQQ
    local nick = getUserConf(userID, "nick", nil)
    if not nick then nick = tostring(userID) end
    local is_v4 = (parsed.sub_cmd == "attr_v4")

    local title = "<" .. nick .. ">命运的馈赠在暗处已标注好了价码："

    for _ = 1, parsed.count do
        local stats = generate_attrs()
        title = title .. "\n\n" .. format_attrs(stats, is_v4)
    end

    return title
end

-- ============================================================
--  D20 检定
-- ============================================================

local function fuzzy_match(target)
    if V3_ATTR_NAMES[target] then return target, true end
    if SKILL_ATTR_MAP[target] then return target, false end

    for skill_name, _ in pairs(SKILL_ATTR_MAP) do
        if starts_with(skill_name, target) then
            return skill_name, false
        end
    end
    for _, attr in ipairs(ATTRS_V3) do
        if starts_with(attr.name, target) then return attr.name, true end
    end
    for _, attr in ipairs(ATTRS_V4) do
        if starts_with(attr.name, target) then return attr.name, true end
    end

    return target, false
end

-- D20 检定核心（从 Dice! 角色卡读取属性/技能）
local function perform_d20_check(gid, userID, target, nick, extra_attr, extra_skill,
                                  absolute_attr, absolute_skill, override_attr, roll_mode)
    -- 奖励投/惩罚投
    local d20, roll_tag
    if roll_mode == "adv" then
        local d1, d2 = ranint(1, 20), ranint(1, 20)
        d20 = math.max(d1, d2)
        roll_tag = "【奖励投】" .. d1 .. "/" .. d2 .. "→取高→" .. d20
    elseif roll_mode == "dis" then
        local d1, d2 = ranint(1, 20), ranint(1, 20)
        d20 = math.min(d1, d2)
        roll_tag = "【惩罚投】" .. d1 .. "/" .. d2 .. "→取低→" .. d20
    else
        d20 = ranint(1, 20)
        roll_tag = nil
    end

    local is_skill = not V3_ATTR_NAMES[target]
    local linked_attr_name = override_attr or SKILL_ATTR_MAP[target] or "力量"

    -- 从 Dice! 角色卡读取属性
    local card_attr = get_card_attr(gid, userID, linked_attr_name)

    local attr_val, attr_display
    if absolute_attr then
        attr_val = absolute_attr
        attr_display = linked_attr_name .. "(" .. attr_val .. " 手动指定)"
    else
        local extra_a = extra_attr or 0
        attr_val = card_attr + extra_a
        if extra_a ~= 0 then
            attr_display = linked_attr_name .. "(卡片" .. card_attr .. " + 调整" .. string.format("%+d", extra_a) .. ")"
        else
            attr_display = linked_attr_name .. "(" .. card_attr .. ")"
        end
    end

    local has_manual = (absolute_attr or absolute_skill or extra_attr or extra_skill)
    local lines = {}
    local tags = {}
    if has_manual then table.insert(tags, "【手动】") end
    if roll_tag then table.insert(tags, roll_tag) end
    local tag_str = table.concat(tags, " ")
    table.insert(lines, "<" .. nick .. ">对【" .. target .. "】进行检定：" .. tag_str)

    local bonus = attr_val
    local skill_info = ""
    local skill_bonus = 0

    if is_skill then
        -- 从 Dice! 角色卡读取技能等级
        local card_skill = get_card_skill(gid, userID, target)
        local level_name, card_skill_bonus = parse_skill_level(card_skill)

        if absolute_skill then
            local lv_name, sk_bonus = parse_skill_level(absolute_skill)
            skill_bonus = sk_bonus
            skill_info = " + 技能" .. target .. "(手动指定 等级" .. absolute_skill .. " " .. lv_name .. ":" .. string.format("%+d", sk_bonus) .. ")"
        else
            local extra_s = extra_skill or 0
            skill_bonus = card_skill_bonus + extra_s
            if extra_s ~= 0 then
                skill_info = " + 技能" .. target .. "(卡片" .. level_name .. ":" .. string.format("%+d", card_skill_bonus) .. " + 调整" .. string.format("%+d", extra_s) .. ")"
            else
                skill_info = " + 技能" .. target .. "(" .. level_name .. ":" .. string.format("%+d", skill_bonus) .. ")"
            end
        end

        bonus = attr_val + skill_bonus
        table.insert(lines, "rd20(" .. d20 .. ") + " .. attr_display .. skill_info)
    else
        table.insert(lines, "rd20(" .. d20 .. ") + " .. attr_display)
    end

    local total = d20 + bonus
    local is_crit_success = (d20 == 20)
    local is_crit_fail = (d20 == 1)

    table.insert(lines, "= " .. total)

    if is_crit_success then
        table.insert(lines, "『大成功！』命运的眷顾降临于你。")
    elseif is_crit_fail then
        table.insert(lines, "『大失败！』命运对你露出了恶意的微笑。")
    else
        table.insert(lines, "检定结果: " .. total)
    end

    local skill_summary = ""
    if is_skill then
        skill_summary = "+技能(" .. skill_bonus .. ")"
    end
    table.insert(lines, "（对抗时以此值比较：" .. d20 .. "+" .. attr_val .. skill_summary .. "=" .. total .. "）")

    return table.concat(lines, "\n")
end

-- .gm 检定入口
local function handle_gm_check(msg, raw_target, external_roll_mode)
    if not raw_target or raw_target == "" then
        return "请指定技能或属性名称，如 .gm力量 或 .gm格斗"
    end

    local gid = msg.fromGroup
    local userID = msg.fromQQ

    local clean_target, manual_mod, mod_mode, override_attr, parsed_roll_mode =
        parse_manual_modifier(raw_target)

    if external_roll_mode then
        parsed_roll_mode = external_roll_mode
    end

    if not clean_target then
        clean_target = raw_target
        manual_mod = nil; mod_mode = nil; override_attr = nil
    end

    local nick = getUserConf(userID, "nick", nil) or tostring(userID)
    local final_target, is_attr = fuzzy_match(clean_target)
    local is_skill = not is_attr

    if manual_mod then
        if mod_mode == "absolute" then
            if is_skill then
                return perform_d20_check(gid, userID, final_target, nick,
                    nil, nil, nil, manual_mod, override_attr, parsed_roll_mode)
            else
                return perform_d20_check(gid, userID, final_target, nick,
                    nil, nil, manual_mod, nil, override_attr, parsed_roll_mode)
            end
        else
            if is_skill then
                return perform_d20_check(gid, userID, final_target, nick,
                    nil, manual_mod, nil, nil, override_attr, parsed_roll_mode)
            else
                return perform_d20_check(gid, userID, final_target, nick,
                    manual_mod, nil, nil, nil, override_attr, parsed_roll_mode)
            end
        end
    else
        return perform_d20_check(gid, userID, final_target, nick,
            nil, nil, nil, nil, override_attr, parsed_roll_mode)
    end
end

-- ============================================================
--  理智检定 (SC)
-- ============================================================

local function roll_dice_expr(expr)
    if not expr or expr == "" then return 1, 2, 1 end
    expr = string.lower(trim(expr))
    local count, sides = string.match(expr, "^(%d*)[dD](%d+)$")
    if sides then
        count = (count == "" or not count) and 1 or tonumber(count)
        sides = tonumber(sides)
        local total = 0
        for _ = 1, count do
            total = total + ranint(1, sides)
        end
        return count, sides, total
    end
    local num = tonumber(expr)
    if num then return 1, 1, num end
    return 1, 2, 1
end

local function handle_sc(msg, sc_success, sc_fail)
    local gid = msg.fromGroup
    local userID = msg.fromQQ
    local current_san = get_card_san(gid, userID)
    local d20 = ranint(1, 20)
    local success = (d20 <= current_san)

    if not sc_success then sc_success = "1" end
    if not sc_fail then sc_fail = "1d2" end

    local nick = getUserConf(userID, "nick", nil) or tostring(userID)

    local lines = {}
    table.insert(lines, "<" .. nick .. ">进行理智检定：")
    table.insert(lines, "rd20(" .. d20 .. ") vs 理智(" .. current_san .. ")")

    local loss_expr, loss
    if success then
        table.insert(lines, d20 .. " ≤ " .. current_san .. "，【理智检定成功】")
        loss_expr = sc_success
        _, _, loss = roll_dice_expr(sc_success)
    else
        table.insert(lines, d20 .. " > " .. current_san .. "，【理智检定失败】")
        loss_expr = sc_fail
        _, _, loss = roll_dice_expr(sc_fail)
    end

    table.insert(lines, "损失理智: " .. loss_expr .. " = " .. loss)
    local new_san = math.max(0, current_san - loss)
    table.insert(lines, "理智变化: " .. current_san .. " → " .. new_san)

    if new_san <= 0 and current_san > 0 then
        table.insert(lines, "☠ 理智归零，你已【失控】！")
    elseif new_san <= 2 and current_san > 2 then
        table.insert(lines, "⚠⚠ 你已陷入【真疯】状态，难以沟通。")
    elseif new_san <= 8 and current_san > 8 then
        table.insert(lines, "⚠ 你已陷入【半疯】状态，获得随机疯狂倾向。")
    end

    return table.concat(lines, "\n")
end

-- ============================================================
--  衍生属性刷新
-- ============================================================

local function handle_refresh(msg)
    local gid = msg.fromGroup
    local userID = msg.fromQQ
    local nick = getUserConf(userID, "nick", nil) or tostring(userID)

    -- 从 Dice! 角色卡读取序列/消化/属性
    local seq_raw = getPlayerCardAttr(userID, gid, "序列", nil)
    local digest = getPlayerCardAttr(userID, gid, "消化", 0) or 0
    local con = get_card_attr(gid, userID, "体质")
    local pow_val = get_card_attr(gid, userID, "意志")
    local int_val = get_card_attr(gid, userID, "灵感")

    -- 序列加成：序列9→1倍, 序列8→2倍, ..., 序列0→10倍
    local seq_mult = 0
    if seq_raw then seq_mult = 10 - seq_raw end
    local digest_bonus = math.floor(digest / 5)

    local hp_new = 10 + con + seq_mult * con + digest_bonus
    local mp_new = pow_val + int_val + seq_mult * int_val + digest_bonus
    local san_new = 10 + pow_val

    -- 写回 Dice! 角色卡
    setPlayerCardAttr(userID, gid, "生命", hp_new)
    setPlayerCardAttr(userID, gid, "灵性", mp_new)
    setPlayerCardAttr(userID, gid, "理智", san_new)

    local seq_info
    if seq_raw then
        seq_info = "序列" .. seq_raw .. "（" .. seq_mult .. "倍）"
    else
        seq_info = "无序列"
    end

    return "<" .. nick .. "> " .. seq_info .. "  消化" .. digest .. "（+" .. digest_bonus .. "）\n"
        .. "生命→" .. hp_new .. "  灵性→" .. mp_new .. "  理智→" .. san_new .. "  已更新"
end

-- ============================================================
--  先攻检定
-- ============================================================

local function handle_ri(msg)
    local gid = msg.fromGroup
    local userID = msg.fromQQ
    local nick = getUserConf(userID, "nick", nil) or tostring(userID)
    local d20 = ranint(1, 20)
    local dex = get_card_attr(gid, userID, "敏捷")
    local total = d20 + dex

    -- 存入群配置（简易先攻列表）
    if gid and gid ~= "0" then
        setGroupConf(gid, "guimi_init_" .. userID, nick .. "=" .. total)
    end

    return "<" .. nick .. ">先攻检定：rd20(" .. d20 .. ") + 敏捷(" .. dex .. ") = " .. total .. "  已加入先攻列表"
end

-- ============================================================
--  主入口
-- ============================================================

local text = msg.fromMsg
local cmd_prefix, rest = strip_cmd_prefix(text)

if not cmd_prefix or rest == "" then
    return ""
end

-- 判断命令类型并分发
if starts_with(rest, "诡秘") then
    local tail = string.sub(rest, 7)
    return handle_guimi(msg, tail)
end

if starts_with(rest, "gm") or starts_with(rest, "GM") then
    local parsed = parse_gm(rest)

    if parsed.cmd_type == "help" then
        return HELP_TEXT
    elseif parsed.cmd_type == "refresh" then
        return handle_refresh(msg)
    elseif parsed.cmd_type == "gmri" then
        return handle_ri(msg)
    elseif parsed.cmd_type == "gmsc" then
        return handle_sc(msg, parsed.sc_success, parsed.sc_fail)
    elseif parsed.cmd_type == "gmb" or parsed.cmd_type == "gmp" then
        if parsed.error then return parsed.error end
        if parsed.target and tonumber(parsed.target) then
            local num = tonumber(parsed.target)
            if num < 1 then return "参数错误" end
            if num > MAX_GEN then
                return '"你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"'
            end
            return handle_guimi(msg, tostring(num))
        end
        return handle_gm_check(msg, parsed.target, parsed.roll_mode)
    elseif parsed.cmd_type == "gm" then
        if parsed.error then return parsed.error end
        if parsed.target and tonumber(parsed.target) then
            local num = tonumber(parsed.target)
            if num < 1 then return "参数错误" end
            if num > MAX_GEN then
                return '"你应该去向伟大的宿命之环祈祷，这要观察的【命运】也太多了，我没这么大能耐。"'
            end
            return handle_guimi(msg, tostring(num))
        end
        return handle_gm_check(msg, parsed.target, parsed.roll_mode)
    end
end

return ""
