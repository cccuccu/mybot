import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# إعداد التسجيل للأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# ⚙️ إعدادات المطور (قم بتعديلها من هنا)
# ==========================================
TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"          # توكين البوت من BotFather

# ميزة الاشتراك الإجباري (اجعلها True لتفعيلها، أو False لإلغائها)
ENABLE_FORCE_SUB = True                    

# بيانات القناة (تُستخدم فقط عند تفعيل ENABLE_FORCE_SUB = True)
CHANNEL_USERNAME = "@YourChannel"          # معرف قناتك (مع @)
CHANNEL_URL = "https://t.me/YourChannel"     # رابط قناتك
# ==========================================

# دالة كشف الحسابات المشبوهة/الوهمية (الرشق)
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
    # إذا كانت الميزة معطلة من إعدادات المطور، اعتبر المستخدم مشتركون تلقائياً
    if not ENABLE_FORCE_SUB:
        return True

    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except TelegramError:
        # في حال وجود خطأ في الوصول للقناة (مثلاً البوت ليس مشرفاً)
        return False

# أمر البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق من الاشتراك إذا كانت الميزة مفعّلة
    if ENABLE_FORCE_SUB and not await is_user_subscribed(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:\n{CHANNEL_USERNAME}",
            reply_markup=reply_markup
        )
        return

    # الواجهة الرئيسية
    keyboard = [[InlineKeyboardButton("❤️ تصويت / تفاعل", callback_data="vote")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("أهلاً بك! اضغط على الزر أدناه للتصويت:", reply_markup=reply_markup)

# التعامل مع الضغط على الأزرار
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # زر التحقق من الاشتراك
    if query.data == "check_sub":
        if await is_user_subscribed(user.id, context):
            keyboard = [[InlineKeyboardButton("❤️ تصويت / تفاعل", callback_data="vote")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("✅ تم التحقق بنجاح! يمكنك الآن الاستخدام:", reply_markup=reply_markup)
        else:
            await query.answer("❌ لم تشترك في القناة بعد!", show_alert=True)
        return

    # زر التصويت
    if query.data == "vote":
        # إعادة التأكد من الاشتراك إذا كان مفاعلاً
        if ENABLE_FORCE_SUB and not await is_user_subscribed(user.id, context):
            await query.edit_message_text(f"⚠️ يرجى الاشتراك في القناة أولاً: {CHANNEL_USERNAME}")
            return

        # فحص الحساب الوهمي/الرشق
        is_fake, reason = is_suspicious_user(user)
        if is_fake:
            await query.edit_message_text(f"⚠️ تم رفض التصويت.\nالسبب: الحساب مشبوه ({reason}).")
        else:
            await query.edit_message_text(f"✅ تم تسجيل تصويتك بنجاح يا {user.first_name}!")

if name == 'main':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("البوت يعمل الآن...")
    app.run_polling()
    
