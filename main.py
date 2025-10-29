# main.py
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN
from bot_controller import so_start, so_generate, cancel_so, ed_report

async def reject_everything_else(update, context):
    if update.message:
        await update.message.reply_text("❌ Bot ini hanya menerima perintah /so")
    elif update.callback_query:
        await update.callback_query.answer("❌ Akses ditolak", show_alert=True)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # handler utama
    app.add_handler(CommandHandler("so", so_start))
    app.add_handler(CallbackQueryHandler(so_generate, pattern=r"^SO\|"))
    app.add_handler(CallbackQueryHandler(cancel_so, pattern=r"^CANCEL_SO$"))

    app.add_handler(CommandHandler("ed", ed_report))
    # app.add_handler(CallbackQueryHandler(so_generate, pattern=r"^ED\|"))
    # app.add_handler(CallbackQueryHandler(cancel_so, pattern=r"^CANCEL_SO$"))

    app.add_handler(MessageHandler(filters.ALL, reject_everything_else))

    # jalankan via polling, BUKAN webhook
    app.run_polling()

if __name__ == "__main__":
    main()