from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from collections import defaultdict
from datetime import time

# 🔐 Replace with your bot token
BOT_TOKEN = '8319413626:AAGVZNEziOiQoREQEOSO20jDv3t-jtJKMMU'

# Stores: group_id -> user_id -> count
group_user_photo_counts = defaultdict(lambda: defaultdict(int))
group_user_photo_duplicates = defaultdict(lambda: defaultdict(int))
group_user_photo_ids = defaultdict(lambda: defaultdict(set))

# 📸 Handle photo messages
async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    group_id = update.effective_chat.id
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    photo = update.message.photo[-1]
    unique_id = photo.file_unique_id

    group_user_photo_counts[group_id][user_id] += 1

    if unique_id in group_user_photo_ids[group_id][user_id]:
        group_user_photo_duplicates[group_id][user_id] += 1
        print(f"[{group_id}] {username} sent a duplicate photo.")
    else:
        group_user_photo_ids[group_id][user_id].add(unique_id)

    print(f"[{group_id}] {username}: {group_user_photo_counts[group_id][user_id]} photos (Duplicates: {group_user_photo_duplicates[group_id][user_id]})")

# 📬 Send daily stats to each group
async def send_stats(context: ContextTypes.DEFAULT_TYPE):
    for group_id, user_counts in group_user_photo_counts.items():
        if not user_counts:
            continue

        stats = "📊 *Daily Photo Stats*\n\n"
        for user_id, total in user_counts.items():
            dup = group_user_photo_duplicates[group_id][user_id]
            try:
                user = await context.bot.get_chat_member(group_id, user_id)
                username = user.user.username or user.user.first_name
            except:
                username = "Unknown User"
            stats += f"• {username}: {total} photos ({dup} duplicates)\n"

        await context.bot.send_message(chat_id=group_id, text=stats, parse_mode="Markdown")

    # 🧼 Reset daily counts but keep photo history
    group_user_photo_counts.clear()
    group_user_photo_duplicates.clear()

# 🚀 Initialize bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# 🧠 Register handler
app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, count_messages))

# 🕗 Daily job at 20:00
app.job_queue.run_daily(send_stats, time(hour=20, minute=0))

print("📡 Bot is running... Press Ctrl+C to stop.")
app.run_polling()
