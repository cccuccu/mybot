import asyncio
from aiogram import Bot, Dispatcher, types

TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def echo(message: types.Message):
    if message.text == "/start":
        await message.answer("أهلاً بك، هذا بوت الرسائل")
    else:
        await message.answer(f"وصلت رسالتك: {message.text}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
