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
    WEBHOOK_PUBLIC_URL = "http://10.10.10.31/bot/rsuwh/so"
    LOCAL_LISTEN_HOST = "127.0.0.1"
    LOCAL_LISTEN_PORT = 7890
    LOCAL_ENDPOINT_PATH = "so"

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # handler yang boleh
    app.add_handler(CommandHandler("so", so_start))
    app.add_handler(CallbackQueryHandler(so_generate, pattern=r"^SO\|"))
    app.add_handler(CallbackQueryHandler(cancel_so, pattern=r"^CANCEL_SO$"))
    app.add_handler(MessageHandler(filters.ALL, reject_everything_else))

    # jalankan webhook
    app.run_webhook(
        listen=LOCAL_LISTEN_HOST,
        port=LOCAL_LISTEN_PORT,
        url_path=LOCAL_ENDPOINT_PATH,
        webhook_url=WEBHOOK_PUBLIC_URL,
    )

if __name__ == "__main__":
    main()