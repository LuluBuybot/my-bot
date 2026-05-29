import os
import psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 环境变量
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
INVALID_MSG = os.getenv("INVALID_MSG", "未识别指令，请选择底部菜单或输入达人专属码查询优惠~")
PAYMENT_URL = os.getenv("PAYMENT_URL", "https://你的收款链接.com")

# 连接数据库
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 欢迎！输入达人专属码查询优惠")

# 处理优惠码
def handle_code(update: Update, context: CallbackContext):
    code = update.message.text.strip()
    tg_id = update.message.from_user.id
    username = update.message.from_user.username or ""

    # 查优惠码
    cur.execute("SELECT description, discount_rules FROM promo_codes WHERE code=%s AND is_active=TRUE", (code,))
    row = cur.fetchone()
    if not row:
        update.message.reply_text(INVALID_MSG)
        return

    desc, rules = row
    # 记录领取
    cur.execute("INSERT INTO users (tg_id, username) VALUES (%s, %s) ON CONFLICT (tg_id) DO NOTHING", (tg_id, username))
    cur.execute("INSERT INTO redemptions (tg_id, code) VALUES (%s, %s)", (tg_id, code))
    conn.commit()

    # 发优惠+收款链接
    text = f"🎁 {desc}\n优惠：{rules}\n👉 立即下单：{PAYMENT_URL}"
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