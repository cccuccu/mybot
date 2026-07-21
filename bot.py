import sys
import subprocess

# ==========================================
# 📦 تثبيت المكتبات تلقائياً عند التشغيل
# ==========================================
def install_requirements():
    required = ["python-telegram-bot==20.7", "Flask==3.0.0"]
    for package in required:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(f"Error installing {package}: {e}")

install_requirements()

# ==========================================
# 🛠️ استيراد المكتبات المطلوبة
# ==========================================
import logging
import os
import uuid
from threading import Thread
from flask import Flask
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    InlineQueryResultArticle, 
    InputTextMessageContent
)
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    InlineQueryHandler, 
    filters, 
    ContextTypes
)
from telegram.error import TelegramError

# ==========================================
# 🌐 خادم ويب مصغر لإبقاء البوت نشطاً على Render
# ==========================================
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is active!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

Thread(target=run_web_server, daemon=True).start()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# ⚙️ إعدادات المطور الأساسية
# ==========================================
TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"
ADMIN_ID = 8182419990

force_sub_config = {
    "enabled": True,
    "username": "@DAVMTGR",
    "url": "https://t.me/DAVMTGR"
}

user_sessions = {}
polls_db = {}

# ==========================================
# 🛠️ أدوات مساعدة
# ==========================================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not force_sub_config["enabled"]:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=force_sub_config["username"], user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError:
        return False

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إنشاء تصويت جديد", callback_data="btn_create_poll")],
        [
            InlineKeyboardButton("📢 الاشتراك الإجباري", callback_data="btn_force_sub"),
            InlineKeyboardButton("⚪ زر التفاعل", callback_data="btn_reaction")
        ],
        [InlineKeyboardButton("🌐 المركز الإداري", callback_data="btn_admin_center")]
    ])

# ==========================================
# 🤖 بدء التشغيل /start
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if force_sub_config["enabled"] and not await is_user_subscribed(user_id, context):
        msg = (
            f"🚸| عذراً عزيزي\n"
            f"🔰| عليك الاشتراك بقناة البوت لتتمكن من استخدامه\n\n"
            f"- {force_sub_config['url']}\n\n"
            f"‼️| اشترك ثم ارسل /start"
        )
        await update.message.reply_text(msg, disable_web_page_preview=True)
        return

    await update.message.reply_text(
        "أهلاً بك في بوت إنشاء التصويت! اختر من القائمة أدناه:",
        reply_markup=get_main_keyboard()
    )

# ==========================================
# 🔘 معالجة الأزرار (استجابة مضمونة وفورية)
# ==========================================

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    user_id = query.from_user.id
    data = query.data

    # 1. زر إنشاء تصويت جديد
    if data == "btn_create_poll":
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        user_sessions[user_id]["state"] = "waiting_title"
        await query.edit_message_text(
            "📝 <b>أرسل لي الآن اسم المسابقة أو صاحب التصويت:</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="btn_back_main")]]),
            parse_mode="HTML"
        )
        return

    # 2. زر اختيار الإيموجي والتفاعل (شاشة التفاعلات المتاحة)
    if data == "btn_reaction":
        current_emoji = user_sessions.get(user_id, {}).get("emoji", "❤️")
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❤️", callback_data="set_emoji_❤️"),
                InlineKeyboardButton("🔥", callback_data="set_emoji_🔥"),
                InlineKeyboardButton("👍", callback_data="set_emoji_👍"),
                InlineKeyboardButton("👏", callback_data="set_emoji_👏")
            ],
            [
                InlineKeyboardButton("⭐", callback_data="set_emoji_⭐"),
                InlineKeyboardButton("🎉", callback_data="set_emoji_🎉"),
                InlineKeyboardButton("💎", callback_data="set_emoji_💎")
            ],
            [InlineKeyboardButton("🔙 عودة", callback_data="btn_back_main")]
        ])
        await query.edit_message_text(
            f"⚪ <b>اختيار زر التفاعل الخاص بك:</b>\n\nالإيموجي المحدد حالياً: {current_emoji}\nاختر الإيموجي الذي تريد استخدامه في تصويتك القادم:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    # تحديد الإيموجي
    if data.startswith("set_emoji_"):
        selected_emoji = data.replace("set_emoji_", "")
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        user_sessions[user_id]["emoji"] = selected_emoji
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❤️", callback_data="set_emoji_❤️"),
                InlineKeyboardButton("🔥", callback_data="set_emoji_🔥"),
                InlineKeyboardButton("👍", callback_data="set_emoji_👍"),
                InlineKeyboardButton("👏", callback_data="set_emoji_👏")
            ],
            [
                InlineKeyboardButton("⭐", callback_data="set_emoji_⭐"),
                InlineKeyboardButton("🎉", callback_data="set_emoji_🎉"),
                InlineKeyboardButton("💎", callback_data="set_emoji_💎")
            ],
            [InlineKeyboardButton("🔙 عودة", callback_data="btn_back_main")]
        ])
        await query.edit_message_text(
            f"✅ تم تحديد {selected_emoji}\n\n⚪ <b>اختيار زر التفاعل الخاص بك:</b>\n\nالإيموجي المحدد حالياً: {selected_emoji}\nاختر الإيموجي الذي تريد استخدامه في تصويتك القادم:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    # 3. زر الاشتراك الإجباري
    if data == "btn_force_sub":
        status_str = "مفعل 🟢" if force_sub_config["enabled"] else "معطل 🔴"
        text = (
            f"📢 <b>إعدادات الاشتراك الإجباري:</b>\n\n"
            f"• الحالة: {status_str}\n"
            f"• القناة: {force_sub_config['username']}\n"
            f"• الرابط: {force_sub_config['url']}\n"
        )
        keyboard = []
        if is_admin(user_id):
            toggle_text = "❌ تعطيل الاشتراك" if force_sub_config["enabled"] else "✅ تفعيل الاشتراك"
            keyboard.append([InlineKeyboardButton(toggle_text, callback_data="toggle_force_sub")])
        keyboard.append([InlineKeyboardButton("🔙 عودة", callback_data="btn_back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # 4. زر المركز الإداري
    if data == "btn_admin_center":
        if not is_admin(user_id):
            return
        admin_text = (
            f"🌐 <b>المركز الإداري للمطور</b>\n\n"
            f"• أيدي الأدمن: <code>{ADMIN_ID}</code>\n"
            f"• عدد التصويتات المنشأة: <code>{len(polls_db)}</code>\n"
            f"• حالة الاشتراك: <code>{'مفعل' if force_sub_config['enabled'] else 'معطل'}</code>"
        )
        await query.edit_message_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="btn_back_main")]]),
            parse_mode="HTML"
        )
        return

    # 5. زر العودة للرئيسية
    if data == "btn_back_main":
        if user_id in user_sessions and "state" in user_sessions[user_id]:
            del user_sessions[user_id]["state"]
        await query.edit_message_text(
            "أهلاً بك في بوت إنشاء التصويت! اختر من القائمة أدناه:",
            reply_markup=get_main_keyboard()
        )
        return

    # 6. تبديل حالة الاشتراك الإجباري
    if data == "toggle_force_sub" and is_admin(user_id):
        force_sub_config["enabled"] = not force_sub_config["enabled"]
        status_str = "مفعل 🟢" if force_sub_config["enabled"] else "معطل 🔴"
        text = (
            f"📢 <b>إعدادات الاشتراك الإجباري:</b>\n\n"
            f"• الحالة: {status_str}\n"
            f"• القناة: {force_sub_config['username']}\n"
            f"• الرابط: {force_sub_config['url']}\n"
        )
        toggle_text = "❌ تعطيل الاشتراك" if force_sub_config["enabled"] else "✅ تفعيل الاشتراك"
        keyboard = [
            [InlineKeyboardButton(toggle_text, callback_data="toggle_force_sub")],
            [InlineKeyboardButton("🔙 عودة", callback_data="btn_back_main")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    # 7. تسجيل التصويت
    if data.startswith("vote_"):
        await handle_vote_action(query, context)

# ==========================================
# 📝 استلام النصوص وإنشاء التصويت
# ==========================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_id = update.effective_user.id

    if force_sub_config["enabled"] and not await is_user_subscribed(user_id, context):
        msg = (
            f"🚸| عذراً عزيزي\n"
            f"🔰| عليك الاشتراك بقناة البوت لتتمكن من استخدامه\n\n"
            f"- {force_sub_config['url']}\n\n"
            f"‼️| اشترك ثم ارسل /start"
        )
        await update.message.reply_text(msg, disable_web_page_preview=True)
        return

    text = update.message.text.strip()
    user_emoji = user_sessions.get(user_id, {}).get("emoji", "❤️")

    poll_id = f"{user_id}{int(update.message.date.timestamp())}"
    polls_db[poll_id] = {
        "title": text,
        "emoji": user_emoji,
        "votes": set()
    }

    bot_username = (await context.bot.get_me()).username
    inline_code = f"@{bot_username} {poll_id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("• اضغط هنا للمشاركة •", switch_inline_query=poll_id)]
    ])

    reply_msg = f"<b>{text}</b>\n\n• <code>{inline_code}</code>"
    await update.message.reply_text(reply_msg, reply_markup=keyboard, parse_mode="HTML")

# ==========================================
# 🔗 Inline Query للمشاركة
# ==========================================

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    
    if query in polls_db:
        poll_data = polls_db[query]
        title = poll_data["title"]
        emoji = poll_data.get("emoji", "❤️")
        vote_count = len(poll_data["votes"])
        bot_username = (await context.bot.get_me()).username
        
        content = InputTextMessageContent(
            message_text=f"📊 <b>التصويت لصالح:</b> {title}\n\n{emoji} عدد الأصوات: {vote_count}",
            parse_mode="HTML"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{emoji} تصويت ({vote_count})", callback_data=f"vote_{query}")],
            [InlineKeyboardButton("اضغط هنا للدخول الى البوت !", url=f"https://t.me/{bot_username}")]
        ])

        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="اضغط هنا للارسال .",
                description=f"مشاركة تصويت: {title}",
                input_message_content=content,
                reply_markup=keyboard
            )
        ]
        await update.inline_query.answer(results, cache_time=1)

# ==========================================
# ❤️ تسجيل الصوت والتحقق من القناة
# ==========================================

async def handle_vote_action(query, context):
    user_id = query.from_user.id
    
    if force_sub_config["enabled"] and not await is_user_subscribed(user_id, context):
        return

    poll_id = query.data.replace("vote_", "")
    if poll_id in polls_db:
        poll = polls_db[poll_id]
        if user_id not in poll["votes"]:
            poll["votes"].add(user_id)
            vote_count = len(poll["votes"])
            emoji = poll.get("emoji", "❤️")
            bot_username = (await context.bot.get_me()).username
            
            new_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{emoji} تصويت ({vote_count})", callback_data=f"vote_{poll_id}")],
                [InlineKeyboardButton("اضغط هنا للدخول الى البوت !", url=f"https://t.me/{bot_username}")]
            ])
            
            await query.edit_message_text(
                text=f"📊 <b>التصويت لصالح:</b> {poll['title']}\n\n{emoji} عدد الأصوات: {vote_count}",
                reply_markup=new_keyboard,
                parse_mode="HTML"
            )

# ==========================================
# 🚀 تشغيل البوت
# ==========================================
if __name__ == '__main__':
    bot_app = ApplicationBuilder().token(TOKEN).build()
    
    bot_app.add_handler(CallbackQueryHandler(handle_buttons))
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(InlineQueryHandler(inline_query_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("البوت يعمل...")
    bot_app.run_polling()
