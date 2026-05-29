import os
import psycopg2
from telegram import Update
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext
)

# 从环境变量读取配置（Railway 里设置）
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
INVALID_MSG = os.getenv("INVALID_MSG", "未识别指令，请选择底部菜单或输入达人专属码查询优惠~")
PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-payment-link.com")

# 数据库连接
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 欢迎！输入你的达人专属码查询优惠")

def handle_code(update: Update, context: CallbackContext):
    code = update.message.text.strip()
    tg_id = update.message.from_user.id
    username = update.message.from_user.username or ""

    # 查优惠码
    cur.execute(
        "SELECT description, discount_rules FROM promo_codes WHERE code=%s AND is_active=TRUE",
        (code,)
    )
    row = cur.fetchone()
    if not row:
        update.message.reply_text(INVALID_MSG)
        return

    desc, rules = row
    # 记录用户
    cur.execute(
        "INSERT INTO users (tg_id, username) VALUES (%s, %s) ON CONFLICT (tg_id) DO NOTHING",
        (tg_id, username)
    )
    # 记录兑换
    cur.execute(
        "INSERT INTO redemptions (tg_id, code) VALUES (%s, %s)",
        (tg_id, code)
    )
    conn.commit()

    text = (
        f"🎁 {desc}\n"
        f"优惠内容：\n{rules.replace(',', '• ')}\n\n"
        f"👉 立即下单：{PAYMENT_URL}"
    )
    update.message.reply_text(text)

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_code))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()