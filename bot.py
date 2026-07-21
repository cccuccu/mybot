import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ConversationHandler, filters, ContextTypes
)

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔑 التوكن والآيدي الخاص بك
TOKEN = "8813278276:AAFshG2TngZXJ8ZewhU_Lq6TRy1mbt2Ez6M"
ADMIN_ID = 8182419990

# 📊 البيانات المخزنة (تتعدل بالكامل من داخل الشات)
developer_info = "@YourHandle"
start_message_custom = "• اهلاً بك في لوحة تحكم السايت والتواصل"
force_channel = ""  # يتم تعيين القناة من داخل البوت مباشرة
fake_users_count = 0 
user_ids = set()

# حالات الانتظار لإدخال البيانات من الشات
SET_DEV, SET_START, SET_FORCE_SUB, SET_FAKE_SUB, BROADCAST = range(5)

# 🏠 لوحة التحكم المطابقة للصورة
def get_admin_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("تغيير المطور", callback_data="change_dev"),
            InlineKeyboardButton("تغيير /start", callback_data="change_start")
        ],
        [
            InlineKeyboardButton("الاشتراك الاجباري", callback_data="force_sub"),
            InlineKeyboardButton("الاحصائيات", callback_data="stats")
        ],
        [
            InlineKeyboardButton("الاشتراك الوهمي", callback_data="fake_sub"),
            InlineKeyboardButton("الاذاعة", callback_data="broadcast")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# 🔍 فحص الاشتراك الإجباري
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not force_channel:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=force_channel, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception:
        return True

# 🚀 أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_ids.add(user.id)

    # لوحة الأدمن
    if user.id == ADMIN_ID:
        text = f"• اهلاً بك في لوحة الادمن\n\n{start_message_custom}"
        if update.message:
            await update.message.reply_text(text, reply_markup=get_admin_keyboard())
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=get_admin_keyboard())
        return

    # المستخدم العادي (فحص الاشتراك الإجباري)
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        clean_channel = force_channel.replace('@', '')
        keyboard = [[InlineKeyboardButton("📢 اضغط هنا للاشتراك في القناة", url=f"https://t.me/{clean_channel}")]]
        await update.message.reply_text(
            f"⚠️ عذراً عزيزي، لا يمكنك استخدام البوت حتى تشترك في القناة التالية:\n{force_channel}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(f"{start_message_custom}\n\n👤 المطور: {developer_info}\nأرسل رسالتك وسوف تصل للإدارة.")

# 🔄 الضغط على الأزرار من داخل التليجرام
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_admin")]])

    if data == "stats":
        real_users = len(user_ids)
        total_users = real_users + fake_users_count
        text = (
            f"📊 <b>إحصائيات البوت:</b>\n\n"
            f"• الأعضاء الحقيقيين: <code>{real_users}</code>\n"
            f"• الأعضاء الوهميين: <code>{fake_users_count}</code>\n"
            f"• الإجمالي الظاهر: <code>{total_users}</code>"
        )
        await query.edit_message_text(text, reply_markup=back_btn, parse_mode="HTML")

    elif data == "change_dev":
        await query.edit_message_text(f"👤 المطور الحالي: {developer_info}\n\nأرسل معرف المطور الجديد من الشات (مثال: @username):", reply_markup=back_btn)
        return SET_DEV

    elif data == "change_start":
        await query.edit_message_text(f"📝 الكليشة الحالية:\n{start_message_custom}\n\nأرسل الكليشة الجديدة من الشات:", reply_markup=back_btn)
        return SET_START

    elif data == "force_sub":
        status = force_channel if force_channel else "غير مفعّل"
        await query.edit_message_text(
            f"⚙️ الاشتراك الإجباري الحالي: {status}\n\n"
            f"📢 أرسل معرف القناة الآن في الشات (مثال: @myChannel)\n"
            f"أو أرسل الرقم 0 لإلغاء الاشتراك الإجباري:", 
            reply_markup=back_btn
        )
        return SET_FORCE_SUB

    elif data == "fake_sub":
        await query.edit_message_text(f"⚙️ العدد الوهمي الحالي: {fake_users_count}\n\nأرسل الرقم الجديد لإضافته للإحصائيات:", reply_markup=back_btn)
        return SET_FAKE_SUB

    elif data == "broadcast":
        await query.edit_message_text("📢 قم بإرسال أو توجيه أي رسالة في الشات الآن لإذاعتها لجميع الأعضاء:", reply_markup=back_btn)
        return BROADCAST

    elif data == "back_admin":
        text = f"• اهلاً بك في لوحة الادمن\n\n{start_message_custom}"
        await query.edit_message_text(text, reply_markup=get_admin_keyboard())
        return ConversationHandler.END

# 📝 استقبال الأوامر والنصوص مباشرة من الشات
async def save_dev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global developer_info
    developer_info = update.message.text
    await update.message.reply_text(f"✅ تم تغيير المطور إلى: {developer_info}", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

async def save_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global start_message_custom
    start_message_custom = update.message.text
    await update.message.reply_text("✅ تم تحديث كليشة /start بنجاح!", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

async def save_force_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global force_channel
    text = update.message.text.strip()
    if text == "0":
        force_channel = ""
        await update.message.reply_text("✅ تم إلغاء الاشتراك الإجباري.", reply_markup=get_admin_keyboard())
    else:
        force_channel = text if text.startswith("@") else f"@{text}"
        await update.message.reply_text(f"✅ تم تعيين القناة {force_channel} للاشتراك الإجباري بنجاح!\n\n⚠️ تأكد من رفع البوت أدمن داخل القناة.", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

async def save_fake_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fake_users_count
    if update.message.text.isdigit():
        fake_users_count = int(update.message.text)
        await update.message.reply_text(f"✅ تم تحديث العدد الوهمي إلى: {fake_users_count}", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("❌ أرسل أرقاماً فقط!")
    return ConversationHandler.END

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    success, failed = 0, 0
    await msg.reply_text("⏳ جاري بدء الإذاعة...")

    for u_id in list(user_ids):
        try:
            await msg.forward(chat_id=u_id)
            success += 1
        except Exception:
            failed += 1

    await msg.reply_text(
        f"✅ <b>تمت الإذاعة!</b>\n\n• تم الإرسال لـ: {success}\n• المحظورين: {failed}",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    return ConversationHandler.END

# 📩 توجيه رسائل التواصل
async def forward_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        user_ids.add(user.id)
        if await check_subscription(user.id, context):
            await update.message.forward(chat_id=ADMIN_ID)
            await update.message.reply_text("✅ تم إرسال رسالتك إلى الإدارة.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_buttons)],
        states={
            SET_DEV: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_dev)],
            SET_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_start)],
            SET_FORCE_SUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_force_sub)],
            SET_FAKE_SUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_fake_sub)],
            BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, do_broadcast)],
        },
        fallbacks=[CallbackQueryHandler(admin_buttons, pattern="^back_admin$")]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_messages))

    print("جاري تشغيل البوت...")
    app.run_polling()


