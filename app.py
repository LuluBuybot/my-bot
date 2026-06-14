import os
import math
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# ===================== 【1. 价格配置区】=====================
COUNTRY_ROUTE_CONFIG = {
    "美国": [
        {
            "name": "空运敏感专线",
            "rule_type": "weight_05kg",
            "first": 148,
            "add": 54,
            "free_first_weight": 11,
            "volume_div": 6000,
            "min_weight": None,
            "special_tip": "参考时效：7-14工作日"
        },
        {
            "name": "美国海运普货",
            "rule_type": "per_kg",
            "price_per_kg": 28,
            "volume_div": 6000,
            "min_weight": 12,
            "special_tip": "12KG起发"
        },
        {
            "name": "美国海运普快船",
            "rule_type": "per_kg",
            "price_per_kg": 35,
            "volume_div": 6000,
            "min_weight": 12,
            "special_tip": "12KG起发"
        },
        {
            "name": "美国海运敏快船",
            "rule_type": "per_kg",
            "price_per_kg": 38,
            "volume_div": 6000,
            "min_weight": 12,
            "special_tip": "12KG起发"
        }
    ],
    "英国": [
        {
            "name": "空运敏感专线",
            "rule_type": "weight_05kg",
            "first": 65,
            "add": 36,
            "free_first_weight": 11,
            "volume_div": 6000,
            "special_tip": "参考时效：10-15工作日"
        }
    ],
    "加拿大": [
        {
            "name": "空运专线",
            "rule_type": "weight_05kg",
            "first": 108,
            "add": 35,
            "free_first_weight": 11,
            "volume_div": 6000,
            "special_tip": "参考时效：10-15工作日"
        },
        {
            "name": "海运专线",
            "rule_type": "per_kg",
            "price_per_kg": 36,
            "volume_div": 6000,
            "min_weight": 12,
            "special_tip": "12KG起发，30-55工作日"
        }
    ],
    "澳大利亚": [
        {
            "name": "空运专线",
            "rule_type": "weight_05kg",
            "first": 88,
            "add": 32,
            "volume_div": 7000,
            "special_tip": "参考时效：7-14工作日"
        }
    ],
    "新西兰": [
        {
            "name": "空运专线",
            "rule_type": "weight_05kg",
            "first": 118,
            "add": 43,
            "free_first_weight": 11,
            "volume_div": 6000,
            "special_tip": "参考时效：7-15工作日"
        }
    ],
    "瑞士": [
        {
            "name": "EMS",
            "rule_type": "weight_05kg",
            "first": 138,
            "add": 42,
            "volume_div": 6000,
            "special_tip": "参考时效：7-20工作日"
        }
    ],
    "马耳他": [
        {
            "name": "DHL专线",
            "rule_type": "weight_05kg",
            "first": 208,
            "add": 53,
            "free_first_weight": 11,
            "volume_div": 6000,
            "min_weight": 1,
            "special_tip": "参考时效：7-14工作日"
        }
    ],
    "塞浦路斯": [
        {
            "name": "DHL专线",
            "rule_type": "weight_05kg",
            "first": 238,
            "add": 59,
            "free_first_weight": 11,
            "volume_div": 6000,
            "min_weight": 1,
            "special_tip": "参考时效：7-14工作日"
        }
    ],
    "希腊": [
        {
            "name": "普货专线",
            "rule_type": "weight_05kg",
            "first": 136,
            "add": 33,
            "volume_div": 6000,
            "special_tip": "11KG以上68元/KG"
        },
        {
            "name": "敏感专线",
            "rule_type": "weight_05kg",
            "first": 136,
            "add": 43,
            "volume_div": 6000,
            "special_tip": "11KG以上80元/KG"
        }
    ],
    "欧洲": {
        "countries": ["德国","法国","意大利","西班牙","波兰","捷克","丹麦","荷兰","比利时","奥地利","卢森堡","克罗地亚","斯洛伐克","斯洛文尼亚","芬兰","瑞典","保加利亚","爱沙尼亚","拉脱维亚","立陶宛","匈牙利","爱尔兰","葡萄牙","罗马尼亚"],
        "routes": {
            "德国": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 125,"add": 38,"free_first_weight": 11,"volume_div": 6000,"special_tip": "7-14工作日"}],
            "法国": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 136,"add": 39,"free_first_weight": 11,"volume_div": 6000,"special_tip": "10-15工作日"}],
            "意大利": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 136,"add": 41,"free_first_weight": 11,"volume_div": 6000,"special_tip": "7-15工作日"}],
            "西班牙": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 136,"add": 39,"free_first_weight": 11,"volume_div": 6000,"special_tip": "10-15工作日"}],
            "罗马尼亚": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 155,"add": 43,"free_first_weight": 11,"volume_div": 6000,"special_tip": "7-12工作日"}],
        }
    }
}

RAIL_PRICE = {
    "de_fr_it_es": 39,
    "pl_cz_dk_nl_be_at_lu": 41.5,
    "hr_sk_si": 42.5,
    "fi_mc_se_bg_ee_lv_lt_hu": 44.5,
    "gr_ie_pt": 45.5,
    "min_weight": 15,
    "tip": "欧洲卡航免税专线，28-38天"
}

# ===================== 【2. 优惠码】=====================
COUPON_CONFIG = {
    "K1507": """🎁 LuluBuy 新用户优惠券
使用专属码可领取：
· 满0减30｜满250减50｜满420减80
· 满500减100｜满1250减158｜满1988减300
· 无门槛15%折扣
有效期30天""",
}

DEFAULT_COUPON = "🎁 新人券：LULUBUY10 运费立减10元"

# ===================== 【3. 数据库连接】=====================
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# 初始化表（第一次自动创建）
def init_db():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                tg_id BIGINT PRIMARY KEY,
                username TEXT,
                first_used TIMESTAMP DEFAULT NOW()
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS coupon_usage (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT,
                username TEXT,
                code TEXT,
                used_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS freight_log (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT,
                username TEXT,
                country TEXT,
                route TEXT,
                weight REAL,
                price REAL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
    conn.commit()
    conn.close()

# 记录用户
def log_user(tg_id, username):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO users (tg_id, username) VALUES (%s,%s) ON CONFLICT DO NOTHING', (tg_id, username))
    conn.commit()
    conn.close()

# 记录优惠码使用
def log_coupon(tg_id, username, code):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO coupon_usage (tg_id, username, code) VALUES (%s,%s,%s)', (tg_id, username, code))
    conn.commit()
    conn.close()

# 记录运费查询
def log_freight(tg_id, username, country, route, weight, price):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO freight_log (tg_id, username, country, route, weight, price) VALUES (%s,%s,%s,%s,%s,%s)',
                    (tg_id, username, country, route, weight, price))
    conn.commit()
    conn.close()

# ===================== 【4. 菜单 & 按钮】=====================
keyboard = [["📦 运费查询", "🏠 仓库地址"],["💬 联系客服", "🎁 专属优惠码"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
user_state = {}

# ===================== 【5. 工具函数】=====================
def calc_05kg_rule(bill_weight, route):
    unit = 0.5
    total_unit = math.ceil(bill_weight / unit)
    first = route["first"]
    add = route["add"]
    free = route.get("free_first_weight")
    if free and bill_weight >= free:
        return round(total_unit * add, 2)
    return round(first + (total_unit-1)*add, 2) if total_unit>1 else round(first,2)

def calc_per_kg_rule(w, route):
    return round(w * route["price_per_kg"], 2)

def parse_weight(text):
    text = text.lower().strip()
    if "kg" in text:
        text = text.replace("kg","")
    if "g" in text:
        try: return True, float(text.replace("g",""))/1000
        except: return False, None
    try: return True, float(text)
    except: return False, None

# ===================== 【6. 按钮生成】=====================
def country_main_btns():
    btns = [[InlineKeyboardButton("欧洲", callback_data="cg:欧洲")]]
    for c in [k for k in COUNTRY_ROUTE_CONFIG if k!="欧洲"]:
        btns.append([InlineKeyboardButton(c, callback_data=f"c:{c}")])
    return InlineKeyboardMarkup(btns)

def europe_country_btns():
    btns = []
    for c in COUNTRY_ROUTE_CONFIG["欧洲"]["countries"]:
        btns.append([InlineKeyboardButton(c, callback_data=f"c:欧洲_{c}")])
    return InlineKeyboardMarkup(btns)

def route_btns(country, is_europe):
    btns = []
    if is_europe:
        rs = COUNTRY_ROUTE_CONFIG["欧洲"]["routes"].get(country, [])
    else:
        rs = COUNTRY_ROUTE_CONFIG.get(country, [])
    for r in rs:
        btns.append([InlineKeyboardButton(r["name"], callback_data=f"r:{country}:{r['name']}:{is_europe}")])
    if is_europe:
        btns.append([InlineKeyboardButton("欧洲卡航免税专线", callback_data=f"r:{country}:卡航:True")])
    return InlineKeyboardMarkup(btns)

# ===================== 【7. 逻辑处理】=====================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    log_user(u.id, u.username)
    user_state.pop(u.id, None)
    await update.message.reply_text(f"欢迎 LuluBuy 国际物流 🚀\n\n{DEFAULT_COUPON}", reply_markup=reply_markup)

async def btn_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    d = q.data

    if d.startswith("cg:欧洲"):
        user_state[uid] = {"step":"eu","prev":"main"}
        await q.edit_message_text("选择欧洲国家", reply_markup=europe_country_btns())
        return

    if d.startswith("c:") and not d.startswith("c:欧洲_"):
        c = d.split(":")[1]
        user_state[uid] = {"step":"route","country":c,"eu":False,"prev":"main"}
        await q.edit_message_text(f"{c} 线路", reply_markup=route_btns(c,False))
        return

    if d.startswith("c:欧洲_"):
        c = d.split("_")[1]
        user_state[uid] = {"step":"route","country":c,"eu":True,"prev":"eu"}
        await q.edit_message_text(f"{c} 线路", reply_markup=route_btns(c,True))
        return

    if d.startswith("r:"):
        _, c, rname, eu = d.split(":")
        user_state[uid] = {"step":"weight","country":c,"eu":eu=="True","route_name":rname,"prev":"route"}
        if rname == "卡航":
            user_state[uid]["rail"]=True
            await q.edit_message_text("卡航15KG起发\n输入：重量 或 长 宽 高")
        else:
            user_state[uid]["rail"]=False
            await q.edit_message_text("输入：重量 或 长 宽 高")

async def msg_handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    u = update.effective_user
    uid = u.id
    state = user_state.get(uid, {})
    step = state.get("step")

    # 优惠码
    code = msg.upper()
    if code in COUPON_CONFIG:
        log_coupon(uid, u.username, code)
        await update.message.reply_text(COUPON_CONFIG[code])
        return

    # 返回
    if msg == "返回":
        if step == "weight":
            user_state[uid] = {"step":"route","country":state["country"],"eu":state["eu"],"prev":"eu" if state["eu"] else "main"}
            await update.message.reply_text(f"{state['country']} 线路", reply_markup=route_btns(state["country"], state["eu"]))
        elif step == "route":
            if state["eu"]:
                user_state[uid] = {"step":"eu","prev":"main"}
                await update.message.reply_text("欧洲国家", reply_markup=europe_country_btns())
            else:
                user_state[uid] = {"step":"main","prev":None}
                await update.message.reply_text("选择国家", reply_markup=country_main_btns())
        elif step == "eu":
            user_state[uid] = {"step":"main","prev":None}
            await update.message.reply_text("选择国家", reply_markup=country_main_btns())
        else:
            user_state.pop(uid, None)
            await update.message.reply_text("主菜单", reply_markup=reply_markup)
        return

    # 运费查询入口
    if msg == "📦 运费查询":
        user_state[uid] = {"step":"main","prev":None}
        await update.message.reply_text("选择国家", reply_markup=country_main_btns())
        return

    # 运费计算
    if step == "weight":
        c = state["country"]
        rname = state["route_name"]

        # 卡航
        if state.get("rail"):
            ok, w = parse_weight(msg)
            if ok:
                if w < 15:
                    await update.message.reply_text("❌ 15KG起发")
                    return
                if c in ["德国","法国","意大利","西班牙"]: pri=39
                elif c in ["波兰","捷克","丹麦","荷兰","比利时","奥地利","卢森堡"]: pri=41.5
                elif c in ["克罗地亚","斯洛伐克","斯洛文尼亚"]: pri=42.5
                elif c in ["芬兰","瑞典","保加利亚","爱沙尼亚","拉脱维亚","立陶宛","匈牙利"]: pri=44.5
                elif c in ["希腊","爱尔兰","葡萄牙"]: pri=45.5
                else: pri=0
                total = round(w*pri,2)
                log_freight(uid, u.username, c, "卡航", w, total)
                await update.message.reply_text(f"计费：{w:.1f}kg\n💰 {total}元\n{RAIL_PRICE['tip']}")
                return
            else:
                parts = msg.split()
                if len(parts)==3:
                    try:
                        l,w,h = map(float, parts)
                        vol = l*w*h/6000
                        if vol<15:
                            await update.message.reply_text("❌ 15KG起发")
                            return
                        if c in ["德国","法国","意大利","西班牙"]: pri=39
                        elif c in ["波兰","捷克","丹麦","荷兰","比利时","奥地利","卢森堡"]: pri=41.5
                        elif c in ["克罗地亚","斯洛伐克","斯洛文尼亚"]: pri=42.5
                        elif c in ["芬兰","瑞典","保加利亚","爱沙尼亚","拉脱维亚","立陶宛","匈牙利"]: pri=44.5
                        elif c in ["希腊","爱尔兰","葡萄牙"]: pri=45.5
                        else: pri=0
                        total = round(vol*pri,2)
                        log_freight(uid, u.username, c, "卡航", vol, total)
                        await update.message.reply_text(f"体积重：{vol:.1f}kg\n💰 {total}元")
                        return
                    except: pass
            await update.message.reply_text("格式错误")
            return

        # 普通线路
        if state["eu"]:
            rs = COUNTRY_ROUTE_CONFIG["欧洲"]["routes"][c]
        else:
            rs = COUNTRY_ROUTE_CONFIG[c]
        route = next(x for x in rs if x["name"]==rname)
        div = route["volume_div"]
        min_w = route.get("min_weight")

        ok, act_w = parse_weight(msg)
        if ok:
            if min_w and act_w < min_w:
                await update.message.reply_text(f"❌ 最低{min_w}KG")
                return
            bill = act_w
        else:
            parts = msg.split()
            if len(parts)!=3:
                await update.message.reply_text("格式错误")
                return
            try:
                l,b,h = map(float, parts)
                bill = (l*b*h)/div
            except:
                await update.message.reply_text("格式错误")
                return

        if route["rule_type"]=="weight_05kg":
            total = calc_05kg_rule(bill, route)
        else:
            total = calc_per_kg_rule(bill, route)

        log_freight(uid, u.username, c, rname, bill, total)
        await update.message.reply_text(f"计费：{bill:.1f}kg\n💰 {total}元\n{route['special_tip']}")
        return

    # 菜单
    if msg == "🏠 仓库地址":
        await update.message.reply_text("🏠 仓库地址\n收货人：曜途国际\n电话：19566061044\n地址：广州市白云区鹤龙一路168号福大园区38号Sashun转曜途国际")
    elif msg == "💬 联系客服":
        await update.message.reply_text("💬 客服：@Lulu_Buy")
    elif msg == "🎁 专属优惠码":
        await update.message.reply_text("请输入优惠码（如 K1507）")
    else:
        await update.message.reply_text("请使用菜单或输入优惠码")

# ===================== 【8. 启动】=====================
def main():
    init_db()
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn_callback))
    app.add_handler(MessageHandler(filters.TEXT, msg_handle))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()    ],
    "加拿大": [
        {
            "name": "空运专线",
            "rule_type": "weight_05kg",
            "first": 108,
            "add": 35,
            "free_first_weight": 11,
            "volume_div": 6000,
            "special_tip": "参考时效：10-15工作日"
        },
        {
            "name": "海运专线",
            "rule_type": "per_kg",
            "price_per_kg": 36,
            "volume_div": 6000,
            "min_weight": 12,
            "special_tip": "12KG起发，30-55工作日"
        }
    ],
    "澳大利亚": [
        {
            "name": "空运专线",
            "rule_type": "weight_05kg",
            "first": 88,
            "add": 32,
            "volume_div": 7000,
            "special_tip": "参考时效：7-14工作日"
        }
    ],
    "新西兰": [
        {
            "name": "空运专线",
            "rule_type": "weight_05kg",
            "first": 118,
            "add": 43,
            "free_first_weight": 11,
            "volume_div": 6000,
            "special_tip": "参考时效：7-15工作日"
        }
    ],
    "瑞士": [
        {
            "name": "EMS",
            "rule_type": "weight_05kg",
            "first": 138,
            "add": 42,
            "volume_div": 6000,
            "special_tip": "参考时效：7-20工作日"
        }
    ],
    "马耳他": [
        {
            "name": "DHL专线",
            "rule_type": "weight_05kg",
            "first": 208,
            "add": 53,
            "free_first_weight": 11,
            "volume_div": 6000,
            "min_weight": 1,
            "special_tip": "参考时效：7-14工作日"
        }
    ],
    "塞浦路斯": [
        {
            "name": "DHL专线",
            "rule_type": "weight_05kg",
            "first": 238,
            "add": 59,
            "free_first_weight": 11,
            "volume_div": 6000,
            "min_weight": 1,
            "special_tip": "参考时效：7-14工作日"
        }
    ],
    "希腊": [
        {
            "name": "普货专线",
            "rule_type": "weight_05kg",
            "first": 136,
            "add": 33,
            "volume_div": 6000,
            "special_tip": "11KG以上68元/KG"
        },
        {
            "name": "敏感专线",
            "rule_type": "weight_05kg",
            "first": 136,
            "add": 43,
            "volume_div": 6000,
            "special_tip": "11KG以上80元/KG"
        }
    ],
    "欧洲": {
        "countries": ["德国","法国","意大利","西班牙","波兰","捷克","丹麦","荷兰","比利时","奥地利","卢森堡","克罗地亚","斯洛伐克","斯洛文尼亚","芬兰","瑞典","保加利亚","爱沙尼亚","拉脱维亚","立陶宛","匈牙利","爱尔兰","葡萄牙","罗马尼亚"],
        "routes": {
            "德国": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 125,"add": 38,"free_first_weight": 11,"volume_div": 6000,"special_tip": "7-14工作日"}],
            "法国": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 136,"add": 39,"free_first_weight": 11,"volume_div": 6000,"special_tip": "10-15工作日"}],
            "意大利": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 136,"add": 41,"free_first_weight": 11,"volume_div": 6000,"special_tip": "7-15工作日"}],
            "西班牙": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 136,"add": 39,"free_first_weight": 11,"volume_div": 6000,"special_tip": "10-15工作日"}],
            "罗马尼亚": [{"name": "空运敏感专线","rule_type": "weight_05kg","first": 155,"add": 43,"free_first_weight": 11,"volume_div": 6000,"special_tip": "7-12工作日"}],
        }
    }
}

RAIL_PRICE = {
    "de_fr_it_es": 39,
    "pl_cz_dk_nl_be_at_lu": 41.5,
    "hr_sk_si": 42.5,
    "fi_mc_se_bg_ee_lv_lt_hu": 44.5,
    "gr_ie_pt": 45.5,
    "min_weight": 15,
    "tip": "欧洲卡航免税专线，28-38天"
}

# ===================== 【2. 优惠码】=====================
COUPON_CONFIG = {
    "K1507": """🎁 LuluBuy 新用户优惠券
使用专属码可领取：
· 满0减30｜满250减50｜满420减80
· 满500减100｜满1250减158｜满1988减300
· 无门槛15%折扣
有效期30天""",
}

DEFAULT_COUPON = "🎁 新人券：LULUBUY10 运费立减10元"

# ===================== 【3. 数据库连接】=====================
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# 初始化表（第一次自动创建）
def init_db():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                tg_id BIGINT PRIMARY KEY,
                username TEXT,
                first_used TIMESTAMP DEFAULT NOW()
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS coupon_usage (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT,
                username TEXT,
                code TEXT,
                used_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS freight_log (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT,
                username TEXT,
                country TEXT,
                route TEXT,
                weight REAL,
                price REAL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
    conn.commit()
    conn.close()

# 记录用户
def log_user(tg_id, username):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO users (tg_id, username) VALUES (%s,%s) ON CONFLICT DO NOTHING', (tg_id, username))
    conn.commit()
    conn.close()

# 记录优惠码使用
def log_coupon(tg_id, username, code):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO coupon_usage (tg_id, username, code) VALUES (%s,%s,%s)', (tg_id, username, code))
    conn.commit()
    conn.close()

# 记录运费查询
def log_freight(tg_id, username, country, route, weight, price):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO freight_log (tg_id, username, country, route, weight, price) VALUES (%s,%s,%s,%s,%s,%s)',
                    (tg_id, username, country, route, weight, price))
    conn.commit()
    conn.close()

# ===================== 【4. 菜单 & 按钮】=====================
keyboard = [["📦 运费查询", "🏠 仓库地址"],["💬 联系客服", "🎁 专属优惠码"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
user_state = {}

# ===================== 【5. 工具函数】=====================
def calc_05kg_rule(bill_weight, route):
    unit = 0.5
    total_unit = math.ceil(bill_weight / unit)
    first = route["first"]
    add = route["add"]
    free = route.get("free_first_weight")
    if free and bill_weight >= free:
        return round(total_unit * add, 2)
    return round(first + (total_unit-1)*add, 2) if total_unit>1 else round(first,2)

def calc_per_kg_rule(w, route):
    return round(w * route["price_per_kg"], 2)

def parse_weight(text):
    text = text.lower().strip()
    if "kg" in text:
        text = text.replace("kg","")
    if "g" in text:
        try: return True, float(text.replace("g",""))/1000
        except: return False, None
    try: return True, float(text)
    except: return False, None

# ===================== 【6. 按钮生成】=====================
def country_main_btns():
    btns = [[InlineKeyboardButton("欧洲", callback_data="cg:欧洲")]]
    for c in [k for k in COUNTRY_ROUTE_CONFIG if k!="欧洲"]:
        btns.append([InlineKeyboardButton(c, callback_data=f"c:{c}")])
    return InlineKeyboardMarkup(btns)

def europe_country_btns():
    btns = []
    for c in COUNTRY_ROUTE_CONFIG["欧洲"]["countries"]:
        btns.append([InlineKeyboardButton(c, callback_data=f"c:欧洲_{c}")])
    return InlineKeyboardMarkup(btns)

def route_btns(country, is_europe):
    btns = []
    if is_europe:
        rs = COUNTRY_ROUTE_CONFIG["欧洲"]["routes"].get(country, [])
    else:
        rs = COUNTRY_ROUTE_CONFIG.get(country, [])
    for r in rs:
        btns.append([InlineKeyboardButton(r["name"], callback_data=f"r:{country}:{r['name']}:{is_europe}")])
    if is_europe:
        btns.append([InlineKeyboardButton("欧洲卡航免税专线", callback_data=f"r:{country}:卡航:True")])
    return InlineKeyboardMarkup(btns)

# ===================== 【7. 逻辑处理】=====================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    log_user(u.id, u.username)
    user_state.pop(u.id, None)
    await update.message.reply_text(f"欢迎 LuluBuy 国际物流 🚀\n\n{DEFAULT_COUPON}", reply_markup=reply_markup)

async def btn_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    d = q.data

    if d.startswith("cg:欧洲"):
        user_state[uid] = {"step":"eu","prev":"main"}
        await q.edit_message_text("选择欧洲国家", reply_markup=europe_country_btns())
        return

    if d.startswith("c:") and not d.startswith("c:欧洲_"):
        c = d.split(":")[1]
        user_state[uid] = {"step":"route","country":c,"eu":False,"prev":"main"}
        await q.edit_message_text(f"{c} 线路", reply_markup=route_btns(c,False))
        return

    if d.startswith("c:欧洲_"):
        c = d.split("_")[1]
        user_state[uid] = {"step":"route","country":c,"eu":True,"prev":"eu"}
        await q.edit_message_text(f"{c} 线路", reply_markup=route_btns(c,True))
        return

    if d.startswith("r:"):
        _, c, rname, eu = d.split(":")
        user_state[uid] = {"step":"weight","country":c,"eu":eu=="True","route_name":rname,"prev":"route"}
        if rname == "卡航":
            user_state[uid]["rail"]=True
            await q.edit_message_text("卡航15KG起发\n输入：重量 或 长 宽 高")
        else:
            user_state[uid]["rail"]=False
            await q.edit_message_text("输入：重量 或 长 宽 高")

async def msg_handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    u = update.effective_user
    uid = u.id
    state = user_state.get(uid, {})
    step = state.get("step")

    # 优惠码
    code = msg.upper()
    if code in COUPON_CONFIG:
        log_coupon(uid, u.username, code)
        await update.message.reply_text(COUPON_CONFIG[code])
        return

    # 返回
    if msg == "返回":
        if step == "weight":
            user_state[uid] = {"step":"route","country":state["country"],"eu":state["eu"],"prev":"eu" if state["eu"] else "main"}
            await update.message.reply_text(f"{state['country']} 线路", reply_markup=route_btns(state["country"], state["eu"]))
        elif step == "route":
            if state["eu"]:
                user_state[uid] = {"step":"eu","prev":"main"}
                await update.message.reply_text("欧洲国家", reply_markup=europe_country_btns())
            else:
                user_state[uid] = {"step":"main","prev":None}
                await update.message.reply_text("选择国家", reply_markup=country_main_btns())
        elif step == "eu":
            user_state[uid] = {"step":"main","prev":None}
            await update.message.reply_text("选择国家", reply_markup=country_main_btns())
        else:
            user_state.pop(uid, None)
            await update.message.reply_text("主菜单", reply_markup=reply_markup)
        return

    # 运费查询入口
    if msg == "📦 运费查询":
        user_state[uid] = {"step":"main","prev":None}
        await update.message.reply_text("选择国家", reply_markup=country_main_btns())
        return

    # 运费计算
    if step == "weight":
        c = state["country"]
        rname = state["route_name"]

        # 卡航
        if state.get("rail"):
            ok, w = parse_weight(msg)
            if ok:
                if w < 15:
                    await update.message.reply_text("❌ 15KG起发")
                    return
                if c in ["德国","法国","意大利","西班牙"]: pri=39
                elif c in ["波兰","捷克","丹麦","荷兰","比利时","奥地利","卢森堡"]: pri=41.5
                elif c in ["克罗地亚","斯洛伐克","斯洛文尼亚"]: pri=42.5
                elif c in ["芬兰","瑞典","保加利亚","爱沙尼亚","拉脱维亚","立陶宛","匈牙利"]: pri=44.5
                elif c in ["希腊","爱尔兰","葡萄牙"]: pri=45.5
                else: pri=0
                total = round(w*pri,2)
                log_freight(uid, u.username, c, "卡航", w, total)
                await update.message.reply_text(f"计费：{w:.1f}kg\n💰 {total}元\n{RAIL_PRICE['tip']}")
                return
            else:
                parts = msg.split()
                if len(parts)==3:
                    try:
                        l,w,h = map(float, parts)
                        vol = l*w*h/6000
                        if vol<15:
                            await update.message.reply_text("❌ 15KG起发")
                            return
                        if c in ["德国","法国","意大利","西班牙"]: pri=39
                        elif c in ["波兰","捷克","丹麦","荷兰","比利时","奥地利","卢森堡"]: pri=41.5
                        elif c in ["克罗地亚","斯洛伐克","斯洛文尼亚"]: pri=42.5
                        elif c in ["芬兰","瑞典","保加利亚","爱沙尼亚","拉脱维亚","立陶宛","匈牙利"]: pri=44.5
                        elif c in ["希腊","爱尔兰","葡萄牙"]: pri=45.5
                        else: pri=0
                        total = round(vol*pri,2)
                        log_freight(uid, u.username, c, "卡航", vol, total)
                        await update.message.reply_text(f"体积重：{vol:.1f}kg\n💰 {total}元")
                        return
                    except: pass
            await update.message.reply_text("格式错误")
            return

        # 普通线路
        if state["eu"]:
            rs = COUNTRY_ROUTE_CONFIG["欧洲"]["routes"][c]
        else:
            rs = COUNTRY_ROUTE_CONFIG[c]
        route = next(x for x in rs if x["name"]==rname)
        div = route["volume_div"]
        min_w = route.get("min_weight")

        ok, act_w = parse_weight(msg)
        if ok:
            if min_w and act_w < min_w:
                await update.message.reply_text(f"❌ 最低{min_w}KG")
                return
            bill = act_w
        else:
            parts = msg.split()
            if len(parts)!=3:
                await update.message.reply_text("格式错误")
                return
            try:
                l,b,h = map(float, parts)
                bill = (l*b*h)/div
            except:
                await update.message.reply_text("格式错误")
                return

        if route["rule_type"]=="weight_05kg":
            total = calc_05kg_rule(bill, route)
        else:
            total = calc_per_kg_rule(bill, route)

        log_freight(uid, u.username, c, rname, bill, total)
        await update.message.reply_text(f"计费：{bill:.1f}kg\n💰 {total}元\n{route['special_tip']}")
        return

    # 菜单
    if msg == "🏠 仓库地址":
        await update.message.reply_text("🏠 仓库地址\n收货人：曜途国际\n电话：19566061044\n地址：广州市白云区鹤龙一路168号福大园区38号Sashun转曜途国际")
    elif msg == "💬 联系客服":
        await update.message.reply_text("💬 客服：@Lulu_Buy")
    elif msg == "🎁 专属优惠码":
        await update.message.reply_text("请输入优惠码（如 K1507）")
    else:
        await update.message.reply_text("请使用菜单或输入优惠码")

# ===================== 【8. 启动】=====================
def main():
    init_db()
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btn_callback))
    app.add_handler(MessageHandler(filters.TEXT, msg_handle))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
