# main.py
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN
from bot_controller import so_start, so_generate, cancel_so

async def reject_everything_else(update, context):
    if update.message:
        await update.message.reply_text("❌ Bot ini hanya menerima perintah /so")
    elif update.callback_query:
        await update.callback_query.answer("❌ Akses ditolak", show_alert=True)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 1. Izinkan hanya command /so
    app.add_handler(CommandHandler("so", so_start))

    # 2. Izinkan hanya callback inline keyboard kita (SO|...)
    app.add_handler(CallbackQueryHandler(so_generate, pattern=r"^SO\|"))

    app.add_handler(CallbackQueryHandler(cancel_so, pattern=r"^CANCEL_SO$"))

    # 3. TOLAK SEMUA YANG LAIN
    app.add_handler(MessageHandler(filters.ALL, reject_everything_else))

    # 4. Start bot (polling)
    app.run_polling()
    # 5. Jalankan webserver supaya tetap hidup di Heroku
    app.run(host='0.0.0.0', port=7890)

if __name__ == "__main__":
    main()