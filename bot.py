import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"
ADMIN_ID = 8182419990
CHANNEL_USERNAME = "@DAVMTGR"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# دالة لفحص الاشتراك الإجباري
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        print(f"Error checking sub: {e}")
        return True

@dp.message()
async def main_handler(message: types.Message):
    user_id = message.from_user.id

    # 1. إذا كان المرسل هو المالك (أنت)
    if user_id == ADMIN_ID:
        await message.answer("أهلاً بك يا مالك البوت. هذه لوحة التحكم الخاصة بك.")
        return

    # 2. فحص الاشتراك الإجباري للمستخدمين
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        builder = InlineKeyboardBuilder()
        builder.button(text="اضغط هنا للاشتراك في القناة 📢", url=f"https://t.me/DAVMTGR")
        builder.button(text="تأكد من الاشتراك بعد الانضمام ✅", callback_data="check_sub")
        builder.adjust(1)
        
        await message.answer(
            f"❌ عذراً عزيزي، يجب عليك الاشتراك في قناة متجر ديف أولاً لاستخدام البوت المطور.\n\nاشترك في القناة ثم اضغط على زر التأكيد أدناه👇",
            reply_markup=builder.as_markup()
        )
        return

    # 3. إذا ضغط المستخدم على /start وهو مشترك
    if message.text == "/start":
        await message.answer("👋 أهلاً بك في قناة متجر ديف!\n\nيسعدنا تواصلك معنا، يمكنك الآن إرسال استفسارك أو رسالتك مباشرة هنا، وسيتم إيصالها للمالك والرد عليك في أقرب وقت ممكن.")
        return

    # 4. تحويل رسائل المستخدمين إلى حسابك الشخصي
    user_name = message.from_user.full_name
    user_username = f"@{message.from_user.username}" if message.from_user.username else "بدون معرف"
    user_text = message.text

    admin_message = (
        "📩 رسالة جديدة من متجر ديف:\n\n"
        f"👤 الاسم: {user_name}\n"
        f"🔗 المعرف: {user_username}\n"
        f"🆔 الآيدي: `{user_id}`\n\n"
        f"💬 النص:\n{user_text}"
    )

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode="Markdown")
        await message.answer("✅ تم إرسال رسالتك إلى إدارة متجر ديف بنجاح، سيتم الرد عليك قريباً.")
    except Exception as e:
        print(f"Error forwarding message: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
