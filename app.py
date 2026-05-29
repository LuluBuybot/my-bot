import os
import psycopg2
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# 读取环境变量
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
INVALID_MSG = os.getenv("INVALID_MSG", "未识别指令，请输入你的达人专属码查询优惠~")
PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-payment-link.com")

# 数据库连接
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 欢迎！输入你的达人专属码查询优惠")

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    tg_id = update.effective_user.id
    username = update.effective_user.username or ""

    # 查询优惠码
    cur.execute(
        "SELECT description, discount_rules FROM promo_codes WHERE code=%s AND is_active=TRUE",
        (code,)
    )
    row = cur.fetchone()
    if not row:
        await update.message.reply_text(INVALID_MSG)
        return

    desc, rules = row
    # 记录用户信息
    cur.execute(
        "INSERT INTO users (tg_id, username) VALUES (%s, %s) ON CONFLICT (tg_id) DO NOTHING",
        (tg_id, username)
    )
    # 记录兑换行为
    cur.execute(
        "INSERT INTO redemptions (tg_id, code) VALUES (%s, %s)",
        (tg_id, code)
    )
    conn.commit()

    # 回复用户
    text = (
        f"🎁 {desc}\n"
        f"优惠内容：\n{rules.replace(',', '• ')}\n\n"
        f"👉 立即下单：{PAYMENT_URL}"
    )
    await update.message.reply_text(text)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # 注册处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code))

    # 启动 Bot
    application.run_polling()

if __name__ == "__main__":
    main()
