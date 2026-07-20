from aiogram import Bot, Dispatcher, executor, types

TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("أهلاً بك، هذا بوت الرسائل")

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer("وصلت رسالتك: " + message.text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
