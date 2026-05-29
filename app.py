import os
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

# ===================== 【价格配置区 - 后期改价只改这里】 =====================
# 格式说明：
# 空运类：首重(0.5kg价格)、续重(0.5kg价格)、体积除数、时效、是否11kg免首重
# 海运/卡航类：单价(元/kg)、起运重量、时效

# 美国
USA_AIR_SENS = {"first": 148, "add": 54, "div": 6000, "time": "7-14工作日", "free_first": True}
USA_SEA_NORMAL = {"price": 28, "min_w": 12, "time": "海运普货，时效另行咨询"}
USA_SEA_FAST = {"price": 35, "min_w": 12, "time": "海运快船，时效另行咨询"}
USA_SEA_SENS = {"price": 38, "min_w": 12, "time": "海运敏快船，时效另行咨询"}

# 英国
UK_AIR_SENS = {"first": 65, "add": 36, "div": 6000, "time": "10-15工作日", "free_first": True}

# 加拿大
CA_AIR = {"first": 108, "add": 35, "div": 6000, "time": "10-15工作日", "free_first": True}
CA_SEA = {"price": 36, "min_w": 12, "div": 6000, "time": "30-55工作日"}

# 澳大利亚
AU_AIR = {"first": 88, "add": 32, "div": 7000, "time": "7-14工作日", "free_first": False}

# 新西兰
NZ_AIR = {"first": 118, "add": 43, "div": 6000, "time": "7-15工作日", "free_first": True}

# 瑞士 EMS
CH_EMS = {"first": 138, "add": 42, "div": 6000, "time": "7-20工作日", "free_first": False}

# 欧洲卡航包税(15KG起)
EU_GROUP1 = {"price": 39, "min_w": 15, "time": "29-39工作日"}    # 德/法/意/西
EU_GROUP2 = {"price": 41.5, "min_w": 15, "time": "29-39工作日"}  # 波/捷/丹/荷/比/奥/卢
EU_GROUP3 = {"price": 42.5, "min_w": 15, "time": "29-39工作日"} # 克/斯伐/斯文
EU_GROUP4 = {"price": 44.5, "min_w": 15, "time": "29-39工作日"} # 芬/摩/瑞/保/爱/拉/立/匈
EU_GROUP5 = {"price": 45.5, "min_w": 15, "time": "29-39工作日"} # 希/爱/葡

# 欧洲各国空运敏感专线 / DHL
HR_DHL = {"first": 136, "add": 42, "div": 6000, "time": "7-14工作日", "free_first": True}
BE_AIR = {"first": 125, "add": 37, "div": 6000, "time": "7-14工作日", "free_first": True}
NL_AIR = {"first": 125, "add": 40, "div": 6000, "time": "7-15工作日", "free_first": True}
LU_AIR = {"first": 125, "add": 38, "div": 6000, "time": "7-12工作日", "free_first": True}
PL_AIR = {"first": 125, "add": 37, "div": 6000, "time": "7-15工作日", "free_first": True}
DE_AIR = {"first": 125, "add": 38, "div": 6000, "time": "7-14工作日", "free_first": True}
CZ_AIR = {"first": 125, "add": 38, "div": 6000, "time": "7-14工作日", "free_first": True}
FR_AIR = {"first": 136, "add": 39, "div": 6000, "time": "10-15工作日", "free_first": True}
AT_AIR = {"first": 136, "add": 38, "div": 6000, "time": "7-15工作日", "free_first": True}
IE_AIR = {"first": 136, "add": 41, "div": 6000, "time": "7-15工作日", "free_first": True}
HU_AIR = {"first": 125, "add": 40, "div": 6000, "time": "10-15工作日", "free_first": True}
ES_AIR = {"first": 136, "add": 39, "div": 6000, "time": "10-15工作日", "free_first": True}
IT_AIR = {"first": 136, "add": 41, "div": 6000, "time": "7-15工作日", "free_first": True}
SE_AIR = {"first": 178, "add": 40, "div": 6000, "time": "7-15工作日", "free_first": True}
SI_AIR = {"first": 125, "add": 37, "div": 6000, "time": "7-14工作日", "free_first": True}
PT_AIR = {"first": 136, "add": 40, "div": 6000, "time": "7-15工作日", "free_first": True}
DK_AIR = {"first": 155, "add": 40, "div": 6000, "time": "10-15工作日", "free_first": True}
LV_AIR = {"first": 145, "add": 41, "div": 6000, "time": "7-14工作日", "free_first": True}
EE_AIR = {"first": 145, "add": 42, "div": 6000, "time": "7-15工作日", "free_first": True}
FI_AIR = {"first": 175, "add": 47, "div": 6000, "time": "10-15工作日", "free_first": True}
BG_AIR = {"first": 136, "add": 40, "div": 6000, "time": "7-14工作日", "free_first": True}
RO_AIR = {"first": 155, "add": 43, "div": 6000, "time": "7-12工作日", "free_first": True}

# 马耳他 DHL
MT_DHL = {"first": 208, "add": 53, "div": 6000, "time": "7-14工作日", "free_first": True}
# 塞浦路斯 DHL
CY_DHL = {"first": 238, "add": 59, "div": 6000, "time": "7-14工作日", "free_first": True}
# 希腊专线
GR_NORMAL = {"first": 136, "add": 33, "over11": 68, "div": 6000, "time": "7-15工作日"}
GR_SENS = {"first": 136, "add": 43, "over11": 80, "div": 6000, "time": "7-14工作日"}
# =============================================================================

# 数据库连接
def get_db_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# 底部常驻菜单
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📦 运费查询"), KeyboardButton("🎁 优惠码")],
            [KeyboardButton("ℹ️ 关于我们"), KeyboardButton("📞 联系客服")],
            [KeyboardButton("❓ 帮助")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# 计算空运类价格（首重+续重、免首重、体积重）
def calc_air_price(weight, l, w, h, rule):
    vol_weight = (l * w * h) / rule["div"]
    calc_w = max(weight, vol_weight)
    half_kg = calc_w / 0.5
    if rule["free_first"] and calc_w >= 11:
        total = rule["add"] * (half_kg - 1)
    else:
        total = rule["first"] + rule["add"] * (half_kg - 1)
    return round(total, 2), rule["time"]

# 计算海运/卡航（按kg单价、起运重）
def calc_sea_kahang(weight, rule):
    if weight < rule["min_w"]:
        return -1, f"该线路最低起运重量：{rule['min_w']}KG"
    total = round(weight * rule["price"], 2)
    return total, rule["time"]

# 希腊专属计算
def calc_greece(weight, l, w, h, rule):
    vol_weight = (l * w * h) / rule["div"]
    calc_w = max(weight, vol_weight)
    if calc_w >= 11:
        total = round(calc_w * rule["over11"], 2)
    else:
        half = calc_w / 0.5
        total = rule["first"] + rule["add"] * (half - 1)
        total = round(total, 2)
    return total, rule["time"]

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👋 欢迎使用集运机器人\n请点击下方菜单选择功能"
    await update.message.reply_text(text, reply_markup=main_menu())

# 运费查询入口
async def freight_query_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tip = "📝 请按格式输入：国家 线路 实重(kg) 长 宽 高\n" \
          "示例：美国 空运敏感专线 5 30 20 15\n" \
          "支持线路可查看帮助，100KG以上/超大件请联系客服"
    await update.message.reply_text(tip)

# 解析并计算运费
async def handle_freight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    parts = msg.split()
    if len(parts) != 6:
        await update.message.reply_text("❌ 格式错误！\n正确格式：国家 线路 实重 长 宽 高")
        return
    country, route, w_str, l_str, wi_str, h_str = parts
    try:
        weight = float(w_str)
        length = float(l_str)
        width = float(wi_str)
        height = float(h_str)
    except ValueError:
        await update.message.reply_text("❌ 重量/长宽高必须为数字！")
        return

    total_price = -1
    time_text = ""

    # 美国
    if country == "美国":
        if route == "空运敏感专线":
            total_price, time_text = calc_air_price(weight, length, width, height, USA_AIR_SENS)
        elif route == "美国海运普货":
            total_price, time_text = calc_sea_kahang(weight, USA_SEA_NORMAL)
        elif route == "海运普快船":
            total_price, time_text = calc_sea_kahang(weight, USA_SEA_FAST)
        elif route == "海运敏快船":
            total_price, time_text = calc_sea_kahang(weight, USA_SEA_SENS)
    # 英国
    elif country == "英国" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, UK_AIR_SENS)
    # 加拿大
    elif country == "加拿大":
        if route == "空运专线":
            total_price, time_text = calc_air_price(weight, length, width, height, CA_AIR)
        elif route == "海运专线":
            total_price, time_text = calc_sea_kahang(weight, CA_SEA)
    # 澳大利亚
    elif country == "澳大利亚" and route == "空运专线":
        total_price, time_text = calc_air_price(weight, length, width, height, AU_AIR)
    # 新西兰
    elif country == "新西兰" and route == "空运专线":
        total_price, time_text = calc_air_price(weight, length, width, height, NZ_AIR)
    # 瑞士
    elif country == "瑞士" and route == "EMS":
        total_price, time_text = calc_air_price(weight, length, width, height, CH_EMS)
    # 克罗地亚 DHL
    elif country == "克罗地亚" and route == "DHL敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, HR_DHL)
    # 比利时
    elif country == "比利时" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, BE_AIR)
    # 荷兰
    elif country == "荷兰" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, NL_AIR)
    # 卢森堡
    elif country == "卢森堡" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, LU_AIR)
    # 波兰
    elif country == "波兰" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, PL_AIR)
    # 德国
    elif country == "德国" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, DE_AIR)
    # 捷克
    elif country == "捷克" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, CZ_AIR)
    # 法国
    elif country == "法国" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, FR_AIR)
    # 奥地利
    elif country == "奥地利" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, AT_AIR)
    # 爱尔兰
    elif country == "爱尔兰" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, IE_AIR)
    # 匈牙利
    elif country == "匈牙利" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, HU_AIR)
    # 西班牙
    elif country == "西班牙" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, ES_AIR)
    # 意大利
    elif country == "意大利" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, IT_AIR)
    # 瑞典
    elif country == "瑞典" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, SE_AIR)
    # 斯洛文尼亚
    elif country == "斯洛文尼亚" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, SI_AIR)
    # 葡萄牙
    elif country == "葡萄牙" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, PT_AIR)
    # 丹麦
    elif country == "丹麦" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, DK_AIR)
    # 拉脱维亚
    elif country == "拉脱维亚" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, LV_AIR)
    # 爱沙尼亚
    elif country == "爱沙尼亚" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, EE_AIR)
    # 芬兰
    elif country == "芬兰" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, FI_AIR)
    # 保加利亚
    elif country == "保加利亚" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, BG_AIR)
    # 罗马尼亚
    elif country == "罗马尼亚" and route == "空运敏感专线":
        total_price, time_text = calc_air_price(weight, length, width, height, RO_AIR)
    # 马耳他 DHL
    elif country == "马耳他" and route == "DHL专线":
        total_price, time_text = calc_air_price(weight, length, width, height, MT_DHL)
    # 塞浦路斯 DHL
    elif country == "塞浦路斯" and route == "DHL专线":
        total_price, time_text = calc_air_price(weight, length, width, height, CY_DHL)
    # 希腊
    elif country == "希腊":
        if route == "普货专线":
            total_price, time_text = calc_greece(weight, length, width, height, GR_NORMAL)
        elif route == "敏感专线":
            total_price, time_text = calc_greece(weight, length, width, height, GR_SENS)
    # 欧洲卡航分组
    elif route == "欧洲卡航包税专线":
        if country in ["德国","法国","意大利","西班牙"]:
            total_price, time_text = calc_sea_kahang(weight, EU_GROUP1)
        elif country in ["波兰","捷克","丹麦","荷兰","比利时","奥地利","卢森堡"]:
            total_price, time_text = calc_sea_kahang(weight, EU_GROUP2)
        elif country in ["克罗地亚","斯洛伐克","斯洛文尼亚"]:
            total_price, time_text = calc_sea_kahang(weight, EU_GROUP3)
        elif country in ["芬兰","摩纳哥","瑞典","保加利亚","爱沙尼亚","拉脱维亚","立陶宛","匈牙利"]:
            total_price, time_text = calc_sea_kahang(weight, EU_GROUP4)
        elif country in ["希腊","爱尔兰","葡萄牙"]:
            total_price, time_text = calc_sea_kahang(weight, EU_GROUP5)

    # 结果输出
    if isinstance(total_price, str) or total_price == -1:
        await update.message.reply_text(f"⚠️ {time_text}")
    else:
        out = f"✅ 计算完成\n线路：{country} {route}\n总价：¥{total_price}\n参考时效：{time_text}"
        await update.message.reply_text(out)

# 优惠码功能
async def promo_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("请输入你的达人专属码查询优惠")

async def handle_promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT description, discount_rules FROM promo_codes WHERE code=%s AND is_active=TRUE",
                (code,)
            )
            row = cur.fetchone()
            if not row:
                await update.message.reply_text("未识别指令，请选择底部菜单或输入达人专属码查询优惠~")
                return
            # 记录用户
            cur.execute(
                "INSERT INTO users (tg_id, username) VALUES (%s, %s) ON CONFLICT (tg_id) DO NOTHING",
                (update.effective_user.id, update.effective_user.username)
            )
            cur.execute(
                "INSERT INTO redemptions (tg_id, code) VALUES (%s, %s)",
                (update.effective_user.id, code)
            )
            conn.commit()
            text = f"🎁 {row['description']}\n优惠内容：{row['discount_rules']}"
            await update.message.reply_text(text)
    finally:
        conn.close()

# 关于我们
async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🏢 曜途国际集运\n专业全球跨境物流\n双清包税，多条专线可选"
    await update.message.reply_text(text)

# 联系客服
async def contact_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📞 如需咨询100KG以上大件、超长件、特殊货物\n请直接联系在线客服"
    await update.message.reply_text(text)

# 帮助
async def help_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "❓ 使用帮助\n1. 运费查询：按「国家 线路 实重 长 宽 高」格式发送\n2. 优惠码：输入专属码领取优惠\n3. 100KG以上/超大件请联系客服"
    await update.message.reply_text(text)

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # 命令
    app.add_handler(CommandHandler("start", start))

    # 菜单按钮
    app.add_handler(MessageHandler(filters.Text("📦 运费查询"), freight_query_enter))
    app.add_handler(MessageHandler(filters.Text("🎁 优惠码"), promo_enter))
    app.add_handler(MessageHandler(filters.Text("ℹ️ 关于我们"), about_us))
    app.add_handler(MessageHandler(filters.Text("📞 联系客服"), contact_service))
    app.add_handler(MessageHandler(filters.Text("❓ 帮助"), help_info))

    # 输入解析
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_freight_input))

    app.run_polling()

if __name__ == "__main__":
    main()
