import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# إعداد التسجيل للأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# ⚙️ إعدادات المطور الأساسية
# ==========================================
TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"      # ✅ تم إضافة التوكين الخاص بك
ADMIN_ID = 8182419990                                     # ✅ تم تحديد الـ ID الخاص بك

# متغيّرات النظام (يمكن تعديلها من داخل البوت مستقبلاً)
force_sub_config = {
    "enabled": True,
    "username": "@YourChannel",
    "url": "https://t.me/YourChannel"
}
# ==========================================

# دالة التحقق مما إذا كان المستخدم هو الأدمن
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# دالة كشف الحسابات المشبوهة/الوهمية
def is_suspicious_user(user) -> tuple[bool, str]:
    if not user.username:
        return True, "لا يوجد معرف (@username)"
    if re.search(r'\d{5,}$', user.username):
        return True, "المعرف يحتوي على أرقام عشوائية كثيرة"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if len(full_name) < 2:
        return True, "الاسم قصير جداً"
    return False, "حساب طبيعي"

# دالة التحقق من الاشتراك في القناة
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not force_sub_config["enabled"]:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=force_sub_config["username"], user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError:
        return False

# ==========================================
# 👑 أوامر التحكم الخاصة بالمطور (من داخل البوت)
# ==========================================

async def force_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    force_sub_config["enabled"] = True
    await update.message.reply_text("✅ تم **تفعيل** ميزة الاشتراك الإجباري بنجاح.")

async def force_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    force_sub_config["enabled"] = False
    await update.message.reply_text("❌ تم **إيقاف** ميزة الاشتراك الإجباري بنجاح.")

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    
    # التأكد من إدخال المعرف والرابط
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ الاستخدام الصحيح:\n`/set_channel @username https://t.me/username`", parse_mode="Markdown")
        return
    
    force_sub_config["username"] = context.args[0]
    force_sub_config["url"] = context.args[1]
    
    await update.message.reply_text(
        f"✅ تم تحديث بيانات القناة بنجاح!\n\n"
        f"📢 المعرف: `{force_sub_config['username']}`\n"
        f"🔗 الرابط: {force_sub_config['url']}", 
        parse_mode="Markdown"
    )

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    status_str = "مفعلة 🟢" if force_sub_config["enabled"] else "معطلة 🔴"
    await update.message.reply_text(
        f"⚙️ **حالة الاشتراك الإجباري:** {status_str}\n"
        f"📢 **القناة الحالية:** {force_sub_config['username']}\n"
        f"🔗 **الرابط:** {force_sub_config['url']}",
        parse_mode="Markdown"
    )

# ==========================================
# 🤖 أوامر البوت العامة للمستخدمين
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if force_sub_config["enabled"] and not await is_user_subscribed(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة", url=force_sub_config["url"])],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:\n{force_sub_config['username']}",
            reply_markup=reply_markup
        )
        return

    keyboard = [[InlineKeyboardButton("❤️ تصويت / تفاعل", callback_data="vote")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("أهلاً بك! اضغط على الزر أدناه للتصويت:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if query.data == "check_sub":
        if await is_user_subscribed(user.id, context):
            keyboard = [[InlineKeyboardButton("❤️ تصويت / تفاعل", callback_data="vote")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("✅ تم التحقق بنجاح! يمكنك الآن الاستخدام:", reply_markup=reply_markup)
        else:
            await query.answer("❌ لم تشترك في القناة بعد!", show_alert=True)
        return

    if query.data == "vote":
        if force_sub_config["enabled"] and not await is_user_subscribed(user.id, context):
            await query.edit_message_text(f"⚠️ يرجى الاشتراك في القناة أولاً: {force_sub_config['username']}")
            return

        is_fake, reason = is_suspicious_user(user)
        if is_fake:
            await query.edit_message_text(f"⚠️ تم رفض التصويت.\nالسبب: الحساب مشبوه ({reason}).")
        else:
            await query.edit_message_text(f"✅ تم تسجيل تصويتك بنجاح يا {user.first_name}!")

# ==========================================
# 🚀 تشغيل البوت
# ==========================================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # أوامر المستخدمين
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # أوامر الأدمن للتحكم من داخل الشات
    app.add_handler(CommandHandler("force_on", force_on))
    app.add_handler(CommandHandler("force_off", force_off))
    app.add_handler(CommandHandler("set_channel", set_channel))
    app.add_handler(CommandHandler("status", bot_status))
    
    print("البوت يعمل الآن...")
    app.run_polling()
