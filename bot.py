import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent

API_TOKEN = '8902067749:AAG1_xIylE24VaLq6GiDA7CrESWKKfRt4lU'
CHANNEL_USERNAME = '@DAVMTGR' 
CHANNEL_LINK = 'https://t.me/DAVMTGR' 

bot = telebot.TeleBot(API_TOKEN)

# 1. دالة التحقق من الاشتراك الإجباري في قناتك
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        return False

# 2. استقبال الأوامر والرسائل العادية
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    # التحقق من الاشتراك الإجباري أولاً
    if not check_subscription(user_id):
        error_text = (
            "- عذرا عزيزي 🚸 .\n"
            "- عليك الاشتراك بقناة البوت لتتمكن من استخدامه 🟩\n\n"
            f"- {CHANNEL_LINK}\n\n"
            "‼️ | اشترك ثم ارسل /start"
        )
        bot.reply_to(message, error_text, disable_web_page_preview=False)
        return

    # إذا أرسل /start أو دخل البوت بنجاح تظهر له لوحة التحكم المذكورة في الصورة
    if message.text.startswith('/start'):
        welcome_text = (
            "بوت إنشاء التصويت الذكي | V2.2.4 ⚡️\n\n"
            "مرحباً بك في لوحة التحكم. يمكنك الآن:\n\n"
            "✅ إنشاء تصويت: تصميم منشورات تفاعلية احترافية.\n\n"
            "✅ قفل القناة: تفعيل ميزة الاشتراك الإجباري للمتابعين.\n\n"
            "✅ تخصيص كامل: تحكم في مظهر وأيقونات التفاعل.\n\n"
            "استخدم الأزرار أدناه للتحكم في البوت 👇"
        )
        
        # تصميم الأزرار الشفافة كما في الصورة تماماً
        markup = InlineKeyboardMarkup(row_width=2)
        
        btn_create = InlineKeyboardButton(text="📊 إنشاء تصويت جديد", callback_data="create_vote")
        btn_interact = InlineKeyboardButton(text="⚪️ زر التفاعل", callback_data="btn_interact")
        btn_sub = InlineKeyboardButton(text="📢 الاشتراك الإجباري", callback_data="btn_sub")
        btn_admin = InlineKeyboardButton(text="🌐 المركز الإداري", callback_data="btn_admin")
        
        # ترتيب الأزرار في صفوف
        markup.add(btn_create)
        markup.add(btn_interact, btn_sub)
        markup.add(btn_admin)
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
        return

    # إذا أرسل المستخدم اسماً مباشراً (خارج نطاق الضغط على الأزرار) لتوليد رابط تصويت سريع
    target_name = message.text
    markup_share = InlineKeyboardMarkup()
    share_button = InlineKeyboardButton(
        text="🚀 اضغط هنا لنشر التصويت والاسم", 
        switch_inline_query=f"vote_{target_name}"
    )
    markup_share.add(share_button)

    bot.reply_to(
        message, 
        f"✅ تم تجهيز رابط التصويت بنجاح للاسم: **{target_name}**\n\nاضغط على الزر بالأسفل لتبدأ بنشره في المجموعات والقنوات على شكل نقاط للتصويت لها👇", 
        reply_markup=markup_share,
        parse_mode="Markdown"
    )

# 3. معالجة الضغط على أزرار لوحة التحكم (Callback Queries)
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    if call.data == "create_vote":
        bot.send_message(call.message.chat.id, "📝 حسناً، أرسل لي الآن الاسم الذي تريد إنشاء تصويت له.")
    elif call.data == "btn_interact":
        bot.send_message(call.message.chat.id, "⚙️ قسم تخصيص أزرار التفاعل (سيتم ربطه بالإعدادات قريباً).")
    elif call.data == "btn_sub":
        bot.send_message(call.message.chat.id, f"📢 إعدادات الاشتراك الإجباري الحالية مربوطة بـ: {CHANNEL_USERNAME}")
    elif call.data == "btn_admin":
        bot.send_message(call.message.chat.id, "🔒 المركز الإداري خاص بمالك البوت فقط.")
    
    # لإنهاء حالة التحميل بالزر بعد الضغط
    bot.answer_callback_query(call.id)

# 4. معالجة نظام الإنلاين (Inline Query) لنشر التصويت بالنقاط
@bot.inline_handler(func=lambda query: query.query.startswith('vote_'))
def inline_vote_generator(query):
    try:
        name_to_vote = query.query.split('vote_')[1]
        
        results_text = (
            f"📊 تصويت جديد للاسم: **{name_to_vote}**\n\n"
            "• ━━━━━━━━━━━━━━━━━━ •\n"
            "اضغط على الرابط بالأسفل لدعم هذا الاسم والتصويت له!\n"
            "• ━━━━━━━━━━━━━━━━━━ •"
        )
        
        reply_markup = InlineKeyboardMarkup()
        vote_url = f"https://t.me/{bot.get_me().username}?start=voted_{query.from_user.id}"
        reply_markup.add(InlineKeyboardButton(text="📥 اضغط هنا للتصويت له", url=vote_url))
        
        item = InlineQueryResultArticle(
            id='1',
            title=f"نشر منشور تصويت لـ {name_to_vote}",
            description="اضغط هنا لإرسال المنشور فوراً بنظام النقاط",
            input_message_content=InputTextMessageContent(results_text, parse_mode="Markdown"),
            reply_markup=reply_markup
        )
        
        bot.answer_inline_query(query.id, [item], cache_time=1)
    except Exception as e:
        print(e)

bot.polling()
    
