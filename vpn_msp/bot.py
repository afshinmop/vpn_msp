import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # توکن ربات
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # آیدی ادمین
BASE_URL = os.getenv("BASE_URL", "")  # برای webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # ← اصلاح‌شده: name → __name__

USERS = set()
WAITING_FOR_AD = set()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)
    keyboard = [
        [InlineKeyboardButton("🛡️ سرویس VPN", callback_data="vpn_menu")],
        [InlineKeyboardButton("📢 تبلیغات شما", callback_data="ads_menu")],
    ]
    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n"
        "من ربات VPN هستم.\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# منوی VPN
async def vpn_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("💎 پلن 1 ماهه", callback_data="vpn_1")],
        [InlineKeyboardButton("🔥 پلن 3 ماهه", callback_data="vpn_3")],
        [InlineKeyboardButton("🚀 پلن 6 ماهه", callback_data="vpn_6")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        "🛡️ پلن‌های VPN:\n💎 1 ماهه\n🔥 3 ماهه\n🚀 6 ماهه",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# درخواست VPN
async def vpn_request(update: Update, context: ContextTypes.DEFAULT_TYPE, plan):
    query = update.callback_query
    await query.edit_message_text(
        f"✅ درخواست VPN ({plan}) ثبت شد. ادمین به زودی با شما تماس می‌گیرد."
    )
    await context.bot.send_message(
        ADMIN_ID,
        f"📥 درخواست VPN جدید:\n"
        f"کاربر: {query.from_user.first_name}\n"
        f"پلن: {plan}\n"
        f"ID: {query.from_user.id}"
    )

# تبلیغات
async def ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    WAITING_FOR_AD.add(query.from_user.id)
    await query.edit_message_text("📢 متن تبلیغ خود را بفرستید.")

async def handle_ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in WAITING_FOR_AD:
        WAITING_FOR_AD.remove(user.id)
        await context.bot.send_message(
            ADMIN_ID,
            f"📢 تبلیغ جدید:\n{update.message.text}\n"
            f"از: {user.first_name} ({user.id})"
        )
        await update.message.reply_text("✅ تبلیغت ارسال شد.")

# پیام از ادمین به کاربر
async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("فرمت: /msg <user_id> <text>")
        return
    user_id = int(context.args[0])
    text = " ".join(context.args[1:])
    await context.bot.send_message(user_id, f"📩 پیام از ادمین:\n{text}")
    await update.message.reply_text("✅ ارسال شد.")

# کنترل منوها
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "vpn_menu":
        await vpn_menu(update, context)
    elif data == "ads_menu":
        await ads_menu(update, context)
    elif data == "main_menu":
        await start(update, context)
    elif data == "vpn_1":
        await vpn_request(update, context, "1 ماهه")
    elif data == "vpn_3":
        await vpn_request(update, context, "3 ماهه")
    elif data == "vpn_6":
        await vpn_request(update, context, "6 ماهه")

# ساخت اپلیکیشن
def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("msg", msg))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ad_text))
    return app

# اجرای اصلی
if __name__ == "__main__":  # ← اصلاح‌شده: name → __name__
    if not BOT_TOKEN:
        raise RuntimeError("توکن ربات خالی است!")
    app = build_app()
    PORT = int(os.getenv("PORT", "10000"))
    if BASE_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{BASE_URL}/{BOT_TOKEN}"
        )
    else:
        app.run_polling()
