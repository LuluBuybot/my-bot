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

# ========== 数据库连接 ==========
def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )

# ========== 菜单键盘（常驻） ==========
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

# ========== /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 欢迎使用曜途国际集运机器人！\n"
        "请点击下方菜单使用功能：\n"
        "📦 运费查询 | 🎁 优惠码 | ℹ️ 关于我们 | 📞 联系客服"
    )
    await update.message.reply_text(text, reply_markup=main_menu())

# ========== 运费查询（按重量/国家） ==========
async def freight_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "请输入：国家/地区 + 重量(kg)\n"
        "示例：英国 1.5"
    )

async def handle_freight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("格式错误！请用：英国 1.5")
        return
    country, weight_str = parts
    try:
        weight = float(weight_str)
    except ValueError:
        await update.message.reply_text("重量必须是数字！")
        return

    # 这里写你原来的运费规则（示例）
    price_per_kg = {
        "英国": 85,
        "德国": 88,
        "法国": 88,
        "美国": 95,
        "加拿大": 92,
        "澳大利亚": 90
    }
    if country not in price_per_kg:
        await update.message.reply_text(f"暂不支持 {country}")
        return
    total = price_per_kg[country] * weight
    await update.message.reply_text(
        f"📦 {country} 运费\n"
        f"重量：{weight} kg\n"
        f"单价：¥{price_per_kg[country]}/kg\n"
        f"总计：¥{total:.2f}"
    )

# ========== 优惠码查询 ==========
async def promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("请输入你的达人专属码查询优惠")

async def handle_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM promo_codes WHERE code = %s AND is_active = true",
                (code,)
            )
            promo = cur.fetchone()
            if not promo:
                await update.message.reply_text("❌ 无效或已过期优惠码")
                return
            # 记录核销
            cur.execute(
                "INSERT INTO redemptions (user_id, username, code) VALUES (%s, %s, %s)",
                (update.effective_user.id, update.effective_user.username, code)
            )
            conn.commit()
            await update.message.reply_text(
                f"✅ 优惠码有效！\n"
                f"码：{promo['code']}\n"
                f"优惠：{promo['discount']}\n"
                f"说明：{promo['note']}"
            )
    finally:
        conn.close()

# ========== 关于我们 / 联系客服 / 帮助 ==========
async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 曜途国际集运\n"
        "专注中国→全球门到门物流\n"
        "双清包税 | 5日达 | 价格透明\n"
        "服务国家：英/德/法/美/加/澳等"
    )

async def contact_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 联系客服\n"
        "Telegram：@你的客服账号\n"
        "工作时间：周一至周日 10:00-22:00"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ 使用帮助\n"
        "📦 运费查询：国家 + 重量（例：英国 1.5）\n"
        "🎁 优惠码：输入专属码查优惠\n"
        "ℹ️ 关于我们：公司介绍\n"
        "📞 联系客服：咨询问题"
    )

# ========== 主入口 ==========
def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    # 命令
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # 菜单按钮
    app.add_handler(MessageHandler(filters.Text("📦 运费查询"), freight_query))
    app.add_handler(MessageHandler(filters.Text("🎁 优惠码"), promo_code))
    app.add_handler(MessageHandler(filters.Text("ℹ️ 关于我们"), about_us))
    app.add_handler(MessageHandler(filters.Text("📞 联系客服"), contact_support))
    app.add_handler(MessageHandler(filters.Text("❓ 帮助"), help_cmd))

    # 文本处理（运费/优惠码）
    app.add_handler(MessageHandler(filters.Regex(r"^[\u4e00-\u9fa5]+\s+\d+(\.\d+)?$"), handle_freight))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_promo))

    app.run_polling()

if __name__ == "__main__":
    main()
