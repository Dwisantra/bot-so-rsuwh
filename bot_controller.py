# bot_controller.py
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
)
from telegram.ext import (
    ContextTypes,
)
from datetime import datetime
from config import ALLOWED_CHAT_IDS
from services import get_ruangan_list, get_master_rows, get_stok_rows_pre, get_so_final_rows, get_last_so_date, get_obat_ed
from helpers import merge_stok_into_master, build_xlsx_so, build_ed_xlsx

def is_private_chat(update):
    """Cek apakah chat ini private (bukan grup / channel)."""
    chat = update.effective_chat
    return chat and chat.type == "private"

async def so_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ⛔ Tolak jika bukan chat pribadi
    if not is_private_chat(update):
        if update.message:
            await update.message.reply_text("❌ Hanya boleh via chat pribadi.")

    """
    /so
    1. Validasi akses
    2. Ambil cutoff_date otomatis dari stok_opname terakhir
    3. Kirim pilihan ruangan
    """
    chat_id = update.message.chat_id
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("Unauthorized.")
        return

    # Ambil tanggal SO terbaru dari DB
    cutoff_date = get_last_so_date()
    if not cutoff_date:
        await update.message.reply_text("Tidak ada data SO.")
        return

    # Ambil daftar ruangan
    ruangan_list = get_ruangan_list()
    if not ruangan_list:
        await update.message.reply_text("Tidak ada ruangan ditemukan.")
        return

    # Buat tombol ruangan
    # callback_data sekarang: SO|<cutoff>|<kode_ruangan>|<deskripsi_ruangan>
    buttons = []
    for r in ruangan_list:
        kode = r["ID"]
        desk = r["DESKRIPSI"]
        buttons.append([
            InlineKeyboardButton(
                f"{desk} ({kode})",
                callback_data=f"SO|{cutoff_date}|{kode}|{desk}"
            )
        ])

    # Tambahkan tombol batal
    buttons.append([InlineKeyboardButton("❌ Batal", callback_data="CANCEL_SO")])

    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        f"Tanggal SO terakhir: {cutoff_date}\n"
        "Pilih ruangan untuk generate SO:",
        reply_markup=keyboard
    )


async def so_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ⛔ Tolak jika bukan chat pribadi
    if not is_private_chat(update):
        if update.message:
            await update.message.reply_text("❌ Hanya boleh via chat pribadi.")

    """
    Callback setelah user pilih salah satu ruangan.
    Generate file Excel & kirim balik.
    """
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        await query.edit_message_text("Unauthorized.")
        return

    # data: "SO|2025-10-25|10304XYZ|FARMASI SATELIT A"
    parts = query.data.split("|", 3)
    # parts[0] = "SO"
    cutoff_date   = parts[1]
    kode_ruangan  = parts[2]
    nama_ruangan  = parts[3] if len(parts) > 3 else kode_ruangan

    # Update pesan jadi status proses, pakai nama ruangan (lebih manusiawi)
    await query.edit_message_text(
        f"⏳ Sedang proses {nama_ruangan} ({kode_ruangan})...\n"
        f"Tanggal SO: {cutoff_date}"
    )

    try:
        # Ambil data sumber
        master_rows   = get_master_rows(kode_ruangan)
        stok_pre_rows = get_stok_rows_pre(cutoff_date, kode_ruangan)  # stok sebelum cutoff
        stok_post_rows = get_so_final_rows(cutoff_date, kode_ruangan)  # stok setelah SO

        # Merge jadi satu dataset siap Excel
        merged_rows = merge_stok_into_master(
            master_rows,
            stok_pre_rows,
            stok_post_rows,
        )

        # Build workbook
        xlsx_data = build_xlsx_so(merged_rows, stok_pre_rows, stok_post_rows)

        # Nama file
        filename = f"SO_{nama_ruangan}_{kode_ruangan}_{cutoff_date}.xlsx"
        xlsx_data.name = filename

        # Kirim file
        await query.message.reply_document(
            document=InputFile(xlsx_data, filename),
            caption=(
                "✅ SO siap.\n"
                f"Ruangan: {nama_ruangan} ({kode_ruangan})\n"
                f"Cutoff <= {cutoff_date} 23:59:59\n\n"
                "- Sheet STOK_PRE_SO = cutoff raw pre SO\n"
                "- Sheet STOK_POST_SO = data final setelah SO"
            )
        )

        # update pesan status jadi final
        await query.edit_message_text(
            f"✅ Proses selesai.\n"
            f"{nama_ruangan} ({kode_ruangan}) — file sudah dikirim."
        )

    except Exception as e:
        await query.message.reply_text(f"❌ Terjadi kesalahan: {e}")


async def cancel_so(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Dibatalkan ✅", show_alert=False)
    await query.edit_message_text("❌ Proses dibatalkan.")

async def ed_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private_chat(update):
        if update.message:
            await update.message.reply_text("❌ Hanya boleh via chat pribadi.")
        return

    chat_id = update.message.chat_id
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("Unauthorized.")
        return

    # default hari
    threshold_days = 90

    rows = get_obat_ed(threshold_days)

    # ngasih status sementara
    status_msg = await update.message.reply_text(
        f"⏳ Sedang proses mengambil data obat EXP ≤ {threshold_days} hari..."
    )

    # update pesan status jadi final
    await status_msg.edit_text(
        f"✅ Laporan EXP siap. Total batch: {len(rows)}."
    )

    if not rows:
        await update.message.reply_text(
            f"✅ Tidak ada obat yang EXP dalam {threshold_days} hari ke depan."
        )
        return

    # bangun Excel
    xlsx_data = build_ed_xlsx(rows, threshold_days)

    # nama file
    filename = f"EXP_{threshold_days}hari_{datetime.now().strftime('%Y%m%d')}.xlsx"
    xlsx_data.name = filename

    # kirim file ke user
    await update.message.reply_document(
        document=InputFile(xlsx_data, filename),
        caption=(
            f"📄 Laporan EXP (≤ {threshold_days} hari)\n"
            # f"Total batch: {len(rows)}\n"
            # "Sheet1: OBAT_EXP\n"
            # "Sheet2: INFO"
        )
    )
